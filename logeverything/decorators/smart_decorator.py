"""
Smart unified decorator module for LogEverything.

This module provides a smart unified decorator that can automatically detect
whether it's being applied to a function, method, or class, and apply the
appropriate logging behavior including async function detection.
"""

import inspect
from typing import Any, Callable, Optional, Type, TypeVar, Union, cast

from .decorators import log_class, log_function, log_io

# Type variable for functions
F = TypeVar("F", bound=Callable)
# Type variable for classes
T = TypeVar("T", bound=type)


def _is_io_function(func: Callable) -> bool:
    """
    Determine if a function performs I/O operations based on its name and source code.

    Args:
        func: The function to analyze.

    Returns:
        True if the function appears to perform I/O operations, False otherwise.
    """
    func_name = func.__name__.lower()
    source_code = None

    try:
        # Try to get the source code of the function
        source_code = inspect.getsource(func).lower()
    except (OSError, IOError, TypeError):
        # Can't get source code, just use function name for detection
        pass

    # Check if the function performs I/O operations
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
        "_io",  # More specific - looks for _io suffix/prefix patterns
        "io_",  # More specific - looks for io_ prefix patterns
        "input",
        "output",
    ]

    # Function name or parameters suggest I/O operations
    name_suggests_io = any(indicator in func_name for indicator in io_indicators)

    # Source code suggests I/O operations
    if source_code:
        code_suggests_io = any(
            [
                "with open" in source_code,
                "open(" in source_code,
                "requests." in source_code,
                "urllib" in source_code,
                "socket." in source_code,
                "http" in source_code,
                "curl" in source_code,
                "fetch" in source_code,
                "download" in source_code,
                "upload" in source_code,
            ]
        )
    else:
        code_suggests_io = False

    return name_suggests_io or code_suggests_io


def log(
    obj: Optional[Union[F, Type[T]]] = None, using: Optional[str] = None, **options: Any
) -> Union[Union[F, Type[T]], Callable[[Union[F, Type[T]]], Union[F, Type[T]]]]:
    """
    Smart unified decorator that automatically detects and applies appropriate logging.

    This decorator will:
    - Apply async logging for async functions (coroutines)
    - Apply I/O logging for functions that perform I/O operations (if they match certain patterns)
    - Apply function logging for regular functions
    - Apply class logging for classes

    Args:
        obj: The function or class to decorate
        using: Name of the LogEverything Logger instance to use for logging
        **options: Decorator options that override default configuration

    Returns:
        The decorated function or class
    """

    def decorator(obj: Union[F, Type[T]]) -> Union[F, Type[T]]:  # Skip if disabled
        if options.get("enabled", True) is False:
            return obj

        # Pass the 'using' parameter to the underlying decorators
        if using is not None:
            options["using"] = using

        # Determine the type of object being decorated
        if inspect.isclass(obj):
            # It's a class - apply log_class
            return cast(Type[T], log_class(obj, **options))
        elif inspect.isfunction(obj) or inspect.ismethod(obj):
            # First check if it's an async function
            if inspect.iscoroutinefunction(obj):
                # It's an async function - use async_log_function
                try:
                    from ..asyncio import async_log_function

                    return cast(F, async_log_function(cast(Callable, obj), **options))
                except ImportError:
                    # Fallback to regular function logging if async module not available
                    return cast(F, log_function(cast(Callable, obj), **options))
            # If function likely performs I/O, use log_io, otherwise use log_function
            elif _is_io_function(obj):
                return cast(F, log_io(cast(Callable, obj), **options))
            else:
                return cast(F, log_function(cast(Callable, obj), **options))

        else:
            # Not a class or function - just return the original object
            return obj

    # If called with parameters, return the decorator function
    if obj is None:
        return decorator

    # If called without parameters, apply the decorator directly
    return decorator(obj)
