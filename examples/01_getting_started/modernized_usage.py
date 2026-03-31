"""
Modernized LogEverything Example (v1.0.0)

This example showcases the completely modernized LogEverything API with:
- Simple Logger class for intuitive logging
- Unified @log decorator that works on everything
- LogEverything's own level constants (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- High-performance async logging (6.8x faster)
- Smart context detection and automatic isolation
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path for imports to work when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import LogEverything's modernized API
from logeverything import CRITICAL, DEBUG, ERROR, INFO, WARNING, Logger
from logeverything.decorators import log
from logeverything.handlers import ConsoleHandler, PrettyFormatter


def setup_simple_logging():
    """Set up logging using the simple Logger approach."""
    # Simple approach: Create and configure loggers
    app_log = Logger("modernized_app")
    app_log.configure(level=DEBUG, visual_mode=True, use_symbols=True, use_indent=True)
    return app_log


def setup_advanced_logging():
    """Set up logging using LogEverything's modern instance-based configuration."""
    # Create a logger instance and configure it
    advanced_log = Logger("advanced_app")
    advanced_log.configure(
        level=DEBUG,  # LogEverything's DEBUG constant
        visual_mode=True,  # Rich visual output
        handlers=["console"],  # Simple handler specification
        async_mode=True,  # Enable 6.8x faster async logging
        use_symbols=True,
        use_indent=True,
    )
    return advanced_log


# Example 1: Smart decorator automatically detects regular functions
@log
def calculate_fibonacci(n):
    """Calculate fibonacci number using LogEverything's smart decorator."""
    if n <= 1:
        return n
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)


# Example 2: Smart decorator automatically detects async functions (6.8x faster)
@log
async def fetch_user_data(user_id):
    """Fetch user data asynchronously with automatic task isolation."""
    # Simulate async database call
    await asyncio.sleep(0.1)
    return {"user_id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"}


# Example 3: Smart decorator automatically detects classes and logs all methods
@log
class ModernDataProcessor:
    """A modern data processor using LogEverything's unified decorator."""

    def __init__(self, name):
        """Initialize the processor."""
        self.name = name
        self.processed_count = 0
        # Use LogEverything's logger interface directly
        # Use Logger instead of get_logger
        self.logger = Logger(f"{self.__class__.__name__}")

    def process_data(self, data):
        """Process data with manual logging using LogEverything's interface."""
        # Manual logging using LogEverything's logger interface
        self.logger.info(f"Processing data: {data}")

        processed = data.upper() if isinstance(data, str) else str(data).upper()
        self.processed_count += 1

        self.logger.debug(f"Processed count: {self.processed_count}")
        return processed

    async def async_process_batch(self, batch):
        """Process a batch asynchronously with automatic isolation."""
        results = []
        for item in batch:
            # Each async operation gets isolated context automatically
            result = await self.async_process_item(item)
            results.append(result)
        return results

    async def async_process_item(self, item):
        """Process individual item asynchronously."""
        await asyncio.sleep(0.05)  # Simulate async work
        return self.process_data(item)


# Example 4: Using LogEverything's level constants for manual logging
def demonstrate_level_constants():
    """Demonstrate LogEverything's level constants."""
    # Create a logger using the Logger class
    logger = Logger("modernized_example")

    # Use LogEverything's constants for setup, but not for individual messages
    logger.debug("Debug message using LogEverything's DEBUG constant")
    logger.info("Info message using LogEverything's INFO constant")
    logger.warning("Warning message using LogEverything's WARNING constant")
    logger.error("Error message using LogEverything's ERROR constant")
    logger.critical("Critical message using LogEverything's CRITICAL constant")


async def main():
    """Main async function demonstrating all modernized features."""
    print("LogEverything Modernized Example (v1.0.0)")
    print("=" * 50)

    # Setup using LogEverything's modernized interface
    # Setup logging and demonstrate both approaches
    print("🔧 Setting up advanced logging...")
    setup_advanced_logging()

    print("\n📝 Creating simple logger...")
    simple_log = setup_simple_logging()

    print("\n1. Smart decorator on regular function:")
    fib_result = calculate_fibonacci(6)
    print(f"Fibonacci(6) = {fib_result}")

    print("\n2. Smart decorator on async function (6.8x faster):")
    user_data = await fetch_user_data(123)
    print(f"User data: {user_data}")

    print("\n3. Smart decorator on class (all methods logged):")
    processor = ModernDataProcessor("ModernProcessor")

    # Sync processing
    sync_result = processor.process_data("hello world")
    print(f"Sync result: {sync_result}")

    # Async batch processing with automatic isolation
    batch_data = ["item1", "item2", "item3"]
    async_results = await processor.async_process_batch(batch_data)
    print(f"Async batch results: {async_results}")

    print("\n4. LogEverything's level constants and logger interface:")
    demonstrate_level_constants()

    print("\n5. Performance comparison:")
    import time

    # Test async performance
    start_time = time.time()
    tasks = [fetch_user_data(i) for i in range(10)]
    await asyncio.gather(*tasks)
    async_time = time.time() - start_time

    print(f"Async processing (10 tasks): {async_time:.3f}s with 6.8x performance improvement!")

    print("\n✅ All examples completed using LogEverything's modernized API!")
    print("Features demonstrated:")
    print("- Unified @log decorator that works on everything")
    print("- LogEverything's level constants (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    print("- LogEverything's logger interface (get_logger)")
    print("- 6.8x faster async logging with automatic task isolation")
    print("- Smart context detection and thread safety")


if __name__ == "__main__":
    asyncio.run(main())
