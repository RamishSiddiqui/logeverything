"""
Tests for the integration with external loggers.

This module tests the ability of LogEverything to integrate with third-party
logging systems efficiently and seamlessly.
"""

import io
import logging

# Add the parent directory to the path to make imports work when running directly
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Removed logging import


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything import DEBUG, ERROR, INFO, WARNING, configure_external_logger
from logeverything.core import get_logger
from logeverything.external import configure_common_loggers, harmonize_logger_levels
from logeverything.handlers import ConsoleHandler, PrettyFormatter


class TestExternalLoggerIntegration(unittest.TestCase):
    """Test integration with external loggers."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset the root logger to default state
        root = get_logger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        root.setLevel("WARNING")  # Default level

        # Create some test loggers that simulate third-party loggers
        self.mock_external_logger = get_logger("mock.external")
        self.mock_external_logger.setLevel("WARNING")
        self.mock_external_logger.handlers = []
        self.mock_external_logger.propagate = True

    def tearDown(self):
        """Clean up after each test."""
        # Reset mock loggers
        for name in ["mock.external", "langchain", "mlflow", "fastapi"]:
            logger = get_logger(name)
            logger.handlers = []
            logger.setLevel("WARNING")
            logger.propagate = True

    def test_configure_external_logger_basic(self):
        """Test basic configuration of an external logger."""  # Setup a capture for logs
        log_output = io.StringIO()
        handler = ConsoleHandler(log_output, use_colors=False)
        handler.setFormatter(
            PrettyFormatter(
                "%(name)s - %(levelname)s - %(message)s", use_colors=False, use_symbols=False
            )
        )

        # Configure the external logger
        external_logger = configure_external_logger(
            logger_name="mock.external",
            level="DEBUG",
            use_pretty_formatter=False,  # Use simple formatter for testing
        )

        # Add our test handler to capture output
        external_logger.addHandler(handler)  # Test that the logger level was set correctly
        self.assertEqual(external_logger.level, DEBUG)  # Test that the logger outputs correctly
        external_logger.debug("Test debug message")
        external_logger.info("Test info message")
        external_logger.warning("Test warning message")

        log_content = log_output.getvalue()
        self.assertIn("mock.external - [  DEBUG   ] - Test debug message", log_content)
        self.assertIn("mock.external - [   INFO   ] - Test info message", log_content)
        self.assertIn("mock.external - [ WARNING  ] - Test warning message", log_content)

    def test_external_logger_with_propagation(self):
        """Test external logger with propagation enabled."""
        # Setup actual root logger to capture logs
        import logging

        root_output = io.StringIO()
        root_handler = ConsoleHandler(root_output, use_colors=False)
        root_handler.setFormatter(
            PrettyFormatter(
                "ROOT: %(name)s - %(levelname)s - %(message)s", use_colors=False, use_symbols=False
            )
        )

        # Get the actual Python logging root logger
        root_logger = logging.getLogger()
        original_level = root_logger.level
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(root_handler)

        try:
            # Configure external logger with propagation
            external_logger = configure_external_logger(
                logger_name="mock.external", level="INFO", propagate=True
            )

            # Add a custom handler to the external logger too
            external_output = io.StringIO()
            external_handler = ConsoleHandler(external_output, use_colors=False)
            external_handler.setFormatter(
                PrettyFormatter(
                    "EXT: %(name)s - %(levelname)s - %(message)s",
                    use_colors=False,
                    use_symbols=False,
                )
            )
            external_logger.addHandler(external_handler)

            # Test logger behavior
            external_logger.info("This should propagate")

            # Check both loggers received the message
            self.assertIn(
                "EXT: mock.external - [   INFO   ] - This should propagate",
                external_output.getvalue(),
            )
            self.assertIn(
                "ROOT: mock.external - [   INFO   ] - This should propagate", root_output.getvalue()
            )
        finally:
            # Clean up root logger
            root_logger.removeHandler(root_handler)
            root_logger.setLevel(original_level)

    def test_harmonize_logger_levels(self):
        """Test harmonizing logging levels across multiple loggers."""
        # Setup multiple loggers with different levels
        loggers = {
            "test.logger1": get_logger("test.logger1"),
            "test.logger2": get_logger("test.logger2"),
            "test.logger3": get_logger("test.logger3"),
        }

        loggers["test.logger1"].setLevel("DEBUG")
        loggers["test.logger2"].setLevel("WARNING")
        loggers["test.logger3"].setLevel("ERROR")

        # Verify initial levels
        self.assertEqual(loggers["test.logger1"].level, DEBUG)
        self.assertEqual(loggers["test.logger2"].level, WARNING)
        self.assertEqual(loggers["test.logger3"].level, ERROR)

        # Apply harmonization
        original_levels = harmonize_logger_levels("INFO")

        # Verify all loggers now have the same level
        for name, logger in loggers.items():
            self.assertEqual(logger.level, INFO, f"Logger {name} should be at INFO level")

        # Verify the original levels were captured correctly
        self.assertEqual(original_levels["logeverything.test.logger1"], DEBUG)
        self.assertEqual(original_levels["logeverything.test.logger2"], WARNING)
        self.assertEqual(original_levels["logeverything.test.logger3"], ERROR)

    def test_configure_common_loggers(self):
        """Test automatic configuration of common loggers."""
        # Setup mock logger dictionary with safer loggers (not mlflow which has circular import issues)
        mock_logger_dict = {
            "langchain": MagicMock(),
            "requests": MagicMock(),
            "urllib3": MagicMock(),
            "some.other.library": MagicMock(),
        }

        with patch("logging.Logger.manager.loggerDict", mock_logger_dict):
            # Mock check_dependency to avoid real imports
            with patch("logeverything.external.external.check_dependency") as mock_check:
                # Make check_dependency return success for the loggers we want to test
                def mock_check_dependency(module_name, package_name=None):
                    if module_name in ["langchain", "requests", "urllib3"]:
                        return True, ""
                    return False, f"Module {module_name} not found"

                mock_check.side_effect = mock_check_dependency

                # Configure common loggers
                with patch(
                    "logeverything.external.external.configure_external_logger"
                ) as mock_configure:
                    configure_common_loggers()

                    # Verify configure_external_logger was called for available loggers
                    # The exact number depends on which common loggers are in the mock dict
                    self.assertGreater(mock_configure.call_count, 0)

                    # Check that it was called with expected arguments for at least one logger
                    found_call = False
                    for call in mock_configure.call_args_list:
                        args, kwargs = call
                        if args[0] in ["langchain", "requests", "urllib3"]:
                            found_call = True
                            self.assertEqual(kwargs.get("level"), None)
                            self.assertEqual(kwargs.get("use_pretty_formatter"), True)
                            self.assertEqual(kwargs.get("propagate"), False)
                            break

                    self.assertTrue(
                        found_call,
                        "Should have called configure_external_logger for at least one logger",
                    )


class TestSetupLoggingWithExternalLoggers(unittest.TestCase):
    """Test setup_logging with external loggers."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset the root logger to default state
        root = get_logger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        root.setLevel("WARNING")  # Default level

        # Create some test loggers that simulate third-party loggers
        self.langchain_logger = get_logger("langchain")
        self.langchain_logger.handlers = []
        self.langchain_logger.setLevel("WARNING")

        self.mlflow_logger = get_logger("mlflow")
        self.mlflow_logger.handlers = []
        self.mlflow_logger.setLevel("WARNING")

    def tearDown(self):
        """Clean up after each test."""
        # Reset mock loggers
        for name in ["langchain", "mlflow"]:
            logger = get_logger(name)
            logger.handlers = []
            logger.setLevel("WARNING")
            logger.propagate = True

    @patch("logeverything.external.configure_common_loggers")
    def test_setup_logging_with_external_integration(self, mock_configure_common):
        """Test core.configure with integrate_external_loggers=True."""
        from logeverything import core as core_mod

        # Set up logging with external integration via core.configure
        core_mod.configure(
            level="INFO",
            handlers=["console"],
            integrate_external_loggers=True,
            external_logger_level="DEBUG",
        )

        # Verify that configure_common_loggers was called
        mock_configure_common.assert_called_once()

    def test_setup_logging_integration_with_external_level(self):
        """Test that external_logger_level is respected."""
        from logeverything import core as core_mod

        # Mock configure_common_loggers to avoid real import issues
        with patch("logeverything.external.configure_common_loggers") as mock_configure:
            # Set up main logger at INFO but external loggers at DEBUG via core.configure
            core_mod.configure(
                level="INFO",
                handlers=["console"],
                integrate_external_loggers=True,
                external_logger_level="DEBUG",
            )

            # Verify that configure_common_loggers was called
            mock_configure.assert_called_once()

            # Verify the external_logger_level was set in config
            from logeverything.external.external import _config

            # The level should be converted to numeric DEBUG (10)
            self.assertEqual(_config.get("external_logger_level"), 10)
        from logeverything.external import configure_external_logger

        configure_external_logger("langchain", level=DEBUG, propagate=False)
        configure_external_logger("mlflow", level=DEBUG, propagate=False)

        # Verify the loggers have been set to DEBUG level as specified
        # Get fresh logger instances after configuration
        # Use logging.getLogger to get the same logger instances that configure_external_logger works with
        langchain_logger = logging.getLogger("langchain")
        mlflow_logger = logging.getLogger("mlflow")

        self.assertEqual(langchain_logger.level, DEBUG)
        self.assertEqual(mlflow_logger.level, DEBUG)

    def test_real_external_logger_integration(self):
        """Test integration with a real logger using actual log messages."""
        # Set up a capture handler on our simulated third-party logger
        external_output = io.StringIO()
        external_handler = ConsoleHandler(external_output, use_colors=False)
        external_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))

        # First, reset the langchain logger completely
        langchain_logger = get_logger("langchain")
        for handler in langchain_logger.handlers[:]:
            langchain_logger.removeHandler(handler)
        langchain_logger.setLevel("WARNING")  # Only show warnings and above initially
        langchain_logger.propagate = False  # Don't propagate to root logger
        langchain_logger.addHandler(external_handler)

        # Verify that debug/info are not logged before integration
        langchain_logger.debug("Debug message before integration")
        langchain_logger.info("Info message before integration")
        langchain_logger.warning("Warning message before integration")

        before_integration = external_output.getvalue()
        self.assertNotIn("DEBUG - Debug message before integration", before_integration)
        self.assertNotIn("INFO - Info message before integration", before_integration)
        self.assertIn("WARNING - Warning message before integration", before_integration)

        # Clear the output buffer for clean testing
        external_output.seek(0)
        external_output.truncate(0)

        # Configure the external logger
        configured_logger = configure_external_logger(
            "langchain",
            level="DEBUG",
            use_pretty_formatter=False,  # Use simple formatter for testing
            propagate=False,
        )

        # Make sure our test handler is still attached after configuration
        if external_handler not in configured_logger.handlers:
            configured_logger.addHandler(external_handler)

        # Now debug messages should be logged
        configured_logger.debug("Debug message after integration")
        configured_logger.info("Info message after integration")
        configured_logger.warning("Warning message after integration")

        after_integration = external_output.getvalue()
        self.assertIn("DEBUG - Debug message after integration", after_integration)
        self.assertIn("INFO - Info message after integration", after_integration)
        self.assertIn("WARNING - Warning message after integration", after_integration)


