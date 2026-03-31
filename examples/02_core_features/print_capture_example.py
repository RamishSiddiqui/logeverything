#!/usr/bin/env python
"""
Example demonstrating how to capture print statements with LogEverything.

This example shows different ways to capture print statements and redirect them
to the logging system, so they appear in the same logs as other log messages.
"""

import logging
import time

from logeverything import (
    Logger,
    capture_print,
    disable_print_capture,
    enable_print_capture,
    log_function,
)


@log_function
def process_data(value):
    """A function that uses print for status messages."""
    print(f"Processing data: {value}")
    # Simulate some processing
    time.sleep(0.1)
    result = value * 2
    print(f"Data processed: {result}")
    return result


def main():
    # Configure logging with modern Logger API
    logger = Logger("print_capture_example")
    logger.configure(
        level="DEBUG", handlers=["console", "file"], file_path="print_capture_example.log"
    )
    logger.info("Example started")

    print("\n1. REGULAR PRINT STATEMENTS (not captured)")
    print("----------------------------------------")
    print("These print statements are not captured in logs")
    process_data(5)

    print("\n2. USING CONTEXT MANAGER")
    print("----------------------------------------")
    print("Now we'll capture prints using the context manager")

    # Use the context manager to capture prints temporarily
    with capture_print(prefix="[USER INFO] "):
        print("This print statement will be captured in logs")
        process_data(10)
        print("Still capturing inside the context manager")

    print("This print statement is outside the context manager (not captured)")

    print("\n3. USING GLOBAL PRINT CAPTURE")
    print("----------------------------------------")
    print("Now we'll enable global print capturing")

    # Enable global print capturing
    enable_print_capture(prefix="[GLOBAL] ")

    print("This print statement will be captured in logs")
    process_data(15)

    # Disable global print capturing
    disable_print_capture()
    print("Print capturing has been disabled")

    print("\n4. USING CONFIGURATION")
    print("----------------------------------------")
    print("Now we'll use the logger.configure() function")

    # Enable print capturing via configuration
    logger.configure(capture_print=True, print_prefix="[CONFIG] ", print_level=logging.INFO)

    print("This print statement is captured via configuration")
    process_data(20)

    # Disable again
    logger.configure(capture_print=False)
    print("Print capturing disabled via configuration")

    logger.info("Example completed")
    print("\nCheck the print_capture_example.log file to see the captured print statements")


if __name__ == "__main__":
    main()
