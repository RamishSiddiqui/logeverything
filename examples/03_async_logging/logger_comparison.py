"""
Comparison example showing Logger vs AsyncLogger usage
"""

import asyncio

from logeverything import AsyncLogger, Logger


async def async_operation():
    """Simulate an async operation."""
    await asyncio.sleep(0.01)
    return "async_result"


def sync_operation():
    """Simulate a sync operation."""
    return "sync_result"


async def main():
    print("=" * 70)
    print("Logger vs AsyncLogger Comparison")
    print("=" * 70)

    # Regular Logger
    print("\n1. Regular Logger:")
    sync_log = Logger("sync_app")
    sync_log.info("Starting sync application")
    result = sync_operation()
    sync_log.info(f"Sync operation result: {result}")

    # Structured logging with sync logger
    user_sync_log = sync_log.bind(user_id=123, type="sync")
    user_sync_log.info("Sync user action completed")

    # AsyncLogger
    print("\n2. AsyncLogger:")
    async_log = AsyncLogger("async_app")
    async_log.info("Starting async application")
    await async_log.ainfo("Async logger initialized")

    # Async operations
    result = await async_operation()
    async_log.info(f"Async operation result: {result}")

    # Structured logging with async logger
    user_async_log = async_log.bind(user_id=456, type="async")
    user_async_log.info("Async user action completed")
    await user_async_log.ainfo("Async user action with await")

    print("\n3. Import Compatibility:")
    print("✓ from logeverything import Logger")
    print("✓ from logeverything import AsyncLogger")
    print("✓ Both classes provide the same interface")
    print("✓ AsyncLogger optimized for async applications")

    # Cleanup
    await async_log.close()

    print("\n" + "=" * 70)
    print("Comparison completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
