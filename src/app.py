import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from .gui.main_window import MainWindow
from .automation.automation_coordinator import AutomationCoordinator

def main():
    root = ThemedTk(theme="adapta")
    root.title("Kindle to PDF App")

    window_width = 500
    window_height = 400
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f'{window_width}x{window_height}+{x}+{y}')

    main_window_frame = MainWindow(master=root)
    main_window_frame.pack(fill=tk.BOTH, expand=True)

    automation = AutomationCoordinator(
        status_callback=main_window_frame.update_status,
        error_callback=main_window_frame.show_error,
        success_callback=main_window_frame.show_success_dialog,
        completion_callback=main_window_frame.enable_start_button,
        root_window=root
    )

    main_window_frame.start_command = automation.run


    root.mainloop()

if __name__ == "__main__":
    main()
