#!/usr/bin/env python3
"""
Shared Logger Creation Example
==============================

This example demonstrates LogEverything's automatic shared logger creation
when mixing sync loggers with async functions. This is one of the key
behaviors that users should understand for optimal performance.

Key Learning Points:
- When shared loggers are created (execution time, not decoration time)
- Why you see AsyncLogger auto-detection messages
- Performance characteristics of different logger configurations
- Best practices for mixed sync/async applications

Run this example to see shared logger creation in action!
"""

import asyncio
import time

from logeverything import Logger
from logeverything.asyncio import AsyncLogger
from logeverything.core import _active_loggers
from logeverything.decorators import log


def show_registry(phase):
    """Display the current logger registry."""
    loggers = list(_active_loggers.keys())
    print(f"📊 {phase}: {loggers}")


def demo_1_shared_logger_creation():
    """Demo 1: Watch shared logger creation happen."""
    print("🎯 Demo 1: Shared Logger Creation")
    print("=" * 40)

    # Clear any existing loggers
    _active_loggers.clear()

    # Step 1: Create sync logger with async compatibility
    print("Step 1: Creating sync logger...")
    sync_logger = Logger("demo_app")
    sync_logger.configure(async_mode=True, level="INFO")
    show_registry("After sync logger creation")

    # Step 2: Define async function (no shared logger created yet)
    print("\nStep 2: Defining async function with @log decorator...")

    @log(using="demo_app")
    async def fetch_user_data(user_id):
        """Simulate async database fetch."""
        await asyncio.sleep(0.1)
        return {"user_id": user_id, "name": f"User {user_id}"}

    show_registry("After decorator definition")

    # Step 3: Execute async function (shared logger created NOW)
    print("\nStep 3: EXECUTING async function...")
    print("👀 Watch for AsyncLogger auto-detection messages...")

    async def run_async_function():
        result = await fetch_user_data(123)
        return result

    result = asyncio.run(run_async_function())
    show_registry("After async function execution")

    print(f"✅ Result: {result}")
    print("\n💡 Notice: 'demo_app_async_shared' was created during execution!")


def demo_2_performance_comparison():
    """Demo 2: Compare performance of different logger configurations."""
    print("\n\n🏁 Demo 2: Performance Comparison")
    print("=" * 40)

    # Clear registry
    _active_loggers.clear()

    async def benchmark_logger_creation():
        """Benchmark different logger creation patterns."""

        # Test 1: Pure sync logger creation
        start_time = time.perf_counter()
        sync_logger = Logger("perf_sync")
        sync_creation_time = (time.perf_counter() - start_time) * 1000

        # Test 2: Pure async logger creation
        start_time = time.perf_counter()
        async_logger = AsyncLogger("perf_async")
        async_creation_time = (time.perf_counter() - start_time) * 1000

        # Test 3: Sync logger with async_mode
        start_time = time.perf_counter()
        mixed_logger = Logger("perf_mixed")
        mixed_logger.configure(async_mode=True)
        mixed_creation_time = (time.perf_counter() - start_time) * 1000

        print("📊 Logger Creation Performance:")
        print(f"   Pure Sync Logger:     {sync_creation_time:.2f}ms")
        print(f"   Pure Async Logger:    {async_creation_time:.2f}ms")
        print(f"   Sync + async_mode:    {mixed_creation_time:.2f}ms")

        return sync_logger, async_logger, mixed_logger

    loggers = asyncio.run(benchmark_logger_creation())
    show_registry("After performance test")