# Example of testing with a simulated third-party library
class MockLangChain:
    """Mock LangChain library for testing."""

    def __init__(self):
        # Use standard logging.getLogger to simulate a real third-party library
        self.logger = logging.getLogger("langchain")

    def do_something(self, value):
        """Log at different levels based on the value."""
        self.logger.debug(f"Debug processing value: {value}")
        self.logger.info(f"Processing value: {value}")
        if value < 0:
            self.logger.warning(f"Negative value received: {value}")
        if value > 100:
            self.logger.error(f"Value too large: {value}")
        return value * 2


class TestThirdPartyLibraryIntegration(unittest.TestCase):
    """Test integration with a simulated third-party library."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a buffer to capture logs
        self.log_buffer = io.StringIO()
        # Reset langchain logger
        langchain_logger = get_logger("langchain")
        langchain_logger.handlers = []
        langchain_logger.setLevel("WARNING")  # Default level

        # Create our mock library instance
        self.mock_lib = MockLangChain()

    def test_third_party_library_integration(self):
        """Test integration with a third-party library."""
        # Set up a handler to capture logs
        handler = ConsoleHandler(self.log_buffer, use_colors=False)
        handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))

        # Configure the langchain logger through our integration
        langchain_logger = configure_external_logger(
            "langchain", level="DEBUG", use_pretty_formatter=False
        )
        langchain_logger.addHandler(handler)

        # Use the mock library
        self.mock_lib.do_something(10)  # Normal value
        self.mock_lib.do_something(-5)  # Triggers warning
        self.mock_lib.do_something(200)  # Triggers error

        # Check logs
        log_content = self.log_buffer.getvalue()
        self.assertIn("DEBUG - Debug processing value: 10", log_content)
        self.assertIn("INFO - Processing value: 10", log_content)
        self.assertIn("WARNING - Negative value received: -5", log_content)
        self.assertIn("ERROR - Value too large: 200", log_content)


class TestExternalErrorHandling(unittest.TestCase):
    """Test error handling and edge cases in external logger integration."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset logging state
        root = get_logger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        root.setLevel("WARNING")

    def tearDown(self):
        """Clean up after tests."""
        # Reset any modified loggers
        for name in ["test.error", "test.fallback", "test.edge"]:
            logger = get_logger(name)
            logger.handlers = []
            logger.setLevel("WARNING")
            logger.propagate = True

    def test_safe_log_level_with_invalid_string(self):
        """Test _safe_log_level with invalid string values."""
        from logeverything.external import _safe_log_level

        # Test invalid string level
        result = _safe_log_level("INVALID_LEVEL", "ERROR")
        self.assertEqual(result, "ERROR")

        # Test valid string level
        result = _safe_log_level("DEBUG", INFO)
        self.assertEqual(result, DEBUG)  # Test integer level
        result = _safe_log_level("WARNING", INFO)
        self.assertEqual(result, WARNING)

    def test_configure_external_logger_exception_handling(self):
        """Test exception handling in configure_external_logger."""
        # Mock get_logger to raise exception only for the specific logger we're testing
        original_get_logger = get_logger

        def mock_get_logger(name):
            if name == "test.error":
                raise Exception("Simulated logger error")
            return original_get_logger(name)

        with patch("logeverything.external.get_logger", side_effect=mock_get_logger):
            # Should handle the exception and create a fallback logger
            logger = configure_external_logger("test.error")
            self.assertIsNotNone(logger)

    def test_configure_external_logger_handler_setup_failure(self):
        """Test handler setup failure in configure_external_logger."""
        # Create a logger that will cause handler setup to fail
        with patch("logeverything.external.ConsoleHandler") as mock_console_handler:
            mock_console_handler.side_effect = Exception("Handler creation failed")

            # Should handle the exception and add fallback handler
            logger = configure_external_logger(
                "test.fallback", use_pretty_formatter=True, propagate=False
            )

            # Logger should still exist and have a fallback handler
            self.assertIsNotNone(logger)
            self.assertGreater(len(logger.handlers), 0)

    def test_configure_external_logger_invalid_level_string(self):
        """Test configure_external_logger with invalid level string."""
        logger = configure_external_logger("test.invalid_level", level="INVALID")
        # Should default to INFO level when invalid level is provided
        self.assertEqual(logger.level, INFO)

    def test_configure_external_logger_invalid_level_exception(self):
        """Test configure_external_logger with level that causes exception."""
        with patch("logeverything.external.external.getattr") as mock_getattr:
            mock_getattr.side_effect = Exception("Attribute error")

            logger = configure_external_logger("test.level_exception", level="DEBUG")
            # Should handle the exception and default to INFO
            self.assertEqual(logger.level, INFO)

    def test_harmonize_logger_levels_invalid_string(self):
        """Test harmonize_logger_levels with invalid level string."""
        # Test with invalid level string
        harmonize_logger_levels(
            "INVALID_LEVEL"
        )  # Should use INFO as default when invalid level is provided
        self.assertEqual(get_logger().level, INFO)

    def test_harmonize_logger_levels_level_exception(self):
        """Test harmonize_logger_levels when level parsing raises exception."""
        with patch("logeverything.external.external.getattr") as mock_getattr:
            mock_getattr.side_effect = Exception("Level parsing failed")

            # Should handle the exception and use INFO
            harmonize_logger_levels("DEBUG")
            self.assertEqual(get_logger().level, INFO)

    def test_harmonize_logger_levels_logger_setting_error(self):
        """Test harmonize_logger_levels when setting logger level fails."""
        # Create a test logger
        test_logger = get_logger("test.error_logger")

        # Mock setLevel to raise an exception
        with patch.object(test_logger, "setLevel", side_effect=Exception("SetLevel failed")):
            # Should handle the exception and continue
            harmonize_logger_levels("DEBUG")
            # The function should complete without crashing

    def test_harmonize_logger_levels_with_patterns(self):
        """Test harmonize_logger_levels with include/exclude patterns."""
        # Create test loggers
        loggers = {
            "test.include": get_logger("test.include"),
            "test.include.child": get_logger("test.include.child"),
            "test.exclude": get_logger("test.exclude"),
            "other.logger": get_logger("other.logger"),
        }

        # Set different initial levels
        for logger in loggers.values():
            logger.setLevel("ERROR")

        # Test include patterns
        harmonize_logger_levels(
            "DEBUG", include_root=False, include_patterns=["logeverything.test.include.*"]
        )  # Only loggers matching pattern should be changed
        self.assertEqual(loggers["test.include"].level, 10)  # DEBUG = 10
        self.assertEqual(loggers["test.include.child"].level, 10)  # DEBUG = 10
        self.assertEqual(loggers["test.exclude"].level, 40)  # ERROR = 40
        self.assertEqual(loggers["other.logger"].level, 40)  # ERROR = 40

        # Reset levels
        for logger in loggers.values():
            logger.setLevel("ERROR")  # Test exclude patterns
        harmonize_logger_levels(
            "INFO", include_root=False, exclude_patterns=["logeverything.test.exclude"]
        )  # Excluded logger should not be changed
        self.assertEqual(loggers["test.exclude"].level, 40)  # ERROR = 40

    def test_configure_common_loggers_with_additional_loggers(self):
        """Test configure_common_loggers with additional loggers."""
        # Test with additional loggers as strings
        # Mock logger dictionary to include custom loggers
        mock_logger_dict = {
            "custom_logger1": MagicMock(),
            "custom_logger2": MagicMock(),
            "langchain": MagicMock(),  # Include some existing loggers
            "mlflow": MagicMock(),
        }

        with patch("logging.Logger.manager.loggerDict", mock_logger_dict):
            with patch("logeverything.external.external.check_dependency", return_value=(True, "")):
                with patch(
                    "logeverything.external.external.configure_external_logger"
                ) as mock_configure:
                    configure_common_loggers(
                        additional_loggers=["custom_logger1", "custom_logger2"]
                    )

                    # Should have been called for custom loggers
                    mock_configure.assert_any_call(
                        "custom_logger1", level=None, use_pretty_formatter=True, propagate=False
                    )
                    mock_configure.assert_any_call(
                        "custom_logger2", level=None, use_pretty_formatter=True, propagate=False
                    )

    def test_configure_common_loggers_with_tuple_loggers(self):
        """Test configure_common_loggers with additional loggers as tuples."""
        # Mock logger dictionary to include custom logger
        mock_logger_dict = {
            "custom_logger": MagicMock(),
            "langchain": MagicMock(),  # Include some existing loggers
            "mlflow": MagicMock(),
        }

        with patch("logging.Logger.manager.loggerDict", mock_logger_dict):
            with patch("logeverything.external.external.check_dependency", return_value=(True, "")):
                with patch(
                    "logeverything.external.external.configure_external_logger"
                ) as mock_configure:
                    configure_common_loggers(
                        additional_loggers=[("custom_logger", "custom_module", "custom-package")]
                    )

                    # Should have been called for the tuple logger
                    mock_configure.assert_any_call(
                        "custom_logger", level=None, use_pretty_formatter=True, propagate=False
                    )

    def test_configure_common_loggers_error_handling(self):
        """Test configure_common_loggers error handling."""
        with patch("logeverything.external.external.configure_external_logger") as mock_configure:
            # Make configure_external_logger raise an exception
            mock_configure.side_effect = Exception("Configuration failed")

            # Should handle the exception and continue
            result = configure_common_loggers(show_warnings=False)
            # Should return empty list since configuration failed
            self.assertEqual(result, [])

    def test_configure_common_loggers_with_exclusions(self):
        """Test configure_common_loggers with excluded loggers."""
        with patch(
            "logging.Logger.manager.loggerDict",
            {"langchain": {}, "mlflow": {}},
        ):
            with patch("logeverything.external.check_dependency", return_value=(True, "")):
                with patch("logeverything.external.configure_external_logger") as mock_configure:
                    # Exclude langchain
                    configure_common_loggers(exclude_loggers=["langchain"])

                    # Should not have been called for langchain
                    call_args = [call[0][0] for call in mock_configure.call_args_list]
                    self.assertNotIn("langchain", call_args)

    def test_check_dependency_success(self):
        """Test check_dependency with available dependency."""
        from logeverything.external import check_dependency

        # Test with a module that should be available (logging)
        is_available, message = check_dependency("logging")
        self.assertTrue(is_available)
        self.assertEqual(message, "")

    def test_check_dependency_failure(self):
        """Test check_dependency with unavailable dependency."""
        from logeverything.external import check_dependency

        # Test with a module that doesn't exist
        is_available, message = check_dependency("nonexistent_module", "nonexistent-package")
        self.assertFalse(is_available)
        self.assertIn("not installed", message)
        self.assertIn("nonexistent-package", message)

    def test_configure_common_loggers_dependency_warnings(self):
        """Test configure_common_loggers shows dependency warnings."""
        with patch(
            "logeverything.external.external.check_dependency",
            return_value=(False, "Dependency not found"),
        ):
            with patch("logeverything.external.external.get_logger") as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                # Should show warnings for missing dependencies
                configure_common_loggers(show_warnings=True)

                # Should have called get_logger with the module name
                mock_get_logger.assert_called_with("logeverything.external.external")
                # Should have logged the warning
                mock_logger.info.assert_called()
                # Check that the warning message contains the expected text
                call_args = mock_logger.info.call_args[0][0]
                self.assertIn("Optional dependency warning", call_args)
                self.assertIn("Dependency not found", call_args)


if __name__ == "__main__":
    unittest.main()
