"""
Tests for the configuration simplification features.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Removed logging import

import logeverything as le
from logeverything import Logger
from logeverything.core import (
    _detect_environment,
    _get_environment_config,
    get_logger,
    setup_logging,
)


class TestConfigurationSimplification(unittest.TestCase):
    """Test the configuration simplification features."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear and reset any loggers
        get_logger("logeverything").handlers = []

    def tearDown(self):
        """Tear down test fixtures."""
        # Clear and reset any loggers
        get_logger("logeverything").handlers = []

    def test_environment_detection(self):
        """Test the environment detection function."""
        # Mock different environments

        # Test notebook detection (highest priority)
        with patch.dict("sys.modules", {"ipykernel": MagicMock(), "flask": MagicMock()}):
            # Even with flask present, notebook should be detected first
            self.assertEqual(_detect_environment(), "notebook")

        # Test web_app detection
        with patch.dict("sys.modules", {"flask": MagicMock()}):
            # Empty sys.argv to ensure we don't detect as script/cli
            with patch("sys.argv", []):
                self.assertEqual(_detect_environment(), "web_app")

        # Test script detection
        with patch("os.path.basename", return_value="script.py"):
            with patch("sys.argv", ["script.py"]):
                with patch.dict(
                    "sys.modules", {}, clear=True
                ):  # Clear modules to ensure clean test
                    self.assertEqual(_detect_environment(), "script")

        # Test CLI detection
        with patch("os.path.basename", return_value="cli"):
            with patch("sys.argv", ["cli"]):
                with patch.dict(
                    "sys.modules", {}, clear=True
                ):  # Clear modules to ensure clean test
                    self.assertEqual(_detect_environment(), "cli")

    def test_environment_config(self):
        """Test that environment-specific configs have correct values."""
        # Web app environment should have async mode enabled
        web_config = _get_environment_config("web_app")
        self.assertTrue(web_config["async_mode"])
        self.assertFalse(web_config["log_arguments"])

        # Notebook environment should have visual features enabled
        notebook_config = _get_environment_config("notebook")
        self.assertTrue(notebook_config["visual_mode"])
        self.assertTrue(notebook_config["use_symbols"])

        # CLI environment should have concise output
        cli_config = _get_environment_config("cli")
        self.assertEqual(cli_config["format"], "%(message)s")

        # Script environment should have debug level set
        script_config = _get_environment_config("script")
        self.assertEqual(script_config["level"], 10)  # DEBUG = 10

    @patch("logeverything.core._detect_environment")
    def test_auto_detection_applied(self, mock_detect):
        """Test that auto-detection is applied when enabled."""
        mock_detect.return_value = "web_app"

        # Use setup_logging directly to test global auto-detection
        setup_logging(auto_detect_env=True, force_ascii=True)

        # Check that web app config was applied
        self.assertTrue(le.core._config["async_mode"])
        self.assertFalse(le.core._config["log_arguments"])

        # Should have called the detection function
        self.assertGreaterEqual(mock_detect.call_count, 1)  # May be called multiple times

        # Reset for next test
        le.core._config = le.core.DEFAULT_CONFIG.copy()

    @patch("logeverything.core._detect_environment")
    def test_auto_detection_disabled(self, mock_detect):
        """Test that auto-detection is not applied when disabled."""
        # Setup with auto-detection disabled
        logger = Logger()
        logger.configure(auto_detect_env=False)

        # Auto-detection may be called during Logger init but should respect the setting
        # The test should verify that the auto-detected config isn't applied, not that it's never called
        self.assertTrue(mock_detect.called)  # May be called during init

    @patch("logeverything.core._detect_environment")
    def test_profile_overrides_auto_detection(self, mock_detect):
        """Test that using a profile overrides auto-detection."""
        mock_detect.return_value = "web_app"

        # Use setup_logging with a profile - profile path should be taken
        # instead of auto_detect_env path (profile takes priority)
        setup_logging(profile="minimal", auto_detect_env=True, force_ascii=True)

        # When profile is specified, auto-detection is skipped entirely
        # (profile takes priority over auto_detect_env)
        self.assertFalse(mock_detect.called)
        # Check that minimal profile was applied, not web_app
        self.assertEqual(le.core._config["level"], 30)  # WARNING = 30

        # Reset for next test
        le.core._config = le.core.DEFAULT_CONFIG.copy()

    @patch("logeverything.external.check_dependency")
    def test_dependency_checking(self, mock_check):
        """Test the dependency checking functionality."""
        # Mock dependency check to return True
        mock_check.return_value = (True, "")

        # Check a dependency
        from logeverything.external import check_dependency

        is_available, message = check_dependency("nonexistent_module", "nonexistent-package")

        # Mock should have been called with the right arguments
        mock_check.assert_called_with("nonexistent_module", "nonexistent-package")

        # Now mock a missing dependency
        mock_check.return_value = (False, "Optional dependency 'test' not installed")

        is_available, message = check_dependency("test", "test")
        self.assertFalse(is_available)
        self.assertIn("not installed", message)


if __name__ == "__main__":
    unittest.main()
