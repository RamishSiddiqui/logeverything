"""
External logger integration for the LogEverything library.

This module provides utilities for integrating third-party loggers with LogEverything,
using Python's standard logging mechanisms rather than complex wrapper classes.
"""

import importlib
import logging
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

from ..core import _config, get_logger
from ..handlers.handlers import ConsoleHandler, PrettyFormatter


def _safe_log_level(val: Any, default: int = logging.INFO) -> int:
    """Safely convert a value to a valid log level."""
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        level: Any = getattr(logging, val.upper(), None)
        if level is not None and isinstance(level, int):
            return int(level)  # Explicit cast to int
    return default


def check_dependency(module_name: str, package_name: Optional[str] = None) -> Tuple[bool, str]:
    """
    Check if an optional dependency is installed.

    Args:
        module_name: The name of the module to import.
        package_name: The name of the package to mention in error messages
            (if different from module_name).

    Returns:
        Tuple of (is_available, message). ``is_available`` is ``True`` if
        the dependency is available; ``message`` is empty when available or
        an error string when not.
    """
    package = package_name or module_name

    try:
        # First check if the module is already imported
        if module_name in sys.modules:
            return True, ""

        # Try to import the module
        importlib.import_module(module_name)
        return True, ""
    except ImportError:
        return False, (
            f"Optional dependency '{package}' not installed. "
            f"Install it with: pip install logeverything[{package.lower()}] "
            f"or pip install {package}"
        )
    except Exception as e:
        # Handle other import errors (like circular imports)
        # Still consider the module available if it's a non-ImportError
        # This handles cases like MLflow's circular import issues
        if module_name in sys.modules:
            return True, ""
        return False, (
            f"Optional dependency '{package}' could not be imported due to error: {e}. "
            f"Install it with: pip install logeverything[{package.lower()}] "
            f"or pip install {package}"
        )


# Module-level state for stdlib interception
_original_root_handlers = None
_intercept_handler = None


class _LogEverythingInterceptHandler(logging.Handler):
    """Handler that routes all stdlib log records through LogEverything formatting."""

    def __init__(self, level=logging.NOTSET, use_pretty_formatter=True):
        super().__init__(level)
        self.use_pretty_formatter = use_pretty_formatter
        if use_pretty_formatter:
            self.setFormatter(PrettyFormatter())

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = sys.stderr if record.levelno >= logging.WARNING else sys.stdout
            try:
                stream.write(msg + "\n")
            except UnicodeEncodeError:
                # Fall back to ASCII-safe output on terminals that can't handle Unicode
                stream.write(msg.encode("ascii", errors="replace").decode("ascii") + "\n")
            stream.flush()
        except Exception:
            self.handleError(record)


def intercept_stdlib(level=None, use_pretty_formatter=True):
    """
    Install a LogEverything handler on the root stdlib logger.
    All stdlib loggers will now use LogEverything's formatting.

    Args:
        level: Logging level (default: uses LogEverything config or INFO)
        use_pretty_formatter: Whether to use PrettyFormatter (default: True)

    Returns:
        The intercept handler (for later removal if needed)
    """
    global _original_root_handlers, _intercept_handler

    root = logging.getLogger()

    # Save original state for restore_stdlib()
    _original_root_handlers = list(root.handlers)

    # Remove existing root handlers
    for h in root.handlers[:]:
        root.removeHandler(h)

    # Install our handler
    _intercept_handler = _LogEverythingInterceptHandler(
        level=level or logging.NOTSET,
        use_pretty_formatter=use_pretty_formatter,
    )
    root.addHandler(_intercept_handler)

    # Set root level
    effective_level = level
    if effective_level is None:
        effective_level = _safe_log_level(_config.get("level", logging.INFO))
    if isinstance(effective_level, str):
        effective_level = getattr(logging, effective_level.upper(), logging.INFO)
    root.setLevel(effective_level)

    return _intercept_handler


def restore_stdlib():
    """Restore the root logger to its state before intercept_stdlib()."""
    global _original_root_handlers, _intercept_handler

    if _original_root_handlers is None:
        return

    root = logging.getLogger()

    # Remove our handler
    for h in root.handlers[:]:
        root.removeHandler(h)

    # Restore originals
    for h in _original_root_handlers:
        root.addHandler(h)

    _original_root_handlers = None
    _intercept_handler = None


