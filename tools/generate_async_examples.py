#!/usr/bin/env python3
"""
Generate async examples with outputs for documentation.

This script runs various async examples of LogEverything and captures their outputs
to create markdown documentation that shows users what to expect when using
async logging features.
"""

import asyncio
import datetime
import inspect
import io
import logging
import os
import sys
import time
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

# Add parent directory to path so we can import logeverything from development
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything import configure, setup_logging
from logeverything.async_logging import (
    AsyncLoggingContext,
    AsyncQueueHandler,
    AsyncQuietLoggingContext,
    AsyncVerboseLoggingContext,
    AsyncVisualLoggingContext,
    async_log_class,
    async_log_function,
)

# Setup output directory
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "source", "_examples")
os.makedirs(DOCS_DIR, exist_ok=True)

# Save current date for documentation
CURRENT_DATE = datetime.datetime.now().strftime("%Y-%m-%d")


async def capture_async_output(coro):
    """Capture output from an async function."""
    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Capture logs
    log_capture = io.StringIO()
    log_handler = logging.StreamHandler(log_capture)
    log_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    log_handler.setFormatter(formatter)

    # Add the handler to the root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)

    try:
        # Run the coroutine with redirected output
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            await coro
    finally:
        # Remove the handler
        root_logger.removeHandler(log_handler)

    return {
        "stdout": stdout_capture.getvalue(),
        "stderr": stderr_capture.getvalue(),
        "logs": log_capture.getvalue(),
    }


def write_markdown_example(file, title, description, code, output=None, level=2):
    """Write a markdown formatted example."""
    # Write title
    marker = "#" * level
    file.write(f"{marker} {title}\n\n")

    # Write description
    file.write(f"{description}\n\n")

    # Write code
    file.write("```python\n")
    file.write(code.strip())
    file.write("\n```\n\n")

    # Write output if provided
    if output:
        file.write("**Output:**\n\n")
        file.write("```\n")
        file.write(output)
        file.write("\n```\n\n")


async def example_basic_async_logging():
    """Example demonstrating basic async logging."""
    # Setup async logging
    setup_logging(
        level=logging.DEBUG,
        async_mode=True,
        async_queue_size=1000,
        async_flush_interval=0.5,
    )

    code = """
    import asyncio
    import logging
    from logeverything import setup_logging
    from logeverything.async_logging import async_log_function

    # Setup async logging
    setup_logging(
        level=logging.DEBUG,
        async_mode=True,  # Enable async queue handler
        async_queue_size=1000,
        async_flush_interval=0.5,
    )

    @async_log_function
    async def fetch_data(item_id):
        # This function is automatically logged with entry/exit
        await asyncio.sleep(0.1)  # Simulate network I/O
        return {"id": item_id, "data": f"Result for {item_id}"}

    @async_log_function
    async def process_items():
        tasks = [fetch_data(i) for i in range(3)]
        return await asyncio.gather(*tasks)

    # Run the async function
    results = await process_items()
    print(f"Processed {len(results)} items")
    """

    # Execute the example code for real output
    @async_log_function
    async def fetch_data(item_id):
        await asyncio.sleep(0.1)  # Simulate network I/O
        return {"id": item_id, "data": f"Result for {item_id}"}

    @async_log_function
    async def process_items():
        tasks = [fetch_data(i) for i in range(3)]
        return await asyncio.gather(*tasks)

    output = await capture_async_output(process_items())
    print(f"Processed 3 items")

    # Return the example details
    return {
        "title": "Basic Async Logging",
        "description": "Using async logging with coroutines is simple with the `async_log_function` decorator.",
        "code": code,
        "output": output["logs"] + output["stdout"],
    }


async def example_async_context_managers():
    """Example demonstrating async context managers."""
    # Reset configuration
    setup_logging(level=logging.INFO)

    code = """
    import asyncio
    import logging
    from logeverything import setup_logging
    from logeverything.async_logging import async_log_function, AsyncLoggingContext, AsyncVerboseLoggingContext

    setup_logging(level=logging.INFO)

    @async_log_function
    async def perform_operation(task_id):
        logging.info(f"Processing task {task_id}")
        await asyncio.sleep(0.1)
        return f"Result {task_id}"

    async def main():
        # Standard logging level (INFO)
        await perform_operation("default")

        # Temporarily increase verbosity with async context manager
        async with AsyncVerboseLoggingContext():
            logging.debug("This debug message will be shown")
            await perform_operation("verbose")

        # Back to normal logging
        logging.debug("This debug message will NOT be shown")
        await perform_operation("back-to-normal")

    await main()
    """

    # Execute the example code for real output
    @async_log_function
    async def perform_operation(task_id):
        logging.info(f"Processing task {task_id}")
        await asyncio.sleep(0.1)
        return f"Result {task_id}"

    async def main():
        # Standard logging level (INFO)
        await perform_operation("default")

        # Temporarily increase verbosity with async context manager
        async with AsyncVerboseLoggingContext():
            logging.debug("This debug message will be shown")
            await perform_operation("verbose")

        # Back to normal logging
        logging.debug("This debug message will NOT be shown")
        await perform_operation("back-to-normal")

    output = await capture_async_output(main())

    # Return the example details
    return {
        "title": "Async Context Managers",
        "description": "Use async context managers to modify logging behavior within an async context.",
        "code": code,
        "output": output["logs"],
    }


