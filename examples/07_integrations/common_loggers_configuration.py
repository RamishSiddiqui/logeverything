"""
Example demonstrating LogEverything's integration with external loggers.

This example shows how to use LogEverything's configure_common_loggers function to
automatically detect and configure external libraries' loggers for a consistent
logging experience across your entire application and its dependencies.
"""

import logging
import os
import sys

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logeverything as le
from logeverything.external import configure_common_loggers, configure_external_logger


def setup_main_logger():
    """Set up the main application logger."""
    # Set up LogEverything with desired configuration
    logger = le.setup_logging(
        level=logging.INFO,
        handlers=["console", "file"],
        file_path="external_loggers_integration.log",
        beautify=True,
        log_entry_exit=True,
        # Configure the default level for external loggers
        external_logger_level=logging.WARNING,  # Default level for external loggers
    )

    logger.info("Main application logger configured")
    return logger


@le.log
def demonstrate_manual_external_logger_config():
    """Demonstrate manually configuring specific external loggers."""
    logger = logging.getLogger(__name__)
    logger.info("Manually configuring specific external loggers")

    # Configure specific external loggers individually with different settings
    requests_logger = configure_external_logger(
        "requests", level=logging.WARNING, use_pretty_formatter=True, propagate=False
    )

    urllib3_logger = configure_external_logger(
        "urllib3",
        level=logging.ERROR,  # Higher level to reduce noise
        use_pretty_formatter=True,
        propagate=False,
    )

    # Now these loggers will use LogEverything's formatting
    logger.info("External loggers configured individually")

    # Log something using these loggers
    requests_logger.warning("This is a warning from the requests library")
    urllib3_logger.error("This is an error from the urllib3 library")


@le.log
def demonstrate_common_loggers_auto_config():
    """Demonstrate automatic configuration of common external loggers."""
    logger = logging.getLogger(__name__)
    logger.info("Automatically configuring common external loggers")

    # Configure all common external loggers at once
    configured_loggers = configure_common_loggers(
        level=logging.INFO,
        use_pretty_formatter=True,
        propagate=False,
        show_warnings=True,  # Show warnings for missing dependencies
    )

    logger.info(f"Configured {len(configured_loggers)} common loggers:")
    for logger_name in configured_loggers:
        logger.info(f"  - {logger_name}")

    # Try to use some of these loggers if available
    # These will be configured with LogEverything's formatting
    for logger_name in configured_loggers:
        external_logger = logging.getLogger(logger_name)
        external_logger.info(f"Test message from {logger_name}")
        external_logger.warning(f"Warning message from {logger_name}")


@le.log
def demonstrate_selective_logger_config():
    """Demonstrate selective configuration of external loggers."""
    logger = logging.getLogger(__name__)
    logger.info("Selectively configuring external loggers")

    # Configure only specific loggers and exclude others
    configured_loggers = configure_common_loggers(
        additional_loggers=[
            "custom_library",  # A custom logger not in the default list
            ("special.logger", "special"),  # Logger name with associated module
        ],
        exclude_loggers=["sqlalchemy", "alembic"],  # Exclude specific loggers
        level=logging.DEBUG,
        use_pretty_formatter=True,
    )

    logger.info(f"Selectively configured {len(configured_loggers)} loggers")


@le.log
def demonstrate_library_integration(logger):
    """Demonstrate integration with various libraries using mock imports."""
    logger.info("Demonstrating integration with various libraries")

    # We'll simulate various libraries to show how their logs would appear
    # when configured with LogEverything

    # Create simulated loggers for popular libraries
    simulated_libs = ["pandas", "numpy", "tensorflow", "torch", "fastapi", "sqlalchemy"]

    # Configure these loggers
    configure_common_loggers(additional_loggers=simulated_libs, level=logging.INFO)

    # Simulate log messages from these libraries
    logger.info("Simulated logs from external libraries:")

    # Pandas log
    pandas_logger = logging.getLogger("pandas")
    pandas_logger.info("DataFrame created with 10000 rows and 50 columns")
    pandas_logger.warning("Missing values detected in column 'revenue'")

    # NumPy log
    numpy_logger = logging.getLogger("numpy")
    numpy_logger.info("Array operation completed in 0.25s")
    numpy_logger.warning("Overflow encountered in matrix multiplication")

    # TensorFlow log
    tf_logger = logging.getLogger("tensorflow")
    tf_logger.info("Model training: Epoch 1/10, loss=0.342, accuracy=0.891")
    tf_logger.warning("GPU memory usage at 85%")

    # PyTorch log
    torch_logger = logging.getLogger("torch")
    torch_logger.info("CUDA device initialized: GeForce RTX 3080")
    torch_logger.warning("Gradient clipping applied - values exceeded threshold")

    # FastAPI log
    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.info("GET /api/users - 200 OK - 45ms")
    fastapi_logger.warning("Rate limit exceeded for client 192.168.1.105")

    # SQLAlchemy log
    sqlalchemy_logger = logging.getLogger("sqlalchemy")
    sqlalchemy_logger.info("Connected to PostgreSQL database 'production'")
    sqlalchemy_logger.warning("Slow query detected: SELECT * FROM orders WHERE...")


@le.log
def demonstrate_nested_loggers():
    """Demonstrate handling nested and hierarchical loggers."""
    logger = logging.getLogger(__name__)
    logger.info("Setting up hierarchical logger configuration")

    # Configure parent loggers
    configure_external_logger("api", level=logging.INFO)
    configure_external_logger("database", level=logging.WARNING)

    # Child loggers
    api_auth_logger = logging.getLogger("api.auth")
    api_users_logger = logging.getLogger("api.users")
    db_queries_logger = logging.getLogger("database.queries")
    db_migrations_logger = logging.getLogger("database.migrations")

    # Log with parent loggers
    parent_api = logging.getLogger("api")
    parent_api.info("API service started")

    parent_db = logging.getLogger("database")
    parent_db.warning("Database connection pool at 80% capacity")

    # Log with child loggers - these inherit properties from parents
    # when propagation is enabled
    api_auth_logger.info("User authentication successful")
    api_users_logger.warning("Failed login attempt for user 'admin'")

    db_queries_logger.warning("Query execution time exceeded threshold")
    db_migrations_logger.error("Migration failed: Unable to add column 'tax_id'")


@le.log
def run_demonstration():
    """Run a complete demonstration of external logger integration."""
    logger = setup_main_logger()
    logger.info("Starting external logger integration demonstration")

    try:
        # Demonstrate different ways to configure external loggers
        demonstrate_manual_external_logger_config()
        demonstrate_common_loggers_auto_config()
        demonstrate_selective_logger_config()

        # Demonstrate integration with libraries
        demonstrate_library_integration(logger)

        # Demonstrate hierarchical logger configuration
        demonstrate_nested_loggers()

        logger.info("External logger integration demonstration completed successfully")

    except Exception as e:
        logger.exception(f"Error in demonstration: {e}")


if __name__ == "__main__":
    run_demonstration()
