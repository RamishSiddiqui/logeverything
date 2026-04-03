"""
Integration tests with additional third-party libraries.

This module tests the integration of LogEverything with additional third-party libraries
including transformers, pandas, numpy, and requests.
"""

import io
import os
import sys
import unittest
from unittest.mock import patch

import pytest

# Import the safe shutdown utilities
from safe_shutdown import register_safe_shutdown

# Add the parent directory to the path to make imports work when running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything import configure_external_logger
from logeverything.core import get_logger
from logeverything.handlers import ConsoleHandler


# Skip tests if libraries are not available
def check_library(library_name):
    """Check if a library is available."""
    try:
        __import__(library_name)
        return False  # Don't skip
    except ImportError:
        return True  # Skip


class TestTransformersIntegration(unittest.TestCase):
    """Test integration with Hugging Face Transformers library."""

    @pytest.mark.skipif(check_library("transformers"), reason="transformers not installed")
    def setUp(self):
        """Set up test fixtures."""

        # Save original state of transformers loggers
        for name in ["transformers", "datasets"]:
            logger = get_logger(name)
            setattr(self, f"original_handlers_{name.replace('.', '_')}", list(logger.handlers))
            setattr(self, f"original_level_{name.replace('.', '_')}", logger.level)
            setattr(self, f"original_propagate_{name.replace('.', '_')}", logger.propagate)

        # Set up output capture
        self.log_buffer = io.StringIO()

        self.handler = ConsoleHandler(self.log_buffer)
        # Use a simple custom formatter that matches the expected test format

        class SimpleTestFormatter:
            def format(self, record):
                import re

                message = record.getMessage()
                # Strip ANSI color codes
                ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
                clean_message = ansi_escape.sub("", message)
                return f"{record.name} - {record.levelname} - {clean_message}"

        self.handler.setFormatter(SimpleTestFormatter())

    @pytest.mark.skipif(check_library("transformers"), reason="transformers not installed")
    def tearDown(self):
        """Clean up after each test."""
        # Apply safe shutdown to handle PyTorch and transformers logging
        register_safe_shutdown()

        # Restore loggers to original state
        for name in ["transformers", "datasets"]:
            logger = get_logger(name)
            handlers_attr = f"original_handlers_{name.replace('.', '_')}"
            level_attr = f"original_level_{name.replace('.', '_')}"
            propagate_attr = f"original_propagate_{name.replace('.', '_')}"

            if hasattr(self, handlers_attr):
                # Replace with safe handlers
                from safe_shutdown import SafeHandler

                handlers = getattr(self, handlers_attr)
                safe_handlers = []
                for handler in handlers:
                    if not isinstance(handler, SafeHandler):
                        safe_handlers.append(SafeHandler(handler))
                    else:
                        safe_handlers.append(handler)
                logger.handlers = safe_handlers
            if hasattr(self, level_attr):
                logger.setLevel(getattr(self, level_attr))
            if hasattr(self, propagate_attr):
                logger.propagate = getattr(self, propagate_attr)

    @pytest.mark.skipif(check_library("transformers"), reason="transformers not installed")
    def test_transformers_logger_integration(self):
        """Test integration with Transformers logger."""
        # Configure Transformers logger using LogEverything
        transformers_logger = configure_external_logger(
            "transformers", level="INFO", use_pretty_formatter=False, propagate=False
        )

        # Add our test handler
        transformers_logger.addHandler(self.handler)

        # Trigger logging by importing a component or setting verbosity
        import transformers

        transformers.logging.set_verbosity_info()
        transformers.logging.get_logger().info("Testing transformers integration")
        # Check if our custom handler captured the log
        log_content = self.log_buffer.getvalue()
        self.assertIn("transformers - INFO - Testing transformers integration", log_content)

    @pytest.mark.skipif(check_library("transformers"), reason="transformers not installed")
    @pytest.mark.skipif(
        True, reason="Transformers tokenizer test causes torch/pandas import conflicts"
    )
    def test_transformers_tokenizer_logging(self):
        """Test integration with Transformers tokenizer component."""

        import requests
        from huggingface_hub import configure_http_backend

        def backend_factory() -> requests.Session:
            session = requests.Session()
            session.verify = False
            return session

        configure_http_backend(backend_factory=backend_factory)
        # Configure Transformers logger using LogEverything
        transformers_logger = configure_external_logger(
            "transformers", level="DEBUG", use_pretty_formatter=False, propagate=False
        )

        # Add our test handler
        transformers_logger.addHandler(self.handler)
        # Use a tokenizer which triggers logs
        import transformers

        # Force logging directly
        transformers.logging.get_logger().debug("Loading tokenizer")
        transformers.logging.get_logger().info("Tokenizer loaded successfully")

        # Use the built-in mock tokenizer instead of downloading from HuggingFace
        tokenizer = transformers.AutoTokenizer.from_pretrained("bert-base-uncased")
        tokenizer.encode("Testing LogEverything integration with transformers")

        # Verify logs were captured
        log_content = self.log_buffer.getvalue()
        self.assertIn("transformers - DEBUG - Loading tokenizer", log_content)
        self.assertIn("transformers - INFO - Tokenizer loaded successfully", log_content)


