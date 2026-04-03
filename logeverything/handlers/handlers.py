"""
Handlers for the LogEverything library.

This module provides specialized log handlers for different output formats and destinations.
"""

import datetime
import json
import logging
import os
import threading
import weakref
from typing import IO, Any, Dict, List, Literal, Optional, Set, TextIO, Tuple, Union


# Global adaptive column width management
class AdaptiveColumnManager:
    """
    Global manager for adaptive column widths across all formatters.

    This ensures consistent visual alignment across all loggers regardless of
    their name lengths, while maintaining responsive design that adapts when
    loggers are created or destroyed. Includes smart truncation to prevent
    terminal wrapping issues.
    """

    def __init__(self, max_name_width: int = 30):
        self._lock = threading.Lock()
        self._formatters: weakref.WeakSet = (
            weakref.WeakSet()
        )  # Track all formatters using weak references
        self._max_name_width = 10  # Minimum width for logger names
        self._absolute_max_width = max_name_width  # Maximum width to prevent terminal wrapping
        self._active_loggers: Set[str] = set()  # Track active logger names
        self._truncated_names: Dict[str, str] = {}  # Cache for truncated names

    def register_formatter(self, formatter: Any) -> None:
        """Register a formatter to receive column width updates."""
        with self._lock:
            self._formatters.add(formatter)
            # Set initial width for new formatter
            formatter.column_widths["name"] = min(self._max_name_width, self._absolute_max_width)

    def update_logger_name(self, logger_name: str) -> None:
        """Update the maximum name width if this logger name is longer."""
        # Fast path: name already registered, no lock needed
        if logger_name in self._active_loggers:
            return
        with self._lock:
            self._active_loggers.add(logger_name)
            new_width = len(logger_name)

            # Cap the width at absolute maximum to prevent terminal wrapping
            effective_width = min(new_width, self._absolute_max_width)

            if effective_width > self._max_name_width:
                self._max_name_width = effective_width
                # Update all registered formatters
                for formatter in list(
                    self._formatters
                ):  # Create list to avoid set changed during iteration
                    try:
                        formatter.column_widths["name"] = self._max_name_width
                    except (AttributeError, ReferenceError):
                        # Formatter was garbage collected, weakref will handle cleanup
                        pass

    def get_display_name(self, logger_name: str) -> str:
        """
        Get the display name for a logger, with smart truncation if needed.

        Args:
            logger_name: The original logger name

        Returns:
            The name to display, potentially truncated with ellipsis
        """
        if len(logger_name) <= self._absolute_max_width:
            return logger_name

        # Cache truncated names for performance (bounded to prevent unbounded growth)
        if logger_name not in self._truncated_names:
            if len(self._truncated_names) > 500:
                self._truncated_names.clear()
            # Smart truncation - keep start and end of name
            if self._absolute_max_width > 10:
                keep_start = (self._absolute_max_width - 3) // 2
                keep_end = self._absolute_max_width - 3 - keep_start
                truncated = f"{logger_name[:keep_start]}...{logger_name[-keep_end:]}"
            else:
                # Very short max width - just truncate with ellipsis
                truncated = logger_name[: self._absolute_max_width - 3] + "..."

            self._truncated_names[logger_name] = truncated

        return self._truncated_names[logger_name]

    def remove_logger_name(self, logger_name: str) -> None:
        """
        Remove a logger name and potentially resize if it was the longest.
        Note: This is optional/advanced - for now we'll keep it simple and not shrink.
        """
        with self._lock:
            self._active_loggers.discard(logger_name)
            # Remove from truncated names cache
            self._truncated_names.pop(logger_name, None)
            # For simplicity, we won't shrink the width to avoid visual jumps
            # In a more advanced implementation, we could recalculate max width
            # but this could cause visual instability

    def get_current_name_width(self) -> int:
        """Get the current maximum name width."""
        with self._lock:
            return min(self._max_name_width, self._absolute_max_width)

    def set_max_width(self, max_width: int) -> None:
        """Set the absolute maximum width for logger names."""
        with self._lock:
            self._absolute_max_width = max_width
            # Clear truncated names cache
            self._truncated_names.clear()
            # Update current width if needed
            if self._max_name_width > max_width:
                self._max_name_width = max_width
                # Update all formatters
                for formatter in list(self._formatters):
                    try:
                        formatter.column_widths["name"] = self._max_name_width
                    except (AttributeError, ReferenceError):
                        pass


# Global instance with sensible defaults for typical terminal widths
_adaptive_column_manager = AdaptiveColumnManager(max_name_width=25)


