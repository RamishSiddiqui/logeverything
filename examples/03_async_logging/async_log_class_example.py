#!/usr/bin/env python3
"""
Example demonstrating async_log_class decorator with 'using' parameter.
This shows how to use async class decorators with specific logger selection.
"""

import asyncio

from logeverything import Logger
from logeverything.asyncio import async_log_class

# Create logger for async data processing
async_data_logger = Logger("AsyncDataProcessor", level="DEBUG")


@async_log_class(using="AsyncDataProcessor")
class AsyncDataProcessor:
    """Async data processor with automatic method logging."""

    def __init__(self, name):
        self.name = name
        self.processed_count = 0

    async def process_item(self, item):
        """Process a single item."""
        await asyncio.sleep(0.01)  # Simulate async work
        self.processed_count += 1
        return f"processed_{item}"

    async def process_batch(self, items):
        """Process multiple items concurrently."""
        tasks = [self.process_item(item) for item in items]
        results = await asyncio.gather(*tasks)
        return results

    def get_stats(self):
        """Get processing statistics."""
        return {"name": self.name, "processed": self.processed_count}


# Alternative: automatic logger selection for async classes
@async_log_class(level="INFO", include_private=False)
class AsyncCacheManager:
    """Async cache manager with automatic logger selection."""

    def __init__(self):
        self.cache = {}

    async def get_async(self, key):
        """Get item from cache asynchronously."""
        await asyncio.sleep(0.01)  # Simulate async cache lookup
        return self.cache.get(key)

    async def set_async(self, key, value):
        """Set item in cache asynchronously."""
        await asyncio.sleep(0.01)  # Simulate async cache write
        self.cache[key] = value


async def main():
    # Test async class logging with different loggers
    processor = AsyncDataProcessor("BatchProcessor")  # Uses AsyncDataProcessor logger
    cache_manager = AsyncCacheManager()  # Uses automatic logger selection

    items = ["item1", "item2", "item3"]
    results = await processor.process_batch(items)
    stats = processor.get_stats()

    await cache_manager.set_async("key1", "value1")
    cached_value = await cache_manager.get_async("key1")

    print(f"Results: {results}")
    print(f"Stats: {stats}")
    print(f"Cached value: {cached_value}")


if __name__ == "__main__":
    asyncio.run(main())
