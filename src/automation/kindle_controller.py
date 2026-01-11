"""
Kindle Controller module.
Handles Kindle window detection, region detection, and page turn automation.
"""

import time
from typing import Optional, Dict, Tuple, Callable
import pyautogui
import pygetwindow as gw
import mss
import cv2
import numpy as np
from PIL import Image
from src.constants import (
    Delays,
    PyAutoGUIConfig,
    WindowDimensions,
    RegionDetection,
    PageDetection,
    PageTurnDirection,
    ErrorMessages
)
from src.image_hasher import ImageHasher
from src.callback_utils import get_callback_or_default

class KindleController:
    """
    Controller for automating Kindle for PC application.
    Handles window detection, activation, and interaction.
    """

    def __init__(
        self,
        status_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize Kindle controller

        Args:
            status_callback: Function to call with status messages
            error_callback: Function to call with error messages
        """
        self.status_callback = get_callback_or_default(status_callback, "Status")
        self.error_callback = get_callback_or_default(error_callback, "Error")

        # Set instance delay values (can be overridden from constants)
        self.WINDOW_RESTORE_DELAY = Delays.WINDOW_RESTORE
        self.WINDOW_ACTIVATION_DELAY = Delays.WINDOW_ACTIVATION
        self.PAGE_TURN_DELAY = Delays.PAGE_TURN

        # Configure PyAutoGUI
        pyautogui.PAUSE = PyAutoGUIConfig.PAUSE
        pyautogui.FAILSAFE = PyAutoGUIConfig.FAILSAFE

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
                self.error_callback(ErrorMessages.KINDLE_WINDOW_NOT_FOUND)
                return None

            # Use the first valid Kindle window
            main_window = kindle_windows[0]
            window_title = main_window.title

            if len(kindle_windows) > 1:
                self.status_callback(f"Found {len(kindle_windows)} Kindle windows, using: '{window_title}'")

            if window_title.strip().lower() == 'kindle':
                self.status_callback(ErrorMessages.KINDLE_NO_BOOK_OPEN)
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

        self.status_callback("Activating and positioning Kindle window...")

        # Log window position for debugging multi-monitor setups
        self.status_callback(f"Current window position: ({kindle_win.left}, {kindle_win.top}), "
                           f"size: {kindle_win.width}x{kindle_win.height}")

        if kindle_win.isMinimized:
            kindle_win.restore()
            time.sleep(self.WINDOW_RESTORE_DELAY)

        monitor = self.get_monitor_for_window(kindle_win)
        if monitor:
            self.status_callback(f"Window is on monitor: left={monitor['left']}, top={monitor['top']}, "
                               f"size={monitor['width']}x{monitor['height']}")
        else:
            # Use primary monitor if no monitor detected
            with mss.mss() as sct:
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else None

        # ウィンドウをモニターの左半分にリサイズして配置
        if monitor:
            # 左半分のサイズを計算（タスクバーの高さを考慮）
            half_width = monitor["width"] // 2
            taskbar_height = WindowDimensions.TASKBAR_HEIGHT
            window_height = monitor["height"] - taskbar_height

            # ウィンドウをリサイズして左側に配置
            try:
                self.status_callback(f"Resizing window to half screen: {half_width}x{window_height} (excluding taskbar)")
                kindle_win.resizeTo(half_width, window_height)
                time.sleep(0.3)
                kindle_win.moveTo(monitor["left"], monitor["top"])
                time.sleep(0.5)
                self.status_callback(f"Window repositioned to: ({monitor['left']}, {monitor['top']})")
            except Exception as e:
                self.status_callback(f"Window resize/move warning: {e}")
                # If resize fails, continue with current window size

        # ウィンドウをアクティブ化
        kindle_win.activate()
        time.sleep(self.WINDOW_ACTIVATION_DELAY)

        # Calculate window center for focus
        window_center_x = kindle_win.left + kindle_win.width // 2
        window_center_y = kindle_win.top + kindle_win.height // 2

        # Move mouse to window and click to ensure focus
        try:
            self.status_callback(f"Moving cursor to window center: ({window_center_x}, {window_center_y})")
            pyautogui.moveTo(window_center_x, window_center_y, duration=0.2)
            time.sleep(0.3)
            pyautogui.click()
            time.sleep(0.5)
            self.status_callback("Window focused successfully")
        except Exception as e:
            self.status_callback(f"Focus warning: {e}")

        self.status_callback("Kindle window activated and positioned in half-screen mode")
        return kindle_win, monitor

    def get_book_region(self, kindle_win):
        self.status_callback("Dynamically detecting book region...")

        try:
            # ウィンドウ全体をキャプチャ（横半分ウィンドウモード）
            window_rect = {
                "left": kindle_win.left,
                "top": kindle_win.top,
                "width": kindle_win.width,
                "height": kindle_win.height
            }

            self.status_callback(f"Capture area: {window_rect['width']}x{window_rect['height']} at ({window_rect['left']}, {window_rect['top']})")

            with mss.mss() as sct:
                sct_img = sct.grab(window_rect)
                full_screenshot_np = np.array(Image.frombytes("RGB", sct_img.size, sct_img.rgb))

            # 2. Process the image with OpenCV
            gray = cv2.cvtColor(full_screenshot_np, cv2.COLOR_RGB2GRAY)

            # Apply blur to reduce noise
            blurred = cv2.GaussianBlur(gray, RegionDetection.GAUSSIAN_BLUR_KERNEL, RegionDetection.GAUSSIAN_BLUR_SIGMA)

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
            capture_area = window_rect["width"] * window_rect["height"]
            area_percentage = (contour_area / capture_area) * 100
            self.status_callback(f"Largest contour: {contour_area:.0f} pixels ({area_percentage:.1f}% of capture area)")

            # Check if the largest contour is reasonably large
            min_area = capture_area * RegionDetection.MIN_BOOK_REGION_SIZE
            if contour_area < min_area:
                self.status_callback(f"Contour too small (min: {min_area:.0f}, found: {contour_area:.0f})")
                raise ValueError("Largest contour is too small. Unlikely to be the book page.")

            x, y, w, h = cv2.boundingRect(max_contour)

            # 5. Convert to absolute screen coordinates and apply a margin
            # contourで検出した領域を外側に広げるため、負のマージンを使用
            top_margin = RegionDetection.TOP_MARGIN
            bottom_margin = RegionDetection.BOTTOM_MARGIN
            side_margin = RegionDetection.SIDE_MARGIN

            book_region = {
                "left": window_rect["left"] + x + side_margin,
                "top": window_rect["top"] + y + top_margin,  # 負の値なので上に広がる
                "width": w - (2 * side_margin),
                "height": h - top_margin - bottom_margin  # 負の値を引くので高さが増える
            }

            self.status_callback(f"Dynamic detection SUCCESS: {book_region}")
            self.status_callback(f"Book region size: {book_region['width']}x{book_region['height']}")
            return book_region

        except Exception as e:
            self.status_callback(f"Dynamic detection failed: {e}")
            self.status_callback("Using window-based fallback method...")

            # Windowed mode (横半分) - タイトルバー、メニューバー、タスクバーを考慮
            title_bar_height = WindowDimensions.TITLE_BAR_HEIGHT
            kindle_menu_height = WindowDimensions.KINDLE_MENU_HEIGHT
            side_margin = WindowDimensions.SIDE_MARGIN
            bottom_margin = WindowDimensions.BOTTOM_MARGIN

            # 上部: タイトルバー + Kindleメニューバー
            top_offset = title_bar_height + kindle_menu_height

            book_x = kindle_win.left + side_margin
            book_y = kindle_win.top + top_offset
            book_width = kindle_win.width - (2 * side_margin)
            book_height = kindle_win.height - top_offset - bottom_margin

            self.status_callback(f"Half-screen windowed mode - margins: Title+Menu={top_offset}px (Title={title_bar_height}px, Menu={kindle_menu_height}px), Side={side_margin}px, Bottom={bottom_margin}px")

            book_width = max(100, book_width)  # Minimum 100px width
            book_height = max(100, book_height)  # Minimum 100px height

            fallback_region = {"left": book_x, "top": book_y, "width": book_width, "height": book_height}
            self.status_callback(f"Fallback region: {fallback_region}")
            self.status_callback(f"Fallback size: {book_width}x{book_height}")
            return fallback_region

    def _hash_image(self, screenshot_region):
        """
        指定された領域のスクリーンショットを撮り、ハッシュを返す
        Returns: tuple (mean_value, histogram_hash)
        """
        with mss.mss() as sct:
            sct_img = sct.grab(screenshot_region)
            return ImageHasher.hash_image(sct_img)

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

        # Kindleウィンドウに確実にフォーカスを当てる（強化版）
        try:
            # Calculate capture region center for more accurate focus
            region_center_x = book_region["left"] + book_region["width"] // 2
            region_center_y = book_region["top"] + book_region["height"] // 2

            self.status_callback(f"Ensuring window focus at capture region center: ({region_center_x}, {region_center_y})")

            # Move mouse to capture region center
            pyautogui.moveTo(region_center_x, region_center_y, duration=0.3)
            time.sleep(0.5)

            # Activate window multiple times to ensure focus
            for i in range(2):
                kindle_win.activate()
                time.sleep(0.3)
                pyautogui.click(region_center_x, region_center_y)
                time.sleep(0.5)

            self.status_callback("✓ Window focused successfully at capture region center")
            self.status_callback("NOTE: Please ensure the book is OPEN and visible (not the library)")
        except Exception as e:
            self.status_callback(f"Focus warning during direction test: {e}")

        # 安定するまで待機
        time.sleep(0.5)

        # 最初のページハッシュを記録
        initial_hash = self._hash_image(sct_monitor)
        self.status_callback(f"Initial page hash recorded: mean={initial_hash[0]:.2f}, dhash={initial_hash[1]}")

        # Take a test screenshot to verify we're capturing something
        try:
            with mss.mss() as sct:
                test_img = sct.grab(sct_monitor)
                test_arr = np.array(Image.frombytes("RGB", test_img.size, test_img.rgb))
                mean_brightness = np.mean(test_arr)
                std_brightness = np.std(test_arr)
                self.status_callback(f"Capture verification - Size: {test_img.size}, Brightness: {mean_brightness:.2f}, StdDev: {std_brightness:.2f}")

                # Save debug image for troubleshooting
                try:
                    debug_img = Image.fromarray(test_arr)
                    debug_path = "debug_capture_initial.png"
                    debug_img.save(debug_path)
                    self.status_callback(f"Debug: Saved initial capture to {debug_path}")
                except Exception as save_err:
                    self.status_callback(f"Debug: Could not save test image: {save_err}")

                # Check if image is not completely black or white
                if mean_brightness < PageDetection.MIN_BRIGHTNESS:
                    self.status_callback(f"⚠ WARNING: Captured image is too dark (brightness: {mean_brightness:.2f} < {PageDetection.MIN_BRIGHTNESS})")
                    self.status_callback("This suggests the capture region may be wrong or the screen is black")
                elif mean_brightness > PageDetection.MAX_BRIGHTNESS:
                    self.status_callback(f"⚠ WARNING: Captured image is too bright (brightness: {mean_brightness:.2f} > {PageDetection.MAX_BRIGHTNESS})")
                    self.status_callback("This suggests a blank/white screen or wrong capture region")
                elif std_brightness < 10:
                    self.status_callback(f"⚠ WARNING: Very low variation in image (StdDev: {std_brightness:.2f})")
                    self.status_callback("This suggests a uniform color screen - likely not showing book content")
        except Exception as e:
            self.status_callback(f"Capture verification warning: {e}")

        # 右矢印でテスト
        self.status_callback("Testing RIGHT arrow key...")
        self.status_callback("Pressing RIGHT arrow...")

        # Use keyDown/keyUp instead of press for more reliable input
        pyautogui.keyDown(PageTurnDirection.RIGHT_KEY)
        time.sleep(Delays.KEY_PRESS)
        pyautogui.keyUp(PageTurnDirection.RIGHT_KEY)

        self.status_callback(f"Waiting {self.PAGE_TURN_DELAY}s for page to turn...")
        time.sleep(self.PAGE_TURN_DELAY)

        after_right_hash = self._hash_image(sct_monitor)
        right_diff = ImageHasher.compare_hashes(initial_hash, after_right_hash)
        self.status_callback(f"After RIGHT arrow: mean={after_right_hash[0]:.2f}, dhash={after_right_hash[1]} (diff: {right_diff:.2f})")

        # Save debug image after RIGHT arrow
        try:
            with mss.mss() as sct:
                debug_img_data = sct.grab(sct_monitor)
                debug_img = Image.frombytes("RGB", debug_img_data.size, debug_img_data.rgb)
                debug_path = "debug_capture_after_right.png"
                debug_img.save(debug_path)
                self.status_callback(f"Debug: Saved after-RIGHT capture to {debug_path}")
        except Exception as save_err:
            self.status_callback(f"Debug: Could not save after-RIGHT image: {save_err}")

        # ハッシュの差を計算（より堅牢な検出のため）
        if right_diff > PageDetection.HASH_DIFF_THRESHOLD:
            self.status_callback(f"✓ Page turn detected! RIGHT arrow changes page (diff: {right_diff:.2f} > threshold: {PageDetection.HASH_DIFF_THRESHOLD})")
            self.status_callback("Page turn direction: Right-to-Left (RTL) - RIGHT arrow advances page")
            # ページがめくれたので、テストで進んだ分を戻す
            self.status_callback("Pressing LEFT arrow to return to original page...")
            pyautogui.keyDown(PageTurnDirection.LEFT_KEY)
            time.sleep(Delays.KEY_PRESS)
            pyautogui.keyUp(PageTurnDirection.LEFT_KEY)
            time.sleep(self.PAGE_TURN_DELAY)
            return PageTurnDirection.RIGHT_KEY

        # No change detected - try going back with LEFT to return to original state
        self.status_callback("No change detected with RIGHT arrow. Pressing LEFT to return to original state...")
        pyautogui.keyDown(PageTurnDirection.LEFT_KEY)
        time.sleep(Delays.KEY_PRESS)
        pyautogui.keyUp(PageTurnDirection.LEFT_KEY)
        time.sleep(self.PAGE_TURN_DELAY)

        # 元のページに戻ったか確認
        current_hash = self._hash_image(sct_monitor)
        back_diff = ImageHasher.compare_hashes(initial_hash, current_hash)
        self.status_callback(f"After LEFT return: mean={current_hash[0]:.2f}, dhash={current_hash[1]} (diff: {back_diff:.2f})")

        if back_diff > PageDetection.HASH_DIFF_THRESHOLD:
            # LEFT made a change, so we're probably not at initial page anymore
            self.status_callback("WARNING: Could not reliably return to initial page. Trying RIGHT to stabilize...")
            pyautogui.press(PageTurnDirection.RIGHT_KEY)
            time.sleep(self.PAGE_TURN_DELAY)

        # Wait and recapture initial state
        time.sleep(1)
        initial_hash = self._hash_image(sct_monitor)
        self.status_callback(f"Re-captured initial page hash: mean={initial_hash[0]:.2f}, dhash={initial_hash[1]}")

        # 左矢印でテスト
        self.status_callback("Testing LEFT arrow key...")
        self.status_callback("Pressing LEFT arrow...")

        # Use keyDown/keyUp instead of press for more reliable input
        pyautogui.keyDown(PageTurnDirection.LEFT_KEY)
        time.sleep(Delays.KEY_PRESS)
        pyautogui.keyUp(PageTurnDirection.LEFT_KEY)

        self.status_callback(f"Waiting {self.PAGE_TURN_DELAY}s for page to turn...")
        time.sleep(self.PAGE_TURN_DELAY)

        after_left_hash = self._hash_image(sct_monitor)
        left_diff = ImageHasher.compare_hashes(initial_hash, after_left_hash)
        self.status_callback(f"After LEFT arrow: mean={after_left_hash[0]:.2f}, dhash={after_left_hash[1]} (diff: {left_diff:.2f})")

        # Save debug image after LEFT arrow
        try:
            with mss.mss() as sct:
                debug_img_data = sct.grab(sct_monitor)
                debug_img = Image.frombytes("RGB", debug_img_data.size, debug_img_data.rgb)
                debug_path = "debug_capture_after_left.png"
                debug_img.save(debug_path)
                self.status_callback(f"Debug: Saved after-LEFT capture to {debug_path}")
        except Exception as save_err:
            self.status_callback(f"Debug: Could not save after-LEFT image: {save_err}")

        if left_diff > PageDetection.HASH_DIFF_THRESHOLD:
            self.status_callback(f"✓ Page turn detected! LEFT arrow changes page (diff: {left_diff:.2f} > threshold: {PageDetection.HASH_DIFF_THRESHOLD})")
            self.status_callback("Page turn direction: Left-to-Right (LTR) - LEFT arrow advances page")
            # ページがめくれたので、テストで進んだ分を戻す
            self.status_callback("Pressing RIGHT arrow to return to original page...")
            pyautogui.keyDown(PageTurnDirection.RIGHT_KEY)
            time.sleep(Delays.KEY_PRESS)
            pyautogui.keyUp(PageTurnDirection.RIGHT_KEY)
            time.sleep(self.PAGE_TURN_DELAY)
            return PageTurnDirection.LEFT_KEY

        # Neither direction worked - check if it's close to threshold
        max_diff = max(right_diff, left_diff)

        # Enhanced error reporting with debug info
        error_details = (
            f"ページめくり方向を検出できませんでした / Could not detect page turn direction\n\n"
            f"📊 Detection Results:\n"
            f"- Initial hash: mean={initial_hash[0]:.2f}, dhash={initial_hash[1]}\n"
            f"- RIGHT arrow diff: {right_diff:.2f}\n"
            f"- LEFT arrow diff: {left_diff:.2f}\n"
            f"- Detection threshold: {PageDetection.HASH_DIFF_THRESHOLD}\n"
            f"- Max diff found: {max_diff:.2f} (need > {PageDetection.HASH_DIFF_THRESHOLD})\n"
            f"- Capture region: {book_region['width']}x{book_region['height']} at ({book_region['left']}, {book_region['top']})\n\n"
        )

        if max_diff > PageDetection.HASH_DIFF_THRESHOLD * 0.5:
            # Close to detection, suggest increasing delay
            error_details += (
                f"⚠ The page is changing slightly (diff={max_diff:.2f}), but not enough for reliable detection.\n\n"
                f"✅ RECOMMENDED SOLUTIONS (試してください):\n"
                f"1. ★★★ INCREASE 'Page Turn Delay' to 4-5 seconds (現在: {self.PAGE_TURN_DELAY}秒)\n"
                f"2. ★★★ MANUALLY SELECT page direction: LtoR (横書き) or RtoL (縦書き・漫画)\n"
                f"3. ★★ Click INSIDE the book page 3-4 times to ensure keyboard focus\n"
                f"4. ★ Re-select the capture region to ensure it covers the book content\n"
                f"5. Check that NO menus/dialogs are covering the book page\n"
                f"6. Wait a few seconds for the page to fully load, then try again\n\n"
                f"🔍 Debug images saved: debug_capture_*.png (check these to see what was captured)"
            )
        else:
            # Very little change detected
            error_details += (
                f"❌ CRITICAL: No significant page change detected (diff={max_diff:.2f}).\n\n"
                f"This indicates one of these critical issues:\n"
                f"1. ★★★ Book is NOT open - showing library or blank screen\n"
                f"2. ★★★ Kindle window does NOT have keyboard focus\n"
                f"3. ★★ Capture region is WRONG - not capturing book content\n"
                f"4. ★ Page is covered by menus/dialogs/popups\n"
                f"5. ★ Book has reached the end or beginning\n\n"
                f"✅ IMMEDIATE ACTIONS REQUIRED:\n"
                f"1. ★★★ OPEN A BOOK in Kindle (not just the library)\n"
                f"2. ★★★ CLICK on the book page 3-4 times to give it keyboard focus\n"
                f"3. ★★★ MANUALLY SELECT page direction: LtoR (横書き) or RtoL (縦書き・漫画)\n"
                f"4. ★★ Re-select capture region using the region selector\n"
                f"5. ★★ Increase 'Page Turn Delay' to 4-5 seconds (現在: {self.PAGE_TURN_DELAY}秒)\n"
                f"6. ★ Close any menus, dialogs, or popups in Kindle\n"
                f"7. ★ Ensure you're on a normal page (not cover/title page)\n\n"
                f"🔍 Debug images saved: debug_capture_*.png (check these to verify capture area)"
            )

        self.error_callback(error_details)
        return None