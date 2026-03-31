"""
Print capturing functionality for the logeverything package.

This module provides functions to capture print statements and redirect them
to the logging system.
"""

import builtins
import logging  # Still needed for StreamHandler type checks
import sys
import threading
from types import TracebackType
from typing import Any, Callable, Dict, Literal, Optional, Protocol, TextIO, Type

from typing_extensions import ParamSpec, TypeVar, TypeVarTuple

# Import LogEverything's logger system
from ..core import _is_concurrent, get_logger

# Import INFO directly from levels module to avoid circular import
from ..utils.levels import INFO

# Create a thread-local storage for recursion prevention
_thread_local = threading.local()

# Cache for logger instances to reduce getLogger overhead
_logger_cache: Dict[str, Any] = {}

# Cache for handler enumeration result: (has_console_handler, has_any_handlers)
# Keyed by (logger_name, handler_count, root_handler_count) — invalidates when counts change
_handler_cache: Dict[tuple, tuple] = {}

# Define type variables for print function signature
P = ParamSpec("P")
R = TypeVar("R")
Ts = TypeVarTuple("Ts")


# Define protocol for print function
class PrintFuncProtocol(Protocol):
    def __call__(
        self,
        *args: Any,
        sep: str = ...,
        end: str = ...,
        file: Optional[TextIO] = ...,
        flush: bool = ...,
    ) -> None: ...


# Type for print function
PrintFunc = Callable[..., None]

# Original print function for use in internal functions
_original_print: PrintFunc = builtins.print

# Keep original print until after logging_print is defined
original_print = builtins.print


class PrintCaptureStream:
    """A stream class that captures writes and sends them to a logger."""

    def __init__(
        self,
        original_stream: TextIO,
        logger_name: str = "stdout",
        level: int = INFO,
        prefix: str = "[PRINT] ",
    ):
        """
        Initialize a PrintCaptureStream.

        Args:
            original_stream: Original stream to forward writes to
            logger_name: Name of the logger to log output to
            level: Logging level to use
            prefix: Prefix to add to logged messages
        """
        self.original_stream = original_stream
        self.logger_name = logger_name
        self.level = level
        self.prefix = prefix
        self.buffer = ""

    def write(self, text: str) -> int:
        """
        Write text to the stream and log it.

        Args:
            text: Text to write

        Returns:
            Number of characters written
        """
        # Write to original stream
        result = self.original_stream.write(text)

        # Accumulate text in buffer until we get a newline
        self.buffer += text

        # Process complete lines
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            if line:  # Skip empty lines
                self._log_line(line)

        return result

    def _log_line(self, line: str) -> None:
        """
        Log a line to the logger.

        Args:
            line: Line to log
        """  # Get logger
        logger = get_logger(f"logeverything.{self.logger_name}")

        # Prevent infinite recursion in logging
        if getattr(_thread_local, "in_logging", False):
            return

        try:
            _thread_local.in_logging = True
            # Log the line
            logger.log(self.level, f"{self.prefix}{line}")
        finally:
            _thread_local.in_logging = False

    def flush(self) -> None:
        """Flush the stream and log any remaining content."""
        self.original_stream.flush()
        # Log any remaining content in the buffer
        if self.buffer:
            self._log_line(self.buffer)
            self.buffer = ""

    def isatty(self) -> bool:
        """Return whether the original stream is a TTY."""
        return self.original_stream.isatty()

    @property
    def name(self) -> str:
        """Return the name of the original stream."""
        return getattr(self.original_stream, "name", "")

    @property
    def mode(self) -> str:
        """Return the mode of the original stream."""
        return getattr(self.original_stream, "mode", "")

    @property
    def closed(self) -> bool:
        """Return whether the original stream is closed."""
        return getattr(self.original_stream, "closed", False)


