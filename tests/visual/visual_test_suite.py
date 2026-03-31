#!/usr/bin/env python3
"""
Comprehensive Visual Test Suite for LogEverything
=================================================

This interactive test suite runs various logging scenarios and prompts the user
to visually confirm alignment and formatting. It's designed to be run manually
to validate visual changes and ensure hierarchical logging alignment is correct.

Key Test Scenarios:
1. Basic hierarchical logging with all log levels
2. Deep nesting with multiple levels
3. Mixed emoji and log levels
4. Problematic emojis that cause alignment issues
5. Real-world application scenario
6. Performance under load
7. Clean output validation

Usage:
    python visual_test_suite.py

The suite will run each test and pause for visual confirmation.
"""

import logging
import os
import sys
import time
from pathlib import Path

# Add the parent directory to the path to import logeverything
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from logeverything import VisualLoggingContext, log_function, setup_logging
from logeverything.core import get_logger


def clear_screen():
    """Clear the console screen."""
    os.system("cls" if os.name == "nt" else "clear")


def wait_for_confirmation(test_name):
    """Wait for user confirmation before proceeding."""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")
    print("Please examine the output above for:")
    print("  ✓ Perfect alignment of tree lines (│, ┌─►, └─◄)")
    print("  ✓ Consistent spacing in [emoji LEVEL] blocks")
    print("  ✓ Proper column alignment")
    print("  ✓ No visual artifacts or misaligned text")

    while True:
        response = input("\nDoes the output look correct? (y/n/q): ").lower().strip()
        if response in ["y", "yes"]:
            print("✓ Test passed - continuing to next test...")
            break
        elif response in ["n", "no"]:
            print("✗ Test failed - please note the issues")
            break
        elif response in ["q", "quit"]:
            print("Exiting test suite...")
            sys.exit(0)
        else:
            print("Please enter 'y' for yes, 'n' for no, or 'q' to quit")


@log_function
def database_connection():
    """Simulate database connection with hierarchical logging."""
    logger = get_logger()
    logger.debug("Connecting to database...")
    logger.info("Database connection established")
    logger.warning("Connection pool size is low")


@log_function
def service_initialization():
    """Simulate service initialization with hierarchical logging."""
    logger = get_logger()
    logger.info("Initializing user service...")
    logger.error("Failed to load user preferences")
    logger.critical("Critical service failure!")


def test_basic_hierarchy():
    """Test 1: Basic hierarchical logging with all log levels."""
    print("\n" + "=" * 80)
    print("TEST 1: BASIC HIERARCHICAL LOGGING")
    print("=" * 80)

    # Setup visual logging with hierarchical features
    setup_logging(
        level=logging.DEBUG,
        visual_mode=True,
        use_symbols=True,
        use_indent=True,
        log_entry_exit=True,
        beautify=True,
    )

    logger = get_logger()

    with VisualLoggingContext():
        logger.info("Starting application...")

        # Use decorated functions to create hierarchical structure
        database_connection()
        service_initialization()

    wait_for_confirmation("Basic Hierarchical Logging")


@log_function
def level_2_processing():
    """Level 2 processing function."""
    logger = get_logger()
    logger.debug("Processing level 2")

    level_3_processing()


@log_function
def level_3_processing():
    """Level 3 processing function."""
    logger = get_logger()
    logger.warning("Deep nesting warning")

    level_4_processing()


@log_function
def level_4_processing():
    """Level 4 processing function."""
    logger = get_logger()
    logger.error("Very deep error")

    level_5_processing()


@log_function
def level_5_processing():
    """Level 5 processing function."""
    logger = get_logger()
    logger.critical("Deepest level critical")
    logger.info("Still aligned at level 5")
    logger.debug("Debug message at deepest level")


def test_deep_nesting():
    """Test 2: Deep nesting with multiple levels."""
    print("\n" + "=" * 80)
    print("TEST 2: DEEP NESTING")
    print("=" * 80)

    setup_logging(
        level=logging.DEBUG,
        visual_mode=True,
        use_symbols=True,
        use_indent=True,
        log_entry_exit=True,
        beautify=True,
    )

    logger = get_logger()

    @log_function
    def level_1_processing():
        logger.info("Starting level 1")
        level_2_processing()

    with VisualLoggingContext():
        level_1_processing()

    wait_for_confirmation("Deep Nesting")


def test_mixed_emoji_levels():
    """Test 3: Mixed emoji and log levels."""
    print("\n" + "=" * 80)
    print("TEST 3: MIXED EMOJI AND LOG LEVELS")
    print("=" * 80)

    setup_logging(
        level=logging.DEBUG,
        visual_mode=True,
        use_symbols=True,
        use_indent=True,
        log_entry_exit=True,
        beautify=True,
    )

    logger = get_logger()

    @log_function
    def mixed_logging_test():
        logger.debug("Debug message with 🐛")
        logger.info("Info message with ℹ️")
        logger.warning("Warning message with ⚠️")
        logger.error("Error message with ❌")
        logger.critical("Critical message with 🔥")

        nested_mixed_processing()

    @log_function
    def nested_mixed_processing():
        logger.info("Nested info with ℹ️")
        logger.warning("Nested warning with ⚠️")
        logger.error("Nested error with ❌")

    with VisualLoggingContext():
        mixed_logging_test()

    wait_for_confirmation("Mixed Emoji and Log Levels")


