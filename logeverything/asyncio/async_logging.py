"""
Asynchronous support for the LogEverything library.

This module provides asynchronous logging capabilities, including:
- Async-compatible handlers with non-blocking emit() methods
- Queue-based log record processing
- Async-compatible decorator for logging async functions
- Task context tracking for proper indent management

Performance optimizations:
- Lazy evaluation of expensive operations
- Cached function metadata
- Fast path for disabled logging
- Reduced function call overhead
"""

import contextvars
import functools
import inspect
import logging
import queue
import sys
import threading
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union, cast

# Import core functionality
from .. import core as core_module
from ..core import find_logger_for_decorator

_config = core_module._config
_context = core_module._context

# Import unified indent functions - these now delegate to IndentManager
decrement_indent = core_module.decrement_indent
get_current_indent = core_module.get_current_indent
get_logger = core_module.get_logger
increment_indent = core_module.increment_indent

# Define type variables for better type hints
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])

# Global registry to track all AsyncQueueHandler instances
# This is critical for preventing thread leaks during testing
_global_handler_registry: Set["AsyncQueueHandler"] = set()


# Global handler pool for reusing AsyncQueueHandler instances
_handler_pool: Dict[str, List["AsyncQueueHandler"]] = {}
_handler_pool_lock = threading.Lock()


def get_pooled_handler(
    queue_size: int = 1000,
    target_handlers: Optional[List[Any]] = None,
    flush_level: int = logging.CRITICAL,
    flush_interval: float = 1.0,
) -> "AsyncQueueHandler":
    """Get a reusable handler from the pool or create a new one."""
    target_handlers = target_handlers or []

    # Create a key based on configuration
    key = f"{queue_size}_{flush_level}_{flush_interval}_{len(target_handlers)}"

    with _handler_pool_lock:
        if key in _handler_pool and _handler_pool[key]:
            handler = _handler_pool[key].pop()
            # Update target handlers
            handler.target_handlers = target_handlers
            return handler

    # Create new handler if none available in pool
    return AsyncQueueHandler(
        queue_size=queue_size,
        target_handlers=target_handlers,
        flush_level=flush_level,
        flush_interval=flush_interval,
    )


def return_handler_to_pool(handler: "AsyncQueueHandler") -> None:
    """Return a handler to the pool for reuse."""
    if not handler or handler._stop_event.is_set():
        return

    # Create key based on configuration
    key = (
        f"{handler.queue.maxsize}_{handler.flush_level}"
        f"_{handler.flush_interval}_{len(handler.target_handlers)}"
    )

    with _handler_pool_lock:
        if key not in _handler_pool:
            _handler_pool[key] = []

        # Limit pool size to prevent memory leaks
        if len(_handler_pool[key]) < 5:
            # Clear the queue but keep the thread alive
            while not handler.queue.empty():
                try:
                    handler.queue.get_nowait()
                    handler.queue.task_done()
                except Exception:
                    break

            handler.target_handlers = []  # Clear references
            _handler_pool[key].append(handler)
        else:
            # Pool full, properly close the handler
            handler.close()


def get_all_async_handlers() -> List["AsyncQueueHandler"]:
    """Get all currently active AsyncQueueHandler instances."""
    return list(_global_handler_registry)


def cleanup_all_async_handlers() -> int:
    """Close all registered AsyncQueueHandler instances."""
    count = 0
    for handler in list(_global_handler_registry):
        try:
            handler.close()
            count += 1
        except Exception as e:
            # Log exception rather than silently ignoring it
            logging.getLogger(__name__).warning(f"Error closing handler {handler}: {e}")
    return count


