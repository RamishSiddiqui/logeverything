"""
Enhanced tests for async logging functionality with comprehensive coverage.

This module contains comprehensive tests for the async logging features of LogEverything,
designed to achieve high test coverage for async_logging.py module.
"""

import asyncio
import logging  # Keep for LogRecord and level constants compatibility
import time
from io import StringIO
from typing import List
from unittest.mock import Mock, patch

import pytest

from logeverything import CRITICAL, DEBUG, ERROR, INFO, AsyncLogger
from logeverything import core as core_module
from logeverything.asyncio.async_logging import (
    AsyncLoggingContext,
    AsyncQueueHandler,
    AsyncQuietLoggingContext,
    AsyncTemporaryHandlerContext,
    AsyncVerboseLoggingContext,
    AsyncVisualLoggingContext,
    async_log_class,
    async_log_function,
    log_async_class,
    log_async_function,
)
from logeverything.handlers import ConsoleHandler, PrettyFormatter


class TestAsyncQueueHandler:
    """Comprehensive tests for AsyncQueueHandler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.log_output = StringIO()
        self.target_handler = ConsoleHandler(stream=self.log_output, use_colors=False)
        self.target_handler.setFormatter(
            PrettyFormatter(use_colors=False, use_symbols=False, fmt="%(message)s")
        )
        self.created_handlers = []  # Track handlers we create

    def teardown_method(self):
        """Clean up after tests."""
        # Close any AsyncQueueHandler instances that were created during tests
        # This is critical to prevent worker thread leaks
        try:
            from thread_cleanup_fix import cleanup_async_handlers

            # Close all tracked handlers first
            for handler in self.created_handlers:
                try:
                    if hasattr(handler, "close"):
                        handler.close()
                except Exception:
                    pass

            # Global cleanup
            cleanup_async_handlers()
        except Exception:
            pass  # Ignore cleanup errors

        self.log_output.close()

    def test_async_queue_handler_initialization(self):
        """Test AsyncQueueHandler initialization with various parameters."""
        # Test default initialization
        handler = AsyncQueueHandler()
        self.created_handlers.append(handler)  # Track for cleanup
        assert handler.queue.maxsize == 1000
        assert handler.flush_interval == 1.0
        assert handler.flush_level == CRITICAL
        assert handler.name == "async_handler"

        # Test custom initialization
        custom_handler = AsyncQueueHandler(
            queue_size=500,
            target_handlers=[self.target_handler],
            flush_level=ERROR,
            flush_interval=2.0,
            name="custom_async",
        )
        self.created_handlers.append(custom_handler)  # Track for cleanup
        assert custom_handler.queue.maxsize == 500
        assert custom_handler.flush_level == ERROR
        assert custom_handler.flush_interval == 2.0
        assert custom_handler.name == "custom_async"
        assert self.target_handler in custom_handler.target_handlers

    def test_queue_full_handling(self):
        """Test behavior when queue becomes full."""
        # Create handler with very small queue
        handler = AsyncQueueHandler(queue_size=2, target_handlers=[self.target_handler])

        # Stop the worker thread to prevent processing
        handler._stop_event.set()
        if handler._worker_thread and handler._worker_thread.is_alive():
            handler._worker_thread.join(timeout=0.5)

        # Now fill the queue beyond capacity rapidly
        for i in range(10):
            record = logging.LogRecord(
                name="test",
                level=INFO,
                pathname="",
                lineno=0,
                msg=f"Message {i}",
                args=(),
                exc_info=None,
            )
            handler.emit(record)

        # Should have dropped some records
        assert handler.dropped_records > 0

    def test_critical_record_direct_handling(self):
        """Test that critical records are handled directly when queue is full."""
        # Create handler with tiny queue
        handler = AsyncQueueHandler(queue_size=1, target_handlers=[self.target_handler])

        # Fill queue first
        record1 = logging.LogRecord(
            name="test",
            level=INFO,
            pathname="",
            lineno=0,
            msg="Fill queue",
            args=(),
            exc_info=None,
        )
        handler.emit(record1)

        # Now emit a critical record when queue is full
        critical_record = logging.LogRecord(
            name="test",
            level=CRITICAL,
            pathname="",
            lineno=0,
            msg="Critical message",
            args=(),
            exc_info=None,
        )
        handler.emit(critical_record)

        # Critical message should be handled directly
        time.sleep(0.1)  # Allow processing
        assert "Critical message" in self.log_output.getvalue()

    def test_worker_thread_management(self):
        """Test worker thread start and stop behavior."""
        handler = AsyncQueueHandler(target_handlers=[self.target_handler])

        # Worker should start automatically when handler is created
        assert handler._worker_thread is not None
        assert handler._worker_thread.is_alive()

        record = logging.LogRecord(
            name="test",
            level=INFO,
            pathname="",
            lineno=0,
            msg="Start worker",
            args=(),
            exc_info=None,
        )
        handler.emit(record)

        # Worker thread should still be running
        time.sleep(0.1)
        assert handler._worker_thread is not None
        assert handler._worker_thread.is_alive()

        # Test close stops worker
        handler.close()
        time.sleep(0.1)
        assert not handler._worker_thread.is_alive()

    def test_flush_functionality(self):
        """Test flush operations."""
        handler = AsyncQueueHandler(target_handlers=[self.target_handler], flush_interval=0.1)

        # Emit some records
        for i in range(3):
            record = logging.LogRecord(
                name="test",
                level=INFO,
                pathname="",
                lineno=0,
                msg=f"Message {i}",
                args=(),
                exc_info=None,
            )
            handler.emit(record)

        # Force flush
        handler.flush()
        time.sleep(0.2)

        # Check all messages were processed
        output = self.log_output.getvalue()
        assert "Message 0" in output
        assert "Message 1" in output
        assert "Message 2" in output

    def test_error_handling_in_worker_thread(self):
        """Test error handling within worker thread."""
        # Create a mock handler that raises an exception
        failing_handler = Mock()
        failing_handler.handle.side_effect = Exception("Handler error")
        failing_handler.level = DEBUG

        handler = AsyncQueueHandler(target_handlers=[failing_handler])

        # Emit a record that will cause handler to fail
        record = logging.LogRecord(
            name="test",
            level=INFO,
            pathname="",
            lineno=0,
            msg="This will fail",
            args=(),
            exc_info=None,
        )

        # Worker should handle the exception gracefully
        with patch("sys.stderr", new_callable=StringIO):
            handler.emit(record)
            time.sleep(0.2)

            # Error should be logged to stderr but thread should continue
            assert handler._worker_thread.is_alive()

    def test_queue_timeout_and_flush_interval(self):
        """Test queue timeout and automatic flush behavior."""
        handler = AsyncQueueHandler(target_handlers=[self.target_handler], flush_interval=0.1)

        # Start worker but don't emit anything
        handler._start_worker()
        time.sleep(0.2)  # Wait longer than flush interval        # Worker should still be alive
        assert handler._worker_thread.is_alive()

        handler.close()

    def test_multiple_target_handlers(self):
        """Test with multiple target handlers."""
        output1 = StringIO()
        output2 = StringIO()
        handler1 = ConsoleHandler(stream=output1, use_colors=False)
        handler2 = ConsoleHandler(stream=output2, use_colors=False)
        handler1.setFormatter(
            PrettyFormatter(use_colors=False, use_symbols=False, fmt="H1: %(message)s")
        )
        handler2.setFormatter(
            PrettyFormatter(use_colors=False, use_symbols=False, fmt="H2: %(message)s")
        )

        async_handler = AsyncQueueHandler(target_handlers=[handler1, handler2])

        record = logging.LogRecord(
            name="test",
            level=INFO,
            pathname="",
            lineno=0,
            msg="Multi-handler test",
            args=(),
            exc_info=None,
        )
        async_handler.emit(record)

        time.sleep(0.2)

        # Check actual output for debugging
        output1_str = output1.getvalue()
        output2_str = output2.getvalue()

        # Both handlers should receive the message without color codes
        assert "H1: Multi-handler test" in output1_str, (
            f"Expected 'H1: Multi-handler test' in {repr(output1_str)}"
        )
        assert "H2: Multi-handler test" in output2_str, (
            f"Expected 'H2: Multi-handler test' in {repr(output2_str)}"
        )

        async_handler.close()
        output1.close()
        output2.close()


class TestAsyncContextManagers:
    """Test async context managers."""

    @pytest.mark.asyncio
    async def test_async_logging_context(self):
        """Test AsyncLoggingContext."""
        # Test that the context manager works without errors
        async with AsyncLoggingContext(level=DEBUG):
            # Context should work without errors
            pass

    @pytest.mark.asyncio
    async def test_async_quiet_logging_context(self):
        """Test AsyncQuietLoggingContext."""
        # Test that the context manager works without errors
        async with AsyncQuietLoggingContext(level=ERROR):
            # Context should work without errors
            pass

    @pytest.mark.asyncio
    async def test_async_verbose_logging_context(self):
        """Test AsyncVerboseLoggingContext."""
        async with AsyncVerboseLoggingContext():
            # Should enable verbose logging
            pass  # Context manager should work without errors

    @pytest.mark.asyncio
    async def test_async_visual_logging_context(self):
        """Test AsyncVisualLoggingContext."""
        async with AsyncVisualLoggingContext():
            # Should enable visual logging features
            pass  # Context manager should work without errors

    @pytest.mark.asyncio
    async def test_async_temporary_handler_context(self):
        """Test AsyncTemporaryHandlerContext."""
        temp_handler = ConsoleHandler(stream=StringIO(), use_colors=False)

        async with AsyncTemporaryHandlerContext([temp_handler]):
            # Handler should be temporarily configured
            # This tests that the context manager works without errors
            pass

        # Context should exit cleanly


class TestAsyncDecorators:
    """Test async decorators."""

    @pytest.mark.asyncio
    async def test_async_log_function_decorator(self):
        """Test async_log_function decorator."""

        @async_log_function
        async def sample_async_func(x: int, y: int) -> int:
            await asyncio.sleep(0.01)
            return x + y

        result = await sample_async_func(3, 4)
        assert result == 7

    @pytest.mark.asyncio
    async def test_log_async_function_decorator(self):
        """Test log_async_function decorator (alias)."""

        @log_async_function
        async def another_async_func(data: str) -> str:
            await asyncio.sleep(0.01)
            return data.upper()

        result = await another_async_func("hello")
        assert result == "HELLO"

    @pytest.mark.asyncio
    async def test_async_log_class_decorator(self):
        """Test async_log_class decorator."""

        @async_log_class
        class AsyncSampleClass:
            def __init__(self, name: str):
                self.name = name

            async def async_method(self, value: int) -> int:
                await asyncio.sleep(0.01)
                return value * 2

            def sync_method(self, value: int) -> int:
                return value + 1

        obj = AsyncSampleClass("test")

        # Test async method
        async_result = await obj.async_method(5)
        assert async_result == 10

        # Test sync method
        sync_result = obj.sync_method(5)
        assert sync_result == 6

    @pytest.mark.asyncio
    async def test_log_async_class_decorator(self):
        """Test log_async_class decorator (alias)."""

        @log_async_class
        class AnotherAsyncClass:
            async def process(self, items: List[int]) -> List[int]:
                await asyncio.sleep(0.01)
                return [x * 2 for x in items]

        obj = AnotherAsyncClass()
        result = await obj.process([1, 2, 3])
        assert result == [2, 4, 6]

    @pytest.mark.asyncio
    async def test_async_decorator_with_exceptions(self):
        """Test async decorators handle exceptions properly."""

        @async_log_function
        async def failing_async_func():
            await asyncio.sleep(0.01)
            raise ValueError("Test exception")

        with pytest.raises(ValueError, match="Test exception"):
            await failing_async_func()

    @pytest.mark.asyncio
    async def test_async_decorator_with_complex_types(self):
        """Test async decorators with complex argument and return types."""

        @async_log_function
        async def complex_async_func(data: dict, items: List[str], callback=None) -> dict:
            await asyncio.sleep(0.01)
            result = {
                "processed": len(items),
                "data_keys": list(data.keys()),
                "has_callback": callback is not None,
            }
            return result

        result = await complex_async_func(
            {"key1": "value1", "key2": "value2"}, ["item1", "item2", "item3"], lambda x: x
        )

        assert result["processed"] == 3
        assert result["data_keys"] == ["key1", "key2"]
        assert result["has_callback"] is True


class TestAsyncLoggingIntegration:
    """Test async logging integration with main library."""

    @pytest.mark.asyncio
    async def test_async_logging_with_logger_configure(self):
        """Test async logging configuration via AsyncLogger.configure."""
        logger = AsyncLogger("async_configure_test")
        await logger.configure(
            level=DEBUG,
            async_queue_size=100,
            async_flush_interval=0.1,
            handlers=["console"],
        )

        # AsyncLogger.configure sets up handlers on the instance's internal logger
        # Verify the logger is properly configured with handlers
        assert len(logger.logger.handlers) > 0, "AsyncLogger should have handlers after configure"

        # Verify the logger can actually log messages
        logger.info("Test async logging message")

        # Clean up handlers
        for handler in logger.logger.handlers[:]:
            if hasattr(handler, "close"):
                handler.close()
            logger.logger.removeHandler(handler)

    @pytest.mark.asyncio
    async def test_async_logging_performance(self):
        """Test that async logging doesn't block significantly."""
        # Note: Using global configure() here to test the global async mode
        # When using AsyncLogger(), async_mode=True is automatic
        core_module.configure(async_mode=True, async_queue_size=1000)

        @async_log_function
        async def fast_operation(n: int) -> int:
            # This should complete quickly even with logging
            return n * 2

        start_time = time.time()

        # Run multiple concurrent operations
        tasks = [fast_operation(i) for i in range(100)]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete reasonably quickly (less than 2 seconds)
        assert duration < 2.0
        assert len(results) == 100
        assert results[0] == 0
        assert results[99] == 198

        # Clean up
        core_module.configure(async_mode=False)

    @pytest.mark.asyncio
    async def test_mixed_sync_async_logging(self):
        """Test that sync and async logging can coexist."""
        # Note: Using global configure() here to test the global async mode
        # When using AsyncLogger(), async_mode=True is automatic
        core_module.configure(async_mode=True)

        # Create both sync and async decorated functions
        from logeverything.decorators import log_function

        @log_function
        def sync_function(x: int) -> int:
            return x + 1

        @async_log_function
        async def async_function(x: int) -> int:
            await asyncio.sleep(0.01)
            return x + 2

        # Both should work
        sync_result = sync_function(5)
        async_result = await async_function(5)

        assert sync_result == 6
        assert async_result == 7

        # Clean up
        core_module.configure(async_mode=False)


