"""
Example demonstrating the simplified configuration with sensible defaults.

This example shows how LogEverything provides sensible defaults for common use cases
without requiring extensive configuration, while demonstrating visual formatting.
"""

import os
import sys

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything import Logger
from logeverything.decorators import log


def main():
    print("🚀 LogEverything Simplified Configuration Example\n")
    print("=" * 60)

    # ============================================================================
    # Example 1: Simplest Setup with Visual Formatting
    # ============================================================================
    print("\n📝 Example 1: Simple Logger with Visual Formatting")
    print("-" * 60)

    # Create a logger with default configuration
    logger = Logger("simplified_example")

    # Display configuration information
    logger.info("LogEverything is using default configuration")

    # Log messages of different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    @log(using="simplified_example", use_symbols=True)  # Visual formatting enabled
    def example_function(a, b):
        """Example function demonstrating the decorator with visual symbols."""
        logger.info("Inside example_function")
        return a + b

    result = example_function(10, 20)
    logger.info(f"Result: {result}")

    # ============================================================================
    # Example 2: Web Application Environment
    # ============================================================================
    print("\n\n🌐 Example 2: Web Application Configuration")
    print("-" * 60)

    # Create a logger with web-optimized configuration
    web_logger = Logger("web_app", level="INFO", format_type="visual")
    web_logger.info("Now using web environment configuration")
    web_logger.debug("This debug message may not appear depending on the level")

    @log(using="web_app", use_symbols=True)
    def process_request(user_id, action):
        """Simulate a web request handler with automatic indentation."""
        web_logger.info(f"Processing {action} for user {user_id}")
        return {"status": "success", "user_id": user_id}

    result = process_request("user123", "login")
    web_logger.info(f"API response: {result}")

    # ============================================================================
    # Summary
    # ============================================================================
    print("\n\n" + "=" * 60)
    print("✨ Key Features Demonstrated:")
    print("  • Simple logger creation with sensible defaults")
    print("  • Visual formatting with emojis (🔵 CALL, ✅ DONE)")
    print("  • Automatic indentation for nested operations")
    print("  • Different log levels (DEBUG, INFO, WARNING, ERROR)")
    print("  • Environment-specific configurations (script, web app)")
    print("=" * 60)


if __name__ == "__main__":
    main()
