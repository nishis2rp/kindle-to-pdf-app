"""
Constants used throughout the Kindle to PDF application.
Centralizes all magic numbers and configuration values for maintainability.
"""

# ============================================================================
# WINDOW DIMENSIONS
# ============================================================================
DEFAULT_WINDOW_WIDTH = 1000
DEFAULT_WINDOW_HEIGHT = 700

# ============================================================================
# TIMING DELAYS (seconds)
# ============================================================================
class Delays:
    """Timing delays for various operations"""
    # Window operations
    WINDOW_RESTORE = 0.5
    WINDOW_ACTIVATION = 3.0
    EXIT_FULLSCREEN = 0.5

    # Page operations
    PAGE_TURN = 3.0
    PAGE_STABILIZATION = 0.3

    # Kindle operations
    KINDLE_STARTUP = 10.0
    NAVIGATION = 7.0

    # Mouse and keyboard
    MOUSE_MOVE = 0.2
    MOUSE_CLICK = 0.3
    KEY_PRESS = 0.1
    FOCUS_WAIT = 0.5

# ============================================================================
# PYAUTOGUI CONFIGURATION
# ============================================================================
class PyAutoGUIConfig:
    """PyAutoGUI library configuration"""
    PAUSE = 0.1
    FAILSAFE = True

# ============================================================================
# WINDOW DIMENSIONS AND MARGINS
# ============================================================================
class WindowDimensions:
    """Window size and margin calculations"""
    TASKBAR_HEIGHT = 48  # Windows taskbar height (pixels)
    TITLE_BAR_HEIGHT = 32  # Window title bar height (pixels)
    KINDLE_MENU_HEIGHT = 35  # Kindle app menu bar height (pixels)
    SIDE_MARGIN = 8  # Window left/right border (pixels)
    BOTTOM_MARGIN = 15  # Bottom margin to avoid taskbar (pixels)

# ============================================================================
# BOOK REGION DETECTION
# ============================================================================
class RegionDetection:
    """Book region detection parameters"""
    # Minimum size threshold (percentage of window area)
    MIN_BOOK_REGION_SIZE = 0.15  # 15% of window area

    # Margins for detected region (pixels)
    TOP_MARGIN = -300  # Negative = expand upward (prevent text cutoff)
    BOTTOM_MARGIN = 10  # Positive = shrink downward (prevent over-capture)
    SIDE_MARGIN = 2  # Positive = shrink inward from sides

    # OpenCV parameters
    GAUSSIAN_BLUR_KERNEL = (5, 5)
    GAUSSIAN_BLUR_SIGMA = 0

# ============================================================================
# PAGE TURN DETECTION
# ============================================================================
class PageDetection:
    """Page turn detection thresholds"""
    # Hash difference threshold for detecting page changes
    # Uses combined metric: mean diff (0-255) + hamming distance * 2 (0-128)
    # Typical page turn diff: 15-100+, same page: 0-5
    HASH_DIFF_THRESHOLD = 10.0

    # End of book detection
    DEFAULT_END_DETECTION_SENSITIVITY = 3  # consecutive identical pages

    # Image brightness validation thresholds
    MIN_BRIGHTNESS = 10  # Too dark = likely invalid capture
    MAX_BRIGHTNESS = 245  # Too bright = likely blank/white screen