def logging_print(
    *args: Any,
    sep: str = " ",
    end: str = "\n",
    file: Optional[TextIO] = None,
    flush: bool = False,
    **kwargs: Any,
) -> None:
    """
    Optimized replacement for the built-in print function that logs output with smart isolation.

    Performance optimizations:
    - Cached logger instances with smart isolation (only when needed)
    - Bundled thread-local settings read (single getattr for settings tuple)
    - Cached handler enumeration (invalidates when handler count changes)
    - Direct _logger_cache lookup to skip _initialize_context() on cache hit
    - Fast path for silent mode (no console output)
    - Optimized string operations

    Args:
        *args: Values to print
        sep: Separator between values
        end: String to append after the last value
        file: File to write to
        flush: Whether to forcibly flush the stream
        **kwargs: Additional keyword arguments
    """
    # If file is specified, use original print
    if file is not None:
        _original_print(*args, sep=sep, end=end, file=file, flush=flush, **kwargs)
        return

    # Prevent infinite recursion in logging
    if getattr(_thread_local, "in_logging", False):
        _original_print(*args, sep=sep, end=end)
        return

    # Phase 2B: Read bundled print settings in one shot (single tuple read)
    settings = getattr(_thread_local, "print_settings", None)
    if settings is not None:
        _print_logger_name, _print_log_level, _print_prefix = settings
    else:
        _print_logger_name = getattr(_thread_local, "print_logger_name", "print")
        _print_log_level = getattr(_thread_local, "print_log_level", INFO)
        _print_prefix = getattr(_thread_local, "print_prefix", "[PRINT] ")

    # Optimized string conversion and joining
    if not args:
        output = ""
    elif len(args) == 1:
        output = str(args[0])
    else:
        output = sep.join(str(arg) for arg in args)

    log_output = output if end == "\n" else output + end

    # Phase 2C: Direct _logger_cache lookup to skip get_logger() / _initialize_context() overhead
    # Only use isolation suffix in concurrent environments
    isolation_suffix = ""
    if _is_concurrent() and hasattr(_thread_local, "print_isolation_id"):
        isolation_suffix = f"_iso_{_thread_local.print_isolation_id}"

    logger_name = f"logeverything.{_print_logger_name}{isolation_suffix}"
    logger = _logger_cache.get(logger_name)
    if logger is None:
        # Initialize isolation only on cache miss (first call per thread)
        _initialize_print_isolation()
        logger = get_logger(logger_name)
        _logger_cache[logger_name] = logger

    try:
        _thread_local.in_logging = True
        logger.log(_print_log_level, f"{_print_prefix}{log_output}")
    finally:
        _thread_local.in_logging = False

    # Phase 2A: Cached handler enumeration — keyed by handler counts
    logger_hcount = len(logger.handlers)
    root_logger = logging.getLogger()
    root_hcount = len(root_logger.handlers)
    cache_key = (logger_name, logger_hcount, root_hcount)

    cached = _handler_cache.get(cache_key)
    if cached is not None:
        has_console_handler, has_any_handlers = cached
    else:
        has_console_handler = False
        has_any_handlers = bool(logger.handlers)
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream in (
                sys.stdout,
                sys.stderr,
            ):
                has_console_handler = True
                break

        if not has_console_handler and not has_any_handlers:
            for handler in root_logger.handlers:
                if isinstance(handler, logging.StreamHandler) and handler.stream in (
                    sys.stdout,
                    sys.stderr,
                ):
                    has_console_handler = True
                    break
                elif handler:
                    has_any_handlers = True

        # Bound cache size to prevent unbounded growth
        if len(_handler_cache) > 200:
            _handler_cache.clear()
        _handler_cache[cache_key] = (has_console_handler, has_any_handlers)

    # Print to console only if we have console handlers AND we're not in a test/captured environment
    if has_console_handler and not (has_any_handlers and not has_console_handler):
        _original_print(output, end=end, flush=flush, **kwargs)
    elif not has_any_handlers:
        _original_print(output, end=end, flush=flush, **kwargs)


