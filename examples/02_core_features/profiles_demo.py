"""
Profiles demonstration for LogEverything.

This example shows how to use the predefined configuration profiles
to quickly set up logging with different settings for various environments.

Available profiles:
- development: Detailed, visually enhanced logging for development environments
- production: Minimal logging focused on warnings and errors
- minimal: Very basic logging with minimal overhead
- debug: Maximum verbosity for debugging purposes
- api: Optimized for API and web service logging
- testing: Configuration for test environments
"""

import sys
import time
from pathlib import Path

# Add the parent directory to the path for imports to work when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from logeverything import Logger, get_profile, log_function


def demonstrate_development_profile():
    """Show how to use the development profile."""
    # Set up logging with the development profile
    logger = Logger("development_demo")
    logger.configure(profile="development")

    # Log function with this profile will show detailed, visually enhanced logs
    @log_function(using="development_demo")
    def process_data(items, multiplier=2):
        """Process some items by multiplying them."""
        logger.debug("Starting data processing...")
        result = [item * multiplier for item in items]
        logger.info(f"✓ Processed {len(items)} items successfully")
        return result

    print("\n=== DEVELOPMENT PROFILE ===")
    print("✨ Detailed logs with full context, colors, symbols, and visual enhancements")
    print("📊 Shows: DEBUG level | Arguments | Return values | Symbols | Indentation")
    process_data([1, 2, 3, 4, 5])


def demonstrate_production_profile():
    """Show how to use the production profile."""
    # Set up logging with the production profile - minimal overhead, warnings and above
    logger = Logger("production_demo")
    logger.configure(profile="production")

    @log_function(using="production_demo")
    def process_data(items, multiplier=2):
        """Process some items by multiplying them."""
        logger.debug("This DEBUG message won't appear (level too low)")
        logger.info("This INFO message won't appear (level too low)")
        result = [item * multiplier for item in items]
        logger.warning("⚠️ Production mode: Only warnings and errors are logged")
        return result

    print("\n=== PRODUCTION PROFILE ===")
    print("⚡ Minimal logs - only WARNING and above (no decorators, no args/returns)")
    print("📊 Shows: WARNING+ level | No visual enhancements | No function tracking")
    process_data([1, 2, 3, 4, 5])


def demonstrate_minimal_profile():
    """Show how to use the minimal profile."""
    # Set up logging with the minimal profile - absolute minimum overhead
    logger = Logger("minimal_demo")
    logger.configure(profile="minimal")

    @log_function(using="minimal_demo")
    def process_data(items, multiplier=2):
        """Process some items by multiplying them."""
        logger.debug("This won't appear")
        logger.info("This won't appear")
        result = [item * multiplier for item in items]
        logger.error("❌ Critical error occurred - minimal profile only shows warnings+")
        return result

    print("\n=== MINIMAL PROFILE ===")
    print("🎯 Absolute minimum - WARNING+ level with simplest format")
    print("📊 Shows: WARNING+ level | No timestamps | No logger names | No extras")
    process_data([1, 2, 3, 4, 5])


def demonstrate_debug_profile():
    """Show how to use the debug profile."""
    # Set up logging with the debug profile - maximum verbosity
    logger = Logger("debug_demo")
    logger.configure(profile="debug")

    @log_function(using="debug_demo")
    def process_data(items, multiplier=2):
        """Process some items by multiplying them."""
        logger.debug("🔍 Step 1: Validating input items")
        logger.debug(f"🔍 Step 2: Applying multiplier={multiplier}")
        result = [item * multiplier for item in items]
        logger.debug(f"🔍 Step 3: Computed result with {len(result)} items")
        logger.info("✅ Processing complete")
        return result

    print("\n=== DEBUG PROFILE ===")
    print("🔬 Maximum verbosity with milliseconds, file/line numbers, and deep indentation")
    print("📊 Shows: ALL levels | Verbose format | Args/returns | Symbols | Max details")
    process_data([1, 2, 3, 4, 5])


