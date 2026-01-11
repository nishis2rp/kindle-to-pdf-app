"""
Main application entry point for Kindle to PDF converter.
"""

import customtkinter as ctk
from src.constants import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
from src.gui.main_window import MainWindow
from src.automation.automation_coordinator import AutomationCoordinator
from src.hotkey_listener import start_hotkey_listener

def main():
    """Initialize and run the Kindle to PDF application"""
    # Set appearance mode and color theme
    ctk.set_appearance_mode("System")  # Modes: system, light, dark
    ctk.set_default_color_theme("blue")  # Themes: blue, dark-blue, green

    root = ctk.CTk()
    root.title("Kindle to PDF")

    # Window dimensions and positioning
    window_width = DEFAULT_WINDOW_WIDTH
    window_height = DEFAULT_WINDOW_HEIGHT
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f'{window_width}x{window_height}+{x}+{y}')

    # Set minimum window size (increased height to ensure log is always visible)
    root.minsize(900, 700)

    main_window_frame = MainWindow(master=root)
    main_window_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Create the automation coordinator and link its callbacks to the GUI
    automation = AutomationCoordinator(
        status_callback=main_window_frame.update_status,
        error_callback=main_window_frame.show_error,
        success_callback=main_window_frame.show_success_dialog,
        completion_callback=main_window_frame.enable_start_button,
        preview_callback=main_window_frame.update_preview,
        progress_callback=main_window_frame.update_progress,
        root_window=root
    )

    # Set the command that the GUI's start button will execute
    main_window_frame.start_command = automation.run
    main_window_frame.automation = automation # Give the GUI a reference to the coordinator

    # Start the global hotkey listener
    start_hotkey_listener(automation.stop)

    root.mainloop()

if __name__ == "__main__":
    main()
