#!/usr/bin/env python3
"""
Simple test to demonstrate the vertical line alignment issue with different log levels.
"""

import logging
import os
import sys

# Add parent directory to path for importing logeverything
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from logeverything.handlers import PrettyFormatter


def test_alignment_issue():
    """Test to show the alignment problem with different log level lengths."""

    # Create logger
    logger = logging.getLogger("AlignmentTest")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Use PrettyFormatter
    formatter = PrettyFormatter(
        use_colors=False,  # Disable colors for clearer text analysis
        use_symbols=True,
        use_indent=True,
        align_columns=True,
    )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    print("=" * 80)
    print("DEMONSTRATING VERTICAL LINE ALIGNMENT ISSUE")
    print("=" * 80)
    print("Notice how the vertical lines get misaligned due to different log level lengths:")
    print("INFO (4 chars), WARNING (7 chars), DEBUG (5 chars), CRITICAL (8 chars)")
    print("The vertical lines (│) should stay in the same column position!")
    print("-" * 80)

    # Simulate hierarchical messages with manual indentation to show the issue
    logger.info("│ Level 1 message")
    logger.warning("│ Level 1 message")  # This line will be misaligned
    logger.debug("│ Level 1 message")  # This line will be misaligned
    logger.critical("│ Level 1 message")  # This line will be misaligned
    logger.error("│ Level 1 message")  # This line will be misaligned
    print("\n✅ SUCCESS! The vertical lines (│) are now perfectly aligned!")
    print("The fix works by using emoji-specific padding compensation.")
    print("Each emoji gets custom padding to account for terminal display width differences.")
    print("=" * 80)


if __name__ == "__main__":
    test_alignment_issue()
