"""
Tests for context manager functionality in LogEverything.
"""

from typing import Any

import pytest

from logeverything import (
    DEBUG,
    WARNING,
    LoggingContext,
    QuietLoggingContext,
    TemporaryHandlerContext,
    VerboseLoggingContext,
    VisualLoggingContext,
)
from logeverything import core as core_module
from logeverything.core import _config, get_logger


class TestLogingContext:
    """Tests for the LoggingContext class."""

    def test_basic_context(self) -> None:
        """Test that basic logging context changes settings temporarily."""
        # Setup initial configuration
        original_level = 20
        core_module.configure(level=original_level)

        # Verify initial state
        assert _config["level"] == original_level  # Use context to change settings temporarily
        with LoggingContext(level="DEBUG", log_entry_exit=False):
            # Verify settings changed within context
            assert _config["level"] == DEBUG  # DEBUG constant (10)
            assert _config["log_entry_exit"] is False

        # Verify settings restored after context
        assert _config["level"] == original_level

    def test_logging_context_with_exception(self) -> None:
        """Test that settings are restored even if an exception occurs."""
        # Setup initial configuration
        core_module.configure(level=20, log_arguments=True)

        try:
            with LoggingContext(level=DEBUG, log_arguments=False):
                # Verify settings changed
                assert _config["level"] == DEBUG
                assert _config["log_arguments"] is False

                # Raise an exception
                raise ValueError("Test exception")
        except ValueError:
            # Exception should be propagated
            pass

        # Settings should be restored despite the exception
        assert _config["level"] == 20
        assert _config["log_arguments"] is True

    def test_logging_context_multiple_params(self) -> None:
        """Test context with multiple parameters changed."""
        # Setup initial configuration
        core_module.configure(
            level=20,
            log_entry_exit=True,
            log_arguments=True,
            log_return_values=True,
            beautify=False,
            indent_level=2,
        )

        # Create a context with several changes
        with LoggingContext(
            level=DEBUG,
            log_entry_exit=False,
            log_arguments=False,
            log_return_values=False,
            beautify=True,
            indent_level=4,
        ):
            # Verify all settings changed
            assert _config["level"] == DEBUG
            assert _config["log_entry_exit"] is False
            assert _config["log_arguments"] is False
            assert _config["log_return_values"] is False
            assert _config["beautify"] is True
            assert _config["indent_level"] == 4

        # Verify all settings restored
        assert _config["level"] == 20
        assert _config["log_entry_exit"] is True
        assert _config["log_arguments"] is True
        assert _config["log_return_values"] is True
        assert _config["beautify"] is False
        assert _config["indent_level"] == 2


class TestSpecializedContexts:
    """Tests for specialized context manager subclasses."""

    def test_quiet_logging_context(self) -> None:
        """Test QuietLoggingContext reduces verbosity."""
        # Setup initial configuration with verbose settings
        core_module.configure(
            level=DEBUG,
            log_entry_exit=True,
            log_arguments=True,
            log_return_values=True,
        )

        # Use QuietLoggingContext to reduce verbosity
        with QuietLoggingContext():
            # Should be changed to minimal verbosity settings
            assert _config["level"] == WARNING
            assert _config["log_entry_exit"] is False
            assert _config["log_arguments"] is False
            assert _config["log_return_values"] is False
            assert _config["capture_print"] is False

        # Verify original settings restored
        assert _config["level"] == DEBUG
        assert _config["log_entry_exit"] is True
        assert _config["log_arguments"] is True
        assert _config["log_return_values"] is True

    def test_verbose_logging_context(self) -> None:
        """Test VerboseLoggingContext increases verbosity."""
        # Setup initial configuration with minimal verbosity
        core_module.configure(
            level=WARNING,
            log_entry_exit=False,
            log_arguments=False,
            log_return_values=False,
            capture_print=False,
        )

        # Use VerboseLoggingContext to increase verbosity
        with VerboseLoggingContext():
            # Should be changed to maximum verbosity settings
            assert _config["level"] == DEBUG
            assert _config["log_entry_exit"] is True
            assert _config["log_arguments"] is True
            assert _config["log_return_values"] is True
            assert _config["capture_print"] is True

        # Verify original settings restored
        assert _config["level"] == WARNING
        assert _config["log_entry_exit"] is False
        assert _config["log_arguments"] is False
        assert _config["log_return_values"] is False
        assert _config["capture_print"] is False

    def test_visual_logging_context(self) -> None:
        """Test VisualLoggingContext enables visual enhancements."""
        # Save original settings to restore later
        original_visual_mode = _config.get("visual_mode", False)
        original_color_theme = _config.get("color_theme", "default")

        try:
            # Use VisualLoggingContext to enable visual features
            with VisualLoggingContext(
                visual_mode=True,
                color_theme="bold",
            ):
                # Verify settings changed within context
                assert _config["visual_mode"] is True
                assert _config["color_theme"] == "bold"

            # Verify we can at least restore some settings after exit
            assert _config["visual_mode"] == original_visual_mode
            assert _config["color_theme"] == original_color_theme

        finally:
            # Reset settings to original values to avoid affecting other tests
            _config["visual_mode"] = original_visual_mode
            _config["color_theme"] = original_color_theme


