"""
Configure pytest testing environment for the LogEverything library.
"""

import atexit
import os
import sys
import threading
import time

# Add the parent directory to sys.path so pytest can import the logeverything module correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import safe shutdown utilities and register them
from safe_shutdown import register_safe_shutdown

# Register safe shutdown to handle logging during test teardown
atexit.register(register_safe_shutdown)


def _safe_print(msg):
    """Print a message, falling back to ASCII if Unicode encoding fails."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="replace").decode("ascii"))


"""
Shared fixtures for LogEverything tests.

This module provides pytest fixtures shared across test modules.
"""

import io
import logging
import tempfile

import pytest

from logeverything import core as core_module
from logeverything.core import get_logger

# Global thread tracking for leak detection
_initial_thread_count = None
_initial_threads = None


def pytest_sessionstart(session):
    """Called after the Session object has been created."""
    global _initial_thread_count, _initial_threads
    _initial_threads = set(threading.enumerate())
    _initial_thread_count = len(_initial_threads)

    _safe_print(f"\nPYTEST SESSION START - Initial thread count: {_initial_thread_count}")


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished."""
    global _initial_thread_count, _initial_threads

    # Give threads a moment to clean up
    time.sleep(0.2)

    # Check final thread state
    final_threads = set(threading.enumerate())
    final_thread_count = len(final_threads)

    _safe_print("\nPYTEST SESSION END - Thread verification:")
    _safe_print(f"   Initial threads: {_initial_thread_count}")
    _safe_print(f"   Final threads: {final_thread_count}")

    # Check for thread leaks
    new_threads = final_threads - _initial_threads

    if new_threads:
        _safe_print(f"   WARNING: {len(new_threads)} new threads detected:")

        for thread in new_threads:
            thread_type = "daemon" if thread.daemon else "non-daemon"
            print(f"     - {thread.name} ({thread_type}, alive: {thread.is_alive()})")

        # Check specifically for worker threads
        worker_threads = [t for t in new_threads if "worker" in t.name.lower()]
        if worker_threads:
            _safe_print(f"   CRITICAL: {len(worker_threads)} worker threads detected!")
            print("   This indicates a potential thread leak.")

            # Try to clean up
            from thread_cleanup_fix import cleanup_async_handlers, force_cleanup_all_threads

            cleaned_handlers = cleanup_async_handlers()
            cleaned_threads = force_cleanup_all_threads()

            if cleaned_handlers > 0 or cleaned_threads > 0:
                _safe_print(
                    f"   CLEANUP: Closed {cleaned_handlers} handlers, {cleaned_threads} threads"
                )

                # Recheck after cleanup
                time.sleep(0.2)
                final_final_threads = set(threading.enumerate())
                remaining_new = final_final_threads - _initial_threads

                if remaining_new:
                    _safe_print(
                        f"   FAILURE: {len(remaining_new)} threads still remain after cleanup!"
                    )
                    for thread in remaining_new:
                        print(f"     - {thread.name} (alive: {thread.is_alive()})")
                else:
                    _safe_print("   SUCCESS: All threads cleaned up successfully!")
            else:
                _safe_print("   FAILURE: No cleanup performed, threads may still be leaking!")
        else:
            _safe_print("   INFO: New threads appear to be non-worker threads (likely OK)")
    else:
        _safe_print("   SUCCESS: No thread leaks detected!")


@pytest.fixture(autouse=True, scope="function")
def thread_leak_detection():
    """Automatically detect thread leaks for each test function."""
    # Record threads before test
    threads_before = set(threading.enumerate())
    thread_count_before = len(threads_before)

    yield

    # Check threads after test
    time.sleep(0.1)  # Give threads time to clean up
    threads_after = set(threading.enumerate())
    thread_count_after = len(threads_after)

    # Check for new threads
    new_threads = threads_after - threads_before

    if new_threads:
        # Check if they're worker threads (indicating a leak)
        worker_threads = [t for t in new_threads if "worker" in t.name.lower()]
        if worker_threads:
            # Try immediate cleanup
            try:
                from thread_cleanup_fix import cleanup_async_handlers

                cleanup_async_handlers()
                time.sleep(0.1)

                # Recheck
                final_threads = set(threading.enumerate())
                remaining_new = final_threads - threads_before

                if remaining_new:
                    pytest.fail(
                        f"Thread leak detected: {len(remaining_new)} threads created during test "
                        f"and not cleaned up: {[t.name for t in remaining_new]}"
                    )
            except Exception:
                pytest.fail(
                    f"Thread leak detected: {len(worker_threads)} worker threads created "
                    f"during test: {[t.name for t in worker_threads]}"
                )


