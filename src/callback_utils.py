"""
Callback utility functions for handling status, error, and other callbacks.
"""
from typing import Optional, Callable


def default_callback(prefix: str) -> Callable[[str], None]:
    """
    Create a default callback function that prints messages with a prefix.

    Args:
        prefix: The prefix to use for messages (e.g., "Status", "Error")

    Returns:
        A callback function that prints messages
    """
    return lambda msg: print(f"{prefix}: {msg}")


def get_callback_or_default(callback: Optional[Callable], prefix: str) -> Callable:
    """
    Get the provided callback or return a default one.

    Args:
        callback: The provided callback function or None
        prefix: The prefix to use for default callback

    Returns:
        The provided callback or a default callback
    """
    return callback if callback else default_callback(prefix)
