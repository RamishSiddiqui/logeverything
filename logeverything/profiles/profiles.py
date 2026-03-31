"""
Predefined configuration profiles for LogEverything.

This module provides standard configuration profiles for common use cases,
allowing users to quickly set up logging with sensible defaults for different scenarios.
"""

import logging
from typing import Any, Dict

# Development profile - detailed, interactive logging for development environments
DEVELOPMENT_PROFILE: Dict[str, Any] = {
    "level": logging.DEBUG,
    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    "date_format": "%H:%M:%S",
    "handlers": ["console"],
    "log_entry_exit": True,
    "log_arguments": True,
    "log_return_values": True,
    "log_io": True,
    "log_exceptions": True,
    "beautify": True,
    "indent_level": 2,
    "max_arg_length": 500,
    "include_line_numbers": True,
    "capture_print": True,
    "print_logger_name": "print",
    "print_level": logging.DEBUG,
    "print_prefix": "[PRINT] ",
    "visual_mode": True,
    "use_symbols": True,
    "use_indent": True,
    "use_colors": True,
    "color_theme": "default",
}

# Production profile - optimized for performance with minimal logging
PRODUCTION_PROFILE: Dict[str, Any] = {
    "level": logging.WARNING,
    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "handlers": ["file", "console"],
    "log_entry_exit": False,
    "log_arguments": False,
    "log_return_values": False,
    "log_io": False,
    "log_exceptions": True,
    "beautify": False,
    "indent_level": 0,
    "max_arg_length": 100,
    "file_path": "app.log",
    "include_line_numbers": True,
    "capture_print": False,
    "visual_mode": False,
    "use_symbols": False,
    "use_indent": False,
    "use_colors": False,
}

# Minimal profile - very basic logging with minimal overhead
MINIMAL_PROFILE: Dict[str, Any] = {
    "level": logging.WARNING,
    "format": "%(levelname)-8s | %(message)s",
    "handlers": ["console"],
    "log_entry_exit": False,
    "log_arguments": False,
    "log_return_values": False,
    "log_io": False,
    "log_exceptions": True,
    "beautify": False,
    "indent_level": 0,
    "max_arg_length": 50,
    "include_line_numbers": False,
    "capture_print": False,
    "visual_mode": False,
    "use_symbols": False,
    "use_indent": False,
    "use_colors": False,
}

# Debug profile - maximum verbosity for debugging purposes
DEBUG_PROFILE: Dict[str, Any] = {
    "level": logging.DEBUG,
    "format": (
        "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s | "
        "[%(filename)s:%(lineno)d] | %(message)s"
    ),
    "date_format": "%H:%M:%S",
    "handlers": ["console", "file"],
    "log_entry_exit": True,
    "log_arguments": True,
    "log_return_values": True,
    "log_io": True,
    "log_exceptions": True,
    "beautify": True,
    "indent_level": 4,
    "max_arg_length": 1000,
    "file_path": "debug.log",
    "include_line_numbers": True,
    "capture_print": True,
    "print_logger_name": "print",
    "print_level": logging.DEBUG,
    "print_prefix": "[PRINT] ",
    "visual_mode": True,
    "use_symbols": True,
    "use_indent": True,
    "use_colors": True,
    "color_theme": "vibrant",
}

# API/Web Service profile - optimized for API and web service logging
API_PROFILE: Dict[str, Any] = {
    "level": logging.INFO,
    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "handlers": ["console", "json"],
    "log_entry_exit": True,
    "log_arguments": True,
    "log_return_values": False,  # Don't log response bodies by default
    "log_io": False,
    "log_exceptions": True,
    "beautify": False,
    "indent_level": 0,
    "max_arg_length": 200,
    "include_line_numbers": True,
    "capture_print": False,
    "json_file_path": "api_logs.json",
    "visual_mode": False,
    "use_symbols": False,
    "use_indent": False,
    "use_colors": False,
}

# Testing profile - for use in test environments
TESTING_PROFILE: Dict[str, Any] = {
    "level": logging.DEBUG,
    "format": "%(levelname)-8s | %(name)s | %(message)s",
    "handlers": ["console"],
    "log_entry_exit": True,
    "log_arguments": True,
    "log_return_values": True,
    "log_io": False,
    "log_exceptions": True,
    "beautify": False,
    "indent_level": 0,
    "max_arg_length": 100,
    "include_line_numbers": False,
    "capture_print": False,
    "visual_mode": False,
    "use_symbols": False,
    "use_indent": False,
    "use_colors": False,
}

# Silent profile - file-only logging with no console output
SILENT_PROFILE: Dict[str, Any] = {
    "level": logging.DEBUG,
    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "handlers": ["file"],
    "log_entry_exit": True,
    "log_arguments": True,
    "log_return_values": True,
    "log_io": True,
    "log_exceptions": True,
    "beautify": False,
    "indent_level": 0,
    "max_arg_length": 500,
    "file_path": "silent.log",
    "include_line_numbers": True,
    "capture_print": False,
    "visual_mode": False,
    "use_symbols": False,
    "use_indent": False,
    "use_colors": False,
    "auto_detect_env": False,  # Explicitly disable environment auto-detection
}

# Distributed profile - for multi-process / microservice deployments with transport
DISTRIBUTED_PROFILE: Dict[str, Any] = {
    "level": logging.INFO,
    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "handlers": ["console", "json"],
    "log_entry_exit": True,
    "log_arguments": True,
    "log_return_values": False,
    "log_io": False,
    "log_exceptions": True,
    "beautify": False,
    "indent_level": 0,
    "max_arg_length": 200,
    "include_line_numbers": True,
    "capture_print": False,
    "async_mode": True,
    "visual_mode": False,
    "use_symbols": False,
    "use_indent": False,
    "use_colors": False,
}

# Map profile names to their configuration dictionaries
PROFILES = {
    "development": DEVELOPMENT_PROFILE,
    "production": PRODUCTION_PROFILE,
    "minimal": MINIMAL_PROFILE,
    "debug": DEBUG_PROFILE,
    "api": API_PROFILE,
    "web": API_PROFILE,  # Alias for API profile
    "testing": TESTING_PROFILE,
    "test": TESTING_PROFILE,  # Alias for testing profile
    "silent": SILENT_PROFILE,
    "distributed": DISTRIBUTED_PROFILE,
}


def get_profile(profile_name: str) -> Dict[str, Any]:
    """
    Get a predefined configuration profile by name.

    Args:
        profile_name: Name of the profile to retrieve.
                     One of: "development", "production", "minimal", "debug",
                     "api", "web", "testing", "test", "silent"

    Returns:
        Dict[str, Any]: Configuration dictionary for the requested profile

    Raises:
        ValueError: If the profile name is not recognized
    """
    profile_name = profile_name.lower().strip()
    if profile_name not in PROFILES:
        valid_profiles = ", ".join(f'"{k}"' for k in PROFILES.keys())
        raise ValueError(f'Unknown profile: "{profile_name}". Valid profiles are: {valid_profiles}')

    return PROFILES[profile_name].copy()  # Return a copy to prevent modification of the original
