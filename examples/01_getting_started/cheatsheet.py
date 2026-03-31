#!/usr/bin/env python3
"""
LogEverything Quick Reference Cheat Sheet
=========================================

This file provides a comprehensive quick reference for all LogEverything features.
Perfect for rapid lookup and copy-paste usage.

Unicode Symbols:
🔵 Debug    ✅ Success    ℹ️ Info    ⚠️ Warning    ❌ Error
"""

import asyncio

from logeverything import AsyncLogger, Logger, get_logger
from logeverything.decorators import log

# =============================================================================
# 1. BASIC LOGGER CREATION
# =============================================================================

# Method 1: Direct instantiation
logger = Logger("MyApp")

# Method 2: Factory function
logger2 = get_logger("MyApp2")

# Method 3: Async logger
async_logger = AsyncLogger("AsyncApp")

# =============================================================================
# 2. BASIC LOGGING LEVELS
# =============================================================================


def basic_logging_example():
    """🔵 Basic logging levels demonstration"""
    logger.debug("🔵 Debug message - detailed diagnostic info")
    logger.info("ℹ️ Info message - general information")
    logger.warning("⚠️ Warning message - something unexpected")
    logger.error("❌ Error message - something went wrong")
    logger.critical("🚨 Critical message - serious problem")


# =============================================================================
# 3. DECORATORS QUICK REFERENCE
# =============================================================================


@log  # Auto-detects logger
def decorated_function(x, y):
    """✅ Function with automatic logging"""
    return x + y


@log(logger=logger)  # Explicit logger
def explicit_logger_function(name):
    """✅ Function with explicit logger"""
    return f"Hello, {name}!"


@log(level="warning")  # Custom log level
def warning_level_function(data):
    """⚠️ Function logged at warning level"""
    return len(data)


# =============================================================================
# 4. ASYNC LOGGING
# =============================================================================


@log(logger=async_logger)
async def async_function(delay):
    """✅ Async function with logging"""
    await asyncio.sleep(delay)
    return f"Waited {delay} seconds"


# =============================================================================
# 5. CONTEXT MANAGERS
# =============================================================================


def context_example():
    """📁 Context manager examples"""
    # Basic context
    with logger.context("Processing data"):
        logger.info("ℹ️ Step 1: Loading data")
        logger.info("ℹ️ Step 2: Processing")

    # Nested contexts
    with logger.context("Main Process"):
        with logger.context("Sub Process"):
            logger.info("ℹ️ Deep nested operation")


async def async_context_example():
    """📁 Async context manager example"""
    async with async_logger.context("Async Operation"):
        await asyncio.sleep(0.1)
        async_logger.info("ℹ️ Async operation complete")


# =============================================================================
# 6. CONFIGURATION QUICK REFERENCE
# =============================================================================


def configuration_examples():
    """⚙️ Logger configuration patterns"""

    # Console + File logging - ensure visual consistency
    config_logger = Logger(
        "ConfigExample",
        console=True,
        file_path="app.log",
        visual_mode=True,  # Ensure consistent formatting
        use_symbols=True,  # Ensure bracket format
    )

    # JSON logging - ensure visual consistency
    json_logger = Logger(
        "JSONExample",
        json_file="data.json",
        visual_mode=True,  # Ensure consistent formatting
        use_symbols=True,  # Ensure bracket format
    )

    # Custom format - should still use our PrettyFormatter for consistency
    custom_logger = Logger(
        "CustomExample",
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",  # Removed :%(lineno)d to maintain alignment
        visual_mode=True,  # Ensure it uses our PrettyFormatter
        use_symbols=True,  # Maintain consistent visual style
    )

    return config_logger, json_logger, custom_logger


# =============================================================================
# 7. ERROR HANDLING PATTERNS
# =============================================================================


def error_handling_example():
    """🚨 Error handling with logging"""
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.error(f"❌ Division error: {e}")
        logger.exception("❌ Full traceback:")


# =============================================================================
# 8. PERFORMANCE MONITORING
# =============================================================================


@log(include_performance=True)
def performance_monitored_function():
    """📊 Function with performance monitoring"""
    import time

    time.sleep(0.1)
    return "Performance tracked"


# =============================================================================
# 9. CLASS-BASED LOGGING
# =============================================================================


class ExampleClass:
    """📦 Class with integrated logging"""

    def __init__(self):
        self.logger = Logger(self.__class__.__name__)

    @log
    def method_one(self, data):
        """✅ Auto-logged method"""
        return data.upper()

    @log(logger="class_logger")
    def method_two(self, data):
        """✅ Method with custom logger name"""
        return data.lower()


# =============================================================================
# 10. MAIN DEMONSTRATION
# =============================================================================


def main():
    """🚀 Cheat Sheet Demonstration"""
    print("🔵 LogEverything Cheat Sheet Demo")
    print("=" * 50)

    # Basic logging
    print("\n1️⃣ Basic Logging:")
    basic_logging_example()

    # Decorators
    print("\n2️⃣ Decorated Functions:")
    result1 = decorated_function(5, 3)
    result2 = explicit_logger_function("World")
    result3 = warning_level_function([1, 2, 3, 4, 5])

    # Context managers
    print("\n3️⃣ Context Managers:")
    context_example()

    # Configuration
    print("\n4️⃣ Different Configurations:")
    config_logger, json_logger, custom_logger = configuration_examples()
    config_logger.info("ℹ️ Console + File logger")
    json_logger.info("ℹ️ JSON logger")
    custom_logger.info("ℹ️ Custom format logger")

    # Error handling
    print("\n5️⃣ Error Handling:")
    error_handling_example()

    # Performance
    print("\n6️⃣ Performance Monitoring:")
    performance_result = performance_monitored_function()

    # Class-based
    print("\n7️⃣ Class-based Logging:")
    example_obj = ExampleClass()
    example_obj.method_one("hello world")
    example_obj.method_two("HELLO WORLD")


async def async_main():
    """🚀 Async examples demonstration"""
    print("\n8️⃣ Async Logging:")

    # Async function
    await async_function(0.1)

    # Async context
    await async_context_example()


if __name__ == "__main__":
    print("🔵 Starting LogEverything Cheat Sheet...")

    # Run sync examples
    main()

    # Run async examples
    print("\n" + "=" * 50)
    asyncio.run(async_main())

    print("\n✅ Cheat sheet demonstration complete!")
    print("📚 Copy any patterns above for your own use.")
