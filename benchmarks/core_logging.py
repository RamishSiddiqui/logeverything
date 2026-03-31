"""
Benchmarks for core logging functionality of LogEverything.
"""

import logging
import os
import sys
import tempfile
import time
from typing import Any, Dict, List

# Add parent directory to path to import logeverything
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from benchmarks import utils
from logeverything import Logger
from logeverything.decorators import log

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


def benchmark_simple_logging(
    iterations: int = 1000, warmup: int = 100, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark simple logging operations.
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    logger = _create_silent_logger(temp_log)

    # Define the function to benchmark
    def log_message():
        logger.info("This is a benchmark message")

    # Run the benchmark
    results = utils.run_benchmark(
        log_message, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup - close handlers before deleting file
    for handler in logging.getLogger(logger.logger.name).handlers[:]:
        handler.close()
        logging.getLogger(logger.logger.name).removeHandler(handler)

    temp_log.close()
    try:
        os.unlink(temp_log.name)
    except (PermissionError, OSError):
        pass

    return results


def benchmark_structured_logging(
    iterations: int = 100, warmup: int = 10, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark structured logging with additional context.
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    logger = _create_silent_logger(temp_log)

    # Define the function to benchmark
    def log_structured():
        logger.info(
            "Processed item",
            extra={
                "item_id": "12345",
                "status": "complete",
                "processing_time": 532.42,
                "metadata": {"source": "database", "priority": "high"},
            },
        )

    # Run the benchmark
    results = utils.run_benchmark(
        log_structured, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    cleanup_logging_and_file(temp_log)

    return results


def benchmark_log_decorator(
    iterations: int = 1000, warmup: int = 100, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark the @log decorator for timing and logging function calls.
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    _create_silent_logger(temp_log)

    # Define test functions to benchmark
    @log
    def fibonacci(n):
        if n <= 1:
            return n
        return fibonacci(n - 1) + fibonacci(n - 2)

    # Define the function to benchmark (with small n to avoid excessive recursion)
    def run_decorated_function():
        return fibonacci(5)

    # Run the benchmark
    results = utils.run_benchmark(
        run_decorated_function, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    cleanup_logging_and_file(temp_log)

    return results


def cleanup_logging_and_file(temp_log):
    """
    Properly cleanup temporary file.
    This ensures the file is closed before attempting to delete it.
    """
    # Close the temporary file
    temp_log.close()

    # Small delay to ensure file is fully closed
    time.sleep(0.1)

    # Try to delete the temporary file
    try:
        os.unlink(temp_log.name)
    except (OSError, PermissionError):
        # File might still be locked, ignore the error
        pass


def run_all(verbose: bool = False) -> Dict[str, Any]:
    """
    Run all core logging benchmarks and return combined results.

    Args:
        verbose: Whether to print verbose output during benchmarking

    Returns:
        Dictionary containing all benchmark results
    """
    if verbose:
        print("Running core logging benchmarks with verbose output...")
    else:
        print("Running core logging benchmarks...")

    benchmarks = []

    if verbose:
        print("  - Simple logging")
    benchmarks.append(benchmark_simple_logging(verbose=verbose))

    if verbose:
        print("  - Structured logging")
    benchmarks.append(benchmark_structured_logging(verbose=verbose))

    if verbose:
        print("  - Log decorator")
    benchmarks.append(benchmark_log_decorator(verbose=verbose))

    results = {"name": "Core Logging Benchmarks", "benchmarks": benchmarks}

    # Save and print results
    filepath = utils.save_benchmark_results(results, "core_logging", verbose=verbose)

    # Print results summary
    print(f"Saved results to {filepath}")
    utils.print_benchmark_results(results, verbose=verbose)

    return results


if __name__ == "__main__":
    # Check for verbose flag when run directly
    if "--verbose" in sys.argv or "-v" in sys.argv:
        run_all(verbose=True)
    else:
        run_all(verbose=False)
