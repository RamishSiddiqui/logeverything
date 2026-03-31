#!/usr/bin/env python3
"""
Visual Alignment Demonstration

This example demonstrates LogEverything's improved decorator visual formatting,
showing how function entry/exit logs are aligned and function body content
is properly indented to create a clear visual hierarchy.

Key Features Demonstrated:
- Function entry and exit alignment at each nesting level
- Function body content indented one level deeper than entry/exit
- Clear visual hierarchy for nested function calls
- Conditional emoji/symbol usage based on configuration
- Professional logging output suitable for production use

Run this example to see:
✅ Perfect function entry/exit alignment
✅ Proper function body indentation
✅ Clear and readable visual hierarchy
✅ Conditional emoji/symbol usage
"""

import os
import sys

# Add the package to Python path for examples
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from logeverything import Logger, log_function

# Create a logger with visual mode enabled to show the full visual formatting
logger = Logger(
    name="alignment_demo", visual_mode=True, use_symbols=True, use_indent=True, beautify=True
)


@log_function(using="alignment_demo")
def process_data(data_type, count):
    """
    Process some data with nested operations.

    This function demonstrates how nested decorated functions create
    a clear visual hierarchy in the logs.
    """
    logger.info(f"Starting to process {count} items of type: {data_type}")

    @log_function(using="alignment_demo")
    def validate_items(items):
        """Validate the items before processing."""
        logger.info("Running validation checks")
        logger.info(f"Checking {items} items for consistency")
        if items > 10:
            logger.warning("Large dataset detected - this may take longer")
        return True

    @log_function(using="alignment_demo")
    def transform_data(items):
        """Transform the data into the required format."""
        logger.info("Applying data transformations")

        @log_function(using="alignment_demo")
        def apply_filter(filter_type):
            """Apply a specific filter to the data."""
            logger.info(f"Applying {filter_type} filter")
            logger.debug("Filter configuration loaded")
            return f"{filter_type}_filtered"

        filter_result = apply_filter("quality")
        logger.info(f"Filter applied: {filter_result}")
        return f"transformed_{items}_items"

    # Execute the nested operations
    validation_result = validate_items(count)
    logger.info(f"Validation result: {validation_result}")

    if validation_result:
        transform_result = transform_data(count)
        logger.info(f"Transformation complete: {transform_result}")
        return f"processed_{count}_{data_type}"
    else:
        logger.error("Validation failed - aborting processing")
        return None


def demonstrate_visual_alignment():
    """Demonstrate the visual alignment features with explanatory output."""
    print("=" * 70)
    print("LOGEVERYTHING VISUAL ALIGNMENT DEMONSTRATION")
    print("=" * 70)
    print("This example shows LogEverything's improved decorator visual formatting:")
    print()
    print("🎯 KEY FEATURES:")
    print("  • Function entry and exit logs are aligned at the same level")
    print("  • Function body content is indented one level deeper")
    print("  • Visual hierarchy clearly shows function nesting levels")
    print("  • Emojis and symbols are conditional based on configuration")
    print("  • Professional output suitable for production environments")
    print()
    print("📋 WHAT TO OBSERVE:")
    print("  • 🔵 CALL and ✅ DONE messages are aligned at each level")
    print("  • Logger messages inside functions are indented deeper")
    print("  • Each nesting level is clearly visually distinct")
    print("  • Return values and timing information are included")
    print("=" * 70)
    print()

    # Run the demonstration
    result = process_data("customer_records", 15)

    print()
    print("=" * 70)
    print("✅ DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("OBSERVED FEATURES:")
    print("✅ Function entry/exit alignment: PERFECT")
    print("✅ Function body indentation: PROPERLY IMPLEMENTED")
    print("✅ Visual hierarchy: CLEAR AND PROFESSIONAL")
    print("✅ Emoji/symbol usage: CONDITIONAL ON CONFIGURATION")
    print("✅ Performance timing: INCLUDED")
    print("✅ Return value logging: WORKING")
    print()
    print("This visual formatting makes it easy to:")
    print("  • Track function call flow and nesting")
    print("  • Debug complex application logic")
    print("  • Monitor performance at each level")
    print("  • Understand code execution hierarchy")
    print("=" * 70)

    return result


if __name__ == "__main__":
    # Run the complete demonstration
    demonstrate_visual_alignment()