# ============================================================================
# STORAGE AND FILE OPERATIONS
# ============================================================================
class Storage:
    """Storage-related constants"""
    ESTIMATED_BYTES_PER_PAGE = 2 * 1024 * 1024  # 2 MB per page
    PDF_OVERHEAD_FACTOR = 1.1  # 10% overhead for PDF structure

    # Default paths
    @staticmethod
    def get_default_output_dir():
        """Get the user's Downloads folder"""
        import os
        return os.path.join(os.path.expanduser("~"), "Downloads")

    @staticmethod
    def get_default_filename():
        """Get default filename in yyyymmdd.pdf format"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d.pdf")

    # Legacy constants for backward compatibility
    DEFAULT_OUTPUT_DIR = None  # Will be set dynamically
    DEFAULT_FILENAME = None  # Will be set dynamically
    CONFIG_FILENAME = "config.json"

# ============================================================================
# IMAGE PROCESSING
# ============================================================================
class ImageProcessing:
    """Image optimization parameters"""
    DEFAULT_JPEG_QUALITY = 90  # 0-100 scale

    # Supported formats
    SUPPORTED_FORMATS = ["PNG", "JPEG"]

    # Image resizing
    MAX_IMAGE_WIDTH = 1200  # Maximum width for optimized images
    LANCZOS_RESAMPLING = True  # High-quality downsampling

# ============================================================================
# SYSTEM POWER MANAGEMENT
# ============================================================================
class PowerManagement:
    """Windows API constants for power management"""
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002

# ============================================================================
# PAGE TURN DIRECTIONS
# ============================================================================
class PageTurnDirection:
    """Page turn direction modes"""
    AUTOMATIC = "Automatic"
    LEFT_TO_RIGHT = "LtoR"
    RIGHT_TO_LEFT = "RtoL"

    # Arrow key mappings
    LEFT_KEY = "left"
    RIGHT_KEY = "right"

    @staticmethod
    def get_key(direction: str) -> str:
        """Get arrow key for direction"""
        if direction == PageTurnDirection.LEFT_TO_RIGHT:
            return PageTurnDirection.LEFT_KEY
        elif direction == PageTurnDirection.RIGHT_TO_LEFT:
            return PageTurnDirection.RIGHT_KEY
        return None

# ============================================================================
# REGION DETECTION MODES
# ============================================================================
class RegionDetectionMode:
    """Region detection mode options"""
    AUTOMATIC = "Automatic"
    MANUAL = "Manual"

# ============================================================================
# ERROR MESSAGES
# ============================================================================
class ErrorMessages:
    """Standardized error messages"""
    KINDLE_WINDOW_NOT_FOUND = (
        "Kindle app window not found.\n\n"
        "Please ensure:\n"
        "1. Kindle for PC is installed and running\n"
        "2. You are logged into your Amazon account\n"
        "3. A book is open (not just the library view)\n"
        "4. The Kindle window is not minimized"
    )

    KINDLE_NO_BOOK_OPEN = (
        "WARNING: Kindle is running but no book appears to be open."
    )

    DISK_SPACE_INSUFFICIENT = (
        "Insufficient disk space in '{output_folder}'.\n"
        "Needed {needed_gb:.2f} GB, Available {available_gb:.2f} GB."
    )

    PAGE_TURN_DETECTION_FAILED = (
        "Could not determine page turn direction. Screen did not change significantly.\n\n"
        "CRITICAL ISSUES DETECTED:\n"
        "1. ★ Book is NOT open - showing library or blank screen\n"
        "2. ★ Kindle window does NOT have keyboard focus\n"
        "3. Page is covered by menus/dialogs\n\n"
        "IMMEDIATE ACTIONS REQUIRED:\n"
        "1. ★ OPEN A BOOK in Kindle (not just the library)\n"
        "2. ★ CLICK on the book page 3-4 times to ensure focus\n"
        "3. ★ MANUALLY SELECT page direction: LtoR or RtoL\n"
        "4. Close any menus or dialogs in Kindle\n"
        "5. Increase 'Page Turn Delay' to 4-5 seconds"
    )

    REGION_DETECTION_FAILED = (
        "Failed to determine book capture region. Aborting automation."
    )

    MANUAL_REGION_INVALID = (
        "Manual region mode selected, but region is invalid or not set. "
        "Aborting automation."
    )

# ============================================================================
# GUI CONSTANTS
# ============================================================================
class GUI:
    """GUI-related constants"""
    # Preview image size (reduced for better log visibility)
    PREVIEW_WIDTH = 200
    PREVIEW_HEIGHT = 250

    # Text widget configuration
    LOG_HEIGHT = 15  # lines

    # Button text
    BTN_START = "Start"
    BTN_PAUSE = "Pause"
    BTN_RESUME = "Resume"
    BTN_STOP = "Stop"
    BTN_TEST_CAPTURE = "Test Capture"
    BTN_SELECT_REGION = "Select Region"
    BTN_SELECT_OUTPUT = "Select Output Folder"

    # Section titles
    SECTION_BASIC = "Basic Settings"
    SECTION_ADVANCED = "Advanced Timing Settings"
    SECTION_REGION = "Capture Region Settings"
    SECTION_OUTPUT = "Output Settings"
    SECTION_IMAGE = "Image Optimization Settings"

# ============================================================================
# DEFAULT CONFIGURATION VALUES
# ============================================================================
class DefaultConfig:
    """Default configuration values for new installations"""
    PAGES = 100
    OPTIMIZE_IMAGES = True
    PAGE_TURN_DELAY = 3.0
    KINDLE_STARTUP_DELAY = 10.0
    WINDOW_ACTIVATION_DELAY = 3.0
    FULLSCREEN_DELAY = 3.0
    NAVIGATION_DELAY = 7.0
    PAGE_TURN_DIRECTION = PageTurnDirection.AUTOMATIC
    REGION_DETECTION_MODE = RegionDetectionMode.AUTOMATIC
    MANUAL_CAPTURE_REGION = None

    @staticmethod
    def get_output_folder():
        """Get default output folder (Downloads)"""
        return Storage.get_default_output_dir()

    @staticmethod
    def get_output_filename():
        """Get default output filename (yyyymmdd.pdf)"""
        return Storage.get_default_filename()

    # Legacy constants - use static methods instead
    OUTPUT_FOLDER = None  # Will be set dynamically
    OUTPUT_FILENAME = None  # Will be set dynamically
    IMAGE_FORMAT = "PNG"
    JPEG_QUALITY = ImageProcessing.DEFAULT_JPEG_QUALITY
    END_DETECTION_SENSITIVITY = PageDetection.DEFAULT_END_DETECTION_SENSITIVITY
