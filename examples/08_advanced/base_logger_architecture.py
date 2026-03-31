#!/usr/bin/env python3
"""
BaseLogger Architecture Example

This example demonstrates the new BaseLogger architecture and how
configuration is now done through logger instances rather than a
global configure function.
"""

import sys
from pathlib import Path

# Add the parent directory to the path for imports to work when running directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio

from logeverything import AsyncLogger, BaseLogger, Logger


# Example 1: Using the standard Logger with instance configuration
def demo_logger():
    print("=== Logger with Instance Configuration ===")

    # Create a logger instance
    log = Logger("my_app")

    # Configure it using the instance method (no global configure needed!)
    log.configure(level="DEBUG", visual_mode=True, use_symbols=True, use_indent=True)

    log.info("Application started")
    log.debug("Debug information")
    log.warning("This is a warning")


# Example 2: Creating a custom logger by inheriting from BaseLogger
class CustomLogger(BaseLogger):
    """
    Example custom logger that adds a prefix to all messages.
    """

    def __init__(self, name: str, prefix: str = "[CUSTOM]"):
        super().__init__(name)
        self.prefix = prefix

    def configure(self, **kwargs):
        """Configure the custom logger."""
        # Store configuration
        self._config.update(kwargs)

        # Set up the underlying Python logger
        level = kwargs.get("level", "INFO")
        if isinstance(level, str):
            level = getattr(__import__("logging"), level.upper())
        self._logger.setLevel(level)

        # Add a simple console handler if none exists
        if not self._logger.handlers:
            import logging

            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

        return self

    def _log_message(self, level, message, *args, **kwargs):
        """Add prefix to all messages."""
        prefixed_message = f"{self.prefix} {message}"
        self._logger.log(level, prefixed_message, *args, **kwargs)


# Example 3: Using AsyncLogger with instance configuration
async def demo_async_logger():
    print("\n=== AsyncLogger with Instance Configuration ===")

    # Create an async logger instance
    async_log = AsyncLogger("my_async_app")

    # Configure it using the async instance method
    await async_log.configure(level="INFO", visual_mode=True, async_mode=True, use_symbols=True)

    async_log.info("Async application started")
    async_log.debug("Async debug information")


def demo_custom_logger():
    print("\n=== Custom Logger Example ===")

    # Create and configure our custom logger
    custom_log = CustomLogger("my_custom_app", "[MY-PREFIX]")
    custom_log.configure(level="DEBUG")

    custom_log.info("This message has a custom prefix")
    custom_log.debug("Debug message with prefix")
    custom_log.error("Error message with prefix")


async def main():
    print("LogEverything BaseLogger Architecture Demo")
    print("=" * 50)

    # Demo standard Logger
    demo_logger()

    # Demo AsyncLogger
    await demo_async_logger()

    # Demo custom logger
    demo_custom_logger()

    print("\n✅ Key Benefits of BaseLogger Architecture:")
    print("   • No global configure function confusion")
    print("   • Each logger instance manages its own configuration")
    print("   • Easy to create custom logger types")
    print("   • Consistent API across all logger types")
    print("   • Future extensibility for specialized loggers")


if __name__ == "__main__":
    asyncio.run(main())
