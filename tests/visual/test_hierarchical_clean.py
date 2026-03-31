#!/usr/bin/env python3
"""
Clean test for hierarchical alignment with our bracket encapsulation.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from logeverything.handlers import PrettyFormatter


def test_hierarchical_alignment_clean():
    print("=" * 80)
    print("HIERARCHICAL ALIGNMENT TEST WITH BRACKET ENCAPSULATION")
    print("=" * 80)
    print("Simulating LogEverything hierarchical output with our alignment fix.")
    print()

    # Create logger with our improved formatter
    logger = logging.getLogger("HierarchyDemo")
    logger.setLevel(logging.DEBUG)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create handler with our improved formatter
    handler = logging.StreamHandler()
    formatter = PrettyFormatter(
        use_colors=False, use_symbols=True, use_indent=True, align_columns=True
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    print("🌳 HIERARCHICAL LOGGING WITH PERFECT ALIGNMENT:")
    print("-" * 60)

    # Simulate hierarchical context structure like LogEverything would produce
    logger.info("Starting main application process")

    # Level 1
    logger.debug("│ Initializing application components")
    logger.info("│ ┌─► Authentication Module")
    logger.debug("│ │   Validating user credentials")
    logger.warning("│ │   Password expires in 3 days")
    logger.info("│ └─◄ Authentication completed")

    # Level 1 continued
    logger.info("│ ┌─► Database Connection")
    logger.debug("│ │   Establishing database connection")

    # Level 2
    logger.debug("│ │   ┌─► Connection Pool")
    logger.debug("│ │   │   Initializing connection pool")
    logger.error("│ │   │   Failed to connect to primary DB")
    logger.info("│ │   │   Switching to backup database")
    logger.info("│ │   └─◄ Connection pool established")

    # Back to Level 1
    logger.info("│ └─◄ Database connection successful")

    # Level 1 - Data Processing
    logger.info("│ ┌─► Data Processing Pipeline")
    logger.debug("│ │   Loading user data")

    # Level 2 - Validation
    logger.debug("│ │   ┌─► Data Validation")
    logger.debug("│ │   │   Checking data integrity")
    logger.warning("│ │   │   Some fields are missing")

    # Level 3 - Error handling
    logger.debug("│ │   │   ┌─► Error Recovery")
    logger.critical("│ │   │   │   Critical validation failure!")
    logger.debug("│ │   │   │   Attempting data recovery")
    logger.info("│ │   │   │   Using default values")
    logger.info("│ │   │   └─◄ Recovery completed")

    # Back to Level 2
    logger.info("│ │   └─◄ Validation completed")

    # Level 2 - Transformation
    logger.debug("│ │   ┌─► Data Transformation")
    logger.debug("│ │   │   Converting data format")
    logger.debug("│ │   │   Applying business rules")
    logger.info("│ │   └─◄ Transformation completed")

    # Back to Level 1
    logger.info("│ └─◄ Data processing completed")

    # Level 0 - Completion
    logger.info("Application startup completed successfully")

    print()
    print("=" * 80)
    print("ALIGNMENT ANALYSIS:")
    print("=" * 80)
    print("✅ Check if ALL vertical lines (│) are perfectly aligned")
    print("✅ Verify that bracket encapsulation maintains consistency")
    print("✅ Confirm that tree structure is clear and readable")
    print("✅ Look for any misalignment in emoji or level names")
    print()
    print("The bracket format [emoji LEVEL] should ensure perfect")
    print("alignment regardless of emoji display width differences!")


if __name__ == "__main__":
    test_hierarchical_alignment_clean()
