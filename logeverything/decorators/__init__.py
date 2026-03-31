"""
LogEverything Decorators

This module provides decorators for automatically logging function calls,
I/O operations, and class methods with minimal code changes.

Usage::

    from logeverything.decorators import log, log_function, log_io, log_class

    @log  # Smart decorator that auto-detects function vs I/O vs class
    def my_function():
        pass

    @log_function  # Explicit function logging
    def my_function():
        pass

    @log_io  # For I/O operations
    def read_file(filename):
        pass

    @log_class  # For class method logging
    class MyClass:
        pass
"""

# Import all decorators from the decorators module
from .decorators import log_class, log_function, log_io

# Import the smart decorator from smart_decorator module
from .smart_decorator import log

# Import async decorators from asyncio module for convenience
try:
    from ..asyncio import async_log_class, async_log_function, log_async_class, log_async_function

    _async_available = True
except ImportError:
    _async_available = False

# Define what gets exported when someone does "from logeverything.decorators import *"
if _async_available:
    __all__ = [
        "log",  # Smart unified decorator (most commonly used)
        "log_function",  # Explicit function logging
        "log_io",  # I/O operation logging
        "log_class",  # Class method logging
        # Async decorators (for convenience)
        "async_log_function",  # Async function logging
        "async_log_class",  # Async class method logging
        "log_async_function",  # Alias for async_log_function
        "log_async_class",  # Alias for async_log_class
    ]
else:
    __all__ = [
        "log",  # Smart unified decorator (most commonly used)
        "log_function",  # Explicit function logging
        "log_io",  # I/O operation logging
        "log_class",  # Class method logging
    ]
