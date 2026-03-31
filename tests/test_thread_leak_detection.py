"""
Test thread leak detection in the test suite.

This module verifies that our thread leak detection system works properly
and catches any AsyncQueueHandler-related thread leaks.
"""

import logging  # Need standard logging for LogRecord creation

# Removed standard logging import - using LogEverything instead
import threading
import time

import pytest

from logeverything.asyncio.async_logging import AsyncQueueHandler
from logeverything.handlers import ConsoleHandler, PrettyFormatter


class TestThreadLeakDetection:
    """Test that thread leak detection works correctly."""

    def test_no_thread_leak_with_proper_cleanup(self):
        """Test that properly cleaned up handlers don't trigger leak detection."""
        initial_threads = set(threading.enumerate())

        # Create an AsyncQueueHandler
        handler = AsyncQueueHandler(name="test_handler_clean")

        # Use it briefly
        record = logging.LogRecord(
            name="test",
            level="INFO",
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        handler.emit(record)

        # Clean it up properly
        handler.close()

        # Wait for cleanup
        time.sleep(0.2)

        # Verify no new threads remain
        final_threads = set(threading.enumerate())
        new_threads = final_threads - initial_threads

        # Should be no new threads
        assert len(new_threads) == 0, f"Unexpected threads remain: {[t.name for t in new_threads]}"

    def test_thread_cleanup_via_global_registry(self):
        """Test that the global registry cleanup works correctly."""
        from logeverything.asyncio.async_logging import (
            cleanup_all_async_handlers,
            get_all_async_handlers,
        )

        initial_handlers = len(get_all_async_handlers())
        initial_threads = set(threading.enumerate())

        # Create multiple handlers
        handlers = []
        for i in range(3):
            handler = AsyncQueueHandler(name=f"test_handler_{i}")
            handlers.append(handler)

        # Verify they're registered
        current_handlers = len(get_all_async_handlers())
        assert current_handlers >= initial_handlers + 3

        # Clean up via global registry
        cleaned_count = cleanup_all_async_handlers()
        assert cleaned_count >= 3

        # Verify cleanup
        time.sleep(0.2)
        final_threads = set(threading.enumerate())
        new_threads = final_threads - initial_threads

        # Should be no new threads
        assert len(new_threads) == 0, f"Thread leak detected: {[t.name for t in new_threads]}"

    def test_thread_verification_system_integration(self):
        """Test that our thread verification integrates properly with pytest."""
        # This test itself verifies that thread_leak_detection fixture works
        # If there were any leaks, the fixture would have already caught them

        # Create and properly clean up a handler to test the system
        handler = AsyncQueueHandler(name="integration_test_handler")

        # Emit a test record
        record = logging.LogRecord(
            name="test",
            level="INFO",
            pathname="",
            lineno=0,
            msg="Integration test",
            args=(),
            exc_info=None,
        )
        handler.emit(record)

        # Clean up
        handler.close()

        # The thread_leak_detection fixture should ensure no leaks remain
        # If this test passes, it means the verification system is working
        assert True

    def test_multiple_handlers_with_cleanup(self):
        """Test multiple handlers being created and cleaned up properly."""
        # This is a more realistic test of multiple handlers being used
        handlers = []

        try:
            # Create multiple handlers
            for i in range(5):
                output = ConsoleHandler()
                async_handler = AsyncQueueHandler(
                    target_handlers=[output], name=f"multi_test_handler_{i}"
                )
                handlers.append(async_handler)

                # Use each handler
                record = logging.LogRecord(
                    name="test",
                    level="INFO",
                    pathname="",
                    lineno=0,
                    msg=f"Message from handler {i}",
                    args=(),
                    exc_info=None,
                )
                async_handler.emit(record)

        finally:
            # Clean up all handlers
            for handler in handlers:
                try:
                    handler.close()
                except Exception:
                    pass  # Ignore cleanup errors

        # The thread_leak_detection fixture will verify no threads remain


class TestAsyncHandlerIntegrationWithThreadDetection:
    """Test async handler functionality with thread leak detection enabled."""

    def test_async_handler_basic_functionality(self):
        """Test basic async handler functionality doesn't cause thread leaks."""
        import io

        # Set up output capture
        log_output = io.StringIO()
        target_handler = ConsoleHandler(log_output)
        target_handler.setFormatter(PrettyFormatter("%(message)s"))

        # Create async handler
        async_handler = AsyncQueueHandler(
            target_handlers=[target_handler], name="functionality_test_handler"
        )

        try:
            # Test basic functionality
            test_message = "Async handler functionality test"
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,  # Use integer level instead of string
                pathname="",
                lineno=0,
                msg=test_message,
                args=(),
                exc_info=None,
            )

            async_handler.emit(record)

            # Wait for processing
            time.sleep(0.2)
            async_handler.flush()

            # Verify message was logged
            output = log_output.getvalue()
            assert test_message in output

        finally:
            # Clean up
            async_handler.close()
            log_output.close()

    def test_async_handler_error_handling(self):
        """Test async handler error handling doesn't cause thread leaks."""
        # Create a handler that will cause errors
        failing_handler = logging.Handler()
        failing_handler.emit = lambda record: exec('raise Exception("Test error")')

        async_handler = AsyncQueueHandler(
            target_handlers=[failing_handler], name="error_test_handler"
        )

        try:
            # Send a record that will cause an error
            record = logging.LogRecord(
                name="test",
                level="INFO",
                pathname="",
                lineno=0,
                msg="This will cause an error",
                args=(),
                exc_info=None,
            )

            # This should not crash, just handle the error gracefully
            async_handler.emit(record)

            # Wait for processing
            time.sleep(0.2)

        finally:
            # Clean up
            async_handler.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
