"""
Base Logger Interface for LogEverything

This module provides the base logger class that all other loggers inherit from,
ensuring a consistent API and enabling extensibility.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Union


class BaseLogger(ABC):
    """
    Base logger class that provides the foundation for all LogEverything loggers.

    This abstract base class defines the common interface and behavior that all
    loggers must implement, ensuring consistency and enabling extensibility.

    Users can inherit from this class to create custom logger implementations::

        class CustomLogger(BaseLogger):
            def __init__(self, name: str):
                super().__init__(name)
                # Custom initialization

            def _log_message(self, level, message, *args, **kwargs):
                # Custom logging implementation
                pass
    """

    # Cached import references to avoid per-call import overhead
    _get_current_indent: Any = None
    _colorama_fore: Any = None
    _colorama_style: Any = None
    _colorama_checked = False

    def __init__(self, name: str):
        """
        Initialize the base logger.

        Args:
            name: The name of the logger
        """
        self._name = name
        self._logger = logging.getLogger(name)
        self._config: Dict[str, Any] = {}
        self._initialized = False

        # Common attributes for user/system tracking and context
        self._user_created: bool = True  # Flag to track if this is a user-created logger
        self._context: Dict[str, Any] = {}  # Context variables for bound logging
        self._options: Dict[str, Any] = {}  # Logging options
        self._is_registered: bool = False  # Track if this logger is registered

    @abstractmethod
    def configure(self, **kwargs: Any) -> "BaseLogger":
        """
        Configure the logger with the specified parameters.

        This method must be implemented by subclasses to handle
        logger-specific configuration.

        Args:
            **kwargs: Configuration parameters

        Returns:
            Self for method chaining
        """
        pass

    @abstractmethod
    def _log_message(self, level: int, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Internal method to handle the actual logging.

        This method must be implemented by subclasses to define
        how messages are actually logged.

        Args:
            level: Logging level
            message: Message to log
            *args: Additional arguments
            **kwargs: Additional keyword arguments
        """
        pass

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        self._log_message(logging.DEBUG, message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        self._log_message(logging.INFO, message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        self._log_message(logging.WARNING, message, *args, **kwargs)

    def warn(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Alias for warning."""
        self.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self._log_message(logging.ERROR, message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        self._log_message(logging.CRITICAL, message, *args, **kwargs)

    def fatal(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Alias for critical."""
        self.critical(message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an exception with traceback."""
        kwargs.setdefault("exc_info", True)
        self.error(message, *args, **kwargs)

    def log(self, level: int, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a message at the specified level."""
        self._log_message(level, message, *args, **kwargs)

    def _mark_as_system_created(self) -> "BaseLogger":
        """
        Mark this logger as system-created (not user-created).

        System-created loggers are automatically cleaned up when used as context managers.
        User-created loggers are not cleaned up automatically.

        Returns:
            Self for method chaining
        """
        self._user_created = False
        return self

    def _register_logger(self) -> None:
        """Register this logger instance for decorator usage."""
        try:
            # Import here to avoid circular imports
            from ..core import register_logger

            register_logger(self._name, self)
            self._is_registered = True  # Mark as registered
        except ImportError:
            # Ignore if core module is not available
            pass

    def _unregister_logger(self) -> None:
        """Unregister this logger from the global registry."""
        # Only unregister if this logger was actually registered
        if not getattr(self, "_is_registered", False):
            return

        try:
            # Import here to avoid circular imports during cleanup
            from ..core import unregister_logger

            if hasattr(self, "_name") and self._name:
                unregister_logger(self._name)
                self._is_registered = False  # Mark as unregistered
        except (ImportError, AttributeError):
            # Ignore errors during cleanup - Python might be shutting down
            pass

    def _format_message_with_context(self, message: str) -> str:
        """Format message with bound context and indentation if available."""
        # First, get the current indentation (cached import)
        current_indent = ""
        if BaseLogger._get_current_indent is None:
            try:
                from ..core import get_current_indent

                BaseLogger._get_current_indent = get_current_indent
            except (ImportError, AttributeError):
                BaseLogger._get_current_indent = lambda: ""
        try:
            current_indent = BaseLogger._get_current_indent()
        except (KeyError, TypeError):
            pass

        # Apply bound context if available
        if hasattr(self, "_context") and self._context:
            context_str = " | ".join(f"{k}={v}" for k, v in self._context.items())

            # Colorize the context brackets (cached import)
            if not BaseLogger._colorama_checked:
                try:
                    from colorama import Fore, Style

                    BaseLogger._colorama_fore = Fore
                    BaseLogger._colorama_style = Style
                except (ImportError, AttributeError):
                    pass
                BaseLogger._colorama_checked = True

            if BaseLogger._colorama_fore is not None:
                colored_context = (
                    f"{BaseLogger._colorama_fore.CYAN}[{context_str}]"
                    f"{BaseLogger._colorama_style.RESET_ALL}"
                )
                formatted_message = f"{current_indent}{colored_context} {message}"
            else:
                formatted_message = f"{current_indent}[{context_str}] {message}"
        else:
            # For regular messages, just apply current indentation
            formatted_message = f"{current_indent}{message}" if current_indent else message

        return formatted_message

    def _log_context_boundary(self, level: int, message: str) -> None:
        """
        Log a context boundary message without bound context formatting.

        This is used for context manager symbols (┌─► and └─◄) which should
        not include bound context data to avoid visual clutter.
        """
        # Get current indentation but skip bound context formatting
        current_indent = ""
        try:
            from ..core import get_current_indent

            current_indent = get_current_indent()
        except (ImportError, AttributeError, KeyError, TypeError):
            pass

        # Add color to context symbols for better visibility
        colored_message = self._colorize_context_message(message)

        # Format with indentation only, no bound context
        formatted_message = (
            f"{current_indent}{colored_message}" if current_indent else colored_message
        )

        # Log directly without going through _format_message_with_context
        self._logger.log(level, formatted_message)

    def _colorize_context_message(self, message: str) -> str:
        """
        Add color to context boundary messages for better readability.

        Args:
            message: The context message (e.g., "┌─► Context Name")

        Returns:
            Colored message string
        """
        try:
            import colorama
            from colorama import Fore, Style

            # Initialize colorama if not already done
            colorama.init()

            # Use a pleasant blue-green color for context symbols
            # This makes them distinct from regular log levels
            if "┌─►" in message or "└─◄" in message:
                return f"{Fore.CYAN}{Style.BRIGHT}{message}{Style.RESET_ALL}"
            else:
                return message

        except ImportError:
            # Fallback without colors if colorama is not available
            return message

    @abstractmethod
    def _create_bound_logger(self, **kwargs: Any) -> "BaseLogger":
        """
        Create a bound logger instance. Must be implemented by subclasses.

        Bound loggers should share the same name and underlying logger
        as the parent, with only context data being different and additive.

        Args:
            **kwargs: Context variables to bind

        Returns:
            New bound logger instance with merged context
        """
        pass

    def bind(self, **kwargs: Any) -> "BaseLogger":
        """
        Create a new logger instance with bound context data.

        Following Loguru-style binding: bound loggers share the same name
        and underlying logger, with only context data being additive.
        This avoids registry pollution and maintains clean logger naming.

        Args:
            **kwargs: Context data to bind

        Returns:
            New logger instance with merged context (same name, additive context)
        """
        # Create bound logger using subclass implementation
        # Note: No hierarchical naming - bound loggers share the same name
        bound_logger = self._create_bound_logger(**kwargs)

        # Mark bound loggers as system-created (temporary)
        bound_logger._mark_as_system_created()

        return bound_logger

    def __enter__(self) -> "BaseLogger":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Context manager exit.

        Only closes and cleans up system-created loggers.
        User-created loggers are left intact.
        """
        if not getattr(self, "_user_created", True):  # Default to user_created=True for safety
            self._cleanup()

    @abstractmethod
    def _cleanup(self) -> None:
        """
        Clean up logger resources. Must be implemented by subclasses.

        This should handle logger-specific cleanup (sync vs async).
        For async loggers, this should be a synchronous wrapper that
        can be called from __del__.
        """
        pass

    def __del__(self) -> None:
        """
        Cleanup when logger is deleted.

        Unregisters the logger from the global registry to prevent memory leaks
        and stale references in decorator lookups.
        """
        try:
            self._cleanup()
        except Exception:  # nosec B110
            # Ignore errors during cleanup
            pass

    @property
    def level(self) -> int:
        """Get the current logging level."""
        return self._logger.level

    @level.setter
    def level(self, level: Union[int, str]) -> None:
        """Set the logging level."""
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        self._logger.setLevel(level)

    def is_enabled_for(self, level: int) -> bool:
        """Check if logging is enabled for the given level."""
        return self._logger.isEnabledFor(level)

    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        return self._config.copy()

    def __repr__(self) -> str:
        """String representation of the logger."""
        return f"{self.__class__.__name__}(name='{self._name}')"
