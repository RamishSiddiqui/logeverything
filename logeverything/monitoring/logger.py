"""
Structured Logging for LogEverything Monitoring

Provides structured, JSON-formatted logging with automatic correlation IDs,
performance tracking, and integration with the monitoring system.
"""

import json
import threading
import time
import traceback
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from logeverything.correlation import _correlation_id as correlation_id

# Context variable for operation tracking (local to monitoring)
operation_context: ContextVar[Dict[str, Any]] = ContextVar("operation_context", default={})


class StructuredLogger:
    """
    High-performance structured logger with JSON output format.

    Features:
    - Structured JSON logging
    - Automatic correlation IDs
    - Performance tracking
    - Thread-safe operations
    - Automatic log rotation
    """

    def __init__(self, name: str, storage=None, max_files: int = 100, max_size_mb: int = 50):
        self.name = name
        self.storage = storage
        self.max_files = max_files
        self.max_size_mb = max_size_mb
        self._lock = threading.Lock()

        # Current log file tracking
        self._current_log_file = None
        self._current_file_size = 0
        self._log_counter = 0

        # Initialize first log file
        self._initialize_log_file()

    def _initialize_log_file(self):
        """Initialize a new log file."""
        if not self.storage:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"app_logs_{timestamp}_{self._log_counter:04d}.jsonl"
        self._current_log_file = self.storage.logs_dir / log_filename
        self._current_file_size = 0

        # Create initial log entry
        self._write_log_entry(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "logger": self.name,
                "message": "Log file initialized",
                "log_file": str(self._current_log_file),
                "session_info": {
                    "pid": __import__("os").getpid(),
                    "thread_id": threading.get_ident(),
                },
            }
        )

    def _should_rotate_log(self) -> bool:
        """Check if log file should be rotated."""
        if not self._current_log_file:
            return False

        max_size_bytes = self.max_size_mb * 1024 * 1024
        return self._current_file_size >= max_size_bytes

    def _rotate_log_file(self):
        """Rotate to a new log file."""
        self._log_counter += 1

        # Clean up old files if needed
        if self.storage:
            self.storage.cleanup_old_logs(self.max_files)

        self._initialize_log_file()

    def _write_log_entry(self, entry: Dict[str, Any]):
        """Write a log entry to the current file."""
        if not self._current_log_file:
            return

        try:
            json_line = json.dumps(entry, ensure_ascii=False) + "\\n"

            with open(self._current_log_file, "a", encoding="utf-8") as f:
                f.write(json_line)
                f.flush()

            self._current_file_size += len(json_line.encode("utf-8"))

            # Check for rotation
            if self._should_rotate_log():
                self._rotate_log_file()

        except Exception as e:
            # Fallback to stderr if file writing fails
            print(f"Failed to write log entry: {e}", file=__import__("sys").stderr)

    def _create_log_entry(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None,
    ) -> Dict[str, Any]:
        """Create a structured log entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "logger": self.name,
            "message": message,
            "correlation_id": correlation_id.get(""),
            "thread_id": threading.get_ident(),
            "process_id": __import__("os").getpid(),
        }

        # Add operation context
        ctx = operation_context.get({})
        if ctx:
            entry["operation"] = ctx

        # Add extra fields
        if extra:
            entry.update(extra)

        # Add exception info
        if exc_info:
            entry["exception"] = {
                "type": type(exc_info).__name__,
                "message": str(exc_info),
                "traceback": traceback.format_exc(),
            }

        return entry

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log a debug message."""
        with self._lock:
            entry = self._create_log_entry("DEBUG", message, extra)
            self._write_log_entry(entry)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log an info message."""
        with self._lock:
            entry = self._create_log_entry("INFO", message, extra)
            self._write_log_entry(entry)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log a warning message."""
        with self._lock:
            entry = self._create_log_entry("WARNING", message, extra)
            self._write_log_entry(entry)

    def error(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None,
    ):
        """Log an error message."""
        with self._lock:
            entry = self._create_log_entry("ERROR", message, extra, exc_info)
            self._write_log_entry(entry)

    def critical(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None,
    ):
        """Log a critical message."""
        with self._lock:
            entry = self._create_log_entry("CRITICAL", message, extra, exc_info)
            self._write_log_entry(entry)

    def operation_start(self, operation_name: str, **kwargs) -> str:
        """Start tracking an operation."""
        op_id = str(uuid.uuid4())

        # Set context
        correlation_id.set(op_id)
        operation_context.set(
            {
                "operation_id": op_id,
                "operation_name": operation_name,
                "start_time": time.time(),
                **kwargs,
            }
        )

        self.info(
            f"Operation started: {operation_name}",
            extra={
                "operation_id": op_id,
                "operation_name": operation_name,
                "operation_status": "started",
                **kwargs,
            },
        )

        return op_id

    def operation_end(self, operation_id: str, success: bool = True, **kwargs):
        """End tracking an operation."""
        ctx = operation_context.get({})
        start_time = ctx.get("start_time", time.time())
        duration = time.time() - start_time

        status = "success" if success else "failed"
        operation_name = ctx.get("operation_name", "unknown")

        self.info(
            f"Operation ended: {operation_name}",
            extra={
                "operation_id": operation_id,
                "operation_name": operation_name,
                "operation_status": status,
                "duration_seconds": duration,
                **kwargs,
            },
        )

        # Clear context
        correlation_id.set("")
        operation_context.set({})


def set_correlation_context(corr_id: str, context: Optional[Dict[str, Any]] = None):
    """Set correlation ID and context for current thread."""
    correlation_id.set(corr_id)
    if context:
        operation_context.set(context)


class OperationTracker:
    """Context manager for tracking operations."""

    def __init__(self, logger: StructuredLogger, operation_name: str, **kwargs):
        self.logger = logger
        self.operation_name = operation_name
        self.kwargs = kwargs
        self.operation_id = None

    def __enter__(self):
        self.operation_id = self.logger.operation_start(self.operation_name, **self.kwargs)
        return self.operation_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        success = exc_type is None

        if exc_val:
            self.logger.error(
                f"Operation failed: {self.operation_name}",
                extra={"operation_id": self.operation_id},
                exc_info=exc_val,
            )

        self.logger.operation_end(self.operation_id, success=success)