def test_problematic_emojis():
    """Test 4: Problematic emojis that historically caused alignment issues."""
    print("\n" + "=" * 80)
    print("TEST 4: PROBLEMATIC EMOJIS")
    print("=" * 80)

    setup_logging(
        level=logging.DEBUG,
        visual_mode=True,
        use_symbols=True,
        use_indent=True,
        log_entry_exit=True,
        beautify=True,
    )

    logger = get_logger()

    @log_function
    def problematic_emoji_test():
        # These emojis have historically caused alignment issues
        logger.info("Info with ℹ️ (double-width)")
        logger.warning("Warning with ⚠️ (double-width)")
        logger.error("Error with ❌ (single-width)")
        logger.debug("Debug with 🐛 (double-width)")
        logger.critical("Critical with 🔥 (double-width)")

        more_problematic_emojis()

    @log_function
    def more_problematic_emojis():
        logger.info("Unicode info: 📝")
        logger.warning("Unicode warning: ⚡")
        logger.error("Unicode error: 💥")

    with VisualLoggingContext():
        problematic_emoji_test()

    wait_for_confirmation("Problematic Emojis")


def test_real_world_scenario():
    """Test 5: Real-world application scenario."""
    print("\n" + "=" * 80)
    print("TEST 5: REAL-WORLD APPLICATION SCENARIO")
    print("=" * 80)

    setup_logging(
        level=logging.DEBUG,
        visual_mode=True,
        use_symbols=True,
        use_indent=True,
        log_entry_exit=True,
        beautify=True,
    )

    logger = get_logger()

    @log_function
    def handle_web_request():
        logger.info("Received HTTP request: GET /api/users")

        authenticate_user()
        query_database()
        process_response()
        handle_caching()

        logger.info("Request completed successfully (200 OK)")

    @log_function
    def authenticate_user():
        logger.debug("Validating JWT token...")
        logger.info("User authenticated successfully")

    @log_function
    def query_database():
        logger.debug("Executing SQL query: SELECT * FROM users")
        logger.warning("Query took longer than expected (1.2s)")
        logger.info("Retrieved 150 user records")

    @log_function
    def process_response():
        logger.debug("Serializing user data to JSON")
        logger.info("Response prepared successfully")

    @log_function
    def handle_caching():
        logger.debug("Storing result in Redis cache")
        logger.error("Cache write failed - continuing without cache")

    with VisualLoggingContext():
        handle_web_request()

    wait_for_confirmation("Real-World Application Scenario")


def test_performance_load():
    """Test 6: Performance under load."""
    print("\n" + "=" * 80)
    print("TEST 6: PERFORMANCE UNDER LOAD")
    print("=" * 80)

    setup_logging(
        level=logging.DEBUG,
        visual_mode=True,
        use_symbols=True,
        use_indent=True,
        log_entry_exit=True,
        beautify=True,
    )

    logger = get_logger()

    @log_function
    def performance_test():
        logger.info("Starting performance test...")

        for i in range(20):
            process_batch(i + 1)

    @log_function
    def process_batch(batch_num):
        logger.debug(f"Processing batch {batch_num}")
        if batch_num % 5 == 0:
            logger.warning(f"Batch {batch_num} took longer than expected")
        if batch_num % 7 == 0:
            logger.error(f"Error in batch {batch_num} - retrying...")
        logger.info(f"Batch {batch_num} completed")

    with VisualLoggingContext():
        performance_test()

    wait_for_confirmation("Performance Under Load")


def test_clean_output():
    """Test 7: Clean output validation."""
    print("\n" + "=" * 80)
    print("TEST 7: CLEAN OUTPUT VALIDATION")
    print("=" * 80)

    setup_logging(
        level=logging.DEBUG,
        visual_mode=True,
        use_symbols=True,
        use_indent=True,
        log_entry_exit=True,
        beautify=True,
    )

    logger = get_logger()

    @log_function
    def clean_output_test():
        logger.info("This should have perfect alignment")
        logger.debug("All tree lines should be straight")
        logger.warning("No extra spaces or misplaced characters")
        logger.error("Every log entry should be perfectly aligned")

        nested_clean_test()

    @log_function
    def nested_clean_test():
        logger.info("Nested entries should also be clean")
        logger.debug("Tree branches should connect properly")
        logger.warning("No visual artifacts should be present")

    with VisualLoggingContext():
        clean_output_test()

    wait_for_confirmation("Clean Output Validation")


def run_all_tests():
    """Run all visual tests in sequence."""
    tests = [
        ("Basic Hierarchy", test_basic_hierarchy),
        ("Deep Nesting", test_deep_nesting),
        ("Mixed Emoji Levels", test_mixed_emoji_levels),
        ("Problematic Emojis", test_problematic_emojis),
        ("Real-World Scenario", test_real_world_scenario),
        ("Performance Load", test_performance_load),
        ("Clean Output", test_clean_output),
    ]

    print("🧪 LogEverything Visual Test Suite")
    print("=" * 80)
    print("This suite will run 7 comprehensive tests to validate visual alignment.")
    print("Please examine each test output carefully and confirm if it looks correct.")
    print("=" * 80)

    input("Press Enter to start the test suite...")

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        clear_screen()
        try:
            test_func()
            passed += 1
        except KeyboardInterrupt:
            print("\n\nTest suite interrupted by user.")
            break
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error: {e}")
            failed += 1

    # Final summary
    clear_screen()
    print("🏁 TEST SUITE COMPLETE")
    print("=" * 80)
    print(f"Tests Passed: {passed}")
    print(f"Tests Failed: {failed}")
    print(f"Total Tests: {len(tests)}")

    if failed == 0:
        print("\n🎉 All tests completed! Visual alignment appears to be working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) had issues. Please review the failing scenarios.")

    print("\nThank you for validating the LogEverything visual alignment!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
