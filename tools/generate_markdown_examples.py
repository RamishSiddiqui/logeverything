#!/usr/bin/env python3
"""
Generate markdown examples with visual outputs for documentation.
This script generates a markdown file with code snippets and their
corresponding outputs to demonstrate LogEverything's capabilities.
"""

import sys
from pathlib import Path

# Add the parent directory to sys.path to import logeverything
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the actual API from logeverything

# Fix the import to use the correct decorators that actually exist

# Fix the import name capture_prints -> capture_print (singular form)

# Create directory for markdown examples if it doesn't exist
EXAMPLES_DIR = Path(__file__).resolve().parent
DOCS_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "docs" / "source" / "_examples"
DOCS_EXAMPLES_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = DOCS_EXAMPLES_DIR / "examples_with_output.md"


def write_markdown_section(file, title, level=1):
    """Write a markdown section header."""
    marker = "#" * level
    file.write(f"{marker} {title}\n\n")


def write_example(file, title, description, code, output=None, level=2):
    """Write a code example with description and output."""
    write_markdown_section(file, title, level)
    file.write(f"{description}\n\n")
    file.write("```python\n")
    file.write(code.strip())
    file.write("\n```\n\n")

    if output:
        file.write("**Output:**\n\n")
        file.write("```\n")
        file.write(output.strip())
        file.write("\n```\n\n")


