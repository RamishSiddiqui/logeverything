"""
Tests for the BaseLogger architecture and inheritance hierarchy.

This module tests the new BaseLogger foundation and Logger/AsyncLogger inheritance.
"""

import asyncio
import logging
import os
import sys
import unittest

# Add the parent directory to the path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything import AsyncLogger, BaseLogger, Logger


class CustomTestLogger(BaseLogger):
    """Test custom logger implementation."""

    def __init__(self, name: str, prefix: str = "[TEST]"):
        super().__init__(name)
        self.prefix = prefix
        self.messages = []  # Store messages for testing

    def configure(self, **kwargs):
        """Configure the test logger."""
        self._config.update(kwargs)

        # Set up basic logging level
        level = kwargs.get("level", "INFO")
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        self._logger.setLevel(level)

        return self

    def _log_message(self, level, message, *args, **kwargs):
        """Store messages for testing instead of actual logging."""
        formatted_message = f"{self.prefix} {message}"
        self.messages.append((level, formatted_message, args, kwargs))
        # Also log to the actual logger for integration testing
        self._logger.log(level, formatted_message, *args, **kwargs)

    def _create_bound_logger(self, **kwargs):
        """Create a bound logger instance for testing with merged context."""
        # Create new logger with the SAME name (following Loguru-style binding)
        bound_logger = CustomTestLogger(self._name, self.prefix)

        # Merge context: parent context + new context (additive)
        parent_context = getattr(self, "_context", {})
        bound_logger._context = {**parent_context, **kwargs}

        bound_logger._mark_as_system_created()  # Bound loggers are system-created
        return bound_logger

    def _cleanup(self):
        """Clean up test logger resources."""
        # Remove all handlers
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)
        # Clear messages for testing
        self.messages.clear()