async def example_async_performance():
    """Example demonstrating async vs sync logging performance."""
    code = """
    import asyncio
    import time
    import logging
    from logeverything import setup_logging, configure
    from logeverything.async_logging import async_log_function

    async def run_comparison():
        # First with sync logging
        configure(async_mode=False)
        start_time = time.time()
        await intensive_logging_task(sync=True)
        sync_time = time.time() - start_time
        print(f"Sync logging time: {sync_time:.4f}s")

        # Wait for sync logs to finish
        await asyncio.sleep(0.5)

        # Then with async logging
        configure(async_mode=True)
        start_time = time.time()
        await intensive_logging_task(sync=False)
        async_time = time.time() - start_time
        print(f"Async logging time: {async_time:.4f}s")
        print(f"Performance improvement: {(sync_time-async_time)/sync_time:.1%}")

        # Wait for async logs to flush
        await asyncio.sleep(1)

    @async_log_function
    async def intensive_logging_task(sync=False):
        logging.info(f"Starting {'sync' if sync else 'async'} logging task")
        # Create many concurrent tasks with logging
        tasks = []
        for i in range(100):
            tasks.append(log_subtask(i))
        await asyncio.gather(*tasks)
        logging.info(f"Completed {'sync' if sync else 'async'} logging task")

    @async_log_function
    async def log_subtask(i):
        logging.debug(f"Subtask {i} started")
        await asyncio.sleep(0.01)  # Simulate some work
        logging.debug(f"Subtask {i} completed")
        return i

    # Configure initial logging
    setup_logging(
        level=logging.DEBUG,
        async_queue_size=5000,
        async_flush_interval=0.5
    )

    # Run the comparison
    await run_comparison()
    """

    # Execute the example code for real output
    # Note: We'll use a reduced version for demonstration
    async def run_comparison():
        # First with sync logging
        configure(async_mode=False)
        start_time = time.time()
        await intensive_logging_task(sync=True)
        sync_time = time.time() - start_time
        print(f"Sync logging time: {sync_time:.4f}s")

        # Wait for sync logs to finish
        await asyncio.sleep(0.5)

        # Then with async logging
        configure(async_mode=True)
        start_time = time.time()
        await intensive_logging_task(sync=False)
        async_time = time.time() - start_time
        print(f"Async logging time: {async_time:.4f}s")
        print(f"Performance improvement: {(sync_time-async_time)/sync_time:.1%}")

        # Wait for async logs to flush
        await asyncio.sleep(1)
        print(f"Performance improvement: {(sync_time-async_time)/sync_time:.1%}")

        # Wait for async logs to flush
        await asyncio.sleep(1)

    @async_log_function
    async def intensive_logging_task(sync=False):
        logging.info(f"Starting {'sync' if sync else 'async'} logging task")
        # Create many concurrent tasks with logging - using fewer for the example
        tasks = []
        for i in range(10):  # Reduced number for example
            tasks.append(log_subtask(i))
        await asyncio.gather(*tasks)
        logging.info(f"Completed {'sync' if sync else 'async'} logging task")

    @async_log_function
    async def log_subtask(i):
        logging.debug(f"Subtask {i} started")
        await asyncio.sleep(0.01)  # Simulate some work
        logging.debug(f"Subtask {i} completed")
        return i

    # Configure for this example
    setup_logging(level=logging.DEBUG, async_queue_size=5000, async_flush_interval=0.5)

    output = await capture_async_output(run_comparison())

    # Return the example details
    return {
        "title": "Async Logging Performance",
        "description": "Compare performance between synchronous and asynchronous logging.",
        "code": code,
        "output": output["stdout"],
    }


async def main():
    """Generate all examples and write to markdown file."""
    # Create a markdown file for async examples
    output_file = os.path.join(DOCS_DIR, "async_examples.md")

    async_examples = [
        await example_basic_async_logging(),
        await example_async_context_managers(),
        await example_async_performance(),
    ]

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# Async Logging Examples\n\n")
        f.write(f"Generated on {CURRENT_DATE}\n\n")
        f.write("These examples demonstrate how to use LogEverything with asynchronous code.\n\n")

        for example in async_examples:
            write_markdown_example(
                f, example["title"], example["description"], example["code"], example.get("output")
            )

    print(f"Generated async examples at {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
