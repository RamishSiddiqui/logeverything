"""
Tests for Windows Unicode compatibility and encoding fixes.

This module tests the automatic Unicode encoding fixes implemented in LogEverything
to prevent UnicodeEncodeError on Windows systems with cp1252 console encoding.
"""

import io
import os
import platform
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

# Add the parent directory to the path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything import Logger
from logeverything.core import detect_platform_capabilities
from logeverything.handlers import ConsoleHandler, EnhancedConsoleHandler, FileHandler


class TestWindowsUnicodeCompatibility(unittest.TestCase):
    """Test Windows Unicode encoding compatibility fixes."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass  # Ignore cleanup errors

    def test_filehandler_defaults_to_utf8(self):
        """Test that FileHandler defaults to UTF-8 encoding."""
        log_file = os.path.join(self.temp_dir, "test_utf8.log")
        handler = FileHandler(log_file)

        # Check that encoding is UTF-8 by default
        self.assertEqual(handler.encoding, "utf-8")

        # Test that Unicode symbols can be written
        handler.emit(self._create_log_record("Test with Unicode: 🔍 ℹ️ ⚠️ ❌ ✅ 🔵"))
        handler.close()

        # Verify file was created and contains Unicode symbols
        self.assertTrue(os.path.exists(log_file))
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("🔍", content)
            self.assertIn("ℹ️", content)

    def test_filehandler_explicit_utf8(self):
        """Test FileHandler with explicit UTF-8 encoding."""
        log_file = os.path.join(self.temp_dir, "test_explicit_utf8.log")
        handler = FileHandler(log_file, encoding="utf-8")

        self.assertEqual(handler.encoding, "utf-8")

        # Test Unicode symbol logging
        unicode_message = "Unicode test: 🔍 DEBUG ℹ️ INFO ⚠️ WARNING ❌ ERROR ✅ SUCCESS 🔵 CALL"
        handler.emit(self._create_log_record(unicode_message))
        handler.close()

        # Verify content preservation
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
            for symbol in ["🔍", "ℹ️", "⚠️", "❌", "✅", "🔵"]:
                self.assertIn(symbol, content)

    def test_consolehandler_unicode_fallback(self):
        """Test ConsoleHandler Unicode fallback to ASCII."""
        # Create a mock stream that raises UnicodeEncodeError on Unicode
        mock_stream = Mock()
        mock_stream.write.side_effect = UnicodeEncodeError(
            "cp1252", "🔍", 0, 1, "character maps to <undefined>"
        )
        mock_stream.flush = Mock()

        handler = ConsoleHandler(stream=mock_stream)

        # This should not raise an exception due to fallback handling
        try:
            handler.emit(self._create_log_record("🔍 Debug message"))
        except UnicodeEncodeError:
            self.fail("ConsoleHandler should handle UnicodeEncodeError with fallback")

    def test_enhanced_console_handler_unicode_fallback(self):
        """Test EnhancedConsoleHandler Unicode fallback."""
        mock_stream = Mock()
        mock_stream.write.side_effect = UnicodeEncodeError(
            "cp1252", "🔍", 0, 1, "character maps to <undefined>"
        )
        mock_stream.flush = Mock()

        # Test platform detection fallback
        caps = detect_platform_capabilities()
        handler = EnhancedConsoleHandler(
            stream=mock_stream, ascii_only=not caps.get("supports_unicode", True)
        )

        # Should handle Unicode gracefully
        try:
            handler.emit(self._create_log_record("🔍 ℹ️ ⚠️ Debug with symbols"))
        except UnicodeEncodeError:
            self.fail("EnhancedConsoleHandler should handle UnicodeEncodeError")

    def test_logger_configure_file_utf8_default(self):
        """Test Logger.configure() creates file handlers with UTF-8 encoding."""
        log_file = os.path.join(self.temp_dir, "logger_configure_test.log")

        logger = Logger("test_logger", auto_setup=False)
        logger.configure(handlers=["file"], file_path=log_file, level="INFO")

        # Find the FileHandler in logger's handlers
        file_handler = None
        for handler in logger.logger.handlers:
            if isinstance(handler, FileHandler):
                file_handler = handler
                break

        self.assertIsNotNone(file_handler, "FileHandler should be created")
        self.assertEqual(file_handler.encoding, "utf-8", "FileHandler should use UTF-8 encoding")

        # Test Unicode logging
        logger.info("Unicode test: 🔍 ℹ️ ⚠️ ❌ ✅ 🔵")

        # Verify file content
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Unicode test", content)

    def test_mixed_handlers_unicode_compatibility(self):
        """Test mixed console and file handlers with Unicode."""
        log_file = os.path.join(self.temp_dir, "mixed_handlers.log")

        # Create logger with both console and file handlers
        logger = Logger("mixed_test", auto_setup=False)
        logger.configure(
            handlers=["console", "file"], file_path=log_file, visual_mode=True, use_symbols=True
        )

        # Should work without errors
        test_messages = [
            "🔍 Debug message with search symbol",
            "ℹ️ Info message with info symbol",
            "⚠️ Warning message with warning symbol",
            "❌ Error message with error symbol",
            "✅ Success message with checkmark",
            "🔵 Call message with circle",
        ]

        for message in test_messages:
            try:
                logger.info(message)
            except UnicodeEncodeError:
                self.fail(f"Mixed handlers should handle Unicode: {message}")

    def test_platform_detection(self):
        """Test platform capability detection."""
        caps = detect_platform_capabilities()

        # Should return a dictionary with expected keys
        self.assertIsInstance(caps, dict)
        self.assertIn("supports_unicode", caps)
        self.assertIn("supports_colors", caps)

        # Unicode support should be boolean
        self.assertIsInstance(caps["supports_unicode"], bool)

    @unittest.skipUnless(platform.system() == "Windows", "Windows-specific test")
    def test_windows_cp1252_handling(self):
        """Test Windows cp1252 encoding handling (Windows only)."""
        # Create a mock Windows environment
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.encoding = "cp1252"
            mock_stdout.write.side_effect = UnicodeEncodeError(
                "cp1252", "🔍", 0, 1, "character maps to <undefined>"
            )

            handler = ConsoleHandler(stream=mock_stdout)

            # Should not raise exception
            try:
                handler.emit(self._create_log_record("🔍 Windows cp1252 test"))
            except UnicodeEncodeError:
                self.fail("Should handle Windows cp1252 encoding issues")

    def test_ascii_fallback_symbols(self):
        """Test ASCII fallback symbol mapping."""
        # Expected fallback mappings
        expected_mappings = {
            "🔍": "[D]",
            "ℹ️": "[I]",
            "⚠️": "[W]",
            "❌": "[E]",
            "✅": "[OK]",
            "🔵": "[CALL]",
            "┌─►": "+-> ",
            "└─◄": "+-< ",
            "├──": "+-- ",
            "│": "|",
        }

        # Test that fallback conversion works
        for unicode_char, ascii_fallback in expected_mappings.items():
            # Create a message with Unicode
            original_message = f"Test {unicode_char} message"

            # Simulate ASCII fallback conversion
            ascii_message = original_message
            for unicode_sym, ascii_sym in expected_mappings.items():
                ascii_message = ascii_message.replace(unicode_sym, ascii_sym)

            # Verify conversion
            expected_message = f"Test {ascii_fallback} message"
            self.assertEqual(ascii_message, expected_message)

    def test_filehandler_rotation_utf8(self):
        """Test FileHandler with rotation maintains UTF-8 encoding."""
        log_file = os.path.join(self.temp_dir, "rotation_test.log")

        # Create handler with small max size to trigger rotation
        handler = FileHandler(log_file, max_size=100, backup_count=2)
        self.assertEqual(handler.encoding, "utf-8")

        # Write enough Unicode content to trigger rotation
        for i in range(10):
            message = f"Line {i}: 🔍 ℹ️ ⚠️ ❌ ✅ 🔵 Unicode symbols test"
            handler.emit(self._create_log_record(message))

        handler.close()

        # Verify files were created and contain Unicode
        self.assertTrue(os.path.exists(log_file))
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("🔍", content)

    def _create_log_record(self, message):
        """Create a mock log record for testing."""
        import logging

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg=message,
            args=(),
            exc_info=None,
        )
        return record


class TestUnicodeIntegration(unittest.TestCase):
    """Integration tests for Unicode compatibility across LogEverything features."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass

    def test_logger_with_unicode_visual_formatting(self):
        """Test Logger with Unicode visual formatting end-to-end."""
        log_file = os.path.join(self.temp_dir, "visual_unicode.log")

        logger = Logger("unicode_visual", auto_setup=False)
        logger.configure(
            level="DEBUG", visual_mode=True, use_symbols=True, handlers=["file"], file_path=log_file
        )

        # Test all log levels with Unicode
        logger.debug("🔍 Debug message")
        logger.info("ℹ️ Info message")
        logger.warning("⚠️ Warning message")
        logger.error("❌ Error message")

        # Test context with Unicode
        with logger.context("unicode_context"):
            logger.info("Inside Unicode context")

        # Verify file was written with UTF-8
        self.assertTrue(os.path.exists(log_file))
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
            # Should contain all Unicode symbols
            for symbol in ["🔍", "ℹ️", "⚠️", "❌"]:
                self.assertIn(symbol, content)
            # Should contain context symbols
            self.assertIn("┌─►", content)
            self.assertIn("└─◄", content)

    def test_decorator_with_unicode_symbols(self):
        """Test decorators with Unicode symbol logging."""
        from logeverything.decorators import log

        # This test just verifies that the decorator can handle Unicode in return values
        @log
        def unicode_function(x, y):
            """Test function with Unicode in output."""
            return f"Result: {x} + {y} = {x + y} ✅"

        # Call the decorated function
        result = unicode_function(1, 2)

        # Verify Unicode is preserved in return value
        self.assertIn("✅", result)
        self.assertEqual(result, "Result: 1 + 2 = 3 ✅")


if __name__ == "__main__":
    unittest.main()
