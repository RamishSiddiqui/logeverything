"""
AsyncLogger Interface for LogEverything

This module provides an async-optimized logger interface that leverages
LogEverything's async infrastructure for high-performance async applications.

Example usage::

    from logeverything.asyncio import AsyncLogger

    # Simple usage with automatic async setup
    log = AsyncLogger()
    log.info("Hello, async world!")

    # Advanced usage with async-optimized configuration
    log = AsyncLogger("my_async_app")
    await log.configure(
        level="DEBUG",
        visual_mode=True,
        async_queue_size=5000,
        async_handlers=["console", "file"],
        file_path="async_app.log"
    )

    # Async contextual logging
    async with log.context("Async Data Processing"):
        log.info("Starting async processing")
        await some_async_operation()
        log.debug("Async operation completed")
        log.info("Processing complete")

    # Bound context for structured async logging
    user_log = log.bind(user_id=123, session_id="async-abc-def")
    user_log.info("Async user action performed")
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional, cast

from ..base import BaseLogger
from ..core import get_logger
from .async_logging import (
    AsyncQueueHandler,
    AsyncQuietLoggingContext,
    AsyncTemporaryHandlerContext,
    AsyncVerboseLoggingContext,
    AsyncVisualLoggingContext,
)

# Global flag to track if async auto-detection has been shown
_async_auto_detection_shown = False


class AsyncLogger(BaseLogger):
    """
    An async-optimized logger interface for LogEverything.

    This class provides the same clean interface as Logger but is specifically
    designed for async applications with async-optimized defaults and native
    async context manager support.

    Inherits from BaseLogger to provide a consistent API and enable extensibility.

    Key Features:
        - Automatically enables async_mode=True (no need to specify)
        - Async-first configuration with await logger.configure()
        - Built-in async context managers (async with logger.verbose())
        - Optimized for high-performance async applications
        - AsyncQueueHandler configured by default for non-blocking logging

    Usage:
        Basic async logging::

            logger = AsyncLogger()
            logger.info("This logs asynchronously")

        Async configuration::

            await logger.configure(level="DEBUG", handlers=["file"])

        Async context managers::

            async with logger.verbose():
                logger.debug("Enhanced logging in this context")
    """

    def __init__(
        self,
        name: Optional[str] = None,
        auto_setup: bool = True,
        _register: bool = True,
        **config: Any,
    ) -> None:
        """
        Initialize the AsyncLogger with async-optimized configuration.

        Args:
            name: Logger name (default: automatic based on caller)
            auto_setup: Whether to automatically setup async logging
            _register: Whether to register this logger (internal parameter for bound loggers)
            **config: Configuration options (level, async_queue_size, handlers, etc.)
        """
        self._name = name or "AsyncLogger"
        super().__init__(self._name)  # Initialize BaseLogger with the name
        self._async_handler: Optional[AsyncQueueHandler] = None
        self._is_async: bool = True  # Mark as async logger for smart casting

        # Disable propagation to prevent duplicate logs from parent loggers
        self.logger.propagate = False

        # Register logger name with adaptive column manager for optimal visual alignment
        try:
            from ..handlers.handlers import register_logger_name

            register_logger_name(self._name)
        except ImportError:
            # Fallback in case handlers module isn't available
            pass

        # Auto-attach HierarchyFilter for structured hierarchy fields
        from ..hierarchy import HierarchyFilter

        if not any(isinstance(f, HierarchyFilter) for f in self.logger.filters):
            self.logger.addFilter(HierarchyFilter())

        # Register this logger instance for decorator usage (skip for bound loggers)
        if _register:
            self._register_logger()
            # Also register with the clean name for decorator lookup
            from ..core import register_logger

            register_logger(self._name, self)

        if auto_setup:
            # Apply any passed configuration first
            if config:
                self._auto_configure_sync(**config)
            else:
                # Use intelligent defaults
                self._auto_configure_sync()

    def _translate_convenience_parameters(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate convenience parameters to proper handler configuration.

        Args:
            config: Raw configuration dictionary

        Returns:
            Translated configuration with proper handlers setup
        """
        translated = config.copy()
        handlers_list = translated.get("handlers", [])

        # Handle console convenience parameter
        if translated.get("console") is True:
            if "console" not in handlers_list:
                handlers_list.append("console")
            translated.pop("console", None)

        # Handle json_file convenience parameter
        if "json_file" in translated:
            if "json" not in handlers_list:
                handlers_list.append("json")
            translated.pop("json_file", None)

        # Update handlers if we added any
        if handlers_list and not translated.get("handlers"):
            translated["handlers"] = handlers_list

        return translated

    class CenteredFormatter(logging.Formatter):
        """Custom formatter that centers the levelname field."""

        def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
            # Use standard date format if none provided
            if datefmt is None:
                datefmt = "%Y-%m-%d %H:%M:%S"
            super().__init__(fmt, datefmt)

        def format(self, record: logging.LogRecord) -> str:
            # Store original levelname
            original_levelname = record.levelname
            # Center the levelname in 8 characters
            record.levelname = f"{original_levelname:^8}"
            # Format with centered levelname
            result = super().format(record)
            # Restore original levelname
            record.levelname = original_levelname
            return result

    def _configure_instance(self, **config: Any) -> None:
        """Configure this specific AsyncLogger instance with visual formatting."""
        # Translate convenience parameters
        translated_config = self._translate_convenience_parameters(config)

        # Set level for this logger only
        if "level" in translated_config:
            level = translated_config["level"]
            if isinstance(level, str):
                level = getattr(logging, level.upper(), logging.INFO)
            self.logger.setLevel(level)

        # Check if this is an explicit configure() call with handlers or visual formatting
        explicit_config = any(
            key in translated_config
            for key in [
                "handlers",
                "visual_mode",
                "use_symbols",
                "use_indent",
                "format_type",
                "format",
            ]
        )

        # Check if visual formatting is requested
        visual_formatting = any(
            key in translated_config for key in ["visual_mode", "use_symbols", "use_indent"]
        ) or translated_config.get("visual_mode", False)

        # If visual formatting is requested, we need proper handlers
        if visual_formatting:
            # Clear existing handlers to replace them with visual ones
            if self.logger.handlers:
                self.logger.handlers.clear()

            # Detect platform capabilities to handle Windows console encoding issues
            from .. import core as core_module

            platform_capabilities = core_module.detect_platform_capabilities()

            # Auto-detect if we should force ASCII to prevent encoding errors
            should_force_ascii = translated_config.get("force_ascii", False)
            if not should_force_ascii and not platform_capabilities.get("supports_unicode", True):
                should_force_ascii = True

            # Create EnhancedConsoleHandler with proper platform handling
            from ..handlers.handlers import EnhancedConsoleHandler

            console_handler = EnhancedConsoleHandler(
                use_colors=translated_config.get("use_colors", True),
                color_messages=translated_config.get("color_messages", False),
                use_symbols=translated_config.get("use_symbols", visual_formatting)
                and not should_force_ascii,
                use_indent=translated_config.get("use_indent", visual_formatting),
                align_columns=translated_config.get("align_columns", False),
                color_theme=translated_config.get("color_theme", "default"),
                ascii_only=should_force_ascii,
                level=translated_config.get("level", logging.INFO),
            )
            self.logger.addHandler(console_handler)

        # If explicit config requested but no handlers and no visual, add default
        elif explicit_config and not self.logger.handlers:
            # Create a default console handler for non-visual configuration
            from ..handlers.handlers import ConsoleHandler

            default_handler = ConsoleHandler()
            if "level" in translated_config:
                default_handler.setLevel(translated_config["level"])
            self.logger.addHandler(default_handler)

        # Handle explicit handlers configuration
        elif "handlers" in translated_config:
            handlers_config = translated_config["handlers"]
            self._configure_instance_handlers(handlers_config, **translated_config)

        # Apply additional configuration through core configure for global settings
        # Include visual formatting parameters now since we've handled them at the instance level
        core_config = {
            k: v
            for k, v in translated_config.items()
            if k not in ["handlers"]  # Only exclude handlers, keep visual params for global config
        }

        if core_config:
            # Import here to avoid circular imports
            from ..core import configure as core_configure

            # Valid parameters for core configure function
            valid_params = {
                "level",
                "format",
                "date_format",
                "log_entry_exit",
                "log_arguments",
                "log_return_values",
                "beautify",
                "indent_level",
                "logger_name",
                "capture_print",
                "print_logger_name",
                "print_level",
                "print_prefix",
                "visual_mode",
                "use_symbols",
                "use_indent",
                "align_columns",
                "color_theme",
                "async_mode",
                "async_queue_size",
                "async_flush_level",
                "async_flush_interval",
                "integrate_external_loggers",
                "external_logger_level",
            }

            # Filter out invalid parameters
            filtered_config = {k: v for k, v in core_config.items() if k in valid_params}
            core_configure(_internal=True, **filtered_config)

        # Note: Do NOT override the formatter here - EnhancedConsoleHandler already sets up
        # PrettyFormatter with the right visual formatting (symbols, brackets, etc.)
        # The CenteredFormatter is only needed for basic handlers without visual formatting

    def _configure_instance_handlers(self, handlers_config: Any, **kwargs: Any) -> None:
        """Configure handlers for this AsyncLogger instance only."""
        if not handlers_config:
            return

        # Clear existing handlers if we're replacing them
        self.logger.handlers.clear()

        # Import handlers here to avoid circular imports
        from ..handlers.handlers import ConsoleHandler, FileHandler

        if isinstance(handlers_config, list):
            for handler_spec in handlers_config:
                handler: Any = None

                if isinstance(handler_spec, str):
                    if handler_spec == "console":
                        handler = ConsoleHandler()
                    elif handler_spec == "file":
                        file_path = kwargs.get("file_path", f"{self._name}.log")
                        handler = FileHandler(file_path, encoding="utf-8")
                    else:
                        # Default to console for unknown handler names
                        handler = ConsoleHandler()
                else:
                    # Assume it's a handler object
                    handler = handler_spec

                if handler:
                    # Apply CenteredFormatter to this handler
                    if hasattr(handler, "formatter") and handler.formatter:
                        current_format = handler.formatter._fmt
                        current_datefmt = getattr(handler.formatter, "datefmt", None)
                        if current_format and "levelname" in current_format:
                            handler.setFormatter(
                                self.CenteredFormatter(current_format, current_datefmt)
                            )

                    # Add handler to THIS logger only
                    self.logger.addHandler(handler)

    def _auto_configure_sync(self, **config: Any) -> None:
        """Synchronously configure the logger with async-optimized defaults."""
        global _async_auto_detection_shown

        # Import here to avoid circular imports
        from ..core import _detect_environment, _get_environment_config

        # Detect environment and get appropriate config
        env_type = _detect_environment()
        env_config = _get_environment_config(env_type)

        # Add async-specific optimizations (async_mode is always True for AsyncLogger)
        async_config: Dict[str, Any] = {
            **env_config,
            "async_mode": True,  # AsyncLogger always uses async mode
            **config,  # User config overrides defaults
        }

        # Log auto-detection info at DEBUG level (no stdout spam)
        if not _async_auto_detection_shown:
            _internal_logger = logging.getLogger("logeverything")
            _internal_logger.debug(f"AsyncLogger: Auto-detected environment: {env_type}")
            _internal_logger.debug(
                f"AsyncLogger: Applied async-optimized configuration for {env_type} environment"
            )
            _internal_logger.debug("AsyncLogger: Using high-performance async logging")
            _internal_logger.debug(
                "AsyncLogger: You can override this by specifying a profile "
                "or configuration parameters"
            )
            _async_auto_detection_shown = True

        # Use instance-level configuration for proper formatter handling
        self._configure_instance(**async_config)

    async def _auto_configure(self) -> None:
        """Automatically configure the logger with async-optimized defaults."""
        global _async_auto_detection_shown

        # Import here to avoid circular imports
        from ..core import _detect_environment, _get_environment_config, setup_logging

        # Detect environment and get appropriate config
        env_type = _detect_environment()
        env_config = _get_environment_config(env_type)

        # Add async-specific optimizations (async_mode is always True for AsyncLogger)
        async_config: Dict[str, Any] = {
            **env_config,
            "async_mode": True,  # AsyncLogger always uses async mode
            "async_queue_size": 5000,  # Larger queue for async workloads
            "async_flush_interval": 0.1,  # Faster flush for responsive async apps
        }

        # Log auto-detection info at DEBUG level (no stdout spam)
        if not _async_auto_detection_shown:
            _internal_logger = logging.getLogger("logeverything")
            _internal_logger.debug(f"AsyncLogger: Auto-detected environment: {env_type}")
            _internal_logger.debug(
                f"AsyncLogger: Applied async-optimized configuration for {env_type} environment"
            )
            _internal_logger.debug(
                "AsyncLogger: Using AsyncQueueHandler for high-performance async logging"
            )
            _internal_logger.debug(
                "AsyncLogger: You can override this by specifying a profile "
                "or configuration parameters"
            )
            _async_auto_detection_shown = True

        # Setup logging with async-optimized defaults
        setup_logging(auto_detect_env=False, _internal=True, **async_config)

        # Create and configure async handler
        console_handler = logging.StreamHandler()

        # Ensure proper types for AsyncQueueHandler
        queue_size = async_config.get("async_queue_size", 5000)
        if not isinstance(queue_size, int):
            queue_size = int(queue_size) if queue_size else 5000

        flush_interval = async_config.get("flush_interval", 0.1)
        if not isinstance(flush_interval, (int, float)):
            flush_interval = float(flush_interval) if flush_interval else 0.1

        self._async_handler = AsyncQueueHandler(
            queue_size=queue_size,
            target_handlers=[console_handler],
            flush_interval=flush_interval,
        )

        # Add async handler to logger
        self.logger.addHandler(self._async_handler)

    @property
    def logger(self) -> logging.Logger:
        """Get the underlying Python logger instance."""
        if self._logger is None:
            self._logger = get_logger(self._name)  # type: ignore[unreachable]
        return self._logger

    @property
    def name(self) -> str:
        """Get the logger name without the logeverything prefix."""
        full_name = self.logger.name
        if full_name.startswith("logeverything."):
            return full_name[14:]  # Remove "logeverything." prefix
        return full_name

    def _log_message(self, level: int, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Internal method to handle the actual logging.

        This implements the BaseLogger abstract method.
        """
        message = self._format_message_with_context(message)
        self.logger.log(level, message, *args, **kwargs)

    def _create_bound_logger(self, **kwargs: Any) -> "AsyncLogger":
        """
        Create a bound async logger instance with merged context.

        Bound loggers share the same name and underlying logger,
        with only context data being additive.
        """
        # Create new async logger with the SAME name (no hierarchical naming)
        # Don't auto-setup or register to avoid registry pollution
        bound_logger = AsyncLogger(self._name, auto_setup=False, _register=False)

        # Share the same underlying Python logger and async handler
        bound_logger._logger = self._logger
        bound_logger._async_handler = self._async_handler

        # Merge context: parent context + new context (additive)
        parent_context = getattr(self, "_context", {})
        bound_logger._context = {**parent_context, **kwargs}

        return bound_logger

    def _cleanup(self) -> None:
        """Clean up async logger resources (synchronous wrapper for __del__)."""
        self._unregister_logger()
        if hasattr(self, "_async_handler") and self._async_handler:
            try:
                # Synchronous cleanup of async handler
                self._async_handler.close()
            except Exception:  # nosec B110
                # Ignore errors during cleanup
                pass

    # Standard logging methods (synchronous for compatibility)
    def _filter_logging_kwargs(self, kwargs: dict) -> dict:
        """Filter kwargs to only include those accepted by Python's logging methods."""
        valid_kwargs = {"exc_info", "extra", "stack_info", "stacklevel"}
        return {k: v for k, v in kwargs.items() if k in valid_kwargs}

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        message = self._format_message_with_context(message)
        filtered_kwargs = self._filter_logging_kwargs(kwargs)
        self.logger.log(logging.DEBUG, message, *args, **filtered_kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        message = self._format_message_with_context(message)
        filtered_kwargs = self._filter_logging_kwargs(kwargs)
        self.logger.log(logging.INFO, message, *args, **filtered_kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        message = self._format_message_with_context(message)
        filtered_kwargs = self._filter_logging_kwargs(kwargs)
        self.logger.log(logging.WARNING, message, *args, **filtered_kwargs)

    def warn(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message (alias for warning)."""
        self.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        message = self._format_message_with_context(message)
        filtered_kwargs = self._filter_logging_kwargs(kwargs)
        self.logger.log(logging.ERROR, message, *args, **filtered_kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        message = self._format_message_with_context(message)
        filtered_kwargs = self._filter_logging_kwargs(kwargs)
        self.logger.log(logging.CRITICAL, message, *args, **filtered_kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an exception message with traceback."""
        message = self._format_message_with_context(message)
        kwargs.setdefault("exc_info", True)
        filtered_kwargs = self._filter_logging_kwargs(kwargs)
        self.logger.log(logging.ERROR, message, *args, **filtered_kwargs)

    # Async-specific methods
    async def adebug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Async debug logging (ensures async context is properly handled)."""
        await asyncio.sleep(0)  # Yield control to event loop
        # Separate context data from logging kwargs
        context_data = {
            k: v
            for k, v in kwargs.items()
            if k not in {"exc_info", "extra", "stack_info", "stacklevel"}
        }
        logging_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k in {"exc_info", "extra", "stack_info", "stacklevel"}
        }

        if context_data:
            # Create bound logger with context and use it for logging
            bound_logger = self.bind(**context_data)
            bound_logger.debug(message, *args, **logging_kwargs)
        else:
            self.debug(message, *args, **logging_kwargs)

    async def ainfo(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Async info logging (ensures async context is properly handled)."""
        await asyncio.sleep(0)  # Yield control to event loop
        # Separate context data from logging kwargs
        context_data = {
            k: v
            for k, v in kwargs.items()
            if k not in {"exc_info", "extra", "stack_info", "stacklevel"}
        }
        logging_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k in {"exc_info", "extra", "stack_info", "stacklevel"}
        }

        if context_data:
            # Create bound logger with context and use it for logging
            bound_logger = self.bind(**context_data)
            bound_logger.info(message, *args, **logging_kwargs)
        else:
            self.info(message, *args, **logging_kwargs)

    async def awarning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Async warning logging (ensures async context is properly handled)."""
        await asyncio.sleep(0)  # Yield control to event loop
        # Separate context data from logging kwargs
        context_data = {
            k: v
            for k, v in kwargs.items()
            if k not in {"exc_info", "extra", "stack_info", "stacklevel"}
        }
        logging_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k in {"exc_info", "extra", "stack_info", "stacklevel"}
        }

        if context_data:
            # Create bound logger with context and use it for logging
            bound_logger = self.bind(**context_data)
            bound_logger.warning(message, *args, **logging_kwargs)
        else:
            self.warning(message, *args, **logging_kwargs)

    async def aerror(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Async error logging (ensures async context is properly handled)."""
        await asyncio.sleep(0)  # Yield control to event loop
        # Separate context data from logging kwargs
        context_data = {
            k: v
            for k, v in kwargs.items()
            if k not in {"exc_info", "extra", "stack_info", "stacklevel"}
        }
        logging_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k in {"exc_info", "extra", "stack_info", "stacklevel"}
        }

        if context_data:
            # Create bound logger with context and use it for logging
            bound_logger = self.bind(**context_data)
            bound_logger.error(message, *args, **logging_kwargs)
        else:
            self.error(message, *args, **logging_kwargs)

    async def acritical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Async critical logging (ensures async context is properly handled)."""
        await asyncio.sleep(0)  # Yield control to event loop
        # Separate context data from logging kwargs
        context_data = {
            k: v
            for k, v in kwargs.items()
            if k not in {"exc_info", "extra", "stack_info", "stacklevel"}
        }
        logging_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k in {"exc_info", "extra", "stack_info", "stacklevel"}
        }

        if context_data:
            # Create bound logger with context and use it for logging
            bound_logger = self.bind(**context_data)
            bound_logger.critical(message, *args, **logging_kwargs)
        else:
            self.critical(message, *args, **logging_kwargs)

    async def aexception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Async exception logging (ensures async context is properly handled)."""
        await asyncio.sleep(0)  # Yield control to event loop
        # Separate context data from logging kwargs
        context_data = {
            k: v
            for k, v in kwargs.items()
            if k not in {"exc_info", "extra", "stack_info", "stacklevel"}
        }
        logging_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k in {"exc_info", "extra", "stack_info", "stacklevel"}
        }

        if context_data:
            # Create bound logger with context and use it for logging
            bound_logger = self.bind(**context_data)
            bound_logger.exception(message, *args, **logging_kwargs)
        else:
            self.exception(message, *args, **logging_kwargs)

    # Configuration methods
    async def configure(self, **config: Any) -> "AsyncLogger":  # type: ignore[override]
        """
        Configure the async logger with the specified options.

        Args:
            **config: Configuration options

        Returns:
            AsyncLogger: Self for method chaining
        """
        # Valid parameters for core configure function
        valid_params = {
            "level",
            "log_entry_exit",
            "log_arguments",
            "log_return_values",
            "beautify",
            "indent_level",
            "handlers",
            "logger_name",
            "capture_print",
            "print_logger_name",
            "print_level",
            "print_prefix",
            "async_mode",
            "async_queue_size",
            "async_flush_level",
            "async_flush_interval",
            "integrate_external_loggers",
            "external_logger_level",
        }

        # Filter out invalid parameters
        filtered_config = {k: v for k, v in config.items() if k in valid_params}

        # Add async-specific defaults if not specified
        async_defaults = {
            "async_mode": True,  # AsyncLogger always uses async mode
            "async_queue_size": filtered_config.get("async_queue_size", 5000),
            "async_flush_interval": filtered_config.get("async_flush_interval", 0.1),
        }

        final_config = {**async_defaults, **filtered_config}
        self._configure_instance(**final_config)

        return self

    # Helper methods

    # Async context managers
    @asynccontextmanager
    async def context(
        self, context_name: str, **kwargs: Any
    ) -> AsyncGenerator["AsyncLogger", None]:
        """
        Async context manager for hierarchical logging with automatic indentation.

        Args:
            context_name: Name of the context for log messages
            **kwargs: Additional context variables to bind

        Example:
            async with logger.context("Data Processing", batch_id=123):
                await process_data()
        """
        # Import the unified indent manager instead of separate functions
        from ..indent_manager import get_indent_manager

        indent_manager = get_indent_manager()

        # Log context entry with current indentation (without bound context)
        self._log_context_boundary(logging.INFO, f"┌─► {context_name}")

        # Increment indentation twice for content inside the context (2 levels deeper)
        indent_manager.increment()

        try:
            # Yield bound logger if kwargs provided, otherwise yield self
            if kwargs:
                bound_logger = self.bind(**kwargs)
                async_bound_logger = cast("AsyncLogger", bound_logger)
                yield async_bound_logger
            else:
                yield self
        except Exception as e:
            # Log error with current indentation
            self.error(f"✗ {context_name} failed: {e}")
            raise
        finally:
            # Decrement indentation twice for content
            indent_manager.decrement()

            # Log context exit with context boundary indentation (without bound context)
            self._log_context_boundary(logging.INFO, f"└─◄ {context_name} complete")

            # Decrement indentation for context boundary
            # decrement_indent()

    @asynccontextmanager
    async def verbose(self, **kwargs: Any) -> AsyncGenerator["AsyncLogger", None]:
        """
        Async context manager for verbose logging.

        Example:
            async with logger.verbose():
                await detailed_operation()
        """
        async with AsyncVerboseLoggingContext(**kwargs):
            yield self

    @asynccontextmanager
    async def quiet(self, **kwargs: Any) -> AsyncGenerator["AsyncLogger", None]:
        """
        Async context manager for quiet logging.

        Example:
            async with logger.quiet():
                await noisy_operation()
        """
        async with AsyncQuietLoggingContext(**kwargs):
            yield self

    @asynccontextmanager
    async def visual(self, **kwargs: Any) -> AsyncGenerator["AsyncLogger", None]:
        """
        Async context manager for visual logging enhancements.

        Example:
            async with logger.visual(use_symbols=True):
                await important_operation()
        """
        async with AsyncVisualLoggingContext(**kwargs):
            yield self

    @asynccontextmanager
    async def handlers(self, handlers: list, **kwargs: Any) -> AsyncGenerator["AsyncLogger", None]:
        """
        Async context manager for temporary handler changes.

        Args:
            handlers: List of handlers to use temporarily

        Example:
            async with logger.handlers([file_handler]):
                await file_only_operation()
        """
        async with AsyncTemporaryHandlerContext(handlers, **kwargs):
            yield self

    # Cleanup methods
    async def close(self) -> None:
        """Close the async logger and cleanup resources."""
        if self._async_handler:
            self._async_handler.close()
            self._async_handler = None

        # Use the base class unregister logic which properly checks _is_registered
        self._unregister_logger()

    async def __aenter__(self) -> "AsyncLogger":
        """
        Async context manager entry.

        Automatically marks logger as temporary if it wasn't explicitly created
        by the user beforehand (i.e., created inline with 'async with AsyncLogger(...)').
        """
        # Check if this logger was just created (heuristic: no previous logging calls)
        # If it's a brand new logger created inline, mark it as temporary
        if not hasattr(self, "_used_before_context"):
            self._is_temporary = True

        # Mark that we've entered a context to track usage
        self._used_before_context = True
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Async context manager exit.

        Only closes and cleans up system-created loggers.
        User-created loggers are left intact.
        """
        if not getattr(self, "_user_created", True):  # Default to user_created=True for safety
            await self.close()

    def __del__(self) -> None:
        """
        Cleanup when async logger is deleted.

        Uses the base class cleanup logic which properly checks _is_registered
        to avoid unregistering bound loggers that share the same name.
        """
        try:
            # Use base class cleanup which has proper _is_registered check
            self._cleanup()
        except Exception:  # nosec B110
            # Ignore errors during cleanup - Python might be shutting down
            pass
