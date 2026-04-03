"""
Example demonstrating LogEverything integration with SQLAlchemy using context managers.

This example shows how to use context managers with SQLAlchemy to provide
appropriate logging for database operations, transactions, and query performance.
"""

import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logeverything as le
from logeverything import (
    LoggingContext,
    QuietLoggingContext,
    TemporaryFileHandlerContext,
    VerboseLoggingContext,
    VisualLoggingContext,
)


# Mock SQLAlchemy functionality for demonstration
class MockSession:
    """Mock SQLAlchemy session for demonstration."""

    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


class MockModel:
    """Mock SQLAlchemy model for demonstration."""

    def __init__(self, id=None, **kwargs):
        self.id = id or 0
        for key, value in kwargs.items():
            setattr(self, key, value)
        self._changes = {}

    def __repr__(self):
        attrs = ", ".join(
            f"{key}={value}" for key, value in self.__dict__.items() if not key.startswith("_")
        )
        return f"<{self.__class__.__name__}({attrs})>"


# Setup logging for database operations
logger = le.setup_logging(
    level=logging.INFO, handlers=["console"], log_entry_exit=True, beautify=True
)

db_logger = le.get_logger("database")


# Custom context managers for database operations
class TransactionContext:
    """
    Context manager for database transactions that integrates with LogEverything.

    This context manager wraps around SQLAlchemy transactions and provides
    appropriately detailed logging at each stage of the transaction.

    Example:
        with TransactionContext(session, "create_user") as tx_session:
            user = User(name="Alice", email="alice@example.com")
            tx_session.add(user)
    """

    def __init__(self, session, operation_name: str):
        self.session = session
        self.operation_name = operation_name
        self.start_time = None
        self.logger = db_logger

    def __enter__(self):
        # Use VerboseLoggingContext to capture detailed information during transaction start
        with VerboseLoggingContext():
            self.start_time = time.time()
            self.logger.debug(f"Starting transaction for '{self.operation_name}'")
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Calculate duration
        duration = time.time() - self.start_time

        if exc_type:
            # Use VerboseLoggingContext with error level for exceptions
            with VerboseLoggingContext(level=logging.ERROR):
                self.logger.error(
                    f"Transaction '{self.operation_name}' failed after {duration:.3f}s: {exc_val}"
                )
                try:
                    # Log additional error details at DEBUG level
                    self.logger.debug(
                        f"Rolling back transaction due to {exc_type.__name__}: {exc_val}"
                    )
                    self.session.rollback()
                except Exception as rollback_error:
                    self.logger.error(f"Rollback also failed: {rollback_error}")
            # Don't suppress the exception
            return False
        else:
            # Use different logging contexts based on transaction duration
            if duration > 1.0:
                # Slow transactions get warning level with visual formatting
                with VisualLoggingContext(level=logging.WARNING):
                    self.logger.warning(
                        f"⚠️ Slow transaction '{self.operation_name}' completed in {duration:.3f}s"
                    )
                    try:
                        self.session.commit()
                    except Exception as commit_error:
                        self.logger.error(f"Commit failed: {commit_error}")
                        self.session.rollback()
                        return False
            else:
                # Fast transactions get quieter logging
                with QuietLoggingContext():
                    self.logger.info(
                        f"Transaction '{self.operation_name}' completed in {duration:.3f}s"
                    )
                    try:
                        self.session.commit()
                    except Exception as commit_error:
                        # Switch to error context if commit fails
                        with LoggingContext(level=logging.ERROR):
                            self.logger.error(f"Commit failed: {commit_error}")
                        self.session.rollback()
                        return False

            return True


