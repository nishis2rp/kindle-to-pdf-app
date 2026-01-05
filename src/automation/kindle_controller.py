import os
import time
import subprocess
import pyautogui
import pygetwindow as gw
import mss

class KindleController:
    def __init__(self, status_callback=None, error_callback=None):
        self.status_callback = status_callback if status_callback else self._default_status_callback
        self.error_callback = error_callback if error_callback else self._default_error_callback
        self.KINDLE_STARTUP_DELAY = 10
        self.WINDOW_RESTORE_DELAY = 0.5
        self.WINDOW_ACTIVATION_DELAY = 1
        self.FULLSCREEN_DELAY = 1

    def _default_status_callback(self, message):
        print(f"Status: {message}")

    def _default_error_callback(self, message):
        print(f"Error: {message}")

    def start_kindle_app(self):
        self.status_callback("Attempting to start Kindle application...")
        kindle_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Amazon', 'Kindle', 'Kindle.exe')
        
        if not os.path.exists(kindle_path):
            kindle_path_pf = os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Amazon', 'Kindle', 'Kindle.exe')
            if os.path.exists(kindle_path_pf):
                kindle_path = kindle_path_pf
            else:
                self.status_callback("Could not find Kindle.exe to auto-start. Please ensure it is running.")
                return False, None
        
        if kindle_path and os.path.exists(kindle_path):
            try:
                subprocess.Popen(kindle_path)
                self.status_callback(f"Waiting for Kindle to start ({self.KINDLE_STARTUP_DELAY}s)...")
                time.sleep(self.KINDLE_STARTUP_DELAY)
                return True, None
            except Exception as e:
                self.status_callback(f"Failed to start Kindle automatically: {e}")
                return False, f"Failed to start Kindle: {e}"
        return False, None

    def get_monitor_for_window(self, window):
        with mss.mss() as sct:
            for monitor in sct.monitors[1:]:
                window_center_x = window.left + window.width / 2
                window_center_y = window.top + window.height / 2
                if (monitor["left"] <= window_center_x < monitor["left"] + monitor["width"] and
                    monitor["top"] <= window_center_y < monitor["top"] + monitor["height"]):
                    return monitor
        if len(sct.monitors) > 1:
            return sct.monitors[1]
        return None

    def find_and_activate_kindle(self):
        self.status_callback("Finding Kindle app window...")
        kindle_windows = gw.getWindowsWithTitle('Kindle')
        if not kindle_windows:
            self.error_callback("Kindle app window not found. Please ensure it is running and visible.")
            return None, None

        kindle_win = kindle_windows[0]
        
        self.status_callback("Activating and focusing Kindle window...")

        if kindle_win.isMinimized:
            kindle_win.restore()
        time.sleep(self.WINDOW_RESTORE_DELAY)
        kindle_win.activate()
        time.sleep(self.WINDOW_ACTIVATION_DELAY)

        monitor = self.get_monitor_for_window(kindle_win)

        pyautogui.press('f11')
        time.sleep(self.FULLSCREEN_DELAY)
        return kindle_win, monitor

    def launch_and_activate_kindle(self):
        started, error = self.start_kindle_app()
        if error:
            self.error_callback(error)
            return None, None
        
        return self.find_and_activate_kindle()

    def navigate_to_first_page(self):
        self.status_callback("Navigating to the beginning of the book (pressing 'Home' key)...")
        pyautogui.press('home')
        time.sleep(5)
