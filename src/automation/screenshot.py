import os
import time
import uuid
import pyautogui
import pygetwindow as gw
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import subprocess

class ScreenshotAutomation:
    def __init__(self, output_dir="Kindle_PDFs", status_callback=None, error_callback=None):
        self.output_dir = output_dir
        self.status_callback = status_callback if status_callback else self._default_status_callback
        self.error_callback = error_callback if error_callback else self._default_error_callback
        os.makedirs(self.output_dir, exist_ok=True)

    def _default_status_callback(self, message):
        print(f"Status: {message}")

    def _default_error_callback(self, message):
        print(f"Error: {message}")

    def run(self, pages: int, delay: int = 3):
        kindle_win = None
        is_fullscreen = False
        screenshots_folder = None
        try:
            # --- New: Auto-start Kindle ---
            self.status_callback("Attempting to start Kindle application...")
            kindle_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Amazon', 'Kindle', 'Kindle.exe')
            
            if not os.path.exists(kindle_path):
                kindle_path_pf = os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Amazon', 'Kindle', 'Kindle.exe')
                if os.path.exists(kindle_path_pf):
                    kindle_path = kindle_path_pf
                else:
                    self.status_callback("Could not find Kindle.exe to auto-start. Please ensure it is running.")
                    kindle_path = None # Will proceed and try to find window anyway

            if kindle_path:
                try:
                    subprocess.Popen(kindle_path)
                    self.status_callback("Waiting for Kindle to start (10s)...")
                    time.sleep(10)
                except Exception as e:
                    self.status_callback(f"Failed to start Kindle automatically: {e}")
            # --- End of new code ---

            self.status_callback("Finding Kindle app window...")
            kindle_windows = gw.getWindowsWithTitle('Kindle')
            if not kindle_windows:
                self.error_callback("Kindle app not found. Please make sure it is running.")
                return False, None

            kindle_win = kindle_windows[0]
            
            self.status_callback("Activating and focusing Kindle window...")
            
            if kindle_win.isMinimized:
                kindle_win.restore()
            time.sleep(0.5)
            kindle_win.activate()
            time.sleep(1)

            # Make it full screen
            pyautogui.press('f11')
            is_fullscreen = True
            time.sleep(1)
            
            self.status_callback(f"Starting screenshots in {delay} seconds...")
            time.sleep(delay)
            
            session_id = str(uuid.uuid4())
            screenshots_folder = os.path.join(self.output_dir, "temp_screenshots_" + session_id)
            os.makedirs(screenshots_folder, exist_ok=True)
            
            image_files = []
            for i in range(pages):
                self.status_callback(f"Taking screenshot {i + 1}/{pages}")
                screenshot = pyautogui.screenshot()
                image_path = os.path.join(screenshots_folder, f"page_{i + 1}.png")
                screenshot.save(image_path)
                image_files.append(image_path)

                pyautogui.press('right')
                time.sleep(2)

            self.status_callback("Creating PDF...")
            
            # Exit full screen before showing success message
            pyautogui.press('f11')
            is_fullscreen = False
            time.sleep(0.5)
            if kindle_win:
                kindle_win.activate() # Refocus after f11

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
            
            self.status_callback(f"PDF saved as {pdf_name}")
            return True, pdf_path

        except Exception as e:
            self.error_callback(f"An error occurred: {str(e)}")
            return False, None
        finally:
            # Ensure we exit full screen mode in case of an error
            if is_fullscreen:
                pyautogui.press('f11')
            
            # Clean up temporary screenshot files
            if screenshots_folder and os.path.exists(screenshots_folder):
                image_files_to_clean = []
                for f in os.listdir(screenshots_folder):
                    if f.endswith(".png"):
                        image_files_to_clean.append(os.path.join(screenshots_folder, f))
                for img_file in image_files_to_clean:
                    if os.path.exists(img_file):
                        os.remove(img_file)
                os.rmdir(screenshots_folder)
