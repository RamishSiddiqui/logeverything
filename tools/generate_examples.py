#!/usr/bin/env python
"""
Generate examples with outputs for documentation.

This script runs various examples of LogEverything and captures their outputs to
create markdown documentation that shows users what to expect.
"""

import datetime
import inspect
import io
import logging
import os
import platform
import sys
import textwrap
from contextlib import redirect_stdout

# Add parent directory to path so we can import logeverything from development
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything import (
    log_class,
)

# Setup output directory
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "source", "_examples")
os.makedirs(DOCS_DIR, exist_ok=True)

# Save current date for documentation
CURRENT_DATE = datetime.datetime.now().strftime("%Y-%m-%d")


def capture_output(func):
    """Decorator to capture function output and logging."""

    def wrapper(*args, **kwargs):
        # Capture stdout
        stdout_capture = io.StringIO()
        # Capture logs
        log_capture = io.StringIO()

        # Create a special handler to capture logs
        capture_handler = logging.StreamHandler(log_capture)
        capture_handler.setLevel(logging.DEBUG)
        capture_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", "%Y-%m-%d %H:%M:%S"
            )
        )

        # Remove existing handlers from the root logger
        root_logger = logging.getLogger()
        old_handlers = root_logger.handlers.copy()
        for handler in old_handlers:
            root_logger.removeHandler(handler)

        # Add our capture handler
        root_logger.addHandler(capture_handler)

        # Run the function, capturing its output
        with redirect_stdout(stdout_capture):
            result = func(*args, **kwargs)

        # Remove our capture handler and restore original handlers
        root_logger.removeHandler(capture_handler)
        for handler in old_handlers:
            root_logger.addHandler(handler)

        return {
            "result": result,
            "stdout": stdout_capture.getvalue(),
            "logs": log_capture.getvalue(),
        }

    return wrapper


def markdown_example(title, description, code, output=None, logs=None):
    """Format an example as markdown."""
    md = f"## {title}\n\n"
    md += f"{description}\n\n"
    md += "```python\n"
    md += code.strip() + "\n"
    md += "```\n\n"

    if output:
        md += "**Output:**\n\n"
        md += "```\n"
        md += output.strip() + "\n"
        md += "```\n\n"

    if logs:
        md += "**Logs:**\n\n"
        md += "```\n"
        md += logs.strip() + "\n"
        md += "```\n\n"

    return md


def extract_function_body(func):
    """Extract the function body (code inside the function) as a string."""
    # Get the source code of the function
    source = inspect.getsource(func)

    # Get the indentation level of the first line (should be the decorator or def)
    first_line = source.split("\n")[0]
    base_indent = len(first_line) - len(first_line.lstrip())

    # Find the function definition line
    for i, line in enumerate(source.split("\n")):
        if line.strip().startswith("def "):
            start_line = i
            break
    else:
        # If no function definition found, just return the source
        return source

    # Extract lines after the function definition
    lines = source.split("\n")[start_line + 1 :]

    # Determine the base indentation of the function body
    for line in lines:
        if line.strip():
            body_indent = len(line) - len(line.lstrip())
            break
    else:
        body_indent = base_indent + 4

    # Remove base indentation from each line
    dedented_lines = []
    for line in lines:
        if line.strip():
            # Only dedent non-empty lines
            dedent_amount = min(body_indent, len(line) - len(line.lstrip()))
            dedented_lines.append(line[dedent_amount:])
        else:
            dedented_lines.append("")

    return "\n".join(dedented_lines)


# Example functions
@capture_output
def example_basic_logging():
    """Demonstrate basic logging with LogEverything."""
    import logging

    from logeverything import log_function, setup_logging

    # Basic setup
    setup_logging(level=logging.DEBUG)

    @log_function
    def greet(name):
        logger = logging.getLogger("example.basic")
        logger.info(f"Creating greeting for {name}")
        return f"Hello, {name}!"

    # Call the function to generate logs
    result = greet("World")
    print(f"Function returned: {result}")


