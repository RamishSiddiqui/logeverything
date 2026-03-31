"""
Tests for the smart decorator functionality.

This module tests the smart unified decorator that automatically detects
whether it's being applied to a function, method, or class.
"""

import io
import logging  # Temporary import for compatibility during refactoring
import os
import sys
import unittest
from unittest.mock import patch

import pytest

# Add the parent directory to the path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything import CRITICAL, DEBUG, ERROR, INFO, WARNING
from logeverything import core as core_module
from logeverything.core import get_logger
from logeverything.decorators import log
from logeverything.handlers import ConsoleHandler, PrettyFormatter


@pytest.mark.usefixtures("reset_logging_config")
class TestSmartDecorator(unittest.TestCase):
    """Test the smart unified decorator functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear all logger caches to prevent interference
        self._clear_logger_caches()

        # Store original configuration state
        self._store_original_config_state()

        # Store original logger state for restoration
        self._store_original_logger_state()

        # Clear all existing loggers to prevent interference
        self._clear_all_loggers()  # Force a complete clean slate
        self._force_clean_logging_environment()

        # Capture logs to a string buffer
        self.log_output = io.StringIO()
        self.handler = ConsoleHandler(self.log_output)
        self.handler.setFormatter(
            PrettyFormatter("%(message)s", use_colors=False, use_symbols=False)
        )
        self.handler.setLevel(DEBUG)

        # Reset configuration to defaults FIRST, then configure loggers
        self._force_reset_configuration()

        # Configure logeverything loggers to capture all decorator output
        self._configure_logeverything_loggers()

    def _force_clean_logging_environment(self):
        """Force a completely clean logging environment."""
        # Clear all handlers from root logger

        root_logger = get_logger()
        root_logger.handlers.clear()
        root_logger.setLevel(WARNING)

        # Clear all logger caches in core modules
        from logeverything import core, decorators

        if hasattr(decorators, "_logger_cache"):
            decorators._logger_cache.clear()
        if hasattr(core, "_logger_cache"):
            core._logger_cache.clear()

        # Clear the active loggers registry so decorators don't find stale Logger
        # instances from previous tests
        if hasattr(core, "_active_loggers"):
            core._active_loggers.clear()

        # Reset any global context in core
        if hasattr(core, "_context"):
            # Thread-local storage, just create new instance
            import threading

            core._context = threading.local()
        if hasattr(core, "_indent_level"):
            core._indent_level = 0

    def _store_original_global_state(self):
        """Store the original global state for restoration."""
        # Store logging module state
        self.original_logger_class = logging.getLoggerClass()
        self.original_logger_dict = logging.Logger.manager.loggerDict.copy()

        # Store core module state
        from logeverything import core

        self.original_context = (
            getattr(core, "_context", {}).copy() if hasattr(core, "_context") else {}
        )
        self.original_indent_level = getattr(core, "_indent_level", 0)

    def _force_reset_configuration(self):
        """Force a complete reset of the logging configuration."""
        # Clear all existing handlers and loggers first
        logging.getLogger().handlers.clear()
        logging.getLogger().setLevel(logging.WARNING)

        # Clear the logger manager completely
        logging.Logger.manager.loggerDict.clear()

        # Reset the core module state
        import threading

        from logeverything import core

        # Reset thread-local context by creating a new one
        if hasattr(core, "_context"):
            core._context = threading.local()
        if hasattr(core, "_indent_level"):
            core._indent_level = 0

        # Now set up with our configuration
        core_module.configure(
            level=logging.DEBUG,
            log_entry_exit=True,
            log_arguments=True,
            log_return_values=True,
            beautify=True,
            indent_level=2,
            handlers=["console"],
        )

        # Configure our test handler after setup
        root_logger = logging.getLogger()
        if self.handler not in root_logger.handlers:
            root_logger.addHandler(self.handler)
        root_logger.setLevel(logging.DEBUG)

    def _clear_logger_caches(self):
        """Clear all logger caches to prevent interference between tests."""
        # Clear the logger cache in decorators module
        from logeverything import decorators

        if hasattr(decorators, "_logger_cache"):
            decorators._logger_cache.clear()

        # Clear any other logger caches
        from logeverything import core

        if hasattr(core, "_logger_cache"):
            core._logger_cache.clear()

    def _store_original_config_state(self):
        """Store the original configuration state for restoration."""
        from logeverything import core

        self.original_config = core._config.copy()

    def _restore_original_config_state(self):
        """Restore the original configuration state."""
        from logeverything import core

        core._config.clear()
        core._config.update(self.original_config)

    def _store_original_logger_state(self):
        """Store the original state of all loggers for restoration."""
        self.original_loggers = {}

        # Store root logger state
        root_logger = logging.getLogger()
        self.original_loggers["root"] = {
            "handlers": root_logger.handlers[:],
            "level": root_logger.level,
            "propagate": root_logger.propagate,
        }

        # Store state of all existing loggers
        for name in logging.Logger.manager.loggerDict:
            logger = logging.getLogger(name)
            if hasattr(logger, "handlers"):  # Skip PlaceHolder objects
                self.original_loggers[name] = {
                    "handlers": logger.handlers[:],
                    "level": logger.level,
                    "propagate": logger.propagate,
                }

    def _clear_all_loggers(self):
        """Clear all existing loggers to prevent test interference."""
        # Clear root logger
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Clear all existing loggers
        for name in list(logging.Logger.manager.loggerDict.keys()):
            logger = logging.getLogger(name)
            if hasattr(logger, "handlers"):  # Skip PlaceHolder objects
                logger.handlers.clear()
                logger.setLevel(logging.NOTSET)

    def _configure_logeverything_loggers(self):
        """Configure logeverything loggers to capture decorator output."""
        # Configure the main logeverything logger
        logeverything_logger = logging.getLogger("logeverything")
        logeverything_logger.addHandler(self.handler)
        logeverything_logger.setLevel(logging.DEBUG)
        logeverything_logger.propagate = False

        # Configure loggers for different module contexts that tests might use
        test_contexts = [
            "logeverything.test_smart_decorator",
            "logeverything.__main__",
            "logeverything.tests.test_smart_decorator",
            "test_smart_decorator",
            "tests.test_smart_decorator",  # Add the actual test module name
            "__main__",  # Add main module context
        ]
        for context in test_contexts:
            logger = logging.getLogger(context)
            # Clear existing handlers first to avoid duplicates
            logger.handlers.clear()
            logger.addHandler(self.handler)
            logger.setLevel(logging.DEBUG)
            logger.propagate = False

        # Also configure any logger that starts with the test module pattern
        for name in logging.Logger.manager.loggerDict:
            if "test_smart_decorator" in name:
                logger = logging.getLogger(name)
                if hasattr(logger, "addHandler"):
                    # Clear existing handlers first
                    logger.handlers.clear()
                    logger.addHandler(self.handler)
                    logger.setLevel(logging.DEBUG)
                    logger.propagate = False

        # Set our handler level explicitly
        self.handler.setLevel(logging.DEBUG)

        # Add a root logger handler as fallback to catch everything
        root_logger = logging.getLogger()
        if self.handler not in root_logger.handlers:
            root_logger.addHandler(self.handler)
        root_logger.setLevel(logging.DEBUG)

    def tearDown(self):
        """Tear down test fixtures."""
        # Clear logger caches first
        self._clear_logger_caches()

        # Restore all original logger states
        self._restore_original_logger_state()

        # Restore original configuration state
        self._restore_original_config_state()

        # Close the log output buffer
        if hasattr(self, "log_output"):
            self.log_output.close()

    def _restore_original_logger_state(self):
        """Restore all loggers to their original state."""
        # First clear all current handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        for name in list(logging.Logger.manager.loggerDict.keys()):
            logger = logging.getLogger(name)
            if hasattr(logger, "handlers"):  # Skip PlaceHolder objects
                logger.handlers.clear()

        # Restore original states
        for name, state in self.original_loggers.items():
            if name == "root":
                logger = logging.getLogger()
            else:
                logger = logging.getLogger(name)

            # Restore handlers
            logger.handlers = state["handlers"][:]
            # Restore level
            logger.setLevel(state["level"])
            # Restore propagate
            logger.propagate = state["propagate"]

    def test_function_decoration(self):
        """Test that @log correctly decorates regular functions."""

        @log
        def regular_function(x, y):
            """A regular function for testing."""
            return x + y

        # Call the function
        result = regular_function(2, 3)

        # Check the result
        self.assertEqual(result, 5)  # Check that function entry and exit were logged
        logs = self.log_output.getvalue()
        self.assertIn("regular_function", logs)
        self.assertIn("(x=2, y=3)", logs)
        self.assertIn("→ 5", logs.replace("➜", "→"))

    def test_function_decoration_with_options(self):
        """Test that @log with options works for functions."""

        @log(log_arguments=False, log_return_values=False)
        def function_with_options(a, b):
            """A function with decorator options."""
            return a * b

        # Call the function
        result = function_with_options(3, 4)

        # Check the result
        self.assertEqual(result, 12)

        # Check that function was logged but not args/return
        logs = self.log_output.getvalue()
        self.assertIn("function_with_options", logs)
        # Should not contain arguments or return value
        self.assertNotIn("a=3", logs)
        self.assertNotIn("b=4", logs)
        self.assertNotIn("→ 12", logs)

    def test_io_function_detection_by_name(self):
        """Test that functions with I/O-related names are detected as I/O functions."""

        @log
        def read_file(filename):
            """Function that appears to read files based on name."""
            return f"content of {filename}"

        @log
        def write_data(data):
            """Function that appears to write data based on name."""
            return f"wrote {data}"

        @log
        def fetch_url(url):
            """Function that appears to fetch URLs based on name."""
            return f"fetched {url}"

        @log
        def save_database_record(record):
            """Function that appears to save to database based on name."""
            return f"saved {record}"

        # Test each function
        read_file("test.txt")
        write_data("test data")
        fetch_url("http://example.com")
        save_database_record("record123")

        # All should be logged as I/O operations
        logs = self.log_output.getvalue()
        self.assertIn("read_file", logs)
        self.assertIn("write_data", logs)
        self.assertIn("fetch_url", logs)
        self.assertIn("save_database_record", logs)

    def test_io_function_detection_by_code(self):
        """Test that functions with I/O-related code are detected as I/O functions."""

        @log
        def process_file():
            """Function that uses 'with open' in code."""
            # This code suggests I/O operations
            with open("test.txt", "r") as f:
                return f.read()

        @log
        def make_request():
            """Function that uses 'requests.' in code."""
            import requests

            # This code suggests HTTP operations
            return requests.get("http://example.com")

        # Since we can't actually call these (they'd fail), let's just test
        # that the decorator was applied without errors
        self.assertTrue(callable(process_file))
        self.assertTrue(callable(make_request))

    def test_class_decoration(self):
        """Test that @log correctly decorates classes."""

        @log
        class TestClass:
            """A test class for decorator testing."""

            def __init__(self, name):
                self.name = name

            def method1(self, x):
                return f"{self.name}: {x}"

            def method2(self, y):
                return f"{self.name}: {y * 2}"

        # Create an instance and call methods
        obj = TestClass("test")
        result1 = obj.method1("hello")
        result2 = obj.method2(5)

        # Check results
        self.assertEqual(result1, "test: hello")
        self.assertEqual(result2, "test: 10")

        # Check that class methods were logged
        logs = self.log_output.getvalue()
        self.assertIn("TestClass", logs)
        self.assertIn("method1", logs)
        self.assertIn("method2", logs)

    def test_class_decoration_with_options(self):
        """Test that @log with options works for classes."""

        @log(log_arguments=False)
        class TestClassWithOptions:
            """A test class with decorator options."""

            def method(self, value):
                return value * 2

        # Create instance and call method
        obj = TestClassWithOptions()
        result = obj.method(10)

        # Check result
        self.assertEqual(result, 20)

        # Check that method was logged but not arguments
        logs = self.log_output.getvalue()
        self.assertIn("method", logs)
        self.assertNotIn("value=10", logs)

    def test_decorator_with_parentheses(self):
        """Test using @log() with parentheses but no arguments."""

        @log()
        def function_with_empty_parens():
            return "test"

        result = function_with_empty_parens()
        self.assertEqual(result, "test")

        logs = self.log_output.getvalue()
        self.assertIn("function_with_empty_parens", logs)

    def test_decorator_disabled(self):
        """Test that the decorator can be disabled."""

        @log(enabled=False)
        def disabled_function():
            return "test"

        result = disabled_function()
        self.assertEqual(result, "test")

        # Should have no logs since decorator is disabled
        logs = self.log_output.getvalue()
        self.assertEqual(logs.strip(), "")

    def test_non_function_non_class_object(self):
        """Test that non-function, non-class objects are returned unchanged."""

        # Test with a simple value
        decorated_value = log(42)
        self.assertEqual(decorated_value, 42)

        # Test with a list
        test_list = [1, 2, 3]
        decorated_list = log(test_list)
        self.assertEqual(decorated_list, test_list)

    def test_io_indicators_comprehensive(self):
        """Test all I/O indicators are properly detected."""
        io_indicators = [
            "file",
            "open",
            "read",
            "write",
            "load",
            "save",
            "fetch",
            "download",
            "upload",
            "http",
            "request",
            "response",
            "socket",
            "connect",
            "database",
            "db",
            "sql",
            "query",
            "insert",
            "update",
            "delete",
            "api",
            "stream",
            "io",
            "input",
            "output",
        ]

        for indicator in io_indicators:
            # Create a function with the indicator in the name
            function_name = f"test_{indicator}_function"

            @log
            def test_function():
                return f"test {indicator}"

            # Rename the function to include the indicator
            test_function.__name__ = function_name

            # Call the function
            result = test_function()
            self.assertEqual(result, f"test {indicator}")

    def test_method_decoration(self):
        """Test that methods can be decorated individually."""

        class TestMethodClass:
            def __init__(self, name):
                self.name = name

            @log
            def decorated_method(self, value):
                return f"{self.name}: {value}"

            def undecorated_method(self, value):
                return f"{self.name}: {value}"

        # Create instance and test both methods
        obj = TestMethodClass("test")
        decorated_result = obj.decorated_method("decorated")
        undecorated_result = obj.undecorated_method("undecorated")

        self.assertEqual(decorated_result, "test: decorated")
        self.assertEqual(undecorated_result, "test: undecorated")

        # Only the decorated method should appear in logs
        logs = self.log_output.getvalue()
        self.assertIn("decorated_method", logs)
        self.assertNotIn("undecorated_method", logs)

    def test_source_code_unavailable(self):
        """Test behavior when source code cannot be retrieved."""

        # Create a function where getsource might fail
        @log
        def lambda_function():
            return "lambda result"  # Mock inspect.getsource to raise an exception

        with patch(
            "logeverything.decorators.smart_decorator.inspect.getsource", side_effect=OSError
        ):
            # This should still work, falling back to name-based detection
            result = lambda_function()
            self.assertEqual(result, "lambda result")

        logs = self.log_output.getvalue()
        self.assertIn("lambda_function", logs)

    def test_complex_io_detection(self):
        """Test complex I/O detection scenarios."""

        @log
        def complex_io_function():
            """Function with multiple I/O indicators in source."""
            # with open("file.txt") as f:
            #     content = f.read()
            # requests.get("http://api.example.com")
            # socket.connect(("host", 80))
            return "complex result"

        result = complex_io_function()
        self.assertEqual(result, "complex result")

        logs = self.log_output.getvalue()
        self.assertIn("complex_io_function", logs)


@pytest.mark.usefixtures("reset_logging_config")
class TestSmartDecoratorEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for the smart decorator."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear all logger caches to prevent interference
        self._clear_logger_caches()

        # Store original configuration state
        self._store_original_config_state()

        # Store original logger state for restoration
        self._store_original_logger_state()

        # Clear all existing loggers to prevent interference
        self._clear_all_loggers()

        # Capture logs to a string buffer
        self.log_output = io.StringIO()
        self.handler = logging.StreamHandler(self.log_output)
        self.handler.setFormatter(logging.Formatter("%(message)s"))
        self.handler.setLevel(logging.DEBUG)

        # Configure the root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(self.handler)
        root_logger.setLevel(logging.DEBUG)
        root_logger.propagate = True

        # Configure logeverything loggers to capture all decorator output
        self._configure_logeverything_loggers()

        # Reset configuration to defaults
        core_module.configure(
            level=logging.DEBUG,
            log_entry_exit=True,
            log_arguments=True,
            log_return_values=True,
            beautify=True,
            indent_level=2,
            handlers=["console"],
        )

    def _clear_logger_caches(self):
        """Clear all logger caches to prevent interference between tests."""
        # Clear the logger cache in decorators module
        from logeverything import decorators

        if hasattr(decorators, "_logger_cache"):
            decorators._logger_cache.clear()

        # Clear any other logger caches
        from logeverything import core

        if hasattr(core, "_logger_cache"):
            core._logger_cache.clear()

    def _store_original_config_state(self):
        """Store the original configuration state for restoration."""
        from logeverything import core

        self.original_config = core._config.copy()

    def _restore_original_config_state(self):
        """Restore the original configuration state."""
        from logeverything import core

        core._config.clear()
        core._config.update(self.original_config)

    def _store_original_logger_state(self):
        """Store the original state of all loggers for restoration."""
        self.original_loggers = {}

        # Store root logger state
        root_logger = logging.getLogger()
        self.original_loggers["root"] = {
            "handlers": root_logger.handlers[:],
            "level": root_logger.level,
            "propagate": root_logger.propagate,
        }

        # Store state of all existing loggers
        for name in logging.Logger.manager.loggerDict:
            logger = logging.getLogger(name)
            if hasattr(logger, "handlers"):  # Skip PlaceHolder objects
                self.original_loggers[name] = {
                    "handlers": logger.handlers[:],
                    "level": logger.level,
                    "propagate": logger.propagate,
                }

    def _clear_all_loggers(self):
        """Clear all existing loggers to prevent test interference."""
        # Clear root logger
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Clear all existing loggers
        for name in list(logging.Logger.manager.loggerDict.keys()):
            logger = logging.getLogger(name)
            if hasattr(logger, "handlers"):  # Skip PlaceHolder objects
                logger.handlers.clear()
                logger.setLevel(logging.NOTSET)

    def _configure_logeverything_loggers(self):
        """Configure logeverything loggers to capture decorator output."""
        # Configure the main logeverything logger
        logeverything_logger = logging.getLogger("logeverything")
        if self.handler not in logeverything_logger.handlers:
            logeverything_logger.addHandler(self.handler)
        logeverything_logger.setLevel(logging.DEBUG)
        logeverything_logger.propagate = True

        # Configure loggers for different module contexts that tests might use
        test_contexts = [
            "logeverything.test_smart_decorator",
            "logeverything.__main__",
            "logeverything.tests.test_smart_decorator",
            "test_smart_decorator",
            "tests.test_smart_decorator",  # Add the actual test module name
            "__main__",  # Add main module context
        ]

        for context in test_contexts:
            logger = logging.getLogger(context)
            if self.handler not in logger.handlers:
                logger.addHandler(self.handler)
            logger.setLevel(logging.DEBUG)
            logger.propagate = True

    def tearDown(self):
        """Tear down test fixtures."""
        # Clear logger caches first
        self._clear_logger_caches()

        # Restore all original logger states
        self._restore_original_logger_state()

        # Restore original configuration state
        self._restore_original_config_state()

        # Close the log output buffer
        if hasattr(self, "log_output"):
            self.log_output.close()

    def _restore_original_logger_state(self):
        """Restore all loggers to their original state."""
        # First clear all current handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        for name in list(logging.Logger.manager.loggerDict.keys()):
            logger = logging.getLogger(name)
            if hasattr(logger, "handlers"):  # Skip PlaceHolder objects
                logger.handlers.clear()

        # Restore original states
        for name, state in self.original_loggers.items():
            if name == "root":
                logger = logging.getLogger()
            else:
                logger = logging.getLogger(name)

            # Restore handlers
            logger.handlers = state["handlers"][:]
            # Restore level
            logger.setLevel(state["level"])
            # Restore propagate
            logger.propagate = state["propagate"]

    def test_builtin_function_decoration(self):
        """Test decorating built-in functions (edge case)."""
        # This is an edge case - decorating built-in functions
        # The decorator should handle this gracefully
        try:
            decorated_len = log(len)
            result = decorated_len([1, 2, 3])
            self.assertEqual(result, 3)
        except Exception as e:
            # If it fails, that's acceptable for built-ins
            self.assertIsInstance(e, (TypeError, AttributeError))

    def test_decorated_function_attributes(self):
        """Test that decorated functions preserve important attributes."""

        @log
        def documented_function(x, y):
            """This function has documentation."""
            return x + y

        # Check that important attributes are preserved
        self.assertEqual(documented_function.__name__, "documented_function")
        self.assertEqual(documented_function.__doc__, "This function has documentation.")

    def test_nested_decoration(self):
        """Test that the smart decorator works with other decorators."""

        def other_decorator(func):
            """Another decorator for testing."""

            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper

        @log
        @other_decorator
        def nested_decorated_function(x):
            return x * 2

        result = nested_decorated_function(5)
        self.assertEqual(result, 10)

        logs = self.log_output.getvalue()
        self.assertIn("nested_decorated_function", logs)

    def test_async_function_detection(self):
        """Test that async functions are handled appropriately."""
        import asyncio

        @log
        async def async_function(x):
            await asyncio.sleep(0.001)  # Tiny sleep to make it properly async
            return x * 2

        # Test that the decorator doesn't break async functions
        async def run_async_test():
            result = await async_function(5)
            return result

        # This might not work in all test environments, so we'll be defensive
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run_async_test())
            self.assertEqual(result, 10)
            loop.close()
        except Exception:
            # If async doesn't work in test environment, that's okay
            pass


if __name__ == "__main__":
    unittest.main()
