"""
Example demonstrating the use of context managers in LogEverything.

This example shows how to use context managers to temporarily modify logging
configuration for specific sections of code, and how they can make debugging
and logging management much cleaner.
"""

import logging
import time

from logeverything import (
    LoggingContext,
    QuietLoggingContext,
    TemporaryHandlerContext,
    VerboseLoggingContext,
    VisualLoggingContext,
    log_function,
    setup_logging,
)

# Initialize logging with INFO level and standard console output
setup_logging(level=logging.INFO, handlers=["console"])
logger = logging.getLogger("context_examples")


@log_function
def process_data(data):
    """Process some data, demonstrating context managers."""
    logger.info(f"Processing {len(data)} items")

    # Standard processing at INFO level
    for i, item in enumerate(data):
        if i % 10 == 0:  # Only log every 10th item at INFO level
            logger.info(f"Processing item {i}: {item}")
        process_item(item)


@log_function
def process_item(item):
    """Process a single item with different logging verbosity based on value."""
    # Regular processing uses standard logging level
    logger.debug(f"Item details: {item}")

    # Critical items need more detailed logging
    if item > 90:
        with VerboseLoggingContext():
            logger.info("Critical item detected - increasing log verbosity")
            logger.debug(f"Critical item processing details: {item}")
            complex_calculation(item)
            logger.debug("Critical item processing complete")

    # Routine items have reduced logging to avoid noise
    elif item < 10:
        with QuietLoggingContext():
            logger.info("Routine item detected - reducing log verbosity")
            routine_task(item)

    # Standard items use normal logging
    else:
        standard_task(item)

    return item * 2


@log_function
def complex_calculation(value):
    """Perform a complex calculation that benefits from detailed logging."""
    logger.debug(f"Starting complex calculation with value {value}")

    # Simulate different calculation phases
    stages = ["initialization", "processing", "validation", "finalization"]
    result = value

    for stage in stages:
        logger.debug(f"Stage: {stage}")
        # Simulate calculation work
        time.sleep(0.01)
        result *= 1.1

    logger.debug(f"Complex calculation complete, result: {result}")
    return result


@log_function
def routine_task(value):
    """A routine task with minimal logging."""
    result = value * 0.9
    logger.debug("Routine task completed")  # May not be shown in quiet mode
    return result


@log_function
def standard_task(value):
    """A standard task with normal logging."""
    result = value * 1.5
    logger.debug(f"Standard calculation: {value} * 1.5 = {result}")
    return result


def visual_demo():
    """Demonstrate visual logging context for improved readability."""
    logger.info("Starting visual logging demonstration")

    # Normal logging
    logger.info("This is standard logging output")
    logger.debug("A debug message with standard formatting")

    # Switch to visual formatting temporarily
    with VisualLoggingContext(use_symbols=True, use_indent=True, align_columns=True):
        logger.info("Visual logging activated for this section")
        logger.debug("Debug messages now have enhanced formatting")
        logger.warning("Warnings are more visible")
        logger.error("Errors stand out clearly")

        # Nested logging with indentation
        for i in range(3):
            logger.info(f"Processing item {i}")
            logger.debug(f"Item {i} details")

    # Back to normal logging
    logger.info("Returned to standard logging format")


def output_to_file_demo():
    """Demonstrate switching handlers with context managers."""
    logger.info("Starting handler switching demonstration")

    # Log to console
    logger.info("This message goes to the console")

    # Temporarily switch to file and JSON logging
    with TemporaryHandlerContext(["file", "json"]):
        logger.info("This message goes to a file and JSON")
        logger.warning("This warning is also directed to file and JSON")

        # Generate some nested logs
        for i in range(3):
            logger.info(f"File log entry {i}")

    # Back to console
    logger.info("This message goes to the console again")


def context_nesting_demo():
    """Demonstrate nesting of different logging contexts."""
    logger.info("Starting context nesting demonstration")

    # Base context: DEBUG level, visual mode on
    with LoggingContext(level=logging.DEBUG, visual_mode=True):
        logger.debug("Debug message in outer context")

        # Nested context: keep DEBUG but change visual formatting
        with VisualLoggingContext(use_symbols=True, use_indent=True):
            logger.debug("Debug message with visual enhancements")

            # Innermost context: temporarily quiet for a specific operation
            with QuietLoggingContext():
                logger.debug("This debug message should not appear")
                logger.warning("Only warnings and higher appear in quiet mode")

            # Back to visual mode with DEBUG level
            logger.debug("Debug message with visual enhancements again")

        # Back to first context: DEBUG but standard visual settings
        logger.debug("Back to standard debug logging")

    # Outside all contexts: back to initial settings
    logger.info("Back to initial logging settings")


def main():
    """Run all example functions."""
    logger.info("===== CONTEXT MANAGERS EXAMPLES =====")

    # Process a range of data values
    test_data = [5, 20, 50, 95]
    process_data(test_data)

    logger.info("\n===== VISUAL LOGGING EXAMPLE =====")
    visual_demo()

    logger.info("\n===== HANDLER SWITCHING EXAMPLE =====")
    output_to_file_demo()

    logger.info("\n===== CONTEXT NESTING EXAMPLE =====")
    context_nesting_demo()

    logger.info("\n===== EXAMPLES COMPLETE =====")


if __name__ == "__main__":
    main()