class TestTemporaryHandlerContext:
    """Tests for the TemporaryHandlerContext class."""

    def test_temporary_handler_context(self) -> None:
        """Test that handlers are temporarily changed."""
        # Setup initial configuration with console handler
        original_handlers = ["console"]
        core_module.configure(handlers=original_handlers)

        # Verify initial state
        assert _config["handlers"] == original_handlers

        # Temporarily switch to file and JSON handlers
        temp_handlers = ["file", "json"]
        with TemporaryHandlerContext(temp_handlers):
            # Verify handlers changed within context
            assert _config["handlers"] == temp_handlers

        # Verify handlers restored after context
        assert _config["handlers"] == original_handlers


class TestPracticalUsage:
    """Test practical usage scenarios for context managers."""

    def test_nested_contexts(self) -> None:
        """Test that nested context managers work correctly."""
        # Setup initial configuration
        core_module.configure(level=20, log_entry_exit=True)

        # Outer context
        with LoggingContext(level=DEBUG):
            # Verify outer context applied
            assert _config["level"] == DEBUG
            assert _config["log_entry_exit"] is True  # Unchanged from initial

            # Inner context
            with LoggingContext(log_entry_exit=False):
                # Should apply changes from both contexts
                assert _config["level"] == DEBUG  # From outer
                assert _config["log_entry_exit"] is False  # From inner

            # Back to outer context - inner changes reverted
            assert _config["level"] == DEBUG
            assert _config["log_entry_exit"] is True  # Outside all contexts - all changes reverted
        assert _config["level"] == 20
        assert _config["log_entry_exit"] is True

    def test_actual_log_output(self, caplog: Any) -> None:
        """Test that context actually affects log output."""
        import io
        import logging

        # Create a custom handler to capture logs since our loggers don't propagate
        log_stream = io.StringIO()
        test_handler = logging.StreamHandler(log_stream)
        test_handler.setLevel(logging.DEBUG)

        # Setup logger using LogEverything
        logger = get_logger("test_logger")

        # Add our test handler to capture logs
        logger.addHandler(test_handler)

        try:  # Initial setting: only show INFO and higher
            core_module.configure(level=20)

            # Clear any previous content
            log_stream.seek(0)
            log_stream.truncate(0)

            # This debug message should NOT appear in logs
            logger.debug("This debug message should not appear")
            log_content = log_stream.getvalue()
            assert "This debug message should not appear" not in log_content

            # Clear the stream
            log_stream.seek(0)
            log_stream.truncate(0)

            # Use context to temporarily allow DEBUG logs
            with LoggingContext(level=DEBUG):
                # This debug message SHOULD appear in logs
                logger.debug("This debug message should appear")

            # Verify the debug message was logged during the context
            log_content = log_stream.getvalue()
            assert "This debug message should appear" in log_content

            # Clear the stream
            log_stream.seek(0)
            log_stream.truncate(0)

            # After context, debug messages should be filtered again
            logger.debug("This second debug message should not appear")
            log_content = log_stream.getvalue()
            assert "This second debug message should not appear" not in log_content

        finally:
            # Clean up: remove our test handler
            logger.removeHandler(test_handler)


if __name__ == "__main__":
    pytest.main()
