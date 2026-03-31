#!/usr/bin/env python3
"""
Advanced Context Managers Example

This example demonstrates LogEverything's powerful context manager features
for automatic logging of operations, resource management, and hierarchical
logging contexts.
"""

import contextlib
import sys
import tempfile
import time
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from logeverything import Logger, configure
from logeverything.contexts import error_context, log_context, performance_context


def basic_context_managers():
    """Demonstrate basic context manager usage."""
    print("1. Basic Context Managers")
    print("-" * 30)

    logger = Logger("context_demo")

    # Basic log context
    with log_context("Processing user data", logger=logger):
        logger.info("Fetching user from database")
        time.sleep(0.1)  # Simulate DB query
        logger.info("User data retrieved successfully")

        with log_context("Validating user permissions", logger=logger, level="DEBUG"):
            logger.debug("Checking user role")
            logger.debug("Checking resource permissions")
            logger.info("Permissions validated")

    print("✓ Basic context managers completed")


def performance_monitoring():
    """Show performance monitoring with context managers."""
    print("\n2. Performance Monitoring")
    print("-" * 35)

    perf_logger = Logger("performance")

    # Performance context automatically measures execution time
    with performance_context("Database operation", logger=perf_logger):
        time.sleep(0.2)  # Simulate slow DB operation

    with performance_context("API call", logger=perf_logger, threshold=0.1):
        time.sleep(0.05)  # Fast operation

    with performance_context("Heavy computation", logger=perf_logger, threshold=0.1):
        time.sleep(0.15)  # Slow operation (will trigger warning)

    print("✓ Performance monitoring completed")


def error_handling_contexts():
    """Demonstrate error handling with context managers."""
    print("\n3. Error Handling Contexts")
    print("-" * 35)

    error_logger = Logger("error_handling")

    # Error context catches and logs exceptions
    with error_context("Safe operation", logger=error_logger):
        error_logger.info("This operation will succeed")
        time.sleep(0.05)

    # This will catch and log the exception
    try:
        with error_context("Risky operation", logger=error_logger, reraise=False):
            error_logger.info("Starting risky operation")
            raise ValueError("Something went wrong!")
    except ValueError:
        pass  # Exception was suppressed by context manager

    # This will log and re-raise the exception
    try:
        with error_context("Critical operation", logger=error_logger, reraise=True):
            error_logger.info("Starting critical operation")
            raise RuntimeError("Critical failure!")
    except RuntimeError as e:
        error_logger.info(f"Caught re-raised exception: {e}")

    print("✓ Error handling contexts completed")


def nested_contexts():
    """Show nested context managers."""
    print("\n4. Nested Context Managers")
    print("-" * 35)

    nested_logger = Logger("nested_operations")

    with log_context("User registration process", logger=nested_logger):
        with performance_context("Input validation", logger=nested_logger):
            nested_logger.info("Validating email format")
            nested_logger.info("Checking password strength")
            time.sleep(0.03)

        with performance_context("Database operations", logger=nested_logger):
            with log_context("User creation", logger=nested_logger):
                nested_logger.info("Creating user record")
                time.sleep(0.1)

            with log_context("Profile setup", logger=nested_logger):
                nested_logger.info("Creating user profile")
                time.sleep(0.05)

        with error_context("Email notification", logger=nested_logger, reraise=False):
            nested_logger.info("Sending welcome email")
            # Simulate email service failure
            if False:  # Change to True to simulate failure
                raise ConnectionError("Email service unavailable")

    print("✓ Nested contexts completed")


