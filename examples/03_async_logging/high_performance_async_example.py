#!/usr/bin/env python3
"""
High-Performance Async Logging Example

This example demonstrates LogEverything's high-performance async logging
capabilities, including batch processing, queue management, and performance
monitoring.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from logeverything import AsyncLogger, configure
from logeverything.decorators import log


async def basic_async_logging():
    """Demonstrate basic async logging usage."""
    print("1. Basic Async Logging")
    print("-" * 25)

    # Create async logger
    async_log = AsyncLogger("async_app")

    # Async logging doesn't block
    await async_log.info("Application started")
    await async_log.debug("Debug information")
    await async_log.warning("This is a warning")
    await async_log.error("Error occurred")

    print("✓ Basic async logging completed")


async def performance_comparison():
    """Compare sync vs async logging performance."""
    print("\n2. Performance Comparison")
    print("-" * 30)

    from logeverything import Logger

    num_logs = 1000

    # Sync logging performance
    sync_logger = Logger("sync_perf")
    start_time = time.time()

    for i in range(num_logs):
        sync_logger.info(f"Sync log message {i}")

    sync_time = time.time() - start_time

    # Async logging performance
    async_logger = AsyncLogger("async_perf")
    start_time = time.time()

    # Create async tasks for all logs
    tasks = []
    for i in range(num_logs):
        task = async_logger.info(f"Async log message {i}")
        tasks.append(task)

    # Wait for all async logs to complete
    await asyncio.gather(*tasks)
    async_time = time.time() - start_time

    print(f"Sync logging: {sync_time:.4f}s for {num_logs} logs")
    print(f"Async logging: {async_time:.4f}s for {num_logs} logs")
    print(f"Performance improvement: {sync_time / async_time:.2f}x faster")


async def concurrent_logging():
    """Demonstrate concurrent logging from multiple coroutines."""
    print("\n3. Concurrent Logging")
    print("-" * 25)

    async_log = AsyncLogger("concurrent_app")

    async def worker(worker_id, task_count):
        """Worker coroutine that logs its progress."""
        for i in range(task_count):
            await async_log.info(f"Worker {worker_id}: Processing task {i + 1}")
            await asyncio.sleep(0.01)  # Simulate work
        await async_log.info(f"Worker {worker_id}: Completed all tasks")

    # Start multiple workers concurrently
    workers = [worker(1, 5), worker(2, 3), worker(3, 7), worker(4, 4)]

    start_time = time.time()
    await asyncio.gather(*workers)
    total_time = time.time() - start_time

    print(f"✓ All workers completed in {total_time:.2f}s")


async def async_decorator_logging():
    """Show async functions with decorators."""
    print("\n4. Async Function Decorators")
    print("-" * 35)

    @log
    async def fetch_user_data(user_id):
        """Fetch user data from async database."""
        await asyncio.sleep(0.1)  # Simulate DB query
        return {"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"}

    @log
    async def process_user_data(user_data):
        """Process user data asynchronously."""
        await asyncio.sleep(0.05)  # Simulate processing
        user_data["processed"] = True
        return user_data

    @log
    async def save_user_data(user_data):
        """Save processed user data."""
        await asyncio.sleep(0.08)  # Simulate save operation
        return f"User {user_data['id']} saved successfully"

    # Process multiple users concurrently
    user_ids = [1, 2, 3, 4, 5]

    # Fetch all user data
    fetch_tasks = [fetch_user_data(uid) for uid in user_ids]
    users = await asyncio.gather(*fetch_tasks)

    # Process all user data
    process_tasks = [process_user_data(user) for user in users]
    processed_users = await asyncio.gather(*process_tasks)

    # Save all user data
    save_tasks = [save_user_data(user) for user in processed_users]
    results = await asyncio.gather(*save_tasks)

    print(f"✓ Processed {len(results)} users concurrently")


async def error_handling():
    """Demonstrate error handling in async logging."""
    print("\n5. Async Error Handling")
    print("-" * 30)

    error_log = AsyncLogger("error_handler")

    async def risky_operation(operation_id):
        """Operation that might fail."""
        try:
            await error_log.info(f"Starting operation {operation_id}")

            if operation_id % 3 == 0:
                raise ValueError(f"Operation {operation_id} failed")

            await asyncio.sleep(0.05)  # Simulate work
            await error_log.info(f"Operation {operation_id} completed successfully")
            return f"Result {operation_id}"

        except Exception as e:
            await error_log.error(f"Operation {operation_id} failed: {e}")
            raise

    # Run multiple operations, some will fail
    operations = [risky_operation(i) for i in range(1, 8)]

    results = await asyncio.gather(*operations, return_exceptions=True)

    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]

    print(f"✓ Operations: {len(successes)} successful, {len(failures)} failed")


async def batched_logging():
    """Demonstrate batched async logging for high throughput."""
    print("\n6. Batched Async Logging")
    print("-" * 30)

    batch_log = AsyncLogger("batch_processor")

    async def log_batch(batch_id, batch_size):
        """Log a batch of messages."""
        await batch_log.info(f"Starting batch {batch_id} with {batch_size} items")

        # Create all log tasks for the batch
        log_tasks = []
        for i in range(batch_size):
            task = batch_log.debug(f"Batch {batch_id}: Processing item {i + 1}")
            log_tasks.append(task)

        # Wait for all logs in batch to complete
        await asyncio.gather(*log_tasks)
        await batch_log.info(f"Completed batch {batch_id}")

    # Process multiple batches concurrently
    batch_sizes = [100, 150, 80, 200, 120]
    start_time = time.time()

    batch_tasks = [log_batch(i + 1, size) for i, size in enumerate(batch_sizes)]
    await asyncio.gather(*batch_tasks)

    total_time = time.time() - start_time
    total_logs = sum(batch_sizes) + len(batch_sizes) * 2  # +2 for start/end logs per batch

    print(f"✓ Processed {total_logs} logs in {total_time:.2f}s")
    print(f"✓ Throughput: {total_logs / total_time:.0f} logs/second")


async def async_context_managers():
    """Show async logging with context managers."""
    print("\n7. Async Context Managers")
    print("-" * 35)

    context_log = AsyncLogger("context_app")

    class AsyncDatabaseConnection:
        """Simulate async database connection."""

        def __init__(self, db_name):
            self.db_name = db_name
            self.logger = AsyncLogger(f"db.{db_name}")

        async def __aenter__(self):
            await self.logger.info(f"Connecting to database {self.db_name}")
            await asyncio.sleep(0.1)  # Simulate connection time
            await self.logger.info(f"Connected to {self.db_name}")
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if exc_type:
                await self.logger.error(f"Error in database {self.db_name}: {exc_val}")
            await self.logger.info(f"Closing connection to {self.db_name}")
            await asyncio.sleep(0.05)  # Simulate cleanup

    # Use async context managers
    async with AsyncDatabaseConnection("users") as db:
        await context_log.info("Performing database operations")
        await asyncio.sleep(0.1)

    print("✓ Async context manager with logging completed")


async def main():
    """Main async function running all examples."""
    print("=== High-Performance Async Logging Demo ===\n")

    # Configure global async logging
    configure(level="INFO", visual_mode=True, use_symbols=True)

    await basic_async_logging()
    await performance_comparison()
    await concurrent_logging()
    await async_decorator_logging()
    await error_handling()
    await batched_logging()
    await async_context_managers()

    print("\n✓ High-performance async logging demonstration complete!")
    print("\nFeatures Demonstrated:")
    print("- Basic async logging operations")
    print("- Performance comparison (sync vs async)")
    print("- Concurrent logging from multiple coroutines")
    print("- Async function decorators")
    print("- Error handling in async context")
    print("- Batched logging for high throughput")
    print("- Async context managers")
    print("- Real-world async patterns")


if __name__ == "__main__":
    asyncio.run(main())
