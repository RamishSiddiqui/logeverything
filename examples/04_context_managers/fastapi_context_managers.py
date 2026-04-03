#!/usr/bin/env python3
"""
FastAPI Integration with Context Managers for LogEverything.

This example demonstrates how to integrate LogEverything's context managers with FastAPI
for enhanced logging capabilities in specific API endpoints, middleware, and error handlers.

Key features demonstrated:
1. Setting up LogEverything for FastAPI applications
2. Middleware with LoggingContext for request tracking
3. Using VerboseLoggingContext for detailed debugging of complex endpoints
4. Using TemporaryHandlerContext for critical operations (payments, user creation)
5. Using QuietLoggingContext to reduce noise from health checks and static assets
6. Using VisualLoggingContext in development mode for better debugging

Requirements:
- logeverything
- fastapi (mock implementation is provided for demo purposes)

Run with:
    python fastapi_context_managers.py
"""

import json
import sys
import time
import uuid
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

# Since we want to run this example without requiring FastAPI installation,
# we'll create a minimal mock implementation for demonstration


class MockRequest:
    """Mock FastAPI request object."""

    def __init__(self, path: str, method: str, json_data: Optional[Dict[str, Any]] = None):
        self.url = MockURL(path)
        self.method = method
        self.headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
        self.client = MockClient()
        self.json_data = json_data or {}

    async def json(self):
        return self.json_data


class MockURL:
    """Mock FastAPI URL object."""

    def __init__(self, path: str):
        self.path = path


class MockClient:
    """Mock FastAPI client object."""

    def __init__(self):
        self.host = "localhost"
        self.port = 8000


class MockResponse:
    """Mock FastAPI response object."""

    def __init__(self, content: Any, status_code: int = 200):
        self.body = content if isinstance(content, bytes) else json.dumps(content).encode()
        self.status_code = status_code
        self.headers = {"Content-Type": "application/json"}


# Mock FastAPI module for demonstration
class MockFastAPI:
    """Mock FastAPI class."""

    def __init__(self):
        self.routes = {}
        self.middleware = []
        self.exception_handlers = {}
        self.debug = True

    def get(self, path: str):
        def decorator(func):
            self.routes[("GET", path)] = func
            return func

        return decorator

    def post(self, path: str):
        def decorator(func):
            self.routes[("POST", path)] = func
            return func

        return decorator

    def middleware(self, middleware_type: str):
        def decorator(func):
            self.middleware.append(func)
            return func

        return decorator

    def exception_handler(self, exc_type: type):
        def decorator(func):
            self.exception_handlers[exc_type] = func
            return func

        return decorator

    async def simulate_request(
        self, path: str, method: str = "GET", json_data: Optional[Dict[str, Any]] = None
    ):
        """Simulate a request for demonstration purposes."""
        request = MockRequest(path, method, json_data)

        # Apply middleware
        for middleware_func in self.middleware:
            # In a real app, middleware would be properly chained
            request = await middleware_func(request)

        # Find and call the route handler
        route_key = (method, path)
        if route_key in self.routes:
            try:
                handler = self.routes[route_key]
                result = await handler(request) if method == "POST" else await handler()
                return result
            except Exception as e:
                # Find exception handler
                handler = self.exception_handlers.get(type(e))
                if handler:
                    return await handler(request, e)
                raise
        return MockResponse({"detail": "Not Found"}, 404)


# Create a mock FastAPI application
app = MockFastAPI()


# Set up logging
def setup_fastapi_logging():
    """Configure LogEverything for FastAPI applications."""
    # Setup with API profile which works well for FastAPI
    logger = setup_logging(
        profile="api",
        level="INFO",
        # Enable visual formatting for better readability
        visual_mode=True,
        use_symbols=True,
        use_indent=True,
        # Enable async mode for FastAPI's async model
        async_mode=True,
        # Enable request ID tracking
        include_context_id=True,
    )

    # Configure external loggers
    configure_external_logger("fastapi", level="INFO")
    configure_external_logger("uvicorn", level="INFO")

    return logger


# Get the logger
logger = setup_fastapi_logging()


# Request ID middleware to track requests
@app.middleware("http")
async def request_middleware(request):
    """Add request ID and log the request details."""
    # Generate a request ID
    request_id = str(uuid.uuid4())

    # Use LoggingContext to add request ID to all logs within this request
    with LoggingContext(request_id=request_id):
        logger.info(f"Request: {request.method} {request.url.path}")
        logger.debug(f"Headers: {request.headers}")

        # Add more logging for API endpoints
        if request.url.path.startswith("/api/"):
            try:
                body = await request.json()
                if body:
                    # Use .debug() so sensitive info isn't logged in production
                    logger.debug(f"Request body: {body}")
            except Exception:
                logger.debug("No JSON body or failed to parse")

    return request


# Error handler with enhanced logging
@app.exception_handler(Exception)
async def exception_handler(request, exc):
    """Handle exceptions with detailed logging."""
    # Use TemporaryHandlerContext to ensure error is logged to a special file
    with TemporaryHandlerContext(FileHandler(filename="fastapi_errors.log")):
        logger.error(
            f"Error handling {request.method} {request.url.path}: {str(exc)}", exc_info=True
        )

    # Return a proper error response
    return MockResponse({"detail": "An error occurred processing your request"}, 500)


# Define some example routes


@app.get("/")
@log_function
async def root():
    """Simple index route."""
    logger.info("Processing index request")
    return MockResponse({"message": "Welcome to the FastAPI LogEverything demo"})


