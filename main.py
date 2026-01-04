import os
import time
import uuid
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import pygetwindow as gw
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import subprocess

class KindleToPdfApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Kindle to PDF")
        self.geometry("400x250") # Increased height for more status text

        self.pages_label = ttk.Label(self, text="Number of pages:")
        self.pages_label.pack(pady=5)

        self.pages_entry = ttk.Entry(self)
        self.pages_entry.insert(0, "10")
        self.pages_entry.pack(pady=5)

        self.start_button = ttk.Button(self, text="Start", command=self.start_process)
        self.start_button.pack(pady=10)

        self.status_label = ttk.Label(self, text="Ready", wraplength=380) # Wrap text
        self.status_label.pack(pady=5)
        
        # Create output directory
        self.output_dir = "Kindle_PDFs"
        os.makedirs(self.output_dir, exist_ok=True)


    def start_process(self):
        try:
            pages = int(self.pages_entry.get())
            if pages <= 0:
                messagebox.showerror("Error", "Please enter a positive number of pages.")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number.")
            return

        self.start_button.config(state=tk.DISABLED)
        thread = threading.Thread(target=self.take_screenshots_and_create_pdf, args=(pages,))
        thread.start()

    def take_screenshots_and_create_pdf(self, pages: int):
        kindle_win = None
        is_fullscreen = False
        try:
            self.status_label.config(text="Finding Kindle app window...")
            self.update_idletasks()
            kindle_windows = gw.getWindowsWithTitle('Kindle')
            if not kindle_windows:
                messagebox.showerror("Error", "Kindle app not found. Please make sure it is running.")
                return

            kindle_win = kindle_windows[0]
            
            self.status_label.config(text="Activating and focusing Kindle window...")
            self.update_idletasks()
            
            if kindle_win.isMinimized:
                kindle_win.restore()
            time.sleep(0.5)
            kindle_win.activate()
            time.sleep(1)

            # Make it full screen
            pyautogui.press('f11')
            is_fullscreen = True
            time.sleep(1)
            
            self.status_label.config(text="Starting screenshots in 3 seconds...")
            self.update_idletasks()
            time.sleep(3)
            
            session_id = str(uuid.uuid4())
            screenshots_folder = os.path.join(self.output_dir, "temp_screenshots_" + session_id)
            os.makedirs(screenshots_folder, exist_ok=True)
            
            image_files = []
            for i in range(pages):
                self.status_label.config(text=f"Taking screenshot {i + 1}/{pages}")
                self.update_idletasks()
                screenshot = pyautogui.screenshot()
                image_path = os.path.join(screenshots_folder, f"page_{i + 1}.png")
                screenshot.save(image_path)
                image_files.append(image_path)

                pyautogui.press('right')
                time.sleep(2)

            self.status_label.config(text="Creating PDF...")
            self.update_idletasks()
            
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
            
            self.status_label.config(text=f"PDF saved as {pdf_name}")
            
            if messagebox.askyesno("Success", f"PDF '{pdf_name}' created successfully!\nDo you want to open the output folder?"):
                subprocess.Popen(f'explorer "{os.path.abspath(self.output_dir)}"')

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            # Ensure we exit full screen mode in case of an error
            if is_fullscreen:
                pyautogui.press('f11')
            
            self.start_button.config(state=tk.NORMAL)
            
            # Clean up temporary screenshot files
            if 'screenshots_folder' in locals() and os.path.exists(screenshots_folder):
                image_files = locals().get('image_files', [])
                for img_file in image_files:
                    if os.path.exists(img_file):
                        os.remove(img_file)
                os.rmdir(screenshots_folder)


if __name__ == "__main__":
    app = KindleToPdfApp()
    app.mainloop()