class JSONHandler(logging.Handler):
    """Log handler that outputs logs as JSON objects."""

    # Pre-computed type tuple for isinstance checks (avoids rebuilding per emit call)
    _SERIALIZABLE_TYPES = (str, int, float, bool, list, dict, tuple, type(None))

    def __init__(
        self,
        filename: str,
        mode: str = "a",
        encoding: Optional[str] = None,
        flatten: bool = False,
        indent: Optional[int] = None,
        level: Union[int, str] = logging.NOTSET,
    ):
        """
        Initialize the JSONHandler.

        Args:
            filename: Path to the JSON log file
            mode: File open mode ('a' for append, 'w' for write)
            encoding: File encoding (defaults to 'utf-8')
            flatten: Whether to flatten the output (one JSON object per line)
            indent: JSON indentation level (None for no pretty-printing)
            level: Logging level (default: logging.NOTSET)
        """
        super().__init__()
        self.filename = filename
        self.mode = mode
        # Default to UTF-8 encoding for Unicode compatibility
        self.encoding = encoding or "utf-8"
        self.flatten = flatten
        self.indent = indent
        self.file_handle: Optional[IO[str]] = None

        # Set logging level
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.NOTSET)
        self.setLevel(level)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)

        # Performance optimization: Cache standard LogRecord attributes
        # to avoid repeatedly creating this set in the emit method
        self._standard_attrs: Set[str] = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "lineno",
            "funcName",
            "created",
            "asctime",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
        }

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record as JSON.

        Args:
            record: The log record to emit
        """
        try:
            # Open file if not already open
            if self.file_handle is None:
                self.file_handle = open(self.filename, self.mode, encoding=self.encoding)

            # Extract basic log record data
            log_data: Dict[str, Any] = {
                "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "thread": record.thread,
                "process": record.process,
            }

            # Include correlation ID if present on the record
            cid = getattr(record, "correlation_id", None)
            if not cid:
                # Fallback: read directly from contextvar
                try:
                    from logeverything.correlation import get_correlation_id

                    cid = get_correlation_id()
                except Exception:
                    cid = ""
            if cid:
                log_data["correlation_id"] = cid

            # Promote hierarchy fields to top-level JSON
            log_data["indent_level"] = getattr(record, "indent_level", 0)
            log_data["call_id"] = getattr(record, "call_id", "")
            log_data["parent_call_id"] = getattr(record, "parent_call_id", "")
            log_data["log_type"] = getattr(record, "log_type", "message")
            log_data["execution_id"] = getattr(record, "execution_id", "")

            # Promote structured key-value data to top-level JSON
            structured = getattr(record, "_structured", None)
            if structured:
                log_data.update(structured)

            # Performance optimization: Efficiently extract extra attributes
            # Uses pre-computed _SERIALIZABLE_TYPES to avoid rebuilding tuple per call
            extra: Dict[str, Any] = {}
            for key, value in record.__dict__.items():
                if (
                    key not in self._standard_attrs
                    and not key.startswith("_")
                    and isinstance(value, self._SERIALIZABLE_TYPES)
                ):
                    extra[key] = value

            # If we have extra fields, put them in an "extra" dictionary
            if extra:
                log_data["extra"] = extra

            # Write JSON to file
            if self.flatten:
                # One JSON object per line
                self.file_handle.write(json.dumps(log_data) + "\n")
            else:
                # Pretty-printed JSON
                json.dump(log_data, self.file_handle, indent=self.indent)
                self.file_handle.write(",\n")

            # Performance optimization: Selective flushing
            # Only flush for important log messages to reduce I/O overhead
            if record.levelno >= logging.WARNING:
                self.file_handle.flush()

        except Exception:
            self.handleError(record)

    def close(self) -> None:
        """Close the handler and its file handle."""
        if self.file_handle is not None:
            # Ensure we flush any remaining data before closing
            self.file_handle.flush()
            self.file_handle.close()
            self.file_handle = None
        super().close()


class ConsoleHandler(logging.StreamHandler):
    """Enhanced console handler with color support and formatting."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[95m",  # Magenta
        "RESET": "\033[0m",  # Reset to default
    }

    def __init__(
        self,
        stream: Optional[TextIO] = None,
        use_colors: bool = True,
        color_messages: bool = False,
        level: Union[int, str] = logging.NOTSET,
        colored: Optional[bool] = None,
    ):
        """
        Initialize the ConsoleHandler.

        Args:
            stream: The output stream (default: sys.stderr)
            use_colors: Whether to use ANSI color codes for log level indicators
            color_messages: Whether to apply colors to message text (default: False)
            level: Logging level (default: logging.NOTSET)
            colored: Alias for use_colors, for API compatibility (deprecated)
        """
        super().__init__(stream)
        # Handle colored parameter for backward compatibility
        if colored is not None:
            self.use_colors = colored
        else:
            self.use_colors = use_colors

        # Store message coloring preference
        self.color_messages = color_messages

        # Set logging level
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.NOTSET)
        self.setLevel(level)

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record with optional color formatting.

        Args:
            record: The log record to emit
        """
        try:
            # Apply message coloring if enabled (separate from level indicator coloring)
            if self.color_messages:  # Message coloring is independent of level indicator coloring
                color_code = self.COLORS.get(record.levelname, self.COLORS["RESET"])
                record.msg = f"{color_code}{record.msg}{self.COLORS['RESET']}"

            # Note: Level indicator coloring is handled in _format_level()
            super().emit(record)
        except UnicodeEncodeError:
            # Handle Windows console encoding issues by falling back to ASCII-safe output
            try:
                # Replace Unicode symbols with ASCII alternatives
                ascii_msg = record.msg
                # Replace common Unicode symbols with ASCII equivalents
                ascii_replacements = {
                    "🔍": "[D]",
                    "ℹ️": "[I]",
                    "⚠️": "[W]",
                    "❌": "[E]",
                    "🔥": "[C]",
                    "✅": "[OK]",
                    "🔵": "[CALL]",
                    "💥": "[!]",
                    "┌─►": "+-> ",
                    "└─◄": "+-< ",
                    "├──": "+-- ",
                    "│": "|",
                    "┌─": "+- ",
                    "└─": "+- ",
                    "├─": "+- ",
                    "┴─": "+- ",
                    "┬─": "+- ",
                    "┤": "+",
                    "┼─": "+- ",
                }
                for unicode_char, ascii_char in ascii_replacements.items():
                    ascii_msg = ascii_msg.replace(unicode_char, ascii_char)

                # Replace any remaining non-ASCII characters with '?'
                ascii_msg = ascii_msg.encode("ascii", "replace").decode("ascii")

                # Create a new record with ASCII-safe message
                ascii_record = logging.makeLogRecord(record.__dict__)
                ascii_record.msg = ascii_msg
                ascii_record.getMessage = lambda: ascii_msg

                super().emit(ascii_record)
            except Exception:
                self.handleError(record)
        except Exception:
            self.handleError(record)


class FileHandler(logging.FileHandler):
    """Enhanced file handler with rotation support."""

    def __init__(
        self,
        filename: str,
        mode: str = "a",
        encoding: Optional[str] = "utf-8",  # Default to UTF-8 instead of None
        max_size: Optional[int] = None,
        backup_count: int = 5,
        compress: bool = False,
        level: Union[int, str] = logging.NOTSET,
    ):
        """
        Initialize the FileHandler.

        Args:
            filename: Path to the log file
            mode: File open mode ('a' for append, 'w' for write)
            encoding: File encoding (defaults to 'utf-8' for Unicode compatibility,
                     preventing Windows cp1252 codec errors with visual formatting)
            max_size: Maximum file size in bytes before rotation (None for no rotation)
            backup_count: Number of backup files to keep
            compress: If True, gzip the most recent rotated file in a background thread.
            level: Logging level (default: logging.NOTSET)
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)

        super().__init__(filename, mode, encoding)
        self.max_size = max_size
        self.backup_count = backup_count
        self.compress = compress

        # Set logging level
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.NOTSET)
        self.setLevel(level)

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record with file rotation if needed.

        Args:
            record: The log record to emit
        """
        try:
            # Check file size and rotate if needed
            if self.max_size is not None and self.stream is not None:
                self.stream.flush()
                if os.path.getsize(self.baseFilename) >= self.max_size:
                    self._rotate_files()

            super().emit(record)
        except UnicodeEncodeError:
            # Handle encoding issues by converting to ASCII-safe output
            try:
                # Replace Unicode symbols with ASCII alternatives
                ascii_msg = record.msg
                ascii_replacements = {
                    "🔍": "[D]",
                    "ℹ️": "[I]",
                    "⚠️": "[W]",
                    "❌": "[E]",
                    "🔥": "[C]",
                    "✅": "[OK]",
                    "🔵": "[CALL]",
                    "💥": "[!]",
                    "┌─►": "+-> ",
                    "└─◄": "+-< ",
                    "├──": "+-- ",
                    "│": "|",
                    "┌─": "+- ",
                    "└─": "+- ",
                    "├─": "+- ",
                    "┴─": "+- ",
                    "┬─": "+- ",
                    "┤": "+",
                    "┼─": "+- ",
                }
                for unicode_char, ascii_char in ascii_replacements.items():
                    ascii_msg = ascii_msg.replace(unicode_char, ascii_char)

                # Replace any remaining non-ASCII characters
                ascii_msg = ascii_msg.encode("ascii", "replace").decode("ascii")

                # Create a new record with ASCII-safe message
                ascii_record = logging.makeLogRecord(record.__dict__)
                ascii_record.msg = ascii_msg
                ascii_record.getMessage = lambda: ascii_msg

                super().emit(ascii_record)
            except Exception:
                self.handleError(record)
        except Exception:
            self.handleError(record)

    def _rotate_files(self) -> None:
        """Rotate log files."""
        self.close()

        # Remove the oldest backup file if it exists
        if self.backup_count > 0:
            oldest = f"{self.baseFilename}.{self.backup_count}"
            if os.path.exists(oldest):
                os.remove(oldest)

            # Shift all backup files
            for i in range(self.backup_count - 1, 0, -1):
                source = f"{self.baseFilename}.{i}"
                dest = f"{self.baseFilename}.{i + 1}"
                if os.path.exists(source):
                    os.rename(source, dest)

            # Rename current log file to .1
            os.rename(self.baseFilename, f"{self.baseFilename}.1")

            if self.compress:
                self._compress_file(f"{self.baseFilename}.1")

        # Re-open the file
        self.stream = self._open()

    def _compress_file(self, filepath: str) -> None:
        """Gzip-compress a file in a background daemon thread.

        Args:
            filepath: Path to the file to compress.
        """
        import gzip
        import shutil
        import threading as _threading

        def _do_compress() -> None:
            gz_path = filepath + ".gz"
            try:
                with open(filepath, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                os.remove(filepath)
            except Exception:
                pass  # nosec B110 -- best-effort gzip compression

        t = _threading.Thread(target=_do_compress, daemon=True)
        t.start()


class TimedRotatingFileHandler(FileHandler):
    """File handler with time-based rotation and optional gzip compression.

    Rotates log files at time boundaries (midnight, hourly, or weekly) and
    optionally compresses rotated files with gzip.

    Args:
        filename: Path to the log file.
        when: Rotation interval type -- ``"midnight"``, ``"hourly"``, or ``"weekly"``.
        interval: Multiplier for *when* (currently unused, reserved for future use).
        retention_days: Delete rotated files older than this many days.
        compress: If True, gzip rotated files in a background thread.
        encoding: File encoding.
        level: Logging level.
    """

    WHEN_MAP = {
        "midnight": "%Y-%m-%d",
        "hourly": "%Y-%m-%d-%H",
        "weekly": "%Y-%W",
    }

    def __init__(
        self,
        filename: str,
        when: str = "midnight",
        interval: int = 1,
        retention_days: int = 30,
        compress: bool = False,
        encoding: Optional[str] = "utf-8",
        level: Union[int, str] = logging.NOTSET,
    ):
        if when not in self.WHEN_MAP:
            raise ValueError(
                f"Invalid 'when' value: {when!r}. Must be one of {list(self.WHEN_MAP.keys())}"
            )
        super().__init__(filename, encoding=encoding, level=level)
        self._when = when
        self._interval = interval
        self._retention_days = retention_days
        self._compress = compress
        self._date_fmt = self.WHEN_MAP[when]
        self._rollover_at = self._compute_next_rollover()

    def _compute_next_rollover(self) -> "datetime.datetime":
        """Compute the next rollover time based on the rotation interval.

        Returns:
            A ``datetime.datetime`` representing the next rollover boundary.
        """
        import datetime as _dt

        now = _dt.datetime.now()
        if self._when == "midnight":
            tomorrow = now.date() + _dt.timedelta(days=1)
            return _dt.datetime.combine(tomorrow, _dt.time.min)
        elif self._when == "hourly":
            return now.replace(minute=0, second=0, microsecond=0) + _dt.timedelta(hours=1)
        else:  # weekly
            days_until_monday = (7 - now.weekday()) % 7 or 7
            next_monday = now.date() + _dt.timedelta(days=days_until_monday)
            return _dt.datetime.combine(next_monday, _dt.time.min)

    def shouldRollover(self, record: logging.LogRecord) -> bool:
        """Check whether the current record should trigger a rollover.

        Args:
            record: The log record being emitted.

        Returns:
            True if a rollover is due.
        """
        import datetime as _dt

        return _dt.datetime.now() >= self._rollover_at

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record, performing a rollover first if one is due.

        Args:
            record: The log record to emit.
        """
        if self.shouldRollover(record):
            self.doRollover()
        super().emit(record)

    def doRollover(self) -> None:
        """Perform the file rollover, compressing and cleaning up as configured."""
        import datetime as _dt

        if self.stream:
            self.stream.close()
            self.stream = None

        suffix = _dt.datetime.now().strftime(self._date_fmt)
        rotated = f"{self.baseFilename}.{suffix}"

        # Avoid overwriting an existing rotated file
        if os.path.exists(rotated):
            idx = 1
            while os.path.exists(f"{rotated}.{idx}"):
                idx += 1
            rotated = f"{rotated}.{idx}"

        if os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, rotated)

        self.stream = self._open()
        self._rollover_at = self._compute_next_rollover()

        if self._compress:
            self._compress_file(rotated)
        self._cleanup_old_files()

    def _cleanup_old_files(self) -> None:
        """Delete rotated files older than ``retention_days``."""
        import datetime as _dt
        import glob as _glob

        cutoff = _dt.datetime.now() - _dt.timedelta(days=self._retention_days)
        pattern = f"{self.baseFilename}.*"
        for path in _glob.glob(pattern):
            try:
                mtime = _dt.datetime.fromtimestamp(os.path.getmtime(path))
                if mtime < cutoff:
                    os.remove(path)
            except Exception:
                pass  # nosec B110 -- best-effort cleanup of old files