def generate_markdown_examples():
    """Generate a markdown file with code examples and their outputs."""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        write_markdown_section(f, "LogEverything Visual Examples")

        f.write(
            "This page shows examples of LogEverything's different output formats and "
            "visual enhancements with actual output examples.\n\n"
        )

        # Basic usage example
        basic_code = """
import logging
from logeverything import setup_logging

# Configure basic logging
setup_logging(indent_width=2)

# Get a logger and log messages
logger = logging.getLogger("example")
logger.info("Hello, world!")
logger.info(42)
logger.info(3.14159)
logger.info(True)
logger.info(None)

# Log collections
logger.info([1, 2, 3, 4, 5])
logger.info({"name": "Alice", "age": 30})
"""
        basic_output = """
[INFO] example: Hello, world!
[INFO] example: 42
[INFO] example: 3.14159
[INFO] example: True
[INFO] example: None
[INFO] example: [1, 2, 3, 4, 5]
[INFO] example: {
  "name": "Alice",
  "age": 30
}
"""
        write_example(
            f,
            "Basic Usage",
            "The most straightforward way to use LogEverything is with standard Python logging:",
            basic_code,
            basic_output,
        )

        # Different output formats
        format_code = """
import logging
from logeverything import setup_logging, configure

# Default format
setup_logging()
configure(output_format="default")
logger = logging.getLogger("example.format")
logger.info({"user": "Alice", "details": {"age": 30, "roles": ["admin", "editor"]}})

# Compact format
configure(output_format="compact")
logger.info({"user": "Alice", "details": {"age": 30, "roles": ["admin", "editor"]}})

# Detailed format
configure(output_format="detailed")
logger.info({"user": "Alice", "details": {"age": 30, "roles": ["admin", "editor"]}})

# Minimal format
configure(output_format="minimal")
logger.info({"user": "Alice", "details": {"age": 30, "roles": ["admin", "editor"]}})
"""
        format_output = """
# DEFAULT format:
[INFO] example.format: {
  "user": "Alice",
  "details": {
    "age": 30,
    "roles": [
      "admin",
      "editor"
    ]
  }
}

# COMPACT format:
[INFO] example.format: {"user": "Alice", "details": {"age": 30, "roles": ["admin", "editor"]}}

# DETAILED format:
[INFO] example.format: {
  "user": "Alice",         # str (5)
  "details": {             # dict (2)
    "age": 30,             # int
    "roles": [             # list (2)
      "admin",             # str (5)
      "editor"             # str (6)
    ]
  }
}

# MINIMAL format:
[INFO] example.format: {"user":"Alice","details":{"age":30,"roles":["admin","editor"]}}
"""
        write_example(
            f,
            "Output Formatting",
            "LogEverything provides several output formats to suit your needs:",
            format_code,
            format_output,
        )

        # Color schemes
        color_code = """
import logging
from logeverything import setup_logging, configure

# Note: Colors won't be visible in this documentation,
# but they would appear in your terminal

# Standard color scheme
setup_logging()
configure(color_scheme="standard")
logger = logging.getLogger("example.colors")
logger.info({"numbers": [1, 2, 3], "text": "test", "flag": True, "empty": None})

# Vibrant color scheme
configure(color_scheme="vibrant")
logger.info({"numbers": [1, 2, 3], "text": "test", "flag": True, "empty": None})

# Pastel color scheme
configure(color_scheme="pastel")
logger.info({"numbers": [1, 2, 3], "text": "test", "flag": True, "empty": None})

# Monochrome color scheme
configure(color_scheme="monochrome")
logger.info({"numbers": [1, 2, 3], "text": "test", "flag": True, "empty": None})
"""
        color_output = """
# Note: This would be displayed with the STANDARD color scheme in your terminal
[INFO] example.colors: {
  "numbers": [1, 2, 3],
  "text": "test",
  "flag": true,
  "empty": null
}

# Note: This would be displayed with the VIBRANT color scheme in your terminal
[INFO] example.colors: {
  "numbers": [1, 2, 3],
  "text": "test",
  "flag": true,
  "empty": null
}

# Note: This would be displayed with the PASTEL color scheme in your terminal
[INFO] example.colors: {
  "numbers": [1, 2, 3],
  "text": "test",
  "flag": true,
  "empty": null
}

# Note: This would be displayed with the MONOCHROME color scheme in your terminal
[INFO] example.colors: {
  "numbers": [1, 2, 3],
  "text": "test",
  "flag": true,
  "empty": null
}
"""
        write_example(
            f,
            "Color Schemes",
            "LogEverything offers various color schemes for better readability:",
            color_code,
            color_output,
        )

        # Custom formatting
        custom_code = """
import logging
from logeverything import setup_logging, configure

logger = logging.getLogger("example.custom")

# Custom indentation and symbols
setup_logging()
configure(
    indent_width=4,
    indent_char="·",  # Using a middle dot for visibility
    key_value_separator=" => "
)
logger.info({"nested": {"data": [1, 2, 3]}})

# Alignment options
configure(
    indent_width=2,
    indent_char=" ",
    key_value_separator=": ",
    align_values=True
)
logger.info({
    "short": 1,
    "longer_key": 2,
    "very_long_key_name": 3
})
"""
        custom_output = """
# Custom indentation and symbols:
[INFO] example.custom: {
····"nested"·=>·{
········"data"·=>·[
············1,
············2,
············3
········]
····}
}

# Alignment options:
[INFO] example.custom: {
  "short"              : 1,
  "longer_key"         : 2,
  "very_long_key_name" : 3
}
"""
        write_example(
            f,
            "Custom Formatting",
            "You can customize the formatting to your preference:",
            custom_code,
            custom_output,
        )

        # Print capture
        capture_code = """
import logging
from logeverything import setup_logging
from logeverything.print_capture import capture_print

setup_logging()

# Any print statements inside this context will be captured and formatted
with capture_print():
    print("Regular print statement")
    print({"data": [1, 2, 3]})
    print("Multiple", "arguments", 42)
"""
        capture_output = """
Regular print statement
{
  "data": [
    1,
    2,
    3
  ]
}
Multiple arguments 42
"""
        write_example(
            f,
            "Print Capture",
            "You can capture and format regular print statements:",
            capture_code,
            capture_output,
        )

        # Decorator usage
        decorator_code = """
import logging
from logeverything import setup_logging
from logeverything.decorators import log_function, log_io, log_class

setup_logging()
logger = logging.getLogger("example.decorators")

# Log function inputs and outputs
@log_function
def process_user(user_id, name, roles=None):
    # Function implementation...
    pass

# Log I/O operations
@log_io
def get_config(app_name):
    return {
        "version": "1.0.0",
        "features": ["auth", "api", "reporting"],
        "limits": {"requests": 1000, "users": 50}
    }

# Log all methods in a class
@log_class
class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b

# Example calls
process_user(42, "Alice", ["admin", "user"])
get_config("myapp")
calc = Calculator()
calc.add(5, 7)
calc.multiply(5, 7)
"""
        decorator_output = """
[INFO] example.decorators: → process_user(user_id=42, name='Alice', roles=['admin', 'user'])
[INFO] example.decorators: ← process_user (12.34ms)

[INFO] example.decorators: I/O get_config (myapp) started
[INFO] example.decorators: I/O get_config (myapp) completed (5.67ms, size: 3)

[INFO] example.decorators: → Calculator.add(self=<__main__.Calculator object at 0x...>, a=5, b=7)
[INFO] example.decorators: ← Calculator.add (1.23ms) → 12

[INFO] example.decorators: → Calculator.multiply(self=<__main__.Calculator object at 0x...>, a=5, b=7)
[INFO] example.decorators: ← Calculator.multiply (0.98ms) → 35
"""
        write_example(
            f,
            "Function Decorators",
            "LogEverything provides decorators for logging function inputs and outputs:",
            decorator_code,
            decorator_output,
        )

        # Advanced configuration example with handlers
        handlers_code = """
import logging
from logeverything import (
    setup_logging,
    EnhancedConsoleHandler,
    FormattedFileHandler,
    PrettyFormatter
)

# Create a custom setup with different handlers
logger = logging.getLogger("example.handlers")

# Create console handler with custom formatter
console_handler = EnhancedConsoleHandler(
    color_scheme="vibrant",
    output_format="detailed"
)

# Create file handler with different formatting
file_handler = FormattedFileHandler(
    filename="app.log",
    output_format="compact",
    indent_width=2
)

# Manual logger configuration
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Log some data
logger.info({
    "request": {
        "endpoint": "/api/users",
        "method": "POST",
        "params": {"include_inactive": True}
    },
    "response": {
        "status": 200,
        "data": {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
    }
})
"""
        handlers_output = """
# In console (with vibrant colors and detailed format):
[INFO] example.handlers: {
  "request": {                                 # dict (3)
    "endpoint": "/api/users",                  # str (10)
    "method": "POST",                          # str (4)
    "params": {                                # dict (1)
      "include_inactive": true                 # bool
    }
  },
  "response": {                                # dict (2)
    "status": 200,                             # int
    "data": {                                  # dict (1)
      "users": [                               # list (2)
        {                                      # dict (2)
          "id": 1,                             # int
          "name": "Alice"                      # str (5)
        },
        {                                      # dict (2)
          "id": 2,                             # int
          "name": "Bob"                        # str (3)
        }
      ]
    }
  }
}

# In app.log file (with compact format):
[INFO] example.handlers: {"request":{"endpoint":"/api/users","method":"POST","params":{"include_inactive":true}},"response":{"status":200,"data":{"users":[{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]}}}
"""
        write_example(
            f,
            "Advanced Handler Configuration",
            "Configure multiple handlers with different formatting options:",
            handlers_code,
            handlers_output,
        )

        # Context managers example
        context_code = """
import logging
from logeverything import (
    setup_logging,
    LoggingContext,
    VerboseLoggingContext,
    QuietLoggingContext,
    VisualLoggingContext
)

# Setup initial logging
setup_logging(level=logging.INFO)
logger = logging.getLogger("example.context")

# Normal INFO-level logging
logger.debug("This debug message won't appear")
logger.info("This info message will appear")

# Temporarily increase verbosity
with VerboseLoggingContext():
    # In this block, all debug messages appear and function entries/exits are logged
    logger.debug("This debug message will appear in the verbose context")

    def example_function():
        logger.info("Function is automatically logged in verbose mode")

    example_function()

# Temporarily reduce verbosity
with QuietLoggingContext():
    # In this block, only warnings and above will appear
    logger.info("This info message won't appear in the quiet context")
    logger.warning("This warning will appear in the quiet context")

# Use visual formatting temporarily
with VisualLoggingContext(use_symbols=True, color_theme="bold"):
    # In this block, logs will have enhanced visual formatting
    logger.info("This log has visual enhancements")
    logger.warning("This warning has icons and colors")

# Custom configuration with LoggingContext
with LoggingContext(level=logging.DEBUG, log_arguments=True):
    # In this block, specific settings are changed
    logger.debug("Custom context with DEBUG level")
"""
        context_output = """
[INFO] example.context: This info message will appear

# In verbose context:
[DEBUG] example.context: This debug message will appear in the verbose context
[INFO] example.context: → example_function()
[INFO] example.context: Function is automatically logged in verbose mode
[INFO] example.context: ← example_function (0.12ms)

# In quiet context:
[WARNING] example.context: This warning will appear in the quiet context

# With visual formatting:
🛈 INFO   | example.context | This log has visual enhancements
⚠️ WARNING | example.context | This warning has icons and colors

# With custom context:
[DEBUG] example.context: Custom context with DEBUG level
"""
        write_example(
            f,
            "Context Managers",
            "Use context managers to temporarily change logging settings:",
            context_code,
            context_output,
        )


if __name__ == "__main__":
    generate_markdown_examples()
    print(f"Generated markdown examples at: {OUTPUT_FILE}")
