"""
LogEverything - A comprehensive logging library for Python applications.

This library allows you to add detailed logging to your Python code with minimal changes
to your existing codebase. It provides function entry/exit logging, I/O call logging,
print statement capturing, and more, all in a beautifully formatted and easy-to-follow way.

It also supports async-compatible logging for asyncio applications.
"""

from typing import Any

# Eager imports: always needed core functionality
from . import core as core_module
from .decorators import log, log_class, log_function, log_io
from .logger import Logger
from .utils import CRITICAL, DEBUG, ERROR, FATAL, INFO, WARN, WARNING  # noqa: F401

__version__ = "0.5.0"

# Re-export core functions
get_logger = core_module.get_logger

# Lazy import mapping: module_path -> list of (attribute_name, module_attr_name)
_LAZY_IMPORTS = {
    "AsyncLogger": (".asyncio.async_logger", "AsyncLogger"),
    "AsyncLoggingContext": (".asyncio.async_logging", "AsyncLoggingContext"),
    "AsyncQueueHandler": (".asyncio.async_logging", "AsyncQueueHandler"),
    "AsyncQuietLoggingContext": (".asyncio.async_logging", "AsyncQuietLoggingContext"),
    "AsyncTemporaryHandlerContext": (".asyncio.async_logging", "AsyncTemporaryHandlerContext"),
    "AsyncVerboseLoggingContext": (".asyncio.async_logging", "AsyncVerboseLoggingContext"),
    "AsyncVisualLoggingContext": (".asyncio.async_logging", "AsyncVisualLoggingContext"),
    "async_log_class": (".asyncio.async_logging", "async_log_class"),
    "async_log_function": (".asyncio.async_logging", "async_log_function"),
    "log_async_class": (".asyncio.async_logging", "log_async_class"),
    "log_async_function": (".asyncio.async_logging", "log_async_function"),
    "BaseLogger": (".base", "BaseLogger"),
    "capture_print": (".capture.print_capture", "capture_print"),
    "capture_stdout": (".capture.print_capture", "capture_stdout"),
    "disable_print_capture": (".capture.print_capture", "disable_print_capture"),
    "enable_print_capture": (".capture.print_capture", "enable_print_capture"),
    "restore_stdout": (".capture.print_capture", "restore_stdout"),
    "LoggingContext": (".contexts.contexts", "LoggingContext"),
    "QuietLoggingContext": (".contexts.contexts", "QuietLoggingContext"),
    "TemporaryHandlerContext": (".contexts.contexts", "TemporaryHandlerContext"),
    "VerboseLoggingContext": (".contexts.contexts", "VerboseLoggingContext"),
    "VisualLoggingContext": (".contexts.contexts", "VisualLoggingContext"),
    "configure_common_loggers": (".external.external", "configure_common_loggers"),
    "configure_external_logger": (".external.external", "configure_external_logger"),
    "harmonize_logger_levels": (".external.external", "harmonize_logger_levels"),
    "intercept_stdlib": (".external.external", "intercept_stdlib"),
    "restore_stdlib": (".external.external", "restore_stdlib"),
    "ConsoleHandler": (".handlers.handlers", "ConsoleHandler"),
    "EnhancedConsoleHandler": (".handlers.handlers", "EnhancedConsoleHandler"),
    "FileHandler": (".handlers.handlers", "FileHandler"),
    "FormattedFileHandler": (".handlers.handlers", "FormattedFileHandler"),
    "JSONHandler": (".handlers.handlers", "JSONHandler"),
    "JSONLineFormatter": (".handlers.handlers", "JSONLineFormatter"),
    "PrettyFormatter": (".handlers.handlers", "PrettyFormatter"),
    "TimedRotatingFileHandler": (".handlers.handlers", "TimedRotatingFileHandler"),
    "PROFILES": (".profiles.profiles", "PROFILES"),
    "get_profile": (".profiles.profiles", "get_profile"),
    # Correlation
    "set_correlation_id": (".correlation", "set_correlation_id"),
    "get_correlation_id": (".correlation", "get_correlation_id"),
    "set_request_context": (".correlation", "set_request_context"),
    "get_request_context": (".correlation", "get_request_context"),
    "clear_correlation": (".correlation", "clear_correlation"),
    "CorrelationFilter": (".correlation", "CorrelationFilter"),
    "propagate_context": (".correlation", "propagate_context"),
    # Hierarchy
    "HierarchyFilter": (".hierarchy", "HierarchyFilter"),
    # Transport
    "HTTPTransportHandler": (".transport.http", "HTTPTransportHandler"),
    "TCPTransportHandler": (".transport.tcp", "TCPTransportHandler"),
    "UDPTransportHandler": (".transport.udp", "UDPTransportHandler"),
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        module_path, attr_name = _LAZY_IMPORTS[name]
        import importlib

        mod = importlib.import_module(module_path, package="logeverything")
        val = getattr(mod, attr_name)
        globals()[name] = val  # Cache for subsequent access
        return val
    raise AttributeError(f"module 'logeverything' has no attribute {name}")


__all__ = [
    # Logging levels
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
    # Core loggers
    "Logger",
    "AsyncLogger",
    "get_logger",
    # Decorators
    "log",
    "log_function",
    "log_class",
    "log_io",
    # Context managers
    "LoggingContext",
    "QuietLoggingContext",
    "VerboseLoggingContext",
    # Print capture
    "enable_print_capture",
    "disable_print_capture",
    "capture_print",
    # Stdlib integration
    "intercept_stdlib",
    "restore_stdlib",
    # External integration
    "configure_external_logger",
    "harmonize_logger_levels",
    # Correlation
    "set_correlation_id",
    "get_correlation_id",
    "clear_correlation",
    "CorrelationFilter",
    "propagate_context",
    # Hierarchy
    "HierarchyFilter",
    # Transport
    "HTTPTransportHandler",
    "TCPTransportHandler",
    "UDPTransportHandler",
    "JSONLineFormatter",
    "TimedRotatingFileHandler",
]
