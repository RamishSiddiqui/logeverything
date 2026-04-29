#!/usr/bin/env python
"""
Tests for evaluating the visual appearance and readability of log output.

This module generates log files in various formats (plain text, colored console output,
JSON) with different logging scenarios to help evaluate and improve the visual appeal
and readability of logs.
"""

# Removed logging import
import os
from datetime import datetime

import pytest

from logeverything import Logger, get_logger
from logeverything import core as core_module
from logeverything.capture.print_capture import capture_print
from logeverything.decorators import log_class, log_function
from logeverything.handlers import ConsoleHandler, FileHandler, JSONHandler, PrettyFormatter

# Create a test directory for storing our log files
TEST_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "test_output")

# Ensure it exists
os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)


class TestVisualOutput:
    """Test the visual appearance and readability of logs."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down the test environment."""
        # Reset logging before each test
        core_module.configure(
            level="INFO",
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

    def test_generate_comparison_logs(self):
        """
        Generate log files for all handlers with identical content for comparison.

        This test creates identical log content in different formats to allow for
        side-by-side comparison of readability.
        """
        scenario_name = "comparison"

        # Define file paths for different outputs
        txt_path = os.path.join(TEST_OUTPUT_DIR, f"{scenario_name}.log")
        json_path = os.path.join(TEST_OUTPUT_DIR, f"{scenario_name}.json")
        colored_path = os.path.join(TEST_OUTPUT_DIR, f"{scenario_name}_colored.log")

        # Create handlers
        txt_handler = FileHandler(txt_path, mode="w")
        txt_handler.setFormatter(
            PrettyFormatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        json_handler = JSONHandler(json_path, mode="w", flatten=True)

        colored_handler = FileHandler(colored_path, mode="w")
        colored_formatter = PrettyFormatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )
        colored_handler.setFormatter(colored_formatter)

        # Configure logging with all handlers
        logger = get_logger("logeverything")
        logger.handlers = []
        logger.addHandler(txt_handler)
        logger.addHandler(json_handler)
        logger.addHandler(colored_handler)

        # Generate consistent log content across all formats
        logger.info("Starting application")
        logger.debug("Configuration loaded successfully")
        logger.info("Processing input data")
        logger.warning("Resource usage above 70%")
        logger.error("Failed to connect to database: Connection refused")

        try:
            1 / 0
        except Exception:
            logger.exception("An unexpected error occurred")

        logger.info("Application shutdown complete")

        # Close handlers
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

        # Paths for verification
        assert os.path.exists(txt_path)
        assert os.path.exists(json_path)
        assert os.path.exists(colored_path)

        print(f"\nGenerated log files for comparison in {TEST_OUTPUT_DIR}:")
        print(f"  - {os.path.basename(txt_path)}")
        print(f"  - {os.path.basename(json_path)}")
        print(f"  - {os.path.basename(colored_path)}")

    def test_complex_hierarchical_logs(self):
        """
        Generate logs that show nested function calls and hierarchical structures.

        This test demonstrates how the library handles complex nested function calls
        and how readable the resulting logs are.
        """
        log_path = os.path.join(TEST_OUTPUT_DIR, "hierarchical.log")
        os.path.join(TEST_OUTPUT_DIR, "hierarchical.json")

        # Setup logging
        logger = Logger()
        logger.configure(
            level="DEBUG",
            handlers=["file", "json"],
            file_path=log_path,
            log_directory=None,  # Use absolute path
            beautify=True,
            indent_level=2,
            log_entry_exit=True,
            log_arguments=True,
            log_return_values=True,
        )

        # Define some decorated functions for our test
        @log_function
        def factorial(n):
            """Calculate factorial recursively."""
            if n <= 1:
                return 1
            return n * factorial(n - 1)

        @log_function
        def fibonacci(n):
            """Calculate Fibonacci number recursively."""
            if n <= 1:
                return n
            return fibonacci(n - 1) + fibonacci(n - 2)

        @log_function
        def process_data(data, operation="sum"):
            """Process data with the given operation."""
            if operation == "sum":
                return sum(data)
            elif operation == "product":
                result = 1
                for item in data:
                    result *= item
                return result
            elif operation == "factorial_sum":
                return sum(factorial(x) for x in data)
            else:
                raise ValueError(f"Unknown operation: {operation}")

        @log_function
        def complex_calculation(a, b, c):
            """Perform a complex calculation with multiple steps."""
            logger = get_logger("logeverything.test")
            logger.info("Starting complex calculation")

            # Step 1
            logger.debug(f"Processing first operation with {a}")
            result1 = process_data(a, "sum")

            # Step 2
            logger.debug(f"Processing second operation with {b}")
            result2 = process_data(b, "product")

            # Step 3
            logger.debug(f"Processing third operation with {c}")
            fib_value = fibonacci(c)

            # Combine results
            final_result = result1 * result2 + fib_value
            logger.info(f"Calculation complete, final value: {final_result}")

            return final_result

        # Execute the functions to generate logs
        try:
            complex_calculation([1, 2, 3, 4], [5, 6, 7], 6)

            # Add a failing case to see error handling
            complex_calculation([1, 2], [3, 4], -1)  # Should fail

        except Exception:
            get_logger("logeverything").exception("Error in test")

        # Close handlers
        logger = get_logger("logeverything")
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

        print(f"\nGenerated hierarchical log files in {TEST_OUTPUT_DIR}:")
        print("  - hierarchical.log")
        print("  - hierarchical.json")

    def test_different_formatting_options(self):
        """
        Test different formatting options for console and file output.

        This test creates multiple log files with different formatting options
        to compare their readability.
        """
        base_path = TEST_OUTPUT_DIR

        # Define different format strings
        formats = {
            "default": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            "compact": "%(asctime)s [%(levelname).1s] %(message)s",
            "detailed": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s",
            "minimal": "%(levelname).1s: %(message)s",
            "aligned": "%(asctime)22s | %(levelname)-8s | %(name)-20s | %(message)s",
        }

        for name, format_str in formats.items():
            log_path = os.path.join(base_path, f"format_{name}.log")

            # Create a file handler with this format
            handler = FileHandler(log_path, mode="w")
            formatter = PrettyFormatter(format_str)
            handler.setFormatter(formatter)

            # Configure logger
            logger = get_logger(f"logeverything.format.{name}")
            logger.handlers = []
            logger.addHandler(handler)
            logger.setLevel("DEBUG")

            # Generate identical log content
            logger.debug("This is a debug message")
            logger.info("User 'admin' logged in successfully")
            logger.warning("Database connection pool reaching capacity (80%)")
            logger.error("Failed to process request: Invalid parameters")

            # Close handler
            handler.close()
            logger.removeHandler(handler)

        print(f"\nGenerated formatting comparison logs in {TEST_OUTPUT_DIR}:")
        for name in formats:
            print(f"  - format_{name}.log")

    @log_class
    class ComplexSystem:
        """A complex system that generates interesting logs."""

        def __init__(self, name):
            self.name = name
            self.logger = get_logger(f"logeverything.system.{name}")
            self.counter = 0
            self.logger.info(f"System '{name}' initialized")

        def process_request(self, request_id, data):
            """Process a request with the given data."""
            self.logger.info(f"Processing request {request_id}")
            self.counter += 1

            if self.counter % 3 == 0:
                self.logger.warning(f"System load high during request {request_id}")

            result = self._internal_process(data)
            self.logger.debug(f"Request {request_id} processed with result: {result}")
            return result

        def _internal_process(self, data):
            """Internal processing method."""
            if isinstance(data, dict):
                return self._process_dict(data)
            elif isinstance(data, list):
                return self._process_list(data)
            else:
                return str(data).upper()

        def _process_dict(self, data):
            """Process dictionary data."""
            self.logger.debug("Processing dictionary data")
            return {k.upper(): v.upper() if isinstance(v, str) else v for k, v in data.items()}

        def _process_list(self, data):
            """Process list data."""
            self.logger.debug("Processing list data")
            return [item.upper() if isinstance(item, str) else item for item in data]

        def cleanup(self):
            """Clean up system resources."""
            self.logger.info(f"Cleaning up system '{self.name}'")
            self.counter = 0
            return True

    def test_real_world_application_logs(self):
        """
        Generate logs that simulate a real-world application with multiple components.

        This test creates a more complex log scenario simulating a real application
        with multiple components and log levels.
        """
        log_path = os.path.join(TEST_OUTPUT_DIR, "real_world.log")
        json_path = os.path.join(TEST_OUTPUT_DIR, "real_world.json")

        # Setup logging with both file and JSON handlers
        handlers = []

        file_handler = FileHandler(log_path, mode="w")
        file_handler.setFormatter(
            PrettyFormatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        handlers.append(file_handler)

        json_handler = JSONHandler(json_path, mode="w", flatten=True)
        handlers.append(json_handler)

        # Configure logging with custom handlers
        logger = Logger()
        logger.configure(
            level="DEBUG",
            handlers=handlers,
            log_entry_exit=True,
            log_arguments=True,
            log_return_values=True,
            beautify=True,
            indent_level=2,
        )

        # Create instances of our complex system
        auth_system = self.ComplexSystem("auth")
        data_system = self.ComplexSystem("data")

        # Simulate application startup
        main_logger = get_logger("logeverything.main")
        main_logger.info("Application starting")

        # Simulate user authentication
        main_logger.info("User authentication request received")
        with capture_print():
            print("Processing authentication request")
            auth_result = auth_system.process_request(
                "auth-123", {"username": "admin", "password": "****"}
            )
            print(f"Authentication result: {auth_result}")

        # Simulate data processing
        main_logger.info("Data processing request received")
        data_system.process_request("data-456", ["item1", "item2", "item3"])

        # Simulate an error condition
        try:
            main_logger.info("Attempting to access protected resource")
            if auth_result.get("USERNAME") != "ADMIN":
                raise PermissionError("Access denied")

            # Process more data
            data_system.process_request("data-789", {"key1": "value1", "key2": "value2"})

        except Exception:
            main_logger.exception("Error processing request")

        # Simulate application shutdown
        auth_system.cleanup()
        data_system.cleanup()
        main_logger.info("Application shutdown complete")

        # Close handlers
        logger = get_logger("logeverything")
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

        print(f"\nGenerated real-world application logs in {TEST_OUTPUT_DIR}:")
        print("  - real_world.log")
        print("  - real_world.json")

    def test_colorful_log_themes(self):
        """
        Test different color schemes for console output.

        This test creates logs using different color schemes to evaluate their
        readability and visual appeal.
        """
        from io import StringIO

        log_path = os.path.join(TEST_OUTPUT_DIR, "color_themes.log")

        # Define different color themes
        themes = {
            "default": {
                "DEBUG": "\033[94m",  # Blue
                "INFO": "\033[92m",  # Green
                "WARNING": "\033[93m",  # Yellow
                "ERROR": "\033[91m",  # Red
                "CRITICAL": "\033[95m",  # Magenta
                "RESET": "\033[0m",  # Reset
            },
            "pastel": {
                "DEBUG": "\033[38;5;111m",  # Light blue
                "INFO": "\033[38;5;121m",  # Light green
                "WARNING": "\033[38;5;221m",  # Light yellow
                "ERROR": "\033[38;5;217m",  # Light red
                "CRITICAL": "\033[38;5;219m",  # Light magenta
                "RESET": "\033[0m",
            },
            "bold": {
                "DEBUG": "\033[1;34m",  # Bold blue
                "INFO": "\033[1;32m",  # Bold green
                "WARNING": "\033[1;33m",  # Bold yellow
                "ERROR": "\033[1;31m",  # Bold red
                "CRITICAL": "\033[1;35m",  # Bold magenta
                "RESET": "\033[0m",
            },
            "monochrome": {
                "DEBUG": "\033[37m",  # White
                "INFO": "\033[1m",  # Bold
                "WARNING": "\033[1;37m",  # Bold white
                "ERROR": "\033[7m",  # Reverse
                "CRITICAL": "\033[1;7m",  # Bold reverse
                "RESET": "\033[0m",
            },
        }

        # Create a file to capture all the colored output
        with open(log_path, "w") as outfile:
            # For each theme, create a handler and generate logs
            for theme_name, theme in themes.items():
                outfile.write(f"\n\n{'=' * 20} {theme_name.upper()} THEME {'=' * 20}\n\n")

                # Create a StringIO to capture output
                output = StringIO()

                # Create a ConsoleHandler with custom colors
                handler = ConsoleHandler(stream=output, use_colors=True)

                # Override the handler's colors
                handler.COLORS = theme

                # Configure logger
                logger = get_logger(f"logeverything.theme.{theme_name}")
                logger.handlers = []
                logger.addHandler(handler)
                logger.setLevel("DEBUG")

                # Generate identical log content
                logger.debug("This is a debug message")
                logger.info("This is an info message")
                logger.warning("This is a warning message")
                logger.error("This is an error message")
                logger.critical("This is a critical message")

                # Write the captured output to our file
                outfile.write(output.getvalue())

                # Clean up
                output.close()
                handler.close()
                logger.removeHandler(handler)

        print(f"\nGenerated color theme comparison in {TEST_OUTPUT_DIR}:")
        print("  - color_themes.log (contains ANSI color codes)")

    def test_generate_sample_report(self):
        """
        Generate a sample log-based report to demonstrate the library's capabilities.

        This test creates a sample report-style log that would be useful in a
        production environment for regular status reporting.
        """
        report_path = os.path.join(TEST_OUTPUT_DIR, "system_report.log")

        # Setup logging
        handler = FileHandler(report_path, mode="w")
        handler.setFormatter(
            PrettyFormatter(
                "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
        )

        # Configure logger
        logger = get_logger("logeverything.report")
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel("INFO")

        # Generate a sample report
        logger.info("=" * 50)
        logger.info("SYSTEM STATUS REPORT - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("=" * 50)

        # System metrics
        logger.info("\nSYSTEM METRICS:")
        logger.info("-" * 30)
        logger.info("CPU Usage: 35%")
        logger.info("Memory Usage: 2.7 GB / 8.0 GB (34%)")
        logger.info("Disk Usage: 128 GB / 512 GB (25%)")
        logger.info("Network: 1.2 MB/s in, 0.4 MB/s out")

        # Application status
        logger.info("\nAPPLICATION STATUS:")
        logger.info("-" * 30)
        logger.info("Web Server: Running (PID 1234)")
        logger.info("Database: Connected (3 active connections)")
        logger.info("Cache: Online (12% hit rate)")
        logger.info("Background Tasks: 2 running, 0 waiting, 1 failed")

        # Recent errors
        logger.info("\nRECENT ERRORS:")
        logger.info("-" * 30)
        logger.error("Failed to connect to backup service (10:15:23)")
        logger.warning("High latency detected on database queries (10:23:45)")
        logger.error("Authentication failure for user 'system' (10:45:12)")

        # Actions needed
        logger.info("\nRECOMMENDED ACTIONS:")
        logger.info("-" * 30)
        logger.warning("Investigate backup service connection issues")
        logger.info("Schedule database maintenance window")
        logger.warning("Review failed background task logs")

        # End of report
        logger.info("\n" + "=" * 50)
        logger.info("END OF REPORT")
        logger.info("=" * 50)

        # Clean up
        handler.close()
        logger.removeHandler(handler)

        print(f"\nGenerated sample system report in {TEST_OUTPUT_DIR}:")
        print("  - system_report.log")


if __name__ == "__main__":
    # If run directly, execute all tests
    test = TestVisualOutput()
    test.setup_and_teardown()
    test.test_generate_comparison_logs()
    test.test_complex_hierarchical_logs()
    test.test_different_formatting_options()
    test.test_real_world_application_logs()
    test.test_colorful_log_themes()
    test.test_generate_sample_report()
    print("\nAll test logs generated successfully!")
