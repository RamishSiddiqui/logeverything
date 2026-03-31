#!/usr/bin/env python3
"""
Comprehensive Context Managers Example for LogEverything.

This example demonstrates all available context managers in LogEverything with practical
use cases, showing how they can be used to temporarily modify logging behavior for
specific sections of code.

Context managers demonstrated:
- LoggingContext: Base context manager for custom configuration
- VerboseLoggingContext: Temporarily increase logging detail
- QuietLoggingContext: Temporarily reduce logging noise
- VisualLoggingContext: Temporarily enable visual enhancements
- TemporaryHandlerContext: Temporarily add or replace log handlers

Run with:
    python context_managers_comprehensive.py
"""

import logging
import sys
import time
from pathlib import Path

# Add the parent directory to the path for imports to work when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from logeverything import (
    LoggingContext,
    QuietLoggingContext,
    TemporaryHandlerContext,
    VerboseLoggingContext,
    VisualLoggingContext,
    log_function,
    setup_logging,
)
from logeverything.handlers import FileHandler, JSONHandler


def setup():
    """Set up initial logging configuration."""
    # Configure with INFO level and minimal visual features
    setup_logging(level="INFO", visual_mode=True, use_symbols=False, use_indent=False)
    return logging.getLogger("context_demo")


@log_function
def process_batch(items, batch_name="default"):
    """Process a batch of items with different logging strategies based on batch type."""
    logger = logging.getLogger("context_demo")
    logger.info(f"Processing batch '{batch_name}' with {len(items)} items")

    results = []
    for i, item in enumerate(items):
        # Log only some items to avoid noise
        if i % 5 == 0:
            logger.info(f"Processing item {i}: {item}")
        results.append(process_item(item, batch_name))

    logger.info(f"Batch '{batch_name}' processing complete")
    return results


@log_function
def process_item(value, batch_name):
    """Process a single item with specific handling based on value."""
    logger = logging.getLogger("context_demo")

    # Simulate some processing
    time.sleep(0.01)

    if value > 90:
        # Critical high-value items
        logger.info(f"Critical item detected: {value}")
        result = complex_calculation(value)
    elif value < 10:
        # Simple low-value items
        logger.debug(f"Simple item: {value}")
        result = value * 0.8
    else:
        # Normal items
        logger.debug(f"Normal item: {value}")
        result = value * 1.2

    return {"original": value, "processed": result, "batch": batch_name}


@log_function
def complex_calculation(value):
    """Perform a complex multi-stage calculation with detailed logging."""
    logger = logging.getLogger("context_demo")

    # Begin complex calculation
    logger.debug(f"Starting complex calculation for value {value}")

    # Simulate multi-stage calculation
    stages = ["initialize", "preprocess", "calculate", "validate", "finalize"]
    result = value

    for stage in stages:
        logger.debug(f"Stage '{stage}' starting for value {result}")
        time.sleep(0.02)  # Simulate processing

        # Apply different transformations per stage
        if stage == "initialize":
            result *= 1.1
        elif stage == "preprocess":
            result += 5
        elif stage == "calculate":
            result = result**1.05
        elif stage == "validate":
            if result > 1000:
                logger.warning(f"Very large result detected: {result}")
        elif stage == "finalize":
            result = round(result, 2)

        logger.debug(f"Stage '{stage}' completed, result: {result}")

    logger.debug(f"Complex calculation complete, final result: {result}")
    return result


def demonstrate_basic_context():
    """Demonstrate the base LoggingContext class."""
    logger = logging.getLogger("context_demo")

    print("\n=== BASIC LOGGING CONTEXT ===")
    logger.info("Starting basic context demonstration")

    # Generate some data
    items = [50, 51, 52, 53, 54]

    # Process with default settings
    logger.info("Processing with default INFO level")
    results_default = process_batch(items, "default")

    # Process with custom temporary settings
    logger.info("Processing with custom temporary settings")
    with LoggingContext(level="DEBUG", log_arguments=True, log_return_values=True):
        logger.info("Inside LoggingContext - DEBUG level with detailed function logs")
        results_custom = process_batch(items, "custom_context")

    # Back to default settings
    logger.info("Back to default logging settings")

    return results_default, results_custom


def demonstrate_verbose_context():
    """Demonstrate the VerboseLoggingContext for detailed debugging."""
    logger = logging.getLogger("context_demo")

    print("\n=== VERBOSE LOGGING CONTEXT ===")
    logger.info("Starting verbose context demonstration")

    # Generate data with some critical items
    items = [85, 92, 45, 97, 76]

    # First process normally
    logger.info("Processing items with normal logging")
    _ = process_batch(items, "normal_verbose")

    # Then process with verbose logging
    logger.info("Processing items with verbose logging")
    with VerboseLoggingContext():
        logger.info("Inside VerboseLoggingContext - maximum detail")
        logger.debug("Debug messages are now visible")
        _ = process_batch(items, "verbose_context")

    logger.debug("Outside context, this debug message may not be visible")


