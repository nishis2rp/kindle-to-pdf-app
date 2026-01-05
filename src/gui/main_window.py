import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess

class MainWindow(ttk.Frame):
    def __init__(self, master=None, start_command=None, launch_kindle_command=None):
        super().__init__(master)
        self.master = master
        self.start_command = start_command
        self.launch_kindle_command = launch_kindle_command
        self.on_success = None
        self.on_completion = None

        self.create_widgets()
        
    def create_widgets(self):
        self.launch_kindle_button = ttk.Button(self, text="Launch Kindle App", command=self._on_launch_kindle_click)
        self.launch_kindle_button.pack(pady=10)

        self.pages_label = ttk.Label(self, text="Number of pages:")
        self.pages_label.pack(pady=5)

        self.pages_entry = ttk.Entry(self)
        self.pages_entry.insert(0, "10")
        self.pages_entry.pack(pady=5)

        self.start_button = ttk.Button(self, text="Start", command=self._on_start_click)
        self.start_button.pack(pady=10)

        self.status_label = ttk.Label(self, text="Ready", wraplength=380)
        self.status_label.pack(pady=5)

    def _on_launch_kindle_click(self):
        if self.launch_kindle_command:
            self.launch_kindle_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.DISABLED)
            import threading
            thread = threading.Thread(target=self._run_launch_kindle_in_thread)
            thread.start()

    def _run_launch_kindle_in_thread(self):
        try:
            self.launch_kindle_command()
        finally:
            self.master.after(0, self._enable_buttons_after_launch)

    def _enable_buttons_after_launch(self):
        self.launch_kindle_button.config(state=tk.NORMAL)
        self.start_button.config(state=tk.NORMAL)

    def _on_start_click(self):
        try:
            pages = int(self.pages_entry.get())
            if pages <= 0:
                messagebox.showerror("Error", "Please enter a positive number of pages.")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number.")
            return

        self.start_button.config(state=tk.DISABLED)
        self.launch_kindle_button.config(state=tk.DISABLED)
        if self.start_command:
            import threading
            thread = threading.Thread(target=self._run_start_in_thread, args=(pages,))
            thread.start()

    def _run_start_in_thread(self, pages):
        self.start_command(pages)
        self.master.after(0, self._enable_buttons_after_start)

    def _enable_buttons_after_start(self):
        self.start_button.config(state=tk.NORMAL)
        self.launch_kindle_button.config(state=tk.NORMAL)

    def update_status(self, message):
        self.status_label.config(text=message)
        self.master.update_idletasks() # Update GUI from main thread

    def show_error(self, message):
        messagebox.showerror("Error", message)

    def enable_start_button(self):
        self.start_button.config(state=tk.NORMAL)

    def show_success_dialog(self, pdf_path):
        output_dir = os.path.dirname(pdf_path)
        pdf_name = os.path.basename(pdf_path)
        if messagebox.askyesno("Success", f"PDF '{pdf_name}' created successfully!\nDo you want to open the output folder?"):
            subprocess.Popen(f'explorer "{os.path.abspath(output_dir)}"')
