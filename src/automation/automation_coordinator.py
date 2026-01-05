import os
import time
import uuid
import pyautogui
from PIL import Image
import mss
from .kindle_controller import KindleController
from .pdf_converter import PdfConverter

class AutomationCoordinator:
    PAGE_TURN_DELAY = 2
    EXIT_FULLSCREEN_DELAY = 0.5

    def __init__(self, output_dir="Kindle_PDFs", status_callback=None, error_callback=None, success_callback=None, completion_callback=None, root_window=None):
        self.output_dir = output_dir
        self.status_callback = status_callback if status_callback else self._default_status_callback
        self.error_callback = error_callback if error_callback else self._default_error_callback
        self.success_callback = success_callback if success_callback else self._default_success_callback
        self.completion_callback = completion_callback if completion_callback else self._default_completion_callback
        self.root_window = root_window
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.kindle_controller = KindleController(status_callback, error_callback)
        self.pdf_converter = PdfConverter(output_dir, status_callback)

    def _default_status_callback(self, message):
        print(f"Status: {message}")

    def _default_error_callback(self, message):
        print(f"Error: {message}")

    def _default_success_callback(self, pdf_path):
        print(f"Success: PDF created at {pdf_path}")

    def _default_completion_callback(self):
        print("Automation complete.")

    def _take_screenshots(self, monitor, pages, screenshots_folder):
        self.kindle_controller.navigate_to_first_page()
        image_files = []
        with mss.mss() as sct:
            for i in range(pages):
                self.status_callback(f"Taking screenshot {i + 1}/{pages}")
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
                image_path = os.path.join(screenshots_folder, f"page_{i + 1}.png")
                img.save(image_path)
                image_files.append(image_path)

                pyautogui.press('right')
                time.sleep(self.PAGE_TURN_DELAY)
        return image_files

    def _cleanup_temp_files(self, screenshots_folder):
        if screenshots_folder and os.path.exists(screenshots_folder):
            for f in os.listdir(screenshots_folder):
                if f.endswith(".png"):
                    os.remove(os.path.join(screenshots_folder, f))
            os.rmdir(screenshots_folder)

    def run(self, pages: int, delay: int = 3):
        kindle_win = None
        is_fullscreen = False
        screenshots_folder = None
        try:
            kindle_win, monitor = self.kindle_controller.launch_and_activate_kindle()
            if not kindle_win:
                return False, None
            is_fullscreen = True

            self.status_callback(f"Starting screenshots in {delay} seconds...")
            time.sleep(delay)

            session_id = str(uuid.uuid4())
            screenshots_folder = os.path.join(self.output_dir, "temp_screenshots_" + session_id)
            os.makedirs(screenshots_folder, exist_ok=True)

            image_files = self._take_screenshots(monitor, pages, screenshots_folder)

            pdf_path = self.pdf_converter.create_pdf_from_images(image_files)

            self.status_callback(f"PDF created successfully: {os.path.basename(pdf_path)}")
            self.success_callback(pdf_path)
            return True, pdf_path

        except Exception as e:
            self.error_callback(f"An error occurred: {str(e)}")
            return False, None
        finally:
            if is_fullscreen:
                pyautogui.press('f11')
                time.sleep(self.EXIT_FULLSCREEN_DELAY)

            if self.root_window:
                self.root_window.deiconify()
                self.root_window.lift()
                self.root_window.focus_force()

            self._cleanup_temp_files(screenshots_folder)
            self.completion_callback()
