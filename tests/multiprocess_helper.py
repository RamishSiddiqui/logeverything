"""
Tests for multiprocessing with LogEverything.

This module tests the integration of LogEverything with multiprocessing.
"""

import logging
import os
import sys
import unittest

# Add the parent directory to the path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything.core import get_logger


def test_multiprocess_logging_windows_compatible():
    """Test logging from multiple processes in a Windows-compatible way."""
    # Create a temp log file
    log_file = os.path.join(os.path.dirname(__file__), "temp_multiprocess.log")
    try:
        # Set up a file handler
        file_handler = logging.FileHandler(log_file, mode="w")
        file_handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))

        # Configure multiple loggers simulating different processes
        for i in range(3):
            process_logger = get_logger(f"simulated_process_{i}")
            process_logger.addHandler(file_handler)
            process_logger.setLevel(logging.INFO)
            process_logger.info(f"Info from simulated process {i}")

        # Close the handler to ensure file is written
        file_handler.close()

        # Verify log content
        with open(log_file, "r") as f:
            log_content = f.read()

        # Check that all simulated processes logged successfully
        all_logs_present = True
        for i in range(3):
            log_msg = f"simulated_process_{i} - INFO - Info from simulated process {i}"
            if log_msg not in log_content:
                all_logs_present = False
                break

        return all_logs_present
    finally:
        # Clean up
        if os.path.exists(log_file):
            os.remove(log_file)

    return False  # Default to failure