class PrettyFormatter(logging.Formatter):
    """
    Enhanced formatter that creates visually appealing logs with Unicode symbols.

    Default format string - pipe encapsulation handles level width consistently.
    """

    DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    DEFAULT_DATE_FORMAT = (
        "%Y-%m-%d %H:%M:%S"  # Unicode symbols for logging levels with consistent spacing
    )
    LEVEL_SYMBOLS = {
        "DEBUG": "🔍",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🔥",
        "EXCEPTION": "💥",
    }

    # Monospace alternative symbols for perfect alignment
    LEVEL_SYMBOLS_MONOSPACE = {
        "DEBUG": "[D]",
        "INFO": "[I]",
        "WARNING": "[W]",
        "ERROR": "[E]",
        "CRITICAL": "[C]",
        "EXCEPTION": "[X]",
    }

    # Unicode box drawing characters for hierarchical visualization
    INDENT_CHAR = "│"
    ENTRY_CHAR = "┌─►"
    EXIT_CHAR = "└─◄"
    CONTINUE_CHAR = "├──"

    # Tree structure characters for improved hierarchy
    TREE_BRANCH = "├─"
    TREE_LAST_BRANCH = "└─"
    TREE_VERTICAL = "│ "
    TREE_SPACE = "  "
    TREE_INDENT = "  "
    # Compact mode settings
    COMPACT_THRESHOLD = 5  # Start compact mode after this depth
    COMPACT_SYMBOL = "⋯"

    # ANSI color codes (for console output only)
    COLORS = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[95m",  # Magenta
        "RESET": "\033[0m",  # Reset
        "BOLD": "\033[1m",  # Bold
        "UNDERLINE": "\033[4m",  # Underline
    }

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: Literal["%", "{", "$"] = "%",
        use_colors: bool = False,
        color_messages: bool = False,
        use_symbols: bool = True,
        use_monospace_symbols: bool = False,
        use_indent: bool = True,
        align_columns: bool = True,
        column_widths: Optional[Dict[str, int]] = None,
        compact_mode: bool = True,
        compact_threshold: int = 5,
    ):
        """
        Initialize the PrettyFormatter.

        Args:
            fmt: Format string (default: class default format)
            datefmt: Date format string (default: class default date format)
            style: Format string style ('%', '{', or '$')
            use_colors: Whether to use ANSI color codes
            use_symbols: Whether to use Unicode symbols for log levels
            use_monospace_symbols: Whether to use monospace symbols for perfect alignment
            use_indent: Whether to use indent visualization
            align_columns: Whether to align columns
            column_widths: Custom column widths for alignment
            compact_mode: Whether to use compact mode for deep hierarchies
            compact_threshold: Depth at which to start compact mode
        """
        fmt = fmt or self.DEFAULT_FORMAT
        datefmt = datefmt or self.DEFAULT_DATE_FORMAT

        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

        self.use_colors = use_colors
        self.color_messages = color_messages
        self.use_symbols = use_symbols
        self.use_indent = use_indent
        self.align_columns = align_columns
        self.compact_mode = compact_mode
        self.compact_threshold = compact_threshold

        # Enhanced column widths for better alignment with adaptive name width
        self.column_widths = {
            "timestamp": 20,  # Length of formatted datetime
            "level": 14,  # Fixed width for level names with pipe encapsulation: | 🔥 | CRITICAL
            "name": _adaptive_column_manager.get_current_name_width(),
            "message": 0,  # No fixed width for message
        }

        # Override with custom column widths
        if column_widths:
            self.column_widths.update(column_widths)

        # Register this formatter with the adaptive column manager
        _adaptive_column_manager.register_formatter(self)

        # Track indentation state for hierarchical visualization
        self._indent_levels: Dict[str, int] = {}
        self._call_stack: Dict[str, List[int]] = {}  # Track function call stack for tree structure

        # Cache display names to avoid repeated get_display_name() calls
        self._display_name_cache: Dict[str, str] = {}

        # Time formatting cache: (integer_second, formatted_string)
        self._cached_time: Optional[Tuple[int, str]] = None

    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        """Cache-optimized formatTime — same-second records reuse the formatted string.

        Args:
            record: The log record
            datefmt: Optional date format string

        Returns:
            Formatted time string
        """
        ct_int = int(record.created)
        cached = self._cached_time
        if cached is not None and cached[0] == ct_int:
            return cached[1]
        result = super().formatTime(record, datefmt)
        self._cached_time = (ct_int, result)
        return result

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with enhanced hierarchical visual elements.

        Modifies the record in-place and restores original values after formatting
        to avoid the overhead of makeLogRecord(record.__dict__) copy.

        Args:
            record: The log record to format

        Returns:
            Formatted log record string with improved tree structure
        """
        # Save original values for in-place restore (avoids full dict copy)
        orig_msg = record.msg
        orig_name = record.name
        orig_levelname = record.levelname

        try:
            # Process the message to extract hierarchical information
            original_msg = str(record.msg) if hasattr(record, "msg") else record.getMessage()
            message = original_msg
            logger_name = record.name

            # Use cached display name to avoid repeated lock acquisition and lookups
            if logger_name not in self._display_name_cache:
                _adaptive_column_manager.update_logger_name(logger_name)
                self._display_name_cache[logger_name] = _adaptive_column_manager.get_display_name(
                    logger_name
                )
            record.name = self._display_name_cache[logger_name]

            # Extract function entry/exit markers if present
            is_entry = False
            is_exit = False
            if message.startswith("→ "):
                is_entry = True
                message = message[2:].strip()
            elif message.startswith("← "):
                is_exit = True
                message = message[2:].strip()

            # Get current indent level and update tracking
            indent_level = self._update_indent_level(message, logger_name, is_entry, is_exit)

            # Format the level name with symbol and proper width
            record.levelname = self._format_level(orig_levelname)

            # Apply hierarchical indentation to the message
            if self.use_indent and indent_level > 0:
                tree_prefix = self._build_tree_prefix(logger_name, indent_level, is_entry, is_exit)
                record.msg = f"{tree_prefix}{message}"
            else:
                record.msg = message

            # Use the parent class to format with our modified record
            formatted = super().format(record)

            # Append correlation ID tag when active
            cid = getattr(record, "correlation_id", None)
            if not cid:
                try:
                    from logeverything.correlation import get_correlation_id

                    cid = get_correlation_id()
                except Exception:
                    cid = ""
            if cid:
                formatted += f" [req:{cid[:8]}]"

            # Append structured key-value data if present
            structured = getattr(record, "_structured", None)
            if structured:
                pairs = " ".join(f"{k}={v!r}" for k, v in structured.items())
                formatted += f" | {pairs}"

            # Apply column alignment if configured
            if self.align_columns:
                formatted = self._align_columns(formatted)

            return formatted
        finally:
            # Restore original record values
            record.msg = orig_msg
            record.name = orig_name
            record.levelname = orig_levelname

    def _format_level(self, levelname: str) -> str:
        """
        Format the log level with symbol and proper width for alignment.

        Args:
            levelname: The level name to format

        Returns:
            Formatted level string with fixed width
        """  # Use single pipe encapsulation with fixed width for consistent alignment
        if self.use_symbols:
            symbol = self.LEVEL_SYMBOLS.get(levelname, " ")
            # Use a fixed format approach to ensure consistent bracket alignment
            # Each level gets exactly the same total character count
            if levelname == "DEBUG":
                formatted_level = f"[ {symbol} {levelname}  ]"
            elif levelname == "INFO":
                formatted_level = f"[  {symbol} {levelname}  ]"
            elif levelname == "WARNING":
                formatted_level = f"[{symbol} {levelname} ]"  # Adjusted spacing for ⚠️ emoji
            elif levelname == "ERROR":
                formatted_level = f"[ {symbol} {levelname}  ]"
            elif levelname == "CRITICAL":
                formatted_level = f"[{symbol} {levelname}]"
            else:
                # Fallback for any other level names
                content = f"{symbol} {levelname}"
                formatted_level = f"[{content:^12}]"
        else:
            # Even without symbols, center the level name for consistency
            formatted_level = f"[ {levelname:^8} ]"  # Center level name in 8 chars

        # Apply colors if configured
        if self.use_colors:
            color = self.COLORS.get(levelname, self.COLORS["RESET"])
            return f"{color}{formatted_level}{self.COLORS['RESET']}"
        else:
            return formatted_level

    def _update_indent_level(
        self, message: str, logger_name: str, is_entry: bool, is_exit: bool
    ) -> int:
        """
        Update and return the current indentation level for hierarchical display.

        Args:
            message: The log message
            logger_name: The logger name (used to track indentation state)
            is_entry: Whether this is a function entry
            is_exit: Whether this is a function exit

        Returns:
            The current indentation level
        """
        # Initialize tracking for this logger if needed
        if logger_name not in self._indent_levels:
            self._indent_levels[logger_name] = 0
        if logger_name not in self._call_stack:
            self._call_stack[logger_name] = []

        current_level = self._indent_levels[logger_name]

        if is_entry:
            # Function entry: record current level, then increment for future calls
            self._call_stack[logger_name].append(current_level)
            self._indent_levels[logger_name] += 1
            return current_level
        elif is_exit:
            # Function exit: restore previous level
            if self._call_stack[logger_name]:
                level = self._call_stack[logger_name].pop()
                self._indent_levels[logger_name] = max(0, len(self._call_stack[logger_name]))
                return level
            else:
                self._indent_levels[logger_name] = max(0, self._indent_levels[logger_name] - 1)
                return self._indent_levels[logger_name]
        else:
            # Regular message: use current level
            return current_level

    def _build_tree_prefix(
        self, logger_name: str, indent_level: int, is_entry: bool, is_exit: bool
    ) -> str:
        """
        Build the tree structure prefix for hierarchical display.

        Args:
            logger_name: The logger name
            indent_level: Current indentation level
            is_entry: Whether this is a function entry
            is_exit: Whether this is a function exit

        Returns:
            Tree structure prefix string
        """
        if indent_level == 0:
            return ""

        # Use compact mode for deep hierarchies
        if self.compact_mode and indent_level >= self.compact_threshold:
            compact_info = f"{self.COMPACT_SYMBOL}[{indent_level}] "
            if is_entry:
                return f"{compact_info}{self.ENTRY_CHAR} "
            elif is_exit:
                return f"{compact_info}{self.EXIT_CHAR} "
            else:
                return f"{compact_info}"

        # Build full tree structure
        prefix_parts = []
        call_stack = self._call_stack.get(logger_name, [])

        # For each level, determine if we need vertical line or space
        for level in range(indent_level):
            if level < len(call_stack) or level < indent_level - 1:
                # Not the last level, use vertical line
                prefix_parts.append(self.TREE_VERTICAL)
            else:
                # Last level, use appropriate connector
                if is_entry:
                    prefix_parts.append(self.ENTRY_CHAR + " ")
                elif is_exit:
                    prefix_parts.append(self.EXIT_CHAR + " ")
                else:
                    prefix_parts.append(self.TREE_BRANCH + " ")

        return "".join(prefix_parts)

    def _align_columns(self, formatted: str) -> str:
        """
        Align columns in the formatted string for better readability.
        Uses fixed-width columns to ensure proper alignment regardless of content length.
        This is crucial for keeping vertical tree lines straight!

        Args:
            formatted: The formatted log string

        Returns:
            A string with aligned columns
        """
        # Only attempt alignment if we have pipe separators
        if "|" not in formatted:
            return formatted

        try:
            # Split by pipe separator
            parts = formatted.split("|")

            # Apply fixed width to each column except the last one (message)
            aligned_parts = []
            for i, part in enumerate(parts):
                if i == 0 and self.column_widths["timestamp"] > 0:
                    # Timestamp column - left aligned
                    aligned_parts.append(part.ljust(self.column_widths["timestamp"]))
                elif i == 1:
                    # Level column - skip alignment since bracket encapsulation
                    # already provides consistency
                    aligned_parts.append(part)
                elif i == 2 and self.column_widths["name"] > 0:
                    # Logger name column - left aligned
                    # Strip whitespace, pad to fixed width, then add single space padding
                    name_part = part.strip()
                    padded_name = name_part.ljust(self.column_widths["name"])
                    aligned_parts.append(f" {padded_name} ")
                else:
                    # Message column - no fixed width, but preserve spacing
                    aligned_parts.append(part)

            # Rejoin with pipe separators
            return "|".join(aligned_parts)
        except Exception:
            # If anything goes wrong, return the original
            return formatted

    def _strip_ansi_codes(self, text: str) -> str:
        """
        Remove ANSI color codes from text for accurate width calculation.

        Args:
            text: Text that may contain ANSI codes

        Returns:
            Text with ANSI codes removed
        """
        import re

        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)

    def _calculate_display_width(self, text: str) -> int:
        """
        Calculate the actual display width of text, accounting for emojis.

        Args:
            text: Text that may contain emojis and ANSI codes

        Returns:
            Approximate display width
        """
        # Remove ANSI codes first
        clean_text = self._strip_ansi_codes(text)

        # More accurate emoji detection and width calculation
        display_width = 0
        for char in clean_text:
            char_code = ord(char)
            # Check if character is an emoji (more comprehensive range)
            if (
                0x1F600 <= char_code <= 0x1F64F
                or 0x1F300 <= char_code <= 0x1F5FF  # Emoticons
                or 0x1F680 <= char_code <= 0x1F6FF  # Misc Symbols
                or 0x1F700 <= char_code <= 0x1F77F  # Transport
                or 0x1F780 <= char_code <= 0x1F7FF  # Alchemical Symbols
                or 0x1F800 <= char_code <= 0x1F8FF  # Geometric Shapes Extended
                or 0x2600 <= char_code <= 0x26FF  # Supplemental Arrows-C
                or 0x2700 <= char_code <= 0x27BF  # Misc symbols
                or char_code == 0x200D  # Dingbats
            ):  # Zero Width Joiner
                display_width += 2  # Emojis typically take 2 terminal columns
            else:
                display_width += 1  # Regular characters take 1 column

        return display_width


class JSONLineFormatter(logging.Formatter):
    """Formatter that outputs each log record as a single JSON object.

    Attach this to any handler (including rotation handlers) to produce
    dashboard-compatible JSON Lines output.  The field layout matches
    :class:`JSONHandler` so the dashboard can read the files directly.

    Args:
        include_extras: Include extra record attributes in an ``extra`` dict.
        source: Optional service/source tag written into every record.
    """

    # Pre-computed type tuple for isinstance checks (avoids rebuilding per format call)
    _SERIALIZABLE_TYPES = (str, int, float, bool, list, dict, tuple, type(None))

    _STANDARD_ATTRS: Set[str] = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "lineno",
        "funcName",
        "created",
        "asctime",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
    }

    _HIERARCHY_ATTRS: Set[str] = {
        "indent_level",
        "call_id",
        "parent_call_id",
        "log_type",
        "execution_id",
    }

    def __init__(
        self,
        include_extras: bool = True,
        source: Optional[str] = None,
    ):
        super().__init__()
        self.include_extras = include_extras
        self.source = source

    def format(self, record: logging.LogRecord) -> str:
        """Return a JSON string for *record* (no trailing newline).

        The handler is responsible for appending the line terminator.
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "thread": record.thread,
            "process": record.process,
        }

        # Correlation ID
        cid = getattr(record, "correlation_id", None)
        if not cid:
            try:
                from logeverything.correlation import get_correlation_id

                cid = get_correlation_id()
            except Exception:
                cid = ""
        if cid:
            log_data["correlation_id"] = cid

        # Hierarchy fields
        log_data["indent_level"] = getattr(record, "indent_level", 0)
        log_data["call_id"] = getattr(record, "call_id", "")
        log_data["parent_call_id"] = getattr(record, "parent_call_id", "")
        log_data["log_type"] = getattr(record, "log_type", "message")
        log_data["execution_id"] = getattr(record, "execution_id", "")

        # Source tag
        if self.source:
            log_data["source"] = self.source

        # Structured key-value data
        structured = getattr(record, "_structured", None)
        if structured:
            log_data.update(structured)

        # Extra attributes (uses pre-computed _SERIALIZABLE_TYPES)
        if self.include_extras:
            extra: Dict[str, Any] = {}
            skip = self._STANDARD_ATTRS | self._HIERARCHY_ATTRS
            for key, value in record.__dict__.items():
                if (
                    key not in skip
                    and not key.startswith("_")
                    and isinstance(value, self._SERIALIZABLE_TYPES)
                ):
                    extra[key] = value
            if extra:
                log_data["extra"] = extra

        return json.dumps(log_data)


