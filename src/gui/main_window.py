import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import threading
from .. import config_manager
from .region_selector import RegionSelector
from PIL import Image, ImageTk

class MainWindow(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
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
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        left_pane = ttk.Frame(paned_window, padding=10)
        paned_window.add(left_pane, weight=1)
        right_pane = ttk.Frame(paned_window, padding=10)
        paned_window.add(right_pane, weight=2)
        self._create_settings_widgets(left_pane)
        self._create_monitoring_widgets(right_pane)

    def _create_settings_widgets(self, parent):
        parent.rowconfigure(3, weight=1)

        target_frame = ttk.LabelFrame(parent, text="Target Settings"); target_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self.region_detection_mode = tk.StringVar(); self.region_detection_mode.trace_add("write", self._on_region_mode_change)
        ttk.Radiobutton(target_frame, text="Automatic Region Detection", variable=self.region_detection_mode, value="Automatic").pack(anchor="w", padx=5) 
        manual_frame = ttk.Frame(target_frame); manual_frame.pack(fill="x", padx=5)
        ttk.Radiobutton(manual_frame, text="Manual Region Selection", variable=self.region_detection_mode, value="Manual").pack(side="left", anchor="w")
        self.select_region_button = ttk.Button(manual_frame, text="Select Area...", command=self._on_select_region_click); self.select_region_button.pack(side="left", padx=5)
        self.test_capture_button = ttk.Button(target_frame, text="Test Capture", command=self._on_test_capture_click); self.test_capture_button.pack(pady=5, padx=5, fill=tk.X)
        self.region_display_label = ttk.Label(target_frame, text="Region: Not set"); self.region_display_label.pack(anchor="w", padx=5, pady=(0, 5))

        action_params_frame = ttk.LabelFrame(parent, text="Action Parameters"); action_params_frame.grid(row=1, column=0, sticky="ew", pady=5)
        action_params_frame.columnconfigure(1, weight=1)
        ttk.Label(action_params_frame, text="Page Turn Direction:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.page_turn_direction_var = tk.StringVar()
        self.page_turn_direction_combo = ttk.Combobox(action_params_frame, textvariable=self.page_turn_direction_var, values=["Automatic", "LtoR", "RtoL"], state="readonly"); self.page_turn_direction_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(action_params_frame, text="Max Pages to Capture:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.pages_entry = ttk.Entry(action_params_frame); self.pages_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(action_params_frame, text="End Detect Sensitivity (>=1):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.end_detection_sensitivity_entry = ttk.Entry(action_params_frame); self.end_detection_sensitivity_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")


        output_frame = ttk.LabelFrame(parent, text="Output Settings"); output_frame.grid(row=2, column=0, sticky="ew", pady=5)
        output_frame.columnconfigure(1, weight=1)
        ttk.Label(output_frame, text="Output Folder:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.output_folder_entry = ttk.Entry(output_frame); self.output_folder_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(output_frame, text="Browse...", command=self._on_browse_folder_click).grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(output_frame, text="Filename:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.output_filename_entry = ttk.Entry(output_frame); self.output_filename_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        
        ttk.Label(output_frame, text="Image Format:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.image_format_var = tk.StringVar()
        self.image_format_combo = ttk.Combobox(output_frame, textvariable=self.image_format_var, values=["PNG", "JPEG"], state="readonly"); self.image_format_combo.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.image_format_combo.bind("<<ComboboxSelected>>", self._on_image_format_change)

        ttk.Label(output_frame, text="JPEG Quality (0-100):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.jpeg_quality_entry = ttk.Entry(output_frame); self.jpeg_quality_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        self.optimize_images_var = tk.BooleanVar()
        self.optimize_images_checkbox = ttk.Checkbutton(output_frame, text="Optimize Images (Grayscale/Resize)", variable=self.optimize_images_var); self.optimize_images_checkbox.grid(row=4, column=0, columnspan=3, sticky="w", padx=5)
        
        delay_frame = ttk.LabelFrame(parent, text="Delay Settings (seconds)"); delay_frame.grid(row=3, column=0, sticky="nsew", pady=5)
        delay_frame.columnconfigure(1, weight=1)
        delays = { "Page Turn": "page_turn_delay_entry", "Kindle Startup": "kindle_startup_delay_entry", "Window Activation": "window_activation_delay_entry", "Fullscreen Toggle": "fullscreen_delay_entry", "Go to Home": "navigation_delay_entry" }
        for i, (text, attr) in enumerate(delays.items()):
            ttk.Label(delay_frame, text=f"{text}:").grid(row=i, column=0, padx=5, pady=2, sticky="w")
            entry = ttk.Entry(delay_frame, width=10); entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew"); setattr(self, attr, entry)

    def _create_monitoring_widgets(self, parent):
        parent.rowconfigure(2, weight=3); parent.rowconfigure(3, weight=1); parent.columnconfigure(0, weight=1)
        button_frame = ttk.Frame(parent); button_frame.grid(row=0, column=0, sticky="ew")
        self.start_pause_resume_button = ttk.Button(button_frame, text="Start", command=self._on_start_pause_resume_click); self.start_pause_resume_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.open_folder_button = ttk.Button(button_frame, text="Open Output Folder", command=self.open_output_folder); self.open_folder_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
        progress_frame = ttk.Frame(parent); progress_frame.grid(row=1, column=0, sticky="ew", pady=5); progress_frame.columnconfigure(0, weight=1)
        self.progress_bar = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate'); self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.progress_label = ttk.Label(progress_frame, text="0 / 0"); self.progress_label.grid(row=0, column=1, padx=(5, 0))
        preview_frame = ttk.LabelFrame(parent, text="Preview"); preview_frame.grid(row=2, column=0, sticky="nsew", pady=(5, 5)); preview_frame.rowconfigure(0, weight=1); preview_frame.columnconfigure(0, weight=1)
        self.preview_image_label = ttk.Label(preview_frame, text="Preview will appear here."); self.preview_image_label.grid(row=0, column=0, sticky="nsew")
        log_frame = ttk.LabelFrame(parent, text="Log"); log_frame.grid(row=3, column=0, sticky="nsew", pady=(5, 0)); log_frame.rowconfigure(0, weight=1); log_frame.columnconfigure(0, weight=1)
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=10, state='disabled'); self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview); log_scrollbar.grid(row=0, column=1, sticky="ns"); self.log_text['yscrollcommand'] = log_scrollbar.set

    def load_settings(self):
        self.config = config_manager.load_config()
        self.pages_entry.delete(0, tk.END); self.pages_entry.insert(0, str(self.config.get("pages", 100)))
        self.optimize_images_var.set(self.config.get("optimize_images", True))
        self.page_turn_direction_var.set(self.config.get("page_turn_direction", "Automatic"))
        self.page_turn_delay_entry.delete(0, tk.END); self.page_turn_delay_entry.insert(0, str(self.config.get("page_turn_delay", 1.5)))
        self.kindle_startup_delay_entry.delete(0, tk.END); self.kindle_startup_delay_entry.insert(0, str(self.config.get("kindle_startup_delay", 10)))
        self.window_activation_delay_entry.delete(0, tk.END); self.window_activation_delay_entry.insert(0, str(self.config.get("window_activation_delay", 3)))
        self.fullscreen_delay_entry.delete(0, tk.END); self.fullscreen_delay_entry.insert(0, str(self.config.get("fullscreen_delay", 3)))
        self.navigation_delay_entry.delete(0, tk.END); self.navigation_delay_entry.insert(0, str(self.config.get("navigation_delay", 7)))
        self.region_detection_mode.set(self.config.get("region_detection_mode", "Automatic"))
        manual_region = self.config.get("manual_capture_region")
        if manual_region and isinstance(manual_region, list) and len(manual_region) == 4:
            self.region_display_label.config(text=f"Region: {manual_region[0]},{manual_region[1]},{manual_region[2]},{manual_region[3]}")
        else: self.config["manual_capture_region"] = None; self.region_display_label.config(text="Region: Not set")
        self.output_folder_entry.delete(0, tk.END); self.output_folder_entry.insert(0, self.config.get("output_folder", "Kindle_PDFs"))
        self.output_filename_entry.delete(0, tk.END); self.output_filename_entry.insert(0, self.config.get("output_filename", "My_Kindle_Book.pdf"))
        
        self.image_format_var.set(self.config.get("image_format", "PNG"))
        self.jpeg_quality_entry.delete(0, tk.END); self.jpeg_quality_entry.insert(0, str(self.config.get("jpeg_quality", 90)))
        self.end_detection_sensitivity_entry.delete(0, tk.END); self.end_detection_sensitivity_entry.insert(0, str(self.config.get("end_detection_sensitivity", 3)))

        self._on_region_mode_change()
        self._on_image_format_change()

    def _on_browse_folder_click(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder_entry.delete(0, tk.END)
            self.output_folder_entry.insert(0, folder)

    def _on_image_format_change(self, *args):
        is_jpeg = self.image_format_var.get() == "JPEG"
        self.jpeg_quality_entry.config(state="normal" if is_jpeg else "disabled")

    def _on_start_pause_resume_click(self):
        if not self.automation: self.show_error("Automation module not loaded."); return
        button_text = self.start_pause_resume_button.cget("text")
        if button_text == "Start":
            try:
                current_config = { "pages": int(self.pages_entry.get()), "optimize_images": self.optimize_images_var.get(),
                                   "page_turn_direction": self.page_turn_direction_var.get(),
                                   "page_turn_delay": float(self.page_turn_delay_entry.get()), "kindle_startup_delay": float(self.kindle_startup_delay_entry.get()),
                                   "window_activation_delay": float(self.window_activation_delay_entry.get()), "fullscreen_delay": float(self.fullscreen_delay_entry.get()),
                                   "navigation_delay": float(self.navigation_delay_entry.get()), "region_detection_mode": self.region_detection_mode.get(),
                                   "manual_capture_region": self.config.get("manual_capture_region"),
                                   "output_folder": self.output_folder_entry.get(), "output_filename": self.output_filename_entry.get(),
                                   "image_format": self.image_format_var.get(), "jpeg_quality": int(self.jpeg_quality_entry.get()),
                                   "end_detection_sensitivity": int(self.end_detection_sensitivity_entry.get()) }

                if current_config["pages"] <= 0: messagebox.showerror("Error", "Max Pages must be positive."); return
                if not current_config["output_folder"] or not current_config["output_filename"]: messagebox.showerror("Error", "Output folder and filename must be set."); return
                if current_config["region_detection_mode"] == "Manual" and not current_config["manual_capture_region"]:
                    messagebox.showerror("Error", "Manual region mode is active, but no region has been selected."); return
                if not (0 <= current_config["jpeg_quality"] <= 100):
                    messagebox.showerror("Error", "JPEG Quality must be between 0 and 100."); return
                if not (current_config["end_detection_sensitivity"] >= 1):
                    messagebox.showerror("Error", "End Detection Sensitivity must be 1 or greater."); return

                self.config = current_config; config_manager.save_config(self.config)
            except (ValueError, TypeError): messagebox.showerror("Error", "Please enter valid numbers for pages, delays, and JPEG quality."); return
            self.is_running = True; self.start_pause_resume_button.config(text="Pause"); self.stop_button.config(state="normal"); self.set_settings_state("disabled"); self.update_progress(0, self.config["pages"])
            threading.Thread(target=self.automation.run, kwargs=self.config).start()
        elif button_text == "Pause": self.automation.pause(); self.start_pause_resume_button.config(text="Resume")
        elif button_text == "Resume": self.automation.resume(); self.start_pause_resume_button.config(text="Pause")

    def _on_stop_click(self):
        if self.is_running and self.automation: self.automation.stop()

    def enable_start_button(self):
        self.is_running = False; self.start_pause_resume_button.config(text="Start"); self.stop_button.config(state="disabled"); self.set_settings_state("normal"); self.log_message("Process finished or stopped."); self.update_progress(0, 0); self.preview_image_label.config(image=None, text="Preview will appear here.")

    def set_settings_state(self, state):
        for child in self.winfo_children():
            if isinstance(child, ttk.PanedWindow):
                left_pane = child.pane(0)
                for widget_name in left_pane.winfo_children():
                    widget = self.nametowidget(widget_name)
                    # Skip radio buttons in Target Settings and other specific widgets
                    if widget is self.select_region_button and self.region_detection_mode.get() == "Manual":
                        widget.config(state="normal" if state == "normal" else "disabled")
                        continue
                    if widget is self.jpeg_quality_entry and self.image_format_var.get() == "JPEG":
                        widget.config(state="normal" if state == "normal" else "disabled")
                        continue

                    try: widget.config(state=state)
                    except tk.TclError:
                        for sub_widget in widget.winfo_children():
                            try: sub_widget.config(state=state)
                            except tk.TclError: pass
                break
        # Special handling for radio buttons
        for child in self.nametowidget("!mainwindow.!panedwindow.!frame.!labelframe").winfo_children():
            if isinstance(child, ttk.Radiobutton): child.config(state="normal")
            if isinstance(child, ttk.Frame):
                for sub_child in child.winfo_children():
                    if isinstance(sub_child, ttk.Radiobutton): sub_child.config(state="normal")
        self._on_region_mode_change() # Update select_region_button state based on mode
        self._on_image_format_change() # Update jpeg_quality_entry state based on format


    def log_message(self, message):
        def append(): self.log_text.configure(state='normal'); self.log_text.insert(tk.END, message + "\n"); self.log_text.see(tk.END); self.log_text.configure(state='disabled')
        if self.master: self.master.after(0, append)

    def _on_region_mode_change(self, *args): self.select_region_button.config(state="normal" if self.region_detection_mode.get() == "Manual" else "disabled")
    def _on_select_region_click(self): self.log_message("Starting region selection... Press ESC to cancel."); RegionSelector(self.master, self._on_region_selected)
    def _on_region_selected(self, region):
        if region: self.log_message(f"Region selected: {region}"); self.config['manual_capture_region'] = region; self.region_display_label.config(text=f"Region: {region[0]},{region[1]},{region[2]},{region[3]}")
        else: self.log_message("Region selection cancelled.")

    def _on_test_capture_click(self):
        self.log_message("Preparing for test capture...")
        test_config = { "region_detection_mode": self.region_detection_mode.get(), "manual_capture_region": self.config.get("manual_capture_region") }
        if test_config["region_detection_mode"] == "Manual" and not test_config["manual_capture_region"]: messagebox.showerror("Error", "Manual region mode is active, but no region has been selected."); return
        if self.test_capture_command: threading.Thread(target=self.test_capture_command, kwargs=test_config).start()
        else: self.show_error("Test capture command is not configured.")

    def update_status(self, message): self.log_message(f"Status: {message}")
    
    def update_progress(self, current, total):
        def do_update():
            if total > 0: self.progress_bar['maximum'] = total; self.progress_bar['value'] = current; self.progress_label.config(text=f"{current} / {total}")
            else: self.progress_bar['value'] = 0; self.progress_label.config(text="0 / 0")
        if self.master: self.master.after(0, do_update)

    def update_preview(self, image_path):
        def do_update():
            try:
                preview_width = self.preview_image_label.winfo_width(); preview_height = self.preview_image_label.winfo_height()
                if preview_width < 2 or preview_height < 2: self.master.after(100, do_update); return
                with Image.open(image_path) as img:
                    img.thumbnail((preview_width - 10, preview_height - 10), Image.LANCZOS)
                    photo_img = ImageTk.PhotoImage(img); self.preview_image_label.config(image=photo_img, text=""); self.preview_image_ref = photo_img
            except Exception as e: self.log_message(f"Preview Error: {e}")
        if self.master: self.master.after(0, do_update)

    def show_error(self, message): self.log_message(f"Error: {message}"); messagebox.showerror("Automation Error", message)
    def show_success_dialog(self, pdf_path):
        self.log_message("Automation finished successfully!")
        if messagebox.askyesno("Success", f"PDF created: {os.path.basename(pdf_path)}\n\nDo you want to open the file?"):
            try: os.startfile(pdf_path)
            except Exception as e: self.show_error(f"Could not open PDF file: {e}")

    def open_output_folder(self):
        output_dir = self.output_folder_entry.get() or "Kindle_PDFs"
        try: os.makedirs(output_dir, exist_ok=True); os.startfile(os.path.realpath(output_dir))
        except AttributeError:
            try: subprocess.run(['xdg-open', output_dir])
            except FileNotFoundError: subprocess.run(['open', output_dir])
        except Exception as e: self.show_error(f"Could not open output directory: {e}")
