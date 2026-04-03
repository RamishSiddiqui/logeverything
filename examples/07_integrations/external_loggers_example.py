"""
Example demonstrating integration with external library loggers.

This example shows how to use LogEverything to integrate with and manage
logs from third-party libraries.
"""

import logging
import sys
from pathlib import Path

# Add the parent directory to the path for imports to work when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from logeverything import (
    configure_external_logger,
    log_function,
    setup_logging,
)


def setup():
    """Set up logging with external logger integration."""
    # Configure logging with all enabled
    setup_logging(
        level="INFO",
        visual_mode=True,
        integrate_external_loggers=True,  # Enable automatic integration with common loggers
    )

    # Show a message
    print("LogEverything configured with external logger integration enabled")
    print("Any logs from common libraries will now use our formatting\n")


def try_external_libraries():
    """Attempt to use some common libraries to demonstrate logging integration."""
    print("Trying to use external libraries for demonstration:")

    # Try mlflow
    try:
        import mlflow

        print("✓ MLflow imported")
        # Generate a log message from mlflow
        mlflow_logger = logging.getLogger("mlflow")
        mlflow_logger.info("This is a log message from MLflow")
    except ImportError:
        print("✗ MLflow not available (pip install mlflow to see integration)")

    # Try langchain
    try:
        import langchain

        print("✓ LangChain imported")
        # Generate a log message from langchain
        langchain_logger = logging.getLogger("langchain")
        langchain_logger.info("This is a log message from LangChain")
    except ImportError:
        print("✗ LangChain not available (pip install langchain to see integration)")

    # Try pandas
    try:
        import pandas

        print("✓ Pandas imported")
        # Generate a log message from pandas
        pandas_logger = logging.getLogger("pandas")
        pandas_logger.info("This is a log message from Pandas")
    except ImportError:
        print("✗ Pandas not available (pip install pandas to see integration)")

    print("\n")


@log_function
def manual_logger_integration():
    """Demonstrate manual integration with a specific external logger."""
    print("Manually integrating with a custom library logger:")

    # Create a logger that simulates an external library
    external_logger = logging.getLogger("external_library")

    # First, show the default formatting
    print("Before integration:")
    external_logger.info("This log message uses the default formatting")

    # Now integrate the external logger with LogEverything
    configure_external_logger("external_library", level="DEBUG", use_pretty_formatter=True)

    # Show the integrated formatting
    print("\nAfter integration:")
    external_logger.info("This log message uses LogEverything's formatting")
    external_logger.warning("This is a warning from the external library")
    external_logger.debug("This is a debug message (should be visible since we set level=DEBUG)")

    return "Logger integration successful"


if __name__ == "__main__":
    setup()
    try_external_libraries()
    manual_logger_integration()
