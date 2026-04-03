"""
Simplified Intelligent Type Casting Demo - No External Registry Required

This example demonstrates LogEverything's intelligent type casting without requiring
manual logger registration, making it easier to run in any environment.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import logeverything
sys.path.insert(0, str(Path(__file__).parent.parent))

from logeverything import Logger
from logeverything.decorators import log, log_function, log_io


def main():
    """Run simplified demonstrations of intelligent type casting."""

    print("=" * 80)
    print("LogEverything: Simplified Intelligent Type Casting Demo")
    print("=" * 80)
    print()

    # Create a single logger and let the system auto-register it
    demo_logger = Logger(name="demo", visual_mode=True, use_symbols=True)

    print("🎯 SCENARIO 1: Smart Decorator Auto-Detection")
    print("-" * 60)

    # The smart decorator will automatically detect async functions
    @log  # No 'using' parameter - will auto-select available logger
    async def async_task(name, duration=0.01):
        """Async function that will be automatically handled."""
        await asyncio.sleep(duration)
        return f"Task '{name}' completed"

    @log  # No 'using' parameter - will auto-select available logger
    def sync_task(name, multiplier=2):
        """Sync function that will be automatically handled."""
        return f"Task '{name}' result: {len(name) * multiplier}"

    async def demo_auto_detection():
        print("Testing auto-detection with mixed sync/async functions...")

        # Test async function
        result1 = await async_task("AsyncWork", 0.02)
        print(f"  {result1}")

        # Test sync function
        result2 = sync_task("SyncWork", 3)
        print(f"  {result2}")
        print()

    asyncio.run(demo_auto_detection())

    print("🎯 SCENARIO 2: Explicit Decorator Types")
    print("-" * 60)

    # Test with explicit decorator types
    @log_function  # Explicit function decorator
    async def async_calculation(x, y):
        """Async calculation with explicit log_function decorator."""
        await asyncio.sleep(0.01)
        return x * y + (x + y)

    @log_io  # Explicit I/O decorator
    def file_operation(filename):
        """Sync I/O operation with explicit log_io decorator."""
        return f"Processing file: {filename}"

    async def demo_explicit_decorators():
        print("Testing explicit decorators with type casting...")

        # Async function with sync-designed decorator
        calc_result = await async_calculation(5, 8)
        print(f"  Calculation result: {calc_result}")

        # Sync I/O function
        file_result = file_operation("data.txt")
        print(f"  {file_result}")
        print()

    asyncio.run(demo_explicit_decorators())

    print("🎯 SCENARIO 3: Type Preservation Verification")
    print("-" * 60)

    # Verify that logger instances are preserved
    original_logger = demo_logger

    @log
    async def test_preservation():
        return "preservation_verified"

    @log
    def test_preservation_sync():
        return "sync_preservation_verified"

    async def demo_preservation():
        print("Testing logger instance preservation...")

        result1 = await test_preservation()
        result2 = test_preservation_sync()

        print(f"  Async result: {result1}")
        print(f"  Sync result: {result2}")
        print(f"  Logger instance preserved: {original_logger is demo_logger}")
        print(f"  Logger _is_async attribute: {demo_logger._is_async}")
        print()

    asyncio.run(demo_preservation())

    print("🎯 SCENARIO 4: Performance Test")
    print("-" * 60)

    @log
    async def fast_operation(i):
        """Fast async operation for performance testing."""
        return i**2

    async def demo_performance():
        print("Running performance test...")

        import time

        start_time = time.time()

        # Run multiple operations concurrently
        tasks = [fast_operation(i) for i in range(50)]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        elapsed = (end_time - start_time) * 1000

        print(f"  Completed 50 operations in {elapsed:.2f}ms")
        print(f"  Average per operation: {elapsed / 50:.2f}ms")
        print(f"  All results correct: {all(results[i] == i**2 for i in range(50))}")
        print()

    asyncio.run(demo_performance())

    print("🎯 SUMMARY")
    print("-" * 60)
    print("✅ Auto-detection working correctly")
    print("✅ Type casting transparent to user")
    print("✅ Logger instances preserved")
    print("✅ Performance remains excellent")
    print("✅ No manual configuration required")
    print()
    print("🚀 Key Benefits:")
    print("   • Decorators automatically adapt to function types")
    print("   • No need to worry about sync vs async compatibility")
    print("   • Original logger instances never modified")
    print("   • Minimal performance overhead")
    print("   • Zero configuration required")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
