"""
Core functionality for the LogEverything library.

This module provides the main configuration and setup functions for logging.
"""

import difflib
import logging
import multiprocessing
import os
import platform
import sys
import threading
import time as _time
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from colorama import init as colorama_init  # Ensure colorama is properly typed

# Import profiles only when needed to avoid circular imports
from . import profiles as _profiles_module

# Import the new unified indent manager
from .indent_manager import configure_indent_manager
from .indent_manager import decrement_indent as _new_decrement_indent
from .indent_manager import get_current_indent as _new_get_current_indent
from .indent_manager import increment_indent as _new_increment_indent
from .utils import safe_float, safe_int


def _format_info_message(message: str, message_type: str = "INFO") -> str:
    """
    Format informational messages with timestamp and colors.

    Args:
        message: The message to format
        message_type: Type of message for color coding (INFO, WARNING, ERROR)

    Returns:
        Formatted message with timestamp and colors if supported
    """
    from datetime import datetime

    # Get current timestamp in the same format as our loggers
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get current indentation to respect context hierarchy
    current_indent = ""
    try:
        current_indent = get_current_indent()
    except (NameError, AttributeError, KeyError, TypeError):
        # If indentation system is not available or fails, continue without it
        pass

    # Detect platform capabilities for Unicode support
    platform_caps = detect_platform_capabilities()
    supports_unicode = platform_caps.get("supports_unicode", True)

    # Level symbols (Unicode or ASCII fallback)
    level_symbols = {
        "INFO": "ℹ️" if supports_unicode else "i",
        "WARNING": "⚠️" if supports_unicode else "!",
        "ERROR": "❌" if supports_unicode else "X",
        "SUCCESS": "✅" if supports_unicode else "+",
        "DEBUG": "🔍" if supports_unicode else "?",
    }

    symbol = level_symbols.get(message_type, level_symbols["INFO"])

    # Create bracketed level format matching PrettyFormatter exactly
    # INFO level uses format: [  {symbol} {levelname}  ]
    if message_type == "DEBUG":
        level_text = f"[ {symbol} {message_type}  ]"
    elif message_type == "INFO":
        level_text = f"[  {symbol} {message_type}  ]"
    elif message_type == "WARNING":
        level_text = f"[{symbol} {message_type} ]"
    elif message_type == "ERROR":
        level_text = f"[ {symbol} {message_type}  ]"
    elif message_type in ["SUCCESS", "CRITICAL"]:
        level_text = f"[{symbol} {message_type}]"
    else:
        # Fallback for any other message types
        content = f"{symbol} {message_type}"
        level_text = f"[{content:^12}]"

    # Try to import colorama for colors
    try:
        import colorama
        from colorama import Fore, Style

        # Initialize colorama if not already done
        colorama.init()

        # Color scheme based on message type
        colors = {
            "INFO": f"{Fore.CYAN}",
            "WARNING": f"{Fore.YELLOW}",
            "ERROR": f"{Fore.RED}",
            "SUCCESS": f"{Fore.GREEN}",
        }

        color = colors.get(message_type, Fore.CYAN)
        reset = Style.RESET_ALL

        # Format: timestamp | [ icon LEVEL ] | logeverything | indentation + message
        formatted = (
            f"{color}{timestamp} | {level_text} | logeverything | "
            f"{current_indent}{message}{reset}"
        )

    except ImportError:
        # Fallback without colors
        formatted = f"{timestamp} | {level_text} | logeverything | {current_indent}{message}"

    return formatted


def _print_info_message(message: str, message_type: str = "INFO") -> None:
    """
    Print a formatted informational message.

    Args:
        message: The message to print
        message_type: Type of message for formatting
    """
    formatted_msg = _format_info_message(message, message_type)
    try:
        print(formatted_msg)
    except UnicodeEncodeError:
        # Fallback: strip Unicode characters that can't be encoded (e.g., Windows cp1252)
        ascii_msg = formatted_msg.encode("ascii", errors="replace").decode("ascii")
        print(ascii_msg)


# Environment detection functions for automatic configuration
def _detect_environment() -> str:
    """
    Auto-detect the current execution environment.

    Returns:
        str: Detected environment type - 'web_app', 'script', 'cli', 'notebook', or 'unknown'
    """
    # Check for Jupyter/IPython notebook first (highest priority)
    if "ipykernel" in sys.modules or "google.colab" in sys.modules:
        return "notebook"

    # Check if running as CLI script or regular script
    if len(sys.argv) > 0 and os.path.basename(sys.argv[0]) != "":
        # If it has arguments and appears to be a command
        if sys.argv[0].endswith(".py") or sys.argv[0].startswith("-"):
            return "script"
        return "cli"

    # If not in notebook or script/CLI, check for web frameworks
    web_frameworks = ("flask", "django", "fastapi")
    if any(
        mod in web_frameworks
        or any(mod.startswith(f"{framework}.") for framework in web_frameworks)
        for mod in sys.modules
    ):
        return "web_app"

    return "unknown"


def _get_environment_config(env_type: str) -> Dict[str, Union[bool, int, str]]:
    """
    Get configuration defaults based on the detected environment.

    Args:
        env_type: The detected environment type

    Returns:
        Dict with environment-specific configuration values
    """
    # Common configuration for all environments
    config: Dict[str, Union[bool, int, str]] = {
        "beautify": True,
        "log_entry_exit": True,
        "log_exceptions": True,
    }

    if env_type == "web_app":
        # Web applications benefit from structured logging and async processing
        config.update(
            {
                "level": logging.INFO,
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                "visual_mode": False,
                "async_mode": True,
                # Don't log web request args by default (could contain sensitive data)
                "log_arguments": False,
                "log_return_values": False,
            }
        )

    elif env_type == "notebook":
        # Notebooks benefit from visual formatting and detailed output
        config.update(
            {
                "level": logging.INFO,
                "format": "%(levelname)s: %(message)s",
                "visual_mode": True,
                "use_symbols": True,
                "use_indent": True,
                "align_columns": True,
                "async_mode": False,
                "log_arguments": True,
                "log_return_values": True,
            }
        )

    elif env_type == "cli":
        # CLI tools benefit from concise output
        config.update(
            {
                "level": logging.INFO,
                "format": "%(message)s",
                "visual_mode": False,
                "async_mode": False,
                "log_arguments": True,
                "log_return_values": False,
            }
        )

    else:  # script or unknown
        # Scripts benefit from detailed debug information with enhanced visual formatting
        config.update(
            {
                "level": logging.DEBUG,
                "format": "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
                "visual_mode": True,
                "use_symbols": True,
                "use_indent": True,  # Enable indentation for better visual hierarchy
                "align_columns": True,  # Enable column alignment for consistency
                "async_mode": False,
                "log_arguments": True,
                "log_return_values": True,
            }
        )

    return config


