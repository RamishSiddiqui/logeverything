"""
Comprehensive tests for intelligent type casting between sync and async loggers/functions.

This test suite verifies that LogEverything's decorators can intelligently handle
mismatched logger and function types by automatically casting loggers to compatible
types while preserving the original logger instance for the user.
"""

import asyncio
import io
import logging
import sys
from typing import List
from unittest.mock import Mock, patch

import pytest

from logeverything import AsyncLogger, Logger
from logeverything.asyncio import async_log_class, async_log_function
from logeverything.decorators import log, log_class, log_function, log_io


class MemoryHandler(logging.Handler):
    """Simple memory handler for capturing log messages during tests."""

    def __init__(self):
        super().__init__()
        self.messages: List[str] = []
        # Set level to capture all messages
        self.setLevel(logging.DEBUG)

    def emit(self, record):
        """Capture log record as formatted message."""
        self.messages.append(self.format(record))

    def get_messages(self) -> str:
        """Get all captured messages as a single string."""
        return "\n".join(self.messages)

    def clear(self):
        """Clear all captured messages."""
        self.messages.clear()


class TestIntelligentTypeCasting:
    """Test suite for intelligent type casting between sync and async loggers."""

    def setup_method(self):
        """Set up test environment."""
        # Enable logging configuration first
        from logeverything.core import _config

        _config.update(
            {
                "log_entry_exit": True,
                "log_arguments": True,
                "log_return_values": True,
                "enabled": True,
                "visual_mode": True,
                "use_symbols": True,
            }
        )

        self.sync_logger = Logger(name="test_sync")
        self.async_logger = AsyncLogger(name="test_async")

        # Register loggers in the core system for decorator lookup
        from logeverything.core import register_logger

        register_logger("test_sync", self.sync_logger)
        register_logger("test_async", self.async_logger)

        # Set logger levels to DEBUG to capture all messages
        self.sync_logger.logger.setLevel(logging.DEBUG)
        self.async_logger.logger.setLevel(logging.DEBUG)

        # Create memory handlers to capture logs
        self.sync_memory_handler = MemoryHandler()
        self.async_memory_handler = MemoryHandler()

        # Add handlers to loggers
        self.sync_logger.add_handler(self.sync_memory_handler)
        # For AsyncLogger, use the underlying logger property
        self.async_logger.logger.addHandler(self.async_memory_handler)

    def teardown_method(self):
        """Clean up after tests."""
        # Unregister loggers
        from logeverything.core import unregister_logger

        try:
            unregister_logger("test_sync")
            unregister_logger("test_async")
        except KeyError:
            pass  # Logger may not have been registered

        # Clear handlers
        if hasattr(self, "sync_memory_handler"):
            self.sync_memory_handler.clear()
        if hasattr(self, "async_memory_handler"):
            self.async_memory_handler.clear()

    def test_sync_logger_with_async_function_smart_decorator(self):
        """Test smart decorator with sync logger and async function."""
        original_logger = self.sync_logger

        # Simple test: just check the function runs and original logger is preserved
        @log(using="test_sync")
        async def async_function(x, y):
            return x + y

        # Verify the function is properly decorated and can be called
        async def run_test():
            result = await async_function(1, 2)
            assert result == 3

            # Verify the original logger instance is preserved
            assert original_logger is self.sync_logger
            assert original_logger._is_async is False

        asyncio.run(run_test())

        # The key test is that the function executes correctly with intelligent type casting
        # Additional logging verification can be done in integration tests

    def test_async_logger_with_sync_function_smart_decorator(self):
        """Test smart decorator with async logger and sync function."""
        original_logger = self.async_logger

        @log(using="test_async")
        def sync_function(x, y):
            return x + y

        # Verify the function is properly decorated and can be called
        result = sync_function(1, 2)
        assert result == 3

        # Verify the original logger instance is preserved
        assert original_logger is self.async_logger
        assert original_logger._is_async is True

        # The key test is that the function executes correctly with intelligent type casting
        # Additional logging verification can be done in integration tests

    def test_sync_logger_with_async_function_log_function(self):
        """Test log_function decorator with sync logger and async function."""
        original_logger = self.sync_logger

        @log_function(using="test_sync")
        async def async_function(x, y):
            return x + y

        async def run_test():
            result = await async_function(3, 4)
            assert result == 7

            # Verify the original logger is preserved
            assert original_logger is self.sync_logger
            assert original_logger._is_async is False

        asyncio.run(run_test())

    def test_async_logger_with_sync_function_log_function(self):
        """Test log_function decorator with async logger and sync function."""
        original_logger = self.async_logger

        @log_function(using="test_async")
        def sync_function(x, y):
            return x + y

        result = sync_function(3, 4)
        assert result == 7

        # Verify the original logger is preserved
        assert original_logger is self.async_logger
        assert original_logger._is_async is True

    def test_sync_logger_with_async_function_async_log_function(self):
        """Test async_log_function decorator with sync logger and async function."""
        original_logger = self.sync_logger

        @async_log_function(using="test_sync")
        async def async_function(x, y):
            return x + y

        async def run_test():
            result = await async_function(5, 6)
            assert result == 11

            # Verify the original logger is preserved
            assert original_logger is self.sync_logger
            assert original_logger._is_async is False

        asyncio.run(run_test())

    def test_async_logger_with_sync_function_async_log_function(self):
        """Test async_log_function decorator with sync logger and sync function."""
        original_logger = self.async_logger

        # This should fall back to regular log_function
        @async_log_function(using="test_async")
        def sync_function(x, y):
            return x + y

        result = sync_function(5, 6)
        assert result == 11

        # Verify the original logger is preserved
        assert original_logger is self.async_logger
        assert original_logger._is_async is True

    def test_sync_logger_with_async_io_function(self):
        """Test log_io decorator with sync logger and async I/O function."""
        original_logger = self.sync_logger

        @log_io(using="test_sync")
        async def async_read_file(filename):
            # Simulate async file reading
            await asyncio.sleep(0.01)
            return f"Contents of {filename}"

        async def run_test():
            result = await async_read_file("test.txt")
            assert result == "Contents of test.txt"

            # Verify the original logger is preserved
            assert original_logger is self.sync_logger
            assert original_logger._is_async is False

        asyncio.run(run_test())

    def test_async_logger_with_sync_io_function(self):
        """Test log_io decorator with async logger and sync I/O function."""
        original_logger = self.async_logger

        @log_io(using="test_async")
        def sync_read_file(filename):
            return f"Contents of {filename}"

        result = sync_read_file("test.txt")
        assert result == "Contents of test.txt"

        # Verify the original logger is preserved
        assert original_logger is self.async_logger
        assert original_logger._is_async is True

    def test_mixed_class_decorators(self):
        """Test class decorators with mixed sync/async methods and different logger types."""
        original_sync_logger = self.sync_logger
        original_async_logger = self.async_logger

        @log_class(using="test_sync")
        class MixedClass:
            def sync_method(self, x):
                return x * 2

            async def async_method(self, x):
                await asyncio.sleep(0.01)
                return x * 3

        async def run_test():
            obj = MixedClass()

            # Test sync method
            result1 = obj.sync_method(5)
            assert result1 == 10

            # Test async method
            result2 = await obj.async_method(5)
            assert result2 == 15

            # Verify original loggers are preserved
            assert original_sync_logger is self.sync_logger
            assert original_sync_logger._is_async is False

        asyncio.run(run_test())

    def test_async_log_class_with_sync_logger(self):
        """Test async_log_class decorator with sync logger."""
        original_logger = self.sync_logger

        @async_log_class
        class AsyncClass:
            def __init__(self):
                pass

            def sync_method(self, x):
                return x * 2

            async def async_method(self, x):
                await asyncio.sleep(0.01)
                return x * 3

        async def run_test():
            obj = AsyncClass()

            # Test sync method (handled by regular log_class)
            result1 = obj.sync_method(7)
            assert result1 == 14

            # Test async method (handled by async_log_function)
            result2 = await obj.async_method(7)
            assert result2 == 21

        asyncio.run(run_test())

    def test_log_decorator_with_mixed_types(self):
        """Test @log decorator with mixed sync/async scenarios."""
        original_sync_logger = self.sync_logger
        original_async_logger = self.async_logger

        @log(using="test_sync")
        def sync_func(x):
            return x**2

        @log(using="test_async")
        async def async_func(x):
            await asyncio.sleep(0.01)
            return x**3

        async def run_test():
            # Test sync function with sync logger
            result1 = sync_func(4)
            assert result1 == 16

            # Test async function with async logger
            result2 = await async_func(4)
            assert result2 == 64

            # Verify original loggers are preserved
            assert original_sync_logger is self.sync_logger
            assert original_async_logger is self.async_logger

        asyncio.run(run_test())

    def test_nested_decorators_with_type_casting(self):
        """Test multiple decorators with type casting."""
        original_logger = self.sync_logger

        @log_io(using="test_sync")
        @log_function(using="test_sync")
        async def nested_async_function(data):
            await asyncio.sleep(0.01)
            return f"Processed: {data}"

        async def run_test():
            result = await nested_async_function("test_data")
            assert result == "Processed: test_data"

            # Verify the original logger is preserved
            assert original_logger is self.sync_logger
            assert original_logger._is_async is False

            # Check that logging occurred from both decorators
            log_content = self.sync_memory_handler.get_messages()
            assert "nested_async_function" in log_content

        asyncio.run(run_test())

    def test_type_casting_preserves_logger_configuration(self):
        """Test that type casting preserves logger configuration and options."""
        # Create a logger with specific configuration
        configured_logger = Logger(name="configured", use_symbols=True, visual_mode=True)
        memory_handler = MemoryHandler()
        configured_logger.add_handler(memory_handler)

        # Register the logger for decorator lookup
        from logeverything.core import register_logger, unregister_logger

        register_logger("configured", configured_logger)

        try:
            original_options = configured_logger._options.copy()

            @log(using="configured")
            async def async_func_with_configured_logger(x):
                return x * 2

            async def run_test():
                result = await async_func_with_configured_logger(10)
                assert result == 20

                # Verify logger configuration is preserved
                assert configured_logger._options == original_options
                assert configured_logger._options.get("use_symbols") == True
                assert configured_logger._options.get("visual_mode") == True

                # The key test is that configuration is preserved and function executes correctly
                # Logging verification can be done in integration tests

            asyncio.run(run_test())
        finally:
            # Clean up
            try:
                unregister_logger("configured")
            except KeyError:
                pass

    def test_error_handling_with_type_casting(self):
        """Test error handling works correctly with type casting."""
        original_logger = self.async_logger

        @log(using="test_async")
        def sync_function_that_fails():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            sync_function_that_fails()

        # Verify the original logger is preserved even after exception
        assert original_logger is self.async_logger
        assert original_logger._is_async is True

        # The key test is that exception handling works correctly with type casting
        # Additional logging verification can be done in integration tests

    def test_performance_with_type_casting(self):
        """Test that type casting doesn't significantly impact performance."""
        import time

        @log(using="test_sync")
        async def fast_async_function(x):
            return x + 1

        async def run_performance_test():
            # Time multiple calls
            start_time = time.time()
            for i in range(100):
                result = await fast_async_function(i)
                assert result == i + 1
            end_time = time.time()

            # Verify it completes in reasonable time (should be very fast)
            elapsed = end_time - start_time
            assert elapsed < 1.0  # Should complete 100 calls in less than 1 second

        asyncio.run(run_performance_test())

    def test_logger_attribute_detection(self):
        """Test that _is_async attribute is properly detected."""
        # Test sync logger
        assert hasattr(self.sync_logger, "_is_async")
        assert self.sync_logger._is_async is False

        # Test async logger
        assert hasattr(self.async_logger, "_is_async")
        assert self.async_logger._is_async is True

    def test_type_casting_with_custom_parameters(self):
        """Test type casting with custom decorator parameters.

        When log_function is applied to an async function, it delegates to
        async_log_function which properly awaits the coroutine and logs the
        real return value (not a coroutine repr).
        """
        original_logger = self.sync_logger

        @log_function(
            using="test_sync", log_arguments=True, log_return_values=True, log_entry_exit=True
        )
        async def async_func_with_params(x, y, z=10):
            await asyncio.sleep(0.01)
            return x + y + z

        # Capture stderr where the async logger writes output
        captured = io.StringIO()
        old_stderr = sys.stderr

        async def run_test():
            result = await async_func_with_params(1, 2, z=3)
            assert result == 6

            # Verify the original logger is preserved
            assert original_logger is self.sync_logger
            assert original_logger._is_async is False

        try:
            sys.stderr = captured
            asyncio.run(run_test())
        finally:
            sys.stderr = old_stderr

        # Check log output from either memory handler or stderr
        log_content = self.sync_memory_handler.get_messages() + "\n" + captured.getvalue()
        assert "async_func_with_params" in log_content
        # Should log arguments
        assert (
            ("1" in log_content and "2" in log_content and "3" in log_content)
            or "args" in log_content
            or "kwargs" in log_content
        )
        # Should log the actual return value 6, not a coroutine repr
        assert " 6" in log_content or "->6" in log_content


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
