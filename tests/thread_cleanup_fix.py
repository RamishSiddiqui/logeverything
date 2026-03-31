"""
Critical fix for preventing thread leaks during pytest runs.

This module provides a function to safely clean up AsyncQueueHandler worker threads
that are causing processes to spawn uncontrollably after pytest completion.
"""

import logging
import time
from typing import List


def cleanup_async_handlers() -> int:
    """
    Find and close all AsyncQueueHandler instances to prevent thread leaks.

    This function searches through all loggers in the logging module and
    also uses the global registry to ensure their worker threads
    are properly terminated.

    Returns:
        int: Number of handlers that were closed
    """
    handlers_closed = 0

    # First, try to use the global registry from the async_logging module
    try:
        from logeverything.asyncio.async_logging import cleanup_all_async_handlers

        handlers_closed += cleanup_all_async_handlers()
    except ImportError:
        pass

    # Also search through all loggers as a fallback
    try:
        from logeverything.asyncio.async_logging import AsyncQueueHandler
    except ImportError:
        return handlers_closed

    all_handlers_to_close: List[AsyncQueueHandler] = []

    # Find all AsyncQueueHandler instances
    root_logger = logging.getLogger()

    # Check root logger
    for handler in root_logger.handlers[:]:
        if isinstance(handler, AsyncQueueHandler):
            all_handlers_to_close.append(handler)

    # Check all other loggers
    for name in list(logging.Logger.manager.loggerDict.keys()):
        try:
            logger = logging.getLogger(name)
            if hasattr(logger, "handlers"):
                for handler in logger.handlers[:]:
                    if isinstance(handler, AsyncQueueHandler):
                        all_handlers_to_close.append(handler)
        except Exception:
            continue  # Skip problematic loggers

    # Close all found handlers (that weren't already closed by the registry)
    for handler in all_handlers_to_close:
        try:
            handler.close()
            handlers_closed += 1
        except Exception:
            continue  # Ignore errors during cleanup

    # Give threads time to actually stop
    if handlers_closed > 0:
        time.sleep(0.2)

    return handlers_closed


def force_cleanup_all_threads() -> int:
    """
    Forcefully clean up any remaining threads that might be lingering.

    This is a more aggressive cleanup that tries to identify and stop
    any daemon threads that might still be running.

    Returns:
        int: Number of threads that were stopped
    """
    import threading

    threads_stopped = 0

    # Get all threads
    all_threads = threading.enumerate()

    # Look for async handler worker threads
    for thread in all_threads:
        if thread.name and "worker" in thread.name.lower() and thread != threading.current_thread():
            if thread.is_alive():
                try:
                    # For daemon threads, we can't really stop them, but we can try to interrupt
                    # The threads should be designed to stop when their handlers are closed
                    # Since they're daemon threads, they'll be killed when the main process exits
                    print(f"Found worker thread: {thread.name} (daemon: {thread.daemon})")

                    # Try to join with a very short timeout to see if it stops naturally
                    thread.join(timeout=0.01)
                    if not thread.is_alive():
                        threads_stopped += 1
                        print(f"Thread {thread.name} stopped naturally")
                except Exception:
                    pass  # Ignore errors

    return threads_stopped


if __name__ == "__main__":
    print("Testing thread cleanup...")
    closed = cleanup_async_handlers()
    print(f"Closed {closed} async handlers")
    force_cleanup_all_threads()
    print("Thread cleanup complete")