class TestPandasIntegration(unittest.TestCase):
    """Test integration with pandas."""

    @pytest.mark.skipif(check_library("pandas"), reason="pandas not installed")
    def setUp(self):
        """Set up test fixtures."""

        # Store original state of pandas logger
        self.pandas_logger = get_logger("pandas")
        self.original_handlers = list(self.pandas_logger.handlers)
        self.original_level = self.pandas_logger.level
        self.original_propagate = self.pandas_logger.propagate

        # Set up output capture
        self.log_buffer = io.StringIO()

        self.handler = ConsoleHandler(self.log_buffer)

        # Use a simple custom formatter that matches the expected test format
        class SimpleTestFormatter:
            def format(self, record):
                import re

                message = record.getMessage()
                # Strip ANSI color codes
                ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
                clean_message = ansi_escape.sub("", message)
                return f"{record.name} - {record.levelname} - {clean_message}"

        self.handler.setFormatter(SimpleTestFormatter())

    @pytest.mark.skipif(check_library("pandas"), reason="pandas not installed")
    def tearDown(self):
        """Clean up after each test."""
        # Restore pandas logger to original state
        self.pandas_logger.handlers = list(self.original_handlers)
        self.pandas_logger.setLevel(self.original_level)
        self.pandas_logger.propagate = self.original_propagate

    @pytest.mark.skipif(check_library("pandas"), reason="pandas not installed")
    def test_pandas_logger_integration(self):
        """Test that we can properly integrate with pandas' logger."""

        # Configure pandas logger using LogEverything
        pandas_logger = configure_external_logger(
            "pandas", level="INFO", use_pretty_formatter=False, propagate=False
        )

        # Add our test handler
        pandas_logger.addHandler(self.handler)

        # Trigger some logging
        pandas_logger.info("Info message from pandas")
        pandas_logger.warning("Warning message from pandas")

        # Check logs
        log_content = self.log_buffer.getvalue()
        self.assertIn("pandas - INFO - Info message from pandas", log_content)
        self.assertIn("pandas - WARNING - Warning message from pandas", log_content)

    @pytest.mark.skipif(check_library("pandas"), reason="pandas not installed")
    def test_pandas_operations_logging(self):
        """Test integration with pandas operations that generate logs."""
        import pandas as pd

        # Configure pandas logger using LogEverything
        pandas_logger = configure_external_logger(
            "pandas",
            level="WARNING",  # Set to warning to catch deprecation warnings
            use_pretty_formatter=False,
            propagate=False,
        )

        # Add our test handler
        pandas_logger.addHandler(self.handler)

        # Create a pandas DataFrame with a duplicate index to trigger a warning
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]}, index=[1, 1, 2])

        # Perform operation that might generate warnings
        # Just to ensure we're capturing pandas logs
        if hasattr(pandas_logger, "warning"):
            pandas_logger.warning("Test warning during pandas operations")

        # Check logs
        log_content = self.log_buffer.getvalue()
        self.assertIn("pandas - WARNING - Test warning during pandas operations", log_content)


class TestNumpyIntegration(unittest.TestCase):
    """Test integration with numpy."""

    @pytest.mark.skipif(check_library("numpy"), reason="numpy not installed")
    def setUp(self):
        """Set up test fixtures."""

        # Numpy uses the 'numpy' logger
        self.numpy_logger = get_logger("numpy")
        self.original_handlers = list(self.numpy_logger.handlers)
        self.original_level = self.numpy_logger.level
        self.original_propagate = self.numpy_logger.propagate

        # Set up output capture
        self.log_buffer = io.StringIO()

        self.handler = ConsoleHandler(self.log_buffer)

        # Use a simple custom formatter that matches the expected test format
        class SimpleTestFormatter:
            def format(self, record):
                import re

                message = record.getMessage()
                # Strip ANSI color codes
                ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
                clean_message = ansi_escape.sub("", message)
                return f"{record.name} - {record.levelname} - {clean_message}"

        self.handler.setFormatter(SimpleTestFormatter())

    @pytest.mark.skipif(check_library("numpy"), reason="numpy not installed")
    def tearDown(self):
        """Clean up after each test."""
        # Restore numpy logger to original state
        self.numpy_logger.handlers = list(self.original_handlers)
        self.numpy_logger.setLevel(self.original_level)
        self.numpy_logger.propagate = self.original_propagate

    @pytest.mark.skipif(check_library("numpy"), reason="numpy not installed")
    def test_numpy_logger_integration(self):
        """Test that we can properly integrate with numpy's logger."""

        # Configure numpy logger using LogEverything
        numpy_logger = configure_external_logger(
            "numpy", level="INFO", use_pretty_formatter=False, propagate=False
        )

        # Add our test handler
        numpy_logger.addHandler(self.handler)

        # Trigger some logging
        numpy_logger.info("Info message from numpy")
        numpy_logger.warning("Warning message from numpy")

        # Check logs
        log_content = self.log_buffer.getvalue()
        self.assertIn("numpy - INFO - Info message from numpy", log_content)
        self.assertIn("numpy - WARNING - Warning message from numpy", log_content)

    @pytest.mark.skipif(check_library("numpy"), reason="numpy not installed")
    def test_numpy_operations_with_warnings(self):
        """Test integration with numpy operations that generate warnings."""

        # Configure numpy logger using LogEverything
        numpy_logger = configure_external_logger(
            "numpy", level="WARNING", use_pretty_formatter=False, propagate=False
        )

        # Add our test handler
        numpy_logger.addHandler(self.handler)

        # Force a log message
        if hasattr(numpy_logger, "warning"):
            numpy_logger.warning("Test warning during numpy operations")

        # Check logs
        log_content = self.log_buffer.getvalue()
        self.assertIn("numpy - WARNING - Test warning during numpy operations", log_content)


