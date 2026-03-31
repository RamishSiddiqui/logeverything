"""
Test to verify that the thread leak fix is working properly.
"""

import logging
import threading
import time

from logeverything.async_logging import AsyncQueueHandler
from tests.thread_cleanup_fix import cleanup_async_handlers


def test_thread_leak_fix():
    """Test that AsyncQueueHandler threads are properly cleaned up."""
    print("Testing thread leak fix...")

    # Get initial thread count
    initial_threads = len(threading.enumerate())
    print(f"Initial thread count: {initial_threads}")

    # Create some AsyncQueueHandler instances
    handlers = []
    for i in range(3):
        handler = AsyncQueueHandler(name=f"test_handler_{i}")
        handlers.append(handler)

        # Emit a test record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"Test message {i}",
            args=(),
            exc_info=None,
        )
        handler.emit(record)

    # Check thread count after creating handlers
    after_creation_threads = len(threading.enumerate())
    print(f"Thread count after creating handlers: {after_creation_threads}")

    # Clean up handlers using our fix
    cleanup_count = cleanup_async_handlers()
    print(f"Cleaned up {cleanup_count} handlers")

    # Wait a bit for threads to stop
    time.sleep(0.5)

    # Check final thread count
    final_threads = len(threading.enumerate())
    print(f"Final thread count: {final_threads}")

    # Verify threads were cleaned up
    thread_increase = final_threads - initial_threads
    print(f"Net thread increase: {thread_increase}")

    if thread_increase <= 0:
        print("✅ SUCCESS: No thread leak detected!")
        return True
    else:
        print("❌ FAILURE: Thread leak still present!")

        # Show remaining threads for debugging
        print("Current threads:")
        for thread in threading.enumerate():
            print(f"  - {thread.name} (daemon: {thread.daemon}, alive: {thread.is_alive()})")

        return False


if __name__ == "__main__":
    test_thread_leak_fix()
