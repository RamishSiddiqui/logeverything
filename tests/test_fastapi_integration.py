"""
FastAPI and Uvicorn integration tests for LogEverything.

This module tests the integration of LogEverything with FastAPI and Uvicorn,
focusing on real-world usage patterns in a web application environment.
"""

import io

# Removed logging import
import os
import sys
import unittest
from unittest.mock import patch

import pytest

# Add the parent directory to the path to make imports work when running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything import configure_external_logger
from logeverything.core import get_logger
from logeverything.handlers import ConsoleHandler, PrettyFormatter


# Skip tests if libraries are not available
def check_library(library_name):
    """Check if a library is available."""
    try:
        __import__(library_name)
        return False  # Don't skip
    except ImportError:
        return True  # Skip


class TestFastAPIUvicornIntegration(unittest.TestCase):
    """Test detailed integration with FastAPI and Uvicorn."""

    @pytest.mark.skipif(
        check_library("fastapi") or check_library("uvicorn"),
        reason="FastAPI or Uvicorn not installed",
    )
    def setUp(self):
        """Set up test fixtures."""

        # Save original state of loggers
        self.logger_names = ["fastapi", "uvicorn", "uvicorn.access", "uvicorn.error"]
        self.original_states = {}

        for name in self.logger_names:
            logger = get_logger(name)
            self.original_states[name] = {
                "handlers": list(logger.handlers),
                "level": logger.level,
                "propagate": logger.propagate,
            }

        # Set up output capture
        self.log_buffer = io.StringIO()
        self.handler = ConsoleHandler(self.log_buffer)
        self.handler.setFormatter(
            PrettyFormatter(
                "%(name)s - %(levelname)s - %(message)s",
                use_colors=False,
                use_symbols=False,
            )
        )

    @pytest.mark.skipif(
        check_library("fastapi") or check_library("uvicorn"),
        reason="FastAPI or Uvicorn not installed",
    )
    def tearDown(self):
        """Clean up after each test."""
        # Restore loggers to original state
        for name, state in self.original_states.items():
            logger = get_logger(name)
            logger.handlers = state["handlers"]
            logger.setLevel(state["level"])
            logger.propagate = state["propagate"]

    @pytest.mark.skipif(
        check_library("fastapi") or check_library("uvicorn"),
        reason="FastAPI or Uvicorn not installed",
    )
    def test_fastapi_app_logging(self):
        """Test logging from a FastAPI application."""
        import fastapi

        # Configure FastAPI logger
        fastapi_logger = configure_external_logger(
            "fastapi", level="DEBUG", use_pretty_formatter=False, propagate=False
        )

        # Add our test handler
        fastapi_logger.addHandler(self.handler)

        # Create a FastAPI app
        app = fastapi.FastAPI(title="LogEverything Test App")

        # Add a route that generates logs
        @app.get("/test")
        async def test_route():
            fastapi_logger.debug("Debug log from route handler")
            fastapi_logger.info("Processing request to /test")
            return {"message": "Test successful"}

        # Trigger logging without actually running the server
        fastapi_logger.info("FastAPI app created with title 'LogEverything Test App'")

        # Check logs
        log_content = self.log_buffer.getvalue()
        self.assertIn("FastAPI app created with title", log_content)
        self.assertIn("fastapi", log_content)
        self.assertIn("INFO", log_content)

    @pytest.mark.skipif(
        check_library("fastapi") or check_library("uvicorn"),
        reason="FastAPI or Uvicorn not installed",
    )
    def test_uvicorn_logging_configuration(self):
        """Test configuring Uvicorn's loggers."""

        # Configure all Uvicorn loggers with propagation disabled
        configured_loggers = []
        for name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
            logger = configure_external_logger(
                name, level="INFO", use_pretty_formatter=False, propagate=False
            )
            # Clear existing handlers and add only our test handler
            logger.handlers.clear()
            logger.addHandler(self.handler)
            configured_loggers.append(logger)

        # Manually trigger logs using the configured loggers directly
        configured_loggers[0].info("Main Uvicorn log")  # uvicorn
        configured_loggers[1].info("Access log entry")  # uvicorn.access
        configured_loggers[2].warning("Error log warning")  # uvicorn.error

        # Check logs
        log_content = self.log_buffer.getvalue()
        # Debug: print actual log content for troubleshooting
        print(f"Log buffer content: '{log_content}'")

        # Look for the expected content
        self.assertIn("INFO", log_content)
        self.assertIn("Main Uvicorn log", log_content)
        self.assertIn("Access log entry", log_content)
        self.assertIn("WARNING", log_content)
        self.assertIn("Error log warning", log_content)

    @pytest.mark.skipif(
        check_library("fastapi") or check_library("uvicorn"),
        reason="FastAPI or Uvicorn not installed",
    )
    def test_uvicorn_server_integration(self):
        """Test integration with Uvicorn server."""
        import fastapi
        import uvicorn

        # Configure all relevant loggers and capture their output properly
        configured_loggers = {}
        for name in self.logger_names:
            logger = configure_external_logger(
                name, level="DEBUG", use_pretty_formatter=False, propagate=False
            )
            # Clear existing handlers and add only our test handler
            logger.handlers.clear()
            logger.addHandler(self.handler)
            configured_loggers[name] = logger

        # Create a FastAPI app
        app = fastapi.FastAPI()

        # Mock the run function to avoid actually starting a server
        original_run = uvicorn.run
        try:
            # Replace with our mock
            def mock_run(app, **kwargs):
                configured_loggers["uvicorn"].info(f"Mock server starting with {kwargs}")
                configured_loggers["uvicorn.access"].info("Mock server access log")
                configured_loggers["uvicorn.error"].info("Mock server error log")
                return True

            uvicorn.run = mock_run

            # Attempt to run the server (this will actually call our mock)
            result = uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")
            self.assertTrue(result)  # Our mock returns True

            # Force additional log messages
            for name in self.logger_names:
                configured_loggers[name].debug(
                    f"Additional debug message from {name}"
                )  # Check logs
            log_content = self.log_buffer.getvalue()
            self.assertIn("Mock server starting with", log_content)
            self.assertIn("Mock server access log", log_content)
            self.assertIn("Mock server error log", log_content)
            self.assertIn("Additional debug message", log_content)

        finally:
            # Restore original run function
            uvicorn.run = original_run


