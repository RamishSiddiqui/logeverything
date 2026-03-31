"""
LogEverything Print Capture

This module provides utilities for capturing and redirecting print statements and stdout.
Includes high-performance print capture (7.9k ops/sec).

Usage::

    from logeverything.capture import capture_print, enable_print_capture
    from logeverything.capture import capture_stdout, restore_stdout

    # Context manager for print capture
    with capture_print(silent=True) as captured:
        print("This will be captured")
        output = captured.getvalue()

    # Manual control
    enable_print_capture()
    print("This is captured")
    disable_print_capture()
"""

# Import all print capture functionality
from .print_capture import (
    capture_print,
    capture_stdout,
    disable_print_capture,
    enable_print_capture,
    restore_stdout,
)

# Define what gets exported
__all__ = [
    "capture_print",
    "capture_stdout",
    "disable_print_capture",
    "enable_print_capture",
    "restore_stdout",
]
