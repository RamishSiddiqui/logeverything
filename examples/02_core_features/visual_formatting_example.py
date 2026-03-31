#!/usr/bin/env python
"""
Visual Formatting Example for LogEverything

This example demonstrates the enhanced visual formatting capabilities of LogEverything,
including pretty formatting, colored console output, and hierarchical visualization.
"""

import logging
import os
import platform
import sys
from datetime import datetime

# Add parent directory to path so we can import logeverything from the development directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything import (
    EnhancedConsoleHandler,
    FormattedFileHandler,
    Logger,
    PrettyFormatter,
    log_class,
    log_function,
)


def demonstration_1_basic_setup():
    """Basic visual mode setup demonstration."""
    print("\n\n===== DEMONSTRATION 1: BASIC VISUAL MODE =====")

    # Create a custom handler with visual formatting
    console_handler = EnhancedConsoleHandler(
        use_colors=True,
        use_symbols=True,
        use_indent=True,
        align_columns=True,
        color_theme="default",
    )

    # Setup with visual mode enabled using modern API - use unique logger name
    logger = Logger("demo1_basic_visual")
    logger.set_level("DEBUG")  # Set level directly
    logger.add_handler(console_handler)  # Add our custom handler

    # Generate some logs at different levels
    logger.debug("This is a debug message with visual formatting")
    logger.info("This is an info message with visual formatting")
    logger.warning("This is a warning message with visual formatting")
    logger.error("This is an error message with visual formatting")
    logger.critical("This is a critical message with visual formatting")

    # Cleanup handler
    console_handler.close()


def demonstration_2_custom_handlers():
    """Demonstrating custom visual handlers."""
    print("\n\n===== DEMONSTRATION 2: CUSTOM VISUAL HANDLERS =====")

    # Create custom console handlers with different themes
    themes = ["default", "bold", "pastel", "monochrome"]

    for i, theme in enumerate(themes):
        # Create a themed console handler
        handler = EnhancedConsoleHandler(
            use_colors=True,
            use_symbols=True,
            use_indent=True,
            align_columns=True,
            color_theme=theme,
        )

        # Configure a logger with ONLY this handler (no default handlers)
        theme_logger = Logger(f"theme_{theme}")
        theme_logger.configure(level="DEBUG")
        theme_logger.remove()  # Remove all default handlers
        theme_logger.add_handler(handler)  # Add only our custom handler

        # Show the theme
        print(f"\n--- Theme: {theme.upper()} ---")
        theme_logger.info(f"Sample log entry with the '{theme}' color theme")
        theme_logger.warning("Warning message in this theme")

        # Cleanup
        handler.close()


@log_function(using="demo3_hierarchical")
def factorial(n):
    """Calculate factorial recursively."""
    logger = Logger("demo3_hierarchical")
    logger.debug(f"Computing factorial for {n}")

    if n <= 1:
        logger.debug("Reached base case, returning 1")
        return 1

    result = n * factorial(n - 1)
    logger.debug(f"Factorial calculation: {n} * factorial({n-1}) = {result}")
    return result


@log_function(using="demo3_hierarchical")
def compute_statistics(data):
    """Compute various statistics for a dataset."""
    logger = Logger("demo3_hierarchical")
    logger.info(f"Computing statistics for dataset with {len(data)} elements")

    # Calculate some statistics
    total = sum(data)
    average = total / len(data)
    maximum = max(data)
    minimum = min(data)

    logger.debug(f"Sum: {total}")
    logger.info(f"Average: {average:.2f}")
    logger.debug(f"Max: {maximum}, Min: {minimum}")

    # Compute factorial of a small number for demonstration
    if minimum > 0 and minimum < 10:
        logger.info(f"Computing factorial of minimum value: {minimum}")
        fact = factorial(minimum)
        logger.info(f"Factorial of {minimum} is {fact}")

    return {"sum": total, "average": average, "max": maximum, "min": minimum}


@log_class(using="demo3_hierarchical")
class DataProcessor:
    """A class to demonstrate hierarchical logging with visual formatting."""

    def __init__(self, name):
        self.name = name
        self.logger = Logger("demo3_hierarchical")
        self.logger.info(f"Created DataProcessor: {name}")

    def process_batch(self, items):
        """Process a batch of items with visual hierarchical logging."""
        self.logger.info(f"Processing batch of {len(items)} items")

        results = []
        for i, item in enumerate(items):
            self.logger.debug(f"Processing item {i+1}/{len(items)}")
            result = self._process_item(item)
            results.append(result)

        self.logger.info(f"Batch processing complete")
        return results

    def _process_item(self, item):
        """Process a single item (internal method)."""
        self.logger.debug(f"Processing item: {item}")

        # Simulate some processing steps
        try:
            # Artificial error for some values
            if isinstance(item, int) and item % 5 == 0:
                raise ValueError(f"Cannot process multiples of 5: {item}")

            result = item**2
            self.logger.debug(f"Processed successfully: {item} -> {result}")
            return result

        except Exception as e:
            self.logger.error(f"Error processing item: {str(e)}")
            return None


