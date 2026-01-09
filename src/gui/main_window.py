import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import subprocess
import threading
from .. import config_manager
from .region_selector import RegionSelector
from PIL import Image, ImageTk

class MainWindow(ctk.CTkFrame):
    def __init__(self, master=None):
        super().__init__(master, fg_color="transparent")
        self.master = master
        self.automation = None
        self.test_capture_command = None
        self.preview_image_ref = None
        self.config = {}
        self.is_running = False

        self.create_widgets()
        self.load_settings()
        self.log_message("Welcome! Configure settings and start automation.")

    def create_widgets(self):
        # Create main container with two columns
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # Left panel (Settings)
        self.left_panel = ctk.CTkScrollableFrame(
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
        self.right_panel.grid_rowconfigure(2, weight=1)
        self.right_panel.grid_rowconfigure(3, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        self._create_settings_widgets()
        self._create_control_widgets()

    def _create_settings_widgets(self):
        # Title
        title_label = ctk.CTkLabel(
            self.left_panel,
            text="Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(10, 20), padx=20, anchor="w")

        # Target Settings Section
        self._create_section_header(self.left_panel, "Target Region")

        target_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        target_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.region_detection_mode = ctk.StringVar(value="Automatic")
        self.region_detection_mode.trace_add("write", self._on_region_mode_change)

        self.auto_radio = ctk.CTkRadioButton(
            target_frame,
            text="Automatic Detection",
            variable=self.region_detection_mode,
            value="Automatic",
            font=ctk.CTkFont(size=13)
        )
        self.auto_radio.pack(anchor="w", pady=5)

        self.manual_radio = ctk.CTkRadioButton(
            target_frame,
            text="Manual Selection",
            variable=self.region_detection_mode,
            value="Manual",
            font=ctk.CTkFont(size=13)
        )
        self.manual_radio.pack(anchor="w", pady=5)

        self.select_region_button = ctk.CTkButton(
            target_frame,
            text="Select Area",
            command=self._on_select_region_click,
            height=35,
            corner_radius=8
        )
        self.select_region_button.pack(fill="x", pady=(5, 5))

        self.region_display_label = ctk.CTkLabel(
            target_frame,
            text="Region: Not set",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60")
        )
        self.region_display_label.pack(anchor="w", pady=(5, 0))

        self.test_capture_button = ctk.CTkButton(
            target_frame,
            text="Test Capture",
            command=self._on_test_capture_click,
            height=35,
            corner_radius=8,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40")
        )
        self.test_capture_button.pack(fill="x", pady=(10, 0))

        # Action Parameters Section
        self._create_section_header(self.left_panel, "Action Parameters")

        action_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=(0, 15))

        # Page Turn Direction
        direction_label = ctk.CTkLabel(
            action_frame,
            text="Page Turn Direction:",
            font=ctk.CTkFont(size=12)
        )
        direction_label.pack(anchor="w", pady=(5, 2))

        self.page_turn_direction_var = ctk.StringVar(value="Automatic")
        self.page_turn_direction_combo = ctk.CTkComboBox(
            action_frame,
            variable=self.page_turn_direction_var,
            values=["Automatic", "LtoR", "RtoL"],
            state="readonly",
            height=35,
            corner_radius=8
        )
        self.page_turn_direction_combo.pack(fill="x", pady=(0, 5))

        # Add help text for page turn direction
        direction_help = ctk.CTkLabel(
            action_frame,
            text="💡 Tip: If auto-detection fails, select LtoR (→) or RtoL (←) manually",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray50"),
            wraplength=250,
            justify="left"
        )
        direction_help.pack(anchor="w", pady=(0, 10))

        # Max Pages
        ctk.CTkLabel(
            action_frame,
            text="Max Pages to Capture:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(5, 2))

        self.pages_entry = ctk.CTkEntry(
            action_frame,
            height=35,
            corner_radius=8,
            placeholder_text="100"
        )
        self.pages_entry.pack(fill="x", pady=(0, 10))

        # End Detection Sensitivity
        ctk.CTkLabel(
            action_frame,
            text="End Detect Sensitivity (≥1):",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(5, 2))

        self.end_detection_sensitivity_entry = ctk.CTkEntry(
            action_frame,
            height=35,
            corner_radius=8,
            placeholder_text="3"
        )
        self.end_detection_sensitivity_entry.pack(fill="x", pady=(0, 10))

        # Output Settings Section
        self._create_section_header(self.left_panel, "Output Settings")

        output_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        output_frame.pack(fill="x", padx=20, pady=(0, 15))

        # Output Folder
        ctk.CTkLabel(
            output_frame,
            text="Output Folder:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(5, 2))

        folder_row = ctk.CTkFrame(output_frame, fg_color="transparent")
        folder_row.pack(fill="x", pady=(0, 10))
        folder_row.grid_columnconfigure(0, weight=1)

        self.output_folder_entry = ctk.CTkEntry(
            folder_row,
            height=35,
            corner_radius=8,
            placeholder_text="Kindle_PDFs"
        )
        self.output_folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            folder_row,
            text="Browse",
            command=self._on_browse_folder_click,
            width=80,
            height=35,
            corner_radius=8
        ).grid(row=0, column=1)

        # Filename
        ctk.CTkLabel(
            output_frame,
            text="Filename:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(5, 2))

        self.output_filename_entry = ctk.CTkEntry(
            output_frame,
            height=35,
            corner_radius=8,
            placeholder_text="My_Kindle_Book.pdf"
        )
        self.output_filename_entry.pack(fill="x", pady=(0, 10))

        # Image Format
        ctk.CTkLabel(
            output_frame,
            text="Image Format:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(5, 2))

        self.image_format_var = ctk.StringVar(value="PNG")
        self.image_format_combo = ctk.CTkComboBox(
            output_frame,
            variable=self.image_format_var,
            values=["PNG", "JPEG"],
            state="readonly",
            height=35,
            corner_radius=8,
            command=self._on_image_format_change
        )
        self.image_format_combo.pack(fill="x", pady=(0, 10))

        # JPEG Quality
        ctk.CTkLabel(
            output_frame,
            text="JPEG Quality (0-100):",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(5, 2))

        self.jpeg_quality_entry = ctk.CTkEntry(
            output_frame,
            height=35,
            corner_radius=8,
            placeholder_text="90"
        )
        self.jpeg_quality_entry.pack(fill="x", pady=(0, 10))

        # Optimize Images
        self.optimize_images_var = ctk.BooleanVar(value=True)
        self.optimize_images_checkbox = ctk.CTkCheckBox(
            output_frame,
            text="Optimize Images (Grayscale/Resize)",
            variable=self.optimize_images_var,
            font=ctk.CTkFont(size=12)
        )
        self.optimize_images_checkbox.pack(anchor="w", pady=(5, 10))

        # Delay Settings Section
        self._create_section_header(self.left_panel, "Delay Settings (seconds)")

        delay_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        delay_frame.pack(fill="x", padx=20, pady=(0, 20))

        delays = [
            ("Page Turn:", "page_turn_delay_entry", "3"),
            ("Kindle Startup:", "kindle_startup_delay_entry", "10"),
            ("Window Activation:", "window_activation_delay_entry", "3"),
            ("Fullscreen Toggle:", "fullscreen_delay_entry", "3"),
            ("Go to Home:", "navigation_delay_entry", "7")
        ]

        for label_text, attr_name, placeholder in delays:
            ctk.CTkLabel(
                delay_frame,
                text=label_text,
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", pady=(5, 2))

            entry = ctk.CTkEntry(
                delay_frame,
                height=35,
                corner_radius=8,
                placeholder_text=placeholder
            )
            entry.pack(fill="x", pady=(0, 10))
            setattr(self, attr_name, entry)

    def _create_control_widgets(self):
        # Prerequisites warning
        warning_frame = ctk.CTkFrame(
            self.right_panel,
            corner_radius=10,
            fg_color=("#fff3cd", "#664d03")
        )
        warning_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        warning_icon = ctk.CTkLabel(
            warning_frame,
            text="⚠",
            font=ctk.CTkFont(size=20)
        )
        warning_icon.pack(side="left", padx=(15, 5), pady=10)

        warning_text = ctk.CTkLabel(
            warning_frame,
            text="Before starting:\n1. Open a book in Kindle (NOT just library) and go to the first page\n2. Click on the book page to ensure Kindle has focus\n3. If auto-detection fails, set 'Page Turn Direction' to LtoR or RtoL\n4. Do NOT move mouse or press keys during automation",
            font=ctk.CTkFont(size=10),
            justify="left"
        )
        warning_text.pack(side="left", padx=(5, 15), pady=10, anchor="w")

        # Control Buttons
        button_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        button_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.start_pause_resume_button = ctk.CTkButton(
            button_frame,
            text="Start",
            command=self._on_start_pause_resume_click,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=("#2ecc71", "#27ae60"),
            hover_color=("#27ae60", "#229954")
        )
        self.start_pause_resume_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.stop_button = ctk.CTkButton(
            button_frame,
            text="Stop",
            command=self._on_stop_click,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=("#e74c3c", "#c0392b"),
            hover_color=("#c0392b", "#a93226"),
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=5)

        self.open_folder_button = ctk.CTkButton(
            button_frame,
            text="Open Folder",
            command=self.open_output_folder,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=15),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40")
        )
        self.open_folder_button.grid(row=0, column=2, sticky="ew", padx=(5, 0))

        # Progress Bar
        progress_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        progress_container.grid(row=2, column=0, sticky="ew", padx=20, pady=(5, 10))
        progress_container.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(
            progress_container,
            height=20,
            corner_radius=10
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            progress_container,
            text="0 / 0",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.grid(row=1, column=0)

        # Preview Frame
        preview_container = ctk.CTkFrame(
            self.right_panel,
            corner_radius=10
        )
        preview_container.grid(row=3, column=0, sticky="nsew", padx=20, pady=(5, 10))
        preview_container.grid_rowconfigure(1, weight=1)
        preview_container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            preview_container,
            text="Preview",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        self.preview_image_label = ctk.CTkLabel(
            preview_container,
            text="Preview will appear here",
            font=ctk.CTkFont(size=12)
        )
        self.preview_image_label.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))

        # Log Frame
        log_container = ctk.CTkFrame(
            self.right_panel,
            corner_radius=10
        )
        log_container.grid(row=4, column=0, sticky="nsew", padx=20, pady=(5, 20))
        log_container.grid_rowconfigure(1, weight=1)
        log_container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_container,
            text="Activity Log",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        self.log_text = ctk.CTkTextbox(
            log_container,
            height=150,
            corner_radius=8,
            font=ctk.CTkFont(size=11)
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))

    def _create_section_header(self, parent, text):
        header = ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(pady=(10, 5), padx=20, anchor="w")

    def load_settings(self):
        self.config = config_manager.load_config()
        self.pages_entry.delete(0, "end")
        self.pages_entry.insert(0, str(self.config.get("pages", 100)))
        self.optimize_images_var.set(self.config.get("optimize_images", True))
        self.page_turn_direction_var.set(self.config.get("page_turn_direction", "Automatic"))

        self.page_turn_delay_entry.delete(0, "end")
        self.page_turn_delay_entry.insert(0, str(self.config.get("page_turn_delay", 3)))
        self.kindle_startup_delay_entry.delete(0, "end")
        self.kindle_startup_delay_entry.insert(0, str(self.config.get("kindle_startup_delay", 10)))
        self.window_activation_delay_entry.delete(0, "end")
        self.window_activation_delay_entry.insert(0, str(self.config.get("window_activation_delay", 3)))
        self.fullscreen_delay_entry.delete(0, "end")
        self.fullscreen_delay_entry.insert(0, str(self.config.get("fullscreen_delay", 3)))
        self.navigation_delay_entry.delete(0, "end")
        self.navigation_delay_entry.insert(0, str(self.config.get("navigation_delay", 7)))

        self.region_detection_mode.set(self.config.get("region_detection_mode", "Automatic"))
        manual_region = self.config.get("manual_capture_region")
        if manual_region and isinstance(manual_region, list) and len(manual_region) == 4:
            self.region_display_label.configure(text=f"Region: {manual_region[0]},{manual_region[1]},{manual_region[2]},{manual_region[3]}")
        else:
            self.config["manual_capture_region"] = None
            self.region_display_label.configure(text="Region: Not set")

        self.output_folder_entry.delete(0, "end")
        self.output_folder_entry.insert(0, self.config.get("output_folder", "Kindle_PDFs"))
        self.output_filename_entry.delete(0, "end")
        self.output_filename_entry.insert(0, self.config.get("output_filename", "My_Kindle_Book.pdf"))

        self.image_format_var.set(self.config.get("image_format", "PNG"))
        self.jpeg_quality_entry.delete(0, "end")
        self.jpeg_quality_entry.insert(0, str(self.config.get("jpeg_quality", 90)))
        self.end_detection_sensitivity_entry.delete(0, "end")
        self.end_detection_sensitivity_entry.insert(0, str(self.config.get("end_detection_sensitivity", 3)))

        self._on_region_mode_change()
        self._on_image_format_change()

    def _on_browse_folder_click(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder_entry.delete(0, "end")
            self.output_folder_entry.insert(0, folder)

    def _on_image_format_change(self, *args):
        is_jpeg = self.image_format_var.get() == "JPEG"
        if is_jpeg:
            self.jpeg_quality_entry.configure(state="normal")
        else:
            self.jpeg_quality_entry.configure(state="disabled")

    def _on_start_pause_resume_click(self):
        if not self.automation:
            self.show_error("Automation module not loaded.")
            return

        button_text = self.start_pause_resume_button.cget("text")

        if button_text == "Start":
            try:
                self.log_message("=== Starting Automation ===")
                self.log_message("Validating configuration...")

                current_config = {
                    "pages": int(self.pages_entry.get()),
                    "optimize_images": self.optimize_images_var.get(),
                    "page_turn_direction": self.page_turn_direction_var.get(),
                    "page_turn_delay": float(self.page_turn_delay_entry.get()),
                    "kindle_startup_delay": float(self.kindle_startup_delay_entry.get()),
                    "window_activation_delay": float(self.window_activation_delay_entry.get()),
                    "fullscreen_delay": float(self.fullscreen_delay_entry.get()),
                    "navigation_delay": float(self.navigation_delay_entry.get()),
                    "region_detection_mode": self.region_detection_mode.get(),
                    "manual_capture_region": self.config.get("manual_capture_region"),
                    "output_folder": self.output_folder_entry.get(),
                    "output_filename": self.output_filename_entry.get(),
                    "image_format": self.image_format_var.get(),
                    "jpeg_quality": int(self.jpeg_quality_entry.get()),
                    "end_detection_sensitivity": int(self.end_detection_sensitivity_entry.get())
                }

                if current_config["pages"] <= 0:
                    messagebox.showerror("Validation Error", "Max Pages must be positive.")
                    return
                if not current_config["output_folder"] or not current_config["output_filename"]:
                    messagebox.showerror("Validation Error", "Output folder and filename must be set.")
                    return
                if current_config["region_detection_mode"] == "Manual" and not current_config["manual_capture_region"]:
                    messagebox.showerror("Validation Error", "Manual region mode is active, but no region has been selected.\n\nPlease click 'Select Area' to define the capture region.")
                    return
                if not (0 <= current_config["jpeg_quality"] <= 100):
                    messagebox.showerror("Validation Error", "JPEG Quality must be between 0 and 100.")
                    return
                if not (current_config["end_detection_sensitivity"] >= 1):
                    messagebox.showerror("Validation Error", "End Detection Sensitivity must be 1 or greater.")
                    return

                self.log_message("Configuration validated successfully.")
                self.config = current_config
                config_manager.save_config(self.config)
                self.log_message(f"Settings saved. Max pages: {current_config['pages']}, Region mode: {current_config['region_detection_mode']}")

            except ValueError as e:
                messagebox.showerror("Input Error", f"Please enter valid numbers for pages, delays, and JPEG quality.\n\nDetails: {str(e)}")
                self.log_message(f"Input validation error: {str(e)}")
                return
            except Exception as e:
                messagebox.showerror("Unexpected Error", f"An unexpected error occurred:\n\n{str(e)}")
                self.log_message(f"Unexpected error during validation: {str(e)}")
                return

            try:
                self.is_running = True
                self.start_pause_resume_button.configure(
                    text="Pause",
                    fg_color=("#f39c12", "#e67e22"),
                    hover_color=("#e67e22", "#d35400")
                )
                self.stop_button.configure(state="normal")
                self.set_settings_state("disabled")
                self.update_progress(0, self.config["pages"])
                self.log_message("Starting automation thread...")
                self.log_message("NOTE: Do not move the mouse or press keys during automation.")
                threading.Thread(target=self._run_automation_with_error_handling, daemon=True).start()
            except Exception as e:
                self.log_message(f"Failed to start automation thread: {str(e)}")
                self.show_error(f"Failed to start automation:\n\n{str(e)}")
                self.enable_start_button()

        elif button_text == "Pause":
            self.log_message("Pausing automation...")
            self.automation.pause()
            self.start_pause_resume_button.configure(
                text="Resume",
                fg_color=("#3498db", "#2980b9"),
                hover_color=("#2980b9", "#21618c")
            )
        elif button_text == "Resume":
            self.log_message("Resuming automation...")
            self.automation.resume()
            self.start_pause_resume_button.configure(
                text="Pause",
                fg_color=("#f39c12", "#e67e22"),
                hover_color=("#e67e22", "#d35400")
            )

    def _run_automation_with_error_handling(self):
        try:
            self.automation.run(**self.config)
        except Exception as e:
            error_msg = f"Automation error: {str(e)}"
            self.log_message(error_msg)
            self.master.after(0, lambda: self.show_error(error_msg))
            self.master.after(0, self.enable_start_button)

    def _on_stop_click(self):
        if self.is_running and self.automation:
            self.automation.stop()

    def enable_start_button(self):
        self.is_running = False
        self.start_pause_resume_button.configure(
            text="Start",
            fg_color=("#2ecc71", "#27ae60"),
            hover_color=("#27ae60", "#229954")
        )
        self.stop_button.configure(state="disabled")
        self.set_settings_state("normal")
        self.log_message("Process finished or stopped.")
        self.update_progress(0, 0)
        self.preview_image_label.configure(image=None, text="Preview will appear here")

    def set_settings_state(self, state):
        widgets_to_toggle = [
            self.auto_radio, self.manual_radio, self.select_region_button,
            self.test_capture_button, self.page_turn_direction_combo,
            self.pages_entry, self.end_detection_sensitivity_entry,
            self.output_folder_entry, self.output_filename_entry,
            self.image_format_combo, self.jpeg_quality_entry,
            self.optimize_images_checkbox, self.page_turn_delay_entry,
            self.kindle_startup_delay_entry, self.window_activation_delay_entry,
            self.fullscreen_delay_entry, self.navigation_delay_entry
        ]

        for widget in widgets_to_toggle:
            try:
                widget.configure(state=state)
            except:
                pass

        self._on_region_mode_change()
        self._on_image_format_change()

    def log_message(self, message):
        def append():
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")
        if self.master:
            self.master.after(0, append)

    def _on_region_mode_change(self, *args):
        if self.region_detection_mode.get() == "Manual":
            self.select_region_button.configure(state="normal")
        else:
            self.select_region_button.configure(state="disabled")

    def _on_select_region_click(self):
        self.log_message("Starting region selection... Press ESC to cancel.")
        RegionSelector(self.master, self._on_region_selected)

    def _on_region_selected(self, region):
        if region:
            self.log_message(f"Region selected: {region}")
            self.config['manual_capture_region'] = region
            self.region_display_label.configure(text=f"Region: {region[0]},{region[1]},{region[2]},{region[3]}")
        else:
            self.log_message("Region selection cancelled.")

    def _on_test_capture_click(self):
        self.log_message("Preparing for test capture...")
        test_config = {
            "region_detection_mode": self.region_detection_mode.get(),
            "manual_capture_region": self.config.get("manual_capture_region")
        }
        if test_config["region_detection_mode"] == "Manual" and not test_config["manual_capture_region"]:
            messagebox.showerror("Error", "Manual region mode is active, but no region has been selected.")
            return
        if self.test_capture_command:
            threading.Thread(target=self.test_capture_command, kwargs=test_config).start()
        else:
            self.show_error("Test capture command is not configured.")

    def update_status(self, message):
        self.log_message(f"Status: {message}")

    def update_progress(self, current, total):
        def do_update():
            if total > 0:
                self.progress_bar.set(current / total)
                self.progress_label.configure(text=f"{current} / {total}")
            else:
                self.progress_bar.set(0)
                self.progress_label.configure(text="0 / 0")
        if self.master:
            self.master.after(0, do_update)

    def update_preview(self, image_path):
        def do_update():
            try:
                preview_width = self.preview_image_label.winfo_width()
                preview_height = self.preview_image_label.winfo_height()
                if preview_width < 2 or preview_height < 2:
                    self.master.after(100, do_update)
                    return
                with Image.open(image_path) as img:
                    img.thumbnail((preview_width - 20, preview_height - 20), Image.LANCZOS)
                    photo_img = ImageTk.PhotoImage(img)
                    self.preview_image_label.configure(image=photo_img, text="")
                    self.preview_image_ref = photo_img
            except Exception as e:
                self.log_message(f"Preview Error: {e}")
        if self.master:
            self.master.after(0, do_update)

    def show_error(self, message):
        self.log_message(f"Error: {message}")
        messagebox.showerror("Automation Error", message)

    def show_success_dialog(self, pdf_path):
        self.log_message("Automation finished successfully!")
        if messagebox.askyesno("Success", f"PDF created: {os.path.basename(pdf_path)}\n\nDo you want to open the file?"):
            try:
                os.startfile(pdf_path)
            except Exception as e:
                self.show_error(f"Could not open PDF file: {e}")

    def open_output_folder(self):
        output_dir = self.output_folder_entry.get() or "Kindle_PDFs"
        try:
            os.makedirs(output_dir, exist_ok=True)
            os.startfile(os.path.realpath(output_dir))
        except AttributeError:
            try:
                subprocess.run(['xdg-open', output_dir])
            except FileNotFoundError:
                subprocess.run(['open', output_dir])
        except Exception as e:
            self.show_error(f"Could not open output directory: {e}")