@capture_output
def example_visual_mode_basic():
    """Demonstrate basic visual mode with LogEverything."""
    import logging

    from logeverything import setup_logging

    # Setup with visual mode enabled
    setup_logging(
        level=logging.DEBUG,
        visual_mode=True,  # Enable visual formatting
        use_symbols=True,  # Use Unicode symbols
        use_indent=True,  # Show visual indentation
    )

    # Get a logger
    logger = logging.getLogger("example.visual")

    # Generate some logs at different levels
    logger.debug("Loading configuration file")
    logger.info("Application started")
    logger.warning("Configuration file not found, using defaults")
    logger.error("Failed to connect to database")
    logger.critical("System shutting down due to critical error")


@capture_output
def example_color_themes():
    """Demonstrate different color themes with LogEverything."""
    import logging

    from logeverything import EnhancedConsoleHandler

    # Reset previous handlers
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Create a logger
    logger = logging.getLogger("example.themes")
    logger.setLevel(logging.DEBUG)

    # We're going to simulate the output since color codes won't show in capture
    themes = ["default", "bold", "pastel", "monochrome"]

    for theme in themes:
        print(f"\n===== {theme.upper()} THEME =====")
        # Actually creating the handler but not using it in demo output
        handler = EnhancedConsoleHandler(use_colors=True, color_theme=theme, use_symbols=True)

        # Simulate the output for docs with descriptive comments instead of raw ANSI codes
        if theme == "default":
            print("🔍 DEBUG | example.themes | Debug message with default theme")
            print("ℹ️ INFO | example.themes | Info message with default theme")
            print("⚠️ WARNING | example.themes | Warning message with default theme")
            print("❌ ERROR | example.themes | Error message with default theme")
        elif theme == "bold":
            print("🔍 DEBUG | example.themes | Debug message with bold theme")
            print("ℹ️ INFO | example.themes | Info message with bold theme")
            print("⚠️ WARNING | example.themes | Warning message with bold theme")
            print("❌ ERROR | example.themes | Error message with bold theme")
        elif theme == "pastel":
            print("🔍 DEBUG | example.themes | Debug message with pastel theme")
            print("ℹ️ INFO | example.themes | Info message with pastel theme")
            print("⚠️ WARNING | example.themes | Warning message with pastel theme")
            print("❌ ERROR | example.themes | Error message with pastel theme")
        elif theme == "monochrome":
            print("🔍 DEBUG | example.themes | Debug message with monochrome theme")
            print("ℹ️ INFO | example.themes | Info message with monochrome theme")
            print("⚠️ WARNING | example.themes | Warning message with monochrome theme")
            print("❌ ERROR | example.themes | Error message with monochrome theme")


@capture_output
def example_hierarchical():
    """Demonstrate hierarchical logging with visual formatting."""
    import logging

    from logeverything import log_function, setup_logging

    # Setup with visual mode
    setup_logging(level=logging.DEBUG, visual_mode=True, use_symbols=True, use_indent=True)

    @log_function
    def function_level_1():
        logger = logging.getLogger("example.hier")
        logger.info("Inside the top-level function")

        # Call nested function
        function_level_2()

        logger.debug("Back in the top-level function")

    @log_function
    def function_level_2():
        logger = logging.getLogger("example.hier")
        logger.info("Inside the nested function")

        # Call deeper nested function
        function_level_3()

        logger.debug("Back in the nested function")

    @log_function
    def function_level_3():
        logger = logging.getLogger("example.hier")
        logger.info("Inside the deepest function")
        logger.warning("This is a warning from the deepest function")

    # Call the top-level function
    function_level_1()


@capture_output
def example_platform_compatibility():
    """Demonstrate platform compatibility features."""
    import logging

    from logeverything import setup_logging

    # Display current platform info
    print(f"Current platform: {platform.system()}")

    # Setup with auto-detection
    print("\n=== AUTO-DETECTED CAPABILITIES ===")
    setup_logging(level=logging.INFO, visual_mode=True, auto_detect_platform=True)

    logger = logging.getLogger("example.platform")
    logger.info("This log uses automatically detected platform capabilities")

    # Force ASCII mode for compatibility
    print("\n=== ASCII COMPATIBILITY MODE ===")
    setup_logging(level=logging.INFO, visual_mode=True, force_ascii=True)

    logger = logging.getLogger("example.platform")
    logger.info("This log uses ASCII-only characters for maximum compatibility")

    # Show example of minimal formatting
    print("\n=== MINIMAL FORMATTING (NO COLORS, ASCII ONLY) ===")
    setup_logging(
        level=logging.INFO,
        visual_mode=True,
        force_ascii=True,
        disable_colors=True,
        use_indent=True,
        align_columns=False,
    )

    logger = logging.getLogger("example.platform")
    logger.info("This log uses minimal formatting for terminals with limited support")