def enable_print_capture(
    logger_name: str = "print", level: int = INFO, prefix: str = "[PRINT] "
) -> None:
    """
    Enable print statement capturing.

    Args:
        logger_name: Name of the logger to log output to
        level: Logging level to use
        prefix: Prefix to add to logged messages
    """
    # Store settings in thread-local storage (both individual and bundled for fast access)
    _thread_local.print_logger_name = logger_name
    _thread_local.print_log_level = level
    _thread_local.print_prefix = prefix
    _thread_local.print_settings = (logger_name, level, prefix)  # Bundled for fast read
    # Complex print function type with default args
    builtins.print = logging_print  # type: ignore[assignment]


def disable_print_capture() -> None:
    """Restore the original print function."""
    # Restore original print function
    builtins.print = _original_print

    # Clear thread-local settings (including bundled tuple)
    for attr in ("print_logger_name", "print_log_level", "print_prefix", "print_settings"):
        if hasattr(_thread_local, attr):
            delattr(_thread_local, attr)


# Type variable for the function to be decorated
F = TypeVar("F", bound=Callable[..., Any])


def capture_print(logger_name: str = "print", level: int = INFO, prefix: str = "[PRINT] ") -> Any:
    """
    Context manager for capturing print statements.

    Args:
        logger_name: Name of the logger to log output to
        level: Logging level to use
        prefix: Prefix to add to logged messages

    Returns:
        Context manager that captures print statements
    """
    # Save original print settings if they exist
    original_logger_name = getattr(_thread_local, "print_logger_name", None)
    original_log_level = getattr(_thread_local, "print_log_level", None)
    original_prefix = getattr(_thread_local, "print_prefix", None)

    # Replace print with our version
    enable_print_capture(logger_name, level, prefix)

    class PrintCapture:
        def __enter__(self) -> "PrintCapture":
            return self

        def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType],
        ) -> Literal[False]:
            # Restore original settings if they existed
            if original_logger_name is not None:
                _thread_local.print_logger_name = original_logger_name
                _thread_local.print_log_level = original_log_level
                _thread_local.print_prefix = original_prefix
            else:
                # Otherwise restore original print
                disable_print_capture()
            return False

    return PrintCapture()


def capture_stdout(
    logger_name: str = "stdout", level: int = INFO, prefix: str = "[STDOUT] "
) -> TextIO:
    """
    Capture all stdout output, not just print statements.

    Args:
        logger_name: Name of the logger to log output to
        level: Logging level to use
        prefix: Prefix to add to logged messages

    Returns:
        Original stdout stream
    """
    # Save original stdout
    original_stdout = sys.stdout

    # Create capture stream
    capture_stream = PrintCaptureStream(
        original_stream=original_stdout,
        logger_name=logger_name,
        level=level,
        prefix=prefix,
    )

    # Replace stdout with capture stream
    sys.stdout = capture_stream

    return original_stdout


def restore_stdout(original_stdout: TextIO) -> None:
    """
    Restore stdout to its original value.

    Args:
        original_stdout: Original stdout stream returned by capture_stdout
    """
    # If current stdout is a PrintCaptureStream, flush it
    if isinstance(sys.stdout, PrintCaptureStream):
        sys.stdout.flush()

    # Restore original stdout
    sys.stdout = original_stdout


# Isolation tracking for print capture
_print_capture_isolation_id = 0
_print_isolation_lock = threading.Lock()


def _get_next_print_isolation_id() -> int:
    """Get the next isolation ID for print capture separation."""
    global _print_capture_isolation_id
    with _print_isolation_lock:
        _print_capture_isolation_id += 1
        return _print_capture_isolation_id


def _initialize_print_isolation() -> None:
    """Initialize print capture isolation for the current thread."""
    if not hasattr(_thread_local, "print_isolation_id"):
        _thread_local.print_isolation_id = _get_next_print_isolation_id()
        _thread_local.print_recursion_flag = False


def _reset_print_capture_if_needed() -> None:
    """Reset print capture state if isolation breach is detected."""
    # Check for excessive recursion (potential state corruption)
    if hasattr(_thread_local, "print_recursion_flag") and _thread_local.print_recursion_flag:
        # Reset if we detect recursive call issues
        _thread_local.print_isolation_id = _get_next_print_isolation_id()
        _thread_local.print_recursion_flag = False
