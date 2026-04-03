#!/usr/bin/env python3
"""
Comprehensive Decorators Example

This example demonstrates all of LogEverything's decorators:
- @log (smart decorator)
- @log_function
- @log_class
- @log_io
- Custom decorator configurations
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from logeverything import Logger
from logeverything.decorators import log, log_class, log_function, log_io

# Create the comprehensive_example logger BEFORE decorators are defined
# This prevents temporary logger creation and handler proliferation
print("🚀 Setting up comprehensive example logger...")
comprehensive_logger = Logger("comprehensive_example")
comprehensive_logger.configure(
    level="DEBUG",
    visual_mode=True,
    use_symbols=True,
    async_mode=True,
    async_queue_size=1000,
    async_flush_interval=0.1,
)
print(f"✅ Logger '{comprehensive_logger.name}' ready for decorators")


# 1. Smart @log decorator (auto-detects what it's decorating)
@log(using="comprehensive_example")
def calculate_fibonacci(n):
    """Calculate fibonacci number using the smart decorator."""
    if n <= 1:
        return n
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)


@log(using="comprehensive_example")
async def async_fetch_data(url):
    """Async function with smart decorator."""
    await asyncio.sleep(0.1)  # Simulate network delay
    return f"Data from {url}"


# 2. Explicit function logging
@log_function(using="comprehensive_example", level="DEBUG", include_args=True, include_result=True)
def process_data(data, multiplier=2):
    """Process data with detailed logging."""
    result = [x * multiplier for x in data]
    time.sleep(0.05)  # Simulate processing
    return result


@log_function(using="comprehensive_example", level="INFO")
def validate_email(email):
    """Validate email format."""
    return "@" in email and "." in email.split("@")[1]


# 3. Class logging
@log_class(using="comprehensive_example", level="INFO", include_private=False)
class UserManager:
    """User management class with automatic logging."""

    def __init__(self):
        self.users = {}
        self._private_data = "secret"

    def add_user(self, username, email):
        """Add a new user."""
        if self.user_exists(username):
            raise ValueError(f"User {username} already exists")

        self.users[username] = {"email": email, "created_at": time.time()}
        return True

    def get_user(self, username):
        """Get user information."""
        return self.users.get(username)

    def user_exists(self, username):
        """Check if user exists."""
        return username in self.users

    def _get_private_data(self):
        """Private method (not logged due to include_private=False)."""
        return self._private_data


# 4. I/O logging for file operations
@log_io(using="comprehensive_example", level="INFO", log_args=True)
def write_config_file(filename, config):
    """Write configuration to file."""
    with open(filename, "w") as f:
        f.write(str(config))
    return f"Config written to {filename}"


@log_io(using="comprehensive_example", level="INFO")
def read_config_file(filename):
    """Read configuration from file."""
    try:
        with open(filename, "r") as f:
            return f.read()
    except FileNotFoundError:
        return None


# 5. Custom decorator configurations
@log(using="comprehensive_example", level="WARNING", include_args=True, include_result=False)
def risky_operation(data):
    """Operation that might fail."""
    if not data:
        raise ValueError("Data cannot be empty")
    return len(data) * 2


class APIClient:
    """API client with selective method logging."""

    @log(using="comprehensive_example", level="INFO")
    def __init__(self, base_url):
        self.base_url = base_url
        self.session_id = f"sess_{int(time.time())}"

    @log_function(using="comprehensive_example", level="DEBUG", include_args=True)
    def _make_request(self, endpoint, method="GET"):
        """Internal request method with debug logging."""
        time.sleep(0.1)  # Simulate API call
        return f"{method} {self.base_url}/{endpoint}"

    @log(using="comprehensive_example", level="INFO", include_result=True)
    def get_users(self):
        """Get all users."""
        return self._make_request("users")

    @log_io(using="comprehensive_example", level="INFO")
    def upload_file(self, filepath):
        """Upload file with I/O logging."""
        # Simulate file upload
        time.sleep(0.2)
        return f"Uploaded {filepath}"


async def main():
    """Main demonstration function."""

    print("=== Comprehensive Decorators Demo ===\n")

    # 1. Smart decorator examples
    print("1. Smart @log Decorator")
    print("-" * 30)

    result = calculate_fibonacci(5)
    print(f"Fibonacci(5) = {result}")

    # Async function
    data = await async_fetch_data("https://api.example.com/data")
    print(f"Fetched: {data}")

    # 2. Function decorators
    print("\n2. @log_function Decorator")
    print("-" * 30)

    processed = process_data([1, 2, 3, 4], multiplier=3)
    print(f"Processed data: {processed}")

    valid = validate_email("user@example.com")
    print(f"Email valid: {valid}")

    # 3. Class decorator
    print("\n3. @log_class Decorator")
    print("-" * 30)

    user_mgr = UserManager()
    user_mgr.add_user("alice", "alice@example.com")
    user_mgr.add_user("bob", "bob@example.com")

    alice = user_mgr.get_user("alice")
    print(f"Alice data: {alice}")

    # Try to access private method (should not be logged)
    private = user_mgr._get_private_data()

    # 4. I/O decorator
    print("\n4. @log_io Decorator")
    print("-" * 30)

    config = {"app_name": "MyApp", "version": "1.0.0"}
    write_config_file("app_config.txt", config)

    read_result = read_config_file("app_config.txt")
    print(f"Read config: {read_result}")

    # 5. Custom configurations
    print("\n5. Custom Decorator Configurations")
    print("-" * 40)

    try:
        risky_operation([1, 2, 3])
        risky_operation([])  # This will raise an exception
    except ValueError as e:
        print(f"Caught expected error: {e}")

    # API client example
    client = APIClient("https://api.myservice.com")
    users = client.get_users()
    upload_result = client.upload_file("/path/to/file.txt")

    print("\n✓ All decorator types demonstrated!")
    print("\nDecorator Features Shown:")
    print("- Smart auto-detection (@log)")
    print("- Explicit function logging (@log_function)")
    print("- Class-wide logging (@log_class)")
    print("- I/O operation logging (@log_io)")
    print("- Custom configurations (levels, args, results)")
    print("- Async function support")
    print("- Exception handling")
    print("- Private method filtering")

    # Small delay to ensure all async logging is completed
    await asyncio.sleep(0.1)


if __name__ == "__main__":
    import time
    from datetime import datetime

    # Track overall timing
    script_start_time = time.time()
    print(f"🚀 Script started at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")

    try:
        main_start_time = time.time()
        asyncio.run(main())
        main_end_time = time.time()
        print(f"⏱️  Main execution completed in {(main_end_time - main_start_time):.3f}s")
    finally:
        # Aggressive cleanup to prevent hanging during destructor calls
        cleanup_start_time = time.time()
        print(f"\n🧹 Starting cleanup at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}...")

        # 1. Force cleanup of all AsyncQueueHandler instances
        step_start = time.time()
        try:
            from logeverything.asyncio.async_logging import cleanup_all_async_handlers

            handler_count = cleanup_all_async_handlers()
            step_time = time.time() - step_start
            print(f"   ├─ Closed {handler_count} async handlers ({step_time:.3f}s)")
        except ImportError:
            step_time = time.time() - step_start
            print(f"   ├─ AsyncQueueHandler cleanup not available ({step_time:.3f}s)")

        # 2. Standard logging cleanup
        step_start = time.time()
        import logging

        cleanup_count = 0
        for handler in logging.getLogger().handlers[:]:
            try:
                handler.close()
                logging.getLogger().removeHandler(handler)
                cleanup_count += 1
            except Exception:
                pass
        step_time = time.time() - step_start
        print(f"   ├─ Removed {cleanup_count} standard handlers ({step_time:.3f}s)")

        # 3. Clear logger caches to prevent destructor delays
        step_start = time.time()
        try:
            from logeverything.core import _active_loggers

            logger_count = len(_active_loggers)
            _active_loggers.clear()
            step_time = time.time() - step_start
            print(f"   ├─ Cleared {logger_count} active loggers ({step_time:.3f}s)")
        except (ImportError, AttributeError):
            step_time = time.time() - step_start
            print(f"   ├─ Logger cache cleanup not available ({step_time:.3f}s)")

        # 4. Force garbage collection to trigger destructors now rather than later
        step_start = time.time()
        import gc

        collected = gc.collect()
        step_time = time.time() - step_start
        print(f"   ├─ Garbage collected {collected} objects ({step_time:.3f}s)")

        # 5. Small delay to ensure all background threads have time to stop
        step_start = time.time()
        time.sleep(0.1)
        step_time = time.time() - step_start
        print(f"   ├─ Thread stop delay ({step_time:.3f}s)")

        cleanup_end_time = time.time()
        total_cleanup_time = cleanup_end_time - cleanup_start_time
        print(f"   └─ Total cleanup completed in {total_cleanup_time:.3f}s")

        # Track final timing
        script_end_time = time.time()
        total_script_time = script_end_time - script_start_time
        print(
            f"🏁 Script ended at {datetime.now().strftime('%H:%M:%S.%f')[:-3]} (total: {total_script_time:.3f}s)"
        )

        # Add marker to see if there's any delay after this point
        print("🔚 About to exit Python script - watching for any delays...")
        post_exit_start = time.time()
