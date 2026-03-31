#!/usr/bin/env python3
"""
Simple Visual Alignment Example

This is a beginner-friendly example showing how LogEverything's decorators
create beautifully aligned and indented logs that make it easy to follow
your program's execution flow.

Perfect for newcomers who want to see the visual benefits immediately!
"""

import os
import sys

# Add the package to Python path for examples
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from logeverything import Logger, log

# Create a simple logger with visual formatting
logger = Logger("simple_demo")


@log(logger=logger, use_symbols=True)
def greet_user(name):
    """A simple function that greets a user."""
    logger.info(f"Preparing greeting for {name}")

    @log(logger=logger, use_symbols=True)
    def create_message(user_name):
        """Create a personalized greeting message."""
        logger.info("Generating personalized message")
        message = f"Hello, {user_name}! Welcome to LogEverything!"
        logger.info(f"Message created: {message}")
        return message

    greeting = create_message(name)
    logger.info("Greeting is ready to be displayed")
    return greeting


@log(logger=logger, use_symbols=True)
def simple_math(x, y):
    """A simple math function to show basic alignment."""
    logger.info(f"Calculating {x} + {y}")
    result = x + y
    logger.info(f"Result: {result}")
    return result


if __name__ == "__main__":
    print("🚀 Welcome to LogEverything Simple Visual Alignment Example!")
    print()
    print("Notice how the logs are beautifully formatted:")
    print("• Function calls (🔵) and completions (✅) are aligned")
    print("• What happens inside functions is indented deeper")
    print("• You can easily see the flow of your program!")
    print()
    print("Let's see it in action:")
    print("-" * 50)
    print()

    # Simple examples
    greeting = greet_user("Alice")
    print()

    result = simple_math(5, 3)
    print()

    print("-" * 50)
    print("✨ Pretty cool, right? This makes debugging so much easier!")
    print("🎯 You can instantly see what your program is doing at each step.")
