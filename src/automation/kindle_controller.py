import os
import time
import subprocess
import pyautogui
import pygetwindow as gw
import mss
import cv2 # OpenCVをインポート
import numpy as np # OpenCVで画像データを扱うため

class KindleController:
    def __init__(self, status_callback=None, error_callback=None):
        self.status_callback = status_callback if status_callback else self._default_status_callback
        self.error_callback = error_callback if error_callback else self._default_error_callback
        self.KINDLE_STARTUP_DELAY = 10
        self.WINDOW_RESTORE_DELAY = 0.5
        self.WINDOW_ACTIVATION_DELAY = 3  # Increased for debugging
        self.FULLSCREEN_DELAY = 3         # Increased for debugging
        self.NAVIGATION_DELAY = 7         # Increased for debugging
        self.PAGE_TURN_DELAY = 2 # ページ送りテストで使用

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

    def _get_kindle_window(self):
        self.status_callback("Finding Kindle app window...")
        kindle_windows = gw.getWindowsWithTitle('Kindle')
        if not kindle_windows:
            self.error_callback("Kindle app window not found. Please ensure it is running and visible.")
            return None
        return kindle_windows[0]

    def find_and_activate_kindle(self):
        kindle_win = self._get_kindle_window()
        if not kindle_win:
            return None, None
        
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

            max_contour = max(contours, key=cv2.contourArea)
            
            # Check if the largest contour is reasonably large
            if cv2.contourArea(max_contour) < (kindle_win.width * kindle_win.height * 0.3):
                raise ValueError("Largest contour is too small. Unlikely to be the book page.")

            x, y, w, h = cv2.boundingRect(max_contour)

            # 5. Convert to absolute screen coordinates and apply a margin
            margin = 5  # pixels
            
            book_region = {
                "left": kindle_win.left + x + margin,
                "top": kindle_win.top + y + margin,
                "width": w - (2 * margin),
                "height": h - (2 * margin)
            }
            
            self.status_callback(f"Book region detected dynamically: {book_region}")
            return book_region

        except Exception as e:
            self.error_callback(f"Dynamic region detection failed: {e}. Falling back to hardcoded offsets.")
            
            # Fallback to the old hardcoded method
            title_bar_height = 30
            side_margin = 15
            bottom_margin = 15
            
            book_x = kindle_win.left + side_margin
            book_y = kindle_win.top + title_bar_height
            book_width = kindle_win.width - (2 * side_margin)
            book_height = kindle_win.height - title_bar_height - bottom_margin
            
            book_width = max(0, book_width)
            book_height = max(0, book_height)

            return {"left": book_x, "top": book_y, "width": book_width, "height": book_height}

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

        # 最初のページハッシュを記録
        initial_hash = self._hash_image(sct_monitor)
        self.status_callback("Initial page hash recorded.")

        # 右矢印でテスト
        pyautogui.press('right')
        time.sleep(self.PAGE_TURN_DELAY) # ページめくりの遅延時間を使用
        after_right_hash = self._hash_image(sct_monitor)

        if initial_hash != after_right_hash:
            self.status_callback("Page turn direction: Right-to-Left (RTL)")
            # ページがめくれたので、テストで進んだ分を戻す
            pyautogui.press('left')
            time.sleep(self.PAGE_TURN_DELAY)
            return 'right' # 右矢印で次に進む

        # 元のページに戻ったか確認
        # 再度ハッシュを計算し、initial_hashと比較
        current_hash = self._hash_image(sct_monitor)
        if initial_hash == current_hash:
             self.status_callback("Returned to initial page state after right-arrow test.")
        else:
            self.error_callback("Failed to return to initial page state after right-arrow test. Manual intervention may be needed.")
            # エラーなので、処理を続行せずにNoneを返すか、例外を発生させる
            return None


        # 左矢印でテスト
        pyautogui.press('left')
        time.sleep(self.PAGE_TURN_DELAY)
        after_left_hash = self._hash_image(sct_monitor)

        if initial_hash != after_left_hash:
            self.status_callback("Page turn direction: Left-to-Right (LTR)")
            # ページがめくれたので、テストで進んだ分を戻す
            pyautogui.press('right')
            time.sleep(self.PAGE_TURN_DELAY)
            return 'left' # 左矢印で次に進む
        
        self.error_callback(
            "Could not determine page turn direction. Screen did not change for left or right arrow keys. "
            "Please ensure the book is open and the window is active."
        )
        return None