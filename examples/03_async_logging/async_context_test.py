"""
Simple test to demonstrate the async context manager fix
"""

import asyncio

from logeverything import AsyncLogger


async def test_async_context_manager():
    """Test the async context manager usage."""

    print("Testing AsyncLogger context managers...")

    log = AsyncLogger("test_app")

    try:
        # Method 1: Using existing async context managers (works)
        from logeverything.asyncio import AsyncVerboseLoggingContext

        print("\n1. Using AsyncVerboseLoggingContext directly:")
        async with AsyncVerboseLoggingContext():
            log.info("This works perfectly!")
            log.debug("Debug message in verbose mode")

        # Method 2: Try the AsyncLogger's context method
        print("\n2. Trying AsyncLogger.context() method:")
        try:
            # This SHOULD work if we fix the implementation
            async with log.context("Test Context"):
                log.info("Inside context manager")
        except TypeError as e:
            print(f"Error: {e}")
            print("This is the async_generator issue we need to fix")

        print("\n3. The reason for the error:")
        print("   - @asynccontextmanager creates an async generator function")
        print("   - Calling log.context() returns an async generator object")
        print("   - But 'async with' needs an async context manager object")
        print("   - The @asynccontextmanager decorator should make this work!")

    finally:
        await log.close()


if __name__ == "__main__":
    asyncio.run(test_async_context_manager())