@app.get("/api/items")
@log_function
async def get_items():
    """API endpoint with VerboseLoggingContext for detailed logging."""
    # Use VerboseLoggingContext for detailed logging during complex operations
    with VerboseLoggingContext():
        logger.info("Getting all items with verbose logging")
        logger.debug("Retrieving items from database")

        # Simulate database query
        time.sleep(0.2)

        items = [
            {"id": 1, "name": "Item 1", "price": 19.99},
            {"id": 2, "name": "Item 2", "price": 29.99},
            {"id": 3, "name": "Item 3", "price": 39.99},
        ]

        logger.debug(f"Found {len(items)} items")
        return MockResponse({"items": items})


@app.post("/api/users")
@log_function
async def create_user(request: MockRequest):
    """User creation endpoint with TemporaryHandlerContext for auditing."""
    # For user creation, we want to ensure detailed logging for audit purposes
    with TemporaryHandlerContext(JSONHandler(filename="user_creation.json")):
        logger.info("Processing user creation request")

        # Get user data from request
        user_data = await request.json()
        logger.info(f"Creating user with email: {user_data.get('email', 'unknown')}")

        # Simulate user creation process
        logger.debug("Validating user data")
        time.sleep(0.1)

        logger.debug("Creating user in database")
        time.sleep(0.2)

        # Create a mock user with ID
        new_user = {
            "id": 123,
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "created_at": "2025-06-13T12:34:56Z",
        }

        logger.info(f"User created successfully: ID {new_user['id']}")
        return MockResponse({"user": new_user}, 201)


@app.get("/health")
@log_function
async def health_check():
    """Health check endpoint with QuietLoggingContext to reduce noise."""
    # Use QuietLoggingContext to minimize logging for frequent health checks
    with QuietLoggingContext():
        logger.debug("Health check requested")

        # Simulate health checks
        status = {
            "status": "healthy",
            "version": "1.0.0",
            "uptime": "12h 34m",
        }

        return MockResponse(status)


@app.get("/debug")
@log_function
async def debug_info():
    """Debug endpoint with VisualLoggingContext for enhanced output."""
    # Only enhance visuals in debug mode
    if app.debug:
        with VisualLoggingContext(use_symbols=True, use_indent=True, color_theme="bold"):
            logger.info("Generating debug information with enhanced visual logging")

            # Collect system information
            logger.debug("Collecting system information")
            time.sleep(0.1)

            # Collect application status
            logger.debug("Collecting application status")
            time.sleep(0.1)

            # Collect metrics
            logger.debug("Collecting performance metrics")
            time.sleep(0.1)

            debug_data = {
                "app": {
                    "routes": len(app.routes),
                    "middleware": len(app.middleware),
                },
                "system": {
                    "python": sys.version,
                    "platform": sys.platform,
                },
            }

            logger.info("Debug information collection complete")
            return MockResponse(debug_data)
    else:
        logger.warning("Debug endpoint accessed while not in debug mode")
        return MockResponse({"error": "Debug mode not enabled"}, 403)


@app.post("/api/payments")
@log_function
async def process_payment(request: MockRequest):
    """Payment processing with multiple context managers for enhanced logging."""
    # For payment processing, we want both detailed logs and a dedicated file
    # Combine context managers for complex requirements

    # Get payment data
    payment_data = await request.json()

    # Start with a temporary handler for financial transactions
    with TemporaryHandlerContext(JSONHandler(filename="payments.json")):
        # Add verbose logging for payment processing
        with VerboseLoggingContext():
            logger.info("Processing payment request")
            logger.debug(f"Payment amount: {payment_data.get('amount')}")
            logger.debug(f"Payment method: {payment_data.get('method')}")

            # Simulate payment processing steps
            steps = [
                "validating payment details",
                "checking account balance",
                "processing transaction",
                "generating receipt",
                "sending confirmation",
            ]

            for step in steps:
                logger.debug(f"Payment step: {step}")
                time.sleep(0.1)

            # Create mock payment result
            payment_result = {
                "id": str(uuid.uuid4()),
                "status": "completed",
                "amount": payment_data.get("amount"),
                "transaction_date": "2025-06-13T12:34:56Z",
            }

            logger.info(f"Payment processed successfully. ID: {payment_result['id']}")
            return MockResponse({"payment": payment_result})


async def main():
    """Run a demonstration of the FastAPI integration with context managers."""
    logger.info("=" * 60)
    logger.info("FastAPI Integration Example with Context Managers")
    logger.info("=" * 60)

    # Test example endpoints
    endpoints = [
        ("/", "GET", None),
        ("/api/items", "GET", None),
        ("/api/users", "POST", {"name": "John Doe", "email": "john@example.com"}),
        ("/health", "GET", None),
        ("/debug", "GET", None),
        ("/api/payments", "POST", {"amount": 99.99, "method": "credit_card"}),
        ("/nonexistent", "GET", None),
    ]

    for path, method, data in endpoints:
        logger.info(f"\nTesting endpoint: {method} {path}")
        try:
            response = await app.simulate_request(path, method, data)
            logger.info(f"Response status: {response.status_code}")
        except Exception as e:
            logger.error(f"Error testing endpoint {path}: {e}")

    # List the generated log files
    logger.info("\nFastAPI integration with context managers completed")
    logger.info(
        "Check for additional log files: fastapi_errors.log, user_creation.json, payments.json"
    )
    print("\nFastAPI integration with context managers example completed!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
