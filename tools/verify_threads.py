"""
Post-pytest thread verification script.

This script should be run after pytest to verify that no worker threads
are left hanging that could cause process spawning issues.
"""

import sys
import threading
import time


def check_for_lingering_threads():
    """Check for any worker threads that might still be running."""
    print("Checking for lingering worker threads...")

    all_threads = threading.enumerate()
    worker_threads = []

    for thread in all_threads:
        if thread.name and "worker" in thread.name.lower():
            worker_threads.append(thread)

    if worker_threads:
        print(f"⚠️  WARNING: Found {len(worker_threads)} worker threads still running:")
        for thread in worker_threads:
            print(f"  - {thread.name} (daemon: {thread.daemon}, alive: {thread.is_alive()})")

        # Try to clean them up
        print("Attempting cleanup...")
        try:
            from tests.thread_cleanup_fix import cleanup_async_handlers, force_cleanup_all_threads

            cleanup_count = cleanup_async_handlers()
            print(f"Cleaned up {cleanup_count} async handlers")

            thread_count = force_cleanup_all_threads()
            print(f"Attempted cleanup of {thread_count} threads")

            # Wait and check again
            time.sleep(0.5)
            remaining_threads = []
            for thread in threading.enumerate():
                if thread.name and "worker" in thread.name.lower():
                    remaining_threads.append(thread)

            if remaining_threads:
                print(
                    f"❌ CRITICAL: {len(remaining_threads)} worker threads still running after cleanup!"
                )
                print("This may cause process spawning issues.")
                return False
            else:
                print("✅ SUCCESS: All worker threads cleaned up!")
                return True

        except Exception as e:
            print(f"❌ ERROR during cleanup: {e}")
            return False
    else:
        print("✅ SUCCESS: No worker threads found!")
        return True


def main():
    """Main function."""
    print("=" * 60)
    print("POST-PYTEST THREAD VERIFICATION")
    print("=" * 60)

    # Show all current threads
    all_threads = threading.enumerate()
    print(f"Total threads running: {len(all_threads)}")

    for thread in all_threads:
        thread_type = (
            "main"
            if thread == threading.main_thread()
            else "daemon"
            if thread.daemon
            else "regular"
        )
        print(f"  - {thread.name} ({thread_type})")

    print("\n" + "-" * 60)

    # Check for problematic threads
    success = check_for_lingering_threads()

    print("\n" + "=" * 60)
    if success:
        print("✅ THREAD VERIFICATION PASSED")
        print("It should be safe to exit without process spawning issues.")
        sys.exit(0)
    else:
        print("❌ THREAD VERIFICATION FAILED")
        print("Process spawning issues may occur!")
        sys.exit(1)


if __name__ == "__main__":
    main()
