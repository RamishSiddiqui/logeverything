#!/usr/bin/env python3
"""
Minimal Clean Async Services Example - Perfect Logging Output
=============================================================

This example demonstrates the cleanest possible async logging output
by simplifying the architecture and avoiding context bleeding issues.

Key features:
- Clean, readable logging output
- Proper async/sync integration
- No context bleeding between operations
- Demonstrates the intelligent type casting in action
"""

import asyncio

from logeverything.asyncio import AsyncLogger
from logeverything.core import register_logger
from logeverything.decorators import log


class SimpleAsyncService:
    """A simple async service with clean logging."""

    def __init__(self):
        # Create a clean async logger
        self.log = AsyncLogger("service", level="INFO", visual_mode=True)
        # Register it with the decorator system for seamless integration
        register_logger("service", self.log)

    @log(using="service")  # Explicitly use our async logger
    async def fetch_data(self, item_id: int) -> dict:
        """Async operation with clean logging."""
        self.log.info(f"🔍 Fetching data for item {item_id}")

        # Simulate async work
        await asyncio.sleep(0.1)

        result = {"id": item_id, "data": f"Data for item {item_id}"}
        self.log.info(f"✅ Successfully fetched data for item {item_id}")
        return result

    @log(using="service")  # Intelligent type casting: works with sync functions too
    def process_data(self, data: dict) -> dict:
        """Sync operation using the same decorator - type casting in action!"""
        self.log.info(f"⚙️ Processing data for item {data['id']}")

        # Simulate processing work
        processed = {**data, "processed": True, "status": "complete"}

        self.log.info(f"✅ Successfully processed item {data['id']}")
        return processed

    @log(using="service")
    async def complete_workflow(self, item_id: int) -> dict:
        """Complete workflow combining async and sync operations."""
        self.log.info(f"🚀 Starting workflow for item {item_id}")

        # Async operation
        raw_data = await self.fetch_data(item_id)

        # Sync operation (same decorator, intelligent type casting!)
        processed_data = self.process_data(raw_data)

        self.log.info(f"🎉 Workflow completed for item {item_id}")
        return processed_data


async def demo_clean_async_logging():
    """Demonstrate clean async logging with type casting."""
    print("🎯 Clean Async Logging Demo")
    print("=" * 40)
    print("This shows the @log decorator's intelligent type casting:")
    print("- Same decorator works with both async and sync functions")
    print("- Clean, readable output")
    print("- No context bleeding")
    print()

    # Create the service
    service = SimpleAsyncService()

    print("📝 Running Single Workflow:")
    print("-" * 30)

    # Run a single workflow
    result1 = await service.complete_workflow(101)

    print("\n📝 Running Multiple Concurrent Workflows:")
    print("-" * 40)

    # Run multiple workflows concurrently
    tasks = [
        service.complete_workflow(201),
        service.complete_workflow(202),
        service.complete_workflow(203),
    ]
    results = await asyncio.gather(*tasks)

    print("\n📊 Results:")
    print("-" * 15)
    print(f"Single workflow result: {result1}")
    print(f"Concurrent workflows: {len(results)} completed")

    print("\n🎯 Key Features Demonstrated:")
    print("• The @log decorator works seamlessly with both async and sync functions")
    print("• Intelligent type casting automatically adapts to function types")
    print("• Clean, structured logging output")
    print("• AsyncLogger integration with decorator system")


if __name__ == "__main__":
    asyncio.run(demo_clean_async_logging())
