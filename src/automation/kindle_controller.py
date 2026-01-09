import os
import time
import subprocess
import pyautogui
import pygetwindow as gw
import mss
import cv2 # OpenCVをインポート
import numpy as np # OpenCVで画像データを扱うため
from PIL import Image # PIL.Imageをインポート

class KindleController:
    """
    Controller for automating Kindle for PC application.
    Handles window detection, activation, and interaction.
    """

    # Default delay constants (in seconds)
    DEFAULT_KINDLE_STARTUP_DELAY = 10
    DEFAULT_WINDOW_RESTORE_DELAY = 0.5
    DEFAULT_WINDOW_ACTIVATION_DELAY = 3
    DEFAULT_FULLSCREEN_DELAY = 3
    DEFAULT_NAVIGATION_DELAY = 7
    DEFAULT_PAGE_TURN_DELAY = 3  # Increased from 2 to 3 for better reliability

    # PyAutoGUI configuration
    PYAUTOGUI_PAUSE = 0.1
    PYAUTOGUI_FAILSAFE = True

    # Book region detection
    BOOK_REGION_MARGIN = 5  # pixels
    MIN_BOOK_REGION_SIZE = 0.15  # 15% of window area (lowered for better compatibility)

    # Hash comparison threshold for page detection
    # Using mean grayscale value (0-255), so threshold should be lower for better sensitivity
    HASH_DIFF_THRESHOLD = 2.0  # Lowered from 5.0 to detect subtle page changes

    def __init__(self, status_callback=None, error_callback=None):
        """
        Initialize Kindle controller

        Args:
            status_callback: Function to call with status messages
            error_callback: Function to call with error messages
        """
        self.status_callback = status_callback if status_callback else self._default_status_callback
        self.error_callback = error_callback if error_callback else self._default_error_callback

        # Set instance delay values (can be overridden)
        self.KINDLE_STARTUP_DELAY = self.DEFAULT_KINDLE_STARTUP_DELAY
        self.WINDOW_RESTORE_DELAY = self.DEFAULT_WINDOW_RESTORE_DELAY
        self.WINDOW_ACTIVATION_DELAY = self.DEFAULT_WINDOW_ACTIVATION_DELAY
        self.FULLSCREEN_DELAY = self.DEFAULT_FULLSCREEN_DELAY
        self.NAVIGATION_DELAY = self.DEFAULT_NAVIGATION_DELAY
        self.PAGE_TURN_DELAY = self.DEFAULT_PAGE_TURN_DELAY

        # Configure PyAutoGUI
        pyautogui.PAUSE = self.PYAUTOGUI_PAUSE
        pyautogui.FAILSAFE = self.PYAUTOGUI_FAILSAFE

    def _default_status_callback(self, message):
        print(f"Status: {message}")

    def _default_error_callback(self, message):
        print(f"Error: {message}")

    def is_kindle_running(self):
        """Check if Kindle app is already running"""
        try:
            all_windows = gw.getAllWindows()
            for window in all_windows:
                if not window.title:  # Skip windows with no title
                    continue

                title = window.title.lower()
                # Check if it's a Kindle window (but not our own app)
                if ('kindle' in title and
                    'kindle to pdf' not in title and  # Our app name
                    'kindle-to-pdf' not in title and  # Our app name variation
                    'kindletopdf' not in title and    # Our app name variation
                    not window.title.startswith('C:\\') and  # Filter out file paths
                    window.visible):  # Must be visible
                    return True
            return False
        except Exception as e:
            self.status_callback(f"Warning: Error checking if Kindle is running: {e}")
            return False

    def find_kindle_exe(self):
        """Find Kindle.exe in common installation locations"""
        localappdata = os.environ.get('LOCALAPPDATA', '')
        programfiles_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')
        programfiles = os.environ.get('ProgramFiles', 'C:\\Program Files')
        username = os.environ.get('USERNAME', '')

        possible_paths = [
            # Most common location
            os.path.join(localappdata, 'Amazon', 'Kindle', 'application', 'Kindle.exe'),
            # Alternative locations
            os.path.join(localappdata, 'Amazon', 'Kindle', 'Kindle.exe'),
            os.path.join(programfiles_x86, 'Amazon', 'Kindle', 'Kindle.exe'),
            os.path.join(programfiles, 'Amazon', 'Kindle', 'Kindle.exe'),
            f'C:\\Users\\{username}\\AppData\\Local\\Amazon\\Kindle\\application\\Kindle.exe',
        ]

        self.status_callback("Searching for Kindle.exe in standard locations...")
        for path in possible_paths:
            if path and os.path.exists(path):
                self.status_callback(f"Found Kindle.exe at: {path}")
                return path
            else:
                self.status_callback(f"Not found at: {path}")

        return None

    def start_kindle_app(self):
        """Start Kindle application if not already running"""
        # Check if Kindle is already running
        if self.is_kindle_running():
            self.status_callback("Kindle is already running. Using existing window.")
            return True, None

        self.status_callback("Kindle is not running. Attempting to start Kindle application...")
        kindle_path = self.find_kindle_exe()

        if not kindle_path:
            error_msg = (
                "Could not find Kindle.exe in standard installation locations.\n\n"
                "Searched locations:\n"
                "- %LOCALAPPDATA%\\Amazon\\Kindle\\application\\Kindle.exe\n"
                "- %LOCALAPPDATA%\\Amazon\\Kindle\\Kindle.exe\n"
                "- Program Files (x86)\\Amazon\\Kindle\\Kindle.exe\n"
                "- Program Files\\Amazon\\Kindle\\Kindle.exe\n\n"
                "Please either:\n"
                "1. Install Kindle for PC from Amazon, OR\n"
                "2. Start Kindle manually and open a book before starting automation"
            )
            self.error_callback(error_msg)
            return False, error_msg

        try:
            self.status_callback(f"Launching Kindle from: {kindle_path}")

            # Use startupinfo to hide console window on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            process = subprocess.Popen(
                [kindle_path],
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            self.status_callback(f"Kindle process started (PID: {process.pid})")
            self.status_callback(f"Waiting {self.KINDLE_STARTUP_DELAY} seconds for Kindle to fully start...")

            # Wait and check periodically if Kindle window appears
            check_interval = 2  # Check every 2 seconds
            max_checks = int(self.KINDLE_STARTUP_DELAY / check_interval)

            for i in range(max_checks):
                time.sleep(check_interval)
                if self.is_kindle_running():
                    self.status_callback(f"Kindle window detected after {(i+1)*check_interval} seconds!")
                    # Give it a bit more time to fully initialize
                    time.sleep(2)
                    self.status_callback("Kindle started successfully.")
                    return True, None
                else:
                    self.status_callback(f"Waiting... ({(i+1)*check_interval}/{self.KINDLE_STARTUP_DELAY}s)")

            # Final check after full delay
            if self.is_kindle_running():
                self.status_callback("Kindle started successfully.")
                return True, None
            else:
                error_msg = (
                    f"Kindle.exe was launched but no window appeared after {self.KINDLE_STARTUP_DELAY} seconds.\n\n"
                    "Possible issues:\n"
                    "1. Kindle may be starting slowly - try increasing 'Kindle Startup Delay' in settings\n"
                    "2. Kindle may have opened minimized - check your taskbar\n"
                    "3. Kindle may require login - please start it manually first\n\n"
                    "Recommendation: Start Kindle manually, log in if needed, and open a book before using automation."
                )
                self.error_callback(error_msg)
                return False, error_msg

        except FileNotFoundError:
            error_msg = f"Kindle.exe not found at: {kindle_path}\nPlease reinstall Kindle for PC."
            self.error_callback(error_msg)
            return False, error_msg
        except PermissionError:
            error_msg = f"Permission denied when trying to launch Kindle.\nPlease run this app as administrator."
            self.error_callback(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Failed to start Kindle: {type(e).__name__}: {e}"
            self.error_callback(error_msg)
            import traceback
            self.status_callback(f"Traceback: {traceback.format_exc()}")
            return False, error_msg

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

    def _get_kindle_window(self):
        self.status_callback("Finding Kindle app window...")

        try:
            # Find all windows and filter for actual Kindle windows
            all_windows = gw.getAllWindows()
            kindle_windows = []

            self.status_callback(f"Scanning {len(all_windows)} windows for Kindle...")

            for window in all_windows:
                if not window.title:  # Skip windows with no title
                    continue

                title_lower = window.title.lower()
                # Check if it's a Kindle window (but not our own app or empty)
                # Filter out: our app name, file paths, and empty titles
                if ('kindle' in title_lower and
                    'kindle to pdf' not in title_lower and  # Our app name
                    'kindletopdf' not in title_lower and
                    'kindle-to-pdf' not in title_lower and
                    not window.title.startswith('C:\\') and  # Filter out file paths
                    window.title.strip() and
                    window.visible and
                    window.width > 100 and  # Reasonable window size
                    window.height > 100):
                    kindle_windows.append(window)
                    self.status_callback(f"Found candidate: '{window.title}' (size: {window.width}x{window.height})")

            if not kindle_windows:
                error_msg = (
                    "Kindle app window not found.\n\n"
                    "Please ensure:\n"
                    "1. Kindle for PC is installed and running\n"
                    "2. You are logged into your Amazon account\n"
                    "3. A book is open (not just the library view)\n"
                    "4. The Kindle window is not minimized"
                )
                self.error_callback(error_msg)
                return None

            # Use the first valid Kindle window
            main_window = kindle_windows[0]
            window_title = main_window.title

            if len(kindle_windows) > 1:
                self.status_callback(f"Found {len(kindle_windows)} Kindle windows, using: '{window_title}'")

            if window_title.strip().lower() == 'kindle':
                self.status_callback("WARNING: Kindle is running but no book appears to be open.")
                self.status_callback("Window title is just 'Kindle' - please open a book before starting.")
                # Don't return None here, let user proceed but warn them
            else:
                # Safely display window title
                try:
                    self.status_callback(f"Found Kindle window: '{window_title}'")
                except UnicodeEncodeError:
                    self.status_callback(f"Found Kindle window (title contains special characters)")

            return main_window

        except Exception as e:
            error_msg = f"Error while searching for Kindle window: {type(e).__name__}: {e}"
            self.error_callback(error_msg)
            import traceback
            self.status_callback(f"Traceback: {traceback.format_exc()}")
            return None

    def find_and_activate_kindle(self):
        kindle_win = self._get_kindle_window()
        if not kindle_win:
            return None, None

        self.status_callback("Activating and focusing Kindle window...")

        # Log window position for debugging multi-monitor setups
        self.status_callback(f"Window position: ({kindle_win.left}, {kindle_win.top}), "
                           f"size: {kindle_win.width}x{kindle_win.height}")

        if kindle_win.isMinimized:
            kindle_win.restore()
            time.sleep(self.WINDOW_RESTORE_DELAY)

        monitor = self.get_monitor_for_window(kindle_win)
        if monitor:
            self.status_callback(f"Window is on monitor: left={monitor['left']}, top={monitor['top']}, "
                               f"size={monitor['width']}x{monitor['height']}")

        # Calculate window center (works with negative coordinates for multi-monitor)
        window_center_x = kindle_win.left + kindle_win.width // 2
        window_center_y = kindle_win.top + kindle_win.height // 2

        # Move mouse to window first (important for multi-monitor setups)
        try:
            self.status_callback(f"Moving cursor to window center: ({window_center_x}, {window_center_y})")
            pyautogui.moveTo(window_center_x, window_center_y, duration=0.3)
            time.sleep(0.2)
        except Exception as e:
            self.status_callback(f"Cursor move warning: {e}")

        # ウィンドウをアクティブ化して前面に表示
        kindle_win.activate()
        time.sleep(self.WINDOW_ACTIVATION_DELAY)

        # ウィンドウが確実にフォーカスされていることを確認するため、もう一度アクティブ化
        try:
            kindle_win.activate()
            time.sleep(0.5)  # 追加の短い待機時間
        except Exception as e:
            self.status_callback(f"Window reactivation warning: {e}")

        # フルスクリーンに切り替える前にウィンドウをクリックしてフォーカスを確保
        try:
            # Cursor is already at window center from moveTo above
            pyautogui.click()
            time.sleep(0.5)
            self.status_callback("Window clicked and focused successfully")
        except Exception as e:
            self.status_callback(f"Click to focus warning: {e}")

        # F11キーでフルスクリーンに切り替え
        self.status_callback("Switching to fullscreen mode (F11)...")
        pyautogui.press('f11')
        time.sleep(self.FULLSCREEN_DELAY)

        self.status_callback("Kindle window activated and in fullscreen mode")
        return kindle_win, monitor

    def launch_and_activate_kindle(self):
        started, error = self.start_kindle_app()
        if error:
            self.error_callback(error)
            return None, None
        
        return self.find_and_activate_kindle()


    def navigate_to_first_page(self):
        self.status_callback("Navigating to the beginning of the book (pressing 'Home' key)...")
        # Use keyDown/keyUp for more reliable input
        for i in range(2):
            self.status_callback(f"Pressing Home key (attempt {i+1}/2)...")
            pyautogui.keyDown('home')
            time.sleep(0.1)
            pyautogui.keyUp('home')
            time.sleep(0.8)
        self.status_callback(f"Waiting {self.NAVIGATION_DELAY} seconds for navigation to complete...")
        time.sleep(self.NAVIGATION_DELAY)

    def get_book_region(self, kindle_win):
        self.status_callback("Dynamically detecting book region...")
        try:
            # 1. Capture the entire window content
            window_rect = {
                "left": kindle_win.left,
                "top": kindle_win.top,
                "width": kindle_win.width,
                "height": kindle_win.height
            }

            self.status_callback(f"Window size: {kindle_win.width}x{kindle_win.height}")

            with mss.mss() as sct:
                sct_img = sct.grab(window_rect)
                full_screenshot_np = np.array(Image.frombytes("RGB", sct_img.size, sct_img.rgb))

            # 2. Process the image with OpenCV
            gray = cv2.cvtColor(full_screenshot_np, cv2.COLOR_RGB2GRAY)

            # Apply blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Thresholding to create a binary image. The page is light, background is grey.
            # We use THRESH_BINARY_INV + OTSU to make the page black and background white.
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # 3. Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 4. Find the largest contour, which should be the book page
            if not contours:
                raise ValueError("No contours found. Cannot detect book page.")

            # Sort contours by area
            contours_sorted = sorted(contours, key=cv2.contourArea, reverse=True)
            max_contour = contours_sorted[0]
            contour_area = cv2.contourArea(max_contour)

            # Log detection info
            window_area = kindle_win.width * kindle_win.height
            area_percentage = (contour_area / window_area) * 100
            self.status_callback(f"Largest contour: {contour_area:.0f} pixels ({area_percentage:.1f}% of window)")

            # Check if the largest contour is reasonably large
            min_area = window_area * self.MIN_BOOK_REGION_SIZE
            if contour_area < min_area:
                self.status_callback(f"Contour too small (min: {min_area:.0f}, found: {contour_area:.0f})")
                raise ValueError("Largest contour is too small. Unlikely to be the book page.")

            x, y, w, h = cv2.boundingRect(max_contour)

            # 5. Convert to absolute screen coordinates and apply a margin
            margin = self.BOOK_REGION_MARGIN

            # Adjust margins - reduce top margin to capture more of the page
            # and increase bottom margin to exclude taskbar
            top_margin = max(5, margin // 2)  # Reduce top margin to avoid cropping
            bottom_margin = margin * 2  # Increase bottom margin to exclude taskbar
            side_margin = margin

            book_region = {
                "left": kindle_win.left + x + side_margin,
                "top": kindle_win.top + y + top_margin,
                "width": w - (2 * side_margin),
                "height": h - top_margin - bottom_margin
            }

            self.status_callback(f"Dynamic detection SUCCESS: {book_region}")
            return book_region

        except Exception as e:
            self.status_callback(f"Dynamic detection failed: {e}")
            self.status_callback("Using full-window fallback method...")

            # Improved fallback: use almost full window if in fullscreen
            # Check if window looks like fullscreen (very large)
            if kindle_win.width > 1000 and kindle_win.height > 700:
                # Fullscreen mode - use generous margins
                margin_h = int(kindle_win.width * 0.1)  # 10% horizontal margin
                margin_v_top = int(kindle_win.height * 0.03)  # 3% top margin (reduced)
                margin_v_bottom = int(kindle_win.height * 0.08)  # 8% bottom margin (increased to exclude taskbar)

                book_x = kindle_win.left + margin_h
                book_y = kindle_win.top + margin_v_top
                book_width = kindle_win.width - (2 * margin_h)
                book_height = kindle_win.height - margin_v_top - margin_v_bottom

                self.status_callback(f"Fullscreen mode detected - using proportional margins (top: {margin_v_top}px, bottom: {margin_v_bottom}px)")
            else:
                # Windowed mode - use fixed margins
                title_bar_height = 30
                side_margin = 15
                top_margin = 5  # Reduced from default
                bottom_margin = 40  # Increased to exclude taskbar

                book_x = kindle_win.left + side_margin
                book_y = kindle_win.top + title_bar_height + top_margin
                book_width = kindle_win.width - (2 * side_margin)
                book_height = kindle_win.height - title_bar_height - top_margin - bottom_margin

                self.status_callback(f"Windowed mode detected - using fixed margins")

            book_width = max(100, book_width)  # Minimum 100px width
            book_height = max(100, book_height)  # Minimum 100px height

            fallback_region = {"left": book_x, "top": book_y, "width": book_width, "height": book_height}
            self.status_callback(f"Fallback region: {fallback_region}")
            return fallback_region

    def _hash_image(self, screenshot_region):
        """指定された領域のスクリーンショットを撮り、ハッシュ値を返す"""
        with mss.mss() as sct:
            sct_img = sct.grab(screenshot_region)
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
            # OpenCVで処理するためにPIL.Imageをnumpy配列に変換
            img_np = np.array(img)
            # グレースケールに変換してハッシュ化
            gray_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            # シンプルなハッシュ関数（平均ハッシュなど）を使用
            # より堅牢な比較が必要な場合はdHashなどを検討
            return cv2.mean(gray_img)[0]

    def determine_page_turn_direction(self, kindle_win):
        self.status_callback("Determining page turn direction...")

        book_region = self.get_book_region(kindle_win)

        # mss.mss().grab()に渡すモニター引数
        sct_monitor = {
            "left": book_region["left"],
            "top": book_region["top"],
            "width": book_region["width"],
            "height": book_region["height"],
        }

        # Log the capture region for debugging
        self.status_callback(f"Capture region: left={book_region['left']}, top={book_region['top']}, "
                           f"width={book_region['width']}, height={book_region['height']}")

        # Kindleウィンドウに確実にフォーカスを当てる
        try:
            # If window is on a secondary monitor, move mouse there first
            window_center_x = kindle_win.left + kindle_win.width // 2
            window_center_y = kindle_win.top + kindle_win.height // 2

            self.status_callback(f"Moving cursor to window center: ({window_center_x}, {window_center_y})")

            # Move mouse to window (this works across monitors)
            pyautogui.moveTo(window_center_x, window_center_y, duration=0.3)
            time.sleep(0.5)

            # Activate window multiple times to ensure focus
            self.status_callback("Activating Kindle window...")
            kindle_win.activate()
            time.sleep(0.8)

            # Move mouse and click multiple times to ensure focus
            self.status_callback("Clicking window to ensure focus...")
            pyautogui.click()
            time.sleep(0.3)
            pyautogui.click()
            time.sleep(0.3)
            pyautogui.click()
            time.sleep(0.5)

            # Re-activate after clicking
            kindle_win.activate()
            time.sleep(0.5)

            # Final verification - send a harmless key that won't change pages
            # Press and release ESC (usually does nothing in Kindle)
            self.status_callback("Sending test key press to verify focus...")
            pyautogui.press('esc')
            time.sleep(0.3)

            self.status_callback("Window focused and ready for page turn detection")
        except Exception as e:
            self.status_callback(f"Focus warning during direction test: {e}")

        # Wait a bit more to ensure everything is stable
        time.sleep(1)

        # 最初のページハッシュを記録
        initial_hash = self._hash_image(sct_monitor)
        self.status_callback(f"Initial page hash recorded: {initial_hash:.2f}")

        # Take a test screenshot to verify we're capturing something
        try:
            with mss.mss() as sct:
                test_img = sct.grab(sct_monitor)
                test_arr = np.array(Image.frombytes("RGB", test_img.size, test_img.rgb))
                mean_brightness = np.mean(test_arr)
                self.status_callback(f"Capture verification - Image size: {test_img.size}, Mean brightness: {mean_brightness:.2f}")

                # Check if image is not completely black or white
                if mean_brightness < 10 or mean_brightness > 245:
                    self.status_callback(f"WARNING: Captured image may be invalid (brightness: {mean_brightness:.2f})")
        except Exception as e:
            self.status_callback(f"Capture verification warning: {e}")

        # 右矢印でテスト
        self.status_callback("Testing RIGHT arrow key...")
        self.status_callback("Pressing RIGHT arrow...")

        # Use keyDown/keyUp instead of press for more reliable input
        pyautogui.keyDown('right')
        time.sleep(0.1)
        pyautogui.keyUp('right')

        self.status_callback(f"Waiting {self.PAGE_TURN_DELAY}s for page to turn...")
        time.sleep(self.PAGE_TURN_DELAY)

        after_right_hash = self._hash_image(sct_monitor)
        right_diff = abs(initial_hash - after_right_hash)
        self.status_callback(f"After RIGHT arrow hash: {after_right_hash:.2f} (diff: {right_diff:.2f})")

        # ハッシュの差を計算（より堅牢な検出のため）
        if right_diff > self.HASH_DIFF_THRESHOLD:
            self.status_callback(f"✓ Page turn detected! RIGHT arrow changes page (diff: {right_diff:.2f} > threshold: {self.HASH_DIFF_THRESHOLD})")
            self.status_callback("Page turn direction: Right-to-Left (RTL) - RIGHT arrow advances page")
            # ページがめくれたので、テストで進んだ分を戻す
            self.status_callback("Pressing LEFT arrow to return to original page...")
            pyautogui.keyDown('left')
            time.sleep(0.1)
            pyautogui.keyUp('left')
            time.sleep(self.PAGE_TURN_DELAY)
            return 'right'  # 右矢印で次に進む

        # No change detected - try going back with LEFT to return to original state
        self.status_callback("No change detected with RIGHT arrow. Pressing LEFT to return to original state...")
        pyautogui.keyDown('left')
        time.sleep(0.1)
        pyautogui.keyUp('left')
        time.sleep(self.PAGE_TURN_DELAY)

        # 元のページに戻ったか確認
        current_hash = self._hash_image(sct_monitor)
        back_diff = abs(initial_hash - current_hash)
        self.status_callback(f"After LEFT return hash: {current_hash:.2f} (diff from initial: {back_diff:.2f})")

        if back_diff > self.HASH_DIFF_THRESHOLD:
            # LEFT made a change, so we're probably not at initial page anymore
            self.status_callback("WARNING: Could not reliably return to initial page. Trying RIGHT to stabilize...")
            pyautogui.press('right')
            time.sleep(self.PAGE_TURN_DELAY)

        # Wait and recapture initial state
        time.sleep(1)
        initial_hash = self._hash_image(sct_monitor)
        self.status_callback(f"Re-captured initial page hash: {initial_hash:.2f}")

        # 左矢印でテスト
        self.status_callback("Testing LEFT arrow key...")
        self.status_callback("Pressing LEFT arrow...")

        # Use keyDown/keyUp instead of press for more reliable input
        pyautogui.keyDown('left')
        time.sleep(0.1)
        pyautogui.keyUp('left')

        self.status_callback(f"Waiting {self.PAGE_TURN_DELAY}s for page to turn...")
        time.sleep(self.PAGE_TURN_DELAY)

        after_left_hash = self._hash_image(sct_monitor)
        left_diff = abs(initial_hash - after_left_hash)
        self.status_callback(f"After LEFT arrow hash: {after_left_hash:.2f} (diff: {left_diff:.2f})")

        if left_diff > self.HASH_DIFF_THRESHOLD:
            self.status_callback(f"✓ Page turn detected! LEFT arrow changes page (diff: {left_diff:.2f} > threshold: {self.HASH_DIFF_THRESHOLD})")
            self.status_callback("Page turn direction: Left-to-Right (LTR) - LEFT arrow advances page")
            # ページがめくれたので、テストで進んだ分を戻す
            self.status_callback("Pressing RIGHT arrow to return to original page...")
            pyautogui.keyDown('right')
            time.sleep(0.1)
            pyautogui.keyUp('right')
            time.sleep(self.PAGE_TURN_DELAY)
            return 'left'  # 左矢印で次に進む

        # Neither direction worked - check if it's close to threshold
        max_diff = max(right_diff, left_diff)

        if max_diff > self.HASH_DIFF_THRESHOLD * 0.5:
            # Close to detection, suggest increasing delay
            self.error_callback(
                f"Page turn detection partially successful but below threshold.\n\n"
                f"Detection results:\n"
                f"- Initial hash: {initial_hash:.2f}\n"
                f"- RIGHT arrow diff: {right_diff:.2f}\n"
                f"- LEFT arrow diff: {left_diff:.2f}\n"
                f"- Threshold: {self.HASH_DIFF_THRESHOLD}\n"
                f"- Max diff: {max_diff:.2f} (need >{self.HASH_DIFF_THRESHOLD})\n\n"
                f"The page is changing slightly, but not enough to detect reliably.\n\n"
                f"RECOMMENDED SOLUTIONS (in order):\n"
                f"1. ★ INCREASE 'Page Turn Delay' to 4-5 seconds (currently {self.PAGE_TURN_DELAY}s)\n"
                f"2. ★ MANUALLY SELECT page direction: LtoR (English) or RtoL (Manga)\n"
                f"3. Click on the Kindle page 3-4 times to ensure focus\n"
                f"4. Wait a few seconds, then try again\n"
                f"5. Use 'Manual Region Selection' mode if area detection is wrong"
            )
        else:
            # Very little change detected
            self.error_callback(
                f"Could not determine page turn direction. Screen did not change significantly.\n\n"
                f"Detection results:\n"
                f"- Initial hash: {initial_hash:.2f}\n"
                f"- RIGHT arrow diff: {right_diff:.2f}\n"
                f"- LEFT arrow diff: {left_diff:.2f}\n"
                f"- Threshold: {self.HASH_DIFF_THRESHOLD}\n\n"
                f"CRITICAL ISSUES DETECTED:\n"
                f"1. ★ Book is NOT open - showing library or blank screen\n"
                f"2. ★ Kindle window does NOT have keyboard focus\n"
                f"3. Page is covered by menus/dialogs\n\n"
                f"IMMEDIATE ACTIONS REQUIRED:\n"
                f"1. ★ OPEN A BOOK in Kindle (not just the library)\n"
                f"2. ★ CLICK on the book page 3-4 times to ensure focus\n"
                f"3. ★ MANUALLY SELECT page direction: LtoR or RtoL\n"
                f"4. Close any menus or dialogs in Kindle\n"
                f"5. Increase 'Page Turn Delay' to 4-5 seconds"
            )
        return None