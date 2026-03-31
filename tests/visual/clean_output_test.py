#!/usr/bin/env python3
"""
Test clean output without column alignment to show pure pipe encapsulation.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logeverything.handlers import PrettyFormatter


def test_clean_output():
    print("=" * 60)
    print("CLEAN OUTPUT - NO COLUMN ALIGNMENT")
    print("=" * 60)

    # Create a logger
    logger = logging.getLogger("CleanTest")
    logger.setLevel(logging.DEBUG)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a console handler with no column alignment
    handler = logging.StreamHandler()
    formatter = PrettyFormatter(
        use_colors=False, align_columns=False  # Disable column alignment for clean output
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    print("Pure pipe encapsulation output:")
    print("-" * 35)

    # Test all log levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

    print("\nHierarchical example:")
    print("-" * 20)
    logger.info("Starting process")
    logger.debug("│ Step 1")
    logger.info("│ Step 2")
    logger.warning("│ │ Warning in substep")
    logger.error("│ │ Error occurred")
    logger.info("│ Process continues")
    logger.info("Finished")


if __name__ == "__main__":
    test_clean_output()
