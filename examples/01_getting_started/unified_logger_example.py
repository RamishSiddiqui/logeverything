#!/usr/bin/env python3
"""
LogEverything Unified Logger API Example
========================================

This example demonstrates the unified logger API that provides consistent
interfaces across synchronous and asynchronous logging, making it easy
to switch between modes and integrate with different application patterns.

Features demonstrated:
- Unified Logger and AsyncLogger APIs
- Seamless sync/async transitions
- Consistent decorator behavior
- Unified context management
- Cross-compatibility patterns
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Optional, Union

from logeverything import AsyncLogger, Logger, get_logger
from logeverything.decorators import log

# =============================================================================
# 1. UNIFIED LOGGER INTERFACE
# =============================================================================


class UnifiedLoggerWrapper:
    """🔄 Wrapper demonstrating unified logger interface"""

    def __init__(self, name: str, async_mode: bool = False):
        self.name = name
        self.async_mode = async_mode

        if async_mode:
            self.logger: Union[Logger, AsyncLogger] = AsyncLogger(name)
            self.logger_type = "AsyncLogger"
        else:
            self.logger = Logger(name)
            self.logger_type = "Logger"

        self.logger.info(f"🚀 Initialized {self.logger_type} for {name}")

    def log_message(self, level: str, message: str):
        """📝 Unified logging method"""
        getattr(self.logger, level.lower())(message)

    async def async_log_message(self, level: str, message: str):
        """📝 Unified async logging method"""
        if hasattr(self.logger, level.lower()):
            getattr(self.logger, level.lower())(message)


# =============================================================================
# 2. UNIFIED DECORATOR PATTERNS
# =============================================================================

# These decorators work with both sync and async functions
sync_logger = Logger("SyncOperations")
async_logger = AsyncLogger("AsyncOperations")


@log(logger=sync_logger)
def sync_operation(data: str) -> str:
    """⚡ Synchronous operation with unified decorator"""
    time.sleep(0.1)  # Simulate work
    return f"Processed: {data}"


@log(logger=async_logger)
async def async_operation(data: str) -> str:
    """⚡ Asynchronous operation with unified decorator"""
    await asyncio.sleep(0.1)  # Simulate async work
    return f"Async processed: {data}"


@log  # Auto-detection works for both
def auto_detect_sync(value: int) -> int:
    """🤖 Auto-detected sync function"""
    return value * 2


@log  # Auto-detection works for both
async def auto_detect_async(value: int) -> int:
    """🤖 Auto-detected async function"""
    await asyncio.sleep(0.01)
    return value * 3


# =============================================================================
# 3. UNIFIED CONTEXT MANAGERS
# =============================================================================


def demonstrate_sync_contexts():
    """📁 Synchronous context manager demonstration"""
    with sync_logger.context("Sync Main Process"):
        sync_logger.info("ℹ️ Starting sync operations")

        with sync_logger.context("Sync Sub Process"):
            result1 = sync_operation("data1")
            result2 = auto_detect_sync(5)
            sync_logger.info(f"✅ Sync results: {result1}, {result2}")


async def demonstrate_async_contexts():
    """📁 Asynchronous context manager demonstration"""
    async with async_logger.context("Async Main Process"):
        async_logger.info("ℹ️ Starting async operations")

        async with async_logger.context("Async Sub Process"):
            result1 = await async_operation("data1")
            result2 = await auto_detect_async(5)
            async_logger.info(f"✅ Async results: {result1}, {result2}")


# =============================================================================
# 4. UNIFIED ERROR HANDLING
# =============================================================================


@dataclass
class OperationResult:
    """📊 Unified result structure"""

    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: Optional[float] = None


def handle_sync_errors(operation_name: str) -> OperationResult:
    """🚨 Unified sync error handling"""
    start_time = time.perf_counter()

    try:
        sync_logger.info(f"🔄 Starting {operation_name}")

        # Simulate operation that might fail
        if "fail" in operation_name.lower():
            raise ValueError(f"Simulated failure in {operation_name}")

        result = sync_operation(operation_name)
        execution_time = time.perf_counter() - start_time

        sync_logger.info(f"✅ {operation_name} completed in {execution_time:.4f}s")
        return OperationResult(True, result, execution_time=execution_time)

    except Exception as e:
        execution_time = time.perf_counter() - start_time
        error_msg = str(e)
        sync_logger.error(f"❌ {operation_name} failed: {error_msg}")
        return OperationResult(False, None, error_msg, execution_time)


async def handle_async_errors(operation_name: str) -> OperationResult:
    """🚨 Unified async error handling"""
    start_time = time.perf_counter()

    try:
        async_logger.info(f"🔄 Starting {operation_name}")

        # Simulate operation that might fail
        if "fail" in operation_name.lower():
            raise ValueError(f"Simulated failure in {operation_name}")

        result = await async_operation(operation_name)
        execution_time = time.perf_counter() - start_time

        async_logger.info(f"✅ {operation_name} completed in {execution_time:.4f}s")
        return OperationResult(True, result, execution_time=execution_time)

    except Exception as e:
        execution_time = time.perf_counter() - start_time
        error_msg = str(e)
        async_logger.error(f"❌ {operation_name} failed: {error_msg}")
        return OperationResult(False, None, error_msg, execution_time)


# =============================================================================
# 5. UNIFIED PERFORMANCE MONITORING
# =============================================================================


class PerformanceMonitor:
    """📊 Unified performance monitoring for both sync and async"""

    def __init__(self, name: str):
        self.name = name
        self.sync_logger = Logger(f"PerfSync_{name}")
        self.async_logger = AsyncLogger(f"PerfAsync_{name}")

    @log(include_performance=True)
    def monitor_sync_batch(self, items: list) -> dict:
        """📈 Monitor synchronous batch operations"""
        results = {}

        with self.sync_logger.context("Sync Batch Processing"):
            for i, item in enumerate(items):
                start = time.perf_counter()
                result = sync_operation(f"item_{item}")
                duration = time.perf_counter() - start

                results[item] = {"result": result, "duration": duration}

                self.sync_logger.info(f"📊 Item {i+1}/{len(items)}: {duration:.4f}s")

        return results

    @log(include_performance=True)
    async def monitor_async_batch(self, items: list) -> dict:
        """📈 Monitor asynchronous batch operations"""
        results = {}

        async with self.async_logger.context("Async Batch Processing"):
            # Process concurrently for better performance
            tasks = []
            for item in items:
                tasks.append(self._process_async_item(item))

            completed_results = await asyncio.gather(*tasks)

            for item, result in zip(items, completed_results):
                results[item] = result
                self.async_logger.info(f"📊 Async item processed: {result['duration']:.4f}s")

        return results

    async def _process_async_item(self, item: str) -> dict:
        """🔄 Helper for processing async items"""
        start = time.perf_counter()
        result = await async_operation(f"item_{item}")
        duration = time.perf_counter() - start

        return {"result": result, "duration": duration}


# =============================================================================
# 6. UNIFIED CONFIGURATION PATTERNS
# =============================================================================


def create_unified_loggers(base_name: str) -> dict:
    """⚙️ Create matching sync and async loggers with unified config"""

    # Common configuration
    config = {
        "console": True,
        "file_path": f"logs/{base_name.lower()}.log",
        "json_file": f"logs/{base_name.lower()}.json",
        "format": "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    }

    # Create both types with same config
    sync_logger = Logger(f"{base_name}_Sync", **config)
    async_logger = AsyncLogger(f"{base_name}_Async", **config)

    return {"sync": sync_logger, "async": async_logger}


# =============================================================================
# 7. MIGRATION HELPER
# =============================================================================


class SyncToAsyncMigrationHelper:
    """🔄 Helper class for migrating from sync to async logging"""

    def __init__(self, logger_name: str):
        self.logger_name = logger_name
        self.sync_logger = Logger(f"{logger_name}_Sync")
        self.async_logger = AsyncLogger(f"{logger_name}_Async")

    def log_both(self, level: str, message: str):
        """📝 Log to both sync and async loggers during migration"""
        # Log to sync logger
        getattr(self.sync_logger, level)(f"[SYNC] {message}")

        # Log to async logger
        getattr(self.async_logger, level)(f"[ASYNC] {message}")

    @log
    def sync_method(self, data: str) -> str:
        """⚡ Sync method being migrated"""
        self.log_both("info", f"Processing sync: {data}")
        return f"Sync: {data}"

    @log
    async def async_method(self, data: str) -> str:
        """⚡ Equivalent async method"""
        self.log_both("info", f"Processing async: {data}")
        await asyncio.sleep(0.01)  # Simulate async work
        return f"Async: {data}"


# =============================================================================
# 8. MAIN DEMONSTRATION
# =============================================================================


async def main():
    """🚀 Comprehensive unified logger demonstration"""
    print("🔵 LogEverything Unified Logger API Demo")
    print("=" * 50)

    # 1. Unified wrapper demonstration
    print("\n1️⃣ Unified Logger Wrapper:")
    sync_wrapper = UnifiedLoggerWrapper("SyncApp", async_mode=False)
    async_wrapper = UnifiedLoggerWrapper("AsyncApp", async_mode=True)

    sync_wrapper.log_message("info", "ℹ️ Sync wrapper message")
    await async_wrapper.async_log_message("info", "ℹ️ Async wrapper message")

    # 2. Context manager demonstrations
    print("\n2️⃣ Unified Context Managers:")
    demonstrate_sync_contexts()
    await demonstrate_async_contexts()

    # 3. Error handling
    print("\n3️⃣ Unified Error Handling:")
    sync_result = handle_sync_errors("TestOperation")
    async_result = await handle_async_errors("TestOperation")
    print(f"   📊 Sync result: {sync_result.success}")
    print(f"   📊 Async result: {async_result.success}")

    # 4. Performance monitoring
    print("\n4️⃣ Unified Performance Monitoring:")
    monitor = PerformanceMonitor("BatchTest")

    test_items = ["A", "B", "C"]
    sync_results = monitor.monitor_sync_batch(test_items)
    async_results = await monitor.monitor_async_batch(test_items)

    print(f"   📈 Sync batch: {len(sync_results)} items processed")
    print(f"   📈 Async batch: {len(async_results)} items processed")

    # 5. Migration helper
    print("\n5️⃣ Sync-to-Async Migration:")
    migration_helper = SyncToAsyncMigrationHelper("MigrationTest")

    sync_result = migration_helper.sync_method("test_data")
    async_result = await migration_helper.async_method("test_data")

    print(f"   🔄 Migration: {sync_result} -> {async_result}")

    # 6. Unified configuration
    print("\n6️⃣ Unified Configuration:")
    unified_loggers = create_unified_loggers("UnifiedTest")

    unified_loggers["sync"].info("ℹ️ Unified sync logger")
    unified_loggers["async"].info("ℹ️ Unified async logger")


if __name__ == "__main__":
    print("🔵 Starting unified logger API demonstration...")
    asyncio.run(main())
    print("\n✅ Unified logger demonstration complete!")
    print("📚 This API makes it easy to work with both sync and async logging.")
