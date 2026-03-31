"""
LogEverything Asyncio Support

This module provides asynchronous logging support with high-performance async handlers,
decorators, and context managers optimized for asyncio applications.

Features:
- AsyncQueueHandler: 6.8x faster async logging with background processing
- Async decorators: Specialized decorators for async functions and classes
- Async context managers: Control logging within async contexts
- Coroutine-aware logging: Proper tracking of async execution flow

Usage:
    from logeverything.asyncio import AsyncQueueHandler
    from logeverything.asyncio import async_log_function, async_log_class
    from logeverything.asyncio import AsyncLoggingContext

    # Async handler for high-performance logging
    handler = AsyncQueueHandler(target_handlers=[console_handler])

    # Async decorators
    @async_log_function
    async def my_async_function():
        pass

    # Async context managers
    async with AsyncLoggingContext(level="DEBUG"):
        await some_async_operation()
"""

# Import the AsyncLogger class
from .async_logger import AsyncLogger

# Import all async functionality
from .async_logging import (
    AsyncLoggingContext,
    AsyncQueueHandler,
    AsyncQuietLoggingContext,
    AsyncTemporaryHandlerContext,
    AsyncVerboseLoggingContext,
    AsyncVisualLoggingContext,
    async_log_class,
    async_log_function,
    cleanup_all_async_handlers,
    get_all_async_handlers,
    log_async_class,
    log_async_function,
)

# Define what gets exported
__all__ = [
    # Async logger interface
    "AsyncLogger",
    # Async handlers
    "AsyncQueueHandler",
    # Async decorators
    "async_log_function",
    "async_log_class",
    "log_async_function",  # Alias
    "log_async_class",  # Alias
    # Async context managers
    "AsyncLoggingContext",
    "AsyncQuietLoggingContext",
    "AsyncTemporaryHandlerContext",
    "AsyncVerboseLoggingContext",
    "AsyncVisualLoggingContext",
    # Utility functions
    "cleanup_all_async_handlers",
    "get_all_async_handlers",
]
