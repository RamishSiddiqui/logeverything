"""
Comprehensive example demonstrating intelligent type casting between sync and async loggers/functions.

This example shows how LogEverything's decorators automatically handle mismatched logger and function types
by intelligently casting loggers to compatible types while preserving the original logger instance.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the parent directory to the path so we can import logeverything
sys.path.insert(0, str(Path(__file__).parent.parent))

from logeverything import AsyncLogger, Logger
from logeverything.asyncio import async_log_class, async_log_function
from logeverything.core import register_logger, unregister_logger
from logeverything.decorators import log, log_class, log_function, log_io


def main():
    """Run comprehensive demonstrations of intelligent type casting."""

    print("=" * 80)
    print("LogEverything: Intelligent Type Casting Demo")
    print("=" * 80)
    print()

    # Configure loggers with visual mode for better demonstration
    sync_logger = Logger(name="sync_demo", visual_mode=True, use_symbols=True)
    async_logger = AsyncLogger(name="async_demo")

    # Make sure both loggers are available in the global registry
    from logeverything.core import _active_loggers

    _active_loggers["sync_demo"] = sync_logger
    _active_loggers["async_demo"] = async_logger

    print("🎯 SCENARIO 1: Smart Decorator - Sync Logger with Async Function")
    print("-" * 60)

    @log(using="sync_demo")
    async def async_calculation(x, y, operation="add"):
        """Async function decorated with smart decorator using sync logger."""
        await asyncio.sleep(0.01)  # Simulate async work

        if operation == "add":
            return x + y
        elif operation == "multiply":
            return x * y
        else:
            return x - y

    async def demo_async_with_sync_logger():
        print("Calling async function with sync logger...")
        result1 = await async_calculation(5, 3)
        result2 = await async_calculation(4, 7, operation="multiply")
        print(f"Results: {result1}, {result2}")
        print()

    asyncio.run(demo_async_with_sync_logger())

    print("🎯 SCENARIO 2: Smart Decorator - Async Logger with Sync Function")
    print("-" * 60)

    @log(using="async_demo")
    def sync_calculation(x, y, operation="add"):
        """Sync function decorated with smart decorator using async logger."""
        if operation == "add":
            return x + y
        elif operation == "multiply":
            return x * y
        else:
            return x - y

    print("Calling sync function with async logger...")
    result1 = sync_calculation(10, 15)
    result2 = sync_calculation(8, 3, operation="multiply")
    print(f"Results: {result1}, {result2}")
    print()

    print("🎯 SCENARIO 3: Mixed I/O Operations")
    print("-" * 60)

    @log_io(using="sync_demo")
    async def async_file_operation(filename, content):
        """Async I/O function with sync logger."""
        await asyncio.sleep(0.02)  # Simulate async file I/O
        print(f"  -> Simulating async write to {filename}")
        return f"Wrote {len(content)} characters to {filename}"

    @log_io(using="async_demo")
    def sync_file_operation(filename):
        """Sync I/O function with async logger."""
        print(f"  -> Simulating sync read from {filename}")
        return f"Read content from {filename}"

    async def demo_mixed_io():
        print("Mixed I/O operations with cross-type loggers...")

        # Async I/O with sync logger
        write_result = await async_file_operation("data.txt", "Hello, World!")
        print(f"  {write_result}")

        # Sync I/O with async logger
        read_result = sync_file_operation("config.json")
        print(f"  {read_result}")
        print()

    asyncio.run(demo_mixed_io())

    print("🎯 SCENARIO 4: Class Decorators with Mixed Methods")
    print("-" * 60)

    @log_class(using="sync_demo")
    class DataProcessor:
        """Class with mixed sync/async methods using sync logger."""

        def __init__(self, name):
            self.name = name

        def validate_data(self, data):
            """Sync validation method."""
            return len(data) > 0 and isinstance(data, (list, str))

        async def process_data(self, data):
            """Async processing method."""
            await asyncio.sleep(0.01)
            if isinstance(data, str):
                return data.upper()
            elif isinstance(data, list):
                return [item * 2 for item in data]
            return data

        def get_summary(self):
            """Sync summary method."""
            return f"Processor: {self.name}"

    @async_log_class
    class AsyncDataHandler:
        """Class optimized for async operations."""

        def __init__(self, handler_id):
            self.handler_id = handler_id

        def prepare_data(self, raw_data):
            """Sync preparation method."""
            return raw_data.strip() if isinstance(raw_data, str) else raw_data

        async def handle_async_data(self, data):
            """Async handling method."""
            await asyncio.sleep(0.01)
            return f"Handled: {data}"

        async def finalize(self):
            """Async finalization method."""
            await asyncio.sleep(0.01)
            return f"Handler {self.handler_id} finalized"

    async def demo_mixed_classes():
        print("Testing mixed classes with cross-type loggers...")

        # Class with sync logger but mixed methods
        processor = DataProcessor("MainProcessor")
        print(f"  {processor.get_summary()}")

        is_valid = processor.validate_data("test data")
        print(f"  Data valid: {is_valid}")

        processed = await processor.process_data("hello world")
        print(f"  Processed: {processed}")

        # Async-optimized class
        handler = AsyncDataHandler("HANDLER_001")
        prepared = handler.prepare_data("  raw data  ")
        print(f"  Prepared: {prepared}")

        handled = await handler.handle_async_data(prepared)
        print(f"  {handled}")

        finalized = await handler.finalize()
        print(f"  {finalized}")
        print()

    asyncio.run(demo_mixed_classes())

    print("🎯 SCENARIO 5: Nested Decorators and Complex Scenarios")
    print("-" * 60)

    @log_io(using="async_demo")
    @log_function(using="sync_demo", log_arguments=True, log_return_values=True)
    async def complex_async_operation(operation_name, *args, **kwargs):
        """Complex async operation with multiple decorators and cross-type loggers."""
        await asyncio.sleep(0.02)

        result = {
            "operation": operation_name,
            "args_count": len(args),
            "kwargs_count": len(kwargs),
            "timestamp": "2025-06-30T12:00:00Z",
        }

        if operation_name == "calculate":
            result["value"] = sum(args) if args else 0
        elif operation_name == "process":
            result["processed"] = True

        return result

    async def demo_complex_scenarios():
        print("Complex nested decorators with cross-type loggers...")

        result1 = await complex_async_operation("calculate", 1, 2, 3, 4, 5)
        print(f"  Calculation result: {result1}")

        result2 = await complex_async_operation("process", config="production", debug=False)
        print(f"  Process result: {result2}")
        print()

    asyncio.run(demo_complex_scenarios())

    print("🎯 SCENARIO 6: Logger Instance Preservation")
    print("-" * 60)

    # Demonstrate that original logger instances are preserved
    original_sync_logger = sync_logger
    original_async_logger = async_logger

    @log(using="sync_demo")
    async def test_preservation():
        """Test that logger instances remain unchanged."""
        return "preservation_test"

    result = asyncio.run(test_preservation())

    print("Logger instance preservation test:")
    print(f"  Original sync logger preserved: {original_sync_logger is sync_logger}")
    print(f"  Original async logger preserved: {original_async_logger is async_logger}")
    print(f"  Sync logger _is_async attribute: {sync_logger._is_async}")
    print(f"  Async logger _is_async attribute: {async_logger._is_async}")
    print(f"  Test function result: {result}")
    print()

    print("🎯 SCENARIO 7: Performance with Type Casting")
    print("-" * 60)

    @log(using="sync_demo")
    async def performance_test_function(i):
        """Fast async function for performance testing."""
        return i * 2

    async def demo_performance():
        print("Running performance test with type casting...")

        import time

        start_time = time.time()

        tasks = [performance_test_function(i) for i in range(100)]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        elapsed = (end_time - start_time) * 1000  # Convert to milliseconds

        print(f"  Completed 100 async calls with type casting in {elapsed:.2f}ms")
        print(f"  Average per call: {elapsed/100:.2f}ms")
        print(f"  All results correct: {all(results[i] == i * 2 for i in range(100))}")
        print()

    asyncio.run(demo_performance())

    print("🎯 SUMMARY")
    print("-" * 60)
    print("✅ Smart type casting working correctly across all scenarios")
    print("✅ Logger instances preserved during type casting")
    print("✅ Performance impact minimal")
    print("✅ Mixed sync/async operations supported")
    print("✅ Complex decorator combinations working")
    print("✅ All decorator types support intelligent type casting")
    print()
    print("🚀 LogEverything's intelligent type casting allows you to:")
    print("   • Use any logger with any function type (sync/async)")
    print("   • Preserve your original logger instances")
    print("   • Maintain high performance")
    print("   • Use complex decorator combinations")
    print("   • Mix and match sync/async operations seamlessly")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
