"""
Configuration management module.
Handles loading, saving, and validation of application configuration.
"""

import json
import os
from typing import Dict, Any, Tuple, Optional
from src.constants import Storage, DefaultConfig

CONFIG_FILE = Storage.CONFIG_FILENAME


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass


class ConfigValidator:
    """Validates configuration dictionaries"""

    # Define validation rules for essential settings only
    VALIDATION_RULES = {
        "pages": {
            "type": int,
            "min": 1,
            "max": 10000,
            "description": "Number of pages to capture"
        },
        "output_folder": {
            "type": str,
            "description": "Output folder path"
        },
        "output_filename": {
            "type": str,
            "description": "Output PDF filename"
        }
    }

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate a configuration dictionary.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        for key, rules in cls.VALIDATION_RULES.items():
            # Check if key exists in config
            if key not in config:
                return False, f"Missing required config key: '{key}'"

            value = config[key]

            # Type validation
            if not isinstance(value, rules["type"]):
                expected = rules["type"].__name__
                actual = type(value).__name__
                return False, (
                    f"Invalid type for '{key}': expected {expected}, got {actual}. "
                    f"{rules['description']}."
                )

            # Range validation (min/max)
            if "min" in rules and value < rules["min"]:
                return False, (
                    f"Value for '{key}' ({value}) is below minimum ({rules['min']}). "
                    f"{rules['description']}."
                )

            if "max" in rules and value > rules["max"]:
                return False, (
                    f"Value for '{key}' ({value}) exceeds maximum ({rules['max']}). "
                    f"{rules['description']}."
                )

        return True, None

    @classmethod
    def validate_and_raise(cls, config: Dict[str, Any]) -> None:
        """
        Validate configuration and raise exception if invalid.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ConfigValidationError: If configuration is invalid
        """
        is_valid, error_message = cls.validate_config(config)
        if not is_valid:
            raise ConfigValidationError(error_message)

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