def cleanup_all_async_handlers_optimized() -> int:
    """Close all registered AsyncQueueHandler instances with optimized batch processing."""
    count = 0

    # Signal all handlers to stop first (don't wait)
    handlers_to_close = list(_global_handler_registry)
    for handler in handlers_to_close:
        try:
            handler._stop_event.set()
        except Exception:
            pass  # nosec B110 -- shutdown cleanup, logging could cause recursion

    # Small delay to allow threads to see the stop signal
    time.sleep(0.01)

    # Now close them with minimal individual timeouts
    for handler in handlers_to_close:
        try:
            # Skip the normal close() method and do fast cleanup
            if handler._worker_thread and handler._worker_thread.is_alive():
                handler._worker_thread.join(timeout=0.01)  # Very short timeout

            # Quick flush
            try:
                while not handler.queue.empty():
                    handler.queue.get_nowait()
                    handler.processed_records += 1
            except Exception:
                pass  # nosec B110 -- shutdown cleanup, logging could cause recursion

            # Close target handlers without waiting
            for target_handler in handler.target_handlers:
                try:
                    target_handler.close()
                except Exception:
                    pass  # nosec B110 -- best-effort cleanup

            _global_handler_registry.discard(handler)
            count += 1
        except Exception as e:
            # Log exception rather than silently ignoring it
            logging.getLogger(__name__).warning(f"Error closing handler {handler}: {e}")

    return count


class AsyncQueueHandler(logging.Handler):
    """
    A logging handler that queues log records for asynchronous processing.

    This handler places log records into a queue for processing by a separate
    worker thread, allowing the calling thread or task to continue execution
    without waiting for logging I/O to complete.
    """

    def __init__(
        self,
        queue_size: int = 1000,
        target_handlers: Optional[List[logging.Handler]] = None,
        flush_level: int = logging.CRITICAL,
        flush_interval: float = 1.0,
        name: str = "async_handler",
    ):
        """
        Initialize the AsyncQueueHandler.

        Args:
            queue_size: Maximum number of records in the queue (default: 1000)
            target_handlers: Handlers to process records from the queue (default: None)
            flush_level: Records >= this level trigger immediate flush (default: CRITICAL)
            flush_interval: Seconds between background flushes (default: 1.0)
            name: Name for the handler and worker thread (default: "async_handler")
        """
        super().__init__()
        self.name = name
        self.queue = queue.Queue(maxsize=queue_size)  # type: queue.Queue[logging.LogRecord]
        self.target_handlers = target_handlers or []
        self.flush_level = flush_level
        self.flush_interval = flush_interval  # Worker thread and control flags
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._flush_event = threading.Event()

        # Stats for monitoring
        self.dropped_records = 0
        self.processed_records = 0
        self.last_flush_time = time.time()

        # Start the worker thread
        self._start_worker()

        # Register this handler globally for cleanup tracking
        _global_handler_registry.add(self)

    def _start_worker(self) -> None:
        """Start the worker thread to process records from the queue."""
        if self._worker_thread is not None and self._worker_thread.is_alive():
            return  # Worker thread already running

        self._stop_event.clear()
        self._worker_thread = threading.Thread(
            target=self._process_queue,
            name=f"{self.name}_worker",
            daemon=True,  # Use daemon thread so it doesn't block program exit
        )
        self._worker_thread.start()

    def _process_queue(self) -> None:
        """Worker thread function to process log records from the queue."""
        while not self._stop_event.is_set():
            try:
                # Wait for either a record to appear or a flush interval
                try:
                    record = self.queue.get(timeout=self.flush_interval)
                except queue.Empty:
                    # No new records, check if we need to flush
                    self._maybe_flush()
                    continue

                # Check for sentinel None (signals shutdown)
                if record is None:
                    self.queue.task_done()  # type: ignore[unreachable]
                    break

                # Process the record
                self._process_record(record)
                self.queue.task_done()
                self.processed_records += 1

                # Check if we should do a full flush
                self._maybe_flush()

            except Exception:
                # Log any processing errors to stderr but keep thread running
                print("Error in AsyncQueueHandler worker thread:", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)

    def _maybe_flush(self) -> None:
        """Check if we should flush the queue based on time or explicit event."""
        current_time = time.time()
        if self._flush_event.is_set() or current_time - self.last_flush_time >= self.flush_interval:
            self.flush()
            self.last_flush_time = current_time
            self._flush_event.clear()

    def _process_record(self, record: logging.LogRecord) -> None:
        """Process a single log record by sending it to all target handlers."""
        for handler in self.target_handlers:
            if record.levelno >= handler.level:
                try:
                    handler.handle(record)
                except Exception:
                    print(f"Error in handler {handler}:", file=sys.stderr)
                    traceback.print_exc(file=sys.stderr)

    def emit(self, record: logging.LogRecord) -> None:
        """
        Queue the record for asynchronous processing.

        This is a non-blocking operation that returns immediately, allowing
        the calling code to continue execution without waiting for logging I/O.

        Args:
            record: The LogRecord to process
        """
        try:
            self.queue.put_nowait(record)
            # If this is a high-priority record, trigger an immediate flush
            if record.levelno >= self.flush_level:
                self._flush_event.set()
        except queue.Full:
            # Queue is full, increment dropped record count
            self.dropped_records += 1
            # If this is a critical record, try to log directly
            if record.levelno >= logging.CRITICAL:
                for handler in self.target_handlers:
                    if record.levelno >= handler.level:
                        handler.handle(record)
        except Exception:
            self.handleError(record)

    def flush(self) -> None:
        """
        Process all pending records in the queue.

        This is a more expensive operation that ensures all records
        have been sent to the target handlers.
        """
        while not self.queue.empty():
            try:
                record = self.queue.get(block=False)
                if record is None:
                    # Skip sentinel records used for shutdown signaling
                    self.queue.task_done()  # type: ignore[unreachable]
                    continue
                self._process_record(record)
                self.queue.task_done()
                self.processed_records += 1
            except queue.Empty:
                break

    def close(self) -> None:
        """
        Close the handler and shut down the worker thread.

        This ensures all records are processed before shutting down.
        """
        # Signal the worker thread to stop
        self._stop_event.set()

        # Put a sentinel None into the queue to wake up the worker thread
        # if it's blocked on queue.get()
        try:
            self.queue.put_nowait(None)  # type: ignore[arg-type]
        except queue.Full:
            pass  # Queue is full, worker will see stop_event on next timeout

        # Wait for the worker thread to finish with adequate timeout
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)

        # Process any remaining records
        self.flush()

        # Close target handlers
        for handler in self.target_handlers:
            handler.flush()
            handler.close()

        # Unregister this handler from global registry
        _global_handler_registry.discard(self)

        # Call the parent class close method
        super().close()


