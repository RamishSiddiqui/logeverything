"""
Tests for the LogEverything handlers.

This module contains tests for the different log handlers in the LogEverything library.
"""

import json

# Removed logging import
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything import CRITICAL, DEBUG, ERROR, INFO, WARNING, Logger
from logeverything.core import get_logger
from logeverything.handlers import ConsoleHandler, FileHandler, JSONHandler, PrettyFormatter


class TestConsoleHandler(unittest.TestCase):
    """Test the ConsoleHandler functionality."""

    def test_console_handler_output(self):
        """Test that ConsoleHandler correctly formats and outputs logs."""
        # Create a handler with specific settings and a StringIO as the stream
        import io

        test_stream = io.StringIO()
        handler = ConsoleHandler(stream=test_stream, level="INFO", colored=False)

        # Create a logger and add our handler
        logger = get_logger("test_console")
        logger.setLevel("INFO")
        logger.handlers = []
        logger.addHandler(handler)

        # Log a test message
        test_message = "This is a test console log"
        logger.info(test_message)

        # Flush to ensure output is written
        handler.flush()

        # Check the output
        output = test_stream.getvalue()
        self.assertIn(test_message, output)


class TestFileHandler(unittest.TestCase):
    """Test the FileHandler functionality."""

    def test_file_handler_output(self):
        """Test that FileHandler correctly writes logs to a file."""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Create a handler that writes to our temp file
            handler = FileHandler(filename=temp_path, level="INFO")

            # Verify UTF-8 encoding is set by default
            self.assertEqual(handler.encoding, "utf-8")

            # Create a logger and add our handler
            logger = get_logger("test_file")
            logger.setLevel("INFO")
            logger.handlers = []
            logger.addHandler(handler)

            # Log a test message
            test_message = "This is a test file log"
            logger.info(test_message)

            # Flush and close the handler to ensure writing is complete
            handler.flush()
            handler.close()

            # Make sure the logger doesn't reference the handler anymore
            logger.handlers = []

            # Read the file and check for our message
            with open(temp_path, "r") as f:
                content = f.read()
                self.assertIn(test_message, content)

        finally:
            # Add a small delay to ensure file is fully released
            time.sleep(0.1)
            # Clean up
            try:
                os.unlink(temp_path)
            except PermissionError:
                pass  # Skip if file is still locked (Windows issue)


class TestJSONHandler(unittest.TestCase):
    """Test the JSONHandler functionality."""

    def test_json_handler_output(self):
        """Test that JSONHandler correctly formats and writes JSON logs."""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Create a handler that writes to our temp file
            handler = JSONHandler(filename=temp_path, level="INFO", flatten=True)

            # Verify UTF-8 encoding is set by default
            self.assertEqual(handler.encoding, "utf-8")

            # Create a logger and add our handler
            logger = get_logger("test_json")
            logger.setLevel("INFO")
            logger.handlers = []
            logger.addHandler(handler)

            # Log a test message with extra fields
            test_message = "JSON test log"
            extra_data = {"user_id": 123, "action": "login"}
            logger.info(test_message, extra=extra_data)

            # Flush and close the handler to ensure writing is complete
            handler.flush()
            handler.close()

            # Remove the handler from the logger
            logger.handlers = []

            # Add a small delay to ensure file is fully released
            time.sleep(0.1)

            # Read the file and parse the JSON
            with open(temp_path, "r") as f:
                content = f.read().strip()
                log_entry = json.loads(content)

                # Check that our message and extra data are in the JSON
                self.assertEqual(log_entry.get("message"), test_message)
                self.assertEqual(log_entry.get("extra", {}).get("user_id"), 123)
                self.assertEqual(log_entry.get("extra", {}).get("action"), "login")

        finally:
            # Add a small delay to ensure file is fully released
            time.sleep(0.1)
            # Clean up
            try:
                os.unlink(temp_path)
            except PermissionError:
                pass  # Skip if file is still locked (Windows issue)


class TestMultipleHandlers(unittest.TestCase):
    """Test using multiple handlers together."""

    def test_multiple_handlers_configuration(self):
        """Test configuring multiple handlers through setup_logging."""
        # Create temporary files for testing
        file_path = None
        json_path = None

        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(delete=False) as file1:
                file_path = file1.name
            with tempfile.NamedTemporaryFile(delete=False) as json_file:
                json_path = json_file.name

            # Configure logging with multiple handlers
            file_handler = FileHandler(filename=file_path, level="INFO")
            json_handler = JSONHandler(filename=json_path, level="WARNING", flatten=True)

            logger = Logger()
            configured_logger = logger.configure(
                handlers=[file_handler, json_handler], level="DEBUG"
            )

            # Log messages at different levels
            info_message = "This is an info message"
            warn_message = "This is a warning message"
            configured_logger.info(info_message)
            configured_logger.warning(warn_message)

            # Get the actual logging.Logger instance to access handlers
            from logeverything.core import get_logger

            actual_logger = get_logger()

            # Flush the handlers (normally done at process exit)
            for handler in actual_logger.handlers:
                handler.flush()
                handler.close()

            # Remove all handlers
            actual_logger.handlers = []

            # Add a small delay to ensure files are fully released
            time.sleep(0.1)

            # Check file handler output (should have both messages)
            with open(file_path, "r") as f:
                file_content = f.read()
                self.assertIn(info_message, file_content)
                self.assertIn(warn_message, file_content)

            # Check JSON handler output (should only have warning)
            with open(json_path, "r") as f:
                json_content = f.read().strip()
                json_logs = [json.loads(line) for line in json_content.split("\n") if line.strip()]

                # Only the warning should be in the JSON file
                self.assertEqual(len(json_logs), 1)
                self.assertEqual(json_logs[0]["message"], warn_message)

        finally:
            # Add a small delay to ensure files are fully released
            time.sleep(0.1)
            # Clean up
            if file_path:
                try:
                    os.unlink(file_path)
                except PermissionError:
                    pass  # Skip if file is still locked

            if json_path:
                try:
                    os.unlink(json_path)
                except PermissionError:
                    pass  # Skip if file is still locked


class TestUnicodeHandling(unittest.TestCase):
    """Test Unicode handling in file handlers."""

    def test_file_handler_unicode_symbols(self):
        """Test that FileHandler correctly handles Unicode symbols."""
        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as temp_file:
            temp_path = temp_file.name

        try:
            # Create a handler that writes to our temp file
            handler = FileHandler(filename=temp_path, level="INFO")

            # Verify UTF-8 encoding
            self.assertEqual(handler.encoding, "utf-8")

            # Create a logger and add our handler
            logger = get_logger("test_unicode")
            logger.setLevel("INFO")
            logger.handlers = []
            logger.addHandler(handler)

            # Test Unicode symbols
            unicode_message = "Test with symbols: 🔍 ℹ️ ⚠️ ❌ ✅ 🔵"
            logger.info(unicode_message)

            # Flush and close the handler
            handler.flush()
            handler.close()
            logger.handlers = []

            # Read the file and check for Unicode symbols
            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("🔍", content)
                self.assertIn("ℹ️", content)
                self.assertIn("⚠️", content)
                self.assertIn("❌", content)
                self.assertIn("✅", content)
                self.assertIn("🔵", content)

        finally:
            time.sleep(0.1)
            try:
                os.unlink(temp_path)
            except PermissionError:
                pass


if __name__ == "__main__":
    unittest.main()
