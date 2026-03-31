"""
Demo showing the correct way to use @asynccontextmanager
"""

import asyncio
from contextlib import asynccontextmanager


class ExampleLogger:
    @asynccontextmanager
    async def context(self, name):
        print(f"Entering {name}")
        try:
            yield self
        finally:
            print(f"Exiting {name}")


async def demo_wrong_way():
    """This will fail"""
    log = ExampleLogger()
    try:
        # WRONG: This returns an async generator, not a context manager
        async with log.context("test"):  # TypeError!
            print("In context")
    except TypeError as e:
        print(f"Error: {e}")


async def demo_correct_way():
    """This works correctly"""
    log = ExampleLogger()

    # CORRECT: Call the method to get the actual context manager
    context_manager = log.context("test")
    async with context_manager:
        print("In context")


async def main():
    print("=== Demonstrating the async context manager issue ===\n")

    print("1. Wrong way (causes TypeError):")
    await demo_wrong_way()

    print("\n2. Correct way:")
    await demo_correct_way()


if __name__ == "__main__":
    asyncio.run(main())
