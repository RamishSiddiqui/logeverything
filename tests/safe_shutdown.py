"""
Safe shutdown utilities for the LogEverything library.

This module provides utilities to handle logging issues that might occur
during interpreter shutdown, particularly when third-party libraries try to
log messages after handlers have been closed.
"""

import atexit
import logging
import sys
from logging import Handler, Logger


class SafeHandler(logging.Handler):
    """
    A logging handler that wraps another handler and safely handles logging
    during interpreter shutdown.

    This handler prevents "I/O operation on closed file" errors that can happen
    when libraries try to log messages during interpreter shutdown.
    """

    def __init__(self, target_handler):
        """
        Initialize the safe handler with a target handler.

        Args:
            target_handler: The handler to wrap
        """
        super().__init__(level=target_handler.level)
        self.target_handler = target_handler
        self.closed = False

    def emit(self, record):
        """
        Safely emit a record by catching errors during shutdown.

        Args:
            record: The log record to emit
        """
        if self.closed:
            return

        try:
            self.target_handler.emit(record)
        except ValueError as e:
            if "I/O operation on closed file" in str(e):
                # File already closed, probably during interpreter shutdown
                self.closed = True
            else:
                # Some other ValueError, propagate it
                raise

    def close(self):
        """Close the handler and the target handler."""
        self.closed = True
        try:
            self.target_handler.close()
        except Exception:
            pass
        super().close()


def patch_pytorch_logging():
    """
    Patch PyTorch's logging to handle gracefully shutting down.

    This function finds any PyTorch-related loggers and wraps their handlers
    with SafeHandler to prevent "I/O operation on closed file" errors.
    """
    # Look for PyTorch loggers
    for name, logger in logging.root.manager.loggerDict.items():
        if isinstance(logger, Logger) and (name.startswith("torch") or "pytorch" in name.lower()):
            # Replace handlers with safe versions
            for i, handler in enumerate(logger.handlers):
                if not isinstance(handler, SafeHandler):
                    logger.handlers[i] = SafeHandler(handler)


def register_safe_shutdown():
    """
    Register the safe shutdown handler.

    This ensures that when Python is shutting down, we make our loggers safe.
    """
    # Apply patches
    patch_pytorch_logging()

    # Make root logger handlers safe
    root_logger = logging.getLogger()
    for i, handler in enumerate(root_logger.handlers):
        if not isinstance(handler, SafeHandler):
            root_logger.handlers[i] = SafeHandler(handler)

    # Patch the logging module's handleError function to suppress I/O errors during shutdown
    original_handle_error = logging.Handler.handleError

    def safe_handle_error(self, record):
        """Safely handle errors during logging without printing traceback for I/O errors during shutdown."""
        try:
            t, v, tb = sys.exc_info()
            if t is ValueError and "I/O operation on closed file" in str(v):
                # Silently ignore I/O errors during shutdown
                return
            else:
                # For all other errors, call the original handler
                original_handle_error(self, record)
        except Exception:
            # If something goes wrong in our error handler, use the original
            original_handle_error(self, record)

    # Replace the handle_error method to suppress file I/O errors
    logging.Handler.handleError = safe_handle_error

    # Register to handle future logger creations
    orig_getLogger = logging.getLogger

    def safe_getLogger(name=None):
        logger = orig_getLogger(name)
        # If this is a PyTorch logger, make it safe
        if name and (name.startswith("torch") or "pytorch" in name.lower()):
            for i, handler in enumerate(logger.handlers):
                if not isinstance(handler, SafeHandler):
                    logger.handlers[i] = SafeHandler(handler)
        return logger

    logging.getLogger = safe_getLogger
