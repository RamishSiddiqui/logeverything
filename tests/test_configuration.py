"""
Tests for the LogEverything configuration functionality.

This module tests the configuration and setup functionality of LogEverything.
"""

import builtins
import multiprocessing
import os
import sys
import threading
import time
import unittest
from unittest.mock import patch

# Add the parent directory to the path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging  # For NullHandler in performance test

# Import configure from core module for internal testing
from logeverything import DEBUG, INFO, WARNING, Logger  # Import level constants
from logeverything import core as core_module
from logeverything.capture.print_capture import _original_print
from logeverything.core import get_logger
from logeverything.decorators import log_function
from logeverything.handlers import FileHandler


class TestConfiguration(unittest.TestCase):
    """Test the configuration functionality of LogEverything."""

    def setUp(self):
        """Set up test fixtures."""  # Reset configuration between tests
        core_module.configure(
            level="INFO",
            log_entry_exit=True,
            log_arguments=True,
            log_return_values=True,
            beautify=True,
            indent_level=2,
        )

    def test_level_configuration(self):
        """Test setting different log levels."""  # Configure with DEBUG level
        core_module.configure(level="DEBUG")
        logger = get_logger("test_level")

        # Mock the logger's handle method
        with patch("logging.Logger.handle") as mock_handle:
            # Log at different levels
            logger.debug("Debug message")
            logger.info("Info message")

            # Both should be logged at DEBUG level
            self.assertEqual(mock_handle.call_count, 2)  # Reconfigure with INFO level
        core_module.configure(level="INFO")

        # Mock the logger's handle method again
        with patch("logging.Logger.handle") as mock_handle:
            # Log again
            logger.debug("Debug message")
            logger.info("Info message")

            # Only INFO should be logged
            self.assertEqual(mock_handle.call_count, 1)
            args, kwargs = mock_handle.call_args
            self.assertEqual(args[0].getMessage(), "Info message")

    def test_beautify_configuration(self):
        """Test beautify configuration option."""
        # Configure with beautify=True (default)
        core_module.configure(beautify=True)


        # Test with beautify=True - the actual formatting is done in the record formatter
        # We just need to ensure the right configuration is applied
        self.assertTrue(core_module.configure()["beautify"])

        # Configure with beautify=False
        core_module.configure(beautify=False)
        self.assertFalse(core_module.configure()["beautify"])

    def test_indent_level_configuration(self):
        """Test indent level configuration."""
        # Configure with custom indent level
        core_module.configure(indent_level=4)

        # Verify the indent level was set
        self.assertEqual(core_module.configure()["indent_level"], 4)

    def test_setup_logging_integration(self):
        """Test the core.configure function configures everything correctly."""
        # Configure via core module (global configuration)
        core_module.configure(level="WARNING", log_entry_exit=False, log_arguments=False)

        # Verify configuration was applied
        config = core_module.configure()
        self.assertFalse(config["log_entry_exit"])
        self.assertFalse(config["log_arguments"])

    def test_print_capture_configuration(self):
        """Test configuration of print capturing."""
        # Check default state - print capture should be disabled
        self.assertFalse(core_module.configure()["capture_print"])
        self.assertEqual(builtins.print, _original_print)

        # Enable print capture via configuration
        core_module.configure(capture_print=True)

        # Verify configuration was applied
        self.assertTrue(core_module.configure()["capture_print"])
        self.assertNotEqual(builtins.print, _original_print)

        # Disable print capture
        core_module.configure(capture_print=False)

        # Verify print function is restored
        self.assertFalse(core_module.configure()["capture_print"])
        self.assertEqual(builtins.print, _original_print)

    def test_print_capture_custom_config(self):
        """Test custom configuration options for print capture."""
        # Configure with custom print capture settings
        core_module.configure(
            capture_print=True,
            print_logger_name="custom_logger",
            print_level="WARNING",
            print_prefix="[CUSTOM] ",
        )

        # Verify configuration was applied
        config = core_module.configure()
        self.assertTrue(config["capture_print"])
        self.assertEqual(config["print_logger_name"], "custom_logger")
        self.assertEqual(config["print_level"], "WARNING")
        self.assertEqual(config["print_prefix"], "[CUSTOM] ")

        # Disable print capture
        core_module.configure(capture_print=False)

    def test_instance_based_configuration(self):
        """Test the new instance-based configuration API."""
        # Create a logger instance
        logger = Logger("test_instance")

        # Configure using instance method (instance-level, not global)
        logger.configure(level="DEBUG", visual_mode=True, use_symbols=True, beautify=True)

        # Logger.configure() is instance-based, check the logger's own level
        self.assertEqual(logger.logger.level, DEBUG)
        self.assertTrue(logger._options.get("visual_mode"))
        self.assertTrue(logger._options.get("use_symbols"))
        self.assertTrue(logger._options.get("beautify"))

        # Test that we can reconfigure using the instance
        logger.configure(level="INFO", visual_mode=False)
        self.assertEqual(logger.logger.level, INFO)
        self.assertFalse(logger._options.get("visual_mode"))

        # Test that the logger instance methods work correctly
        self.assertTrue(hasattr(logger, "info"))
        self.assertTrue(hasattr(logger, "debug"))
        self.assertTrue(hasattr(logger, "warning"))

        # Test that multiple Logger instances are independent
        logger2 = Logger("test_instance2")
        logger2.configure(level="WARNING", beautify=False)

        # Each logger has its own configuration
        self.assertEqual(logger2.logger.level, WARNING)
        self.assertFalse(logger2._options.get("beautify"))

    # ...existing code...