# Context variable for tracking async task context

# Create context variables for async task tracking
_async_indent: Optional[contextvars.ContextVar[int]]
_async_function_stack: Optional[contextvars.ContextVar[List[str]]]
HAS_CONTEXTVARS: bool = False  # Default to False

try:
    _async_indent = contextvars.ContextVar("async_indent", default=0)
    _async_function_stack = contextvars.ContextVar("async_function_stack", default=[])
    HAS_CONTEXTVARS = True
except ImportError:
    # Fall back to thread-local storage if contextvars is not available
    _async_indent = None
    _async_function_stack = None


def get_async_indent() -> int:
    """
    Get the current indentation level for async functions.

    Returns:
        The current indentation level

    Note: This function now delegates to the unified IndentManager system.
    """
    from ..indent_manager import get_indent_manager

    return get_indent_manager().get_level()


def increment_async_indent() -> int:
    """
    Increment the indentation level for async functions.

    Returns:
    The new indentation level

    Note: This function now delegates to the unified IndentManager system.
    """
    from ..indent_manager import get_indent_manager

    return get_indent_manager().increment()


def decrement_async_indent() -> int:
    """
    Decrement the indentation level for async functions.

    Returns:
        The new indentation level

    Note: This function now delegates to the unified IndentManager system.
    """
    from ..indent_manager import get_indent_manager

    return get_indent_manager().decrement()


