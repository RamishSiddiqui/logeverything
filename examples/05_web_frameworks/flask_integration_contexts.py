#!/usr/bin/env python3
"""
Flask Integration Example with Context Managers for LogEverything.

This example demonstrates how to integrate LogEverything with Flask and use context managers
to enhance logging for specific routes, request contexts, and error handling.

Key features demonstrated:
1. Setting up LogEverything for Flask applications
2. Using VerboseLoggingContext for detailed debugging of specific routes
3. Using QuietLoggingContext for reducing noise from static file requests
4. Using TemporaryHandlerContext for route-specific logging to separate files
5. Using VisualLoggingContext for development environment enhancement
6. Middleware-like logging with request context information

Requirements:
- logeverything
- flask

Run with:
    python flask_integration_contexts.py
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Add the parent directory to the path for imports to work when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from logeverything import (
    LoggingContext,
    QuietLoggingContext,
    TemporaryHandlerContext,
    VerboseLoggingContext,
    VisualLoggingContext,
    configure_external_logger,
    log_function,
    setup_logging,
)
from logeverything.handlers import FileHandler, JSONHandler


# Flask imports (for a real application)
# from flask import Flask, request, jsonify, g, current_app
# For this example, we'll mock Flask to avoid requiring installation
class MockRequest:
    """Mock Flask request object."""

    def __init__(self, path: str, method: str, json_data: Optional[Dict[str, Any]] = None):
        self.path = path
        self.method = method
        self._json = json_data or {}
        self.headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
        self.remote_addr = "127.0.0.1"

    def get_json(self):
        return self._json


class MockResponse:
    """Mock Flask response object."""

    def __init__(self, data: Any, status_code: int = 200):
        self.data = data
        self.status_code = status_code

    def get_data(self):
        return self.data


class MockFlask:
    """Mock Flask application."""

    def __init__(self, name: str):
        self.name = name
        self.routes = {}
        self.request = None
        self.config = {"DEBUG": True, "ENV": "development"}

    def route(self, path: str, methods=None):
        if methods is None:
            methods = ["GET"]

        def decorator(func):
            self.routes[path] = (func, methods)
            return func

        return decorator

    def test_request(
        self, path: str, method: str = "GET", json_data: Optional[Dict[str, Any]] = None
    ):
        """Simulate a request for testing/demo purposes."""
        self.request = MockRequest(path, method, json_data)

        if path in self.routes:
            handler, allowed_methods = self.routes[path]
            if method in allowed_methods:
                return handler()
            else:
                return MockResponse({"error": "Method not allowed"}, 405)
        return MockResponse({"error": "Not found"}, 404)


# Create a mock Flask application
app = MockFlask(__name__)


def setup_flask_logging():
    """Configure LogEverything for the Flask application."""
    # Setup LogEverything with appropriate settings for Flask
    logger = setup_logging(
        profile="api",  # API profile works well for web applications
        level="INFO",
        # Enable visual formatting for better readability
        visual_mode=True,
        use_symbols=True,
        use_indent=True,
        color_theme="bold",
        # Capture print statements from Flask views
        capture_print=True,
    )

    # Configure Flask's loggers to use LogEverything
    configure_external_logger("flask", level="INFO")
    configure_external_logger("werkzeug", level="INFO")

    return logger


# Get the logger
logger = setup_flask_logging()


# Define a request logging middleware
@log_function
def log_request_middleware(request):
    """Log details about the incoming request."""
    logger.info(f"Request: {request.method} {request.path}")
    logger.debug(f"Headers: {request.headers}")

    # For API endpoints, log the request body only in debug mode
    if request.path.startswith("/api/") and app.config["DEBUG"]:
        try:
            body = request.get_json()
            if body:
                logger.debug(f"Request Body: {json.dumps(body)}")
        except Exception as e:
            logger.warning(f"Could not parse request body: {str(e)}")

    # Return so it can be used as a middleware decorator
    return request


# Define example routes
@app.route("/", methods=["GET"])
@log_function
def index():
    """Simple index route."""
    log_request_middleware(app.request)
    logger.info("Processing index route")
    time.sleep(0.1)  # Simulate processing
    return MockResponse({"message": "Welcome to the Flask LogEverything demo"})


@app.route("/api/items", methods=["GET"])
@log_function
def get_items():
    """API route with VerboseLoggingContext for detailed logging."""
    log_request_middleware(app.request)

    # Use VerboseLoggingContext for detailed logging on this API endpoint
    with VerboseLoggingContext():
        logger.info("Processing items request with verbose logging")
        logger.debug("Fetching items from database")

        # Simulate database access
        time.sleep(0.2)

        # Create mock items data
        items = [
            {"id": 1, "name": "Item 1", "price": 19.99},
            {"id": 2, "name": "Item 2", "price": 29.99},
            {"id": 3, "name": "Item 3", "price": 39.99},
        ]

        logger.debug(f"Retrieved {len(items)} items")
        logger.info("Items request processed successfully")

        return MockResponse({"items": items})


@app.route("/api/items", methods=["POST"])
@log_function
def create_item():
    """API route with TemporaryHandlerContext to log to a special file."""
    log_request_middleware(app.request)

    # Use a TemporaryHandlerContext to log this operation to a dedicated file
    # This is useful for critical operations that need their own log trail
    with TemporaryHandlerContext(JSONHandler(filename="item_creation.json")):
        logger.info("Processing item creation request")

        # Get the new item data from the request
        data = app.request.get_json()
        logger.info(f"Creating new item: {data}")

        # Validate the input
        if not data or "name" not in data or "price" not in data:
            logger.error("Invalid item data provided")
            return MockResponse({"error": "Invalid item data"}, 400)

        # Simulate database operation
        time.sleep(0.3)

        # Create a mock item with ID
        new_item = {
            "id": 4,  # In a real app, this would be generated by the database
            "name": data["name"],
            "price": data["price"],
        }

        logger.info(f"Item created successfully with id: {new_item['id']}")
        return MockResponse({"item": new_item, "status": "created"}, 201)


@app.route("/static/styles.css", methods=["GET"])
@log_function
def static_file():
    """Static file route with QuietLoggingContext to reduce log noise."""

    # Use QuietLoggingContext to reduce noise for static file requests
    with QuietLoggingContext():
        log_request_middleware(app.request)
        logger.debug("Serving static file - minimal logging")

        # Simulate file reading
        time.sleep(0.05)

        # Return mock CSS content
        return MockResponse("body { font-family: Arial; }")


@app.route("/debug", methods=["GET"])
@log_function
def debug_route():
    """Debug route with visual enhancements for better debugging experience."""
    log_request_middleware(app.request)

    # Check if we're in debug mode first
    if app.config["DEBUG"]:
        # Use VisualLoggingContext for enhanced visual output in development
        with VisualLoggingContext(use_symbols=True, use_indent=True, color_theme="bold"):
            logger.info("Entering debug mode with enhanced visual logging")

            # Collect debug information
            debug_info = {
                "app_config": app.config,
                "python_version": sys.version,
                "environment": os.environ.get("FLASK_ENV", "development"),
            }

            # Log each section with clear visual separation
            for section, data in debug_info.items():
                logger.debug(f"{section}: {data}")

            # Simulate additional debug operations
            logger.debug("Checking system status...")
            time.sleep(0.2)
            logger.debug("System OK")

            logger.info("Debug information collection complete")

            return MockResponse({"debug_info": debug_info})
    else:
        logger.warning("Debug route accessed in non-debug mode")
        return MockResponse({"error": "Debug mode not enabled"}, 403)


@app.route("/error", methods=["GET"])
@log_function
def error_route():
    """Route that demonstrates error logging with context managers."""
    log_request_middleware(app.request)

    # In production, you might want to capture more information about errors
    try:
        logger.info("Simulating an error condition")
        # Simulate an error
        raise ValueError("This is a simulated error")
    except Exception as e:
        # Use LoggingContext with custom settings for error reporting
        with LoggingContext(level="ERROR", log_exceptions=True):
            logger.error(f"Error occurred: {str(e)}", exc_info=True)
            # In a real application, you might capture additional context
            return MockResponse({"error": "An internal error occurred"}, 500)


def main():
    """Run a demonstration of the Flask integration."""
    logger.info("=" * 60)
    logger.info("Flask Integration Example with Context Managers")
    logger.info("=" * 60)

    # Test the routes with mock requests
    endpoints = [
        ("/", "GET", None),
        ("/api/items", "GET", None),
        ("/api/items", "POST", {"name": "New Item", "price": 49.99}),
        ("/static/styles.css", "GET", None),
        ("/debug", "GET", None),
        ("/error", "GET", None),
        ("/nonexistent", "GET", None),
    ]

    for path, method, data in endpoints:
        logger.info(f"\nTesting endpoint: {method} {path}")
        response = app.test_request(path, method, data)
        logger.info(f"Response status: {response.status_code}")

    logger.info("\nFlask integration example completed")
    logger.info("Check for additional log files: item_creation.json")
    print("\nFlask integration example with context managers completed!")


if __name__ == "__main__":
    main()
