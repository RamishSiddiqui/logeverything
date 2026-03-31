"""
Formatting utility functions for the LogEverything library.
"""

from typing import Any


def safe_int(val: Any, default: int) -> int:
    """
    Safely convert a value to int with a default.

    Args:
        val: The value to convert
        default: Default value if conversion fails

    Returns:
        int: The converted integer or default value
    """
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str) and val.isdigit():
        return int(val)
    return default


def safe_float(val: Any, default: float) -> float:
    """
    Safely convert a value to float with a default.

    Args:
        val: The value to convert
        default: Default value if conversion fails

    Returns:
        float: The converted float or default value
    """
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except ValueError:
            pass
    return default


def format_value(value: Any, max_length: int = 300) -> str:
    """
    Format a value for logging with proper truncation.

    Args:
        value: The value to format
        max_length: Maximum length before truncation

    Returns:
        str: The formatted value string
    """
    try:
        if isinstance(value, (list, tuple, set)) and len(value) > 5:
            # For collections, show first few elements
            value_str = f"{type(value).__name__}({str(list(value)[:3])[:-1]}, ...)"
        else:
            value_str = repr(value)

        # Truncate if too long
        if len(value_str) > max_length:
            return f"{value_str[:max_length-3]}..."

        return value_str
    except Exception:
        return f"<unprintable {type(value).__name__} object>"
