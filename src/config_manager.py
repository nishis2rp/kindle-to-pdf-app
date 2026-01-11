"""
Configuration management module.
Handles loading, saving, and validation of application configuration.
"""

import json
import os
from typing import Dict, Any
from src.constants import Storage, DefaultConfig
from src.config_validator import ConfigValidator, ConfigValidationError

CONFIG_FILE = Storage.CONFIG_FILENAME

def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration values (simplified).

    Returns:
        Dictionary containing default configuration
    """
    return {
        "pages": DefaultConfig.PAGES,
        "output_folder": DefaultConfig.get_output_folder(),
        "output_filename": DefaultConfig.get_output_filename(),
    }

def load_config() -> Dict[str, Any]:
    """
    Load configuration from file with validation.

    Returns:
        Configuration dictionary (defaults if file doesn't exist or is invalid)
    """
    if not os.path.exists(CONFIG_FILE):
        return get_default_config()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)

            # Merge with defaults for missing keys
            defaults = get_default_config()
            for key, value in defaults.items():
                if key not in config:
                    config[key] = value

            # Validate configuration
            is_valid, error_message = ConfigValidator.validate_config(config)
            if not is_valid:
                print(f"Config validation warning: {error_message}")
                print("Using default configuration instead.")
                return get_default_config()

            return config

    except json.JSONDecodeError as e:
        print(f"Error parsing config file: {e}. Using default configuration.")
        return get_default_config()
    except IOError as e:
        print(f"Error reading config file: {e}. Using default configuration.")
        return get_default_config()


def save_config(config: Dict[str, Any]) -> bool:
    """
    Save configuration to file after validation.

    Args:
        config: Configuration dictionary to save

    Returns:
        True if save successful, False otherwise
    """
    try:
        # Validate before saving
        ConfigValidator.validate_and_raise(config)

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        return True

    except ConfigValidationError as e:
        print(f"Configuration validation error: {e}")
        return False
    except IOError as e:
        print(f"Error saving config file: {e}")
        return False

