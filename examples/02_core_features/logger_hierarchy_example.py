#!/usr/bin/env python3
"""
Logger Hierarchy and Configuration Example

This example demonstrates LogEverything's logger hierarchy system,
configuration inheritance, and different logging patterns.
"""

import sys
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from logeverything import Logger
from logeverything.handlers import ConsoleHandler, FileHandler


def demonstrate_hierarchy():
    """Show how logger hierarchy works."""
    print("1. Logger Hierarchy")
    print("-" * 20)

    # Parent logger
    app_logger = Logger("myapp")
    app_logger.info("Application started")

    # Child loggers inherit from parent
    db_logger = Logger("myapp.database")
    api_logger = Logger("myapp.api")
    auth_logger = Logger("myapp.api.auth")

    db_logger.info("Database connection established")
    api_logger.info("API server started on port 8080")
    auth_logger.info("Authentication module loaded")

    # Grandchild logger
    jwt_logger = Logger("myapp.api.auth.jwt")
    jwt_logger.debug("JWT token validated")

    print("✓ Hierarchy: myapp -> myapp.database, myapp.api -> myapp.api.auth -> myapp.api.auth.jwt")


def demonstrate_configuration_inheritance():
    """Show how configuration is inherited through the hierarchy."""
    print("\n2. Configuration Inheritance")
    print("-" * 30)

    # Configure parent logger
    webapp_logger = Logger("webapp")
    webapp_logger.configure(
        level="INFO", visual_mode=True, use_symbols=True, format_type="detailed"
    )

    # Child loggers inherit configuration
    db_logger = Logger("webapp.database")
    cache_logger = Logger("webapp.cache")

    db_logger.info("Database query executed")
    cache_logger.warning("Cache miss for key: user_123")

    # Override configuration for specific logger
    security_logger = Logger("webapp.security")
    security_logger.configure(level="DEBUG", use_colors=True)
    security_logger.debug("Security check passed")
    security_logger.error("Unauthorized access attempt")

    print("✓ Child loggers inherit parent configuration")
    print("✓ Individual loggers can override specific settings")


def demonstrate_different_handlers():
    """Show different handlers for different logger levels."""
    print("\n3. Different Handlers per Logger Level")
    print("-" * 40)

    # Root application logger with custom handlers
    root_logger = Logger("enterprise", auto_setup=False)

    # Add console handler for general logs
    console_handler = ConsoleHandler()
    root_logger.add_handler(console_handler)

    # Database logger with file handler
    db_logger = Logger("enterprise.database", auto_setup=False)
    db_file_handler = FileHandler("database.log")
    db_logger.add_handler(db_file_handler)

    # Security logger with separate file
    security_logger = Logger("enterprise.security", auto_setup=False)
    security_file_handler = FileHandler("security.log")
    security_logger.add_handler(security_file_handler)

    # API logger with both console and file
    api_logger = Logger("enterprise.api", auto_setup=False)
    api_file_handler = FileHandler("api.log")
    api_logger.add_handler(api_file_handler)

    # Test logging to different handlers
    root_logger.info("Enterprise application started")
    db_logger.info("Database connection pool created")
    security_logger.warning("Failed login attempt from IP: 192.168.1.100")
    api_logger.info("REST API endpoint /users called")

    print("✓ Different loggers writing to different files")
    print("✓ enterprise.log, database.log, security.log, api.log created")


def demonstrate_logger_patterns():
    """Show common logging patterns."""
    print("\n4. Common Logging Patterns")
    print("-" * 30)

    # Pattern 1: Module-level logger
    module_logger = Logger(__name__)
    module_logger.info("Module-level logging pattern")

    # Pattern 2: Class-based logging
    class UserService:
        def __init__(self):
            self.logger = Logger(f"{__name__}.{self.__class__.__name__}")

        def create_user(self, username):
            self.logger.info(f"Creating user: {username}")
            return f"user_{username}"

        def delete_user(self, user_id):
            self.logger.warning(f"Deleting user: {user_id}")

    user_service = UserService()
    user_service.create_user("alice")
    user_service.delete_user("user_123")

    # Pattern 3: Function-specific logging
    def process_payment(amount, currency):
        payment_logger = Logger("payment_processor")
        payment_logger.info(f"Processing payment: {amount} {currency}")
        return f"Payment of {amount} {currency} processed"

    process_payment(99.99, "USD")

    # Pattern 4: Feature-based logging
    feature_loggers = {
        "auth": Logger("app.features.authentication"),
        "billing": Logger("app.features.billing"),
        "notifications": Logger("app.features.notifications"),
    }

    feature_loggers["auth"].info("User authenticated successfully")
    feature_loggers["billing"].info("Invoice generated")
    feature_loggers["notifications"].info("Email notification sent")

    print("✓ Module-level, class-based, function-specific, and feature-based patterns")


def demonstrate_conditional_logging():
    """Show conditional and performance-conscious logging."""
    print("\n5. Conditional and Performance Logging")
    print("-" * 40)

    perf_logger = Logger("performance")

    # Conditional logging based on conditions
    error_count = 5
    if error_count > 3:
        perf_logger.warning(f"High error count detected: {error_count}")

    # Lazy evaluation for expensive operations
    def expensive_debug_info():
        # Simulate expensive operation
        return "Expensive debug information"

    # Only call expensive function if DEBUG level is enabled
    if perf_logger.level <= 10:  # DEBUG level is 10
        perf_logger.debug(f"Debug info: {expensive_debug_info()}")
    else:
        perf_logger.info("Debug info not generated (DEBUG level disabled)")

    # Using format strings efficiently
    user_id = 12345
    action = "login"
    perf_logger.info("User %s performed action: %s", user_id, action)

    print("✓ Conditional logging and performance optimizations")


def main():
    print("=== Logger Hierarchy and Configuration Demo ===\n")

    demonstrate_hierarchy()
    demonstrate_configuration_inheritance()
    demonstrate_different_handlers()
    demonstrate_logger_patterns()
    demonstrate_conditional_logging()

    print("\n✓ Logger hierarchy and configuration demonstration complete!")
    print("\nKey Concepts Demonstrated:")
    print("- Hierarchical logger structure")
    print("- Configuration inheritance")
    print("- Multiple handlers per logger")
    print("- Common logging patterns")
    print("- Performance-conscious logging")
    print("- Conditional logging strategies")


if __name__ == "__main__":
    main()