# Cached thread count check with TTL to avoid repeated kernel calls
_thread_count_cache: int = 1
_thread_count_cache_time: float = 0.0


def _is_concurrent() -> bool:
    """Check if we're in a concurrent environment, with 100ms TTL cache.

    Replaces per-call threading.active_count() syscalls with a cached check.
    """
    global _thread_count_cache, _thread_count_cache_time
    now = _time.monotonic()
    if now - _thread_count_cache_time > 0.1:  # 100ms TTL
        _thread_count_cache = threading.active_count()
        _thread_count_cache_time = now
    return _thread_count_cache > 1


# Default configuration
DEFAULT_CONFIG = {
    "level": logging.INFO,
    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "handlers": ["console"],
    "log_entry_exit": True,
    "log_arguments": True,
    "log_return_values": True,
    "log_io": True,
    "log_exceptions": True,
    "beautify": True,
    "indent_level": 2,
    "max_arg_length": 300,
    "file_path": "logeverything.log",
    "log_directory": "",  # Default to current directory
    "include_line_numbers": True,
    "capture_print": False,  # Whether to capture print statements
    "print_logger_name": "print",  # Logger name for captured print statements
    "print_level": logging.INFO,  # Log level for captured print statements
    "print_prefix": "[PRINT] ",  # Prefix for captured print statements
    # Visual formatting options (disabled by default)
    "visual_mode": False,  # Master switch for visual enhancements
    "use_symbols": False,  # Use Unicode symbols for log levels
    "use_indent": False,  # Use visual indentation with box drawing
    "align_columns": False,  # Align log columns
    "auto_detect_platform": True,  # Detect platform capabilities
    "force_ascii": False,  # Force ASCII-only output (no Unicode)
    "disable_colors": False,  # Disable ANSI color codes
    # Default color theme (options: default, pastel, bold, monochrome)
    "color_theme": "default",
    # Async logging options
    "async_mode": False,  # Master switch for async logging
    "async_queue_size": 1000,  # Maximum size of async queue
    "async_flush_level": logging.CRITICAL,  # Level that triggers immediate flush
    "async_flush_interval": 1.0,  # Interval in seconds for flushing the queue
    "worker_threads": 1,  # Default number of worker threads
    "batch_size": 10,  # Number of records to process in a batch,
    # External logger integration options
    "integrate_external_loggers": False,  # Whether to integrate with third-party loggers
    "external_logger_level": None,  # Level for external loggers (None uses main level)
}

# Global configuration dictionary
_config = DEFAULT_CONFIG.copy()

# Thread-local storage for tracking execution context and indentation
_context = threading.local()

# Process dictionary for tracking execution in multiprocessing env
# Use a dict for single process apps to avoid unnecessary Manager overhead
_process_context: Optional[Dict[str, Dict[str, Any]]] = None


def _get_process_context() -> Dict[str, Dict[str, Any]]:
    """Get the process context dictionary, creating it lazily if needed."""
    global _process_context
    if _process_context is None:
        if multiprocessing.parent_process() is None:
            try:
                _process_context = multiprocessing.Manager().dict()  # type: ignore[assignment]
            except Exception:
                _process_context = {}
        else:
            _process_context = {}
    # At this point _process_context is guaranteed to be not None
    return _process_context  # type: ignore[return-value]


# Root logger for the library
logger = logging.getLogger("logeverything")

# Initialize colorama for Windows compatibility
colorama_init()

# Adding type annotations for global variables
_logger_cache: Dict[str, logging.Logger] = {}
# Cache for indent strings to avoid recalculating
# String multiplication can be expensive when called repeatedly
_indent_cache: Dict[Tuple[int, bool, bool, bool], str] = {}

# Registry for active LogEverything Logger instances
# This tracks actual Logger instances created by users, not just cached logging.Logger objects
_active_loggers: Dict[str, Any] = {}  # Dict[str, Logger] but avoiding circular import

# Version counter for _active_loggers, incremented on register/unregister
# Used by decorators to invalidate cached logger references
_active_loggers_version: int = 0

# Set to track decorator locations that have already shown logger selection warnings
_warned_decorator_locations: set = set()


def _initialize_context() -> None:
    """Initialize thread-local context for the current thread/process with automatic isolation."""
    # Check if we need to reset context due to pollution
    _reset_context_if_needed()

    if not hasattr(_context, "indent") or not hasattr(_context, "isolation_id"):
        _create_isolated_context()  # Store in process dictionary for multiprocessing support
        proc_id = str(os.getpid())  # Convert to string key
        thread_id = str(threading.get_ident())  # Convert to string key
        process_context = _get_process_context()
        if proc_id not in process_context:
            process_context[proc_id] = {}
        process_context[proc_id][thread_id] = _context.execution_id


# Isolation tracking
_context_isolation_id = 0
_isolation_lock = threading.Lock()


# Context isolation utilities (internal only)
def _get_next_isolation_id() -> int:
    """Get the next isolation ID for context separation."""
    global _context_isolation_id
    with _isolation_lock:
        _context_isolation_id += 1
        return _context_isolation_id


def _create_isolated_context() -> None:
    """Create a new isolated context for the current thread."""
    isolation_id = _get_next_isolation_id()
    _context.indent = 0
    _context.function_stack = []
    _context.execution_id = f"{os.getpid()}-{threading.get_ident()}-{isolation_id}"
    _context.isolation_id = isolation_id
    _context.created_at = threading.current_thread().ident
    # Initialize indentation preferences to None (will be set by logger configuration)
    if not hasattr(_context, "use_symbols_for_indent"):
        _context.use_symbols_for_indent = None


def set_context_use_symbols(use_symbols: bool) -> None:
    """Set the use_symbols preference for indentation in the current thread context."""
    if not hasattr(_context, "indent"):
        _initialize_context()
    _context.use_symbols_for_indent = use_symbols


def _reset_context_if_needed() -> None:
    """Reset context if we detect potential pollution."""
    if not hasattr(_context, "isolation_id"):
        _create_isolated_context()
        return

    # Check if we're in a different thread than when context was created
    current_thread = threading.current_thread().ident
    if hasattr(_context, "created_at") and _context.created_at != current_thread:
        _create_isolated_context()
        return

    # Reset if function stack is corrupted (isolation breach)
    if hasattr(_context, "function_stack") and len(_context.function_stack) > 50:
        # Likely a context leak, reset
        _create_isolated_context()