def configure_external_logger(
    logger_name: str,
    level: Optional[Union[int, str]] = None,
    use_pretty_formatter: bool = True,
    propagate: bool = False,
) -> logging.Logger:
    """
    Configure a third-party logger to use LogEverything's formatting and handling.

    This function efficiently integrates external loggers with LogEverything's
    configuration without creating complex wrappers or interceptors. It directly
    configures the logger using standard Python logging mechanisms.

    Args:
        logger_name: The name of the logger to configure (e.g., 'langchain', 'mlflow')
        level: The log level to set, or None to use LogEverything's default level
        use_pretty_formatter: Whether to apply LogEverything's pretty formatting
        propagate: Whether to allow the logger to propagate messages to parent loggers

    Returns:
        logging.Logger: The configured logger

    Examples:
        >>> # Configure a third-party logger
        >>> configure_external_logger('langchain', level='DEBUG')
        >>>
        >>> # Configure a logger with propagation to parent loggers
        >>> configure_external_logger('uvicorn.access', propagate=True)
    """
    # Get the external logger
    try:
        external_logger = logging.getLogger(logger_name)
    except Exception as e:
        # This shouldn't happen, but just in case
        get_logger(__name__).error(f"Failed to get logger '{logger_name}': {e}")
        # Create a new logger as a fallback
        external_logger = logging.Logger(logger_name)

    # Determine the level to use - priority: explicit level > external_logger_level > global level
    level_to_use = None
    if level is not None:
        if isinstance(level, str):
            try:
                level_to_use = getattr(logging, level.upper(), None)
                if level_to_use is None:
                    get_logger(__name__).warning(f"Invalid log level '{level}', using INFO instead")
                    level_to_use = logging.INFO
            except Exception:
                get_logger(__name__).warning(
                    f"Failed to parse log level '{level}', using INFO instead"
                )
                level_to_use = logging.INFO
        else:
            level_to_use = level
    elif _config.get("external_logger_level") is not None:
        level_to_use = _safe_log_level(_config.get("external_logger_level"))
    elif _config.get("level") is not None:
        level_to_use = _safe_log_level(_config.get("level"))

    # Set the level if determined
    if level_to_use is not None:
        external_logger.setLevel(level_to_use)

    # Set propagation
    external_logger.propagate = propagate

    # Only manage handlers if not propagating
    # When propagating, we let the parent logger handle the output
    if not propagate:
        # Store existing handlers before removing them (for debugging/auditing)
        existing_handlers = list(external_logger.handlers)

        # Clear existing handlers
        for handler in existing_handlers:
            external_logger.removeHandler(handler)

        # Add appropriate handler with proper formatting
        try:
            if use_pretty_formatter:
                handler = ConsoleHandler()
                handler.setFormatter(PrettyFormatter())
                external_logger.addHandler(handler)
            else:
                # Use a simple console handler
                handler = logging.StreamHandler()
                formatter = logging.Formatter(str(_config.get("format", "%(message)s")))
                handler.setFormatter(formatter)
                external_logger.addHandler(handler)
        except Exception as e:
            # If something goes wrong with our handlers, add a basic one to ensure logging works
            get_logger(__name__).warning(f"Error setting up handlers for '{logger_name}': {e}")
            fallback_handler = logging.StreamHandler()
            fallback_handler.setFormatter(
                logging.Formatter("%(name)s - %(levelname)s - %(message)s")
            )
            external_logger.addHandler(fallback_handler)

    return external_logger


