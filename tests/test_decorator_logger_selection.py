"""
Comprehensive pytest tests for decorator logger selection functionality.

This module tests the enhanced decorator behavior including:
- Logger discovery and selection
- The 'using' parameter functionality
- Error handling for non-existent loggers
- Automatic temporary logger creation
- Logger registry management
"""

import io
import logging
import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything import Logger
from logeverything.core import (
    _active_loggers,
    find_logger_for_decorator,
    get_active_loggers,
    register_logger,
    unregister_logger,
)
from logeverything.decorators import log, log_class, log_function, log_io


@pytest.mark.usefixtures("complete_logging_isolation")
class TestLoggerRegistryManagement:
    """Test the logger registry system."""

    def setup_method(self):
        """Clear the registry before each test."""
        _active_loggers.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _active_loggers.clear()

    def test_register_logger(self):
        """Test logger registration."""
        logger = Logger("test_logger")
        register_logger("test_logger", logger)

        assert "test_logger" in _active_loggers
        assert _active_loggers["test_logger"] is logger

    def test_unregister_logger(self):
        """Test logger unregistration."""
        logger = Logger("test_logger")
        register_logger("test_logger", logger)

        unregister_logger("test_logger")
        assert "test_logger" not in _active_loggers

    def test_unregister_nonexistent_logger(self):
        """Test unregistering a logger that doesn't exist."""
        # Should not raise an error
        unregister_logger("nonexistent")
        assert "nonexistent" not in _active_loggers

    def test_get_active_loggers(self):
        """Test getting all active loggers."""
        logger1 = Logger("logger1")
        logger2 = Logger("logger2")

        register_logger("logger1", logger1)
        register_logger("logger2", logger2)

        active = get_active_loggers()
        assert len(active) == 2
        assert active["logger1"] is logger1
        assert active["logger2"] is logger2

        # Should return a copy, not the original dict
        active["logger3"] = "test"
        assert "logger3" not in _active_loggers


@pytest.mark.usefixtures("complete_logging_isolation")
class TestLoggerDiscovery:
    """Test the logger discovery logic for decorators."""

    def setup_method(self):
        """Clear the registry before each test."""
        _active_loggers.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _active_loggers.clear()

    def test_find_specific_logger_exists(self):
        """Test finding a specific logger that exists."""
        logger = Logger("target_logger")
        register_logger("target_logger", logger)

        found = find_logger_for_decorator("target_logger")
        assert found is logger

    def test_find_specific_logger_not_exists(self):
        """Test error when specific logger doesn't exist."""
        logger1 = Logger("logger1")
        logger2 = Logger("logger2")
        register_logger("logger1", logger1)
        register_logger("logger2", logger2)

        with pytest.raises(ValueError) as exc_info:
            find_logger_for_decorator("nonexistent")

        error_msg = str(exc_info.value)
        assert "nonexistent" in error_msg
        assert "logger1" in error_msg
        assert "logger2" in error_msg

    def test_auto_select_with_available_loggers(self):
        """Test auto-selection when loggers are available."""
        logger1 = Logger("first_logger")
        logger2 = Logger("second_logger")
        register_logger("first_logger", logger1)
        register_logger("second_logger", logger2)

        # Capture debug log output (messages now go through logging, not stdout)
        import logging

        handler = logging.StreamHandler(io.StringIO())
        handler.setLevel(logging.DEBUG)
        le_logger = logging.getLogger("logeverything")
        le_logger.addHandler(handler)
        le_logger.setLevel(logging.DEBUG)
        try:
            found = find_logger_for_decorator(None)
        finally:
            le_logger.removeHandler(handler)

        # Should return the first logger (implementation dependent)
        assert found in [logger1, logger2]

        # Should log helpful message at DEBUG level
        logged = handler.stream.getvalue()
        assert "Auto-selected logger" in logged
        assert "available:" in logged

    def test_create_temporary_logger_when_none_exist(self):
        """Test temporary logger creation when no loggers exist."""
        # Ensure no loggers exist
        assert len(_active_loggers) == 0

        # Clear all Python logger handlers to force temp logger creation
        import logging

        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers[:]
        root_logger.handlers = []

        # Also clear the logeverything logger so the fallback check doesn't find it
        le_logger = logging.getLogger("logeverything")
        le_original_handlers = le_logger.handlers[:]
        le_original_level = le_logger.level
        le_logger.handlers = []
        le_logger.level = logging.NOTSET

        # Clear other known fallback loggers
        known_fallbacks = ["test_basics", "test"]
        saved_fallbacks = {}
        for fb_name in known_fallbacks:
            fb_logger = logging.getLogger(fb_name)
            saved_fallbacks[fb_name] = (list(fb_logger.handlers), fb_logger.level)
            fb_logger.handlers = []
            fb_logger.level = logging.NOTSET

        try:
            found = find_logger_for_decorator(None)

            # Should create a temporary logger
            assert found is not None
            assert hasattr(found, "_logger")
            assert "decorator_temp" in _active_loggers
        finally:
            # Restore original handlers
            root_logger.handlers = original_handlers
            le_logger.handlers = le_original_handlers
            le_logger.level = le_original_level
            for fb_name, (handlers, level) in saved_fallbacks.items():
                fb_logger = logging.getLogger(fb_name)
                fb_logger.handlers = handlers
                fb_logger.level = level


