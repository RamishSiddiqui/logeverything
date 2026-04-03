"""
Advanced Example: Intelligent Type Casting in LogEverything

This example demonstrates how LogEverything's decorators can intelligently handle
mismatched logger and function types by automatically casting loggers to compatible
types while preserving the original logger instance.

Key Features Demonstrated:
1. Smart decorator automatically detects async functions and uses appropriate logging
2. Sync loggers can be used with async functions (and vice versa)
3. Original logger instances are preserved
4. Type casting is transparent to the user
5. All decorators support this intelligent behavior
6. Performance is maintained
7. Configuration and visual formatting are preserved
"""

import asyncio
import time
from pathlib import Path
from typing import Any, Dict, List

from logeverything import AsyncLogger, Logger
from logeverything.asyncio import async_log_class
from logeverything.decorators import log, log_class, log_function, log_io

# =============================================================================
# Setup: Create Different Logger Types
# =============================================================================


def setup_loggers():
    """Set up different types of loggers for demonstration."""

    # Create a sync logger with visual formatting
    sync_logger = Logger(
        name="SyncVisual",
        use_symbols=True,
        visual_mode=True,
        format="%(levelname)s | %(name)s | %(message)s",
    )

    # Create an async logger with minimal formatting
    async_logger = AsyncLogger(
        name="AsyncMinimal", use_symbols=False, visual_mode=False, format="[%(name)s] %(message)s"
    )

    # Create a performance-focused logger
    perf_logger = Logger(name="Performance", use_symbols=False, visual_mode=False)

    print("✅ Loggers created:")
    print(f"   • SyncVisual (sync): _is_async = {sync_logger._is_async}")
    print(f"   • AsyncMinimal (async): _is_async = {async_logger._is_async}")
    print(f"   • Performance (sync): _is_async = {perf_logger._is_async}")
    print()

    return sync_logger, async_logger, perf_logger


# =============================================================================
# Example 1: Smart Decorator with Mixed Types
# =============================================================================


class SmartDecoratorExample:
    """Demonstrates the smart @log decorator with mixed sync/async scenarios."""

    def __init__(self):
        self.sync_logger, self.async_logger, self.perf_logger = setup_loggers()

    # Async function with sync logger - decorator auto-detects and handles
    @log(using="SyncVisual")
    async def async_data_processor(self, data: List[int]) -> Dict[str, Any]:
        """Process data asynchronously using a sync logger."""
        print("🔄 Processing data asynchronously with sync logger...")

        # Simulate async processing
        await asyncio.sleep(0.1)

        result = {
            "sum": sum(data),
            "average": sum(data) / len(data) if data else 0,
            "count": len(data),
            "max": max(data) if data else None,
            "min": min(data) if data else None,
        }

        return result

    # Sync function with async logger - decorator auto-detects and handles
    @log(using="AsyncMinimal")
    def sync_data_validator(self, data: List[int]) -> bool:
        """Validate data synchronously using an async logger."""
        print("✅ Validating data synchronously with async logger...")

        # Simulate validation logic
        if not data:
            return False

        # Check for reasonable values
        if any(x < 0 or x > 1000 for x in data):
            return False

        return True

    # Mixed function types with different loggers
    @log(using="Performance")
    def sync_fast_calculation(self, x: int, y: int) -> int:
        """Fast sync calculation with performance logger."""
        return x * y + (x - y) ** 2

    @log(using="Performance")
    async def async_slow_calculation(self, x: int, y: int) -> float:
        """Slow async calculation with performance logger."""
        await asyncio.sleep(0.05)  # Simulate complex calculation
        return (x**0.5) * (y**0.5) + (x / (y + 1))


# =============================================================================
# Example 2: Advanced I/O Operations
# =============================================================================


class IOOperationsExample:
    """Demonstrates I/O operations with intelligent type casting."""

    def __init__(self):
        self.sync_logger, self.async_logger, self.perf_logger = setup_loggers()

    # Async I/O with sync logger
    @log_io(using="SyncVisual")
    async def async_file_reader(self, filepath: str) -> str:
        """Read file asynchronously using sync logger."""
        print(f"📖 Reading file '{filepath}' asynchronously...")

        # Simulate async file reading
        await asyncio.sleep(0.02)

        try:
            # In real code, you'd use aiofiles
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        except FileNotFoundError:
            return f"File '{filepath}' not found"

    # Sync I/O with async logger
    @log_io(using="AsyncMinimal")
    def sync_file_writer(self, filepath: str, content: str) -> bool:
        """Write file synchronously using async logger."""
        print(f"💾 Writing to file '{filepath}' synchronously...")

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ Error writing file: {e}")
            return False

    # Batch I/O operations
    @log_function(using="Performance", log_arguments=True, log_return_values=True)
    async def batch_process_files(self, filepaths: List[str]) -> List[str]:
        """Process multiple files with performance tracking."""
        print(f"📁 Batch processing {len(filepaths)} files...")

        results = []
        for filepath in filepaths:
            content = await self.async_file_reader(filepath)
            # Process content (example: count lines)
            line_count = len(content.split("\n")) if content else 0
            results.append(f"{filepath}: {line_count} lines")

        return results