def demonstrate_api_profile():
    """Show how to use the API/Web profile."""
    # Set up logging with the API profile - optimized for web services
    logger = Logger("api_demo")
    logger.configure(profile="api")

    @log_function(using="api_demo")
    def handle_request(request_id, user_id, action):
        """Simulate handling an API request."""
        logger.info(f"📥 Received {action} request from user {user_id}")
        logger.debug("Validating request parameters...")
        time.sleep(0.1)  # Simulate work
        logger.info(f"📤 Request {request_id} completed successfully")
        return {"success": True, "action": action}

    print("\n=== API/WEB PROFILE ===")
    print("🌐 Optimized for web services - shows request tracking with function arguments")
    print("📊 Shows: INFO+ level | Function args (for request context) | Timestamps")
    handle_request("req-123", "user-456", "get_data")


def demonstrate_testing_profile():
    """Show how to use the testing profile."""
    # Set up logging with the testing profile - for test environments
    logger = Logger("testing_demo")
    logger.configure(profile="testing")

    @log_function(using="testing_demo")
    def test_calculation(a, b):
        """A function being tested."""
        logger.debug("Running test calculation")
        result = a + b
        logger.info(f"Test assertion: {a} + {b} = {result}")
        return result

    print("\n=== TESTING PROFILE ===")
    print("🧪 Optimized for tests - shows function calls with args/returns, no frills")
    print("📊 Shows: DEBUG+ level | Function tracking | Args/returns | Simple format")
    result = test_calculation(5, 7)
    assert result == 12, "Calculation failed"
    logger.info("✅ Test passed!")


def demonstrate_profile_with_overrides():
    """Show how to use a profile with custom overrides."""
    print("\n=== PROFILE WITH OVERRIDES ===")
    print("Profiles can be customized with specific overrides:")

    # Example 1: Development profile with customizations for less verbose output
    logger1 = Logger("override_demo_1")
    logger1.configure(
        profile="development",
        level="WARNING",  # Override the log level
        max_arg_length=100,  # Limit argument display length
        visual_mode=False,  # Disable visual enhancements
    )

    @log_function(using="override_demo_1")
    def complex_operation(data, options=None):
        """A complex operation with multiple parameters."""
        if options is None:
            options = {"validate": True, "transform": True}
        return f"Processed: {data} with {options}"

    print("\n1. Development profile with reduced verbosity:")
    complex_operation("example data", {"validate": True, "retry": 3, "timeout": 30})

    # Example 2: Production profile with enhanced function logging
    logger2 = Logger("override_demo_2")
    logger2.configure(
        profile="production",
        level="INFO",  # Lower from WARNING to INFO
        log_entry_exit=True,  # Enable function entry/exit logging
        log_arguments=True,  # Enable argument logging
    )

    @log_function(using="override_demo_2")
    def complex_operation2(data, options=None):
        """A complex operation with multiple parameters."""
        if options is None:
            options = {"validate": True, "transform": True}
        return f"Processed: {data} with {options}"

    print("\n2. Production profile with enhanced function visibility:")
    complex_operation2("production data", {"mode": "strict"})

    # Example 3: Minimal profile with visual enhancements
    logger3 = Logger("override_demo_3")
    logger3.configure(
        profile="minimal",
        visual_mode=True,  # Enable visual enhancements
        use_symbols=True,  # Use symbols for log levels
        use_colors=True,  # Enable color output
    )

    @log_function(using="override_demo_3")
    def complex_operation3(data, options=None):
        """A complex operation with multiple parameters."""
        if options is None:
            options = {"validate": True, "transform": True}
        return f"Processed: {data} with {options}"

    print("\n3. Minimal profile with visual enhancements:")
    complex_operation3("minimal data")


def main():
    """Run the profiles demonstration."""
    print("LogEverything Profiles Demonstration")
    print("====================================")
    print("This example shows how to use predefined configuration profiles.")
    # Show how to inspect profile contents
    print("\n=== INSPECTING PROFILES ===")
    print("You can inspect profile contents before applying them:")
    dev_profile = get_profile("development")
    print(f"Development profile has {len(dev_profile)} settings, including:")
    print(f"- Log level: {dev_profile['level']}")
    print(f"- Visual mode: {dev_profile['visual_mode']}")
    print(f"- Log arguments: {dev_profile['log_arguments']}")

    # Demonstrate each profile
    demonstrate_development_profile()
    demonstrate_production_profile()
    demonstrate_minimal_profile()
    demonstrate_debug_profile()
    demonstrate_api_profile()
    demonstrate_testing_profile()
    demonstrate_profile_with_overrides()


if __name__ == "__main__":
    main()