def detect_platform_capabilities() -> Dict[str, Any]:
    """
    Detect the capabilities of the current platform for log formatting.

    This function checks whether the current platform and terminal support
    Unicode characters and ANSI color codes.

    Returns:
        Dict[str, Any]: A dictionary with the platform capabilities
    """
    capabilities: Dict[str, Any] = {
        "supports_unicode": True,
        "supports_colors": True,
    }

    # Check platform
    system = platform.system()

    # Check terminal encoding
    encoding = getattr(sys.stdout, "encoding", None)

    # Windows has limited Unicode support in legacy consoles
    if system == "Windows":
        # Check if we're in a modern terminal with better Unicode support
        if "WT_SESSION" not in os.environ and "TERM_PROGRAM" not in os.environ:
            # Legacy Windows console has limited Unicode support
            capabilities["supports_unicode"] = False

        # Check if ANSICON or other ANSI enablers are present
        if (
            "ANSICON" not in os.environ
            and "WT_SESSION" not in os.environ
            and "TERM_PROGRAM" not in os.environ
        ):
            # Check if we have the colorama module which can help with ANSI colors
            try:
                import colorama

                colorama.init()
                capabilities["supports_colors"] = True
            except ImportError:
                # Without colorama, color support is uncertain
                capabilities["supports_colors"] = False

    # Check for ASCII-only encoding
    if encoding is None or encoding.lower() in ("ascii", "us-ascii"):
        capabilities["supports_unicode"] = False

    # Check for redirected output
    try:
        if not sys.stdout.isatty():
            # Redirected output (e.g., to a file or pipe) may not support colors
            capabilities["supports_colors"] = False
    except (AttributeError, ValueError):
        # If isatty() is not available or fails, assume no color support
        capabilities["supports_colors"] = False

    return capabilities


