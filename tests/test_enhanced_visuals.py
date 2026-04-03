#!/usr/bin/env python
"""
Tests for enhanced visual formatting features of LogEverything.

This module tests the new visual formatting enhancements including
PrettyFormatter, FormattedFileHandler, and EnhancedConsoleHandler.
"""

# Removed logging import
import os
from datetime import datetime
from io import StringIO

import pytest

from logeverything import core as core_module
from logeverything import get_logger
from logeverything.decorators import log_class, log_function
from logeverything.handlers import (
    EnhancedConsoleHandler,
    FileHandler,
    FormattedFileHandler,
    JSONHandler,
    PrettyFormatter,
)

# Create a test directory for storing our log files
TEST_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "test_output")

# Ensure it exists
os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)


class TestEnhancedVisuals:
    """Test enhanced visual log formatting."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down the test environment."""
        # Reset logging before each test
        core_module.configure(
            level="DEBUG",
            log_entry_exit=True,
            log_arguments=True,
            log_return_values=True,
            beautify=True,
            indent_level=2,
            handlers=["console"],
        )

        yield

        # Cleanup any handlers
        logger = get_logger("logeverything")
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

    def test_pretty_formatter(self):
        """Test the PrettyFormatter with various configuration options."""
        # Create output file paths for different formatting styles
        pretty_path = os.path.join(TEST_OUTPUT_DIR, "pretty_format.log")
        symbols_path = os.path.join(TEST_OUTPUT_DIR, "pretty_symbols.log")
        indent_path = os.path.join(TEST_OUTPUT_DIR, "pretty_indent.log")
        align_path = os.path.join(TEST_OUTPUT_DIR, "pretty_aligned.log")
        complete_path = os.path.join(TEST_OUTPUT_DIR, "pretty_complete.log")

        # Create handlers with different formatter options
        handlers = [
            # Basic pretty formatting
            (
                pretty_path,
                PrettyFormatter(
                    use_colors=False, use_symbols=False, use_indent=False, align_columns=False
                ),
            ),
            # With symbols
            (
                symbols_path,
                PrettyFormatter(
                    use_colors=False, use_symbols=True, use_indent=False, align_columns=False
                ),
            ),
            # With indentation
            (
                indent_path,
                PrettyFormatter(
                    use_colors=False, use_symbols=False, use_indent=True, align_columns=False
                ),
            ),
            # With alignment
            (
                align_path,
                PrettyFormatter(
                    use_colors=False,
                    use_symbols=False,
                    use_indent=False,
                    align_columns=True,
                    column_widths={"timestamp": 25, "level": 12, "name": 30},
                ),
            ),
            # Complete formatting
            (
                complete_path,
                PrettyFormatter(
                    use_colors=False, use_symbols=True, use_indent=True, align_columns=True
                ),
            ),
        ]

        for path, formatter in handlers:
            # Create a file handler with this formatter and explicitly use UTF-8 encoding
            file_handler = FileHandler(path, mode="w", encoding="utf-8")
            file_handler.setFormatter(formatter)

            # Configure logger
            logger = get_logger("logeverything.pretty")
            logger.handlers = []
            logger.addHandler(file_handler)
            logger.setLevel("DEBUG")

            # Generate test log entries
            self._generate_test_logs(logger)

            # Ensure the handler is fully flushed and closed
            file_handler.flush()
            file_handler.close()
            logger.removeHandler(file_handler)

        print(f"\nGenerated pretty formatting comparison files in {TEST_OUTPUT_DIR}:")
        for path, _ in handlers:
            print(f"  - {os.path.basename(path)}")

    def test_formatted_file_handler(self):
        """Test the FormattedFileHandler."""
        # Create output files
        basic_path = os.path.join(TEST_OUTPUT_DIR, "formatted_basic.log")
        no_symbols_path = os.path.join(TEST_OUTPUT_DIR, "formatted_no_symbols.log")
        no_indent_path = os.path.join(TEST_OUTPUT_DIR, "formatted_no_indent.log")
        plain_path = os.path.join(TEST_OUTPUT_DIR, "formatted_plain.log")

        # Create handlers with different options
        handlers = [
            # Default options (all enabled)
            FormattedFileHandler(
                filename=basic_path,
                mode="w",
                pretty=True,
                use_symbols=True,
                use_indent=True,
                align_columns=True,
            ),
            # No symbols
            FormattedFileHandler(
                filename=no_symbols_path,
                mode="w",
                pretty=True,
                use_symbols=False,
                use_indent=True,
                align_columns=True,
            ),
            # No indentation
            FormattedFileHandler(
                filename=no_indent_path,
                mode="w",
                pretty=True,
                use_symbols=True,
                use_indent=False,
                align_columns=True,
            ),
            # Plain (no pretty formatting)
            FormattedFileHandler(filename=plain_path, mode="w", pretty=False),
        ]

        # Configure logging and generate logs
        for handler in handlers:
            # Verify UTF-8 encoding for file handlers
            if hasattr(handler, "encoding"):
                assert handler.encoding == "utf-8", (
                    f"Handler {handler.__class__.__name__} should use UTF-8 encoding"
                )

            logger = get_logger("logeverything.formatted")
            logger.handlers = []
            logger.addHandler(handler)
            logger.setLevel("DEBUG")

            # Generate test log entries
            self._generate_test_logs(logger)

            # Close handler
            handler.close()
            logger.removeHandler(handler)

        print(f"\nGenerated formatted file handler output in {TEST_OUTPUT_DIR}:")
        print("  - formatted_basic.log")
        print("  - formatted_no_symbols.log")
        print("  - formatted_no_indent.log")
        print("  - formatted_plain.log")

    def test_enhanced_console_handler(self):
        """Test the EnhancedConsoleHandler with different color themes."""
        ansi_path = os.path.join(TEST_OUTPUT_DIR, "enhanced_console_themes.log")

        # Define the color themes to test
        themes = ["default", "pastel", "bold", "monochrome"]

        # Create a file to capture all theme outputs
        with open(ansi_path, "w", encoding="utf-8") as outfile:
            for theme in themes:
                outfile.write(f"\n\n{'=' * 20} {theme.upper()} THEME {'=' * 20}\n\n")

                # Create a StringIO to capture output
                output = StringIO()

                # Create handler with this theme
                handler = EnhancedConsoleHandler(
                    stream=output,
                    use_colors=True,
                    use_symbols=False,  # Disable symbols for Windows compatibility
                    use_indent=True,
                    align_columns=True,
                    color_theme=theme,
                )

                # Configure logger
                logger = get_logger(f"logeverything.enhanced.{theme}")
                logger.handlers = []
                logger.addHandler(handler)
                logger.setLevel("DEBUG")

                # Generate test logs
                self._generate_test_logs(logger)

                try:
                    # Write the captured output to the file
                    outfile.write(output.getvalue())
                except UnicodeEncodeError:
                    # Handle potential encoding issues by replacing problematic characters
                    outfile.write(
                        "Note: Some characters couldn't be displayed due to encoding issues.\n"
                    )
                    outfile.write(output.getvalue().encode("ascii", "replace").decode("ascii"))

                # Clean up
                output.close()
                handler.close()
                logger.removeHandler(handler)

        print(f"\nGenerated enhanced console handler themes in {TEST_OUTPUT_DIR}:")
        print("  - enhanced_console_themes.log")

    def test_real_world_scenario_with_enhanced_formatting(self):
        """Test a real-world scenario with enhanced formatting."""
        log_path = os.path.join(TEST_OUTPUT_DIR, "enhanced_real_world.log")
        json_path = os.path.join(TEST_OUTPUT_DIR, "enhanced_real_world.json")

        # Create handlers
        formatted_handler = FormattedFileHandler(
            filename=log_path,
            mode="w",
            pretty=True,
            use_symbols=True,
            use_indent=True,
            align_columns=True,
        )

        json_handler = JSONHandler(filename=json_path, mode="w", flatten=True)

        # Configure logger
        logger = get_logger("logeverything.realworld")
        logger.handlers = []
        logger.addHandler(formatted_handler)
        logger.addHandler(json_handler)
        logger.setLevel("DEBUG")

        # Generate real-world scenario logs with hierarchical structure
        logger.info("Starting application with enhanced formatting")

        # Use decorated functions to show the indentation
        @log_function
        def authenticate_user(username, password):
            """Simulate user authentication."""
            logger.info(f"Authenticating user: {username}")
            logger.debug("Validating credentials")

            if username == "admin" and password == "secret":
                logger.info(f"User {username} authenticated successfully")
                return {"success": True, "user_id": 12345}
            else:
                logger.warning(f"Failed authentication attempt for {username}")
                return {"success": False, "reason": "Invalid credentials"}

        @log_function
        def process_order(order_id, items, user_id=None):
            """Process an order with multiple items."""
            logger.info(f"Processing order {order_id} with {len(items)} items")

            total = 0
            for i, item in enumerate(items):
                logger.debug(f"Processing item {i + 1}: {item['name']}")
                if item.get("in_stock", True):
                    total += item["price"]
                else:
                    logger.warning(f"Item {item['name']} is out of stock")

            logger.info(f"Order {order_id} processed, total: ${total:.2f}")
            return {"order_id": order_id, "total": total}

        @log_class
        class PaymentProcessor:
            """Process payments for orders."""

            def __init__(self, provider):
                self.provider = provider
                logger.info(f"Payment processor initialized with provider: {provider}")

            def process_payment(self, order_id, amount, card_info):
                """Process a payment."""
                logger.info(f"Processing payment for order {order_id}")

                # Simulate payment processing steps
                logger.debug("Validating payment information")

                # Simulate an API call
                logger.debug(f"Calling {self.provider} API")

                # Simulate successful payment
                if card_info.get("valid", True):
                    logger.info(f"Payment of ${amount:.2f} for order {order_id} successful")
                    return {
                        "success": True,
                        "transaction_id": f"tx-{order_id}-{int(datetime.now().timestamp())}",
                    }
                else:
                    logger.error(f"Payment for order {order_id} failed: Invalid card")
                    return {"success": False, "reason": "Invalid card information"}

            def refund_payment(self, transaction_id, amount):
                """Process a refund."""
                logger.info(f"Processing refund for transaction {transaction_id}")
                logger.debug(f"Calling {self.provider} refund API")
                logger.info(f"Refund of ${amount:.2f} processed successfully")
                return {"success": True, "refund_id": f"refund-{transaction_id}"}

        # Simulate application flow
        logger.info("Processing incoming request")

        try:
            # User login
            auth_result = authenticate_user("admin", "secret")

            if auth_result["success"]:
                # Process an order
                order_items = [
                    {"name": "Widget A", "price": 19.99},
                    {"name": "Gadget B", "price": 29.99, "in_stock": False},
                    {"name": "Tool C", "price": 14.50},
                ]

                order_result = process_order("ORD-12345", order_items, auth_result["user_id"])

                # Process payment
                payment_processor = PaymentProcessor("Stripe")
                payment_result = payment_processor.process_payment(
                    order_result["order_id"],
                    order_result["total"],
                    {"card_number": "XXXX-XXXX-XXXX-1234", "valid": True},
                )

                # Simulate an error condition
                try:
                    logger.info("Checking shipping availability")
                    if order_result["total"] < 50.0:
                        raise ValueError("Order total below shipping minimum")

                except Exception:
                    logger.exception("Shipping check failed")

                    # Process refund due to shipping issue
                    if payment_result["success"]:
                        refund_result = payment_processor.refund_payment(
                            payment_result["transaction_id"], order_result["total"]
                        )
        except Exception:
            logger.exception("Unexpected error in request processing")

        logger.info("Request processing completed")

        # Close handlers
        formatted_handler.close()
        json_handler.close()
        logger.removeHandler(formatted_handler)
        logger.removeHandler(json_handler)

        print(f"\nGenerated enhanced real-world scenario logs in {TEST_OUTPUT_DIR}:")
        print("  - enhanced_real_world.log")
        print("  - enhanced_real_world.json")

    def _generate_test_logs(self, logger):
        """Generate a standard set of test log entries."""
        # Basic log entries at different levels
        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        logger.critical("This is a critical message")

        # Simulated function entry/exit logs
        logger.info("â†’ my_function(arg1='value1', arg2=42)")
        logger.debug("  Processing data")
        logger.info("  Intermediate step completed")
        logger.info("â† my_function (12.34ms) â†’ {'result': 'success'}")

        # Nested function calls
        logger.info("â†’ outer_function()")
        logger.debug("  Outer function processing")
        logger.info("  â†’ inner_function()")
        logger.debug("    Inner function processing")
        logger.info("    â†’ deepest_function()")
        logger.debug("      Deepest level processing")
        logger.warning("      Potential issue detected")
        logger.info("    â† deepest_function (5.67ms)")
        logger.info("  â† inner_function (8.91ms)")
        logger.info("â† outer_function (23.45ms)")

        # Error with traceback
        try:
            1 / 0
        except Exception:
            logger.exception("An exception occurred")


if __name__ == "__main__":
    # If run directly, execute all tests
    test = TestEnhancedVisuals()
    test.setup_and_teardown()
    test.test_pretty_formatter()
    test.test_formatted_file_handler()
    test.test_enhanced_console_handler()
    test.test_real_world_scenario_with_enhanced_formatting()
    print("\nAll enhanced visual tests completed!")
