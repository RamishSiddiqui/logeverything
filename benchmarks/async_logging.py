"""
Benchmarks for async logging functionality of LogEverything.
"""

import asyncio
import os
import sys
import tempfile
from typing import Any, Dict, List

# Add parent directory to path to import logeverything
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from benchmarks import utils
from logeverything import Logger
from logeverything.asyncio.async_logging import (
    AsyncLoggingContext,
    AsyncQueueHandler,
    async_log_function,
    cleanup_all_async_handlers,
)

# Import the verbose flag from run_benchmarks if available
try:
    from benchmarks.run_benchmarks import VERBOSE
except ImportError:
    VERBOSE = False


def _create_silent_logger(temp_log):
    """Create a logger that only writes to a temp file (no console output)."""
    logger = Logger("benchmark", auto_setup=False)
    logger.configure(level="DEBUG", file_path=temp_log.name)
    return logger


def benchmark_async_queue_handler(
    iterations: int = 1000, warmup: int = 100, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark the AsyncQueueHandler for processing log records.
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    logger = _create_silent_logger(temp_log)

    # Define the function to benchmark
    def log_message():
        logger.info("Async benchmark message")

    # Run the benchmark
    results = utils.run_benchmark(
        log_message, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    temp_log.close()
    try:
        os.unlink(temp_log.name)
    except (OSError, PermissionError):
        pass

    return results


def _make_loop_runner(loop, coro_func, *coro_args):
    """Create a benchmark function that reuses an existing event loop.

    Avoids the ~2-5ms overhead of asyncio.run() creating a new event loop per call.
    """

    def runner():
        loop.run_until_complete(coro_func(*coro_args))

    runner.__name__ = coro_func.__name__
    return runner


def benchmark_async_logging_context(
    iterations: int = 100, warmup: int = 10, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark async logging context manager.
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    logger = _create_silent_logger(temp_log)

    async def async_log_operation():
        async with AsyncLoggingContext(level="DEBUG"):
            logger.debug("Async context benchmark message")

    # Reuse a single event loop to measure logging overhead, not loop creation
    loop = asyncio.new_event_loop()
    run_async_context = _make_loop_runner(loop, async_log_operation)

    # Run the benchmark
    results = utils.run_benchmark(
        run_async_context, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    loop.close()
    temp_log.close()
    try:
        os.unlink(temp_log.name)
    except (OSError, PermissionError):
        pass

    return results


def benchmark_async_decorator(
    iterations: int = 100, warmup: int = 10, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark the async function decorator (optimized version without artificial delays).
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    _create_silent_logger(temp_log)

    @async_log_function
    async def async_test_function(x: int, y: int) -> int:
        """Fast async function for benchmarking (no artificial delay)."""
        return x + y

    # Reuse a single event loop to measure decorator overhead, not loop creation
    loop = asyncio.new_event_loop()
    run_async_function = _make_loop_runner(loop, async_test_function, 1, 2)

    # Run the benchmark
    results = utils.run_benchmark(
        run_async_function, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    loop.close()
    temp_log.close()
    try:
        os.unlink(temp_log.name)
    except (OSError, PermissionError):
        pass

    return results


def benchmark_async_decorator_with_delay(
    iterations: int = 50, warmup: int = 5, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark the async function decorator with artificial delay (original version).
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    _create_silent_logger(temp_log)

    @async_log_function
    async def async_test_function_with_delay(x: int, y: int) -> int:
        """Async function with artificial delay for comparison."""
        await asyncio.sleep(0.001)  # 1ms delay
        return x + y

    # Reuse a single event loop to measure decorator + delay overhead
    loop = asyncio.new_event_loop()
    run_async_function = _make_loop_runner(loop, async_test_function_with_delay, 1, 2)

    # Run the benchmark
    results = utils.run_benchmark(
        run_async_function, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    loop.close()
    temp_log.close()
    try:
        os.unlink(temp_log.name)
    except (OSError, PermissionError):
        pass

    return results


def benchmark_async_decorator_no_logging(
    iterations: int = 1000, warmup: int = 100, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark async function with decorator but logging disabled (fast path test).
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    logger = Logger("benchmark", auto_setup=False)
    logger.configure(level="WARNING", file_path=temp_log.name)

    @async_log_function
    async def async_test_function_no_log(x: int, y: int) -> int:
        """Fast async function with logging disabled."""
        return x + y

    # Reuse a single event loop to measure fast-path overhead
    loop = asyncio.new_event_loop()
    run_async_function = _make_loop_runner(loop, async_test_function_no_log, 1, 2)

    # Run the benchmark
    results = utils.run_benchmark(
        run_async_function, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    loop.close()
    temp_log.close()
    try:
        os.unlink(temp_log.name)
    except (OSError, PermissionError):
        pass

    return results


def run_all(verbose: bool = False) -> Dict[str, Any]:
    """
    Run all async logging benchmarks and return combined results.

    Args:
        verbose: Whether to print verbose output during benchmarking

    Returns:
        Dictionary containing all benchmark results
    """
    if verbose:
        print("Running async logging benchmarks with verbose output...")
    else:
        print("Running async logging benchmarks...")

    benchmarks = []

    try:
        if verbose:
            print("  - Async queue handler")
        benchmarks.append(benchmark_async_queue_handler(verbose=verbose))

        if verbose:
            print("  - Async logging context")
        benchmarks.append(benchmark_async_logging_context(verbose=verbose))

        if verbose:
            print("  - Async decorator")
        benchmarks.append(benchmark_async_decorator(verbose=verbose))

        if verbose:
            print("  - Async decorator with delay")
        benchmarks.append(benchmark_async_decorator_with_delay(verbose=verbose))

        if verbose:
            print("  - Async decorator no logging")
        benchmarks.append(benchmark_async_decorator_no_logging(verbose=verbose))

    except Exception as e:
        if verbose:
            print(f"Error in async logging benchmarks: {e}")
        # Add error info to benchmarks list
        benchmarks.append({"error": str(e)})
    finally:
        # Always cleanup async handlers at the end
        cleanup_all_async_handlers()

    results = {"name": "Async Logging Benchmarks", "benchmarks": benchmarks}

    # Save and print results
    filepath = utils.save_benchmark_results(results, "async_logging", verbose=verbose)

    # Print results summary
    print(f"Saved results to {filepath}")
    utils.print_benchmark_results(results, verbose=verbose)

    return results


if __name__ == "__main__":
    results = run_all(verbose=True)
    print("\nAsync Logging Benchmark Results:")
    for benchmark_name, result in results.items():
        if isinstance(result, dict) and "mean_time" in result:
            print(f"  {benchmark_name}: {result['mean_time']:.6f}s avg")
        else:
            print(f"  {benchmark_name}: {result}")