def harmonize_logger_levels(
    level: Optional[Union[int, str]] = None,
    include_root: bool = True,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> Dict[str, int]:
    """
    Set the same logging level for all detected loggers in the application.

    This function helps ensure consistent logging levels across all loggers,
    which is especially useful when integrating with third-party libraries
    that may have their own logging settings.

    Args:
        level: The log level to set for all loggers (None uses LogEverything's level)
        include_root: Whether to include the root logger (default: True)
        include_patterns: List of logger name patterns to include (e.g., ['langchain.*', 'fastapi'])
        exclude_patterns: List of logger name patterns to exclude (e.g., ['werkzeug.*'])

    Returns:
        Dict[str, int]: Dictionary mapping logger names to their previous levels

    Examples:
        >>> # Set all loggers to INFO level
        >>> harmonize_logger_levels('INFO')
        >>>
        >>> # Set all loggers except the root logger to DEBUG
        >>> harmonize_logger_levels('DEBUG', include_root=False)
        >>>
        >>> # Harmonize only specific loggers
        >>> harmonize_logger_levels('WARNING', include_patterns=['uvicorn.*', 'fastapi'])
    """
    # Determine the level value to use
    level_value = None

    if level is not None:
        if isinstance(level, str):
            try:
                level_value = getattr(logging, level.upper(), None)
                if level_value is None:
                    get_logger(__name__).warning(f"Invalid log level '{level}', using INFO instead")
                    level_value = logging.INFO
            except Exception as e:
                get_logger(__name__).warning(
                    f"Failed to parse log level '{level}', using INFO: {e}"
                )
                level_value = logging.INFO
        else:
            level_value = level
    else:
        # No level specified, use LogEverything's config
        level_value = _safe_log_level(_config.get("level", logging.INFO))

    # Store original levels
    original_levels = {}

    # Handle the root logger
    if include_root:
        root = logging.getLogger()
        original_levels[root.name] = root.level
        root.setLevel(level_value)
    # Process include/exclude patterns

    def should_process_logger(name: str) -> bool:
        # If no include patterns, include everything by default
        should_include = include_patterns is None

        # Check include patterns
        if include_patterns:
            for pattern in include_patterns:
                # Simple wildcard handling
                if pattern.endswith(".*"):
                    prefix = pattern[:-2]
                    if name == prefix or name.startswith(prefix + "."):
                        should_include = True
                        break
                elif pattern == name:
                    should_include = True
                    break

        # Check exclude patterns
        if exclude_patterns:
            for pattern in exclude_patterns:
                if pattern.endswith(".*"):
                    prefix = pattern[:-2]
                    if name == prefix or name.startswith(prefix + "."):
                        return False
                elif pattern == name:
                    return False

        return should_include

    # Get all loggers from the manager
    logger_names = list(logging.root.manager.loggerDict.keys())

    # Process each logger
    errors = []
    for name in logger_names:
        try:
            if should_process_logger(name):
                logger = logging.getLogger(name)
                original_levels[name] = logger.level
                logger.setLevel(level_value)
        except Exception as e:
            errors.append(f"Failed to set level for '{name}': {e}")

    # Report any errors
    if errors and len(errors) > 0:
        for error in errors:
            get_logger(__name__).warning(error)

    return original_levels


def configure_common_loggers(
    additional_loggers: Optional[List[Union[str, Tuple[str, str]]]] = None,
    exclude_loggers: Optional[List[str]] = None,
    level: Optional[Union[int, str]] = None,
    use_pretty_formatter: bool = True,
    propagate: bool = False,
    show_warnings: bool = True,
) -> List[str]:
    """
    Automatically configure common third-party loggers.

    Detects and configures common libraries' loggers to use
    LogEverything's formatting for consistent output.

    Args:
        additional_loggers: Additional loggers to configure beyond the built-in list
        exclude_loggers: Loggers to exclude from configuration
        level: The log level to set for all loggers, or None to use the external_logger_level
        use_pretty_formatter: Whether to apply LogEverything's pretty formatting
        propagate: Whether to allow loggers to propagate messages to parent loggers
        show_warnings: Whether to show warnings for missing optional dependencies

    Returns:
        List[str]: The names of the loggers that were configured

    Examples:
        >>> # Configure all detected common loggers
        >>> configure_common_loggers()
        >>>
        >>> # Configure common loggers plus custom ones
        >>> configure_common_loggers(additional_loggers=['my_custom_lib'])
        >>>
        >>> # Configure common loggers except specific ones
        >>> configure_common_loggers(exclude_loggers=['sqlalchemy'])
    """
    # Define common loggers with their associated module checks
    logger_dependencies = [
        # ML/AI Libraries
        ("langchain", "langchain"),
        ("mlflow", "mlflow"),
        ("transformers", "transformers", "transformers"),
        ("pytorch_lightning", "pytorch_lightning", "pytorch-lightning"),
        ("tensorflow", "tensorflow"),
        ("torch", "torch"),
        ("huggingface_hub", "huggingface_hub"),
        # Web Frameworks
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("uvicorn.access", "uvicorn"),
        ("flask", "flask"),
        ("django", "django"),
        ("starlette", "starlette"),
        # Database
        ("sqlalchemy", "sqlalchemy"),
        ("alembic", "alembic"),
        ("pymongo", "pymongo"),
        # Cloud/APIs
        ("boto3", "boto3"),
        ("azure", "azure"),
        ("google", "google"),
        ("requests", "requests"),
        ("urllib3", "urllib3"),
        # Other common libraries
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("matplotlib", "matplotlib"),
        ("plotly", "plotly"),
        ("jupyter", "jupyter"),
    ]

    # Add any additional loggers (as tuples for consistency)
    if additional_loggers:
        for name in additional_loggers:
            if isinstance(name, str):
                logger_dependencies.append((name, name))
            else:
                logger_dependencies.append(name)  # Apply exclusions
    if exclude_loggers:
        logger_dependencies = [
            item for item in logger_dependencies if item[0] not in exclude_loggers
        ]
    configured = []
    dependency_warnings = []
    # Determine the log level to use
    # Priority: explicit level > external_logger_level > global level
    level_to_use = level
    if level_to_use is None and _config.get("external_logger_level") is not None:
        external_level = _config.get("external_logger_level")
        if isinstance(external_level, (int, str)):
            level_to_use = external_level

    # Track any errors for debugging
    errors = []

    # Get logger for this module
    local_logger = get_logger(__name__)

    for logger_item in logger_dependencies:
        logger_name = logger_item[0]
        module_name = logger_item[1]
        package_name = logger_item[2] if len(logger_item) > 2 else module_name

        # Check if dependency is available
        is_available, warning = check_dependency(module_name, package_name)
        if not is_available:
            if show_warnings:
                dependency_warnings.append(warning)
            continue

        try:
            # Check if the library is imported (has a logger in the logger dict)
            if logger_name in logging.Logger.manager.loggerDict:
                # Configure with the external_logger_level if specified
                configure_external_logger(
                    logger_name,
                    level=level_to_use,
                    use_pretty_formatter=use_pretty_formatter,
                    propagate=propagate,
                )
                configured.append(logger_name)
        except Exception as e:
            errors.append(f"Failed to configure logger '{logger_name}': {e}")

    # If there were any errors, log them
    if errors and len(errors) > 0:
        for error in errors:
            local_logger.warning(error)

    # Show dependency warnings if any
    if dependency_warnings and show_warnings:
        for warning in dependency_warnings:
            local_logger.info(f"Optional dependency warning: {warning}")

    return configured
