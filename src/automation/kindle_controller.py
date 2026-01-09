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
    DEFAULT_PAGE_TURN_DELAY = 2

    # PyAutoGUI configuration
    PYAUTOGUI_PAUSE = 0.1
    PYAUTOGUI_FAILSAFE = True

    # Book region detection
    BOOK_REGION_MARGIN = 5  # pixels
    MIN_BOOK_REGION_SIZE = 0.15  # 15% of window area (lowered for better compatibility)

    # Hash comparison threshold for page detection
    # Using mean grayscale value (0-255), so threshold should be higher
    HASH_DIFF_THRESHOLD = 5.0  # Increased from 0.5 to detect actual page changes

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
        all_windows = gw.getAllWindows()
        for window in all_windows:
            title = window.title.lower()
            # Check if it's a Kindle window (but not our own app)
            if ('kindle' in title and
                'kindletopdf' not in title and
                'kindle-to-pdf' not in title and
                not window.title.startswith('C:\\')):  # Filter out file paths
                return True
        return False

    def find_kindle_exe(self):
        """Find Kindle.exe in common installation locations"""
        possible_paths = [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Amazon', 'Kindle', 'application', 'Kindle.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Amazon', 'Kindle', 'Kindle.exe'),
            os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Amazon', 'Kindle', 'Kindle.exe'),
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Amazon', 'Kindle', 'Kindle.exe'),
            'C:\\Users\\' + os.environ.get('USERNAME', '') + '\\AppData\\Local\\Amazon\\Kindle\\application\\Kindle.exe',
        ]

        for path in possible_paths:
            if path and os.path.exists(path):
                return path
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
                "Could not find Kindle.exe in standard installation locations.\n"
                "Please start Kindle manually and open a book before starting automation."
            )
            self.error_callback(error_msg)
            return False, error_msg

        try:
            self.status_callback(f"Found Kindle at: {kindle_path}")
            subprocess.Popen(kindle_path)
            self.status_callback(f"Kindle launched. Waiting {self.KINDLE_STARTUP_DELAY}s for startup...")
            time.sleep(self.KINDLE_STARTUP_DELAY)

            # Verify that Kindle actually started
            if self.is_kindle_running():
                self.status_callback("Kindle started successfully.")
                return True, None
            else:
                error_msg = "Kindle was launched but no window was detected. Please check if Kindle started correctly."
                self.error_callback(error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = f"Failed to start Kindle: {e}"
            self.error_callback(error_msg)
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

        # Find all windows and filter for actual Kindle windows
        all_windows = gw.getAllWindows()
        kindle_windows = []

        for window in all_windows:
            title_lower = window.title.lower()
            # Check if it's a Kindle window (but not our own app or empty)
            # Filter out: our app name, file paths, and empty titles
            if ('kindle' in title_lower and
                'kindletopdf' not in title_lower and
                'kindle-to-pdf' not in title_lower and
                not window.title.startswith('C:\\') and  # Filter out file paths
                window.title.strip() and
                window.visible):
                kindle_windows.append(window)

        if not kindle_windows:
            self.error_callback("Kindle app window not found. Please ensure Kindle is running and a book is open.")
            return None

        # Use the first valid Kindle window
        main_window = kindle_windows[0]
        window_title = main_window.title

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
        # Kindleがフォーカスされていることを確認するため、複数回Homeキーを押す
        for i in range(2):
            pyautogui.press('home')
            time.sleep(0.5)
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

            book_region = {
                "left": kindle_win.left + x + margin,
                "top": kindle_win.top + y + margin,
                "width": w - (2 * margin),
                "height": h - (2 * margin)
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
                margin_v = int(kindle_win.height * 0.05)  # 5% vertical margin

                book_x = kindle_win.left + margin_h
                book_y = kindle_win.top + margin_v
                book_width = kindle_win.width - (2 * margin_h)
                book_height = kindle_win.height - (2 * margin_v)

                self.status_callback(f"Fullscreen mode detected - using proportional margins")
            else:
                # Windowed mode - use fixed margins
                title_bar_height = 30
                side_margin = 15
                bottom_margin = 15

                book_x = kindle_win.left + side_margin
                book_y = kindle_win.top + title_bar_height
                book_width = kindle_win.width - (2 * side_margin)
                book_height = kindle_win.height - title_bar_height - bottom_margin

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
            time.sleep(0.2)

            # Activate window
            kindle_win.activate()
            time.sleep(0.5)

            # Click to ensure focus (cursor is already at window center)
            pyautogui.click()
            time.sleep(0.5)

            self.status_callback("Window focused and ready for page turn detection")
        except Exception as e:
            self.status_callback(f"Focus warning during direction test: {e}")

        # 最初のページハッシュを記録
        initial_hash = self._hash_image(sct_monitor)
        self.status_callback(f"Initial page hash recorded: {initial_hash:.2f}")

        # 右矢印でテスト
        self.status_callback("Testing RIGHT arrow key...")
        pyautogui.press('right')
        time.sleep(self.PAGE_TURN_DELAY)  # ページめくりの遅延時間を使用
        after_right_hash = self._hash_image(sct_monitor)
        right_diff = abs(initial_hash - after_right_hash)
        self.status_callback(f"After RIGHT arrow hash: {after_right_hash:.2f} (diff: {right_diff:.2f})")

        # ハッシュの差を計算（より堅牢な検出のため）
        if right_diff > self.HASH_DIFF_THRESHOLD:
            self.status_callback("Page turn direction: Right-to-Left (RTL)")
            # ページがめくれたので、テストで進んだ分を戻す
            pyautogui.press('left')
            time.sleep(self.PAGE_TURN_DELAY)
            return 'right'  # 右矢印で次に進む

        # 元のページに戻ったか確認
        # 再度ハッシュを計算し、initial_hashと比較
        current_hash = self._hash_image(sct_monitor)
        if abs(initial_hash - current_hash) <= self.HASH_DIFF_THRESHOLD:
            self.status_callback("Returned to initial page state after right-arrow test.")
        else:
            self.error_callback("Failed to return to initial page state after right-arrow test. Manual intervention may be needed.")
            # エラーなので、処理を続行せずにNoneを返すか、例外を発生させる
            return None

        # 左矢印でテスト
        self.status_callback("Testing LEFT arrow key...")
        pyautogui.press('left')
        time.sleep(self.PAGE_TURN_DELAY)
        after_left_hash = self._hash_image(sct_monitor)
        left_diff = abs(initial_hash - after_left_hash)
        self.status_callback(f"After LEFT arrow hash: {after_left_hash:.2f} (diff: {left_diff:.2f})")

        if left_diff > self.HASH_DIFF_THRESHOLD:
            self.status_callback("Page turn direction: Left-to-Right (LTR)")
            # ページがめくれたので、テストで進んだ分を戻す
            pyautogui.press('right')
            time.sleep(self.PAGE_TURN_DELAY)
            return 'left'  # 左矢印で次に進む

        self.error_callback(
            f"Could not determine page turn direction. Screen did not change significantly.\n"
            f"Right arrow diff: {right_diff:.2f}, Left arrow diff: {left_diff:.2f} "
            f"(threshold: {self.HASH_DIFF_THRESHOLD})\n"
            f"Please ensure:\n"
            f"1. A book is open in Kindle (not just the library)\n"
            f"2. The book page is visible and not covered by menus\n"
            f"3. Try increasing 'Page Turn Delay' in settings if pages turn slowly"
        )
        return None