#!/usr/bin/env python3
"""
Test the new Logger class to ensure it provides a clean interface.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from logeverything import Logger


def test_logger_interface():
    """Test the new Logger interface."""
    print("=" * 60)
    print("TESTING NEW LOGGER INTERFACE")
    print("=" * 60)

    # Create a logger instance
    log = Logger()

    print("\nBasic logging levels:")
    log.debug("This is a debug message")
    log.info("This is an info message")
    log.warning("This is a warning message")
    log.error("This is an error message")
    log.critical("This is a critical message")

    print("\nHierarchical logging with context:")
    with log.context("Application Startup"):
        log.info("Starting application...")

        with log.context("Database Connection"):
            log.debug("Connecting to database...")
            log.info("Database connection established")
            log.warning("Connection pool size is low")

        with log.context("Service Initialization"):
            log.info("Initializing user service...")
            log.error("Failed to load user preferences")
            log.critical("Critical service failure!")

    print("\nDone!")


if __name__ == "__main__":
    test_logger_interface()