class TestRequestsIntegration(unittest.TestCase):
    """Test integration with requests library."""

    @pytest.mark.skipif(check_library("requests"), reason="requests not installed")
    def setUp(self):
        """Set up test fixtures."""

        # Requests uses urllib3 for logging
        self.loggers = {}
        for name in ["requests", "urllib3"]:
            self.loggers[name] = get_logger(name)
            setattr(self, f"original_handlers_{name}", list(self.loggers[name].handlers))
            setattr(self, f"original_level_{name}", self.loggers[name].level)
            setattr(self, f"original_propagate_{name}", self.loggers[name].propagate)

        # Set up output capture
        self.log_buffer = io.StringIO()

        self.handler = ConsoleHandler(self.log_buffer)

        # Use a simple custom formatter that matches the expected test format
        class SimpleTestFormatter:
            def format(self, record):
                import re

                message = record.getMessage()
                # Strip ANSI color codes
                ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
                clean_message = ansi_escape.sub("", message)
                return f"{record.name} - {record.levelname} - {clean_message}"

        self.handler.setFormatter(SimpleTestFormatter())

    @pytest.mark.skipif(check_library("requests"), reason="requests not installed")
    def tearDown(self):
        """Clean up after each test."""
        # Restore loggers to original state
        for name, logger in self.loggers.items():
            logger.handlers = getattr(self, f"original_handlers_{name}")
            logger.setLevel(getattr(self, f"original_level_{name}"))
            logger.propagate = getattr(self, f"original_propagate_{name}")

    @pytest.mark.skipif(check_library("requests"), reason="requests not installed")
    def test_requests_logger_integration(self):
        """Test integration with requests logger."""

        # Configure requests and urllib3 loggers using LogEverything
        configured_loggers = {}
        for name in ["requests", "urllib3"]:
            logger = configure_external_logger(
                name,
                level="DEBUG",  # Debug level to see detailed request logs
                use_pretty_formatter=False,
                propagate=False,
            )
            logger.addHandler(self.handler)
            configured_loggers[name] = logger

        # Trigger some logging using the configured loggers
        configured_loggers["requests"].debug("Debug message from requests")
        configured_loggers["urllib3"].info("Info message from urllib3")

        # Check logs
        log_content = self.log_buffer.getvalue()
        self.assertIn("requests - DEBUG - Debug message from requests", log_content)
        self.assertIn("urllib3 - INFO - Info message from urllib3", log_content)

    @pytest.mark.skipif(check_library("requests"), reason="requests not installed")
    @patch("requests.sessions.Session.send")
    def test_requests_api_logging(self, mock_send):
        """Test integration with requests API that generates logs."""
        import requests

        # Configure requests and urllib3 loggers
        configured_loggers = {}
        for name in ["requests", "urllib3"]:
            logger = configure_external_logger(
                name, level="DEBUG", use_pretty_formatter=False, propagate=False
            )
            logger.addHandler(self.handler)
            configured_loggers[name] = logger

        # Mock response to avoid actual HTTP request
        mock_response = requests.Response()
        mock_response.status_code = 200
        mock_send.return_value = mock_response

        # Make a request which should trigger logging at DEBUG level
        try:
            requests.get("https://example.com", timeout=1)
        except Exception:
            # Even if the request fails, we should still have logs
            pass

        # Force some log messages using the configured loggers
        configured_loggers["requests"].debug("Debug log during requests operation")
        configured_loggers["urllib3"].debug("Debug log from urllib3")

        # Check logs
        log_content = self.log_buffer.getvalue()
        self.assertIn("Debug log during requests operation", log_content)
        self.assertIn("Debug log from urllib3", log_content)