def async_log_function(
    func: Optional[F] = None,
    log_entry_exit: bool = True,
    log_arguments: bool = True,
    log_return_values: bool = True,
    using: Optional[str] = None,
    **options: Any,
) -> Union[F, Callable[[F], F]]:
    """
    Optimized decorator for logging entry, exit, and execution time of async functions.

    Performance optimizations:
    - Fast path for disabled logging
    - Cached function metadata at decoration time
    - Reduced function call overhead
    - Optimized string building

    Args:
        func: The async function to decorate (automatically passed when used as @async_log_function)
        log_entry_exit: Enable/disable logging of function entry and exit
        log_arguments: Enable/disable logging of function arguments
        log_return_values: Enable/disable logging of return values
        using: Name of the LogEverything Logger instance to use for logging
        **options: Additional decorator options

    Returns:
        The decorated function
    """

    def decorator(func: F) -> F:
        # Check if this is an async function at decoration time
        is_async = inspect.iscoroutinefunction(func)

        if not is_async:
            # If it's not an async function, use the regular log_function decorator
            from ..decorators.decorators import log_function

            return cast(
                F,
                log_function(
                    func,
                    log_entry_exit=log_entry_exit,
                    log_arguments=log_arguments,
                    log_return_values=log_return_values,
                    using=using,
                    **options,
                ),
            )

        # Smart logger selection: Use LogEverything Logger instances when available
        # Store the requested logger name for lazy resolution at runtime
        requested_logger_name = using
        fallback_logger_name = options.get("logger_name", func.__module__)

        func_name = _get_qualified_name(
            func
        )  # Cache static data at decoration time for performance
        try:
            argspec = inspect.getfullargspec(func)
            args_list = argspec.args
        except (OSError, TypeError):
            # Handle built-in functions or other edge cases
            args_list = []

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Fast path: Skip logging if disabled during runtime
            if not _config.get("log_entry_exit", True):
                return await func(*args, **kwargs)

            # Lazy logger resolution: resolve logger at runtime
            try:
                # Try to find an appropriate LogEverything Logger instance
                logeverything_logger = find_logger_for_decorator(requested_logger_name, func_name)

                # Smart casting: Check if logger is compatible with async
                # If sync logger used with async, reuse existing or create temp
                if (
                    hasattr(logeverything_logger, "_is_async")
                    and not logeverything_logger._is_async
                ):
                    # Logger is sync but function is async - reuse the async handler if available
                    # Check if there's already an async-compatible handler we can reuse
                    existing_async_handlers = [
                        handler
                        for handler in logeverything_logger._logger.handlers
                        if hasattr(handler, "_worker_thread")
                    ]

                    if existing_async_handlers:
                        # Reuse existing async infrastructure
                        logger = logeverything_logger._logger
                        logeverything_logger = logeverything_logger
                    else:
                        # Create temporary async-compatible logger only if absolutely needed
                        temp_async_logger = _create_async_compatible_logger(logeverything_logger)
                        logger = temp_async_logger._logger
                        logeverything_logger = temp_async_logger
                else:
                    # Use the LogEverything logger's internal Python logger
                    logger = logeverything_logger._logger
            except ValueError:
                # Re-raise ValueError if specific logger was requested but not found
                raise
            except Exception:
                # Fallback to traditional logger cache for other exceptions
                from ..decorators.decorators import _get_cached_logger

                logger = _get_cached_logger(fallback_logger_name)
                logeverything_logger = None

            # Check visual configuration - first from logger instance, then global config
            if logeverything_logger and hasattr(logeverything_logger, "_options"):
                # Use logger-specific visual configuration if available
                visual_config = logeverything_logger._options
                use_symbols = visual_config.get("use_symbols", _config.get("use_symbols", True))
                use_indent = visual_config.get("use_indent", _config.get("use_indent", True))
            else:
                # Fall back to global configuration
                use_symbols = _config.get("use_symbols", True)
                use_indent = _config.get("use_indent", True)

            # Get source info for line numbers (skip expensive frame introspection if disabled)
            source_info = None
            if _config.get("include_line_numbers", True):
                from ..decorators.decorators import _get_source_info

                source_info = _get_source_info(inspect.currentframe())

            # Prepare function call symbols and formatting
            call_symbol = "🔵 CALL" if use_symbols else "→"
            done_symbol = "✅ DONE" if use_symbols else "←"

            # Get proper indentation string from IndentManager BEFORE incrementing
            from ..indent_manager import get_indent_manager

            indent_manager = get_indent_manager()
            entry_indent = indent_manager.get_indent_string() if use_indent else ""

            # Format arguments
            from ..decorators.decorators import _format_args

            args_str = _format_args(args, kwargs, args_list)

            # Format source info
            source_str = ""
            if source_info and _config.get("include_line_numbers", True):
                source_str = f" [{source_info['file']}:{source_info['line']}]"

            # Generate call_id and push onto call stack for hierarchy tracking
            call_id = indent_manager.generate_call_id()
            indent_manager.push_call(call_id)

            # Log entry at current indent level for proper nesting
            logger.info(
                f"{entry_indent}{call_symbol} {func_name}({args_str}){source_str}",
                extra={"log_type": "call_entry"},
            )

            # NOW increment indent for the function body
            increment_async_indent()

            start_time = time.time()
            try:
                # Execute the async function
                result = await func(*args, **kwargs)

                # Calculate execution time
                elapsed = (time.time() - start_time) * 1000  # in ms

                # Format return value
                if _config.get("log_return_values", True):
                    from ..decorators.decorators import _format_value

                    result_str = f" ➜ {_format_value(result)}"
                else:
                    result_str = ""

                # Log successful completion at same level as entry
                logger.info(
                    f"{entry_indent}{done_symbol} {func_name} ({elapsed:.2f}ms){result_str}",
                    extra={"log_type": "call_exit"},
                )
                return result

            except Exception as e:
                # Log exception if configured
                elapsed = (time.time() - start_time) * 1000  # in ms
                error_msg = f"{e.__class__.__name__}: {str(e)}"
                fail_symbol = "❌ FAIL" if use_symbols else "✗"
                # Log failure at same level as entry
                logger.error(
                    f"{entry_indent}{fail_symbol} {func_name} ({elapsed:.2f}ms): {error_msg}",
                    extra={"log_type": "call_exit"},
                )
                raise
            finally:
                decrement_async_indent()
                indent_manager.pop_call()

        return cast(F, wrapper)

    # Handle both @async_log_function and @async_log_function() syntax
    if func is not None:
        return decorator(func)

    return decorator