def setup_logging(
    profile: Optional[str] = None,
    level: Optional[Union[int, str]] = None,
    format_string: Optional[str] = None,
    handlers: Optional[List[Union[str, logging.Handler]]] = None,
    file_path: Optional[str] = None,
    log_directory: Optional[str] = None,
    visual_mode: Optional[bool] = None,
    use_symbols: Optional[bool] = None,
    use_indent: Optional[bool] = None,
    align_columns: Optional[bool] = None,
    auto_detect_platform: Optional[bool] = None,
    force_ascii: Optional[bool] = None,
    disable_colors: Optional[bool] = None,
    color_theme: Optional[str] = None,
    async_mode: Optional[bool] = None,
    async_queue_size: Optional[int] = None,
    async_flush_level: Optional[Union[int, str]] = None,
    async_flush_interval: Optional[float] = None,
    integrate_external_loggers: Optional[bool] = None,
    external_logger_level: Optional[Union[int, str]] = None,
    auto_detect_env: bool = True,
    _internal: bool = False,
    **kwargs: Any,
) -> logging.Logger:
    """
    Set up logging with the specified configuration.

    Args:
        profile: Use a predefined configuration profile. Options: "development", "production",
                "minimal", "debug", "api", "web", "testing". When specified, other parameters
                will override the profile defaults.
        level: The logging level to use (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: The format string for log messages
        handlers: List of handlers to use ("console", "file", "json") or actual handler objects
        file_path: Path to the log file if file handler is used
        log_directory: Directory to store log files (will be created if it doesn't exist)
        visual_mode: Enable enhanced visual formatting (default: False)
        use_symbols: Use Unicode symbols for log levels (default: False)
        use_indent: Use visual indentation with box drawing characters (default: False)
        align_columns: Align columns in log output (default: False)
        auto_detect_platform: Automatically detect platform capabilities (default: True)
        force_ascii: Force ASCII-only output (no Unicode) (default: False)
        disable_colors: Disable ANSI color codes (default: False)
        color_theme: Color theme for console output (default: "default")
        async_mode: Enable asynchronous logging (default: False)
        async_queue_size: Size of the async logging queue (default: 1000)
        async_flush_level: Log level for immediate flush (default: CRITICAL)
        async_flush_interval: Flush interval in seconds (default: 1.0)
        integrate_external_loggers: Enable external logger integration (default: False)
        external_logger_level: The logging level to use for external loggers
            (default: same as level)
        auto_detect_env: Automatically detect the environment and apply
        optimized settings (default: True)
        **kwargs: Additional configuration options

    Returns:
        logging.Logger: The configured logger

    Note:
        When no specific configuration is provided and auto_detect_env is True,
        LogEverything will automatically configure itself based on the detected environment:
        - Web apps: Optimized for structured logs, async mode enabled, sensitive data protection
        - Notebooks: Visual enhanced output with symbols and indentation
        - CLI applications: Concise, direct output format
        - Scripts: Detailed debug information with timestamps and line numbers

    .. deprecated::
        Use ``Logger().configure()`` instead. This function will be removed in a future version.
    """
    if not _internal:
        import warnings

        warnings.warn(
            "setup_logging() is deprecated. Use Logger().configure() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    # Convert values to proper types before using
    def safe_int(val: Any, default: int) -> int:
        """Safely convert a value to int with a default."""
        if isinstance(val, (int, float)):
            return int(val)
        if isinstance(val, str) and val.isdigit():
            return int(val)
        return default  # Apply profile configuration if specified

    if profile is not None:
        try:
            profile_config = _profiles_module.get_profile(profile)
            # Update _config with profile settings
            _config.update(profile_config)
        except ValueError:
            # Log the error but continue with default config
            logging.getLogger("logeverything").debug("Continuing with default configuration.")
    # Apply auto-detected environment settings if enabled and if no profile is specified
    # Environment detection only applies when minimal configuration is provided
    elif auto_detect_env and level is None and format_string is None:
        env_type = _detect_environment()
        env_config = _get_environment_config(env_type)
        # Apply environment-specific configuration without overriding user settings
        _config.update(env_config)

    # Update configuration with provided values, with type validation
    # These will override any profile settings
    if level is not None:
        if isinstance(level, str):
            _config["level"] = getattr(logging, level.upper(), logging.INFO)
        else:
            _config["level"] = safe_int(level, logging.INFO)

    if format_string is not None:
        _config["format"] = str(format_string)

    if handlers is not None:
        if all(isinstance(h, str) for h in handlers):
            _config["handlers"] = list(handlers)
        # If handlers are objects rather than strings, we'll add them directly later

    if log_directory is not None:
        log_dir = str(log_directory)
        _config["log_directory"] = log_dir
        if log_dir:  # Only create if not empty
            os.makedirs(log_dir, exist_ok=True)

    if file_path is not None:
        _config["file_path"] = str(file_path)

    # Cast boolean options with safe defaults
    _config["visual_mode"] = (
        bool(visual_mode) if visual_mode is not None else _config["visual_mode"]
    )
    _config["use_symbols"] = (
        bool(use_symbols) if use_symbols is not None else _config["use_symbols"]
    )
    _config["use_indent"] = bool(use_indent) if use_indent is not None else _config["use_indent"]
    _config["align_columns"] = (
        bool(align_columns) if align_columns is not None else _config["align_columns"]
    )
    _config["auto_detect_platform"] = (
        bool(auto_detect_platform)
        if auto_detect_platform is not None
        else _config["auto_detect_platform"]
    )
    _config["force_ascii"] = (
        bool(force_ascii) if force_ascii is not None else _config["force_ascii"]
    )
    _config["disable_colors"] = (
        bool(disable_colors) if disable_colors is not None else _config["disable_colors"]
    )

    if color_theme is not None:
        _config["color_theme"] = str(color_theme)  # Handle async-specific configurations
    if async_mode is not None:
        _config["async_mode"] = bool(async_mode)
    if async_queue_size is not None:
        _config["async_queue_size"] = safe_int(async_queue_size, 1000)
    if async_flush_level is not None:
        if isinstance(async_flush_level, str):
            _config["async_flush_level"] = getattr(
                logging, async_flush_level.upper(), logging.CRITICAL
            )
        else:
            _config["async_flush_level"] = safe_int(async_flush_level, logging.CRITICAL)
    if async_flush_interval is not None:
        try:
            _config["async_flush_interval"] = float(async_flush_interval)
        except (ValueError, TypeError):
            _config["async_flush_interval"] = 1.0

    # Update any other provided configuration
    for key, value in kwargs.items():
        if key == "level":
            _config[key] = safe_int(value, logging.INFO)
        else:
            _config[key] = value

    # Only configure the root logger if console handlers are needed
    # This prevents unwanted console output when using file-only logging
    handlers_list = _config.get("handlers", ["console"])
    if isinstance(handlers_list, (list, tuple)):
        handlers_names = [
            str(h) if isinstance(h, str) else h.__class__.__name__.lower() for h in handlers_list
        ]
        # Only call basicConfig if console handlers are requested
        if "console" in handlers_names:
            logging.basicConfig(
                level=safe_int(_config["level"], logging.INFO),
                format=str(_config["format"]),
                datefmt=str(_config["date_format"]),
            )
    else:
        # Default behavior if handlers is not a list/tuple
        logging.basicConfig(
            level=safe_int(_config["level"], logging.INFO),
            format=str(_config["format"]),
            datefmt=str(_config["date_format"]),
        )

    # Configure the library's logger
    level = cast(Union[int, str], _config["level"])
    logger.setLevel(level)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Store user's explicit choices before platform detection
    user_use_symbols = use_symbols
    user_use_indent = use_indent
    user_visual_mode = visual_mode

    # Detect platform capabilities if auto-detection is enabled
    platform_capabilities = {"supports_unicode": True, "supports_colors": True}
    if _config["auto_detect_platform"]:
        platform_capabilities = detect_platform_capabilities()

        # Apply platform limitations if auto-detection is enabled, but don't
        # override explicit user settings
        if not _config["force_ascii"] and platform_capabilities["supports_unicode"]:
            if user_use_symbols is None:  # Only set if user didn't configure
                _config["use_symbols"] = True
            if user_use_indent is None:  # Only set if user didn't configure
                _config["use_indent"] = True
        if not _config["disable_colors"] and platform_capabilities["supports_colors"]:
            if user_visual_mode is None:  # Only set if user didn't configure
                _config["visual_mode"] = True
    else:
        # Otherwise, just respect the force_ascii and disable_colors settings,
        # but preserve user choices
        if not _config["force_ascii"]:
            if user_use_symbols is None:  # Only set if user didn't configure
                _config["use_symbols"] = True
            if user_use_indent is None:  # Only set if user didn't explicitly configure
                _config["use_indent"] = True
        if not _config["disable_colors"]:
            if user_visual_mode is None:  # Only set if user didn't explicitly configure
                _config["visual_mode"] = True

    # If handlers are actual handler objects, add them directly
    if handlers and not all(isinstance(h, str) for h in handlers):
        for h in handlers:
            if isinstance(h, logging.Handler):
                # Apply level if not already set
                if h.level == logging.NOTSET:
                    h.setLevel(cast(Union[int, str], _config["level"]))
                logger.addHandler(h)  # Add requested handlers by name
    if isinstance(_config["handlers"], (list, tuple)):
        handlers_list = [
            str(h) if isinstance(h, str) else h.__class__.__name__.lower()
            for h in cast(List[Union[str, logging.Handler]], _config["handlers"])
        ]

        # Prepare a list to collect all handlers for potential async wrapping
        all_handlers = []

        # Handle console output
        if "console" in handlers_list:
            # Use EnhancedConsoleHandler if visual_mode is enabled
            if _config["visual_mode"]:
                # Import here to avoid circular imports
                from .handlers.handlers import EnhancedConsoleHandler

                # Detect platform capabilities for Windows console encoding
                platform_capabilities = detect_platform_capabilities()

                # Auto-detect if we should force ASCII to prevent encoding errors
                should_force_ascii = _config.get("force_ascii", False)
                if not should_force_ascii and not platform_capabilities.get(
                    "supports_unicode", True
                ):
                    should_force_ascii = True

                console_handler: logging.Handler = EnhancedConsoleHandler(
                    use_colors=not bool(_config.get("disable_colors", False)),
                    color_messages=_config.get("color_messages", False),
                    use_symbols=_config.get("use_symbols", _config["visual_mode"])
                    and not should_force_ascii,
                    use_indent=_config.get("use_indent", _config["visual_mode"]),
                    align_columns=_config.get("align_columns", False),
                    color_theme=str(_config.get("color_theme", "default")),
                    ascii_only=should_force_ascii,
                    level=cast(Union[int, str], _config["level"]),
                )

                # Force immediate flushing to prevent print/log ordering issues
                original_emit = console_handler.emit

                def flush_emit(record: logging.LogRecord) -> None:
                    original_emit(record)
                    if hasattr(console_handler, "stream") and hasattr(
                        console_handler.stream, "flush"
                    ):
                        console_handler.stream.flush()

                console_handler.emit = flush_emit  # type: ignore[method-assign]
            else:
                # Use standard console handler with immediate flushing
                console_handler = logging.StreamHandler(sys.stdout)
                formatter = logging.Formatter(
                    fmt=str(_config["format"]), datefmt=str(_config["date_format"])
                )
                console_handler.setFormatter(formatter)
                console_handler.setLevel(cast(Union[int, str], _config["level"]))

                # Force immediate flushing to prevent print/log ordering issues
                original_emit = console_handler.emit

                def flush_emit(record: logging.LogRecord) -> None:
                    original_emit(record)
                    if hasattr(console_handler, "stream") and hasattr(
                        console_handler.stream, "flush"
                    ):
                        console_handler.stream.flush()

                console_handler.emit = flush_emit  # type: ignore[method-assign]

            if not _config["async_mode"]:
                logger.addHandler(console_handler)
            all_handlers.append(console_handler)  # Handle file output
        if "file" in handlers_list:
            # Create full path with directory if specified
            if isinstance(_config["log_directory"], str) and _config["log_directory"]:
                full_path = os.path.join(
                    str(_config["log_directory"]), os.path.basename(str(_config["file_path"]))
                )
            else:
                full_path = str(_config["file_path"])

            # Ensure parent directory exists
            os.makedirs(
                os.path.dirname(os.path.abspath(full_path)), exist_ok=True
            )  # Use FormattedFileHandler if visual_mode is enabled
            try:
                if _config["visual_mode"]:
                    # Import here to avoid circular imports
                    from .handlers.handlers import FormattedFileHandler

                    file_handler: logging.Handler = FormattedFileHandler(
                        filename=full_path,
                        mode="a",
                        encoding="utf-8",  # Always use UTF-8 for file output
                        pretty=True,
                        use_symbols=bool(_config.get("use_symbols", False)),
                        use_indent=bool(_config.get("use_indent", False)),
                        align_columns=bool(_config.get("align_columns", False)),
                        level=cast(Union[int, str], _config["level"]),
                    )
                else:
                    # Use standard file handler
                    file_handler = logging.FileHandler(full_path, encoding="utf-8")
                    file_handler.setFormatter(
                        logging.Formatter(
                            fmt=str(_config["format"]), datefmt=str(_config["date_format"])
                        )
                    )

                if not _config["async_mode"]:
                    logger.addHandler(file_handler)
                all_handlers.append(file_handler)  # Handle JSON output
            except (PermissionError, OSError) as e:
                # Log the error and fall back to console only
                print(f"LogEverything: Error creating file handler: {e}", file=sys.stderr)
                # Ensure we have at least console output in this case
                if "console" not in handlers_list:
                    console_handler = logging.StreamHandler(sys.stdout)
                    formatter = logging.Formatter(
                        fmt=str(_config["format"]), datefmt=str(_config["date_format"])
                    )
                    console_handler.setFormatter(formatter)
                    console_handler.setLevel(cast(Union[int, str], _config["level"]))

                    # Force immediate flushing to prevent print/log ordering issues
                    original_emit = console_handler.emit

                    def flush_emit(record: logging.LogRecord) -> None:
                        original_emit(record)
                        if hasattr(console_handler, "stream") and hasattr(
                            console_handler.stream, "flush"
                        ):
                            console_handler.stream.flush()

                    console_handler.emit = flush_emit  # type: ignore[method-assign]

                    logger.addHandler(console_handler)
        if "json" in handlers_list:
            # Import json handler only when needed
            from .handlers.handlers import JSONHandler

            # Create full path with directory if specified
            if isinstance(_config["log_directory"], str) and _config["log_directory"]:
                json_path = os.path.join(
                    str(_config["log_directory"]),
                    os.path.basename(str(_config["file_path"])).replace(".log", ".json"),
                )
            else:
                json_path = str(_config["file_path"]).replace(".log", ".json")

            json_handler = JSONHandler(str(json_path))

            if not _config["async_mode"]:
                logger.addHandler(json_handler)
            all_handlers.append(json_handler)

        # Set up AsyncQueueHandler if async_mode is enabled
        if _config["async_mode"] and all_handlers:
            # Import AsyncQueueHandler only when needed
            from .asyncio.async_logging import AsyncQueueHandler, get_pooled_handler

            # Check if logger already has an AsyncQueueHandler to avoid duplicates
            existing_async_handler = None
            for handler in logger.handlers:
                if isinstance(handler, AsyncQueueHandler):
                    existing_async_handler = handler
                    break

            if existing_async_handler:
                # Update existing handler with new target handlers
                existing_async_handler.target_handlers = all_handlers
            else:
                # Get a reusable handler from pool or create new one
                try:
                    async_handler = get_pooled_handler(
                        queue_size=safe_int(_config["async_queue_size"], 1000),
                        target_handlers=all_handlers,
                        flush_level=safe_int(_config["async_flush_level"], logging.CRITICAL),
                        flush_interval=safe_float(_config["async_flush_interval"], 1.0),
                    )
                except NameError:
                    # Fallback if pool functions not available
                    async_handler = AsyncQueueHandler(
                        queue_size=safe_int(_config["async_queue_size"], 1000),
                        target_handlers=all_handlers,
                        flush_level=safe_int(_config["async_flush_level"], logging.CRITICAL),
                        flush_interval=safe_float(_config["async_flush_interval"], 1.0),
                    )

                # Add the AsyncQueueHandler to the logger
                logger.addHandler(async_handler)

    # Initialize thread-local context
    _initialize_context()

    # Setup print capturing if enabled
    if _config.get("capture_print", False):
        # Import here to avoid circular imports
        from .capture.print_capture import disable_print_capture, enable_print_capture

        # First disable any existing print capture to ensure clean state
        disable_print_capture()

        # Enable print capturing with configured settings and safe type casting
        print_logger = str(_config.get("print_logger_name", "print"))
        print_level = safe_int(_config.get("print_level"), logging.INFO)
        print_prefix = str(_config.get("print_prefix", "[PRINT] "))

        enable_print_capture(
            logger_name=print_logger,
            level=print_level,
            prefix=print_prefix,
        )
    else:
        # Ensure print capture is disabled if it was previously enabled
        try:
            from .capture.print_capture import disable_print_capture

            disable_print_capture()
        except ImportError:
            pass  # Module not loaded yet

    # Setup external logger integration if enabled
    if integrate_external_loggers is not None:
        _config["integrate_external_loggers"] = bool(integrate_external_loggers)

    if external_logger_level is not None:
        if isinstance(external_logger_level, str):
            _config["external_logger_level"] = getattr(
                logging, external_logger_level.upper(), _config["level"]
            )
        else:
            _config["external_logger_level"] = safe_int(
                external_logger_level, safe_int(_config["level"], logging.INFO)
            )

    # If external logger integration is enabled, configure common third-party loggers
    if _config.get("integrate_external_loggers", False):
        # Import here to avoid circular imports
        from .external import configure_common_loggers

        # Configure common third-party loggers
        configured_loggers = configure_common_loggers()

        if configured_loggers:
            logger.debug(f"Integrated with external loggers: {', '.join(configured_loggers)}")

    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False

    # Set the thread-local indentation preference based on current configuration
    # This allows each thread/logger to have its own indentation style
    current_use_symbols = _config.get("use_symbols", False)
    set_context_use_symbols(bool(current_use_symbols))

    return logger


def configure(
    level: Optional[Union[int, str]] = None,
    format: Optional[str] = None,
    date_format: Optional[str] = None,
    log_entry_exit: Optional[bool] = None,
    log_arguments: Optional[bool] = None,
    log_return_values: Optional[bool] = None,
    beautify: Optional[bool] = None,
    indent_level: Optional[int] = None,
    handlers: Optional[List[Union[str, logging.Handler]]] = None,
    logger_name: Optional[str] = None,
    capture_print: Optional[bool] = None,
    print_logger_name: Optional[str] = None,
    print_level: Optional[int] = None,
    print_prefix: Optional[str] = None,
    visual_mode: Optional[bool] = None,
    use_symbols: Optional[bool] = None,
    use_indent: Optional[bool] = None,
    align_columns: Optional[bool] = None,
    color_theme: Optional[str] = None,
    async_mode: Optional[bool] = None,
    async_queue_size: Optional[int] = None,
    async_flush_level: Optional[Union[int, str]] = None,
    async_flush_interval: Optional[float] = None,
    integrate_external_loggers: Optional[bool] = None,
    external_logger_level: Optional[Union[int, str]] = None,
    _internal: bool = False,
) -> Dict[str, Any]:
    """
    Configure the logging system.

    Args:
        level: Logging level (e.g., DEBUG, INFO).
        format: Log format string (e.g., '%(asctime)s - %(name)s - %(levelname)s - %(message)s').
        date_format: Date format string for timestamps (e.g., '%Y-%m-%d %H:%M:%S').
        log_entry_exit: Whether to log function entry and exit.
        log_arguments: Whether to log function arguments.
        log_return_values: Whether to log function return values.
        beautify: Whether to beautify logs with visual elements.
        indent_level: Indentation level for beautified logs.
        handlers: List of handlers to use (e.g., ["console", "file"]).
        logger_name: Name of the logger to configure.
        capture_print: Whether to capture print statements.
        print_logger_name: Logger name for captured print statements.
        print_level: Logging level for captured print statements.
        print_prefix: Prefix for captured print statements.
        visual_mode: Enable visual formatting with symbols and colors.
        use_symbols: Use Unicode symbols for log levels.
        use_indent: Use visual indentation with box drawing.
        align_columns: Align log columns for better readability.
        color_theme: Color theme for visual formatting
            ('default', 'pastel', 'bold', 'monochrome').
        async_mode: Enable asynchronous logging (default: False).
        async_queue_size: Maximum size of the async logging queue (default: 1000).
        async_flush_level: Log level that triggers immediate flush (default: CRITICAL).
        async_flush_interval: Interval in seconds for flushing the async queue
            (default: 1.0).
        integrate_external_loggers: Whether to integrate with third-party loggers.
        external_logger_level: Logging level for external loggers.

    Returns:
        A dictionary with the updated configuration.

    .. deprecated::
        Use ``Logger().configure()`` instead. This function will be removed in a future version.
    """
    if not _internal:
        import warnings

        warnings.warn(
            "configure() is deprecated. Use Logger().configure() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    global _config  # noqa: F824

    # Update configuration with provided values
    if level is not None:
        old_level = _config.get("level")
        if isinstance(level, str):
            _config["level"] = getattr(logging, level.upper(), logging.INFO)
        else:
            _config["level"] = safe_int(level, logging.INFO)

        # Update all existing loggers with the new level
        new_level = _config["level"] if isinstance(_config["level"], int) else logging.INFO
        if old_level != new_level:
            # Update the main logger
            logger.setLevel(new_level)
            # Update all cached loggers
            for cached_logger in _logger_cache.values():
                cached_logger.setLevel(new_level)

    if log_entry_exit is not None:
        _config["log_entry_exit"] = log_entry_exit

    if log_arguments is not None:
        _config["log_arguments"] = log_arguments

    if log_return_values is not None:
        _config["log_return_values"] = log_return_values

    if beautify is not None:
        _config["beautify"] = beautify

    if format is not None:
        _config["format"] = format

    if date_format is not None:
        _config["date_format"] = date_format

    if indent_level is not None:
        _config["indent_level"] = indent_level

    if handlers is not None:
        _config["handlers"] = handlers

    if logger_name is not None:
        _config["logger_name"] = logger_name

    if print_logger_name is not None:
        _config["print_logger_name"] = print_logger_name

    if print_level is not None:
        _config["print_level"] = print_level

    if print_prefix is not None:
        _config["print_prefix"] = print_prefix

    # Handle visual formatting options
    if visual_mode is not None:
        _config["visual_mode"] = visual_mode

    if use_symbols is not None:
        _config["use_symbols"] = use_symbols

    if use_indent is not None:
        _config["use_indent"] = use_indent

    if align_columns is not None:
        _config["align_columns"] = align_columns

    if color_theme is not None:
        _config["color_theme"] = color_theme

    # Configure the unified indent manager with updated settings
    configure_indent_manager(_config)

    # Handle async-specific configurations
    if async_mode is not None:
        _config["async_mode"] = bool(async_mode)
    if async_queue_size is not None:
        _config["async_queue_size"] = safe_int(async_queue_size, 1000)
    if async_flush_level is not None:
        if isinstance(async_flush_level, str):
            _config["async_flush_level"] = getattr(
                logging, async_flush_level.upper(), logging.CRITICAL
            )
        else:
            _config["async_flush_level"] = safe_int(async_flush_level, logging.CRITICAL)
    if async_flush_interval is not None:
        try:
            _config["async_flush_interval"] = float(async_flush_interval)
        except (ValueError, TypeError):
            _config["async_flush_interval"] = 1.0

    # Ensure logger level is applied to the root logger with proper type casting
    if level is not None:
        logger_level = cast(Union[int, str], _config["level"])
        logging.getLogger().setLevel(logger_level)
        logger.setLevel(logger_level)

    # Setup print capturing if enabled
    if capture_print is not None:
        _config["capture_print"] = capture_print
        if capture_print:
            from .capture.print_capture import disable_print_capture, enable_print_capture

            # Get config values with proper type casting
            log_name = str(print_logger_name or _config["print_logger_name"])
            log_level = safe_int(
                print_level if print_level is not None else _config["print_level"], logging.INFO
            )
            log_prefix = str(print_prefix or _config["print_prefix"])

            enable_print_capture(
                logger_name=log_name,
                level=log_level,
                prefix=log_prefix,
            )

        else:
            from .capture.print_capture import disable_print_capture

            disable_print_capture()  # Handle external logger integration
    if integrate_external_loggers is not None:
        _config["integrate_external_loggers"] = integrate_external_loggers

        if integrate_external_loggers:
            # Import here to avoid circular imports
            from .external import configure_common_loggers

            # Configure or reconfigure common third-party loggers
            configured_loggers = configure_common_loggers()
            if configured_loggers:
                logger.debug(f"Integrated with external loggers: {', '.join(configured_loggers)}")

    if external_logger_level is not None:
        if isinstance(external_logger_level, str):
            _config["external_logger_level"] = getattr(
                logging, external_logger_level.upper(), _config["level"]
            )
        else:
            _config["external_logger_level"] = safe_int(
                external_logger_level, safe_int(_config["level"], logging.INFO)
            )

    # If async mode changes, we need to reconfigure the handlers
    if async_mode is not None and handlers is not None:
        setup_logging(handlers=handlers, async_mode=async_mode, _internal=True)

    return _config


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for the specified name with smart isolation.

    Args:
        name: The name for the logger

    Returns:
        logging.Logger: The logger instance
    """
    # Ensure context is properly isolated only when needed
    _initialize_context()

    if name is None:
        return logger

    # Use isolation ID in cache key only for concurrent environments to prevent cross-contamination
    isolation_suffix = ""
    if _is_concurrent() and hasattr(_context, "isolation_id"):
        isolation_suffix = f"_iso_{_context.isolation_id}"

    cache_key = f"logeverything.{name}{isolation_suffix}"
    if cache_key in _logger_cache:
        return _logger_cache[cache_key]

    # Create and cache the logger
    new_logger = logging.getLogger(cache_key)
    _logger_cache[cache_key] = new_logger
    return new_logger


def register_logger(name: str, logger_instance: Any) -> None:
    """
    Register an active LogEverything Logger instance.

    This is called automatically when a Logger is created and allows decorators
    to find and use configured loggers.

    Args:
        name: The logger name
        logger_instance: The Logger instance
    """
    global _active_loggers_version
    _active_loggers[name] = logger_instance
    _active_loggers_version += 1


def unregister_logger(name: str) -> None:
    """
    Unregister an active LogEverything Logger instance.

    Args:
        name: The logger name to unregister
    """
    global _active_loggers_version
    _active_loggers.pop(name, None)
    _active_loggers_version += 1


def get_active_loggers() -> Dict[str, Any]:
    """
    Get all currently active LogEverything Logger instances.

    Returns:
        Dict mapping logger names to Logger instances
    """
    return _active_loggers.copy()


def find_logger_for_decorator(
    requested_name: Optional[str] = None, caller_info: Optional[str] = None
) -> Any:
    """
    Find an appropriate logger for decorator usage.

    This function implements the smart logger selection logic for decorators:
    1. If requested_name is provided, try to find that specific logger
    2. If no specific logger requested but loggers exist, pick the first available
    3. Check for standard Python loggers with handlers as fallback
    4. If no loggers exist, create a temporary one

    Args:
        requested_name: Optional specific logger name to find
        caller_info: Optional caller information for unique warning identification

    Returns:
        Logger instance to use

    Raises:
        ValueError: If a specific logger was requested but not found
    """
    if requested_name:
        # User specifically requested a logger by name
        if requested_name in _active_loggers:
            return _active_loggers[requested_name]

        # Enhanced: Check for AsyncLogger instances with the requested name
        # Look through all registered loggers to find async loggers too
        for logger_name, logger_instance in _active_loggers.items():
            if hasattr(logger_instance, "_name") and logger_instance._name == requested_name:
                return logger_instance
            # Also check if the logger's actual name matches (without prefixes)
            if hasattr(logger_instance, "name"):
                actual_name = logger_instance.name
                if actual_name.endswith(f".{requested_name}") or actual_name == requested_name:
                    return logger_instance

        # Also check if it's a standard Python logger with handlers
        std_logger = logging.getLogger(requested_name)
        if std_logger.handlers or std_logger.level != logging.NOTSET:
            # Return a proxy that uses the standard logger
            return _create_standard_logger_proxy(std_logger)

        available_names = list(_active_loggers.keys())
        close_matches = difflib.get_close_matches(requested_name, available_names, n=3, cutoff=0.4)
        suggestion = (
            f" Did you mean: {', '.join(repr(m) for m in close_matches)}?" if close_matches else ""
        )
        raise ValueError(
            f"Decorator requested logger '{requested_name}' but it was not found. "
            f"Available loggers: {available_names or 'None'}.{suggestion} "
            f"Hint: Make sure Logger('{requested_name}') is created before "
            f"the decorated function is called."
        )

    if _active_loggers:
        # Loggers exist but none specifically requested
        # Pick the first available logger and inform user
        first_logger_name = next(iter(_active_loggers))
        first_logger = _active_loggers[first_logger_name]

        # Print helpful message to console (not through logging to avoid recursion)
        # Only show warning once per unique decorator location
        warning_key = f"{caller_info or 'unknown'}:{first_logger_name}"
        if warning_key not in _warned_decorator_locations:
            if len(_warned_decorator_locations) > 1000:
                _warned_decorator_locations.clear()
            _warned_decorator_locations.add(warning_key)
            available_names = list(_active_loggers.keys())
            logging.getLogger("logeverything").debug(
                f"Auto-selected logger '{first_logger_name}' "
                f"(available: {available_names}). "
                f"Use @log(using='{first_logger_name}') to be explicit."
            )

        return first_logger

    # Check for standard Python loggers with handlers as fallback
    # Only use this fallback if we have a specifically configured logger
    # (not just a default empty logger)
    for logger_name in ["test_basics", "logeverything", "test"]:
        std_logger = logging.getLogger(logger_name)
        if std_logger.handlers and std_logger.level != logging.NOTSET:
            logging.getLogger("logeverything").debug(
                f"Decorator: No Logger instances configured, "
                f"using standard Python logger '{logger_name}'."
            )
            return _create_standard_logger_proxy(std_logger)

    # Check root logger only if it has explicit configuration
    root_logger = logging.getLogger()
    # Skip pytest's internal handlers and null handlers
    real_handlers = [
        h
        for h in root_logger.handlers
        if not (
            h.__class__.__name__ in ["_LiveLoggingNullHandler", "LogCaptureHandler", "_FileHandler"]
            or (
                hasattr(h, "stream")
                and hasattr(h.stream, "name")
                and h.stream.name in ["\\\\" + ".\\nul", "/dev/null"]
            )
            or h.__class__.__name__.endswith("NullHandler")
        )
    ]
    if real_handlers and (root_logger.level != logging.WARNING or len(real_handlers) > 1):
        # Root logger has non-default configuration, use it
        logging.getLogger("logeverything").debug(
            "Decorator: No Logger instances configured, " "using standard Python logger 'root'."
        )
        return _create_standard_logger_proxy(root_logger)

    # No loggers configured at all - create temporary one
    logging.getLogger("logeverything").debug(
        "Decorator: No loggers configured. Creating temporary logger with default settings."
    )

    # Import here to avoid circular imports
    from .logger import Logger

    temp_logger = Logger("decorator_temp", auto_setup=True)

    # Register it temporarily so other decorators can use it
    register_logger("decorator_temp", temp_logger)

    return temp_logger


def _create_standard_logger_proxy(std_logger: logging.Logger) -> Any:
    """Create a proxy object that makes a standard Python logger work with our decorator system."""

    class StandardLoggerProxy:
        def __init__(self, logger: logging.Logger) -> None:
            self._logger = logger
            self.name = logger.name

        def info(self, message: str, *args: Any, **kwargs: Any) -> None:
            self._logger.info(message, *args, **kwargs)

        def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
            self._logger.debug(message, *args, **kwargs)

        def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
            self._logger.warning(message, *args, **kwargs)

        def error(self, message: str, *args: Any, **kwargs: Any) -> None:
            self._logger.error(message, *args, **kwargs)

        def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
            self._logger.critical(message, *args, **kwargs)

        def isEnabledFor(self, level: int) -> bool:
            return self._logger.isEnabledFor(level)

        def getEffectiveLevel(self) -> int:
            return self._logger.getEffectiveLevel()

    return StandardLoggerProxy(std_logger)


# Duplicate functions removed - already defined earlier in the file


def get_current_indent() -> str:
    """
    Get the current indentation string based on the execution context.

    Returns:
        str: The indentation string

    Note: This function now delegates to the unified IndentManager system.
    """
    return _new_get_current_indent()


def increment_indent() -> None:
    """
    Increase the indentation level for the current execution context.

    Note: This function now delegates to the unified IndentManager system.
    """
    _new_increment_indent()


def decrement_indent() -> None:
    """
    Decrease the indentation level for the current execution context.

    Note: This function now delegates to the unified IndentManager system.
    """
    _new_decrement_indent()


def push_function(func_name: str) -> None:
    """
    Add a function to the execution stack.

    Args:
        func_name: The name of the function
    """
    if not hasattr(_context, "function_stack"):
        _initialize_context()
    _context.function_stack.append(func_name)


def pop_function() -> Optional[str]:
    """
    Remove the most recently added function from the execution stack.

    Returns:
        The function name that was removed, or None if the stack was empty
    """
    if not hasattr(_context, "function_stack"):
        _initialize_context()
    if hasattr(_context, "function_stack") and _context.function_stack:
        func = _context.function_stack.pop()
        return str(func) if func is not None else None
    return None


def get_execution_id() -> str:
    """
    Get the current execution ID (process-thread ID).

    Returns:
        str: The execution ID
    """
    if not hasattr(_context, "execution_id"):
        _initialize_context()
    if hasattr(_context, "execution_id"):  # Check again after initializing
        return str(_context.execution_id)  # Explicitly cast to string
    return f"{os.getpid()}-{threading.get_ident()}"  # Fallback


def get_function_stack() -> List[str]:
    """
    Get the current function call stack.

    Returns:
        List[str]: The function call stack
    """
    if not hasattr(_context, "function_stack"):
        _initialize_context()
    if hasattr(_context, "function_stack"):  # Check again after initializing
        return [str(func) for func in _context.function_stack]  # Ensure all elements are strings
    return []  # Return empty list as fallback


# Configuration validation improvements
def _validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize configuration options with better error messages.

    Args:
        config: Configuration dictionary to validate

    Returns:
        Validated and sanitized configuration

    Raises:
        ValueError: If configuration is invalid with helpful message
    """
    validated = config.copy()

    # Validate log level
    if "level" in validated:
        level = validated["level"]
        if isinstance(level, str):
            level_upper = level.upper()
            if level_upper not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                raise ValueError(
                    f"Invalid log level '{level}'. Must be one of: "
                    "DEBUG, INFO, WARNING, ERROR, CRITICAL"
                )
            validated["level"] = getattr(logging, level_upper)
        elif not isinstance(level, int):
            raise ValueError(f"Log level must be string or int, got {type(level)}")

    # Validate handlers
    if "handlers" in validated and validated["handlers"]:
        handlers = validated["handlers"]
        if isinstance(handlers, str):
            handlers = [handlers]

        valid_handlers = ["console", "file", "json", "async_queue"]
        for handler in handlers:
            if isinstance(handler, str):
                handler_type = handler.split(":")[0]
                if handler_type not in valid_handlers:
                    raise ValueError(
                        f"Invalid handler type '{handler_type}'. "
                        f"Valid types: {', '.join(valid_handlers)}"
                    )

    # Validate boolean options
    bool_options = [
        "log_entry_exit",
        "log_arguments",
        "log_return_values",
        "beautify",
        "capture_print",
        "visual_mode",
        "async_mode",
    ]
    for option in bool_options:
        if option in validated and not isinstance(validated[option], bool):
            raise ValueError(f"Option '{option}' must be boolean, got {type(validated[option])}")

    # Validate numeric options
    if "indent_level" in validated:
        indent = validated["indent_level"]
        if not isinstance(indent, int) or indent < 0:
            raise ValueError("indent_level must be a non-negative integer")

    if "max_arg_length" in validated:
        max_len = validated["max_arg_length"]
        if not isinstance(max_len, int) or max_len < 1:
            raise ValueError("max_arg_length must be a positive integer")

    return validated


# Memory management utilities
_cleanup_threshold = 1000  # Max cache size before cleanup
_last_cleanup = 0.0


def _cleanup_caches_if_needed() -> None:
    """Clean up caches periodically to prevent memory leaks."""
    global _last_cleanup
    import time

    current_time = time.time()

    # Clean up every 5 minutes or when cache is too large
    if current_time - _last_cleanup > 300 or len(_logger_cache) > _cleanup_threshold:
        # Keep only recent entries (simple LRU-like cleanup)
        if len(_logger_cache) > _cleanup_threshold // 2:
            # Remove half the cache (oldest entries)
            cache_items = list(_logger_cache.items())
            keep_items = cache_items[-_cleanup_threshold // 2 :]
            _logger_cache.clear()
            _logger_cache.update(keep_items)

        # Clean up indent cache
        if len(_indent_cache) > 100:
            _indent_cache.clear()

        _last_cleanup = current_time


def get_memory_usage() -> Dict[str, int]:
    """
    Get current memory usage statistics for LogEverything.

    Returns:
        Dictionary with cache sizes and memory usage info
    """
    return {
        "logger_cache_size": len(_logger_cache),
        "indent_cache_size": len(_indent_cache),
        "process_contexts": len(_get_process_context()),
        "isolation_id": (
            getattr(_context, "isolation_id", 0) if hasattr(_context, "isolation_id") else 0
        ),
    }
