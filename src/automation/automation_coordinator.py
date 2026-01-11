"""
Simplified Automation Coordinator module.
Simplified workflow with manual region selection.
"""

import os
import time
import uuid
from typing import Optional, Callable, List, Tuple
import pyautogui
from PIL import Image
import mss
import cv2
import numpy as np
import pygetwindow as gw
import threading
import shutil
import ctypes
import tkinter as tk
import tkinter.messagebox as messagebox
from src.constants import (
    PowerManagement,
    Storage,
    PageDetection,
    PageTurnDirection,
    Delays,
)
from ..utils import create_temp_dir, cleanup_dir
from src.automation.kindle_controller import KindleController
from .pdf_converter import PdfConverter


class AutomationCoordinator:
    """Simplified coordinator for Kindle to PDF conversion"""

    def __init__(self, output_dir=None, status_callback=None, error_callback=None,
                 success_callback=None, completion_callback=None, preview_callback=None,
                 progress_callback=None, root_window=None):
        from src.constants import DefaultConfig
        self.output_dir = output_dir if output_dir is not None else DefaultConfig.get_output_folder()
        self.status_callback = status_callback or (lambda msg: print(f"Status: {msg}"))
        self.error_callback = error_callback or (lambda msg: print(f"Error: {msg}"))
        self.success_callback = success_callback or (lambda path: print(f"Success: {path}"))
        self.completion_callback = completion_callback or (lambda: print("Complete."))
        self.preview_callback = preview_callback or (lambda path: print(f"Preview: {path}"))
        self.progress_callback = progress_callback or (lambda cur, tot: print(f"Progress: {cur}/{tot}"))
        self.root_window = root_window

        self.kindle_controller = KindleController(self.status_callback, self.error_callback)
        self.pdf_converter = PdfConverter(self.status_callback)

        self.stop_event = threading.Event()
        self.current_page = 0
        self.target_pages = 0
        self.is_running = False

    def stop(self):
        self.status_callback("Stopping...")
        self.stop_event.set()

    def get_progress(self):
        """Get current progress information"""
        return {
            "current_page": self.current_page,
            "target_pages": self.target_pages,
            "is_running": self.is_running
        }

    def _hash_image(self, sct_img):
        """
        画像のハッシュを計算（KindleControllerと同じアルゴリズム）
        Returns: tuple (mean_value, dhash)
        """
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        img_np = np.array(img)
        gray_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

        # 平均値
        mean_value = cv2.mean(gray_img)[0]

        # dHash
        resized = cv2.resize(gray_img, (9, 8), interpolation=cv2.INTER_AREA)
        diff = resized[:, 1:] > resized[:, :-1]
        hash_value = sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])

        return (mean_value, hash_value)

    def _compare_hashes(self, hash1, hash2):
        """
        2つのハッシュを比較して差分を返す
        Args:
            hash1, hash2: tuples of (mean_value, dhash)
        Returns:
            float: difference score (higher = more different)
        """
        mean_diff = abs(hash1[0] - hash2[0])
        xor = hash1[1] ^ hash2[1]
        hamming_dist = bin(xor).count('1')
        combined_diff = mean_diff + (hamming_dist * 2.0)
        return combined_diff

    def _take_screenshots(
        self,
        pages: int,
        screenshots_folder: str,
        page_turn_direction: str,
        book_region: Tuple[int, int, int, int]
    ) -> List[str]:
        """Capture screenshots of pages."""
        image_files = []
        last_hashes = []
        consecutive_matches = 3  # Default end detection sensitivity

        sct_monitor = {
            "left": book_region[0],
            "top": book_region[1],
            "width": book_region[2],
            "height": book_region[3]
        }

        page_num = 1
        with mss.mss() as sct:
            while page_num <= pages:
                if self.stop_event.is_set():
                    self.status_callback("Automation stopped by user.")
                    break

                # Update current page
                self.current_page = page_num
                self.progress_callback(page_num, pages)

                # Wait before capturing
                if page_num > 1:
                    time.sleep(Delays.PAGE_STABILIZATION)

                self.status_callback(f"Capturing page {page_num}/{pages}...")
                sct_img = sct.grab(sct_monitor)

                current_hash = self._hash_image(sct_img)

                # Check for end of book (consecutive identical pages)
                if len(last_hashes) >= consecutive_matches:
                    # Check if last N pages are very similar (diff < threshold)
                    recent_hashes = last_hashes[-consecutive_matches:]
                    all_similar = all(
                        self._compare_hashes(current_hash, prev_hash) < PageDetection.HASH_DIFF_THRESHOLD
                        for prev_hash in recent_hashes
                    )
                    if all_similar:
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

                # Turn page
                self.status_callback(f"Turning page with {page_turn_direction} arrow key...")
                pyautogui.keyDown(page_turn_direction)
                time.sleep(Delays.KEY_PRESS)
                pyautogui.keyUp(page_turn_direction)

                time.sleep(Delays.PAGE_TURN)
                page_num += 1
        return image_files

    def _check_disk_space(self, output_folder: str, estimated_pages: int) -> bool:
        """Check if sufficient disk space is available."""
        estimated_total_bytes_needed = (
            estimated_pages *
            Storage.ESTIMATED_BYTES_PER_PAGE *
            Storage.PDF_OVERHEAD_FACTOR
        )

        os.makedirs(output_folder, exist_ok=True)

        try:
            total, used, free = shutil.disk_usage(output_folder)
            self.status_callback(f"Disk space check: Free space {free / (1024**3):.2f} GB, Estimated needed: {estimated_total_bytes_needed / (1024**3):.2f} GB")

            if free < estimated_total_bytes_needed:
                self.error_callback(
                    f"Insufficient disk space in '{output_folder}'.\n"
                    f"Needed {estimated_total_bytes_needed / (1024**3):.2f} GB, "
                    f"Available {free / (1024**3):.2f} GB."
                )
                return False
            return True
        except Exception as e:
            self.error_callback(f"Could not check disk space: {e}")
            return False

    def _prevent_sleep(self) -> None:
        """Prevent system from sleeping during automation"""
        ctypes.windll.kernel32.SetThreadExecutionState(
            PowerManagement.ES_CONTINUOUS |
            PowerManagement.ES_SYSTEM_REQUIRED |
            PowerManagement.ES_DISPLAY_REQUIRED
        )
        self.status_callback("OS sleep prevention activated.")

    def _allow_sleep(self) -> None:
        """Allow system to sleep after automation"""
        ctypes.windll.kernel32.SetThreadExecutionState(PowerManagement.ES_CONTINUOUS)
        self.status_callback("OS sleep prevention deactivated.")

    def _select_region_manual(self, kindle_win, monitor=None) -> Optional[Tuple[int, int, int, int]]:
        """Let user manually select capture region"""
        self.status_callback("Please select the capture region on your Kindle window...")

        # Variable to store the selected region
        selected_region = [None]

        try:
            # Use provided monitor, or detect it from window
            if not monitor and kindle_win:
                monitor = self.kindle_controller.get_monitor_for_window(kindle_win)

            if monitor:
                self.status_callback(f"Opening region selector on monitor at ({monitor['left']}, {monitor['top']})")
            else:
                self.status_callback("Could not detect monitor, using primary monitor")

            # Import RegionSelector here to avoid circular imports
            from src.gui.region_selector import RegionSelector

            # Define callback for when selection is complete
            def on_selection_complete(region):
                selected_region[0] = region

            # Use the existing root window if available, otherwise create a temporary one
            if self.root_window:
                # Use existing root window
                selector = RegionSelector(self.root_window, on_selection_complete, monitor=monitor)
                # Wait for the selector window to close
                self.root_window.wait_window(selector.selector_window)
            else:
                # Fallback: create temporary root window
                temp_root = tk.Tk()
                temp_root.withdraw()
                selector = RegionSelector(temp_root, on_selection_complete, monitor=monitor)
                temp_root.wait_window(selector.selector_window)
                temp_root.destroy()

            # Check if a region was selected
            if selected_region[0]:
                left, top, width, height = selected_region[0]
                self.status_callback(f"Region selected: {width}x{height} at ({left}, {top})")
                return (left, top, width, height)
            else:
                self.error_callback("No region selected.")
                return None

        except Exception as e:
            self.error_callback(f"Region selection failed: {e}")
            import traceback
            self.status_callback(f"Traceback: {traceback.format_exc()}")
            return None

    def run(self, pages: int, output_folder: str = None,
            output_filename: str = None, **kwargs):
        """
        Simplified automation run with manual region selection.

        Args:
            pages: Number of pages to capture
            output_folder: Output directory (defaults to Downloads folder)
            output_filename: Output PDF filename (defaults to yyyymmdd.pdf)
        """
        from src.constants import DefaultConfig

        # Set defaults if not provided
        if output_folder is None:
            output_folder = DefaultConfig.get_output_folder()
        if output_filename is None:
            output_filename = DefaultConfig.get_output_filename()

        self.stop_event.clear()
        self.target_pages = pages
        self.current_page = 0
        self.is_running = True

        kindle_win = None
        screenshots_folder = None

        # Prompt user to prepare Kindle
        while True:
            user_response = messagebox.askokcancel(
                "準備確認",
                "Kindleアプリを立ち上げて、対象書籍のスタートページに移動してください。\n\n"
                "準備ができたら「OK」を押してください。"
            )

            if not user_response:
                self.status_callback("User cancelled the automation.")
                self.completion_callback()
                return

            # Check for Kindle window
            self.status_callback("Checking for Kindle window...")
            temp_kindle_win = self.kindle_controller._get_kindle_window()

            if not temp_kindle_win:
                retry = messagebox.askretrycancel(
                    "Kindleアプリが見つかりません",
                    "Kindleアプリが起動していないか、書籍が開かれていません。\n\n"
                    "以下を確認してください：\n"
                    "1. Kindleアプリが起動している\n"
                    "2. 書籍が開かれている（ライブラリ画面ではない）\n"
                    "3. 対象書籍のスタートページに移動している\n\n"
                    "「再試行」を押して再度確認するか、「キャンセル」で中止してください。"
                )

                if not retry:
                    self.status_callback("User cancelled the automation after Kindle check failed.")
                    self.completion_callback()
                    return
                continue
            else:
                self.status_callback("Kindle window found successfully.")
                break

        self.status_callback("Automation started.")
        self._prevent_sleep()

        try:
            # Check disk space
            self.status_callback(f"Checking disk space in '{output_folder}'...")
            if not self._check_disk_space(output_folder, pages):
                self.error_callback("Disk space check failed. Aborting automation.")
                return
            self.status_callback("Disk space check passed.")

            # Activate Kindle window
            self.status_callback("Activating Kindle window...")
            kindle_win, monitor = self.kindle_controller.find_and_activate_kindle()
            if not kindle_win:
                self.error_callback("Kindle window could not be activated. Aborting automation.")
                return
            self.status_callback("Kindle window activated.")

            # Bring Kindle window to front and ensure it's visible
            self.status_callback("Bringing Kindle window to front...")
            try:
                import time
                kindle_win.activate()
                time.sleep(0.5)
                # Set as foreground window using Windows API
                import ctypes
                hwnd = ctypes.windll.user32.FindWindowW(None, kindle_win.title)
                if hwnd:
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
                    time.sleep(0.5)
                self.status_callback("Kindle window is now in front.")
            except Exception as e:
                self.status_callback(f"Warning: Could not bring Kindle to front: {e}")

            # Manual region selection
            self.status_callback("Starting manual region selection...")
            book_region = self._select_region_manual(kindle_win, monitor)

            if not book_region:
                self.error_callback("Region selection failed. Aborting automation.")
                return

            self.status_callback(f"Capture region: {book_region[2]}x{book_region[3]} at ({book_region[0]}, {book_region[1]})")

            # Determine page turn direction automatically
            self.status_callback("Determining page turn direction automatically...")
            direction_key = self.kindle_controller.determine_page_turn_direction(kindle_win)

            if not direction_key:
                self.error_callback("Could not determine page turn direction. Aborting automation.")
                return
            self.status_callback(f"Page turn direction determined: {direction_key}")

            # Start screenshot capture
            self.status_callback("Starting screenshot process...")
            time.sleep(3)

            if self.stop_event.is_set():
                self.status_callback("Automation stopped before screenshots began.")
                return

            screenshots_folder = create_temp_dir(output_folder, prefix="temp_screenshots_")

            image_files = self._take_screenshots(pages, screenshots_folder, direction_key, book_region)

            if self.stop_event.is_set():
                self.status_callback("Automation stopped during screenshot capture.")
                return
            if not image_files:
                self.status_callback("No images were captured. Aborting PDF creation.")
                return
            self.status_callback(f"{len(image_files)} images captured.")

            # Create PDF
            self.status_callback("Creating PDF from captured images...")
            pdf_path = self.pdf_converter.create_pdf_from_images(
                image_files, output_folder, output_filename,
                optimize_images=True,  # Always optimize
                image_format="PNG",    # Always PNG
                jpeg_quality=90
            )
            self.success_callback(pdf_path)
            self.status_callback("Automation finished successfully.")

        except Exception as e:
            self.error_callback(f"An unexpected error occurred during automation: {e}")
            import traceback
            self.status_callback(f"Error traceback: {traceback.format_exc()}")
        finally:
            try:
                self._allow_sleep()
            except Exception as e:
                self.status_callback(f"Warning: Could not restore sleep settings: {e}")

            if self.root_window:
                try:
                    self.root_window.deiconify()
                    self.root_window.lift()
                    self.root_window.focus_force()
                except Exception as e:
                    self.status_callback(f"Warning: Could not restore main window: {e}")

            try:
                cleanup_dir(screenshots_folder)
            except Exception as e:
                self.status_callback(f"Warning: Could not cleanup temporary files: {e}")

            self.is_running = False
            self.completion_callback()
