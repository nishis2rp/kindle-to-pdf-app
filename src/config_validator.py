"""
Simplified Configuration validation module.
Only validates essential settings: pages, output_folder, output_filename.
"""

from typing import Dict, Any, Tuple, Optional


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass


class ConfigValidator:
    """Validates simplified configuration dictionaries"""

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
