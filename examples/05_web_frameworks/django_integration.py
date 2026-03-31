"""
Example demonstrating Django integration with LogEverything.

This example shows how to integrate LogEverything into a Django project
with minimal configuration.
"""

import os
import sys

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging

import logeverything as le

# In a real Django project, you would put this in settings.py
LOGGING_CONFIG = None  # Disable Django's default logging config


# This would go in your Django settings.py file
def configure_logging():
    """Configure LogEverything for Django."""
    # Setup LogEverything with Django-specific settings
    logger = le.setup_logging(
        profile="api",  # The API profile works well with Django
        level=logging.INFO,
        file_path="django_app.log",
        # Enable asynchronous logging for better performance
        async_mode=True,
        # Capture print statements from Django views
        capture_print=True,
    )

    # Configure Django's loggers to use LogEverything formatting
    le.configure_external_logger("django", level=logging.INFO)
    le.configure_external_logger("django.request", level=logging.WARNING)
    le.configure_external_logger("django.db.backends", level=logging.WARNING)
    le.configure_external_logger("django.template", level=logging.INFO)

    return logger


# Mock Django settings and request for demonstration
class MockDjangoSettings:
    DEBUG = True
    SECRET_KEY = "fake-secret-key"


class MockRequest:
    method = "GET"
    path = "/api/users/"
    GET = {"page": "1", "limit": "10"}
    META = {"REMOTE_ADDR": "127.0.0.1", "HTTP_USER_AGENT": "Example Browser"}
    user = type("User", (), {"id": 123, "username": "test_user", "is_authenticated": True})


def main():
    """Demonstrate LogEverything with Django."""
    # Configure logging
    logger = configure_logging()

    # Get application logger
    app_logger = le.get_logger("myapp.views")
    app_logger.info("Starting Django application demo")

    # Simulate a Django view
    @le.log
    def user_list_view(request):
        """Example Django view function."""
        app_logger.info(f"Processing {request.method} request to {request.path}")

        # Log user information securely (no sensitive data)
        if request.user.is_authenticated:
            app_logger.info(
                "Request from authenticated user",
                user_id=request.user.id,
                username=request.user.username,
            )

        # Simulate database query
        app_logger.debug("Executing database query for users")

        # Simulate processing
        users = [{"id": 1, "name": "User 1"}, {"id": 2, "name": "User 2"}]

        # Log results
        app_logger.info(f"Found {len(users)} users")

        # This would return a Django response
        return {"users": users, "count": len(users)}

    # Call the view
    request = MockRequest()
    response = user_list_view(request)

    app_logger.info("Django application demo completed")


if __name__ == "__main__":
    main()
