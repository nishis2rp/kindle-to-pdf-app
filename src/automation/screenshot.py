import os
import time
import uuid
import pyautogui
import pygetwindow as gw
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import subprocess
import tkinter as tk # Import tkinter for root window manipulation if needed outside of MainWindow
import mss

class ScreenshotAutomation:
    KINDLE_STARTUP_DELAY = 10
    WINDOW_RESTORE_DELAY = 0.5
    WINDOW_ACTIVATION_DELAY = 1
    FULLSCREEN_DELAY = 1
    NAVIGATION_DELAY = 5
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

    def _default_status_callback(self, message):
        print(f"Status: {message}")

    def _default_error_callback(self, message):
        print(f"Error: {message}")

    def _default_success_callback(self, pdf_path):
        print(f"Success: PDF created at {pdf_path}")

    def _default_completion_callback(self):
        print("Automation complete.")

    def _start_kindle_app(self):
        self.status_callback("Attempting to start Kindle application...")
        kindle_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Amazon', 'Kindle', 'Kindle.exe')
        
        if not os.path.exists(kindle_path):
            kindle_path_pf = os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Amazon', 'Kindle', 'Kindle.exe')
            if os.path.exists(kindle_path_pf):
                kindle_path = kindle_path_pf
            else:
                self.status_callback("Could not find Kindle.exe to auto-start. Please ensure it is running.")
                return False, None # Will proceed and try to find window anyway if not found
        
        if kindle_path and os.path.exists(kindle_path):
            try:
                subprocess.Popen(kindle_path)
                self.status_callback(f"Waiting for Kindle to start ({self.KINDLE_STARTUP_DELAY}s)...")
                time.sleep(self.KINDLE_STARTUP_DELAY)
                return True, None
            except Exception as e:
                self.status_callback(f"Failed to start Kindle automatically: {e}")
                return False, f"Failed to start Kindle: {e}"
        return False, None

    def _get_monitor_for_window(self, window):
        with mss.mss() as sct:
            # sct.monitors[0] is the virtual screen of all monitors, so skip it.
            for monitor in sct.monitors[1:]:
                window_center_x = window.left + window.width / 2
                window_center_y = window.top + window.height / 2
                if (monitor["left"] <= window_center_x < monitor["left"] + monitor["width"] and
                    monitor["top"] <= window_center_y < monitor["top"] + monitor["height"]):
                    return monitor
        # Fallback to the primary monitor if no monitor is found
        if len(sct.monitors) > 1:
            return sct.monitors[1]
        return None

    def launch_and_activate_kindle(self):
        started_kindle, kindle_start_error = self._start_kindle_app()
        if kindle_start_error:
            self.error_callback(kindle_start_error)
            return None, None

        kindle_win, monitor = self._find_activate_fullscreen_kindle()
        if not kindle_win:
            self.error_callback("Kindle window not found after launch attempt.")
            return None, None
        return kindle_win, monitor

    def _find_activate_fullscreen_kindle(self):
        self.status_callback("Finding Kindle app window...")
        kindle_windows = gw.getWindowsWithTitle('Kindle')
        if not kindle_windows:
            self.error_callback("Kindle app window not found. Please ensure it is running and visible.")
            return None, None

        kindle_win = kindle_windows[0]
        
        self.status_callback("Activating and focusing Kindle window...")

        if kindle_win.isMinimized:
            kindle_win.restore()
        time.sleep(self.WINDOW_RESTORE_DELAY)
        kindle_win.activate()
        time.sleep(self.WINDOW_ACTIVATION_DELAY)

        monitor = self._get_monitor_for_window(kindle_win)

        # Make it full screen
        pyautogui.press('f11')
        time.sleep(self.FULLSCREEN_DELAY) # Give it time to enter fullscreen
        return kindle_win, monitor

    def _navigate_to_first_page(self):
        self.status_callback("Navigating to the beginning of the book (pressing 'Home' key)...")
        pyautogui.press('home')
        time.sleep(self.NAVIGATION_DELAY) # Increased delay for loading the beginning

    def _take_screenshots_and_create_pdf_core(self, monitor, pages, screenshots_folder):
        self._navigate_to_first_page()
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
                time.sleep(self.PAGE_TURN_DELAY) # Default page turn delay
        return image_files

    def _create_pdf_from_images(self, image_files, screenshots_folder):
        self.status_callback("Creating PDF...")
        pdf_name = f"Kindle_Book_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(self.output_dir, pdf_name)

        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter

        for image_path in image_files:
            img = Image.open(image_path)
            img_width, img_height = img.size
            aspect = img_height / float(img_width)
            new_width = width
            new_height = new_width * aspect
            c.setPageSize((new_width, new_height))
            c.drawImage(image_path, 0, 0, width=new_width, height=new_height)
            c.showPage()

        c.save()
        return pdf_path

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
            # Step 1 & 2: Start, find, activate, and fullscreen Kindle
            kindle_win, monitor = self.launch_and_activate_kindle()
            if not kindle_win:
                return False, None
            is_fullscreen = True # Assume fullscreen is active now

            self.status_callback(f"Starting screenshots in {delay} seconds...")
            time.sleep(delay)

            # Prepare screenshot folder
            session_id = str(uuid.uuid4())
            screenshots_folder = os.path.join(self.output_dir, "temp_screenshots_" + session_id)
            os.makedirs(screenshots_folder, exist_ok=True)

            # Step 4: Take screenshots
            image_files = self._take_screenshots_and_create_pdf_core(monitor, pages, screenshots_folder)

            # Step 5: Create PDF
            pdf_path = self._create_pdf_from_images(image_files, screenshots_folder)

            self.status_callback(f"PDF created successfully: {os.path.basename(pdf_path)}")
            self.success_callback(pdf_path)
            return True, pdf_path

        except Exception as e:
            self.error_callback(f"An error occurred: {str(e)}")
            return False, None
        finally:
            # Ensure we exit full screen mode in case of an error
            if is_fullscreen:
                pyautogui.press('f11')
                time.sleep(self.EXIT_FULLSCREEN_DELAY) # Give it time to exit fullscreen

            # --- New: Explicitly activate GUI root window ---
            if self.root_window:
                # Ensure it's not minimized
                self.root_window.deiconify() 
                # Bring it to the top
                self.root_window.lift()
                # Force focus to the GUI window
                self.root_window.focus_force()
            # --- End of new code ---

            # Clean up temporary screenshot files
            self._cleanup_temp_files(screenshots_folder)
            self.completion_callback()
