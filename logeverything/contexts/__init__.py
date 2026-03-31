"""
LogEverything Context Managers

This module provides context managers for controlling logging behavior within specific code blocks.
Includes both synchronous and asynchronous context managers.

Usage::

    from logeverything.contexts import LoggingContext, QuietLoggingContext
    from logeverything.contexts import AsyncLoggingContext, VisualLoggingContext

    # Synchronous contexts
    with LoggingContext(level="DEBUG"):
        # Code here will use DEBUG level logging
        pass

    # Asynchronous contexts
    async with AsyncLoggingContext(format_type="visual"):
        # Async code with visual formatting
        pass
"""

# Import async contexts from async_logging
from ..asyncio.async_logging import (
    AsyncLoggingContext,
    AsyncQuietLoggingContext,
    AsyncTemporaryHandlerContext,
    AsyncVerboseLoggingContext,
    AsyncVisualLoggingContext,
)

# Import sync contexts
from .contexts import (
    LoggingContext,
    QuietLoggingContext,
    TemporaryHandlerContext,
    VerboseLoggingContext,
    VisualLoggingContext,
)

# Define what gets exported
__all__ = [
    # Synchronous context managers
    "LoggingContext",
    "QuietLoggingContext",
    "TemporaryHandlerContext",
    "VerboseLoggingContext",
    "VisualLoggingContext",
    # Asynchronous context managers
    "AsyncLoggingContext",
    "AsyncQuietLoggingContext",
    "AsyncTemporaryHandlerContext",
    "AsyncVerboseLoggingContext",
    "AsyncVisualLoggingContext",
]
