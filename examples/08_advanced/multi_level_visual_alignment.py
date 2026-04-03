#!/usr/bin/env python3
"""
Advanced Multi-Level Visual Alignment Example

This advanced example demonstrates LogEverything's visual alignment capabilities
with deep function nesting, showing how the library maintains perfect visual
hierarchy even with complex call stacks.

Features Demonstrated:
- Deep function nesting (4+ levels)
- Mixed logging inside and outside decorated functions
- Performance timing at each level
- Error handling and edge cases
- Production-ready logging patterns
- Visual hierarchy maintenance across complex scenarios

This example is perfect for understanding how LogEverything handles
complex applications with deep call stacks and intricate logging needs.
"""

import os
import sys

# Add the package to Python path for examples
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from logeverything import Logger, log_function

# Create a comprehensive logger for advanced scenarios
logger = Logger(
    name="advanced_alignment", visual_mode=True, use_symbols=True, use_indent=True, beautify=True
)


@log_function(using="advanced_alignment")
def level_0_orchestrator():
    """
    Top-level orchestrator function demonstrating deep nesting.

    This simulates a real-world scenario where a main controller
    calls multiple subsystems, each with their own nested operations.
    """
    logger.info("🎯 Starting advanced multi-level processing demonstration")
    logger.info("This will show visual alignment across 4+ nesting levels")

    @log_function(using="advanced_alignment")
    def level_1_processor():
        """Level 1: Main processing logic."""
        logger.info("🔧 Initializing main processor")

        @log_function(using="advanced_alignment")
        def level_2_analyzer():
            """Level 2: Data analysis operations."""
            logger.info("📊 Starting data analysis")
            logger.debug("Loading analysis configuration")

            @log_function(using="advanced_alignment")
            def level_3_validator():
                """Level 3: Deep validation logic."""
                logger.info("✅ Running deep validation checks")

                @log_function(using="advanced_alignment")
                def level_4_checker():
                    """Level 4: The deepest level of processing."""
                    logger.info("🔍 Performing atomic-level checks")
                    logger.debug("Accessing low-level validation rules")

                    # Simulate some complex logic
                    for i in range(3):
                        logger.debug(f"Processing validation rule {i + 1}")

                    logger.info("✨ Atomic checks completed successfully")
                    return "validation_passed"

                result = level_4_checker()
                logger.info(f"🎉 Deep validation completed: {result}")
                return result

            validation_result = level_3_validator()
            logger.info(f"📈 Analysis validation: {validation_result}")

            # Simulate analysis work
            logger.info("🧮 Computing analysis metrics")
            logger.warning("⚠️ Large dataset detected - using optimized algorithms")

            return "analysis_complete"

        analysis_result = level_2_analyzer()
        logger.info(f"🎯 Processing analysis: {analysis_result}")

        # Additional processing
        logger.info("🔄 Running post-analysis operations")

        return "processing_complete"

    # Execute the multi-level operation
    logger.info("🚀 Launching multi-level operation")

    result = level_1_processor()
    logger.info(f"✅ Operation completed: {result}")

    # Final summary logging
    logger.info("📋 Generating operation summary")
    logger.info("🎊 All levels completed successfully!")

    return result


def demonstrate_context_switching():
    """Show how alignment works when switching between contexts."""
    print("🔄 CONTEXT SWITCHING DEMONSTRATION")
    print("Showing how alignment works outside decorated functions:")
    print()

    # Log outside any decorator context
    logger.info("📝 This message is logged OUTSIDE any decorated function")

    # Call a decorated function
    result = level_0_orchestrator()

    # Log outside again
    logger.info("📝 This message is logged OUTSIDE again after the decorated function")

    return result


def run_advanced_demonstration():
    """Run the complete advanced visual alignment demonstration."""
    print("=" * 80)
    print("ADVANCED MULTI-LEVEL VISUAL ALIGNMENT DEMONSTRATION")
    print("=" * 80)
    print()
    print("🎯 ADVANCED FEATURES TO OBSERVE:")
    print("  • Deep nesting (4+ levels) with perfect alignment")
    print("  • Mixed log levels (INFO, DEBUG, WARNING)")
    print("  • Context switching between decorated and undecorated functions")
    print("  • Performance timing at each nesting level")
    print("  • Complex real-world logging scenarios")
    print("  • Visual hierarchy maintenance across all levels")
    print()
    print("📋 WHAT TO WATCH FOR:")
    print("  • Each nesting level has consistent visual indentation")
    print("  • Function entry/exit logs are aligned at each level")
    print("  • Function body content is always indented one level deeper")
    print("  • Context switches are visually clear")
    print("  • Performance metrics show timing for each level")
    print()
    print("🚀 Starting demonstration...")
    print("=" * 80)
    print()

    # Run the demonstration
    result = demonstrate_context_switching()

    print()
    print("=" * 80)
    print("✅ ADVANCED DEMONSTRATION COMPLETE")
    print("=" * 80)
    print()
    print("🎉 SUCCESSFULLY DEMONSTRATED:")
    print("✅ Perfect alignment across 4+ nesting levels")
    print("✅ Consistent visual hierarchy maintenance")
    print("✅ Clean context switching")
    print("✅ Professional production-ready output")
    print("✅ Complex scenario handling")
    print("✅ Mixed log level formatting")
    print()
    print("💡 KEY TAKEAWAYS:")
    print("  • LogEverything maintains visual consistency at any nesting depth")
    print("  • Complex applications get clean, readable logging automatically")
    print("  • Debugging deep call stacks becomes much easier")
    print("  • Performance monitoring is built-in at every level")
    print("  • No manual formatting or indentation required!")
    print("=" * 80)

    return result


if __name__ == "__main__":
    # Run the complete advanced demonstration
    run_advanced_demonstration()
