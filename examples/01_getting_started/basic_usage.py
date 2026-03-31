"""
Basic usage example for LogEverything library (Modernized v1.0.0).

This example demonstrates the modernized core features of LogEverything using the new
simplified Logger API with explicit logger specifications for clean output.
Features demonstrated:
- Simple and advanced Logger configuration approaches
- Visual formatting with symbols and hierarchical context
- Decorator-based logging with explicit logger targeting
- Multiple handler types (Console, File, JSON)
- Function, I/O, and class method logging
"""

import random
import sys
import time
from pathlib import Path

# Add the parent directory to the path for imports to work when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from logeverything import CRITICAL, DEBUG, ERROR, INFO, WARNING, Logger
from logeverything.decorators import log
from logeverything.handlers import ConsoleHandler, FileHandler, JSONHandler


def setup_simple():
    """Set up logging using the simple Logger approach."""
    # Simple approach: Create a Logger and configure it
    log = Logger("example_app", auto_setup=False)
    log.configure(
        level=DEBUG,
        visual_mode=True,
        use_symbols=True,
        handlers=["console", "file"],
        file_path="simple_example.log",
    )
    return log


def setup_advanced():
    """Set up logging with multiple handlers using the advanced Logger approach."""
    # Advanced approach: Create Logger and configure with multiple handlers
    log = Logger("example_app", auto_setup=False)
    log.configure(
        level=DEBUG,
        visual_mode=True,
        use_symbols=True,
        handlers=[
            ConsoleHandler(level=INFO, colored=True),
            FileHandler(filename="advanced_example.log", level=DEBUG),
            JSONHandler(filename="advanced_example.json", level=WARNING),
        ],
    )

    # Return the configured logger
    return log


@log(using="example_app")  # Explicitly specify logger for clean output
def calculate_factorial(n):
    """Calculate factorial of n recursively."""
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)


@log(using="example_app")  # Use main app logger for configuration loading
def read_config(filename):
    """Simulate reading a configuration file."""
    # Simulate file reading
    time.sleep(0.1)
    return {
        "database": {
            "host": "localhost",
            "port": 5432,
            "username": "user",
            "password": "password",  # In real code, use secure methods
        },
        "api": {"url": "https://api.example.com", "key": "api_key_123456"},
        "logging": {"level": "INFO", "file": "app.log"},
    }


@log(using="example_app")  # Explicitly use main logger for data processing
class DataProcessor:
    """Example class for data processing with comprehensive logging."""

    def __init__(self, config):
        """Initialize with configuration."""
        self.config = config
        self.processed_items = 0

    def process_item(self, item):
        """Process a single item."""
        # Simulate processing
        time.sleep(0.05)
        result = {"id": item["id"], "status": "processed", "score": random.random() * 100}
        self.processed_items += 1
        return result

    def process_batch(self, items):
        """Process a batch of items."""
        results = []
        for item in items:
            try:
                result = self.process_item(item)
                results.append(result)
            except Exception as e:
                print(f"Error processing item {item['id']}: {e}")
        return results

    def get_stats(self):
        """Get processing statistics."""
        return {"processed_items": self.processed_items, "success_rate": 0.95}  # Simulated


def main():
    """Main function demonstrating LogEverything usage."""
    print("LogEverything Example Application")
    print("=================================")

    # Demonstrate both approaches
    print("\n🚀 Approach 1: Simple Logger Configuration")
    print("-" * 45)
    log_simple = setup_simple()
    log_simple.info("Simple logger configured successfully")
    log_simple.debug("This is a debug message from simple logger")
    log_simple.warning("This is a warning from simple logger")

    # Show hierarchical context
    with log_simple.context("demonstration"):
        log_simple.info("Inside context demonstration")
        log_simple.debug("Context provides visual hierarchy")

    print("\n🔧 Approach 2: Advanced Application-Wide Setup")
    print("-" * 48)
    log_advanced = setup_advanced()
    log_advanced.info("Advanced logger configured successfully")
    log_advanced.debug("This is a debug message from advanced logger")
    log_advanced.error("This is an error from advanced logger")

    # Component-specific loggers with advanced setup
    api_log = Logger("example_app.api")
    db_log = Logger("example_app.database")

    api_log.info("API component logger")
    db_log.info("Database component logger")

    print("\n📊 Function and Class Logging with Decorators")
    print("-" * 47)
    # Example 1: Function logging with explicit logger specification
    print("\n1. Calculating factorial with clean logging output:")
    result = calculate_factorial(5)
    print(f"Result: {result}")

    # Example 2: I/O operations logging
    print("\n2. Reading configuration file with I/O logging:")
    config = read_config("config.json")
    print(f"Config loaded: {len(config)} sections")

    # Example 3: Class method logging
    print("\n3. Processing data with class method logging:")
    processor = DataProcessor(config)

    # Create sample data
    items = [
        {"id": 1, "name": "Item 1", "value": 100},
        {"id": 2, "name": "Item 2", "value": 200},
        {"id": 3, "name": "Item 3", "value": 300},
    ]

    # Process items
    results = processor.process_batch(items)
    print(f"Processed {len(results)} items")

    # Get stats
    stats = processor.get_stats()
    print(f"Processing stats: {stats}")

    print("\nCheck example.log and example.json for the generated logs!")


if __name__ == "__main__":
    main()