class TestConcurrentLogging(unittest.TestCase):
    """Test logging in multi-threaded and multi-process environments."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset configuration between tests
        core_module.configure(level="INFO")

    def test_threaded_logging(self):
        """Test logging from multiple threads."""
        results = []

        def log_from_thread(thread_id):
            # Configure a logger for this thread
            get_logger(f"thread_{thread_id}")
            # Perform a logged operation and collect result
            results.append(f"Thread {thread_id} logged")

        # Create and start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_from_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()  # Verify results
        self.assertEqual(len(results), 5)
        for i in range(5):
            self.assertIn(f"Thread {i} logged", results)

    def test_multiprocess_logging(self):
        """Test logging from multiple processes."""
        if sys.platform.startswith("win") or sys.platform == "darwin":
            # On Windows, we'll use a simulated approach instead of actual multiprocessing
            # This avoids issues with process spawning on Windows

            # Create a temp log file
            log_file = os.path.join(os.path.dirname(__file__), "temp_multiprocess.log")
            try:
                # Set up a file handler with a simple formatter (not PrettyFormatter
                # which truncates long logger names)
                file_handler = FileHandler(log_file, mode="w", encoding="utf-8")
                file_handler.setFormatter(
                    logging.Formatter("%(name)s - %(levelname)s - %(message)s")
                )

                # Configure multiple loggers simulating different processes
                for i in range(3):
                    process_logger = get_logger(f"simulated_process_{i}")
                    process_logger.addHandler(file_handler)
                    process_logger.setLevel("INFO")
                    process_logger.info(f"Simulated {i}")

                # Close the handler to ensure file is written
                file_handler.close()

                # Verify log content
                with open(log_file, "r") as f:
                    log_content = f.read()

                # Check that all simulated processes logged successfully
                for i in range(3):
                    self.assertIn(
                        f"logeverything.simulated_process_{i} - INFO - Simulated {i}",
                        log_content,
                    )
            finally:
                # Clean up
                if os.path.exists(log_file):
                    os.remove(log_file)
        else:

            def log_from_process(process_id):
                # Configure a logger for this process
                logger = get_logger(f"process_{process_id}")
                logger.info(f"Info from process {process_id}")
                return process_id

            # Create and start multiple processes
            processes = []
            for i in range(3):
                process = multiprocessing.Process(target=log_from_process, args=(i,))
                processes.append(process)
                process.start()

            # Wait for all processes to complete
            for process in processes:
                process.join()
                self.assertEqual(process.exitcode, 0)


class TestPerformance(unittest.TestCase):
    """Test the performance characteristics of the logger."""

    def test_logging_overhead(self):
        """Test the overhead of logging."""  # Configure with a null handler to minimize I/O impact
        null_handler = logging.NullHandler()
        logger = get_logger("performance_test")
        logger.handlers = [null_handler]
        logger.setLevel("DEBUG")

        # Measure time for normal function calls
        def normal_function(a, b):
            return a + b

        start_time = time.time()
        for _ in range(1000):
            normal_function(1, 2)
        normal_time = time.time() - start_time

        # Measure time for logged function calls
        @log_function
        def logged_function(a, b):
            return a + b

        start_time = time.time()
        for _ in range(1000):
            logged_function(1, 2)
        logged_time = time.time() - start_time

        # The logged version will be slower, but should not be extremely slow
        # Avoid division by zero
        if normal_time > 0:
            overhead_ratio = logged_time / normal_time
            self.assertLess(overhead_ratio, 100)
        else:
            # If normal_time is negligible, ensure logged_time is still reasonable
            self.assertLess(logged_time, 1.0)  # Less than 1 second for 1000 iterations


if __name__ == "__main__":
    unittest.main()