def async_log_class(cls: Optional[Type] = None, using: Optional[str] = None, **options: Any) -> Any:
    """
    Decorator to apply async_log_function to all async methods in a class.

    This decorator automatically wraps all coroutine methods in a class with
    the async_log_function decorator, while regular methods get the standard
    log_function decorator.

    Args:
        cls: The class to decorate (automatically passed when used as @async_log_class)
        using: Name of the LogEverything Logger instance to use for logging
        **options: Decorator options that override default configuration

    Returns:
        The decorated class
    """

    def decorator(cls: Type) -> Type:
        # Get regular log_class decorator for non-async methods
        from ..decorators.decorators import log_class

        # Pass parameters to the regular log_class decorator for non-async methods
        if using is not None:
            options["using"] = using

        # First apply the regular log_class decorator
        # This will handle all the non-async methods
        cls = log_class(cls, **options)

        # Then wrap all async methods that weren't already wrapped
        for attr_name in dir(cls):
            # Skip special methods and properties
            if attr_name.startswith("__") or isinstance(getattr(cls, attr_name, None), property):
                continue

            attr = getattr(cls, attr_name)

            # Check for async methods
            if inspect.isfunction(attr) and inspect.iscoroutinefunction(attr):
                # Check if it's already decorated
                if not hasattr(attr, "_log_decorated") and not hasattr(
                    attr, "_logeverything_decorated"
                ):
                    # Apply async_log_function decorator with options
                    decorated: Any = async_log_function(using=using, **options)(cast(Any, attr))
                    setattr(decorated, "_log_decorated", True)
                    setattr(cls, attr_name, decorated)

        # Return the fully decorated class
        return cls

    # Handle both @async_log_class and @async_log_class() syntax
    if cls is not None:
        return decorator(cls)

    return decorator