def demonstration_3_hierarchical_visualization():
    """Demonstrate hierarchical logging visualization."""
    print("\n\n===== DEMONSTRATION 3: HIERARCHICAL VISUALIZATION =====")

    # Set up logging with a formatted file handler
    log_file = os.path.join(os.path.dirname(__file__), "visual_demo.log")

    # Create the handlers
    console_handler = EnhancedConsoleHandler(
        use_colors=True, use_symbols=True, use_indent=True, align_columns=True, color_theme="bold"
    )

    file_handler = FormattedFileHandler(
        log_file,
        mode="w",
        pretty=True,
        use_symbols=True,
        use_indent=True,
        align_columns=True,
        encoding="utf-8",
    )

    # Create logger with LogEverything configuration for decorators
    logger = Logger("demo3_hierarchical")

    # Configure with minimal settings but enable decorator features
    logger.configure(
        level="DEBUG",
        log_entry_exit=True,
        log_arguments=True,
        log_return_values=True,
        handlers=[],  # Explicitly pass empty handlers list
    )

    # Remove any handlers that were added by configure
    logger.remove()

    # Add ONLY our custom handlers
    logger.add_handler(console_handler)
    logger.add_handler(file_handler)

    # Generate hierarchical logs
    logger.info("Starting hierarchical visualization demo")

    # Process some data
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    stats = compute_statistics(data)

    # Use the DataProcessor class
    processor = DataProcessor("DemoProcessor")
    batch = [3, 5, 7, 10, 12, 15]
    results = processor.process_batch(batch)

    logger.info(f"Demo completed, processed {len(batch)} items with {results.count(None)} errors")
    logger.info(f"Log file written to: {log_file}")

    # Cleanup handlers
    console_handler.close()
    file_handler.close()


def demonstration_4_platform_compatibility():
    """Demonstrate platform detection and compatibility features."""
    print("\n\n===== DEMONSTRATION 4: PLATFORM COMPATIBILITY =====")

    # Create handlers with different platform settings
    console_standard = EnhancedConsoleHandler(
        use_colors=True, use_symbols=True, use_indent=True, align_columns=True
    )

    console_ascii = EnhancedConsoleHandler(
        use_colors=True,
        use_symbols=False,  # No Unicode symbols
        use_indent=True,
        align_columns=True,
        ascii_only=True,  # Use ASCII box drawing characters
    )

    console_minimal = EnhancedConsoleHandler(
        use_colors=False,  # No colors
        use_symbols=False,  # No Unicode symbols
        use_indent=True,
        align_columns=False,  # No column alignment
        ascii_only=True,  # Use ASCII box drawing characters
    )

    # Configure loggers with ONLY custom handlers (no default handlers)
    standard_logger = Logger("standard")
    standard_logger.configure(level="DEBUG")
    standard_logger.remove()  # Remove all default handlers
    standard_logger.add_handler(console_standard)

    ascii_logger = Logger("ascii")
    ascii_logger.configure(level="DEBUG")
    ascii_logger.remove()  # Remove all default handlers
    ascii_logger.add_handler(console_ascii)

    minimal_logger = Logger("minimal")
    minimal_logger.configure(level="DEBUG")
    minimal_logger.remove()  # Remove all default handlers
    minimal_logger.add_handler(console_minimal)

    # Show the platform
    print(f"Current platform: {platform.system()}")
    print(f"Terminal encoding: {sys.stdout.encoding}\n")

    # Log with different compatibility modes
    print("--- Standard mode (Unicode + Colors): ---")
    standard_logger.info("This message uses Unicode symbols and ANSI colors")
    standard_logger.warning("Warning message with standard formatting")

    print("\n--- ASCII mode (ASCII + Colors): ---")
    ascii_logger.info("This message uses ASCII only with ANSI colors")
    ascii_logger.warning("Warning message with ASCII formatting")

    print("\n--- Minimal mode (ASCII, no colors): ---")
    minimal_logger.info("This message uses minimal formatting (ASCII, no colors)")
    minimal_logger.warning("Warning message with minimal formatting")

    # Cleanup
    console_standard.close()
    console_ascii.close()
    console_minimal.close()


if __name__ == "__main__":
    # Run all demonstrations
    demonstration_1_basic_setup()
    demonstration_2_custom_handlers()
    demonstration_3_hierarchical_visualization()
    demonstration_4_platform_compatibility()

    print("\n\nVisual formatting demonstrations complete.")
    print("Check the generated visual_demo.log file for the hierarchical log output.")
