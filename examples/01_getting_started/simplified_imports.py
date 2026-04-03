"""
Simplified import example for LogEverything.

This example demonstrates the simplified import experience where all
commonly used components can be imported directly from the top-level package.
No need to navigate deep module hierarchies - everything you need is right here!
"""

import sys
from pathlib import Path

# Add the parent directory to the path for imports to work when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import everything needed from the top-level package
from logeverything import (  # Core setup; Decorators; Handlers; Profile support
    PROFILES,
    Logger,
    get_profile,
    log,
)


def main():
    """Demonstrate the simplified import experience."""
    print("🚀 LogEverything Simplified Import Example")
    print("=" * 70)
    print("\n✨ Everything you need in one simple import!")
    print("   from logeverything import Logger, log, PROFILES, ...")
    print()

    # ============================================================================
    # Available Profiles
    # ============================================================================
    print("\n📋 Available Profiles:")
    print("-" * 70)
    for profile_name in PROFILES:
        profile = get_profile(profile_name)
        print(f"  • {profile_name:15} - {profile.get('description', 'No description')}")

    # ============================================================================
    # Example 1: Decorated Function with Visual Formatting
    # ============================================================================
    print("\n\n🔧 Example 1: Decorated Function")
    print("-" * 70)

    # Create logger with visual formatting enabled (no profile restrictions)
    logger = Logger("simplified_demo")

    @log(using="simplified_demo", use_symbols=True)
    def process_data(items):
        """Process the given items with doubling."""
        logger.info(f"Processing {len(items)} items")
        result = [item * 2 for item in items]
        logger.info(f"Generated {len(result)} results")
        return result

    result = process_data([1, 2, 3, 4, 5])
    print(f"✓ Result: {result}")

    # ============================================================================
    # Example 2: Decorated Class
    # ============================================================================
    print("\n\n🎯 Example 2: Decorated Class")
    print("-" * 70)

    @log(use_symbols=True)
    class DataProcessor:
        """A class for processing data with configurable multiplier."""

        def __init__(self, multiplier=2):
            self.multiplier = multiplier
            logger.info(f"DataProcessor initialized with multiplier={multiplier}")

        def process(self, items):
            """Process items with the multiplier."""
            logger.info(f"Processing {len(items)} items with multiplier {self.multiplier}")
            result = [item * self.multiplier for item in items]
            return result

    processor = DataProcessor(multiplier=3)
    result = processor.process([1, 2, 3, 4, 5])
    print(f"✓ Result: {result}")

    # ============================================================================
    # Summary
    # ============================================================================
    print("\n\n" + "=" * 70)
    print("✨ Key Takeaways:")
    print("  • Single import statement for all common components")
    print("  • Pre-configured profiles for different use cases")
    print("  • Simple decorators with @log for functions and classes")
    print("  • Visual formatting with use_symbols=True")
    print("  • No complex configuration needed to get started")
    print("=" * 70)


if __name__ == "__main__":
    main()