class TestFastAPIIntegrationRealWorld(unittest.TestCase):
    """Test FastAPI integration with more realistic scenarios."""

    @pytest.mark.skipif(check_library("fastapi"), reason="FastAPI not installed")
    def setUp(self):
        """Set up test fixtures."""

        # Save original state
        self.fastapi_logger = get_logger("fastapi")
        self.original_handlers = list(self.fastapi_logger.handlers)
        self.original_level = self.fastapi_logger.level
        self.original_propagate = self.fastapi_logger.propagate

        # Set up output capture
        self.log_buffer = io.StringIO()
        self.handler = ConsoleHandler(self.log_buffer)
        self.handler.setFormatter(
            PrettyFormatter(
                "%(name)s - %(levelname)s - %(message)s",
                use_colors=False,
                use_symbols=False,
            )
        )

    @pytest.mark.skipif(check_library("fastapi"), reason="FastAPI not installed")
    def tearDown(self):
        """Clean up after each test."""
        # Restore logger to original state
        self.fastapi_logger.handlers = list(self.original_handlers)
        self.fastapi_logger.setLevel(self.original_level)
        self.fastapi_logger.propagate = self.original_propagate

    @pytest.mark.skipif(check_library("fastapi"), reason="FastAPI not installed")
    def test_fastapi_request_lifecycle_logging(self):
        """Test logging throughout a FastAPI request lifecycle."""
        import fastapi
        from fastapi.testclient import TestClient

        # Configure FastAPI logger and capture output properly
        fastapi_logger = configure_external_logger(
            "fastapi", level="DEBUG", use_pretty_formatter=False, propagate=False
        )
        # Clear existing handlers and add only our test handler
        fastapi_logger.handlers.clear()
        fastapi_logger.addHandler(self.handler)

        # Create a FastAPI app with middleware to log request lifecycle
        app = fastapi.FastAPI()

        @app.middleware("http")
        async def log_requests(request, call_next):
            fastapi_logger.debug(f"Request started: {request.method} {request.url.path}")
            response = await call_next(request)
            fastapi_logger.debug(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}"
            )
            return response

        @app.get("/hello")
        async def hello():
            fastapi_logger.info("Processing hello endpoint")
            return {"message": "Hello World"}

        # Create a test client
        client = TestClient(app)

        # Make a request
        response = client.get("/hello")

        # Check logs
        log_content = self.log_buffer.getvalue()
        self.assertIn("Request started: GET /hello", log_content)
        self.assertIn("Processing hello endpoint", log_content)
        self.assertIn("Request completed: GET /hello - 200", log_content)

    @pytest.mark.skipif(check_library("fastapi"), reason="FastAPI not installed")
    def test_fastapi_exception_handling_logging(self):
        """Test logging during exception handling in FastAPI."""
        import fastapi
        from fastapi.exceptions import RequestValidationError
        from fastapi.testclient import TestClient
        from pydantic import BaseModel

        # Configure FastAPI logger and capture output properly
        fastapi_logger = configure_external_logger(
            "fastapi", level="DEBUG", use_pretty_formatter=False, propagate=False
        )
        # Clear existing handlers and add only our test handler
        fastapi_logger.handlers.clear()
        fastapi_logger.addHandler(self.handler)

        # Create a FastAPI app
        app = fastapi.FastAPI()

        # Define a model for validation
        class Item(BaseModel):
            name: str
            price: float

        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request, exc):
            fastapi_logger.error(f"Validation error: {exc}")
            return fastapi.responses.JSONResponse(
                status_code=422, content={"detail": "Validation failed"}
            )

        @app.post("/items/")
        async def create_item(item: Item):
            fastapi_logger.info(f"Creating item: {item.name}")
            return item

        # Create a test client
        client = TestClient(app)

        # Make a request with invalid data to trigger validation error
        response = client.post("/items/", json={"name": "Test"})  # Missing required field 'price'

        # Check logs - should include error about validation
        log_content = self.log_buffer.getvalue()
        self.assertIn("Validation error", log_content)

    @pytest.mark.skipif(
        check_library("fastapi") or check_library("requests"),
        reason="FastAPI or requests not installed",
    )
    def test_fastapi_with_multiple_loggers(self):
        """Test FastAPI with multiple integrated loggers."""
        import fastapi
        import requests
        from fastapi.testclient import (  # Configure multiple loggers and capture output properly
            TestClient,
        )

        loggers = {}
        for name in ["fastapi", "requests", "urllib3"]:
            logger = configure_external_logger(
                name, level="DEBUG", use_pretty_formatter=False, propagate=False
            )
            # Clear existing handlers and add only our test handler
            logger.handlers.clear()
            logger.addHandler(self.handler)
            loggers[name] = logger

        # Create a FastAPI app that makes a request
        app = fastapi.FastAPI()

        @app.get("/make-request")
        async def make_request():
            loggers["fastapi"].info("About to make an HTTP request")
            # The actual request won't be made in the test client
            # but we're testing the logging interactions
            try:
                response = requests.get("https://example.com")
                return {"status": "success"}
            except Exception as e:
                loggers["fastapi"].error(f"Request failed: {e}")
                return {"status": "error"}

        # Create a test client
        client = TestClient(app)

        # Make a request that triggers both FastAPI and requests logging
        with patch("requests.get") as mock_get:
            # Mock the requests.get call
            mock_response = requests.Response()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            # Make the request
            response = client.get("/make-request")  # Check logs
            log_content = self.log_buffer.getvalue()
            self.assertIn("About to make an HTTP request", log_content)
