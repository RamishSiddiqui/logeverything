#!/usr/bin/env python3
"""
Logger Creation Methods Example

This example shows the different ways users can create and use loggers
with the new BaseLogger architecture.
"""

import sys
from pathlib import Path

# Add the parent directory to the path for imports to work when running directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio

from logeverything import AsyncLogger, BaseLogger, Logger, get_logger


def demo_logger_creation_methods():
    """Demonstrate different ways to create and use loggers."""

    print("=== Logger Creation Methods ===\n")

    # Method 1: Direct Logger instantiation (Recommended)
    print("1. Direct Logger instantiation:")
    log1 = Logger("my_app")
    log1.configure(level="INFO", visual_mode=True, use_symbols=True)
    log1.info("Logger created via direct instantiation")

    # Method 2: Using get_logger factory function
    print("\n2. Using get_logger factory function:")
    log2 = get_logger("my_app.database")
    log2.info("Logger created via get_logger factory")

    # Method 3: Multiple loggers for different components
    print("\n3. Component-specific loggers:")
    auth_log = Logger("my_app.auth")
    auth_log.configure(level="DEBUG", use_symbols=True)

    api_log = Logger("my_app.api")
    api_log.configure(level="INFO", use_symbols=True)

    db_log = get_logger("my_app.database")  # Using factory function

    auth_log.debug("Authentication module initialized")
    api_log.info("API server started")
    db_log.info("Database connection established")


async def demo_async_logger():
    """Demonstrate AsyncLogger usage."""
    print("\n4. AsyncLogger for async applications:")

    async_log = AsyncLogger("my_async_app")
    await async_log.configure(level="INFO", visual_mode=True, use_symbols=True, async_mode=True)

    async_log.info("Async application started")


def demo_custom_logger():
    """Demonstrate custom logger creation."""
    print("\n5. Custom Logger (inheriting from BaseLogger):")

    class TimestampLogger(BaseLogger):
        """Custom logger that adds timestamps to messages."""

        def configure(self, **kwargs):
            self._config.update(kwargs)

            # Set up basic logging
            import logging

            level = kwargs.get("level", "INFO")
            if isinstance(level, str):
                level = getattr(logging, level.upper())
            self._logger.setLevel(level)

            if not self._logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
                handler.setFormatter(formatter)
                self._logger.addHandler(handler)

            return self

        def _log_message(self, level, message, *args, **kwargs):
            # Add custom prefix
            custom_message = f"[TIMESTAMP] {message}"
            self._logger.log(level, custom_message, *args, **kwargs)

        def _create_bound_logger(self, **kwargs):
            """Create a bound logger with additional context."""
            bound = TimestampLogger(self._name)
            bound._config = self._config.copy()
            bound._context = {**self._context, **kwargs}
            bound.configure(**self._config)
            return bound

        def _cleanup(self):
            """Clean up logger resources."""
            # Remove all handlers to clean up
            for handler in self._logger.handlers[:]:
                self._logger.removeHandler(handler)
                handler.close()

    # Use the custom logger
    custom_log = TimestampLogger("custom_app")
    custom_log.configure(level="INFO")
    custom_log.info("This is a custom logger with timestamp prefix")


async def main():
    print("LogEverything Logger Creation Methods Demo")
    print("=" * 50)

    # Demo different logger creation methods
    demo_logger_creation_methods()

    # Demo async logger
    await demo_async_logger()

    # Demo custom logger
    demo_custom_logger()

    print("\n✅ Key Benefits:")
    print("   • Logger() - Direct instantiation for most use cases")
    print("   • get_logger() - Factory function for getting loggers anywhere")
    print("   • AsyncLogger() - Optimized for async applications")
    print("   • BaseLogger - Create custom logger types")
    print("   • Each logger manages its own configuration")
    print("   • Consistent API across all logger types")


if __name__ == "__main__":
    asyncio.run(main())
