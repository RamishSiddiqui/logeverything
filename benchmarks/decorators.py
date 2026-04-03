"""
Benchmarks for decorator functionality of LogEverything.
"""

import os
import sys
import tempfile
import time
from typing import Any, Dict

# Add parent directory to path to import logeverything
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from benchmarks import utils
from logeverything import Logger
from logeverything.decorators import log, log_function

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


def benchmark_log_decorator(
    iterations: int = 500, warmup: int = 50, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark the @log decorator.
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    _create_silent_logger(temp_log)

    @log_function
    def sample_function(a, b):
        return a + b

    # Define the function to benchmark
    def run_decorated():
        return sample_function(5, 10)

    # Run the benchmark
    results = utils.run_benchmark(
        run_decorated, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    cleanup_logging_and_file(temp_log)

    return results


def benchmark_timed_decorator(
    iterations: int = 500, warmup: int = 50, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark the @log_function decorator with simulated work.
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    _create_silent_logger(temp_log)

    @log_function
    def sample_function(a, b):
        # Add a tiny delay to simulate work
        time.sleep(0.0001)
        return a + b

    # Define the function to benchmark
    def run_decorated():
        return sample_function(5, 10)

    # Run the benchmark
    results = utils.run_benchmark(
        run_decorated, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    cleanup_logging_and_file(temp_log)

    return results


def benchmark_log_exceptions_decorator(
    iterations: int = 500, warmup: int = 50, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark the @log_function decorator (exception path not triggered).
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    _create_silent_logger(temp_log)

    @log_function
    def sample_function(a):
        if a < 0:
            raise ValueError("Negative value")
        return a * 2

    # Define the function to benchmark (not raising an exception)
    def run_decorated():
        return sample_function(5)

    # Run the benchmark
    results = utils.run_benchmark(
        run_decorated, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    cleanup_logging_and_file(temp_log)

    return results


def benchmark_smart_log_decorator(
    iterations: int = 200, warmup: int = 20, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark the @log smart decorator.
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    _create_silent_logger(temp_log)

    @log
    def compute_fibonacci(n, memo=None):
        if memo is None:
            memo = {}
        if n in memo:
            return memo[n]
        if n <= 1:
            return n
        memo[n] = compute_fibonacci(n - 1, memo) + compute_fibonacci(n - 2, memo)
        return memo[n]

    # Define the function to benchmark
    def run_decorated():
        return compute_fibonacci(10)

    # Run the benchmark
    results = utils.run_benchmark(
        run_decorated, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    cleanup_logging_and_file(temp_log)

    return results


def benchmark_stacked_decorators(
    iterations: int = 200, warmup: int = 20, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark stacked decorators.
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    _create_silent_logger(temp_log)

    @log
    @log_function
    def sample_function(a, b):
        # Small delay to simulate work
        time.sleep(0.0001)
        return a + b

    # Define the function to benchmark
    def run_decorated():
        return sample_function(5, 10)

    # Run the benchmark
    results = utils.run_benchmark(
        run_decorated, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    cleanup_logging_and_file(temp_log)

    return results


def run_all(verbose: bool = False) -> Dict[str, Any]:
    """
    Run all decorator benchmarks and return combined results.

    Args:
        verbose: Whether to print verbose output during benchmarking

    Returns:
        Dictionary containing all benchmark results
    """
    if verbose:
        print("Running decorator benchmarks with verbose output...")
    else:
        print("Running decorator benchmarks...")

    benchmarks = []

    if verbose:
        print("  - @log_function decorator")
    benchmarks.append(benchmark_log_decorator(verbose=verbose))

    if verbose:
        print("  - @log_function with work")
    benchmarks.append(benchmark_timed_decorator(verbose=verbose))

    if verbose:
        print("  - @log_function (no exception)")
    benchmarks.append(benchmark_log_exceptions_decorator(verbose=verbose))

    if verbose:
        print("  - @log smart decorator")
    benchmarks.append(benchmark_smart_log_decorator(verbose=verbose))

    if verbose:
        print("  - Stacked decorators")
    benchmarks.append(benchmark_stacked_decorators(verbose=verbose))

    results = {"name": "Decorator Benchmarks", "benchmarks": benchmarks}

    # Save and print results
    filepath = utils.save_benchmark_results(results, "decorators", verbose=verbose)

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
