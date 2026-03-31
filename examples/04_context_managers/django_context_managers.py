"""
Example demonstrating LogEverything integration with Django using context managers.

This example shows how to use LogEverything's context managers for different parts
of a Django application, including views, models, forms and middleware.
"""

import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

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

# Setup logging - this would normally be in Django's settings.py
le.setup_logging(
    profile="api",  # API profile works well with Django
    level=logging.INFO,
    file_path="django_app.log",
    async_mode=True,
    capture_print=True,
)

# Get logger
logger = le.get_logger("django_app")

# Configure Django's loggers
le.configure_external_logger("django", level=logging.INFO)
le.configure_external_logger("django.request", level=logging.WARNING)
le.configure_external_logger("django.db.backends", level=logging.WARNING)


# ---------------------
# Django Model Example
# ---------------------


@dataclass
class User:
    """Example User model."""

    id: int
    username: str
    email: str
    is_active: bool = True


class UserManager:
    """Example User manager demonstrating context managers for CRUD operations."""

    def __init__(self):
        self.logger = le.get_logger("django_app.models.user")
        # Mock database
        self.users = {
            1: User(id=1, username="admin", email="admin@example.com"),
            2: User(id=2, username="user1", email="user1@example.com"),
            3: User(id=3, username="user2", email="user2@example.com"),
        }

    @le.log
    def get_user(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        self.logger.info(f"Getting user with ID: {user_id}")
        return self.users.get(user_id)

    @le.log
    def create_user(self, username: str, email: str) -> User:
        """
        Create a new user with context managers for different logging levels
        based on conditions.
        """
        # Use VerboseLoggingContext for enhanced logging during user creation
        with VerboseLoggingContext(level=logging.DEBUG):
            self.logger.info(f"Creating new user: {username}")

            # Check if username already exists - important check gets detailed logging
            if any(u.username == username for u in self.users.values()):
                self.logger.warning(f"Username '{username}' already exists")
                raise ValueError(f"Username '{username}' already exists")

            # Create new user
            new_id = max(self.users.keys()) + 1 if self.users else 1
            new_user = User(id=new_id, username=username, email=email)

            # Log sensitive operations
            self.logger.debug(f"Assigning ID {new_id} to new user")
            self.logger.debug(f"User data: {new_user}")

            # Store user
            self.users[new_id] = new_user
            self.logger.info(f"User created successfully with ID {new_id}")

            return new_user

    @le.log
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user attributes with conditional context managers."""
        user = self.users.get(user_id)
        if not user:
            self.logger.warning(f"User with ID {user_id} not found")
            return None

        # Use standard logging for most updates
        self.logger.info(f"Updating user {user_id} with {kwargs}")

        # Special handling for email changes with extra verification logging
        if "email" in kwargs:
            # Use TemporaryFileHandlerContext to log email changes to audit log
            with TemporaryFileHandlerContext("user_email_changes.log"):
                old_email = user.email
                user.email = kwargs["email"]
                self.logger.info(
                    f"Email changed for user {user.username}: {old_email} → {user.email}"
                )
                del kwargs["email"]  # Remove from kwargs as we've handled it

        # Handle other attributes with quieter logging for routine updates
        if kwargs:
            with QuietLoggingContext(level=logging.INFO):
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                        self.logger.debug(f"Updated {key}={value} for user {user.username}")
                    else:
                        self.logger.warning(f"Attribute {key} does not exist on User model")

        return user

    @le.log
    def delete_user(self, user_id: int) -> bool:
        """Delete a user with enhanced logging for this critical operation."""
        # Use VisualLoggingContext to make deletion logs stand out
        with VisualLoggingContext():
            self.logger.warning(f"=== Attempting to delete user {user_id} ===")

            if user_id not in self.users:
                self.logger.error(f"❌ User with ID {user_id} not found")
                return False

            user = self.users[user_id]
            # Use TemporaryFileHandlerContext to ensure deletion is logged to audit file
            with TemporaryFileHandlerContext("user_deletions.log", level=logging.INFO):
                self.logger.info(
                    f"Deleting user: {user.username} (ID: {user_id}, Email: {user.email})"
                )
                del self.users[user_id]
                self.logger.warning(f"✓ User {user_id} deleted successfully")

            return True


# ---------------------
# Django View Example
# ---------------------


class RequestData:
    """Mock Django request data."""

    def __init__(self, method: str, path: str, user_id: Optional[int] = None):
        self.method = method
        self.path = path
        self.user_id = user_id


class ResponseData:
    """Mock Django response data."""

    def __init__(self, status_code: int = 200, data: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.data = data or {}


@le.log
def user_list_view(request: RequestData) -> ResponseData:
    """Example Django view with context managers for better API endpoint logging."""
    logger = le.get_logger("django_app.views.user")

    # Use VerboseLoggingContext for API request details
    with VerboseLoggingContext():
        logger.info(f"Processing {request.method} request to {request.path}")

        # Simulate database query timing with context manager
        with LoggingContext(log_entry_exit=True):
            logger.debug("Fetching users from database")
            # Simulate database query
            time.sleep(0.1)

            # Get users (in a real app, this would be a database query)
            user_manager = UserManager()
            users = list(user_manager.users.values())

            logger.debug(f"Found {len(users)} users")

        # Return response
        response = ResponseData(
            status_code=200,
            data={"users": [{"id": u.id, "username": u.username, "email": u.email} for u in users]},
        )

        logger.info(f"Returning response with status {response.status_code}")
        return response


@le.log
def user_detail_view(request: RequestData) -> ResponseData:
    """Example Django view for user details with context managers for error handling."""
    logger = le.get_logger("django_app.views.user")

    logger.info(f"Processing {request.method} request to {request.path}")

    # Check if user_id is provided
    if not request.user_id:
        logger.warning("No user_id provided in request")
        return ResponseData(status_code=400, data={"error": "Missing user_id"})

    user_manager = UserManager()

    try:
        # Normal GET operation with standard logging
        if request.method == "GET":
            user = user_manager.get_user(request.user_id)

            # User not found - use enhanced logging context for error cases
            if not user:
                with VisualLoggingContext():
                    logger.warning(f"❌ User with ID {request.user_id} not found")
                return ResponseData(status_code=404, data={"error": "User not found"})

            # User found - quiet logging for successful routine operations
            with QuietLoggingContext():
                logger.info(f"Retrieved user {user.username}")

            return ResponseData(
                status_code=200,
                data={"id": user.id, "username": user.username, "email": user.email},
            )

        # DELETE operation with enhanced logging due to data deletion
        elif request.method == "DELETE":
            # Use TemporaryFileHandlerContext for audit logging
            with TemporaryFileHandlerContext("user_deletion_audit.log"):
                logger.warning(f"DELETE operation requested for user {request.user_id}")

                success = user_manager.delete_user(request.user_id)

                if not success:
                    return ResponseData(status_code=404, data={"error": "User not found"})

                return ResponseData(status_code=204)

        # Unsupported method
        else:
            logger.warning(f"Unsupported method: {request.method}")
            return ResponseData(status_code=405, data={"error": "Method not allowed"})

    except Exception as e:
        # Use VerboseLoggingContext for detailed error logging
        with VerboseLoggingContext(level=logging.ERROR):
            logger.exception(f"Error processing user detail request: {str(e)}")
        return ResponseData(status_code=500, data={"error": "Internal server error"})


# ---------------------
# Django Middleware Example
# ---------------------


class LoggingMiddleware:
    """Example Django middleware with context managers for request processing."""

    def __init__(self):
        self.logger = le.get_logger("django_app.middleware")

    def process_request(self, request: RequestData):
        """Process a request with appropriate logging contexts."""
        # Get request start time
        request.start_time = time.time()

        # Use VisualLoggingContext for request logging to make it stand out
        with VisualLoggingContext():
            self.logger.info(f"→ {request.method} request to {request.path}")

    def process_response(self, request: RequestData, response: ResponseData):
        """Process a response with context-based logging based on status code."""
        # Calculate request duration
        duration = time.time() - getattr(request, "start_time", time.time())

        # Set context based on response status
        if response.status_code >= 500:
            # Error responses get verbose logging
            with VerboseLoggingContext(level=logging.ERROR):
                self.logger.error(
                    f"← Response {response.status_code} for {request.path} ({duration:.3f}s)"
                )
        elif response.status_code >= 400:
            # Warning for client errors
            with LoggingContext(level=logging.WARNING):
                self.logger.warning(
                    f"← Response {response.status_code} for {request.path} ({duration:.3f}s)"
                )
        else:
            # Success responses get quieter logging
            with QuietLoggingContext():
                self.logger.info(
                    f"← Response {response.status_code} for {request.path} ({duration:.3f}s)"
                )

        return response


# ---------------------
# Demo Application
# ---------------------


def simulate_django_requests():
    """Simulate Django request handling with different scenarios."""
    logger.info("Starting Django application simulation")

    # Create middleware
    middleware = LoggingMiddleware()

    # Create user manager
    user_manager = UserManager()

    # Create a few test requests
    requests = [
        RequestData("GET", "/api/users/"),
        RequestData("GET", "/api/users/1", user_id=1),
        RequestData("GET", "/api/users/999", user_id=999),
        RequestData("DELETE", "/api/users/2", user_id=2),
        RequestData("POST", "/api/users/", user_id=None),
    ]

    # Simulate the Django request/response cycle
    for request in requests:
        # Pre-process request
        middleware.process_request(request)

        # Process view
        if request.path == "/api/users/" and request.method == "GET":
            response = user_list_view(request)
        elif request.path.startswith("/api/users/") and request.user_id:
            response = user_detail_view(request)
        else:
            # Simulate invalid endpoint
            response = ResponseData(status_code=404, data={"error": "Not found"})

        # Post-process response
        middleware.process_response(request, response)

    # Demonstrate user creation with context managers
    with LoggingContext(logger_name="django_app.demo", log_arguments=True):
        logger.info("Demonstrating user creation")

        try:
            # Create new user
            new_user = user_manager.create_user("newuser", "newuser@example.com")
            logger.info(f"Created user: {new_user.username}")

            # Update user with different context managers for different fields
            user_manager.update_user(new_user.id, email="updated@example.com")
            user_manager.update_user(new_user.id, is_active=False)

            # Try to create duplicate user to trigger error
            try:
                user_manager.create_user("newuser", "another@example.com")
            except ValueError as e:
                logger.warning(f"Expected error: {str(e)}")

        except Exception as e:
            logger.exception(f"Error in user operations: {str(e)}")

    logger.info("Django application simulation completed")


if __name__ == "__main__":
    simulate_django_requests()
