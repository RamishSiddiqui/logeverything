"""
Tests for logger deletion and cleanup behavior.

This module contains comprehensive tests to verify that:
- User-created loggers persist after context manager exit
- System-created (temporary) loggers are auto-cleaned after context manager exit
- Bound loggers are auto-cleaned
- Manual cleanup works for all logger types
- Registry is properly maintained throughout
"""

import os
import sys
import threading
import time
import unittest
import weakref

import pytest

# Add the parent directory to the path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything import Logger
from logeverything.asyncio import AsyncLogger
from logeverything.core import _active_loggers


class TestLoggerDeletionCleanup(unittest.TestCase):
    """Test logger deletion and cleanup behavior."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear the logger registry before each test
        _active_loggers.clear()

        # Store original registry size for verification
        self.initial_registry_size = len(_active_loggers)

    def tearDown(self):
        """Clean up after tests."""
        # Clear the registry after each test to avoid interference
        _active_loggers.clear()

    def test_user_created_logger_persists_after_context_exit(self):
        """Test that user-created loggers persist after context manager exit."""
        logger_name = "test_user_logger"

        # Create a user logger (default behavior)
        with Logger(logger_name) as logger:
            self.assertTrue(logger._user_created)
            self.assertIn(logger_name, _active_loggers)

            # Log something to verify the logger works
            logger.info("Test message from user logger")

        # After context exit, user-created logger should still be in registry
        self.assertIn(logger_name, _active_loggers)

        # Logger should still be accessible
        cached_logger = _active_loggers[logger_name]
        self.assertIsNotNone(cached_logger)

        # Verify it's still functional
        cached_logger.info("Message after context exit")

    def test_system_created_logger_cleaned_after_context_exit(self):
        """Test that system-created loggers are auto-cleaned after context manager exit."""
        logger_name = "test_system_logger"

        # Create a system logger by explicitly marking it
        with Logger(logger_name) as logger:
            logger._mark_as_system_created()
            self.assertFalse(logger._user_created)
            self.assertIn(logger_name, _active_loggers)

            # Log something to verify the logger works
            logger.info("Test message from system logger")

        # After context exit, system-created logger should be removed from registry
        self.assertNotIn(logger_name, _active_loggers)

    def test_bound_logger_auto_cleanup(self):
        """Test that bound loggers are automatically marked as system-created and cleaned up."""
        base_logger_name = "test_base_logger"

        # Create a base logger
        base_logger = Logger(base_logger_name)
        self.assertTrue(base_logger._user_created)
        self.assertIn(base_logger_name, _active_loggers)

        # Create a bound logger (should be automatically marked as system-created)
        with base_logger.bind(component="bound_component") as bound_logger:
            self.assertFalse(bound_logger._user_created)  # Should be system-created

            # With improved Loguru-style binding, bound loggers share the same name
            # The base logger is still registered with that name
            self.assertEqual(bound_logger._name, base_logger_name)
            self.assertIn(base_logger_name, _active_loggers)  # Base logger still registered

            # But bound logger is a different object with context
            self.assertIsNot(bound_logger, base_logger)  # Different objects
            self.assertEqual(bound_logger._context, {"component": "bound_component"})

            # Log something to verify the bound logger works
            bound_logger.info("Test message from bound logger")

        # Base logger should still exist and be registered
        self.assertIn(base_logger_name, _active_loggers)

    def test_manual_cleanup_for_user_logger(self):
        """Test that manual cleanup works for user-created loggers."""
        logger_name = "test_manual_cleanup_user"

        # Create a user logger
        logger = Logger(logger_name)
        self.assertTrue(logger._user_created)
        self.assertIn(logger_name, _active_loggers)

        # Manually clean up
        logger._cleanup()

        # Logger should be removed from registry
        self.assertNotIn(logger_name, _active_loggers)

    def test_manual_cleanup_for_system_logger(self):
        """Test that manual cleanup works for system-created loggers."""
        logger_name = "test_manual_cleanup_system"

        # Create a system logger
        logger = Logger(logger_name)
        logger._mark_as_system_created()
        self.assertFalse(logger._user_created)
        self.assertIn(logger_name, _active_loggers)

        # Manually clean up
        logger._cleanup()

        # Logger should be removed from registry
        self.assertNotIn(logger_name, _active_loggers)

    def test_registry_consistency_during_operations(self):
        """Test that the logger registry remains consistent during various operations."""
        initial_size = len(_active_loggers)

        # Create multiple loggers with different behaviors
        user_logger1 = Logger("user1")
        user_logger2 = Logger("user2")

        with Logger("temp1") as temp_logger1:
            temp_logger1._mark_as_system_created()

            with Logger("temp2") as temp_logger2:
                temp_logger2._mark_as_system_created()

                # Registry should have all loggers
                self.assertEqual(len(_active_loggers), initial_size + 4)

                # Create a bound logger (with improved binding, it's not registered)
                with user_logger1.bind(component="test") as bound_logger:
                    # Bound logger is not registered, so count stays the same
                    self.assertEqual(len(_active_loggers), initial_size + 4)
                    # Verify bound logger has correct properties
                    self.assertEqual(bound_logger._name, "user1")  # Same name as parent
                    self.assertEqual(bound_logger._context, {"component": "test"})

                # Bound logger cleanup doesn't affect registry count (wasn't registered)
                self.assertEqual(len(_active_loggers), initial_size + 4)

            # temp2 should be cleaned up
            self.assertEqual(len(_active_loggers), initial_size + 3)

        # temp1 should be cleaned up
        self.assertEqual(len(_active_loggers), initial_size + 2)

        # User loggers should still exist
        self.assertIn("user1", _active_loggers)
        self.assertIn("user2", _active_loggers)

    def test_logger_deletion_memory_management(self):
        """Test that logger deletion properly handles memory management."""
        logger_name = "test_memory_management"

        # Create a logger and get a weak reference to track deletion
        logger = Logger(logger_name)
        weak_ref = weakref.ref(logger)

        # Logger should exist
        self.assertIsNotNone(weak_ref())
        self.assertIn(logger_name, _active_loggers)

        # Manually cleanup and delete
        logger._cleanup()
        del logger

        # Give some time for garbage collection
        import gc

        gc.collect()

        # Logger should be removed from registry
        self.assertNotIn(logger_name, _active_loggers)

    def test_concurrent_logger_operations(self):
        """Test logger operations in concurrent scenarios."""

        def create_and_cleanup_logger(name_suffix):
            """Helper function to create and cleanup a logger."""
            logger_name = f"concurrent_test_{name_suffix}"

            # Create system logger
            with Logger(logger_name) as logger:
                logger._mark_as_system_created()
                logger.info(f"Message from {logger_name}")
                time.sleep(0.01)  # Small delay to simulate work

            # Verify cleanup
            return logger_name not in _active_loggers

        # Run multiple threads
        threads = []
        results = {}

        for i in range(5):

            def thread_func(i=i):
                results[i] = create_and_cleanup_logger(i)

            thread = threading.Thread(target=thread_func)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All loggers should have been cleaned up
        for i in range(5):
            self.assertTrue(results[i], f"Logger {i} was not properly cleaned up")

    def test_user_created_flag_immutability(self):
        """Test that user_created flag cannot be accidentally modified."""
        logger = Logger("test_immutability")

        # Should start as user-created
        self.assertTrue(logger._user_created)

        # Mark as system-created
        logger._mark_as_system_created()
        self.assertFalse(logger._user_created)

        # Should not be able to change back to user-created
        # (there's no public method to do this, which is intentional)
        self.assertFalse(logger._user_created)

    def test_cleanup_idempotency(self):
        """Test that cleanup operations are idempotent (safe to call multiple times)."""
        logger_name = "test_idempotency"
        logger = Logger(logger_name)

        # Logger should be in registry
        self.assertIn(logger_name, _active_loggers)

        # Call cleanup multiple times
        logger._cleanup()
        self.assertNotIn(logger_name, _active_loggers)

        # Should be safe to call again
        logger._cleanup()  # Should not raise an error
        self.assertNotIn(logger_name, _active_loggers)

    def test_context_manager_exception_handling(self):
        """Test that logger cleanup works properly even when exceptions occur in context."""
        logger_name = "test_exception_handling"

        # Test with system logger and exception
        try:
            with Logger(logger_name) as logger:
                logger._mark_as_system_created()
                self.assertIn(logger_name, _active_loggers)
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected exception

        # Logger should still be cleaned up despite the exception
        self.assertNotIn(logger_name, _active_loggers)

        # Test with user logger and exception
        user_logger_name = "test_user_exception"
        try:
            with Logger(user_logger_name) as logger:
                self.assertTrue(logger._user_created)
                self.assertIn(user_logger_name, _active_loggers)
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected exception

        # User logger should persist despite the exception
        self.assertIn(user_logger_name, _active_loggers)

    def test_logger_name_property(self):
        """Test that logger name property works correctly."""
        logger_name = "test_name_property"
        logger = Logger(logger_name)

        # Name property should return the correct name
        self.assertEqual(logger.name, logger_name)

        # Should be in registry with correct name
        self.assertIn(logger_name, _active_loggers)


class TestAsyncLoggerDeletionCleanup:
    """Test async logger deletion and cleanup behavior."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear the logger registry before each test
        _active_loggers.clear()

    def teardown_method(self):
        """Clean up after tests."""
        # Clear the registry after each test to avoid interference
        _active_loggers.clear()

    @pytest.mark.asyncio
    async def test_async_user_created_logger_persists_after_context_exit(self):
        """Test that user-created async loggers persist after context manager exit."""
        logger_name = "test_async_user_logger"

        # Create an async user logger (default behavior)
        async with AsyncLogger(logger_name) as logger:
            assert logger._user_created
            assert logger_name in _active_loggers

            # Log something to verify the logger works (no await needed for info)
            logger.info("Test message from async user logger")

        # After context exit, user-created logger should still be in registry
        assert logger_name in _active_loggers

    @pytest.mark.asyncio
    async def test_async_system_created_logger_cleaned_after_context_exit(self):
        """Test that system-created async loggers are auto-cleaned after context manager exit."""
        logger_name = "test_async_system_logger"

        # Create an async system logger by explicitly marking it
        async with AsyncLogger(logger_name) as logger:
            logger._mark_as_system_created()
            assert not logger._user_created
            assert logger_name in _active_loggers

            # Log something to verify the logger works (no await needed for info)
            logger.info("Test message from async system logger")

        # After context exit, system-created logger should be removed from registry
        assert logger_name not in _active_loggers

    @pytest.mark.asyncio
    async def test_async_bound_logger_auto_cleanup(self):
        """Test that async bound loggers are automatically cleaned up."""
        base_logger_name = "test_async_base_logger"

        # Create a base async logger
        base_logger = AsyncLogger(base_logger_name)
        assert base_logger._user_created
        assert base_logger_name in _active_loggers

        # Create a bound async logger (should be automatically marked as system-created)
        async with base_logger.bind(component="bound_component") as bound_logger:
            assert not bound_logger._user_created  # Should be system-created

            # With improved Loguru-style binding, bound loggers share the same name
            # The base logger is still registered with that name
            assert bound_logger._name == base_logger_name
            assert base_logger_name in _active_loggers  # Base logger still registered

            # But bound logger is a different object with context
            assert bound_logger is not base_logger  # Different objects
            assert bound_logger._context == {"component": "bound_component"}

            # Log something to verify the bound logger works
            bound_logger.info("Test message from async bound logger")

        # Base logger should still exist and be registered
        assert base_logger_name in _active_loggers

    @pytest.mark.asyncio
    async def test_async_manual_cleanup(self):
        """Test that manual cleanup works for async loggers."""
        logger_name = "test_async_manual_cleanup"

        # Create an async logger
        logger = AsyncLogger(logger_name)
        assert logger._user_created
        assert logger_name in _active_loggers

        # Manually clean up using close() method
        await logger.close()

        # Logger should be removed from registry
        assert logger_name not in _active_loggers

    @pytest.mark.asyncio
    async def test_async_exception_handling(self):
        """Test that async logger cleanup works properly even when exceptions occur."""
        logger_name = "test_async_exception_handling"

        # Test with system logger and exception
        try:
            async with AsyncLogger(logger_name) as logger:
                logger._mark_as_system_created()
                assert logger_name in _active_loggers
                raise ValueError("Test async exception")
        except ValueError:
            pass  # Expected exception

        # Logger should still be cleaned up despite the exception
        assert logger_name not in _active_loggers


if __name__ == "__main__":
    # Run the tests
    unittest.main()
