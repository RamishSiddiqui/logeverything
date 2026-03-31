"""
Tests for the LogEverything Logger class.

This module contains comprehensive tests for the new Loguru-style Logger class
that provides a user-friendly interface for hierarchical logging.
"""

import io
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything import Logger, VisualLoggingContext
from logeverything.handlers import ConsoleHandler, PrettyFormatter


class TestLoggerClass(unittest.TestCase):
    """Test the Logger class functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a string buffer to capture log output
        self.log_output = io.StringIO()

        # Setup logging with our LogEverything components only
        self.handler = ConsoleHandler(stream=self.log_output, use_colors=False, level="DEBUG")
        self.handler.setFormatter(
            PrettyFormatter(use_colors=False, use_symbols=True, use_indent=True, align_columns=True)
        )

    def tearDown(self):
        """Clean up after tests."""
        # Close the handler
        if hasattr(self, "handler"):
            self.handler.close()
        if hasattr(self, "log_output"):
            self.log_output.close()

    def create_logger(self, name=None):
        """Create a logger for testing that uses our test handler."""
        # Create logger without auto_setup to avoid conflicts
        logger = Logger(name, auto_setup=False)
        # Ensure the logger uses our test handler
        logger.logger.handlers = [self.handler]
        logger.logger.setLevel(self.handler.level)
        logger.logger.propagate = False  # Don't propagate to root logger
        return logger

    def get_log_output(self):
        """Get the captured log output."""
        self.handler.flush()
        return self.log_output.getvalue()

    def test_logger_creation(self):
        """Test that Logger can be created with default settings."""
        logger = self.create_logger()
        self.assertIsInstance(logger, Logger)
        # With no name, it should use the caller's module name (test_logger_class in this case)
        self.assertEqual(logger.name, "test_logger_class")

    def test_logger_creation_with_name(self):
        """Test that Logger can be created with a custom name."""
        logger = self.create_logger("test_logger")
        self.assertIsInstance(logger, Logger)
        self.assertEqual(logger.name, "test_logger")

    def test_basic_logging_methods(self):
        """Test that all logging level methods work."""
        logger = self.create_logger("test_methods")

        # Test all logging methods
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        logger.exception("Exception message")

        output = self.get_log_output()

        # Check that all messages appear in output
        self.assertIn("Debug message", output)
        self.assertIn("Info message", output)
        self.assertIn("Warning message", output)
        self.assertIn("Error message", output)
        self.assertIn("Critical message", output)
        self.assertIn("Exception message", output)

    def test_logging_with_symbols(self):
        """Test that symbols appear in the output."""
        logger = self.create_logger("test_symbols")

        logger.debug("Debug with symbol")
        logger.info("Info with symbol")
        logger.warning("Warning with symbol")
        logger.error("Error with symbol")
        logger.critical("Critical with symbol")

        output = self.get_log_output()

        # Check for symbols (these should be in brackets due to our formatting)
        self.assertIn("🔍", output)  # Debug symbol
        self.assertIn("ℹ️", output)  # Info symbol
        self.assertIn("⚠️", output)  # Warning symbol
        self.assertIn("❌", output)  # Error symbol
        self.assertIn("🔥", output)  # Critical symbol

    def test_context_manager(self):
        """Test that the context manager creates hierarchical structure."""
        logger = self.create_logger("test_context")

        logger.info("Starting test")

        with logger.context("Test Context"):
            logger.info("Inside context")
            logger.debug("Debug inside context")

            with logger.context("Nested Context"):
                logger.warning("Nested warning")
                logger.error("Nested error")

        logger.info("After context")

        output = self.get_log_output()

        # Check that context messages appear
        self.assertIn("Starting test", output)
        self.assertIn("Inside context", output)
        self.assertIn("Debug inside context", output)
        self.assertIn("Nested warning", output)
        self.assertIn("Nested error", output)
        self.assertIn("After context", output)

    def test_multiple_loggers(self):
        """Test that multiple loggers work independently."""
        logger1 = self.create_logger("logger_one")
        logger2 = self.create_logger("logger_two")

        logger1.info("Message from logger one")
        logger2.warning("Message from logger two")

        output = self.get_log_output()

        # Check both messages and logger names appear
        self.assertIn("Message from logger one", output)
        self.assertIn("Message from logger two", output)
        self.assertIn("logger_one", output)
        self.assertIn("logger_two", output)

    def test_logger_name_propagation(self):
        """Test that logger name appears in output."""
        logger = self.create_logger("custom_logger_name")

        logger.info("Test message")

        output = self.get_log_output()

        # Check that logger name appears in output
        self.assertIn("custom_logger_name", output)

    def test_exception_logging(self):
        """Test exception logging functionality."""
        logger = self.create_logger("test_exception")

        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("Caught an exception")

        output = self.get_log_output()

        # Check exception message appears
        self.assertIn("Caught an exception", output)
        # Check that exception traceback appears
        self.assertIn("ValueError", output)
        self.assertIn("Test exception", output)


if __name__ == "__main__":
    unittest.main()
