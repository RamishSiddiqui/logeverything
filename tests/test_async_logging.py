"""
Tests for async logging functionality.

This module contains tests for the async logging features of LogEverything.
"""

import asyncio

# Removed logging import
import os
import time
from typing import List, cast

import pytest

from logeverything import CRITICAL, DEBUG, ERROR, INFO, WARNING, AsyncLogger
from logeverything import core as core_module
from logeverything.asyncio.async_logging import AsyncQueueHandler, async_log_function
from logeverything.core import get_logger
from logeverything.handlers import ConsoleHandler, PrettyFormatter


@pytest.fixture
def async_logging_setup():
    """Set up async logging for tests."""
    # Configure with async mode using configure function
    core_module.configure(
        level="DEBUG",
        async_mode=True,
        async_queue_size=1000,
        async_flush_interval=0.5,
        handlers=["console"],
    )

    yield

    # Clean up
    core_module.configure(async_mode=False)
    logger = get_logger("logeverything")
    for handler in list(logger.handlers):
        if isinstance(handler, AsyncQueueHandler):
            handler.close()
            logger.removeHandler(handler)


@pytest.mark.asyncio
async def test_async_logging_basic(async_logging_setup, caplog):
    """Test basic async logging functionality."""

    # Define an async function with logging
    @async_log_function
    async def sample_async_function(x: int, y: int) -> int:
        await asyncio.sleep(0.01)  # Small delay to simulate work
        return x + y

    # Call the function
    result = await sample_async_function(5, 7)

    # Verify the function worked
    assert result == 12

    # Allow time for async logging to complete
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_async_log_function_decorator(async_logging_setup):
    """Test that the async_log_function decorator works properly."""
    processed_items = []

    @async_log_function
    async def process_item(item: int) -> int:
        processed_items.append(item)
        await asyncio.sleep(0.01)
        return item * 2

    # Execute multiple concurrent tasks
    tasks = [process_item(i) for i in range(10)]
    results = await asyncio.gather(*tasks)

    # Verify results
    assert results == [i * 2 for i in range(10)]
    assert set(processed_items) == set(range(10))

    # Allow time for async logging to complete
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_async_performance_comparison():
    """Compare performance between sync and async logging."""
    results = {}

    # Define a workload
    @async_log_function
    async def intensive_logging(n: int) -> None:
        for i in range(n):
            await asyncio.sleep(0.001)  # Small delay

    # Test with async logging
    core_module.configure(async_mode=True)
    start_time = time.time()
    await intensive_logging(100)
    # Allow flush to complete
    await asyncio.sleep(1)
    async_time = time.time() - start_time

    # Test with sync logging
    core_module.configure(async_mode=False)
    start_time = time.time()
    await intensive_logging(100)
    sync_time = time.time() - start_time

    # We don't assert specific times as they depend on the environment,
    # but we log them for informational purposes
    print(f"Async logging time: {async_time:.4f}s")
    print(f"Sync logging time: {sync_time:.4f}s")


@pytest.mark.asyncio
async def test_async_queue_handler_close():
    """Test that the AsyncQueueHandler properly closes and processes remaining records."""
    # Configure with async mode using AsyncLogger
    logger = AsyncLogger()
    await logger.configure(
        level="DEBUG",
        async_queue_size=100,
        async_flush_interval=1.0,
        handlers=["file"],
        file_path="test_async_queue.log",
    )

    # Get the AsyncQueueHandler
    logger = get_logger("logeverything")
    async_handler = None
    for handler in logger.handlers:
        if isinstance(handler, AsyncQueueHandler):
            async_handler = handler
            break

    # If we found the async handler
    if async_handler:
        # Log some messages
        logger.info("Test message before close")

        # Close the handler, which should flush and process remaining records
        async_handler.close()

        # Verify the handler is closed
        assert async_handler._worker_thread is None or not async_handler._worker_thread.is_alive()

    # Clean up
    core_module.configure(async_mode=False)

    # Add a small delay to ensure file is released
    import time

    time.sleep(0.1)

    # Clean up log file
    try:
        if os.path.exists("test_async_queue.log"):
            os.remove("test_async_queue.log")
    except PermissionError:
        # File might still be in use, skip cleanup
        pass
