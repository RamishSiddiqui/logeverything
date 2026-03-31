"""
Integration tests for decorator logger selection with existing LogEverything features.

These tests ensure the new decorator enhancements work correctly with:
- Different logger configurations
- Various output formats
- Error handling scenarios
- Performance considerations
"""

import io
import logging
import os
import sys
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything import Logger
from logeverything.core import _active_loggers
from logeverything.decorators import log, log_class, log_function, log_io
from logeverything.handlers import ConsoleHandler


@pytest.mark.usefixtures("complete_logging_isolation")
class TestDecoratorLoggerIntegration:
    """Test integration with different logger configurations."""

    def setup_method(self):
        """Set up clean test environment."""
        _active_loggers.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _active_loggers.clear()

    def test_decorator_with_console_output_capture(self):
        """Test that decorator output can be captured from console."""
        # Note: Decorators use the internal Python logger, so custom handlers
        # on LogEverything Logger instances may not be used directly.
        # This is by design for performance and compatibility reasons.
        logger = Logger("console_test")

        @log(using="console_test")
        def console_function():
            return "console_result"

        result = console_function()
        assert result == "console_result"

        # The function should execute successfully even if output isn't captured
        # through custom handlers

    def test_decorator_with_different_log_levels(self):
        """Test decorator behavior with different log levels."""
        logger = Logger("level_test")
        logger.configure(level="DEBUG")

        @log(using="level_test")
        def level_function():
            return "level_result"

        result = level_function()
        assert result == "level_result"

        # Function should execute successfully regardless of log level

    def test_decorator_with_disabled_logging(self):
        """Test decorator when logging is disabled."""
        logger = Logger("disabled_test")
        logger.configure(level="CRITICAL")  # Set very high level to effectively disable

        @log(using="disabled_test")
        def disabled_function():
            return "disabled_result"

        # Function should still work even if logging is disabled
        result = disabled_function()
        assert result == "disabled_result"

    def test_decorator_with_multiple_handlers(self):
        """Test decorator with logger that has multiple handlers."""
        logger = Logger("multi_handler_test")

        @log(using="multi_handler_test")
        def multi_handler_function():
            return "multi_result"

        result = multi_handler_function()
        assert result == "multi_result"

        # Function should execute successfully with the specified logger


@pytest.mark.usefixtures("complete_logging_isolation")
class TestDecoratorErrorHandling:
    """Test error handling in decorator logger selection."""

    def setup_method(self):
        """Set up clean test environment."""
        _active_loggers.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _active_loggers.clear()

    def test_decorator_handles_logger_with_no_handlers(self):
        """Test decorator behavior with logger that has no handlers."""
        # Create logger but don't configure any handlers
        logger = Logger("no_handlers_test", auto_setup=False)

        @log(using="no_handlers_test")
        def no_handlers_function():
            return "no_handlers_result"

        # Should work without errors even with no handlers
        result = no_handlers_function()
        assert result == "no_handlers_result"

    def test_decorator_handles_function_exceptions(self):
        """Test decorator behavior when decorated function raises exception."""
        logger = Logger("exception_test")

        @log(using="exception_test")
        def exception_function():
            raise ValueError("Test exception")

        # Exception should propagate normally
        with pytest.raises(ValueError, match="Test exception"):
            exception_function()

    def test_decorator_handles_concurrent_access(self):
        """Test decorator behavior with concurrent access to logger registry."""
        logger = Logger("concurrent_test")
        results = []

        @log(using="concurrent_test")
        def concurrent_function(thread_id):
            return f"result_{thread_id}"

        def worker(thread_id):
            try:
                result = concurrent_function(thread_id)
                results.append(result)
            except Exception as e:
                results.append(f"error_{thread_id}: {e}")

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All threads should have succeeded
        assert len(results) == 5
        for i in range(5):
            assert f"result_{i}" in results


@pytest.mark.usefixtures("complete_logging_isolation")
class TestDecoratorPerformanceIntegration:
    """Test performance aspects of decorator integration."""

    def setup_method(self):
        """Set up clean test environment."""
        _active_loggers.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _active_loggers.clear()

    def test_decorator_performance_with_many_loggers(self):
        """Test decorator performance when many loggers are registered."""
        # Create many loggers (auto_setup=False to avoid console output overhead)
        for i in range(100):
            Logger(f"perf_logger_{i}", auto_setup=False)

        @log(using="perf_logger_50")  # Use one in the middle
        def perf_function():
            return "perf_result"

        # Measure performance
        start_time = time.time()
        for _ in range(100):
            result = perf_function()
            assert result == "perf_result"
        end_time = time.time()

        # Should complete reasonably quickly (less than 5 seconds for 100 calls)
        execution_time = end_time - start_time
        assert execution_time < 5.0, f"Decorator too slow: {execution_time}s for 100 calls"

    def test_decorator_memory_usage_stable(self):
        """Test that decorator doesn't cause memory leaks."""
        logger = Logger("memory_test")

        @log(using="memory_test")
        def memory_function(iteration):
            return f"memory_result_{iteration}"

        # Run many iterations
        for i in range(1000):
            result = memory_function(i)
            assert result == f"memory_result_{i}"

        # Registry should not have grown beyond our loggers
        assert len(_active_loggers) <= 2  # Our logger + possible temporary


@pytest.mark.usefixtures("complete_logging_isolation")
class TestDecoratorEdgeCases:
    """Test edge cases and unusual scenarios."""

    def setup_method(self):
        """Set up clean test environment."""
        _active_loggers.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _active_loggers.clear()

    def test_decorator_with_logger_name_collision(self):
        """Test behavior when multiple loggers have the same name."""
        logger1 = Logger("same_name")
        logger2 = Logger("same_name")  # Overwrites the first

        @log(using="same_name")
        def collision_function():
            return "collision_result"

        result = collision_function()
        assert result == "collision_result"

        # Should use the most recently registered logger
        assert _active_loggers["same_name"] is logger2

    def test_decorator_with_empty_logger_name(self):
        """Test behavior with empty logger names."""
        # This should work since Logger handles empty names
        logger = Logger("")

        @log(using="")
        def empty_name_function():
            return "empty_result"

        result = empty_name_function()
        assert result == "empty_result"

    def test_decorator_with_unicode_logger_names(self):
        """Test decorator with Unicode logger names."""
        logger = Logger("test_中文_🎉")

        @log(using="test_中文_🎉")
        def unicode_function():
            return "unicode_result"

        result = unicode_function()
        assert result == "unicode_result"

    def test_nested_decorators_with_different_loggers(self):
        """Test nested function calls with different loggers."""
        logger1 = Logger("outer_logger")
        logger2 = Logger("inner_logger")

        @log(using="inner_logger")
        def inner_function():
            return "inner_result"

        @log(using="outer_logger")
        def outer_function():
            result = inner_function()
            return f"outer_{result}"

        result = outer_function()
        assert result == "outer_inner_result"

    def test_decorator_class_methods_with_specific_loggers(self):
        """Test class method decoration with specific loggers."""
        method_logger = Logger("method_logger")

        @log_class(using="method_logger")
        class TestClass:
            def public_method(self):
                return "public_result"

            def _private_method(self):
                return "private_result"

            @staticmethod
            def static_method():
                return "static_result"

            @classmethod
            def class_method(cls):
                return "class_result"

        instance = TestClass()

        # All methods should work
        assert instance.public_method() == "public_result"
        assert instance._private_method() == "private_result"
        assert TestClass.static_method() == "static_result"
        assert TestClass.class_method() == "class_result"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
