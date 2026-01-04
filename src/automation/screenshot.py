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

class ScreenshotAutomation:
    def __init__(self, output_dir="Kindle_PDFs", status_callback=None, error_callback=None, root_window=None):
        self.output_dir = output_dir
        self.status_callback = status_callback if status_callback else self._default_status_callback
        self.error_callback = error_callback if error_callback else self._default_error_callback
        self.root_window = root_window # Store reference to the main Tkinter root window
        os.makedirs(self.output_dir, exist_ok=True)

    def _default_status_callback(self, message):
        print(f"Status: {message}")

    def _default_error_callback(self, message):
        print(f"Error: {message}")

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
                self.status_callback("Waiting for Kindle to start (10s)...")
                time.sleep(10)
                return True, None
            except Exception as e:
                self.status_callback(f"Failed to start Kindle automatically: {e}")
                return False, f"Failed to start Kindle: {e}"
        return False, None


    def launch_kindle_app_public(self):
        return self._start_kindle_app()

    def find_and_activate_kindle_public(self):
        return self._find_activate_fullscreen_kindle()
    
    def launch_and_activate_kindle(self):
        started_kindle, kindle_start_error = self.launch_kindle_app_public()
        if kindle_start_error:
            self.error_callback(kindle_start_error)
            return None

        kindle_win = self.find_and_activate_kindle_public()
        if not kindle_win:
            self.error_callback("Kindle window not found after launch attempt.")
            return None
        return kindle_win

    def _find_activate_fullscreen_kindle(self):
        self.status_callback("Finding Kindle app window...")
        kindle_windows = gw.getWindowsWithTitle('Kindle')
        if not kindle_windows:
            self.error_callback("Kindle app window not found. Please ensure it is running and visible.")
            return None

        kindle_win = kindle_windows[0]
        
        self.status_callback("Activating and focusing Kindle window...")

        if kindle_win.isMinimized:
            kindle_win.restore()
        time.sleep(0.5)
        kindle_win.activate()
        time.sleep(1)

        # Make it full screen
        pyautogui.press('f11')
        time.sleep(1) # Give it time to enter fullscreen
        return kindle_win

    def _navigate_to_first_page(self):
        self.status_callback("Navigating to the beginning of the book (pressing 'Home' key)...")
        pyautogui.press('home')
        time.sleep(5) # Increased delay for loading the beginning

    def _take_screenshots_and_create_pdf_core(self, kindle_win, pages, screenshots_folder):
        image_files = []
        for i in range(pages):
            self.status_callback(f"Taking screenshot {i + 1}/{pages}")
            screenshot = pyautogui.screenshot()
            image_path = os.path.join(screenshots_folder, f"page_{i + 1}.png")
            screenshot.save(image_path)
            image_files.append(image_path)

            pyautogui.press('right')
            time.sleep(2) # Default page turn delay
        return image_files

    def _create_pdf_from_images(self, image_files, screenshots_folder):
        self.status_callback("Creating PDF...")
        pdf_name = f"Kindle_Book_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(self.output_dir, pdf_name)

        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter

        for image_path in image_files:
            img = Image.Image.open(image_path)
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
            kindle_win = self.launch_and_activate_kindle()
            if not kindle_win:
                return False, None
            is_fullscreen = True # Assume fullscreen is active now

            # Step 3: Navigate to first page
            self._navigate_to_first_page()

            self.status_callback(f"Starting screenshots in {delay} seconds...")
            time.sleep(delay)

            # Prepare screenshot folder
            session_id = str(uuid.uuid4())
            screenshots_folder = os.path.join(self.output_dir, "temp_screenshots_" + session_id)
            os.makedirs(screenshots_folder, exist_ok=True)

            # Step 4: Take screenshots
            image_files = self._take_screenshots_and_create_pdf_core(kindle_win, pages, screenshots_folder)

            # Step 5: Create PDF
            pdf_path = self._create_pdf_from_images(image_files, screenshots_folder)

            self.status_callback(f"PDF created successfully: {os.path.basename(pdf_path)}")
            return True, pdf_path

        except Exception as e:
            self.error_callback(f"An error occurred: {str(e)}")
            return False, None
        finally:
            # Ensure we exit full screen mode in case of an error
            if is_fullscreen:
                pyautogui.press('f11')
                time.sleep(0.5) # Give it time to exit fullscreen
            
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