@pytest.mark.usefixtures("complete_logging_isolation")
class TestDecoratorUsingParameter:
    """Test the 'using' parameter functionality in decorators."""

    def setup_method(self):
        """Set up test environment."""
        _active_loggers.clear()
        self.app_logger = Logger("app")
        self.data_logger = Logger("data")
        self.api_logger = Logger("api")

    def teardown_method(self):
        """Clean up after each test."""
        _active_loggers.clear()

    def test_log_decorator_with_using_parameter(self):
        """Test @log decorator with using parameter."""

        @log(using="data")
        def test_function():
            return "data_result"

        # Function should work without errors
        result = test_function()
        assert result == "data_result"

    def test_log_function_decorator_with_using_parameter(self):
        """Test @log_function decorator with using parameter."""

        @log_function(using="app")
        def test_function():
            return "app_result"

        result = test_function()
        assert result == "app_result"

    def test_log_io_decorator_with_using_parameter(self):
        """Test @log_io decorator with using parameter."""

        @log_io(using="api")
        def test_function():
            return "api_result"

        result = test_function()
        assert result == "api_result"

    def test_log_class_decorator_with_using_parameter(self):
        """Test @log_class decorator with using parameter."""

        @log_class(using="app")
        class TestClass:
            def method(self):
                return "class_result"

        instance = TestClass()
        result = instance.method()
        assert result == "class_result"

    def test_decorator_with_nonexistent_logger(self):
        """Test decorator behavior with non-existent logger."""

        @log(using="nonexistent_logger")
        def test_function():
            return "should_not_work"

        # Error should be raised when function is called, not when decorated
        with pytest.raises(ValueError) as exc_info:
            test_function()

        error_msg = str(exc_info.value)
        assert "nonexistent_logger" in error_msg
        assert "not found" in error_msg


@pytest.mark.usefixtures("complete_logging_isolation")
class TestDecoratorAutoSelection:
    """Test automatic logger selection in decorators."""

    def setup_method(self):
        """Set up test environment."""
        _active_loggers.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _active_loggers.clear()

    def test_decorator_with_no_loggers_creates_temporary(self):
        """Test decorator creates temporary logger when none exist."""
        import logging

        # Clear fallback loggers so temp logger creation is triggered
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers[:]
        root_logger.handlers = []

        le_logger = logging.getLogger("logeverything")
        le_original_handlers = le_logger.handlers[:]
        le_original_level = le_logger.level
        le_logger.handlers = []
        le_logger.level = logging.NOTSET

        known_fallbacks = ["test_basics", "test"]
        saved_fallbacks = {}
        for fb_name in known_fallbacks:
            fb_logger = logging.getLogger(fb_name)
            saved_fallbacks[fb_name] = (list(fb_logger.handlers), fb_logger.level)
            fb_logger.handlers = []
            fb_logger.level = logging.NOTSET

        try:

            @log
            def test_function():
                return "temp_result"

            result = test_function()

            assert result == "temp_result"
            assert "decorator_temp" in _active_loggers
        finally:
            root_logger.handlers = original_handlers
            le_logger.handlers = le_original_handlers
            le_logger.level = le_original_level
            for fb_name, (handlers, level) in saved_fallbacks.items():
                fb_logger = logging.getLogger(fb_name)
                fb_logger.handlers = handlers
                fb_logger.level = level

    def test_decorator_with_available_loggers_shows_guidance(self):
        """Test decorator shows guidance when loggers are available."""
        import logging

        logger = Logger("my_app")

        # Capture debug log output (messages now go through logging, not stdout)
        handler = logging.StreamHandler(io.StringIO())
        handler.setLevel(logging.DEBUG)
        le_logger = logging.getLogger("logeverything")
        le_logger.addHandler(handler)
        le_logger.setLevel(logging.DEBUG)

        try:

            @log
            def test_function():
                return "guided_result"

            result = test_function()
        finally:
            le_logger.removeHandler(handler)

        assert result == "guided_result"

        logged = handler.stream.getvalue()
        assert "Auto-selected logger" in logged
        assert "available:" in logged
        assert "my_app" in logged
        assert "Use @log(using=" in logged

    def test_decorator_with_explicit_logger_no_guidance(self):
        """Test decorator with explicit logger doesn't show guidance."""
        logger = Logger("explicit_logger")

        output = io.StringIO()
        with redirect_stdout(output):

            @log(using="explicit_logger")
            def test_function():
                return "explicit_result"

            result = test_function()

        assert result == "explicit_result"

        printed = output.getvalue()
        # Should not contain guidance messages
        assert "No logger specified" not in printed
        assert "Available loggers:" not in printed


