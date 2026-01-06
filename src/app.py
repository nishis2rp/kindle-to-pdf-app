import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from .gui.main_window import MainWindow
from .automation.automation_coordinator import AutomationCoordinator
from .hotkey_listener import start_hotkey_listener

def main():
    root = ThemedTk(theme="adapta")
    root.title("Kindle to PDF App")

    window_width = 900
    window_height = 600
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f'{window_width}x{window_height}+{x}+{y}')

    main_window_frame = MainWindow(master=root)
    main_window_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

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
    main_window_frame.test_capture_command = automation.test_capture
    main_window_frame.automation = automation # Give the GUI a reference to the coordinator

    # Start the global hotkey listener
    start_hotkey_listener(automation.stop)

    root.mainloop()

if __name__ == "__main__":
    main()