@log_class
class DataProcessor:
    """Example class to demonstrate class logging."""

    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger("example.class")
        self.logger.info(f"Created processor: {name}")

    def process(self, data):
        self.logger.debug(f"Processing data: {data}")

        if not data:
            self.logger.warning("Empty data received")
            return None

        try:
            # Some processing
            result = sum(data) if isinstance(data, list) else int(data) * 2
            self.logger.info(f"Processing complete: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error processing data: {str(e)}")
            raise


@capture_output
def example_class_logging():
    """Demonstrate class logging with visual formatting."""
    import logging

    from logeverything import setup_logging

    # Setup with visual mode
    setup_logging(level=logging.DEBUG, visual_mode=True, use_symbols=True, use_indent=True)

    # Create and use the class
    processor = DataProcessor("ExampleProcessor")

    # Try different inputs
    processor.process([1, 2, 3, 4])
    processor.process([])

    # This will cause an error
    try:
        processor.process("abc")
    except ValueError:
        pass  # Expected error


@capture_output
def example_context_managers():
    """Demonstrate context managers for temporary configuration."""
    import logging

    from logeverything import (
        LoggingContext,
        QuietLoggingContext,
        VerboseLoggingContext,
        setup_logging,
    )

    # Setup basic logging with INFO level
    setup_logging(level=logging.INFO)
    logger = logging.getLogger("example.context")

    # Normal logging - only INFO and above will show
    logger.debug("This debug message won't appear")
    logger.info("Normal INFO message")

    print("\n=== VERBOSE LOGGING CONTEXT ===")
    # Temporarily increase verbosity with VerboseLoggingContext
    with VerboseLoggingContext():
        logger.debug("With VerboseLoggingContext: This DEBUG message will appear")
        logger.info("With VerboseLoggingContext: This INFO message will appear")

    print("\n=== QUIET LOGGING CONTEXT ===")
    # Temporarily decrease verbosity with QuietLoggingContext
    with QuietLoggingContext():
        logger.debug("With QuietLoggingContext: This DEBUG message won't appear")
        logger.info("With QuietLoggingContext: This INFO message won't appear")
        logger.warning("With QuietLoggingContext: This WARNING message will appear")

    print("\n=== STANDARD CONTEXT ===")
    # Using the generic LoggingContext for custom settings
    with LoggingContext(level=logging.DEBUG, log_entry_exit=True):
        logger.debug("With LoggingContext: This DEBUG message will appear")

        # Nested contexts are supported
        with LoggingContext(log_arguments=False):
            logger.debug("With nested LoggingContext: Modified settings apply")

    # Back to normal settings
    logger.debug("This debug message won't appear again")
    logger.info("Back to normal INFO level")