@pytest.mark.usefixtures("complete_logging_isolation")
class TestDecoratorCompatibility:
    """Test backward compatibility and edge cases."""

    def setup_method(self):
        """Set up test environment."""
        _active_loggers.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _active_loggers.clear()

    def test_decorator_without_parameters_still_works(self):
        """Test that decorators work without any parameters."""
        logger = Logger("compat_logger")

        @log
        def simple_function():
            return "simple_result"

        result = simple_function()
        assert result == "simple_result"

    def test_decorator_with_traditional_parameters_still_works(self):
        """Test that traditional decorator parameters still work."""
        logger = Logger("trad_logger")

        @log_function(log_arguments=False, log_return_values=False)
        def traditional_function():
            return "traditional_result"

        result = traditional_function()
        assert result == "traditional_result"

    def test_mixing_using_with_other_parameters(self):
        """Test mixing 'using' parameter with other decorator parameters."""
        logger = Logger("mixed_logger")

        @log_function(using="mixed_logger", log_arguments=False)
        def mixed_function():
            return "mixed_result"

        result = mixed_function()
        assert result == "mixed_result"


@pytest.mark.usefixtures("complete_logging_isolation")
class TestLoggerRegistrationIntegration:
    """Test integration between Logger class and registry."""

    def setup_method(self):
        """Set up test environment."""
        _active_loggers.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _active_loggers.clear()

    def test_logger_auto_registers_on_creation(self):
        """Test that Logger instances auto-register themselves."""
        logger = Logger("auto_register_test")

        # Should be automatically registered
        assert "auto_register_test" in _active_loggers
        assert _active_loggers["auto_register_test"] is logger

    def test_multiple_loggers_auto_register(self):
        """Test that multiple Logger instances all register."""
        logger1 = Logger("logger_one")
        logger2 = Logger("logger_two")
        logger3 = Logger("logger_three")

        assert len(_active_loggers) == 3
        assert _active_loggers["logger_one"] is logger1
        assert _active_loggers["logger_two"] is logger2
        assert _active_loggers["logger_three"] is logger3

    def test_logger_name_collision_handling(self):
        """Test behavior when loggers have the same name."""
        logger1 = Logger("same_name")
        logger2 = Logger("same_name")

        # The second logger should overwrite the first in the registry
        assert _active_loggers["same_name"] is logger2


@pytest.mark.usefixtures("complete_logging_isolation")
class TestDecoratorPerformance:
    """Test performance-related aspects of decorator enhancements."""

    def setup_method(self):
        """Set up test environment."""
        _active_loggers.clear()

    def teardown_method(self):
        """Clean up after each test."""
        _active_loggers.clear()

    def test_logger_discovery_caching(self):
        """Test that logger discovery doesn't cause performance issues."""
        logger = Logger("perf_test")

        @log(using="perf_test")
        def performance_function():
            return "perf_result"

        # Multiple calls should work efficiently
        for _ in range(100):
            result = performance_function()
            assert result == "perf_result"

    def test_temporary_logger_creation_not_repeated(self):
        """Test that temporary logger is created only once."""
        original_count = len(_active_loggers)

        @log
        def temp_function1():
            return "temp1"

        @log
        def temp_function2():
            return "temp2"

        # Call both functions
        result1 = temp_function1()
        result2 = temp_function2()

        assert result1 == "temp1"
        assert result2 == "temp2"

        # Should only create one temporary logger
        assert len(_active_loggers) == original_count + 1
        assert "decorator_temp" in _active_loggers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
