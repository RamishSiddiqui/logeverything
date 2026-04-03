"""
LogEverything Logger Interface

This module provides a comprehensive, user-friendly logger interface that combines
the power of LogEverything's configuration system with an intuitive API.

Example usage::

    from logeverything import Logger

    # Simple usage with automatic setup
    log = Logger()
    log.info("Hello, world!")

    # Advanced usage with custom configuration
    log = Logger("my_app")
    log.configure(
        level="DEBUG",
        visual_mode=True,
        handlers=["console", "file"],
        file_path="app.log"
    )

    # Contextual logging
    with log.context("Data Processing"):
        log.info("Starting processing")
        log.debug("Loading data")
        log.warning("Some data missing")
        log.info("Processing complete")

    # Bound context (similar to structured logging)
    user_log = log.bind(user_id=123, request_id="abc-def")
    user_log.info("User action performed")
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional, Union

# Import from the main core module (lazily to avoid circular imports)
from . import core as core_module
from .base.base_logger import BaseLogger
from .contexts import VisualLoggingContext

get_logger = core_module.get_logger
increment_indent = core_module.increment_indent
decrement_indent = core_module.decrement_indent

# Global flag to track if auto-detection has been shown
_auto_detection_shown = False


class Logger(BaseLogger):
    """
    A comprehensive logger interface for LogEverything.

    This class provides a simple, powerful interface for logging that integrates
    all of LogEverything's features while remaining easy to use.

    Inherits from BaseLogger to provide a consistent API and enable extensibility.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        auto_setup: bool = True,
        _register: bool = True,
        **config: Any,
    ) -> None:
        """
        Initialize the Logger with optional configuration.

        Args:
            name: Logger name (default: automatic based on caller)
            auto_setup: Whether to automatically setup logging
            _register: Whether to register this logger (internal parameter for bound loggers)
            **config: Configuration options (level, visual_mode, handlers, etc.)
        """
        # Determine logger name
        if name is None:
            # Auto-generate name based on caller
            import inspect

            frame = inspect.currentframe()
            if frame and frame.f_back:
                caller_module = frame.f_back.f_globals.get("__name__", "unknown")
                name = f"logeverything.{caller_module}"
            else:
                name = "logeverything.logger"

        # Initialize base logger
        super().__init__(name)

        self._is_async: bool = False  # Mark as sync logger for smart casting
        self._options: Dict[str, Any] = {}  # Store logger options for decorator access

        # Register logger name with adaptive column manager for optimal visual alignment
        try:
            from .handlers.handlers import register_logger_name

            register_logger_name(name)
        except ImportError:
            # Fallback in case handlers module isn't available
            pass

        # Auto-attach HierarchyFilter for structured hierarchy fields
        from .hierarchy import HierarchyFilter

        if not any(isinstance(f, HierarchyFilter) for f in self._logger.filters):
            self._logger.addFilter(HierarchyFilter())

        # Register this logger instance for decorator usage (skip for bound loggers)
        if _register:
            self._register_logger()

        if auto_setup:
            # Apply any passed configuration first
            if config:
                self.configure(**config)
            else:
                # Use intelligent defaults
                self._auto_configure()

    def _auto_configure(self) -> None:
        """Automatically configure the logger with intelligent defaults."""
        global _auto_detection_shown

        # Import here to avoid circular imports
        from . import core as core_module

        _detect_environment = core_module._detect_environment
        _get_environment_config = core_module._get_environment_config

        # Detect environment and get appropriate config
        env_type = _detect_environment()
        env_config = _get_environment_config(env_type)

        # Log auto-detection info at DEBUG level (no stdout spam)
        if not _auto_detection_shown:
            _internal_logger = logging.getLogger("logeverything")
            _internal_logger.debug(f"Auto-detected environment: {env_type}")
            _internal_logger.debug(
                f"Applied optimized default configuration for {env_type} environment"
            )
            _internal_logger.debug(
                "You can override this by specifying a profile or configuration parameters"
            )
            _auto_detection_shown = True

        # Setup logging with environment-appropriate defaults using instance-level configuration
        # Use the same path as manual configure() to ensure consistency
        self._configure_instance(**env_config)

        # Store visual preferences from auto-configuration in _options for decorator access
        for key in ["visual_mode", "use_symbols", "use_indent"]:
            if key in env_config:
                self._options[key] = env_config[key]

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

    # Known stdlib kwargs that should NOT be treated as structured data
    _STDLIB_LOG_KWARGS = {"exc_info", "extra", "stack_info", "stacklevel"}

    def _log_message(self, level: int, message: str, *args: Any, **kwargs: Any) -> None:
        """Internal method to handle the actual logging."""
        message = self._format_message_with_context(message)

        # Fast path: no kwargs means no structured data to process
        if not kwargs:
            self.logger.log(level, message, *args)
            return

        # Separate stdlib kwargs from structured data
        stdlib_kwargs = {k: v for k, v in kwargs.items() if k in self._STDLIB_LOG_KWARGS}
        structured_data = {k: v for k, v in kwargs.items() if k not in self._STDLIB_LOG_KWARGS}

        # If there's structured data, merge it into extra
        if structured_data:
            extra = stdlib_kwargs.get("extra", {})
            if not isinstance(extra, dict):
                extra = {}
            extra["_structured"] = structured_data
            stdlib_kwargs["extra"] = extra

        self.logger.log(level, message, *args, **stdlib_kwargs)

    def _create_bound_logger(self, **kwargs: Any) -> "Logger":
        """
        Create a bound logger instance with merged context.

        Bound loggers share the same name and underlying logger,
        with only context data being additive.
        """
        # Create new logger with the SAME name (no hierarchical naming)
        # Don't auto-setup or register to avoid registry pollution
        bound_logger = Logger(self._name, auto_setup=False, _register=False)

        # Share the same underlying Python logger
        bound_logger._logger = self._logger

        # Merge context: parent context + new context (additive)
        parent_context = getattr(self, "_context", {})
        bound_logger._context = {**parent_context, **kwargs}

        return bound_logger

    def _cleanup(self) -> None:
        """Clean up logger resources and unregister from the global registry."""
        self._unregister_logger()

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
        """Log a warning message (alias for warning)."""
        self.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self._log_message(logging.ERROR, message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        self._log_message(logging.CRITICAL, message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an exception message with traceback."""
        kwargs.setdefault("exc_info", True)
        self._log_message(logging.ERROR, message, *args, **kwargs)

    @contextmanager
    def context(self, context_name: str) -> Iterator[None]:
        """
        Create a hierarchical logging context.

        This creates a visual hierarchy in the logs, similar to how LogEverything's
        decorators work but as a context manager.

        Args:
            context_name: Name of the context to display in logs

        Example:
            with log.context("Database Operation"):
                log.info("Connecting to database")
                log.debug("Executing query")
                log.info("Query completed")
        """
        # Increment indentation first for the entry message
        # increment_indent()

        # Log context entry with current indentation (without bound context)
        self._log_context_boundary(logging.INFO, f"┌─► {context_name}")

        # Use IndentManager for consistent indentation management
        from .indent_manager import get_indent_manager

        indent_manager = get_indent_manager()

        # Increment indentation once for content inside the context (consistent with decorators)
        indent_manager.increment()

        try:
            with VisualLoggingContext():
                yield
        finally:
            # Decrement indentation once for content (consistent with decorators)
            indent_manager.decrement()

            # Log context exit with context boundary indentation (without bound context)
            self._log_context_boundary(logging.INFO, f"└─◄ {context_name} complete")

            # Decrement indentation for context boundary
            # decrement_indent()

    def set_level(self, level: Union[str, int]) -> None:
        """
        Set the logging level.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL or numeric)
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        self.logger.setLevel(level)

    def add_handler(self, handler: logging.Handler) -> None:
        """
        Add a logging handler.

        Args:
            handler: The logging handler to add
        """
        self.logger.addHandler(handler)

        # When a logger gets its own handler, it should not propagate to avoid duplication
        # This is especially important for loggers that have explicit handler configuration
        if self.logger.handlers:
            self.logger.propagate = False

    def remove_handler(self, handler: logging.Handler) -> None:
        """
        Remove a logging handler.

        Args:
            handler: The logging handler to remove
        """
        self.logger.removeHandler(handler)

    def opt(
        self,
        colors: Any = None,
        raw: Any = None,
        depth: Any = None,
        exception: Any = None,
        lazy: Any = None,
        ansi: Any = None,
        record: Any = None,
    ) -> "Logger":
        """
        Configure logging options (Loguru-style).

        Args:
            colors: Enable/disable colors in output
            raw: Use raw output format
            depth: Stack depth for caller information
            exception: Include exception information
            lazy: Use lazy evaluation
            ansi: Enable/disable ANSI codes
            record: Include record information

        Returns:
            Logger: A new logger instance with configured options

        Example:
            logger.opt(colors=True).info("This is <green>colored</green> output")
        """
        # Create a new logger instance with options
        opt_logger = Logger(self._name, auto_setup=False)
        opt_logger._logger = self._logger
        opt_logger._options = {
            "colors": colors,
            "raw": raw,
            "depth": depth,
            "exception": exception,
            "lazy": lazy,
            "ansi": ansi,
            "record": record,
        }
        return opt_logger

    def add(self, sink: Any, **kwargs: Any) -> None:
        """
        Add a logging sink/handler (Loguru-style).

        Args:
            sink: File path, file object, or handler
            **kwargs: Additional configuration options

        Example:
            logger.add("file.log", rotation="500 MB", retention="10 days")
            logger.add(sys.stderr, format="{time} | {level} | {message}")
        """
        import sys
        from typing import Union as typing_Union

        from .handlers.handlers import ConsoleHandler, FileHandler

        handler: typing_Union[FileHandler, ConsoleHandler, Any]

        if isinstance(sink, str):
            # File path - create FileHandler
            handler = FileHandler(sink)
        elif hasattr(sink, "write"):
            # File-like object - create ConsoleHandler
            if sink == sys.stderr or sink == sys.stdout:
                handler = ConsoleHandler()
            else:
                handler = ConsoleHandler()
                handler.stream = sink
        else:
            # Assume it's already a handler
            handler = sink

        self.add_handler(handler)

    def remove(self, handler_id: Any = None) -> None:
        """
        Remove a logging handler (Loguru-style).

        Args:
            handler_id: ID of handler to remove (if None, removes all)
        """
        if handler_id is None:
            # Remove all handlers
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
        else:
            # For now, just remove all handlers (can be enhanced later)
            self.remove()

    def configure(self, handlers: Any = None, **kwargs: Any) -> "Logger":
        """
        Configure the logger with LogEverything's full configuration system.

        Args:
            handlers: List of handler configurations or names
            **kwargs: Configuration options including:
                - level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                - visual_mode: Enable visual formatting with symbols and indentation
                - use_symbols: Use Unicode symbols for log levels
                - use_indent: use visual indentation
                - use_colors: Enable colored log level indicators (default: True)
                - color_messages: Enable colored message text (default: False)
                - beautify: Enable beautiful formatting
                - file_path: File path for file logging
                - async_mode: Enable asynchronous logging
                - format: Custom log format string
                - And many more options from LogEverything's configuration system
        Returns:
            Logger: Self for method chaining
        Examples::

            # Simple configuration
            log.configure(level="DEBUG", visual_mode=True)

            # With message coloring control
            log.configure(level="INFO", visual_mode=True, color_messages=True)

            # Advanced configuration
            log.configure(
                level="INFO",
                visual_mode=True,
                use_symbols=True,
                handlers=["console", "file"],
                file_path="app.log",
                async_mode=True
            )

            # Handler-specific configuration
            log.configure(handlers=[
                {"name": "console", "level": "INFO"},
                {"name": "file", "level": "DEBUG", "file_path": "debug.log"}
            ])
        """
        # Import here to avoid circular imports
        from . import core as core_module

        # Handle intercept_stdlib parameter
        if kwargs.pop("intercept_stdlib", False):
            from .external.external import intercept_stdlib

            intercept_stdlib(level=kwargs.get("level"))

        # Handle profile parameter if provided
        if "profile" in kwargs:
            profile_name = kwargs.pop("profile")
            from .profiles.profiles import get_profile

            profile_config = get_profile(profile_name)
            # Merge profile config with kwargs (kwargs override profile settings)
            profile_config.update(kwargs)
            kwargs = profile_config

        # If specific handler configurations are provided
        if handlers:
            # Handle both simple and complex handler specifications
            if isinstance(handlers, list) and len(handlers) > 0:
                if isinstance(handlers[0], dict):
                    # Complex handler configuration
                    # For now, use the main configuration and let setup_logging handle it
                    kwargs["handlers"] = [h.get("name", "console") for h in handlers]
                elif isinstance(handlers[0], str):
                    # Simple handler names
                    kwargs["handlers"] = handlers
                else:
                    # Assume they are handler objects - pass them directly
                    kwargs["handlers"] = handlers
            else:
                kwargs["handlers"] = handlers

        # Store visual preferences locally for decorator usage
        visual_preferences = {}
        if "visual_mode" in kwargs:
            visual_preferences["visual_mode"] = kwargs["visual_mode"]
        if "use_symbols" in kwargs:
            visual_preferences["use_symbols"] = kwargs["use_symbols"]
        if "use_indent" in kwargs:
            visual_preferences["use_indent"] = kwargs["use_indent"]

        # Store in _options for decorator access
        if visual_preferences:
            self._options.update(visual_preferences)

        # Handle convenience parameters - translate to proper handler configuration
        self._translate_convenience_parameters(kwargs)

        # Configure THIS logger instance only (NO global state modification)
        if kwargs:
            self._configure_instance(**kwargs)

            # Also store any other visual-related settings in _options
            for key in ["use_colors", "color_messages", "beautify"]:
                if key in kwargs:
                    self._options[key] = kwargs[key]

        # Also update global IndentManager configuration for proper indentation
        if visual_preferences:
            try:
                core_module.configure(_internal=True, **visual_preferences)
            except (ImportError, AttributeError, TypeError):
                pass  # Fail silently if core configure is not available

        return self

    def _translate_convenience_parameters(self, kwargs: Dict[str, Any]) -> None:
        """
        Translate convenience parameters to proper handler configurations.

        This method converts shorthand parameters like console=True, json_file="..."
        into proper handlers configuration.
        """
        handlers_to_add = []
        console_requested = kwargs.pop("console", False)

        # Handle console=True parameter
        if console_requested:
            handlers_to_add.append("console")

        # Handle json_file parameter
        if "json_file" in kwargs:
            json_file = kwargs.pop("json_file")
            handlers_to_add.append("json")
            # Convert json_file to file_path for JSON handler
            kwargs["file_path"] = json_file

        # Handle file_path parameter - add file handler if console was also requested
        if "file_path" in kwargs and console_requested:
            handlers_to_add.append("file")
        elif "file_path" in kwargs and not console_requested and not handlers_to_add:
            # Only file_path specified, assume file handler only
            handlers_to_add.append("file")

        # Set handlers if any were determined and not already specified
        if handlers_to_add and "handlers" not in kwargs:
            kwargs["handlers"] = handlers_to_add

    def _configure_instance(self, **kwargs: Any) -> None:
        """
        Configure this specific logger instance without affecting global state.

        This method replaces the global setup_logging() call to prevent
        cross-logger pollution while preserving LogEverything functionality.
        """
        # Set level for this logger only
        if "level" in kwargs:
            level = kwargs["level"]
            if isinstance(level, str):
                level = getattr(logging, level.upper(), logging.INFO)
            self.logger.setLevel(level)

        # Check if this is an explicit configure() call with handlers or visual formatting
        explicit_config = any(
            key in kwargs
            for key in [
                "handlers",
                "visual_mode",
                "use_symbols",
                "use_indent",
                "format_type",
                "format",
            ]
        )

        # If explicit configuration is requested but no handlers exist, create proper handlers
        if explicit_config and not self.logger.handlers:
            # Use EnhancedConsoleHandler for visual formatting, regular handler otherwise
            visual_formatting = any(
                key in kwargs for key in ["visual_mode", "use_symbols", "use_indent"]
            ) or kwargs.get("visual_mode", False)

            if visual_formatting:
                # Detect platform capabilities to handle Windows console encoding issues
                from . import core as core_module

                platform_capabilities = core_module.detect_platform_capabilities()

                # Auto-detect if we should force ASCII to prevent encoding errors
                should_force_ascii = kwargs.get("force_ascii", False)
                if not should_force_ascii and not platform_capabilities.get(
                    "supports_unicode", True
                ):
                    should_force_ascii = True

                # Create EnhancedConsoleHandler with proper platform handling
                from .handlers.handlers import EnhancedConsoleHandler

                console_handler = EnhancedConsoleHandler(
                    use_colors=kwargs.get("use_colors", True),
                    color_messages=kwargs.get("color_messages", False),
                    use_symbols=kwargs.get("use_symbols", visual_formatting)
                    and not should_force_ascii,
                    use_indent=kwargs.get("use_indent", visual_formatting),
                    align_columns=kwargs.get("align_columns", False),
                    color_theme=kwargs.get("color_theme", "default"),
                    ascii_only=should_force_ascii,
                    level=kwargs.get("level", logging.INFO),
                )
                self.logger.addHandler(console_handler)
            else:
                # Create a default console handler for non-visual configuration
                from .handlers.handlers import ConsoleHandler

                default_handler = ConsoleHandler()
                if "level" in kwargs:
                    default_handler.setLevel(kwargs["level"])
                self.logger.addHandler(default_handler)

        # Handle explicit handlers configuration
        if "handlers" in kwargs:
            self._configure_instance_handlers(kwargs["handlers"], **kwargs)

        # Handle visual formatting by updating existing handlers
        needs_formatter = any(
            key in kwargs
            for key in [
                "visual_mode",
                "use_symbols",
                "use_indent",
                "format",
                "format_type",
                "date_format",
            ]
        )

        if needs_formatter and not any(key in kwargs for key in ["handlers"]):
            # Update existing handlers with new formatter
            formatter = self._create_instance_formatter(**kwargs)
            for handler in self.logger.handlers:
                handler.setFormatter(formatter)

        # CRITICAL: Only disable propagation for explicit configure() calls that add handlers
        # This prevents duplication from configure() while preserving normal hierarchy behavior
        if explicit_config and self.logger.handlers:
            # This logger was explicitly configured with its own handlers/formatting
            # Disable propagation to prevent duplication with parent loggers
            self.logger.propagate = False
        # For normal logger usage (auto_setup=True without explicit configure()),
        # leave propagation enabled to use parent/root handlers

    def _create_instance_formatter(self, **config: Any) -> logging.Formatter:
        """Create a formatter for this logger instance."""
        # Import here to avoid circular imports
        from .handlers.handlers import PrettyFormatter

        visual_mode = config.get("visual_mode", False)
        use_symbols = config.get("use_symbols", False)
        use_indent = config.get("use_indent", False)

        if visual_mode or use_symbols or use_indent:
            # Use LogEverything's PrettyFormatter for visual formatting
            return PrettyFormatter(
                use_symbols=use_symbols,
                use_indent=use_indent,
                use_colors=config.get("use_colors", True),
                color_messages=config.get("color_messages", False),
                datefmt=config.get("date_format", "%Y-%m-%d %H:%M:%S"),  # Fixed parameter name
            )
        else:
            # Use standard formatter
            format_string = config.get(
                "format", "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
            )

            # Create a custom formatter that centers the level name
            class CenteredFormatter(logging.Formatter):
                def format(self, record: logging.LogRecord) -> str:
                    # Center the levelname before formatting
                    original_levelname = record.levelname
                    record.levelname = f"{original_levelname:^8}"
                    try:
                        return super().format(record)
                    finally:
                        # Restore original levelname
                        record.levelname = original_levelname

            return CenteredFormatter(
                format_string, datefmt=config.get("date_format", "%Y-%m-%d %H:%M:%S")
            )

    def _configure_instance_handlers(self, handlers_config: Any, **kwargs: Any) -> None:
        """Configure handlers for this logger instance only."""
        if not handlers_config:
            return

        # Clear existing handlers if we're replacing them
        self.logger.handlers.clear()

        # Import handlers here to avoid circular imports
        from .handlers.handlers import ConsoleHandler, FileHandler

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
                    # Apply formatter to this handler
                    formatter = self._create_instance_formatter(**kwargs)
                    handler.setFormatter(formatter)

                    # Add handler to THIS logger only
                    self.logger.addHandler(handler)

    # Additional convenience methods that integrate core LogEverything functionality

    def enable_print_capture(self) -> "Logger":
        """
        Enable print statement capture.

        Returns:
            Logger: Self for method chaining
        """
        from .capture.print_capture import enable_print_capture

        enable_print_capture()
        return self

    def disable_print_capture(self) -> "Logger":
        """
        Disable print statement capture.

        Returns:
            Logger: Self for method chaining
        """
        from .capture.print_capture import disable_print_capture

        disable_print_capture()
        return self

    def enable_async_mode(self, queue_size: int = 1000, flush_interval: float = 1.0) -> "Logger":
        """
        Enable asynchronous logging mode.

        Args:
            queue_size: Maximum size of the async queue
            flush_interval: Interval in seconds for flushing the queue

        Returns:
            Logger: Self for method chaining
        """
        self.configure(
            async_mode=True, async_queue_size=queue_size, async_flush_interval=flush_interval
        )
        return self

    def enable_visual_mode(self, use_symbols: bool = True, use_indent: bool = True) -> "Logger":
        """
        Enable visual formatting mode with symbols and indentation.

        Args:
            use_symbols: Whether to use Unicode symbols for log levels
            use_indent: Whether to use visual indentation

        Returns:
            Logger: Self for method chaining
        """
        self.configure(
            visual_mode=True, use_symbols=use_symbols, use_indent=use_indent, beautify=True
        )
        return self

    def add_file_logging(self, file_path: str, level: Optional[Union[str, int]] = None) -> "Logger":
        """
        Add file logging to the logger.

        Args:
            file_path: Path to the log file
            level: Logging level for the file (if different from main level)

        Returns:
            Logger: Self for method chaining
        """
        config: Dict[str, Any] = {"file_path": file_path, "handlers": ["console", "file"]}
        if level is not None:
            config["level"] = level
        self.configure(**config)
        return self

    def set_profile(self, profile_name: str) -> "Logger":
        """
        Apply a predefined configuration profile.

        Args:
            profile_name: Name of the profile (development, production, testing, etc.)

        Returns:
            Logger: Self for method chaining
        """
        from .profiles.profiles import get_profile

        profile_config = get_profile(profile_name)
        if profile_config:
            self.configure(**profile_config)
        return self


# Users should create their own Logger instances:
# log = Logger()
# log = Logger("my_app")
# log.info("Hello world!")
