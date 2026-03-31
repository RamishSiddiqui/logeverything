"""
Utility functions for the LogEverything library.

This module provides common utility functions used across different modules.
"""

from .format_utils import format_value, safe_float, safe_int
from .levels import CRITICAL, DEBUG, ERROR, FATAL, INFO, WARN, WARNING
from .monitoring import LoggingMetrics, PerformanceMonitor
from .path_utils import get_relative_path
from .platform_utils import clear_symbol_cache, get_ascii_only_mode, get_symbols, supports_unicode

__all__ = [
    "get_relative_path",
    "format_value",
    "safe_int",
    "safe_float",
    "LoggingMetrics",
    "PerformanceMonitor",
    # Platform utilities
    "get_symbols",
    "get_ascii_only_mode",
    "supports_unicode",
    # Logging levels
    "DEBUG",
    "INFO",
    "WARNING",
    "WARN",
    "ERROR",
    "CRITICAL",
    "FATAL",
]
