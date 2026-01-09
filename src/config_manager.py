import json
import os

CONFIG_FILE = "config.json"

def get_default_config():
    """Returns a dictionary with the default configuration values."""
    return {
        "pages": 100,
        "optimize_images": True,
        "page_turn_delay": 3,  # Increased from 1.5 to 3 for better page turn detection
        "kindle_startup_delay": 10,
        "window_activation_delay": 3,
        "fullscreen_delay": 3,
        "navigation_delay": 7,
        "page_turn_direction": "Automatic", # Options: "Automatic", "LtoR", "RtoL"
        "region_detection_mode": "Automatic", # Options: "Automatic", "Manual"
        "manual_capture_region": None, # Stored as [x, y, w, h]
        "output_folder": "Kindle_PDFs",
        "output_filename": "My_Kindle_Book.pdf",
        "image_format": "PNG", # Options: "PNG", "JPEG"
        "jpeg_quality": 90, # For JPEG format, 0-100
        "end_detection_sensitivity": 3 # Number of consecutive identical pages to detect end of book
    }

def load_config():
    """Loads the configuration from config.json. If the file doesn't exist, returns default config."""
    if not os.path.exists(CONFIG_FILE):
        return get_default_config()
    
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            # Ensure all default keys are present
            defaults = get_default_config()
            for key, value in defaults.items():
                if key not in config:
                    config[key] = value
            return config
    except (json.JSONDecodeError, IOError):
        # If file is corrupted or unreadable, return defaults
        return get_default_config()

def save_config(config):
    """Saves the given configuration dictionary to config.json."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except IOError as e:
        # Handle cases where the file cannot be written
        print(f"Error saving config file: {e}")