class TestAsyncLoggerClass:
    """Test AsyncLogger class specifically designed for async applications."""

    @pytest.mark.asyncio
    async def test_async_logger_creation(self):
        """Test AsyncLogger creation and basic functionality."""
        # Create async logger
        logger = AsyncLogger("test_async_logger")

        # Test basic logging methods
        logger.info("Test info message")
        logger.debug("Test debug message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        logger.critical("Test critical message")

        # AsyncLogger should be properly configured for async
        assert logger._name == "test_async_logger"

    @pytest.mark.asyncio
    async def test_async_logger_configure(self):
        """Test AsyncLogger.configure method."""
        logger = AsyncLogger()

        # Configure with async-specific settings
        configured_logger = await logger.configure(
            level=DEBUG, async_queue_size=500, async_flush_interval=0.5, handlers=["console"]
        )

        # Should return self for chaining
        assert configured_logger is logger

        # Test logging after configuration
        logger.info("Configured async logger test")

    @pytest.mark.asyncio
    async def test_async_logger_context_managers(self):
        """Test AsyncLogger with async context managers."""
        logger = AsyncLogger("context_test")

        # Test verbose context
        async with logger.verbose():
            logger.info("Message in verbose context")

        # Test quiet context
        async with logger.quiet():
            logger.warning("Message in quiet context")

    @pytest.mark.asyncio
    async def test_async_logger_binding(self):
        """Test AsyncLogger.bind for structured logging."""
        logger = AsyncLogger("bind_test")

        # Bind context data
        bound_logger = logger.bind(
            user_id=123, request_id="abc-def-456", operation="test_operation"
        )

        # Should create a new instance
        assert bound_logger is not logger
        # With improved Loguru-style binding, bound loggers share the same name
        assert bound_logger._name == "bind_test"
        # But have different context
        assert bound_logger._context == {
            "user_id": 123,
            "request_id": "abc-def-456",
            "operation": "test_operation",
        }

        # Test logging with bound context
        bound_logger.info("Operation completed")
        bound_logger.error("Operation failed")

    @pytest.mark.asyncio
    async def test_async_logger_performance(self):
        """Test AsyncLogger performance with high-volume logging."""
        logger = AsyncLogger("performance_test")
        await logger.configure(level=INFO, async_queue_size=1000, handlers=["console"])

        # Log many messages quickly
        start_time = time.time()
        for i in range(100):
            logger.info(f"Performance test message {i}")
        end_time = time.time()

        # Should complete quickly due to async queue
        elapsed = end_time - start_time
        assert elapsed < 1.0, f"Async logging took too long: {elapsed}s"

    @pytest.mark.asyncio
    async def test_async_logger_with_decorators(self):
        """Test AsyncLogger integration with async decorators."""
        logger = AsyncLogger("decorator_test")
        await logger.configure(level=DEBUG)

        @async_log_function
        async def async_test_function(x, y):
            await asyncio.sleep(0.01)  # Simulate async work
            return x + y

        @async_log_class
        class AsyncTestClass:
            async def async_method(self, value):
                await asyncio.sleep(0.01)  # Simulate async work
                return value * 2

        # Test decorated function
        result = await async_test_function(5, 3)
        assert result == 8

        # Test decorated class
        obj = AsyncTestClass()
        result = await obj.async_method(10)
        assert result == 20

    @pytest.mark.asyncio
    async def test_async_logger_mixed_sync_async(self):
        """Test AsyncLogger in mixed sync/async scenarios."""
        logger = AsyncLogger("mixed_test")
        await logger.configure(level=DEBUG)

        # Sync logging should still work
        logger.info("Sync message from async logger")
        logger.warning("Sync warning from async logger")

        # Async contexts should also work
        async with logger.verbose():
            logger.debug("Debug message in verbose async context")

        # Bound logger with sync logging
        bound = logger.bind(test_case="mixed_scenario")
        bound.error("Error message from bound logger")

    @pytest.mark.asyncio
    async def test_async_logger_has_async_mode_by_default(self):
        """Test that AsyncLogger automatically has async_mode=True without needing to specify it."""
        logger = AsyncLogger("default_async_test")

        # Configure without specifying async_mode - should be True by default
        await logger.configure(level=DEBUG, handlers=["console"])

        # AsyncLogger should be configured with handlers on its internal logger
        assert len(logger.logger.handlers) > 0, "AsyncLogger should have handlers after configure"

        # Test that logging works
        logger.info("This message should be logged asynchronously")

        # Clean up
        for handler in logger.logger.handlers[:]:
            if hasattr(handler, "close"):
                handler.close()
            logger.logger.removeHandler(handler)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