@pytest.fixture(autouse=True)
def complete_logging_isolation():
    """Provide complete logging isolation for every test automatically."""
    # Store original logging state
    original_loggers = {}
    original_logger_dict = logging.Logger.manager.loggerDict.copy()
    original_logger_class = logging.getLoggerClass()

    # Store root logger state
    root_logger = logging.getLogger()
    original_root_state = {
        "handlers": root_logger.handlers[:],
        "level": root_logger.level,
        "propagate": root_logger.propagate,
    }

    # Store state of all existing loggers
    for name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(name)
        if hasattr(logger, "handlers"):  # Skip PlaceHolder objects
            original_loggers[name] = {
                "handlers": logger.handlers[:],
                "level": logger.level,
                "propagate": logger.propagate,
            }

    # Store LogEverything internal state
    from logeverything import core, decorators

    original_config = core._config.copy()
    original_active_loggers = (
        core._active_loggers.copy() if hasattr(core, "_active_loggers") else {}
    )

    # Clear logger caches
    if hasattr(decorators, "_logger_cache"):
        decorators._logger_cache.clear()
    if hasattr(core, "_logger_cache"):
        core._logger_cache.clear()

    yield

    # Complete restoration after test
    try:
        # CRITICAL: First, close all AsyncQueueHandler instances to stop worker threads
        from thread_cleanup_fix import cleanup_async_handlers, force_cleanup_all_threads

        # Clean up async handlers to prevent thread leaks
        cleanup_async_handlers()

        # Clear all current handlers and reset loggers
        root_logger.handlers.clear()
        for name in list(logging.Logger.manager.loggerDict.keys()):
            logger = logging.getLogger(name)
            if hasattr(logger, "handlers"):
                logger.handlers.clear()

        # Restore logging module state
        logging.setLoggerClass(original_logger_class)
        logging.Logger.manager.loggerDict.clear()
        logging.Logger.manager.loggerDict.update(original_logger_dict)

        # Restore root logger state
        root_logger.handlers = original_root_state["handlers"][:]
        root_logger.setLevel(original_root_state["level"])
        root_logger.propagate = original_root_state["propagate"]

        # Restore all other loggers
        for name, state in original_loggers.items():
            logger = logging.getLogger(name)
            logger.handlers = state["handlers"][:]
            logger.setLevel(state["level"])
            logger.propagate = state["propagate"]

        # Restore LogEverything configuration
        core._config.clear()
        core._config.update(original_config)

        # Clear logger caches again
        if hasattr(decorators, "_logger_cache"):
            decorators._logger_cache.clear()
        if hasattr(core, "_logger_cache"):
            core._logger_cache.clear()

        # Restore active loggers registry
        if hasattr(core, "_active_loggers"):
            core._active_loggers.clear()
            core._active_loggers.update(original_active_loggers)

        # Reset thread-local context if it exists
        if hasattr(core, "_context"):
            import threading

            core._context = threading.local()

        # Final cleanup of any remaining async handlers
        force_cleanup_all_threads()

    except Exception:
        # If restoration fails, at least clear everything and stop threads
        try:
            from thread_cleanup_fix import cleanup_async_handlers, force_cleanup_all_threads

            cleanup_async_handlers()
            force_cleanup_all_threads()
        except Exception:
            pass
        logging.getLogger().handlers.clear()
        logging.Logger.manager.loggerDict.clear()


@pytest.fixture
def reset_logging_config():
    """Reset logging configuration to defaults before and after tests."""
    # This fixture is now mainly for backwards compatibility
    # The complete_logging_isolation fixture handles the heavy lifting

    # Reset before test
    core_module.configure(
        level=logging.DEBUG,
        log_entry_exit=True,
        log_arguments=True,
        log_return_values=True,
        beautify=True,
        indent_level=2,
        handlers=["console"],
        logger_name="logeverything",
    )

    yield

    # Apply safe shutdown to handle PyTorch logging
    from safe_shutdown import register_safe_shutdown

    register_safe_shutdown()


@pytest.fixture
def captured_logger():
    """Fixture providing a logger that captures its output to a string buffer."""
    # Create a string buffer to capture log output
    log_output = io.StringIO()

    # Create a handler that writes to the buffer
    handler = logging.StreamHandler(log_output)
    handler.setFormatter(logging.Formatter("%(message)s"))  # Simple format for testing

    # Configure the logger
    logger = get_logger("test_logger")
    logger.handlers = []  # Remove existing handlers
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    yield logger, log_output

    # Clean up
    log_output.close()


@pytest.fixture
def temp_log_file():
    """Fixture providing a temporary log file path."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name

    yield temp_path

    # Clean up
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_json_file():
    """Fixture providing a temporary JSON log file path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
        temp_path = temp_file.name

    yield temp_path

    # Clean up
    if os.path.exists(temp_path):
        os.unlink(temp_path)
