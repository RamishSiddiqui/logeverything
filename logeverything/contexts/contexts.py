"""
Context managers for the LogEverything library.

This module provides context managers that allow for temporarily modifying
logging configuration using Python's `with` statement.
"""

import copy
import logging
from typing import Any, Dict, List, Optional, TypeVar, Union, cast

from ..core import _config, configure, setup_logging

# TypeVar for better type hinting
ConfigValue = TypeVar("ConfigValue", int, str, bool, List[Union[str, logging.Handler]], None)


def _safe_setup_logging(**kwargs: Any) -> None:
    """
    Safely call setup_logging with proper type conversion.

    Args:
        **kwargs: Configuration options that need type conversion
    """
    # Filter out None values
    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    # Call setup_logging with the filtered arguments
    if filtered_kwargs:
        setup_logging(_internal=True, **filtered_kwargs)


class LoggingContext:
    """
    A context manager for temporarily changing logging configuration.

    This allows you to change logging settings within a specific block of code
    and automatically restore the previous settings when exiting the block.

    Example:
        >>> with LoggingContext(level="DEBUG", log_entry_exit=True):
        ...     # Code here will use DEBUG level and log function entry/exit
        ...     my_function()
        ... # Original settings are restored after the with block
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
        Initialize a logging context with temporary configuration.

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
        self.new_config = {
            "level": level,
            "log_entry_exit": log_entry_exit,
            "log_arguments": log_arguments,
            "log_return_values": log_return_values,
            "beautify": beautify,
            "indent_level": indent_level,
            "handlers": handlers,
            "logger_name": logger_name,
            "capture_print": capture_print,
            "print_logger_name": print_logger_name,
            "print_level": print_level,
            "print_prefix": print_prefix,
        }

        # Add any additional kwargs
        for key, value in kwargs.items():
            self.new_config[key] = value

        # Remove None values to only apply specified changes
        self.new_config = {k: v for k, v in self.new_config.items() if v is not None}

        # Will store the original configuration
        self.original_config: Dict[str, Any] = {}

    def __enter__(self) -> Dict[str, Any]:
        """
        Enter the context, save original settings and apply new ones.

        Returns:
            Dict[str, Any]: The current configuration
        """
        # Save original values for all keys we're going to change
        for key in self.new_config:
            if key in _config:
                self.original_config[key] = copy.deepcopy(_config[key])

        # Apply new configuration - we need to pass parameters individually
        # rather than with **self.new_config to satisfy mypy
        if "level" in self.new_config:
            configure(_internal=True, level=cast(Union[int, str, None], self.new_config["level"]))
        if "log_entry_exit" in self.new_config:
            configure(_internal=True, log_entry_exit=cast(bool, self.new_config["log_entry_exit"]))
        if "log_arguments" in self.new_config:
            configure(_internal=True, log_arguments=cast(bool, self.new_config["log_arguments"]))
        if "log_return_values" in self.new_config:
            configure(
                _internal=True, log_return_values=cast(bool, self.new_config["log_return_values"])
            )
        if "beautify" in self.new_config:
            configure(_internal=True, beautify=cast(bool, self.new_config["beautify"]))
        if "indent_level" in self.new_config:
            configure(_internal=True, indent_level=cast(int, self.new_config["indent_level"]))
        if "handlers" in self.new_config:
            configure(
                _internal=True,
                handlers=cast(List[Union[str, logging.Handler]], self.new_config["handlers"]),
            )
        if "logger_name" in self.new_config:
            configure(_internal=True, logger_name=cast(str, self.new_config["logger_name"]))
        if "capture_print" in self.new_config:
            configure(_internal=True, capture_print=cast(bool, self.new_config["capture_print"]))
        if "print_logger_name" in self.new_config:
            configure(
                _internal=True, print_logger_name=cast(str, self.new_config["print_logger_name"])
            )
        if "print_level" in self.new_config:
            configure(_internal=True, print_level=cast(int, self.new_config["print_level"]))
        if "print_prefix" in self.new_config:
            configure(_internal=True, print_prefix=cast(str, self.new_config["print_prefix"]))

        return _config

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit the context and restore original settings.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        # Restore original configuration - handle each parameter individually
        if "level" in self.original_config:
            configure(_internal=True, level=self.original_config["level"])
        if "log_entry_exit" in self.original_config:
            configure(
                _internal=True, log_entry_exit=cast(bool, self.original_config["log_entry_exit"])
            )
        if "log_arguments" in self.original_config:
            configure(
                _internal=True, log_arguments=cast(bool, self.original_config["log_arguments"])
            )
        if "log_return_values" in self.original_config:
            configure(
                _internal=True,
                log_return_values=cast(bool, self.original_config["log_return_values"]),
            )
        if "beautify" in self.original_config:
            configure(_internal=True, beautify=cast(bool, self.original_config["beautify"]))
        if "indent_level" in self.original_config:
            configure(_internal=True, indent_level=cast(int, self.original_config["indent_level"]))
        if "handlers" in self.original_config:
            configure(
                _internal=True,
                handlers=cast(List[Union[str, logging.Handler]], self.original_config["handlers"]),
            )
        if "logger_name" in self.original_config:
            configure(_internal=True, logger_name=cast(str, self.original_config["logger_name"]))
        if "capture_print" in self.original_config:
            configure(
                _internal=True, capture_print=cast(bool, self.original_config["capture_print"])
            )
        if "print_logger_name" in self.original_config:
            configure(
                _internal=True,
                print_logger_name=cast(str, self.original_config["print_logger_name"]),
            )
        if "print_level" in self.original_config:
            configure(_internal=True, print_level=cast(int, self.original_config["print_level"]))
        if "print_prefix" in self.original_config:
            configure(_internal=True, print_prefix=cast(str, self.original_config["print_prefix"]))


class VisualLoggingContext(LoggingContext):
    """
    A context manager for temporarily enabling or configuring visual logging.

    This context manager is specialized for visual enhancements to logging output,
    allowing you to enable colors, symbols, indentation, and other visual elements
    for a specific block of code.

    Visual settings are managed separately from standard logging settings because they
    may require reconfiguration of handlers and formatters. For this reason, they are
    handled through setup_logging() rather than configure().

    Example:
        >>> with VisualLoggingContext(use_colors=True, use_symbols=True):
        ...     # Code here will use visual enhancements
        ...     log_complex_data()
        ... # Original visual settings are restored after the with block
    """

    def __init__(
        self,
        visual_mode: Optional[bool] = True,
        use_symbols: Optional[bool] = None,
        use_indent: Optional[bool] = None,
        align_columns: Optional[bool] = None,
        auto_detect_platform: Optional[bool] = None,
        force_ascii: Optional[bool] = None,
        disable_colors: Optional[bool] = None,
        color_theme: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a visual logging context with temporary configuration.

        Args:
            visual_mode: Master switch for visual enhancements
            use_symbols: Whether to use Unicode symbols for log levels
            use_indent: Whether to use visual indentation with box drawing characters
            align_columns: Whether to align columns in log output
            auto_detect_platform: Whether to detect platform capabilities automatically
            force_ascii: Whether to force ASCII-only output (no Unicode)
            disable_colors: Whether to disable ANSI color codes
            color_theme: Color theme to use for console output
            **kwargs: Additional configuration options
        """
        # Initialize base class with standard settings
        super().__init__(**kwargs)

        # Store visual settings separately
        self.visual_settings = {
            "visual_mode": visual_mode,
            "use_symbols": use_symbols,
            "use_indent": use_indent,
            "align_columns": align_columns,
            "auto_detect_platform": auto_detect_platform,
            "force_ascii": force_ascii,
            "disable_colors": disable_colors,
            "color_theme": color_theme,
        }
        self.visual_settings = {k: v for k, v in self.visual_settings.items() if v is not None}

    def __enter__(self) -> Dict[str, Any]:
        """
        Enter the context, save original settings and apply new ones.

        Returns:
            Dict[str, Any]: The current configuration
        """
        # First save all current visual settings
        visual_keys = [
            "visual_mode",
            "use_symbols",
            "use_indent",
            "align_columns",
            "auto_detect_platform",
            "force_ascii",
            "disable_colors",
            "color_theme",
        ]
        self.original_visual = {k: _config.get(k) for k in visual_keys}

        # Apply the new visual settings
        if self.visual_settings:
            _safe_setup_logging(**self.visual_settings)

        # Then apply standard settings using the parent's __enter__
        super().__enter__()

        return _config

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit the context and restore original settings.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        # First restore visual settings
        if hasattr(self, "original_visual"):
            # Directly update config to handle None values properly
            for key, value in self.original_visual.items():
                _config[key] = value

        # Then restore standard settings through parent
        super().__exit__(exc_type, exc_val, exc_tb)