class AsyncLoggingContext:
    """
    An async context manager for temporarily modifying logging configuration.

    This allows you to change logging settings within an async context and
    automatically restore the previous settings when exiting the context.

    Example:
        >>> async with AsyncLoggingContext(level="DEBUG", log_entry_exit=True):
        ...     # Code here will use DEBUG level and log function entry/exit
        ...     await async_function()
        ... # Original settings are restored after the context
    """

    def __init__(
        self,
        level: Optional[Union[int, str]] = None,
        log_entry_exit: Optional[bool] = None,
        log_arguments: Optional[bool] = None,
        log_return_values: Optional[bool] = None,
        beautify: Optional[bool] = None,
        indent_level: Optional[int] = None,
        handlers: Optional[List[str]] = None,
        logger_name: Optional[str] = None,
        capture_print: Optional[bool] = None,
        print_logger_name: Optional[str] = None,
        print_level: Optional[int] = None,
        print_prefix: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize an async logging context with temporary configuration.

        Args:
            level: Temporarily change the logging level
            log_entry_exit: Whether to log function entry and exit
            log_arguments: Whether to log function arguments
            log_return_values: Whether to log function return values
            beautify: Whether to beautify logs with visual elements
            indent_level: Indentation level for beautified logs
            handlers: List of handlers to use temporarily
            logger_name: Name of the logger to configure
            capture_print: Whether to capture print statements
            print_logger_name: Logger name for captured print statements
            print_level: Logging level for captured print statements
            print_prefix: Prefix for captured print statements
            **kwargs: Additional configuration options
        """
        # Import here to avoid circular imports
        from ..contexts.contexts import LoggingContext

        # Create a regular LoggingContext that we'll delegate to
        self.context = LoggingContext(
            level=level,
            log_entry_exit=log_entry_exit,
            log_arguments=log_arguments,
            log_return_values=log_return_values,
            beautify=beautify,
            indent_level=indent_level,
            handlers=handlers,
            logger_name=logger_name,
            capture_print=capture_print,
            print_logger_name=print_logger_name,
            print_level=print_level,
            print_prefix=print_prefix,
            **kwargs,
        )

    async def __aenter__(self) -> Dict[str, Any]:
        """
        Enter the async context, delegate to the synchronous context.

        Returns:
            Dict[str, Any]: The current configuration
        """
        return self.context.__enter__()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit the async context, delegate to the synchronous context.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        return self.context.__exit__(exc_type, exc_val, exc_tb)

    def __enter__(self) -> Dict[str, Any]:
        """
        Support using this context in regular synchronous code as well.

        Returns:
            Dict[str, Any]: The current configuration
        """
        return self.context.__enter__()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Support using this context in regular synchronous code as well.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        return self.context.__exit__(exc_type, exc_val, exc_tb)


# Create specialized async context managers by extending existing ones
class AsyncVerboseLoggingContext(AsyncLoggingContext):
    """
    An async context manager for temporarily increasing logging verbosity.

    This is the async version of VerboseLoggingContext, specialized for
    maximizing log information for async code blocks.

    Example:
        >>> async with AsyncVerboseLoggingContext():
        ...     # This code will produce detailed logs
        ...     await complex_async_operation()
        ... # Original logging verbosity is restored after the context
    """

    def __init__(
        self,
        level: Union[int, str] = logging.DEBUG,
        log_entry_exit: bool = True,
        log_arguments: bool = True,
        log_return_values: bool = True,
        capture_print: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Initialize an async verbose logging context with maximum verbosity.

        Args:
            level: The logging level to use (defaults to DEBUG)
            log_entry_exit: Whether to log function entry and exit (defaults to True)
            log_arguments: Whether to log function arguments (defaults to True)
            log_return_values: Whether to log function return values (defaults to True)
            capture_print: Whether to capture print statements (defaults to True)
            **kwargs: Additional configuration options
        """
        super().__init__(
            level=level,
            log_entry_exit=log_entry_exit,
            log_arguments=log_arguments,
            log_return_values=log_return_values,
            capture_print=capture_print,
            **kwargs,
        )


class AsyncQuietLoggingContext(AsyncLoggingContext):
    """
    An async context manager for temporarily suppressing logging output.

    This is the async version of QuietLoggingContext, specialized for
    reducing log verbosity for async code blocks.

    Example:
        >>> async with AsyncQuietLoggingContext():
        ...     # This code will produce minimal logs
        ...     await noisy_async_operation()
        ... # Original logging verbosity is restored after the context
    """

    def __init__(
        self,
        level: Union[int, str] = logging.WARNING,
        log_entry_exit: bool = False,
        log_arguments: bool = False,
        log_return_values: bool = False,
        capture_print: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize an async quiet logging context with minimized verbosity.

        Args:
            level: The logging level to use (defaults to WARNING)
            log_entry_exit: Whether to log function entry and exit (defaults to False)
            log_arguments: Whether to log function arguments (defaults to False)
            log_return_values: Whether to log function return values (defaults to False)
            capture_print: Whether to capture print statements (defaults to False)
            **kwargs: Additional configuration options
        """
        super().__init__(
            level=level,
            log_entry_exit=log_entry_exit,
            log_arguments=log_arguments,
            log_return_values=log_return_values,
            capture_print=capture_print,
            **kwargs,
        )


class AsyncVisualLoggingContext(AsyncLoggingContext):
    """
    An async context manager for temporarily enabling visual logging enhancements.

    This is the async version of VisualLoggingContext, allowing you to enable
    colors, symbols, and other visual elements for a specific async code block.

    Example:
        >>> async with AsyncVisualLoggingContext(use_symbols=True, color_theme="bold"):
        ...     # This code will have visual logging enhancements
        ...     await complex_visualization()
        ... # Original visual settings are restored after the context
    """

    def __init__(
        self,
        visual_mode: Optional[bool] = True,
        use_symbols: Optional[bool] = None,
        use_indent: Optional[bool] = None,
        align_columns: Optional[bool] = None,
        color_theme: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize an async visual logging context with visual enhancements.

        Args:
            visual_mode: Master switch for visual enhancements
            use_symbols: Whether to use Unicode symbols for log levels
            use_indent: Whether to use visual indentation with box drawing
            align_columns: Whether to align columns in log output
            color_theme: Color theme to use for console output
            **kwargs: Additional configuration options
        """
        super().__init__(
            visual_mode=visual_mode,
            use_symbols=use_symbols,
            use_indent=use_indent,
            align_columns=align_columns,
            color_theme=color_theme,
            **kwargs,
        )


class AsyncTemporaryHandlerContext:
    """
    An async context manager for temporarily using specific log handlers.

    This is the async version of TemporaryHandlerContext, allowing you to
    temporarily switch handlers for async code blocks.

    Example:
        >>> async with AsyncTemporaryHandlerContext(["file", "json"]):
        ...     # This code will log to file and JSON, ignoring console
        ...     await important_async_operation()
        ... # Original handlers are restored after the context
    """

    def __init__(self, handlers: List[Union[str, logging.Handler]]) -> None:
        """
        Initialize an async temporary handler context.

        Args:
            handlers: A list of handler names or actual handler objects to use temporarily
        """
        # Import here to avoid circular imports
        from ..contexts.contexts import TemporaryHandlerContext

        # Create a regular TemporaryHandlerContext that we'll delegate to
        self.context = TemporaryHandlerContext(handlers)

    async def __aenter__(self) -> Dict[str, Any]:
        """
        Enter the async context, delegate to the synchronous context.

        Returns:
            Dict[str, Any]: The current configuration
        """
        return self.context.__enter__()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit the async context, delegate to the synchronous context.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        return self.context.__exit__(exc_type, exc_val, exc_tb)

    def __enter__(self) -> Dict[str, Any]:
        """
        Support using this context in regular synchronous code as well.

        Returns:
            Dict[str, Any]: The current configuration
        """
        return self.context.__enter__()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Support using this context in regular synchronous code as well.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        return self.context.__exit__(exc_type, exc_val, exc_tb)


# Aliases for better API naming
log_async_function = async_log_function
log_async_class = async_log_class

# Async isolation tracking
_async_isolation_id: Optional[contextvars.ContextVar[int]] = None
_async_isolation_counter = 0
_async_isolation_lock = threading.Lock()


def _get_next_async_isolation_id() -> int:
    """Get the next isolation ID for async context separation."""
    global _async_isolation_counter
    with _async_isolation_lock:
        _async_isolation_counter += 1
        return _async_isolation_counter


def _initialize_async_isolation() -> None:
    """Initialize async isolation context."""
    global _async_isolation_id
    if HAS_CONTEXTVARS and _async_isolation_id is None:
        try:
            _async_isolation_id = contextvars.ContextVar(
                "async_isolation_id", default=_get_next_async_isolation_id()
            )
        except ImportError:
            pass


def _get_async_isolation_id() -> int:
    """Get the current async isolation ID."""
    if HAS_CONTEXTVARS and _async_isolation_id is not None:
        return _async_isolation_id.get()
    return 0


# Initialize async isolation on module load
_initialize_async_isolation()


# Import helper functions from decorators
def _get_qualified_name(func: Callable[..., Any]) -> str:
    """Get the qualified name of a function (with class name if it's a method)."""
    if hasattr(func, "__qualname__") and hasattr(func, "__name__"):
        qualname = func.__qualname__
        name = func.__name__

        # If __qualname__ has meaningful info beyond __name__, use it
        if qualname != name and not qualname.endswith(".<locals>." + name):
            return qualname

    # Default to __name__ or a fallback
    return getattr(func, "__name__", str(func))


def _create_async_compatible_logger(sync_logger: Any) -> Any:
    """
    Create a temporary async-compatible logger from a sync logger.

    This preserves the original logger instance for the user while creating
    a temporary async-compatible copy for internal decorator use.

    Args:
        sync_logger: The original sync LogEverything Logger instance

    Returns:
        A temporary async-compatible logger with the same configuration
    """
    # Import here to avoid circular imports
    from .async_logger import AsyncLogger

    # Create shared temporary async logger to prevent proliferation
    # Use a consistent name to enable reuse across decorators
    shared_temp_name = f"{sync_logger.name}_async_shared"

    # Check if we already have this temporary logger
    from ..core import _active_loggers

    if shared_temp_name in _active_loggers:
        return _active_loggers[shared_temp_name]

    # Create new shared temporary async logger
    temp_async_logger = AsyncLogger(
        name=shared_temp_name,
        level=sync_logger._logger.level,
        format_type=getattr(sync_logger, "_format_type", "default"),
        handlers=getattr(sync_logger, "_handlers", []),
        auto_setup=True,
        _register=True,  # Register it so it can be found by other decorators
    )

    # Copy visual configuration if available
    if hasattr(sync_logger, "_options"):
        temp_async_logger._options = sync_logger._options.copy()

    return temp_async_logger


def _create_sync_compatible_logger(async_logger: Any) -> Any:
    """
    Create a temporary sync-compatible logger from an async logger.

    This preserves the original logger instance for the user while creating
    a temporary sync-compatible copy for internal decorator use.

    Args:
        async_logger: The original async LogEverything Logger instance

    Returns:
        A temporary sync-compatible logger with the same configuration
    """
    # Import here to avoid circular imports
    from ..logger import Logger

    # Create temporary sync logger with same configuration as async logger
    # This doesn't modify the original logger - it creates a new instance
    temp_sync_logger = Logger(
        name=f"{async_logger.name}_sync_temp",
        level=async_logger._logger.level,
        format_type=getattr(async_logger, "_format_type", "default"),
        handlers=getattr(async_logger, "_handlers", []),
    )

    # Copy visual configuration if available
    if hasattr(async_logger, "_options"):
        temp_sync_logger._options = async_logger._options.copy()

    return temp_sync_logger