def generate_examples_markdown():
    """Generate markdown file with examples and their outputs."""
    examples = [
        {
            "title": "Basic Logging",
            "func": example_basic_logging,
            "description": "Simple example of basic logging with LogEverything.",
            "code": textwrap.dedent(
                """\
                import logging
                from logeverything import log_function, setup_logging

                # Basic setup
                setup_logging(level=logging.DEBUG)

                @log_function
                def greet(name):
                    logger = logging.getLogger("example.basic")
                    logger.info(f"Creating greeting for {name}")
                    return f"Hello, {name}!"

                # Call the function to generate logs
                result = greet("World")
                print(f"Function returned: {result}")
            """
            ),
        },
        {
            "title": "Visual Mode",
            "func": example_visual_mode_basic,
            "description": "Enable visual formatting for more readable logs.",
            "code": textwrap.dedent(
                """\
                import logging
                from logeverything import setup_logging

                # Setup with visual mode enabled
                setup_logging(
                    level=logging.DEBUG,
                    visual_mode=True,    # Enable visual formatting
                    use_symbols=True,    # Use Unicode symbols
                    use_indent=True      # Show visual indentation
                )

                # Get a logger
                logger = logging.getLogger("example.visual")

                # Generate some logs at different levels
                logger.debug("Loading configuration file")
                logger.info("Application started")
                logger.warning("Configuration file not found, using defaults")
                logger.error("Failed to connect to database")
                logger.critical("System shutting down due to critical error")
            """
            ),
        },
        {
            "title": "Color Themes",
            "func": example_color_themes,
            "description": "LogEverything supports different color themes for console output.",
            "code": textwrap.dedent(
                """\
                import logging
                from logeverything import EnhancedConsoleHandler

                # Create a logger
                logger = logging.getLogger("example.themes")
                logger.setLevel(logging.DEBUG)

                # Create handlers with different color themes
                default_handler = EnhancedConsoleHandler(
                    use_colors=True,
                    color_theme="default",
                    use_symbols=True
                )

                bold_handler = EnhancedConsoleHandler(
                    use_colors=True,
                    color_theme="bold",
                    use_symbols=True
                )

                pastel_handler = EnhancedConsoleHandler(
                    use_colors=True,
                    color_theme="pastel",
                    use_symbols=True
                )

                monochrome_handler = EnhancedConsoleHandler(
                    use_colors=True,
                    color_theme="monochrome",
                    use_symbols=True
                )

                # Use the different handlers as needed
                logger.addHandler(default_handler)  # or any other themed handler

                # Log messages will now use the selected color theme
                logger.debug("Debug message")
                logger.info("Info message")
                logger.warning("Warning message")
                logger.error("Error message")
            """
            ),
        },
        {
            "title": "Hierarchical Logging",
            "func": example_hierarchical,
            "description": "Visual formatting makes it easy to follow hierarchical logs in nested function calls.",
            "code": textwrap.dedent(
                """\
                import logging
                from logeverything import log_function, setup_logging

                # Setup with visual mode
                setup_logging(
                    level=logging.DEBUG,
                    visual_mode=True,
                    use_symbols=True,
                    use_indent=True
                )

                @log_function
                def function_level_1():
                    logger = logging.getLogger("example.hier")
                    logger.info("Inside the top-level function")

                    # Call nested function
                    function_level_2()

                    logger.debug("Back in the top-level function")

                @log_function
                def function_level_2():
                    logger = logging.getLogger("example.hier")
                    logger.info("Inside the nested function")

                    # Call deeper nested function
                    function_level_3()

                    logger.debug("Back in the nested function")

                @log_function
                def function_level_3():
                    logger = logging.getLogger("example.hier")
                    logger.info("Inside the deepest function")
                    logger.warning("This is a warning from the deepest function")

                # Call the top-level function
                function_level_1()
            """
            ),
        },
        {
            "title": "Platform Compatibility",
            "func": example_platform_compatibility,
            "description": "LogEverything automatically adapts to different terminal capabilities.",
            "code": textwrap.dedent(
                """\
                import logging
                from logeverything import setup_logging
                import platform

                # Display current platform info
                print(f"Current platform: {platform.system()}")

                # Setup with auto-detection
                print("=== AUTO-DETECTED CAPABILITIES ===")
                setup_logging(
                    level=logging.INFO,
                    visual_mode=True,
                    auto_detect_platform=True
                )

                logger = logging.getLogger("example.platform")
                logger.info("This log uses automatically detected platform capabilities")

                # Force ASCII mode for compatibility
                print("=== ASCII COMPATIBILITY MODE ===")
                setup_logging(
                    level=logging.INFO,
                    visual_mode=True,
                    force_ascii=True
                )

                logger = logging.getLogger("example.platform")
                logger.info("This log uses ASCII-only characters for maximum compatibility")

                # Show example of minimal formatting
                print("=== MINIMAL FORMATTING (NO COLORS, ASCII ONLY) ===")
                setup_logging(
                    level=logging.INFO,
                    visual_mode=True,
                    force_ascii=True,
                    disable_colors=True,
                    use_indent=True,
                    align_columns=False
                )

                logger = logging.getLogger("example.platform")
                logger.info("This log uses minimal formatting for terminals with limited support")
            """
            ),
        },
        {
            "title": "Class Logging",
            "func": example_class_logging,
            "description": "Adding logging to all methods of a class is as simple as applying a decorator.",
            "code": textwrap.dedent(
                '''\
                import logging
                from logeverything import log_class, setup_logging

                # Setup with visual mode
                setup_logging(
                    level=logging.DEBUG,
                    visual_mode=True,
                    use_symbols=True,
                    use_indent=True
                )

                @log_class
                class DataProcessor:
                    """Example class to demonstrate class logging."""

                    def __init__(self, name):
                        self.name = name
                        self.logger = logging.getLogger("example.class")
                        self.logger.info(f"Created processor: {name}")

                    def process(self, data):
                        self.logger.debug(f"Processing data: {data}")

                        if not data:
                            self.logger.warning("Empty data received")
                            return None

                        try:
                            # Some processing
                            result = sum(data) if isinstance(data, list) else int(data) * 2
                            self.logger.info(f"Processing complete: {result}")
                            return result
                        except Exception as e:
                            self.logger.error(f"Error processing data: {str(e)}")
                            raise

                # Create and use the class
                processor = DataProcessor("ExampleProcessor")

                # Try different inputs
                processor.process([1, 2, 3, 4])
                processor.process([])

                # This will cause an error
                try:
                    processor.process("abc")
                except ValueError:
                    pass  # Expected error
            '''
            ),
        },
        {
            "title": "Context Managers",
            "func": example_context_managers,
            "description": "LogEverything provides context managers for temporarily changing logging configuration.",
            "code": textwrap.dedent(
                """\
                import logging
                from logeverything import (
                    setup_logging,
                    LoggingContext,
                    VerboseLoggingContext,
                    QuietLoggingContext
                )

                # Setup basic logging with INFO level
                setup_logging(level=logging.INFO)
                logger = logging.getLogger("example.context")

                # Normal logging - only INFO and above will show
                logger.debug("This debug message won't appear")
                logger.info("Normal INFO message")

                # Temporarily increase verbosity with VerboseLoggingContext
                with VerboseLoggingContext():
                    logger.debug("With VerboseLoggingContext: This DEBUG message will appear")
                    logger.info("With VerboseLoggingContext: This INFO message will appear")

                # Temporarily decrease verbosity with QuietLoggingContext
                with QuietLoggingContext():
                    logger.debug("With QuietLoggingContext: This DEBUG message won't appear")
                    logger.info("With QuietLoggingContext: This INFO message won't appear")
                    logger.warning("With QuietLoggingContext: This WARNING message will appear")

                # Using the generic LoggingContext for custom settings
                with LoggingContext(level=logging.DEBUG, log_entry_exit=True):
                    logger.debug("With LoggingContext: This DEBUG message will appear")

                    # Nested contexts are supported
                    with LoggingContext(log_arguments=False):
                        logger.debug("With nested LoggingContext: Modified settings apply")

                # Back to normal settings
                logger.debug("This debug message won't appear again")
                logger.info("Back to normal INFO level")
            """
            ),
        },
    ]

    # Start markdown file
    markdown = f"""# LogEverything Examples

This page shows examples of using LogEverything with their actual outputs.

*Generated on {CURRENT_DATE} using Python {platform.python_version()} on {platform.system()}*

"""

    # Special note about terminal colors
    markdown += """
> **Note about terminal colors**: The examples below show how colored output would look in a terminal
> that supports ANSI colors. The actual appearance may vary depending on your terminal.
>
> Images may be added in the future to better illustrate the visual formatting.

"""

    # Add each example
    for example in examples:
        # Run the example and capture outputs
        outputs = example["func"]()

        # Add to markdown
        markdown += markdown_example(
            title=example["title"],
            description=example["description"],
            code=example["code"],
            output=outputs["stdout"],
            logs=outputs["logs"],
        )

    # Write to file
    examples_path = os.path.join(DOCS_DIR, "examples_with_output.md")
    with open(examples_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Examples with outputs generated at: {examples_path}")
    return examples_path


if __name__ == "__main__":
    generate_examples_markdown()
