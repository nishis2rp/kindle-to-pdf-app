"""
Simplified Main Window for Kindle to PDF Converter.
Only essential settings: pages, output folder, and filename.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import subprocess
import threading
from .. import config_manager
from ..constants import Storage, DefaultConfig, GUI
from .region_selector import RegionSelector
from PIL import Image, ImageTk


class MainWindow(ctk.CTkFrame):
    def __init__(self, master=None):
        super().__init__(master, fg_color="transparent")
        self.master = master
        self.automation = None
        self.start_command = None
        self.preview_image_ref = None
        self.config = {}
        self.is_running = False

        self.create_widgets()
        self.load_settings()
        self.log_message("Welcome! Set your preferences and click Start.")

    def create_widgets(self):
        # Create main container with two columns
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # Left panel (Settings)
        self.left_panel = ctk.CTkFrame(
            self,
            corner_radius=15,
            fg_color=("gray90", "gray17")
        )
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Right panel (Control & Preview)
        self.right_panel = ctk.CTkFrame(
            self,
            corner_radius=15,
            fg_color=("gray90", "gray17")
        )
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        # Don't give weight to progress rows, so they stay compact
        # This ensures preview and log are always visible
        self.right_panel.grid_columnconfigure(0, weight=1)

        self._create_settings_widgets()
        self._create_control_widgets()

    def _create_settings_widgets(self):
        """Create simplified settings panel"""
        # Title
        title_label = ctk.CTkLabel(
            self.left_panel,
            text="Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(20, 30), padx=20, anchor="w")

        # Pages Setting
        pages_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        pages_frame.pack(fill="x", padx=20, pady=(0, 20))

        pages_label = ctk.CTkLabel(
            pages_frame,
            text="Max Pages to Capture",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        pages_label.pack(anchor="w", pady=(0, 8))

        self.pages_entry = ctk.CTkEntry(
            pages_frame,
            placeholder_text="100",
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.pages_entry.pack(fill="x")

        # Output Folder Setting
        folder_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        folder_frame.pack(fill="x", padx=20, pady=(0, 20))

        folder_label = ctk.CTkLabel(
            folder_frame,
            text="Output Folder",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        folder_label.pack(anchor="w", pady=(0, 8))

        folder_input_frame = ctk.CTkFrame(folder_frame, fg_color="transparent")
        folder_input_frame.pack(fill="x")

        self.output_folder_entry = ctk.CTkEntry(
            folder_input_frame,
            placeholder_text=Storage.get_default_output_dir(),
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.output_folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.browse_button = ctk.CTkButton(
            folder_input_frame,
            text="Browse",
            command=self._on_browse_click,
            width=80,
            height=40
        )
        self.browse_button.pack(side="right")

        # Output Filename Setting
        filename_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        filename_frame.pack(fill="x", padx=20, pady=(0, 20))

        filename_label = ctk.CTkLabel(
            filename_frame,
            text="Output Filename",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        filename_label.pack(anchor="w", pady=(0, 8))

        self.output_filename_entry = ctk.CTkEntry(
            filename_frame,
            placeholder_text=Storage.get_default_filename(),
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.output_filename_entry.pack(fill="x")

        # Info text
        info_label = ctk.CTkLabel(
            self.left_panel,
            text="Click Start to begin. You'll select\nthe capture area on your Kindle.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        info_label.pack(pady=(20, 10), padx=20)

    def _create_control_widgets(self):
        """Create control panel with start/stop buttons and preview"""
        # Title
        control_title = ctk.CTkLabel(
            self.right_panel,
            text="Control Panel",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        control_title.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")

        # Control buttons frame
        button_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        button_frame.grid(row=1, column=0, pady=(10, 20), padx=20, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        self.start_button = ctk.CTkButton(
            button_frame,
            text="Start",
            command=self._on_start_click,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=10
        )
        self.start_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.stop_button = ctk.CTkButton(
            button_frame,
            text="Stop",
            command=self._on_stop_click,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="gray40",
            hover_color="gray30",
            state="disabled",
            corner_radius=10
        )
        self.stop_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.right_panel)
        self.progress_bar.grid(row=2, column=0, pady=(0, 10), padx=20, sticky="ew")
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            self.right_panel,
            text="Page: 0/0",
            font=ctk.CTkFont(size=13)
        )
        self.progress_label.grid(row=3, column=0, pady=(0, 10), padx=20, sticky="w")

        # Preview
        preview_label = ctk.CTkLabel(
            self.right_panel,
            text="Preview",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        preview_label.grid(row=4, column=0, pady=(10, 5), padx=20, sticky="w")

        self.preview_frame = ctk.CTkFrame(
            self.right_panel,
            corner_radius=10,
            fg_color=("gray85", "gray25"),
            height=270  # Fixed height to keep it compact
        )
        self.preview_frame.grid(row=5, column=0, pady=(0, 10), padx=20, sticky="ew")
        self.preview_frame.grid_propagate(False)  # Prevent frame from resizing to content

        self.preview_label_widget = ctk.CTkLabel(
            self.preview_frame,
            text="No preview yet",
            font=ctk.CTkFont(size=13)
        )
        self.preview_label_widget.pack(expand=True, fill="both", padx=10, pady=10)

        # Activity Log
        log_label = ctk.CTkLabel(
            self.right_panel,
            text="Activity Log",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        log_label.grid(row=6, column=0, pady=(10, 5), padx=20, sticky="w")

        self.log_text = ctk.CTkTextbox(
            self.right_panel,
            height=200,  # Increased from 150 to 200 for better visibility
            wrap="word",
            font=ctk.CTkFont(size=12)
        )
        self.log_text.grid(row=7, column=0, pady=(0, 20), padx=20, sticky="ew")

    def _on_browse_click(self):
        """Handle browse button click"""
        folder = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=self.output_folder_entry.get() or os.getcwd()
        )
        if folder:
            self.output_folder_entry.delete(0, "end")
            self.output_folder_entry.insert(0, folder)

    def _on_start_click(self):
        """Handle start button click"""
        if self.is_running:
            return

        # Validate settings
        try:
            pages = int(self.pages_entry.get() or "100")
            if pages < 1 or pages > 10000:
                raise ValueError("Pages must be between 1 and 10000")
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Invalid page count: {e}")
            return

        output_folder = self.output_folder_entry.get() or DefaultConfig.get_output_folder()
        output_filename = self.output_filename_entry.get() or DefaultConfig.get_output_filename()

        if not output_filename.endswith(".pdf"):
            output_filename += ".pdf"

        # Save settings
        self.save_settings()

        # Disable start button
        self.is_running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

        # Run automation in thread
        def run_automation():
            if self.start_command:
                self.start_command(
                    pages=pages,
                    output_folder=output_folder,
                    output_filename=output_filename
                )

        thread = threading.Thread(target=run_automation, daemon=True)
        thread.start()

    def _on_stop_click(self):
        """Handle stop button click"""
        if self.automation:
            # Get current progress
            progress = self.automation.get_progress()
            current = progress['current_page']
            target = progress['target_pages']
            is_running = progress['is_running']

            # If not running or already at target, just stop
            if not is_running or current >= target:
                self.automation.stop()
                return

            # Show confirmation dialog if not at target page yet
            response = messagebox.askyesno(
                "停止確認 / Stop Confirmation",
                f"まだ終了ページに届いていません / Not at target page yet\n\n"
                f"現在のページ / Current page: {current}\n"
                f"目標ページ / Target pages: {target}\n"
                f"残り / Remaining: {target - current} ページ / pages\n\n"
                f"続けますか？ / Continue?\n\n"
                f"「はい」で続行、「いいえ」で停止します。\n"
                f"Yes to continue, No to stop."
            )

            if not response:  # No - stop the automation
                self.automation.stop()
            # If Yes - do nothing, automation continues

    def enable_start_button(self):
        """Re-enable start button after automation completes"""
        self.is_running = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def update_status(self, message):
        """Update status in log"""
        self.log_message(message)

    def update_progress(self, current, total):
        """Update progress bar and label"""
        if total > 0:
            progress = current / total
            self.progress_bar.set(progress)
            self.progress_label.configure(text=f"Page: {current}/{total}")

    def update_preview(self, image_path):
        """Update preview image"""
        try:
            img = Image.open(image_path)
            img.thumbnail((GUI.PREVIEW_WIDTH, GUI.PREVIEW_HEIGHT), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.preview_image_ref = photo
            self.preview_label_widget.configure(image=photo, text="")
        except Exception as e:
            self.log_message(f"Preview error: {e}")

    def show_error(self, message):
        """Show error message"""
        self.log_message(f"ERROR: {message}")
        messagebox.showerror("Error", message)

    def show_success_dialog(self, pdf_path):
        """Show success dialog with option to open PDF"""
        response = messagebox.askyesno(
            "Success",
            f"PDF created successfully!\n\n{pdf_path}\n\nDo you want to open it?",
            icon="info"
        )
        if response:
            try:
                os.startfile(pdf_path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open PDF: {e}")

    def log_message(self, message):
        """Add message to activity log"""
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def load_settings(self):
        """Load settings from config"""
        self.config = config_manager.load_config()
        self.pages_entry.insert(0, str(self.config.get("pages", 100)))
        self.output_folder_entry.insert(0, self.config.get("output_folder", DefaultConfig.get_output_folder()))
        self.output_filename_entry.insert(0, self.config.get("output_filename", DefaultConfig.get_output_filename()))

    def save_settings(self):
        """Save current settings to config"""
        self.config["pages"] = int(self.pages_entry.get() or "100")
        self.config["output_folder"] = self.output_folder_entry.get() or DefaultConfig.get_output_folder()
        self.config["output_filename"] = self.output_filename_entry.get() or DefaultConfig.get_output_filename()
        config_manager.save_config(self.config)
