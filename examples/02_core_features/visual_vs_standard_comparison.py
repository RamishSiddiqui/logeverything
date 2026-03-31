#!/usr/bin/env python3
"""
Visual vs Non-Visual Mode Comparison

This example demonstrates the difference between LogEverything's visual
formatting mode and standard logging mode, helping users understand
when to use each approach.

Features Demonstrated:
- Side-by-side comparison of visual vs standard formatting
- Same code with different logger configurations
- Production vs development logging scenarios
- Performance implications of visual formatting
- Configuration best practices

Perfect for understanding when and how to use visual formatting
in different environments and use cases.
"""

import os
import sys

# Add the package to Python path for examples
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from logeverything import Logger, log_function

# Create two loggers: one with visual formatting, one without
visual_logger = Logger(
    name="visual_demo", visual_mode=True, use_symbols=True, use_indent=True, beautify=True
)

standard_logger = Logger(
    name="standard_demo", visual_mode=False, use_symbols=False, use_indent=False, beautify=False
)


@log_function(using="visual_demo")
def process_order_visual(order_id, items):
    """Process an order using visual formatting."""
    visual_logger.info(f"Processing order {order_id} with {len(items)} items")

    @log_function(using="visual_demo")
    def validate_order(order_data):
        """Validate order data."""
        visual_logger.info("Validating order data")
        visual_logger.debug("Checking item availability")
        if len(order_data) > 5:
            visual_logger.warning("Large order detected")
        return True

    @log_function(using="visual_demo")
    def calculate_total(items_list):
        """Calculate order total."""
        visual_logger.info("Calculating order total")
        total = sum(item.get("price", 0) for item in items_list)
        visual_logger.info(f"Order total: ${total:.2f}")
        return total

    validation_result = validate_order(items)
    if validation_result:
        total = calculate_total(items)
        visual_logger.info(f"Order {order_id} processed successfully")
        return total
    else:
        visual_logger.error("Order validation failed")
        return None


@log_function(using="standard_demo")
def process_order_standard(order_id, items):
    """Process an order using standard formatting."""
    standard_logger.info(f"Processing order {order_id} with {len(items)} items")

    @log_function(using="standard_demo")
    def validate_order(order_data):
        """Validate order data."""
        standard_logger.info("Validating order data")
        standard_logger.debug("Checking item availability")
        if len(order_data) > 5:
            standard_logger.warning("Large order detected")
        return True

    @log_function(using="standard_demo")
    def calculate_total(items_list):
        """Calculate order total."""
        standard_logger.info("Calculating order total")
        total = sum(item.get("price", 0) for item in items_list)
        standard_logger.info(f"Order total: ${total:.2f}")
        return total

    validation_result = validate_order(items)
    if validation_result:
        total = calculate_total(items)
        standard_logger.info(f"Order {order_id} processed successfully")
        return total
    else:
        standard_logger.error("Order validation failed")
        return None


def run_comparison():
    """Run side-by-side comparison of visual vs standard formatting."""

    # Sample order data
    sample_order = [
        {"name": "Widget A", "price": 19.99},
        {"name": "Widget B", "price": 29.99},
        {"name": "Widget C", "price": 39.99},
    ]

    print("=" * 90)
    print("VISUAL vs STANDARD FORMATTING COMPARISON")
    print("=" * 90)
    print()
    print("This example shows the same code with two different logging configurations.")
    print("Notice the difference in readability and visual hierarchy!")
    print()

    print("🎨 VISUAL FORMATTING MODE (Development/Debugging)")
    print("-" * 50)
    print("Perfect for:")
    print("• Development and debugging")
    print("• Understanding complex code flow")
    print("• Training and documentation")
    print("• Interactive environments")
    print()

    visual_result = process_order_visual("ORD-001", sample_order)

    print()
    print("📄 STANDARD FORMATTING MODE (Production/Performance)")
    print("-" * 50)
    print("Perfect for:")
    print("• Production environments")
    print("• High-performance applications")
    print("• Log aggregation systems")
    print("• Automated processing")
    print()

    standard_result = process_order_standard("ORD-002", sample_order)

    print()
    print("=" * 90)
    print("COMPARISON SUMMARY")
    print("=" * 90)
    print()
    print("🎨 VISUAL MODE BENEFITS:")
    print("✅ Easy to follow function call hierarchy")
    print("✅ Clear visual separation of nesting levels")
    print("✅ Emojis and symbols make logs more readable")
    print("✅ Perfect for debugging and development")
    print("✅ Great for training and documentation")
    print()
    print("📄 STANDARD MODE BENEFITS:")
    print("✅ Compact, efficient log format")
    print("✅ Better performance (less formatting overhead)")
    print("✅ Ideal for production environments")
    print("✅ Compatible with log aggregation tools")
    print("✅ Professional appearance for business logs")
    print()
    print("💡 RECOMMENDATION:")
    print("• Use VISUAL mode during development and debugging")
    print("• Use STANDARD mode in production environments")
    print("• Switch modes easily with configuration changes")
    print("• Consider your audience and use case")
    print("=" * 90)

    return visual_result, standard_result


if __name__ == "__main__":
    run_comparison()