class DatabaseConnection:
    """Custom context manager for database connections."""

    def __init__(self, db_name, logger=None):
        self.db_name = db_name
        self.logger = logger or Logger(f"db.{db_name}")
        self.connection = None

    def __enter__(self):
        self.logger.info(f"Connecting to database: {self.db_name}")
        time.sleep(0.1)  # Simulate connection time
        self.connection = f"connection_to_{self.db_name}"
        self.logger.info(f"Connected to {self.db_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(f"Database error in {self.db_name}: {exc_val}")
        else:
            self.logger.info(f"Database operation completed successfully")

        self.logger.info(f"Closing connection to {self.db_name}")
        time.sleep(0.05)  # Simulate cleanup
        self.connection = None
        return False  # Don't suppress exceptions

    def execute(self, query):
        """Execute a database query."""
        if not self.connection:
            raise RuntimeError("Not connected to database")

        self.logger.debug(f"Executing query: {query}")
        time.sleep(0.02)  # Simulate query execution
        return f"Result for: {query}"


def custom_context_managers():
    """Show custom context managers with logging."""
    print("\n5. Custom Context Managers")
    print("-" * 35)

    # Use custom database context manager
    with DatabaseConnection("users_db") as db:
        result1 = db.execute("SELECT * FROM users")
        result2 = db.execute("SELECT COUNT(*) FROM users")

    # Demonstrate error handling in custom context manager
    try:
        with DatabaseConnection("payments_db") as db:
            db.execute("SELECT * FROM payments")
            raise ValueError("Payment processing error")
    except ValueError:
        pass  # Exception was logged by context manager

    print("✓ Custom context managers completed")


class LoggingFileHandler:
    """File handler with comprehensive logging."""

    def __init__(self, operation_name, logger=None):
        self.operation_name = operation_name
        self.logger = logger or Logger("file_operations")
        self.temp_files = []

    def __enter__(self):
        self.logger.info(f"Starting file operation: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup temporary files
        for temp_file in self.temp_files:
            try:
                temp_file.unlink()
                self.logger.debug(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                self.logger.warning(f"Failed to cleanup {temp_file}: {e}")

        if exc_type:
            self.logger.error(f"File operation '{self.operation_name}' failed: {exc_val}")
        else:
            self.logger.info(f"File operation '{self.operation_name}' completed successfully")

        return False

    def create_temp_file(self, content=""):
        """Create a temporary file with logging."""
        temp_file = Path(tempfile.mktemp())
        temp_file.write_text(content)
        self.temp_files.append(temp_file)
        self.logger.info(f"Created temporary file: {temp_file}")
        return temp_file

    def process_file(self, filepath, operation):
        """Process a file with logging."""
        self.logger.info(f"Processing file: {filepath}")

        try:
            if operation == "read":
                content = filepath.read_text()
                self.logger.debug(f"Read {len(content)} characters from {filepath}")
                return content
            elif operation == "size":
                size = filepath.stat().st_size
                self.logger.debug(f"File size: {size} bytes")
                return size
            else:
                raise ValueError(f"Unknown operation: {operation}")

        except Exception as e:
            self.logger.error(f"Failed to process {filepath}: {e}")
            raise


def file_operations_context():
    """Demonstrate file operations with context managers."""
    print("\n6. File Operations Context")
    print("-" * 35)

    with LoggingFileHandler("Document processing") as file_handler:
        # Create some temporary files
        doc1 = file_handler.create_temp_file("This is document 1 content")
        doc2 = file_handler.create_temp_file("This is document 2 with more content")

        # Process files
        content1 = file_handler.process_file(doc1, "read")
        size2 = file_handler.process_file(doc2, "size")

        # Simulate some processing
        time.sleep(0.1)

    print("✓ File operations with cleanup completed")


@contextlib.contextmanager
def transaction_context(transaction_id, logger=None):
    """Context manager for database-like transactions."""
    transaction_logger = logger or Logger("transactions")

    transaction_logger.info(f"Starting transaction {transaction_id}")
    start_time = time.time()

    try:
        yield transaction_id

        # Transaction succeeded
        duration = time.time() - start_time
        transaction_logger.info(f"Transaction {transaction_id} committed in {duration:.3f}s")

    except Exception as e:
        # Transaction failed
        duration = time.time() - start_time
        transaction_logger.error(
            f"Transaction {transaction_id} rolled back after {duration:.3f}s: {e}"
        )
        raise


def advanced_context_patterns():
    """Show advanced context manager patterns."""
    print("\n7. Advanced Context Patterns")
    print("-" * 35)

    trans_logger = Logger("transaction_manager")

    # Successful transaction
    with transaction_context("txn_001", trans_logger) as txn_id:
        trans_logger.info(f"Processing in {txn_id}")
        time.sleep(0.1)
        trans_logger.info("Business logic completed")

    # Failed transaction
    try:
        with transaction_context("txn_002", trans_logger) as txn_id:
            trans_logger.info(f"Processing in {txn_id}")
            time.sleep(0.05)
            raise ValueError("Business logic error")
    except ValueError:
        pass  # Exception was logged by context manager

    # Multiple concurrent contexts
    contexts = []
    for i in range(3):
        contexts.append(log_context(f"Parallel operation {i+1}", logger=trans_logger))

    # Enter all contexts
    entered_contexts = [ctx.__enter__() for ctx in contexts]

    try:
        trans_logger.info("All parallel operations started")
        time.sleep(0.1)
        trans_logger.info("All parallel operations completed")
    finally:
        # Exit all contexts in reverse order
        for ctx in reversed(contexts):
            ctx.__exit__(None, None, None)

    print("✓ Advanced context patterns completed")


def main():
    """Main function demonstrating all context manager features."""
    print("=== Advanced Context Managers Demo ===\n")

    # Configure logging
    configure(level="DEBUG", visual_mode=True, use_symbols=True)

    basic_context_managers()
    performance_monitoring()
    error_handling_contexts()
    nested_contexts()
    custom_context_managers()
    file_operations_context()
    advanced_context_patterns()

    print("\n✓ Advanced context managers demonstration complete!")
    print("\nFeatures Demonstrated:")
    print("- Basic log contexts for operation grouping")
    print("- Performance monitoring with automatic timing")
    print("- Error handling with exception catching/logging")
    print("- Nested context managers for complex workflows")
    print("- Custom context managers with resource cleanup")
    print("- File operations with automatic cleanup")
    print("- Transaction-like patterns")
    print("- Multiple concurrent contexts")
    print("- Integration with LogEverything's visual modes")


if __name__ == "__main__":
    main()