def demo_3_best_practices():
    """Demo 3: Best practices for mixed sync/async applications."""
    print("\n\n📋 Demo 3: Best Practices")
    print("=" * 30)

    # Clear registry
    _active_loggers.clear()

    print("✅ BEST PRACTICE: Create logger before decorators")

    # Create logger first (optimal timing)
    app_logger = Logger("best_practice_app")
    app_logger.configure(
        async_mode=True,
        level="INFO",
        profile="production",  # Enable async compatibility
    )

    # Then define decorated functions
    @log(using="best_practice_app")
    def sync_validation(data):
        """Sync validation function."""
        return len(data) > 0

    @log(using="best_practice_app")
    async def async_processing(data):
        """Async processing function."""
        await asyncio.sleep(0.05)
        return f"processed_{data}"

    @log(using="best_practice_app")
    def sync_formatting(result):
        """Sync formatting function."""
        return f"Result: {result.upper()}"

    show_registry("After optimal setup")

    async def run_mixed_pipeline():
        """Run a mixed sync/async pipeline."""
        print("\n🚀 Running mixed sync/async pipeline...")

        # Step 1: Sync validation
        is_valid = sync_validation("test_data")

        # Step 2: Async processing
        processed = await async_processing("test_data")

        # Step 3: Sync formatting
        formatted = sync_formatting(processed)

        return formatted

    result = asyncio.run(run_mixed_pipeline())
    show_registry("After pipeline execution")

    print(f"✅ Pipeline result: {result}")
    print("\n💡 Single shared logger created for all async functions!")


def demo_4_understanding_messages():
    """Demo 4: Understanding AsyncLogger auto-detection messages."""
    print("\n\n🔍 Demo 4: Understanding Auto-Detection Messages")
    print("=" * 50)

    # Clear registry
    _active_loggers.clear()

    print("When you see AsyncLogger auto-detection messages, here's why:")
    print()
    print("1. ✅ You created a sync Logger with async_mode=True")
    print("2. ✅ An async function with @log decorator executes")
    print("3. ✅ LogEverything creates a shared AsyncLogger automatically")
    print("4. ✅ The shared AsyncLogger prints its configuration messages")
    print()
    print("👀 Watch this happen:")

    # Create sync logger
    sync_logger = Logger("message_demo")
    sync_logger.configure(async_mode=True, level="INFO")

    @log(using="message_demo")
    async def trigger_shared_creation():
        """This will trigger shared AsyncLogger creation."""
        return "shared logger created"

    # Execute to trigger the messages
    async def show_messages():
        result = await trigger_shared_creation()
        return result

    print("\n--- AsyncLogger messages will appear below ---")
    result = asyncio.run(show_messages())
    print("--- End of AsyncLogger messages ---\n")

    show_registry("After message demo")
    print("💡 The messages confirm the shared logger was created successfully!")


def demo_5_suppressing_messages():
    """Demo 5: How to suppress auto-detection messages if desired."""
    print("\n\n🔇 Demo 5: Suppressing Auto-Detection Messages")
    print("=" * 45)

    # Clear registry
    _active_loggers.clear()

    print("If you prefer quieter startup, configure explicitly:")

    # Configure logger explicitly to suppress auto-detection
    quiet_logger = Logger("quiet_app")
    quiet_logger.configure(
        level="INFO",
        profile="production",  # Explicit profile prevents auto-detection
        async_mode=True,
    )

    @log(using="quiet_app")
    async def quiet_async_function():
        """Async function with quieter shared logger creation."""
        return "quiet execution"

    print("\n--- Much quieter execution ---")

    async def run_quietly():
        result = await quiet_async_function()
        return result

    result = asyncio.run(run_quietly())
    print("--- End of quiet execution ---\n")

    show_registry("After quiet demo")
    print("✅ Shared logger still created, but with less verbose messages!")


def main():
    """Run all shared logger creation demonstrations."""
    print("🎓 LogEverything: Shared Logger Creation Guide")
    print("=" * 50)
    print()
    print("This example demonstrates the automatic shared logger creation")
    print("that happens when you mix sync loggers with async functions.")
    print()

    demo_1_shared_logger_creation()
    demo_2_performance_comparison()
    demo_3_best_practices()
    demo_4_understanding_messages()
    demo_5_suppressing_messages()

    print("\n🎉 Complete! Key Takeaways:")
    print("=" * 30)
    print("• Shared loggers are created at EXECUTION time, not decoration time")
    print("• AsyncLogger messages are normal when mixing sync/async patterns")
    print("• Creating loggers before decorators prevents temporary logger creation")
    print("• One shared logger is reused for all async functions with the same base name")
    print("• This design provides optimal performance and compatibility")
    print()
    print("📚 For more details, see the documentation:")
    print("   docs/source/user-guide/async-sync-best-practices.rst")


if __name__ == "__main__":
    main()
