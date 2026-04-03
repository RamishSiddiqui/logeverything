"""
Complete explanation of the async context manager TypeError and solutions
"""

import asyncio
from contextlib import asynccontextmanager

from logeverything import AsyncLogger


class DemoAsyncLogger:
    """Demo class to show the async context manager patterns"""

    # PATTERN 1: This causes the TypeError - DON'T DO THIS
    @asynccontextmanager
    async def broken_context(self, name):
        """This pattern causes 'async_generator' object error"""
        print(f"Entering {name}")
        try:
            yield self
        finally:
            print(f"Exiting {name}")

    # PATTERN 2: This works correctly - DO THIS
    def working_context(self, name):
        """This pattern works correctly"""

        @asynccontextmanager
        async def _context():
            print(f"Entering {name}")
            try:
                yield self
            finally:
                print(f"Exiting {name}")

        return _context()


async def demonstrate_the_problem():
    """Show the difference between working and broken patterns."""

    print("=" * 70)
    print("Async Context Manager TypeError Explanation")
    print("=" * 70)

    demo = DemoAsyncLogger()

    print("\n1. BROKEN PATTERN (causes TypeError):")
    print("   @asynccontextmanager on method directly")

    try:
        # This will fail!
        async with demo.broken_context("broken"):
            print("   This won't work!")
    except TypeError as e:
        print(f"   ❌ Error: {e}")
        print("   ❌ Reason: @asynccontextmanager on method creates async generator")
        print("   ❌ When called: returns async generator object, not context manager")

    print("\n2. WORKING PATTERN:")
    print("   Method returns result of @asynccontextmanager function")

    try:
        # This works!
        async with demo.working_context("working"):
            print("   ✅ This works perfectly!")
        print(
            "   ✅ Reason: Method calls @asynccontextmanager function and returns context manager"
        )
    except Exception as e:
        print(f"   Unexpected error: {e}")

    print("\n3. REAL-WORLD EXAMPLE with AsyncLogger:")

    log = AsyncLogger("demo")

    try:
        # This should work with our fixed implementation
        async with log.context("Real Example"):
            log.info("Inside AsyncLogger context manager")
            await asyncio.sleep(0.001)  # Simulate async work

        print("   ✅ AsyncLogger.context() works correctly!")

    except Exception as e:
        print(f"   ❌ AsyncLogger error: {e}")
    finally:
        await log.close()

    print("\n" + "=" * 70)
    print("KEY TAKEAWAYS:")
    print("• @asynccontextmanager on methods directly → async generator (breaks)")
    print("• Method returning @asynccontextmanager() call → context manager (works)")
    print("• Always test async context managers with 'async with'")
    print("• Our AsyncLogger uses the WORKING pattern")
    print("=" * 70)


async def show_correct_usage():
    """Show the correct way to use AsyncLogger context managers."""

    print("\n" + "=" * 50)
    print("Correct AsyncLogger Usage Examples")
    print("=" * 50)

    log = AsyncLogger("usage_demo")

    try:
        # Example 1: Basic context
        print("\n1. Basic context:")
        async with log.context("Data Processing"):
            log.info("Processing data...")
            await asyncio.sleep(0.01)

        # Example 2: Context with parameters
        print("\n2. Context with parameters:")
        async with log.context("User Operation", user_id=123, operation="login"):
            log.info("User performing operation...")

        # Example 3: Using existing async context managers
        print("\n3. Using built-in async contexts:")
        from logeverything.asyncio import AsyncVerboseLoggingContext

        async with AsyncVerboseLoggingContext():
            log.debug("This debug message shows in verbose mode")
            log.info("Verbose logging active")

    finally:
        await log.close()


if __name__ == "__main__":
    asyncio.run(demonstrate_the_problem())
    asyncio.run(show_correct_usage())