class QuietLoggingContext(LoggingContext):
    """
    A context manager for temporarily suppressing or minimizing logging output.

    This context manager is specialized for reducing log verbosity for a specific
    block of code, useful when you want to silence noisy operations temporarily.

    Example:
        >>> with QuietLoggingContext():
        ...     # This code will produce minimal logs
        ...     noisy_operation()
        ... # Original logging verbosity is restored after the with block
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
        Initialize a quiet logging context with minimized verbosity.

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


class VerboseLoggingContext(LoggingContext):
    """
    A context manager for temporarily increasing logging verbosity.

    This context manager is specialized for maximizing log information for a specific
    block of code, useful for debugging or detailed analysis of specific operations.

    Example:
        >>> with VerboseLoggingContext():
        ...     # This code will produce detailed logs
        ...     complex_operation()
        ... # Original logging verbosity is restored after the with block
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
        Initialize a verbose logging context with maximum verbosity.

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


class TemporaryHandlerContext:
    """
    A context manager for temporarily using specific log handlers.

    This context manager allows you to temporarily switch to a different set of
    handlers for a specific block of code, and then automatically restore the
    original handlers when exiting the block.

    Example:
        >>> with TemporaryHandlerContext(["file", "json"]):
        ...     # This code will log to file and JSON, ignoring console
        ...     important_operation()
        ... # Original handlers are restored after the with block
    """

    def __init__(self, handlers: List[Union[str, logging.Handler]]) -> None:
        """
        Initialize a temporary handler context.

        Args:
            handlers: A list of handler names or actual handler objects to use temporarily
        """
        self.handlers = handlers
        self.original_handlers: Optional[List[Union[str, logging.Handler]]] = None

    def __enter__(self) -> Dict[str, Any]:
        """
        Enter the context, save original handlers and apply new ones.

        Returns:
            Dict[str, Any]: The current configuration
        """
        # Save original handlers
        if "handlers" in _config:
            self.original_handlers = cast(
                List[Union[str, logging.Handler]], copy.deepcopy(_config["handlers"])
            )

        # Apply new handlers using setup_logging which handles proper handler initialization
        setup_logging(handlers=self.handlers, _internal=True)

        return _config

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit the context and restore original handlers.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        # Restore original handlers
        if self.original_handlers is not None:
            setup_logging(handlers=self.original_handlers, _internal=True)