class QueryPerformanceContext:
    """
    Context manager for tracking and logging query performance.

    This context manager helps identify slow-performing queries and logs appropriate
    information based on query duration.

    Example:
        with QueryPerformanceContext("find_users_by_role", query_params={"role": "admin"}):
            users = session.query(User).filter_by(role="admin").all()
    """

    def __init__(
        self,
        query_name: str,
        query_params: Optional[Dict] = None,
        slow_threshold: float = 0.5,
        very_slow_threshold: float = 2.0,
    ):
        self.query_name = query_name
        self.query_params = query_params or {}
        self.slow_threshold = slow_threshold
        self.very_slow_threshold = very_slow_threshold
        self.start_time = None
        self.logger = db_logger

    def __enter__(self):
        # Use minimal logging for query start
        with QuietLoggingContext():
            self.start_time = time.time()
            # Log query parameters at debug level only
            self.logger.debug(
                f"Executing query '{self.query_name}' with params: {self.query_params}"
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        if exc_type:
            # Use VerboseLoggingContext for query errors
            with VerboseLoggingContext(level=logging.ERROR):
                self.logger.error(
                    f"Query '{self.query_name}' failed after {duration:.3f}s: {exc_val}"
                )
            return False

        # Use different logging contexts based on query duration
        if duration >= self.very_slow_threshold:
            # Very slow queries get error level with detailed context
            with VerboseLoggingContext(level=logging.ERROR):
                self.logger.error(f"🚨 Very slow query '{self.query_name}' took {duration:.3f}s")
                # Log detailed info to a dedicated file for performance analysis
                with TemporaryFileHandlerContext("slow_queries.log"):
                    self.logger.error(f"Query: {self.query_name}")
                    self.logger.error(f"Params: {self.query_params}")
                    self.logger.error(f"Duration: {duration:.3f}s")
                    self.logger.error(f"Timestamp: {datetime.now().isoformat()}")
                    self.logger.error("-" * 50)
        elif duration >= self.slow_threshold:
            # Slow queries get warning level
            with LoggingContext(level=logging.WARNING):
                self.logger.warning(f"⚠️ Slow query '{self.query_name}' took {duration:.3f}s")
        else:
            # Fast queries get debug level only
            with QuietLoggingContext(level=logging.DEBUG):
                self.logger.debug(f"Query '{self.query_name}' completed in {duration:.3f}s")

        return True


# Mock database models and repositories
class User(MockModel):
    """Mock User model."""

    def __init__(self, id=None, name=None, email=None, role="user", created_at=None):
        super().__init__(id=id)
        self.name = name
        self.email = email
        self.role = role
        self.created_at = created_at or datetime.now()


class UserRepository:
    """
    Example repository using SQLAlchemy with context managers for logging.

    This demonstrates how to integrate LogEverything context managers with
    a repository pattern for database access.
    """

    def __init__(self):
        self.session = MockSession()  # In real code, this would be a SQLAlchemy session
        self.logger = db_logger

    @le.log
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID with performance tracking."""
        with QueryPerformanceContext("get_user_by_id", {"user_id": user_id}):
            # Simulate query execution
            time.sleep(0.1)  # Fast query

            # Mock user retrieval
            if user_id > 0 and user_id < 100:
                return User(
                    id=user_id,
                    name=f"User {user_id}",
                    email=f"user{user_id}@example.com",
                    role="user" if user_id > 10 else "admin",
                )
            return None

    @le.log
    def find_users_by_role(self, role: str) -> List[User]:
        """Find users by role with performance tracking."""
        with QueryPerformanceContext("find_users_by_role", {"role": role}):
            # Simulate query execution
            # Slow query for admin role to demonstrate performance logging
            if role == "admin":
                time.sleep(2.5)  # Very slow query
            else:
                time.sleep(0.6)  # Slow query

            # Mock user retrieval
            if role == "admin":
                return [
                    User(id=i, name=f"Admin {i}", email=f"admin{i}@example.com", role="admin")
                    for i in range(1, 6)
                ]
            else:
                return [
                    User(id=i, name=f"User {i}", email=f"user{i}@example.com", role=role)
                    for i in range(10, 20)
                ]

    @le.log
    def create_user(self, name: str, email: str, role: str = "user") -> User:
        """Create a new user with transaction management."""
        with TransactionContext(self.session, "create_user"):
            # Simulate user creation
            time.sleep(0.3)

            # Create new user
            new_id = 100  # In a real app, this would be generated by the database
            new_user = User(id=new_id, name=name, email=email, role=role)

            # Log user creation at info level
            self.logger.info(f"Created user: id={new_id}, name={name}, role={role}")

            return new_user

    @le.log
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update a user with transaction management."""
        with TransactionContext(self.session, "update_user"):
            # First get the user
            user = self.get_user_by_id(user_id)
            if not user:
                return None

            # Apply updates
            for key, value in kwargs.items():
                if hasattr(user, key):
                    old_value = getattr(user, key)
                    setattr(user, key, value)
                    # Log each changed attribute
                    self.logger.debug(f"Changed {user_id}.{key}: {old_value} → {value}")

            # Simulate slow update for admin role changes
            if kwargs.get("role") == "admin":
                time.sleep(1.2)  # Slow transaction
            else:
                time.sleep(0.2)  # Fast transaction

            return user

    @le.log
    def delete_user(self, user_id: int) -> bool:
        """Delete a user with transaction management."""
        with TransactionContext(self.session, "delete_user"):
            # Use LoggingContext to ensure sensitive operation gets proper logging
            with VisualLoggingContext(level=logging.WARNING):
                self.logger.warning(f"⚠️ Deleting user {user_id} ⚠️")

                # Check if user exists
                user = self.get_user_by_id(user_id)
                if not user:
                    self.logger.warning(f"Cannot delete non-existent user: {user_id}")
                    return False

                # Extra logging for admin user deletion
                if user.role == "admin":
                    self.logger.error(f"🚨 DELETING ADMIN USER: {user.name} (ID: {user.id}) 🚨")

                # Simulate deletion
                time.sleep(0.5)

                return True


def simulate_database_operations():
    """Run a simulation of database operations with context managers for logging."""
    logger.info("Starting database operation simulation")

    # Initialize repository
    user_repo = UserRepository()

    # Simulate different database operations
    with LoggingContext(logger_name="database.simulation", log_arguments=True):
        try:
            # Get individual users
            logger.info("Fetching individual users")
            user1 = user_repo.get_user_by_id(1)
            user50 = user_repo.get_user_by_id(50)
            user999 = user_repo.get_user_by_id(999)  # Non-existent user

            # Find users by role - demonstrates slow query logging
            logger.info("Finding users by role")
            admins = user_repo.find_users_by_role("admin")
            users = user_repo.find_users_by_role("user")

            # Create a new user
            logger.info("Creating new users")
            new_user = user_repo.create_user("Alice Smith", "alice@example.com")
            new_admin = user_repo.create_user("Bob Johnson", "bob@example.com", role="admin")

            # Update users - some updates will be slow, some fast
            logger.info("Updating users")
            updated_user = user_repo.update_user(50, name="Updated User")
            promoted_user = user_repo.update_user(20, role="admin")  # Slow update

            # Delete users
            logger.info("Deleting users")
            user_repo.delete_user(50)
            user_repo.delete_user(1)  # Admin user
            user_repo.delete_user(999)  # Non-existent user

        except Exception as e:
            logger.exception(f"Error in database simulation: {str(e)}")

    logger.info("Database operation simulation completed")


if __name__ == "__main__":
    simulate_database_operations()
