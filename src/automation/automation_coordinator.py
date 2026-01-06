import os
import time
import uuid
import pyautogui
from PIL import Image
import mss
import cv2
import numpy as np
import pygetwindow as gw
import threading
import shutil
import ctypes
from ..utils import create_temp_dir, cleanup_dir
from src.automation.kindle_controller import KindleController
from .pdf_converter import PdfConverter

class AutomationCoordinator:
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002

    EXIT_FULLSCREEN_DELAY = 0.5 

    def __init__(self, output_dir="Kindle_PDFs", status_callback=None, error_callback=None, 
                 success_callback=None, completion_callback=None, preview_callback=None, 
                 progress_callback=None, root_window=None):
        self.output_dir = output_dir
        self.status_callback = status_callback or (lambda msg: print(f"Status: {msg}"))
        self.error_callback = error_callback or (lambda msg: print(f"Error: {msg}"))
        self.success_callback = success_callback or (lambda path: print(f"Success: {path}"))
        self.completion_callback = completion_callback or (lambda: print("Complete."))
        self.preview_callback = preview_callback or (lambda path: print(f"Preview: {path}"))
        self.progress_callback = progress_callback or (lambda cur, tot: print(f"Progress: {cur}/{tot}"))
        self.root_window = root_window
        
        self.kindle_controller = KindleController(self.status_callback, self.error_callback)
        self.pdf_converter = PdfConverter(self.status_callback)
        
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()

    def pause(self):
        self.status_callback("Pausing...")
        self.pause_event.set()

    def resume(self):
        self.status_callback("Resuming...")
        self.pause_event.clear()

    def stop(self):
        self.status_callback("Stopping...")
        self.stop_event.set()
        self.pause_event.clear()

    def _hash_image(self, sct_img):
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        img_np = np.array(img)
        gray_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        return cv2.mean(gray_img)[0]

    def _take_screenshots(self, pages, screenshots_folder, page_turn_delay, page_turn_direction, book_region, end_detection_sensitivity):
        self.kindle_controller.navigate_to_first_page()
        image_files = []
        last_hashes = []
        consecutive_matches = end_detection_sensitivity

        sct_monitor = { "left": book_region[0], "top": book_region[1], "width": book_region[2], "height": book_region[3] }

        page_num = 1
        with mss.mss() as sct:
            while page_num <= pages:
                if self.stop_event.is_set():
                    self.status_callback("Automation stopped by user.")
                    break
                
                while self.pause_event.is_set():
                    time.sleep(0.1)
                    if self.stop_event.is_set():
                        self.status_callback("Automation stopped by user while paused.")
                        return []

                self.progress_callback(page_num, pages)
                self.status_callback(f"Capturing page {page_num}/{pages}...")
                sct_img = sct.grab(sct_monitor)
                
                current_hash = self._hash_image(sct_img)
                if len(last_hashes) >= consecutive_matches and all(h == current_hash for h in last_hashes[-consecutive_matches:]):
                    self.status_callback(f"End of book detected ({consecutive_matches} identical pages).")
                    break
                last_hashes.append(current_hash)

                image_path = os.path.join(screenshots_folder, f"page_{page_num:04d}.png")
                img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
                img.save(image_path)
                image_files.append(image_path)
                
                self.preview_callback(image_path)

                if page_num == pages:
                    self.status_callback(f"Reached user-defined page limit of {pages}.")
                    break

                pyautogui.press(page_turn_direction)
                time.sleep(page_turn_delay)
                page_num += 1
        return image_files

    def _check_disk_space(self, output_folder, estimated_pages):
        ESTIMATED_BYTES_PER_PAGE = 2 * 1024 * 1024
        PDF_OVERHEAD_FACTOR = 1.1

        estimated_total_bytes_needed = estimated_pages * ESTIMATED_BYTES_PER_PAGE * PDF_OVERHEAD_FACTOR

        os.makedirs(output_folder, exist_ok=True)
        
        try:
            total, used, free = shutil.disk_usage(output_folder)
            self.status_callback(f"Disk space check: Free space {free / (1024**3):.2f} GB, Estimated needed: {estimated_total_bytes_needed / (1024**3):.2f} GB")

            if free < estimated_total_bytes_needed:
                self.error_callback(f"Insufficient disk space in '{output_folder}'. "
                                    f"Needed {estimated_total_bytes_needed / (1024**3):.2f} GB, "
                                    f"Available {free / (1024**3):.2f} GB.")
                return False
            return True
        except Exception as e:
            self.error_callback(f"Could not check disk space: {e}")
            return False

    def _prevent_sleep(self):
        ctypes.windll.kernel32.SetThreadExecutionState(
            AutomationCoordinator.ES_CONTINUOUS |
            AutomationCoordinator.ES_SYSTEM_REQUIRED |
            AutomationCoordinator.ES_DISPLAY_REQUIRED
        )
        self.status_callback("OS sleep prevention activated.")

    def _allow_sleep(self):
        ctypes.windll.kernel32.SetThreadExecutionState(AutomationCoordinator.ES_CONTINUOUS)
        self.status_callback("OS sleep prevention deactivated.")

    def test_capture(self, region_detection_mode: str, manual_capture_region: list = None, **kwargs):
        self.status_callback("Running test capture...")
        kindle_win = None
        temp_dir = None
        try:
            kindle_windows = gw.getWindowsWithTitle('Kindle')
            if not kindle_windows:
                self.error_callback("Kindle app window not found.")
                return
            kindle_win = kindle_windows[0]

            book_region_dict = None
            if region_detection_mode == "Manual":
                if manual_capture_region and len(manual_capture_region) == 4:
                    self.status_callback("Using manual region for test capture.")
                    book_region_dict = {"left": manual_capture_region[0], "top": manual_capture_region[1], "width": manual_capture_region[2], "height": manual_capture_region[3]}
                else:
                    self.error_callback("Manual region mode selected, but region is invalid.")
                    return
            else:
                self.status_callback("Using automatic detection for test capture.")
                if kindle_win.isMinimized: kindle_win.restore()
                kindle_win.activate()
                time.sleep(0.5)
                book_region_dict = self.kindle_controller.get_book_region(kindle_win)

            if not book_region_dict:
                self.error_callback("Failed to determine book capture region for test.")
                return

            sct_monitor = { "left": book_region_dict["left"], "top": book_region_dict["top"], "width": book_region_dict["width"], "height": book_region_dict["height"] }

            with mss.mss() as sct:
                sct_img = sct.grab(sct_monitor)
                
                temp_dir = create_temp_dir(self.output_dir, prefix="test_capture_")
                image_path = os.path.join(temp_dir, f"test_capture_{uuid.uuid4()}.png")

                img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
                img.save(image_path)
                
                self.status_callback("Test capture successful.")
                self.preview_callback(image_path)

        except Exception as e:
            self.error_callback(f"Test capture failed: {e}")
        finally:
            cleanup_dir(temp_dir)

    def run(self, pages: int, optimize_images: bool, page_turn_direction: str,
            page_turn_delay: float, kindle_startup_delay: float, 
            window_activation_delay: float, fullscreen_delay: float, 
            navigation_delay: float, region_detection_mode: str, 
            manual_capture_region: list = None, output_folder: str = "Kindle_PDFs", 
            output_filename: str = "My_Kindle_Book.pdf", image_format: str = "PNG", 
            jpeg_quality: int = 90, end_detection_sensitivity: int = 3, **kwargs):
        
        self.stop_event.clear()
        self.pause_event.clear()
        
        kindle_win = None
        is_fullscreen = False
        screenshots_folder = None
        
        self._prevent_sleep()
        
        try:
            if not self._check_disk_space(output_folder, pages):
                return
            
            self.kindle_controller.KINDLE_STARTUP_DELAY = kindle_startup_delay
            self.kindle_controller.WINDOW_ACTIVATION_DELAY = window_activation_delay
            self.kindle_controller.FULLSCREEN_DELAY = fullscreen_delay
            self.kindle_controller.NAVIGATION_DELAY = navigation_delay
            self.kindle_controller.PAGE_TURN_DELAY = page_turn_delay

            kindle_win, _ = self.kindle_controller.launch_and_activate_kindle()
            if not kindle_win: return
            is_fullscreen = True

            book_region_dict = None
            if region_detection_mode == "Manual":
                if manual_capture_region and len(manual_capture_region) == 4:
                    self.status_callback("Using user-defined manual capture region.")
                    book_region_dict = {"left": manual_capture_region[0], "top": manual_capture_region[1], "width": manual_capture_region[2], "height": manual_capture_region[3]}
                else:
                    self.error_callback("Manual region mode selected, but region is invalid.")
                    return
            else:
                book_region_dict = self.kindle_controller.get_book_region(kindle_win)
            
            if not book_region_dict:
                self.error_callback("Failed to determine book capture region.")
                return

            direction_key = None
            if page_turn_direction == "Automatic":
                direction_key = self.kindle_controller.determine_page_turn_direction(kindle_win)
            elif page_turn_direction == "LtoR":
                direction_key = 'left'
            elif page_turn_direction == "RtoL":
                direction_key = 'right'

            if not direction_key:
                self.error_callback("Could not determine page turn direction.")
                return

            self.status_callback("Starting screenshots in 3 seconds...")
            time.sleep(3)
            
            if self.stop_event.is_set(): return

            screenshots_folder = create_temp_dir(output_folder, prefix="temp_screenshots_")
            
            book_region_tuple = (book_region_dict["left"], book_region_dict["top"], book_region_dict["width"], book_region_dict["height"])
            image_files = self._take_screenshots(pages, screenshots_folder, page_turn_delay, direction_key, book_region_tuple, end_detection_sensitivity)

            if self.stop_event.is_set() or not image_files:
                self.status_callback("Process stopped or no images were captured. Aborting PDF creation.")
                return

            pdf_path = self.pdf_converter.create_pdf_from_images(image_files, output_folder, output_filename, 
                                                                 optimize_images, image_format, jpeg_quality)
            self.success_callback(pdf_path)

        except Exception as e:
            self.error_callback(f"An unexpected error occurred: {e}")
        finally:
            self._allow_sleep()

            if is_fullscreen and kindle_win:
                try:
                    if kindle_win.isNotMinimized:
                        pyautogui.press('f11')
                        time.sleep(self.EXIT_FULLSCREEN_DELAY)
                except gw.PyGetWindowException:
                    self.status_callback("Kindle window was closed manually.")
            
            if self.root_window:
                self.root_window.deiconify()
                self.root_window.lift()
                self.root_window.focus_force()

            cleanup_dir(screenshots_folder)
            self.completion_callback()
