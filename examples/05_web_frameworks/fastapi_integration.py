"""
Example demonstrating FastAPI integration with LogEverything.

This example shows how to integrate LogEverything with FastAPI
for comprehensive request logging and API monitoring.
"""

import os
import sys

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging

# Import FastAPI-specific types for type hinting and mock implementation
from typing import Optional

import logeverything as le


# Mock FastAPI for demonstration purposes
class MockFastAPI:
    def __init__(self):
        self.routes = []
        self.middleware = []

    def get(self, path):
        def decorator(func):
            self.routes.append((path, func))
            return func

        return decorator

    def middleware(self, middleware_type):
        def decorator(func):
            self.middleware.append(func)
            return func

        return decorator


# Create a mock FastAPI app
app = MockFastAPI()


def setup_fastapi_logging():
    """Configure LogEverything for FastAPI applications."""
    # Setup LogEverything with FastAPI-specific settings
    logger = le.setup_logging(
        profile="api",  # The API profile works well with FastAPI
        level=logging.INFO,
        # Enable asynchronous logging which works well with FastAPI's async model
        async_mode=True,
        # Don't log function arguments to avoid logging sensitive request data
        log_arguments=False,
    )

    # Configure uvicorn and FastAPI loggers
    le.configure_external_logger("uvicorn", level=logging.INFO)
    le.configure_external_logger("uvicorn.access", level=logging.INFO, propagate=False)
    le.configure_external_logger("uvicorn.error", level=logging.WARNING)
    le.configure_external_logger("fastapi", level=logging.INFO)

    return logger


# Get application logger
api_logger = le.get_logger("api")


# Example FastAPI request logging middleware
@app.middleware("http")
@le.log
async def logging_middleware(request, call_next):
    """Log request and response details."""
    # Log the incoming request
    api_logger.info(
        f"Request {request.method} {request.url.path}",
        client_ip=request.client.host,
        query_params=str(request.query_params),
    )

    # Process the request (this would call the route handler in a real app)
    response = await call_next(request)

    # Log the response
    api_logger.info(
        f"Response {response.status_code} for {request.method} {request.url.path}",
        status_code=response.status_code,
        processing_time=response.headers.get("X-Process-Time"),
    )

    return response


# Example FastAPI route with LogEverything decorator
@app.get("/users/{user_id}")
@le.log
async def get_user(user_id: int, include_details: Optional[bool] = False):
    """Get a user by ID with optional details."""
    api_logger.info(f"Fetching user with ID {user_id}")

    # Simulate database access
    user = {"id": user_id, "username": f"user_{user_id}", "email": f"user_{user_id}@example.com"}

    if include_details:
        api_logger.debug(f"Including additional details for user {user_id}")
        user["details"] = {"last_login": "2023-06-01T12:00:00Z", "account_type": "premium"}

    api_logger.info(f"Successfully retrieved user {user_id}")
    return user


def main():
    """Demonstrate LogEverything with FastAPI."""
    # Configure logging
    logger = setup_fastapi_logging()

    api_logger.info("Starting FastAPI application demo")

    # In a real application, you'd run the FastAPI app with uvicorn
    # In this example, we'll just simulate some requests

    # Simulate a GET request to /users/42?include_details=true
    api_logger.info("Simulating request to /users/42?include_details=true")

    # Find the route handler
    handler = None
    for path, func in app.routes:
        if path == "/users/{user_id}":
            handler = func
            break

    if handler:
        # Simulate calling the handler
        result = handler(42, True)
        api_logger.info(f"Handler returned: {result}")

    api_logger.info("FastAPI application demo completed")


if __name__ == "__main__":
    main()