class FormattedFileHandler(FileHandler):
    """File handler with enhanced formatting for improved readability."""

    def __init__(
        self,
        filename: str,
        mode: str = "a",
        encoding: Optional[str] = "utf-8",  # Default to UTF-8 for Unicode symbols
        pretty: bool = True,
        use_symbols: bool = True,
        use_indent: bool = True,
        align_columns: bool = True,
        compact_mode: bool = True,
        compact_threshold: int = 5,
        level: Union[int, str] = logging.NOTSET,
        max_size: Optional[int] = None,
        backup_count: int = 5,
    ):
        """
        Initialize the FormattedFileHandler.

        Args:
            filename: Path to the log file
            mode: File open mode ('a' for append, 'w' for write)
            encoding: File encoding (default: utf-8 for Unicode support)
            pretty: Whether to use enhanced formatting
            use_symbols: Whether to use Unicode symbols for log levels
            use_indent: Whether to use indent visualization
            align_columns: Whether to align columns
            compact_mode: Whether to use compact mode for deep hierarchies
            compact_threshold: Depth at which to start compact mode
            level: Logging level
            max_size: Maximum file size in bytes before rotation (None for no rotation)
            backup_count: Number of backup files to keep
        """
        # Create directory if it doesn't exist (before the super call)
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)

        # Call the parent constructor
        super().__init__(
            filename=filename,
            mode=mode,
            encoding=encoding,
            level=level,  # Pass encoding to parent
        )

        # Store the max size and backup count for rotation
        self.max_size = max_size
        self.backup_count = backup_count  # Set up the formatter
        if pretty:
            self.setFormatter(
                PrettyFormatter(
                    use_colors=False,  # No colors in files
                    use_symbols=use_symbols,
                    use_indent=use_indent,
                    align_columns=align_columns,
                    compact_mode=compact_mode,
                    compact_threshold=compact_threshold,
                )
            )
        else:
            # Use standard formatter
            self.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record with file rotation if needed.

        Args:
            record: The log record to emit
        """
        try:
            # Check file size and rotate if needed
            if self.max_size is not None and self.stream is not None:
                self.stream.flush()
                if (
                    os.path.exists(self.baseFilename)
                    and os.path.getsize(self.baseFilename) >= self.max_size
                ):
                    self._rotate_files()

            # Call the parent emit method
            super().emit(record)

            # Flush after each record to ensure it's written
            if self.stream:
                self.stream.flush()

        except Exception:
            self.handleError(record)


class EnhancedConsoleHandler(ConsoleHandler):
    """Console handler with enhanced formatting and color options."""

    def __init__(
        self,
        stream: Optional[TextIO] = None,
        use_colors: bool = True,
        color_messages: bool = False,
        use_symbols: bool = True,
        use_indent: bool = True,
        align_columns: bool = True,
        color_theme: str = "default",
        ascii_only: bool = False,
        level: Union[int, str] = logging.NOTSET,
    ):
        """
        Initialize the EnhancedConsoleHandler.

        Args:
            stream: Output stream
            use_colors: Whether to use colors for level indicators
            color_messages: Whether to apply colors to message text (default: False)
            use_symbols: Whether to use Unicode symbols
            use_indent: Whether to use indent visualization
            align_columns: Whether to align columns
            color_theme: Color theme name ('default', 'pastel', 'bold', 'monochrome')
            ascii_only: Whether to use only ASCII characters (no Unicode)
            level: Logging level
        """
        super().__init__(
            stream=stream, use_colors=False, color_messages=color_messages, level=level
        )

        # Custom color themes
        themes = {
            "default": {
                "DEBUG": "\033[94m",  # Blue
                "INFO": "\033[92m",  # Green
                "WARNING": "\033[93m",  # Yellow
                "ERROR": "\033[91m",  # Red
                "CRITICAL": "\033[95m",  # Magenta
                "RESET": "\033[0m",  # Reset
            },
            "pastel": {
                "DEBUG": "\033[38;5;111m",  # Light blue
                "INFO": "\033[38;5;121m",  # Light green
                "WARNING": "\033[38;5;221m",  # Light yellow
                "ERROR": "\033[38;5;217m",  # Light red
                "CRITICAL": "\033[38;5;219m",  # Light magenta
                "RESET": "\033[0m",
            },
            "bold": {
                "DEBUG": "\033[1;34m",  # Bold blue
                "INFO": "\033[1;32m",  # Bold green
                "WARNING": "\033[1;33m",  # Bold yellow
                "ERROR": "\033[1;31m",  # Bold red
                "CRITICAL": "\033[1;35m",  # Bold magenta
                "RESET": "\033[0m",
            },
            "monochrome": {
                "DEBUG": "\033[37m",  # White
                "INFO": "\033[1m",  # Bold
                "WARNING": "\033[1;37m",  # Bold white
                "ERROR": "\033[7m",  # Reverse
                "CRITICAL": "\033[1;7m",  # Bold reverse
                "RESET": "\033[0m",
            },
        }

        # Set up the formatter
        formatter = PrettyFormatter(
            use_colors=use_colors,
            color_messages=color_messages,
            use_symbols=use_symbols and not ascii_only,  # Disable symbols if ASCII only
            use_indent=use_indent,
            align_columns=align_columns,
        )

        # Use the selected color theme
        if color_theme in themes:
            formatter.COLORS = themes[color_theme]

        # If ASCII only, override the indent characters
        if ascii_only:
            formatter.INDENT_CHAR = "|"
            formatter.ENTRY_CHAR = "+-> "
            formatter.EXIT_CHAR = "+-< "
            formatter.CONTINUE_CHAR = "+-- "

            # Replace Unicode symbols with ASCII ones
            formatter.LEVEL_SYMBOLS = {
                "DEBUG": "[D]",
                "INFO": "[I]",
                "WARNING": "[W]",
                "ERROR": "[E]",
                "CRITICAL": "[C]",
                "EXCEPTION": "[!]",
            }

        self.setFormatter(formatter)


# Export functions for adaptive column management
def get_adaptive_column_manager() -> AdaptiveColumnManager:
    """Get the global adaptive column manager instance."""
    return _adaptive_column_manager


def register_logger_name(name: str) -> None:
    """
    Register a logger name with the adaptive column manager.

    This is a convenience function for external code to register logger names
    without having to import the manager directly.
    """
    _adaptive_column_manager.update_logger_name(name)


def get_current_name_column_width() -> int:
    """Get the current adaptive name column width."""
    return _adaptive_column_manager.get_current_name_width()


def set_max_logger_name_width(max_width: int) -> None:
    """
    Set the maximum width for logger names to prevent terminal wrapping.

    Names longer than this will be truncated with smart ellipsis.

    Args:
        max_width: Maximum character width for logger names
    """
    _adaptive_column_manager.set_max_width(max_width)


def get_display_name(logger_name: str) -> str:
    """
    Get the display version of a logger name (potentially truncated).

    Args:
        logger_name: The original logger name

    Returns:
        The display name with smart truncation if needed
    """
    return _adaptive_column_manager.get_display_name(logger_name)
