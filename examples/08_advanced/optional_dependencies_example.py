"""
Example demonstrating the optional dependencies feature of LogEverything.

This example shows how LogEverything gracefully handles missing dependencies
and provides helpful messages for installing them.
"""

import os
import sys

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging

import logeverything as le
from logeverything.external import check_dependency, configure_common_loggers


def main():
    # Set up basic logging
    logger = le.setup_logging(level=logging.INFO)
    logger.info("Optional Dependencies Example")

    # Example 1: Check for a dependency that might not be installed
    logger.info("\nExample 1: Checking individual dependencies")
    frameworks = [
        ("fastapi", "fastapi"),
        ("django", "django"),
        ("flask", "flask"),
        ("transformers", "transformers"),
        ("nonexistent_package", "nonexistent-package"),
    ]

    for module_name, package_name in frameworks:
        is_available, message = check_dependency(module_name, package_name)
        if is_available:
            logger.info(f"✅ {package_name} is available")
        else:
            logger.warning(f"❌ {package_name} is not available: {message}")

    # Example 2: Auto-configure common loggers with dependency checking
    logger.info("\nExample 2: Auto-configuring common loggers")
    logger.info("Configuring common loggers (missing ones will be skipped with a warning):")

    # This will automatically check for dependencies and configure only available ones
    configured = configure_common_loggers(additional_loggers=["custom_logger"], show_warnings=True)

    logger.info(f"Successfully configured {len(configured)} loggers:")
    for logger_name in configured:
        logger.info(f"  - {logger_name}")

    # Example 3: Installation instructions
    logger.info("\nExample 3: Installation Instructions")
    logger.info("To install LogEverything with all dependencies:")
    logger.info("  pip install logeverything[full]")
    logger.info("\nTo install with specific feature dependencies:")
    logger.info("  pip install logeverything[web]      # Web framework integrations")
    logger.info("  pip install logeverything[fastapi]  # FastAPI integration")
    logger.info("  pip install logeverything[flask]    # Flask integration")
    logger.info("  pip install logeverything[django]   # Django integration")
    logger.info("  pip install logeverything[ml]       # Machine learning integrations")
    logger.info("  pip install logeverything[db]       # Database integrations")


if __name__ == "__main__":
    main()
