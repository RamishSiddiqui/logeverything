"""
Benchmarks for context managers functionality of LogEverything.
"""

import os
import sys
import tempfile
import time
from typing import Any, Dict, List

# Add parent directory to path to import logeverything
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from benchmarks import utils
from logeverything import Logger
from logeverything.contexts.contexts import LoggingContext

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


def benchmark_log_context(
    iterations: int = 1000, warmup: int = 100, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark the LoggingContext context manager.
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    _create_silent_logger(temp_log)

    # Define the function to benchmark
    def use_log_context():
        with LoggingContext(level="DEBUG"):
            # Simulate some work
            x = 0
            for i in range(100):
                x += i

    # Run the benchmark
    results = utils.run_benchmark(
        use_log_context, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    cleanup_logging_and_file(temp_log)

    return results


def benchmark_timed_context(
    iterations: int = 1000, warmup: int = 100, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark the LoggingContext with different level settings.
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    _create_silent_logger(temp_log)

    # Define the function to benchmark
    def use_timed_context():
        with LoggingContext(level="INFO"):
            # Simulate some work
            x = 0
            for i in range(100):
                x += i

    # Run the benchmark
    results = utils.run_benchmark(
        use_timed_context, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    cleanup_logging_and_file(temp_log)

    return results


def benchmark_capture_logs(
    iterations: int = 100, warmup: int = 10, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark the LoggingContext for capturing logs.
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    logger = _create_silent_logger(temp_log)

    # Define the function to benchmark
    def use_capture_logs():
        with LoggingContext(level="DEBUG"):
            logger.info("This is a test message")
            logger.warning("This is a warning")
            logger.error("This is an error")

    # Run the benchmark
    results = utils.run_benchmark(
        use_capture_logs, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    cleanup_logging_and_file(temp_log)

    return results


def benchmark_nested_contexts(
    iterations: int = 500, warmup: int = 50, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark nested context managers.
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    _create_silent_logger(temp_log)

    # Define the function to benchmark
    def use_nested_contexts():
        with LoggingContext(level="DEBUG"):
            with LoggingContext(level="INFO"):
                # Simulate some work
                x = 0
                for i in range(50):
                    x += i

    # Run the benchmark
    results = utils.run_benchmark(
        use_nested_contexts, iterations=iterations, warmup=warmup, verbose=verbose
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
    Run all context manager benchmarks and return combined results.

    Args:
        verbose: Whether to print verbose output during benchmarking

    Returns:
        Dictionary containing all benchmark results
    """
    if verbose:
        print("Running context manager benchmarks with verbose output...")
    else:
        print("Running context manager benchmarks...")

    benchmarks = []

    if verbose:
        print("  - LoggingContext (DEBUG)")
    benchmarks.append(benchmark_log_context(verbose=verbose))

    if verbose:
        print("  - LoggingContext (INFO)")
    benchmarks.append(benchmark_timed_context(verbose=verbose))

    if verbose:
        print("  - Capture logs")
    benchmarks.append(benchmark_capture_logs(verbose=verbose))

    if verbose:
        print("  - Nested contexts")
    benchmarks.append(benchmark_nested_contexts(verbose=verbose))

    results = {"name": "Context Manager Benchmarks", "benchmarks": benchmarks}

    # Save and print results
    filepath = utils.save_benchmark_results(results, "context_managers", verbose=verbose)

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
