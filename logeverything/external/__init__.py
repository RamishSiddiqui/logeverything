"""
LogEverything External Logger Integration

This module provides utilities for integrating with external logging libraries
and harmonizing log levels across different loggers.

Usage:
    from logeverything.external import configure_external_logger
    from logeverything.external import harmonize_logger_levels, configure_common_loggers

    # Configure specific external loggers
    configure_external_logger('requests', level='WARNING')
    configure_external_logger('urllib3', level='ERROR')

    # Harmonize levels across all loggers
    harmonize_logger_levels()

    # Configure common third-party loggers
    configure_common_loggers()
"""

import logging

# Import needed modules and functions that tests expect
from ..core import get_logger
from ..handlers.handlers import ConsoleHandler

# Import all external logger functionality
from .external import (
    _safe_log_level,
    check_dependency,
    configure_common_loggers,
    configure_external_logger,
    harmonize_logger_levels,
)

# Define what gets exported
__all__ = [
    "_safe_log_level",
    "check_dependency",
    "configure_common_loggers",
    "configure_external_logger",
    "harmonize_logger_levels",
    "get_logger",
    "ConsoleHandler",
    "logging",
]
