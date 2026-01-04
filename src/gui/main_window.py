import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess

class MainWindow(ttk.Frame):
    def __init__(self, master=None, start_command=None):
        super().__init__(master)
        self.master = master
        self.start_command = start_command # Callback for starting the process

        self.create_widgets()
        
    def create_widgets(self):
        self.pages_label = ttk.Label(self, text="Number of pages:")
        self.pages_label.pack(pady=5)

        self.pages_entry = ttk.Entry(self)
        self.pages_entry.insert(0, "10")
        self.pages_entry.pack(pady=5)

        self.start_button = ttk.Button(self, text="Start", command=self._on_start_click)
        self.start_button.pack(pady=10)

        self.status_label = ttk.Label(self, text="Ready", wraplength=380)
        self.status_label.pack(pady=5)

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
        if self.start_command:
            self.start_command(pages)

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
