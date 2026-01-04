import tkinter as tk
from tkinter import messagebox
import threading
import os

from src.gui.main_window import MainWindow
from src.automation.screenshot import ScreenshotAutomation

class KindleToPdfApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kindle to PDF")
        self.geometry("400x250")

        self.main_window = MainWindow(master=self, start_command=self._start_automation_process)
        self.main_window.pack(expand=True, fill="both")

        self.automation = ScreenshotAutomation(
            status_callback=self._update_status_gui,
            error_callback=self._show_error_gui,
            root_window=self # Pass self (the Tkinter root window)
        )

        # Create output directory for PDFs if it doesn't exist
        os.makedirs(self.automation.output_dir, exist_ok=True)

    def _update_status_gui(self, message):
        self.main_window.update_status(message)

    def _show_error_gui(self, message):
        self.main_window.show_error(message)

    def _start_automation_process(self, pages: int):
        # Run the automation in a separate thread to keep the GUI responsive
        thread = threading.Thread(target=self._run_automation_in_thread, args=(pages,))
        thread.start()

    def _run_automation_in_thread(self, pages: int):
        success, pdf_path = self.automation.run(pages)
        if success and pdf_path:
            self.main_window.show_success_dialog(pdf_path)
        self.main_window.enable_start_button()

if __name__ == "__main__":
    app = KindleToPdfApp()
    app.mainloop()