def demonstrate_quiet_context():
    """Demonstrate the QuietLoggingContext for reducing log noise."""
    logger = logging.getLogger("context_demo")

    print("\n=== QUIET LOGGING CONTEXT ===")
    logger.info("Starting quiet context demonstration")

    # Generate a large batch of mostly routine items
    items = list(range(10, 20))

    # First show normal logging
    logger.info("Processing with normal logging level")
    _ = process_batch(items[:5], "normal_volume")

    # Then reduce noise for the bulk processing
    logger.info("Processing with reduced logging noise")
    with QuietLoggingContext(level="WARNING"):
        logger.info("Inside QuietLoggingContext - this INFO message may not appear")
        logger.warning("But WARNING messages will still show")
        _ = process_batch(items, "quiet_context")

    logger.info("Back to normal logging volume")


def demonstrate_visual_context():
    """Demonstrate the VisualLoggingContext for enhanced visual formatting."""
    logger = logging.getLogger("context_demo")

    print("\n=== VISUAL LOGGING CONTEXT ===")
    logger.info("Starting visual context demonstration")

    # Generate mixed data
    items = [5, 25, 50, 75, 95]

    # First with minimal visual formatting
    logger.info("Processing with minimal visual formatting")
    _ = process_item(50, "minimal_visual")

    # Then with enhanced visuals
    logger.info("Processing with enhanced visual formatting")
    with VisualLoggingContext(use_symbols=True, use_indent=True, color_theme="bold"):
        logger.info("Inside VisualLoggingContext - enhanced visual output")
        _ = process_batch(items, "visual_context")

    logger.info("Back to minimal visual formatting")


def demonstrate_handler_context():
    """Demonstrate the TemporaryHandlerContext for changing log destinations."""
    logger = logging.getLogger("context_demo")

    print("\n=== TEMPORARY HANDLER CONTEXT ===")
    logger.info("Starting handler context demonstration")

    # Create special items that need detailed tracking
    items = [91, 92, 93, 94, 95]

    # Process with default handlers (console only)
    logger.info("Processing with default handlers")
    _ = process_batch(items[:2], "default_handlers")

    # Add a temporary JSON handler for structured logging
    logger.info("Adding a temporary JSON handler")
    with TemporaryHandlerContext(JSONHandler(filename="context_demo.json")):
        logger.info("Inside TemporaryHandlerContext - logging to both console and JSON")
        _ = process_batch(items, "json_context")

    # Replace all handlers with a file handler temporarily
    logger.info("Replacing handlers with a dedicated file handler")
    with TemporaryHandlerContext(FileHandler(filename="context_demo.log"), replace=True):
        # This will only go to the file, not console
        logger.info("Inside TemporaryHandlerContext with replace=True")
        logger.info("This message only appears in the log file, not console")
        _ = process_batch(items, "file_only_context")

    logger.info("Back to default handlers")


def demonstrate_nested_contexts():
    """Demonstrate nested context managers for complex logging scenarios."""
    logger = logging.getLogger("context_demo")

    print("\n=== NESTED CONTEXTS ===")
    logger.info("Starting nested contexts demonstration")

    # Create test data
    items = [15, 45, 75, 95]

    # Use multiple nested contexts to build a complex logging configuration
    with VerboseLoggingContext():
        logger.info("Level 1: VerboseLoggingContext - showing detailed logs")
        logger.debug("Debug messages are visible at this level")

        _ = process_item(45, "level1")

        with VisualLoggingContext(use_symbols=True, use_indent=True):
            logger.info("Level 2: Added VisualLoggingContext - visual enhancements")
            _ = process_item(75, "level2")

            with TemporaryHandlerContext(JSONHandler(filename="nested_contexts.json")):
                logger.info("Level 3: Added JSONHandler - logging to multiple destinations")
                _ = process_item(95, "level3")

                with QuietLoggingContext():
                    logger.info(
                        "Level 4: Added QuietLoggingContext - reduced noise for specific operation"
                    )
                    logger.debug(
                        "This debug message may be suppressed despite the outer VerboseLoggingContext"
                    )
                    _ = process_item(15, "level4")

                logger.info(
                    "Back to Level 3 - full verbosity with visual formatting and JSON output"
                )

            logger.info("Back to Level 2 - verbose with visual formatting, but no JSON output")

        logger.info("Back to Level 1 - verbose but no special visual formatting")

    logger.info("Back to original logging configuration")


def main():
    """Run the demonstration of all context manager types."""
    logger = setup()

    # Introduction
    logger.info("=" * 60)
    logger.info("LogEverything Context Managers Comprehensive Example")
    logger.info("=" * 60)

    try:
        # Demonstrate each context manager type
        demonstrate_basic_context()
        demonstrate_verbose_context()
        demonstrate_quiet_context()
        demonstrate_visual_context()
        demonstrate_handler_context()
        demonstrate_nested_contexts()

        print("\nContext Managers demonstration complete!")
        logger.info("All context manager demonstrations completed successfully")

        print("\nCheck the following files for evidence of the temporary handlers:")
        print("- context_demo.json")
        print("- context_demo.log")
        print("- nested_contexts.json")

    except Exception as e:
        logger.exception(f"Error during demonstration: {e}")


if __name__ == "__main__":
    main()