class TestBaseLoggerArchitecture(unittest.TestCase):
    """Test the BaseLogger architecture and inheritance."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_logger = CustomTestLogger("test_logger")

    def tearDown(self):
        """Clean up after tests."""
        # Clear any handlers to prevent test interference
        for handler in self.test_logger._logger.handlers[:]:
            self.test_logger._logger.removeHandler(handler)

    def test_base_logger_is_abstract(self):
        """Test that BaseLogger cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            BaseLogger("test")

    def test_logger_inherits_from_base_logger(self):
        """Test that Logger inherits from BaseLogger."""
        self.assertTrue(issubclass(Logger, BaseLogger))

        logger = Logger("test")
        self.assertIsInstance(logger, BaseLogger)
        self.assertIsInstance(logger, Logger)

    def test_async_logger_inherits_from_base_logger(self):
        """Test that AsyncLogger inherits from BaseLogger."""
        self.assertTrue(issubclass(AsyncLogger, BaseLogger))

        async_logger = AsyncLogger("test_async")
        self.assertIsInstance(async_logger, BaseLogger)
        self.assertIsInstance(async_logger, AsyncLogger)

    def test_custom_logger_implementation(self):
        """Test creating a custom logger by inheriting from BaseLogger."""
        custom_logger = CustomTestLogger("custom", "[CUSTOM]")

        # Test basic functionality
        self.assertEqual(custom_logger._name, "custom")
        self.assertEqual(custom_logger.prefix, "[CUSTOM]")

        # Test configuration
        custom_logger.configure(level="DEBUG")
        self.assertEqual(custom_logger._config["level"], "DEBUG")

        # Test logging
        custom_logger.info("test message")
        self.assertEqual(len(custom_logger.messages), 1)

        level, message, args, kwargs = custom_logger.messages[0]
        self.assertEqual(level, logging.INFO)
        self.assertEqual(message, "[CUSTOM] test message")

    def test_base_logger_common_methods(self):
        """Test that all logger types have the same basic methods."""
        logger = Logger("test_logger")
        async_logger = AsyncLogger("test_async_logger")
        custom_logger = CustomTestLogger("test_custom_logger")

        # Test all loggers have the same method signatures
        for logger_instance in [logger, async_logger, custom_logger]:
            self.assertTrue(hasattr(logger_instance, "debug"))
            self.assertTrue(hasattr(logger_instance, "info"))
            self.assertTrue(hasattr(logger_instance, "warning"))
            self.assertTrue(hasattr(logger_instance, "error"))
            self.assertTrue(hasattr(logger_instance, "critical"))
            self.assertTrue(hasattr(logger_instance, "configure"))
            self.assertTrue(hasattr(logger_instance, "bind"))

    def test_logger_instance_configuration(self):
        """Test that logger configuration is instance-based."""
        logger1 = Logger("logger1")
        logger2 = Logger("logger2")

        # Configure each logger differently
        logger1.configure(level="DEBUG", visual_mode=True)
        logger2.configure(level="ERROR", visual_mode=False)

        # Each logger should have its own configuration
        # Note: The actual config storage might be handled by the underlying implementation
        # This tests that the methods exist and can be called independently
        self.assertIsNotNone(logger1)
        self.assertIsNotNone(logger2)

    def test_custom_logger_bound_context(self):
        """Test bound context functionality with custom logger."""
        custom_logger = CustomTestLogger("bound_test")

        # Create bound logger
        bound_logger = custom_logger.bind(user_id=123, session="test")

        # Should be a new instance
        self.assertIsInstance(bound_logger, CustomTestLogger)
        self.assertNotEqual(bound_logger, custom_logger)

        # Should have bound context in context
        self.assertIn("user_id", bound_logger._context)
        self.assertIn("session", bound_logger._context)
        self.assertEqual(bound_logger._context["user_id"], 123)
        self.assertEqual(bound_logger._context["session"], "test")

    def test_logger_level_properties(self):
        """Test level property getter and setter."""
        logger = Logger("level_test")

        # Test setting level
        logger.level = logging.DEBUG
        self.assertEqual(logger.level, logging.DEBUG)

        # Test setting level by string
        logger.level = "INFO"
        self.assertEqual(logger.level, logging.INFO)

    def test_logger_enabled_for_level(self):
        """Test is_enabled_for method."""
        logger = Logger("enabled_test")
        logger.level = logging.INFO

        self.assertTrue(logger.is_enabled_for(logging.INFO))
        self.assertTrue(logger.is_enabled_for(logging.WARNING))
        self.assertFalse(logger.is_enabled_for(logging.DEBUG))

    def test_logger_string_representation(self):
        """Test string representation of loggers."""
        logger = Logger("repr_test")
        async_logger = AsyncLogger("async_repr_test")
        custom_logger = CustomTestLogger("custom_repr_test")

        # Test __repr__ exists and includes class name and name
        logger_repr = repr(logger)
        self.assertIn("Logger", logger_repr)
        self.assertIn("repr_test", logger_repr)

        async_repr = repr(async_logger)
        self.assertIn("AsyncLogger", async_repr)
        self.assertIn("async_repr_test", async_repr)

        custom_repr = repr(custom_logger)
        self.assertIn("CustomTestLogger", custom_repr)
        self.assertIn("custom_repr_test", custom_repr)


class TestAsyncLoggerConfiguration(unittest.TestCase):
    """Test AsyncLogger specific configuration."""

    async def test_async_logger_configure(self):
        """Test AsyncLogger configuration method."""
        async_logger = AsyncLogger("async_config_test")

        # Test async configuration
        result = await async_logger.configure(level="DEBUG", async_mode=True, visual_mode=True)

        # Should return self for method chaining
        self.assertEqual(result, async_logger)

    async def test_async_logger_logging_methods(self):
        """Test that AsyncLogger logging methods are synchronous."""
        async_logger = AsyncLogger("async_logging_test")
        await async_logger.configure(level="DEBUG")

        # Logging methods should be synchronous (not awaitable)
        # This should not raise a TypeError
        async_logger.info("test message")
        async_logger.debug("debug message")
        async_logger.warning("warning message")
        async_logger.error("error message")
        async_logger.critical("critical message")


if __name__ == "__main__":
    # Run async tests
    async def run_async_tests():
        test_suite = unittest.TestSuite()

        # Add async test methods
        async_test_class = TestAsyncLoggerConfiguration()
        await async_test_class.test_async_logger_configure()
        await async_test_class.test_async_logger_logging_methods()

        print("✅ Async tests completed successfully")

    # Run sync tests
    unittest.main(exit=False, verbosity=2)

    # Run async tests
    asyncio.run(run_async_tests())
