"""
Benchmarks for print capture functionality in LogEverything.
"""

import os
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional

# Add parent directory to path to import logeverything
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from benchmarks import utils
from logeverything import Logger
from logeverything.capture.print_capture import (
    capture_print,
    disable_print_capture,
    enable_print_capture,
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


def benchmark_print_with_capture(
    iterations: int = 1000, warmup: int = 100, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark print statements with global print capture enabled.

    Args:
        iterations: Number of iterations to run
        warmup: Number of warmup iterations
        verbose: Whether to print verbose output during benchmarking

    Returns:
        Dictionary containing benchmark results
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    logger = _create_silent_logger(temp_log)
    enable_print_capture(logger_name=logger.name)

    # Define the function to benchmark
    def print_message():
        print("This is a captured print message")

    try:
        # Run the benchmark
        results = utils.run_benchmark(
            print_message, iterations=iterations, warmup=warmup, verbose=verbose
        )
    finally:
        # Cleanup
        disable_print_capture()
        cleanup_logging_and_file(temp_log)

    return results


def benchmark_print_without_capture(
    iterations: int = 1000, warmup: int = 100, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark standard print statements without capture for comparison.

    Args:
        iterations: Number of iterations to run
        warmup: Number of warmup iterations
        verbose: Whether to print verbose output during benchmarking

    Returns:
        Dictionary containing benchmark results
    """
    # Redirect stdout to null for clean benchmarking
    original_stdout = sys.stdout
    null_file = open(os.devnull, "w")
    sys.stdout = null_file

    # Define the function to benchmark
    def print_message():
        print("This is a normal print message")

    try:
        # Run the benchmark
        results = utils.run_benchmark(
            print_message, iterations=iterations, warmup=warmup, verbose=verbose
        )
    finally:
        # Restore stdout
        sys.stdout = original_stdout
        null_file.close()

    return results


def benchmark_context_print_capture(
    iterations: int = 500, warmup: int = 50, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark using the context manager for print capture.

    Args:
        iterations: Number of iterations to run
        warmup: Number of warmup iterations
        verbose: Whether to print verbose output during benchmarking

    Returns:
        Dictionary containing benchmark results
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    logger = _create_silent_logger(temp_log)

    # Define the function to benchmark
    def use_capture_context():
        with capture_print(logger_name=logger.name):
            print("This is a print inside a capture context")

    # Run the benchmark
    results = utils.run_benchmark(
        use_capture_context, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    cleanup_logging_and_file(temp_log)

    return results


def benchmark_start_stop_capture(
    iterations: int = 200, warmup: int = 20, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark starting and stopping print capture.

    Args:
        iterations: Number of iterations to run
        warmup: Number of warmup iterations
        verbose: Whether to print verbose output during benchmarking

    Returns:
        Dictionary containing benchmark results
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    logger = _create_silent_logger(temp_log)

    # Define the function to benchmark
    def toggle_capture():
        enable_print_capture(logger_name=logger.name)
        print("This message is captured")
        disable_print_capture()

    # Run the benchmark
    results = utils.run_benchmark(
        toggle_capture, iterations=iterations, warmup=warmup, verbose=verbose
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
    Run all print capture benchmarks and return combined results.

    Args:
        verbose: Whether to print verbose output during benchmarking

    Returns:
        Dictionary containing all benchmark results
    """
    if verbose:
        print("Running print capture benchmarks with verbose output...")
    else:
        print("Running print capture benchmarks...")

    benchmarks = []

    if verbose:
        print("  - Print with capture")
    benchmarks.append(benchmark_print_with_capture(verbose=verbose))

    if verbose:
        print("  - Print without capture (baseline)")
    benchmarks.append(benchmark_print_without_capture(verbose=verbose))

    if verbose:
        print("  - Context print capture")
    benchmarks.append(benchmark_context_print_capture(verbose=verbose))

    if verbose:
        print("  - Start/stop print capture")
    benchmarks.append(benchmark_start_stop_capture(verbose=verbose))

    results = {"name": "Print Capture Benchmarks", "benchmarks": benchmarks}
    # Save results
    filepath = utils.save_benchmark_results(results, "print_capture", verbose=verbose)

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