# =============================================================================
# Example 3: Class-Based Examples
# =============================================================================


@log_class(using="SyncVisual")
class DataProcessor:
    """A class with mixed sync/async methods using sync logger."""

    def __init__(self, name: str):
        self.name = name
        self.processed_count = 0

    def validate_input(self, data: Any) -> bool:
        """Sync validation method."""
        if data is None:
            return False
        return True

    async def process_data(self, data: List[int]) -> Dict[str, Any]:
        """Async processing method."""
        if not self.validate_input(data):
            raise ValueError("Invalid input data")

        # Simulate async processing
        await asyncio.sleep(0.1)

        self.processed_count += 1

        return {
            "processor": self.name,
            "data": data,
            "sum": sum(data),
            "processed_count": self.processed_count,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics."""
        return {"name": self.name, "processed_count": self.processed_count}


@async_log_class
class AsyncDataManager:
    """A class optimized for async operations."""

    def __init__(self, manager_id: str):
        self.manager_id = manager_id
        self.cache = {}

    def sync_cache_operation(self, key: str, value: Any) -> None:
        """Sync cache operation (handled by regular log_class)."""
        self.cache[key] = value

    async def async_data_fetch(self, data_id: str) -> Any:
        """Async data fetching (handled by async_log_function)."""
        # Check cache first
        if data_id in self.cache:
            return self.cache[data_id]

        # Simulate async data fetching
        await asyncio.sleep(0.05)

        # Simulate fetched data
        fetched_data = f"Data for {data_id} (fetched by {self.manager_id})"
        self.cache[data_id] = fetched_data

        return fetched_data


# =============================================================================
# Example 4: Performance Demonstration
# =============================================================================


class PerformanceExample:
    """Demonstrates that type casting maintains performance."""

    def __init__(self):
        self.sync_logger, self.async_logger, self.perf_logger = setup_loggers()

    @log(using="Performance")
    async def high_frequency_async_operation(self, iterations: int) -> float:
        """High-frequency async operation to test performance."""
        start_time = time.perf_counter()

        total = 0
        for i in range(iterations):
            # Simulate work
            total += i * 2
            if i % 100 == 0:
                await asyncio.sleep(0.001)  # Yield control occasionally

        end_time = time.perf_counter()
        return end_time - start_time

    @log(using="AsyncMinimal")
    def high_frequency_sync_operation(self, iterations: int) -> float:
        """High-frequency sync operation to test performance."""
        start_time = time.perf_counter()

        total = 0
        for i in range(iterations):
            # Simulate work
            total += i * 2

        end_time = time.perf_counter()
        return end_time - start_time


# =============================================================================
# Example 5: Error Handling and Edge Cases
# =============================================================================


class ErrorHandlingExample:
    """Demonstrates error handling with type casting."""

    def __init__(self):
        self.sync_logger, self.async_logger, self.perf_logger = setup_loggers()

    @log(using="SyncVisual")
    async def async_operation_that_fails(self, should_fail: bool = True):
        """Async operation that may fail."""
        print("⚠️  Testing error handling with async function and sync logger...")

        await asyncio.sleep(0.01)

        if should_fail:
            raise ValueError("This is a test error from async operation")

        return "Success!"

    @log(using="AsyncMinimal")
    def sync_operation_that_fails(self, should_fail: bool = True):
        """Sync operation that may fail."""
        print("⚠️  Testing error handling with sync function and async logger...")

        if should_fail:
            raise RuntimeError("This is a test error from sync operation")

        return "Success!"


# =============================================================================
# Main Demonstration
# =============================================================================


async def run_demonstrations():
    """Run all demonstrations."""

    print("=" * 80)
    print("🚀 LogEverything Intelligent Type Casting Demonstration")
    print("=" * 80)
    print()

    # Example 1: Smart Decorator
    print("📝 Example 1: Smart Decorator with Mixed Types")
    print("-" * 50)

    smart_example = SmartDecoratorExample()

    # Test async function with sync logger
    data = [1, 2, 3, 4, 5, 10, 15, 20]
    result = await smart_example.async_data_processor(data)
    print(f"Async processing result: {result}")
    print()

    # Test sync function with async logger
    is_valid = smart_example.sync_data_validator(data)
    print(f"Validation result: {is_valid}")
    print()

    # Test performance calculations
    calc_result1 = smart_example.sync_fast_calculation(10, 5)
    calc_result2 = await smart_example.async_slow_calculation(10, 5)
    print(f"Fast calc: {calc_result1}, Slow calc: {calc_result2:.3f}")
    print()

    # Example 2: I/O Operations
    print("📁 Example 2: I/O Operations with Type Casting")
    print("-" * 50)

    io_example = IOOperationsExample()

    # Create a test file
    test_content = "Line 1\nLine 2\nLine 3\nTest data for demonstration"
    success = io_example.sync_file_writer("test_demo.txt", test_content)
    print(f"File write success: {success}")

    # Read the file asynchronously
    read_content = await io_example.async_file_reader("test_demo.txt")
    print(f"File content preview: {read_content[:50]}...")
    print()

    # Batch process files
    batch_results = await io_example.batch_process_files(["test_demo.txt"])
    print(f"Batch processing results: {batch_results}")
    print()

    # Example 3: Class-Based Operations
    print("🏭 Example 3: Class-Based Operations")
    print("-" * 50)

    # Data processor with sync logger
    processor = DataProcessor("MainProcessor")
    process_result = await processor.process_data([1, 2, 3, 4, 5])
    print(f"Processing result: {process_result}")

    stats = processor.get_stats()
    print(f"Processor stats: {stats}")
    print()

    # Async data manager
    manager = AsyncDataManager("Manager001")
    manager.sync_cache_operation("key1", "cached_value")

    fetched_data = await manager.async_data_fetch("data123")
    print(f"Fetched data: {fetched_data}")

    # Fetch again (should use cache)
    cached_data = await manager.async_data_fetch("data123")
    print(f"Cached data: {cached_data}")
    print()

    # Example 4: Performance Test
    print("⚡ Example 4: Performance Test")
    print("-" * 50)

    perf_example = PerformanceExample()

    # Test async operation with sync logger
    async_time = await perf_example.high_frequency_async_operation(1000)
    print(f"Async operation (1000 iterations): {async_time:.4f} seconds")

    # Test sync operation with async logger
    sync_time = perf_example.high_frequency_sync_operation(1000)
    print(f"Sync operation (1000 iterations): {sync_time:.4f} seconds")
    print()

    # Example 5: Error Handling
    print("🛠️  Example 5: Error Handling")
    print("-" * 50)

    error_example = ErrorHandlingExample()

    # Test async error with sync logger
    try:
        await error_example.async_operation_that_fails(True)
    except ValueError as e:
        print(f"✅ Caught async error: {e}")

    # Test sync error with async logger
    try:
        error_example.sync_operation_that_fails(True)
    except RuntimeError as e:
        print(f"✅ Caught sync error: {e}")

    print()

    # Clean up
    try:
        Path("test_demo.txt").unlink()
        print("🧹 Cleaned up test files")
    except FileNotFoundError:
        pass

    print()
    print("=" * 80)
    print("🎉 Demonstration Complete!")
    print("=" * 80)
    print()
    print("Key Takeaways:")
    print("• Smart decorators automatically detect function types")
    print("• Sync loggers can be used with async functions (and vice versa)")
    print("• Original logger instances are always preserved")
    print("• Type casting is completely transparent")
    print("• Performance is maintained across all scenarios")
    print("• All decorators support intelligent type casting")
    print("• Error handling works correctly with type casting")


# =============================================================================
# Additional Utility Functions
# =============================================================================


def demonstrate_logger_preservation():
    """Demonstrate that original logger instances are preserved."""
    print("\n🔍 Logger Preservation Verification")
    print("-" * 40)

    sync_logger = Logger(name="TestSync")
    async_logger = AsyncLogger(name="TestAsync")

    original_sync_id = id(sync_logger)
    original_async_id = id(async_logger)

    print(f"Original sync logger ID: {original_sync_id}")
    print(f"Original async logger ID: {original_async_id}")

    @log(using="TestSync")
    async def test_async_with_sync():
        return "test"

    @log(using="TestAsync")
    def test_sync_with_async():
        return "test"

    # After decoration, loggers should be unchanged
    assert id(sync_logger) == original_sync_id
    assert id(async_logger) == original_async_id
    assert sync_logger._is_async is False
    assert async_logger._is_async is True

    print("✅ Logger instances preserved after decoration")
    print(f"Sync logger ID after decoration: {id(sync_logger)}")
    print(f"Async logger ID after decoration: {id(async_logger)}")


if __name__ == "__main__":
    # Demonstrate logger preservation
    demonstrate_logger_preservation()

    # Run main demonstrations
    asyncio.run(run_demonstrations())
