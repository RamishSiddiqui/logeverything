"""
Benchmarks for external logger integration in LogEverything.
"""

import logging
import logging as py_logging
import os
import sys
import tempfile
import time
from typing import Any, Dict

# Add parent directory to path to import logeverything
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from benchmarks import utils
from logeverything import Logger

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
    Properly cleanup both LogEverything and standard Python logging handlers and temporary file.
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


def benchmark_external_logger_setup(
    iterations: int = 100, warmup: int = 10, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark setting up external loggers.
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    _create_silent_logger(temp_log)

    # Define the function to benchmark
    def setup_external():
        return logging.getLogger("ext_benchmark")

    # Run the benchmark
    results = utils.run_benchmark(
        setup_external, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    cleanup_logging_and_file(temp_log)

    return results


def benchmark_standard_logging(
    iterations: int = 1000, warmup: int = 100, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark standard Python logging as a baseline.
    """
    # Configure standard Python logging
    temp_log = tempfile.NamedTemporaryFile(delete=False)

    py_logging.basicConfig(
        level=py_logging.INFO,
        filename=temp_log.name,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = py_logging.getLogger("std_benchmark")

    # Define the function to benchmark
    def log_message():
        logger.info("This is a standard logging message")

    # Run the benchmark
    results = utils.run_benchmark(
        log_message, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    cleanup_logging_and_file(temp_log)

    return results


def benchmark_external_logger_usage(
    iterations: int = 1000, warmup: int = 100, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark using an external logger that's been integrated with LogEverything.
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    _create_silent_logger(temp_log)

    # Setup the external logger
    logger = logging.getLogger("ext_benchmark")

    # Define the function to benchmark
    def log_message():
        logger.info("This is an external logger message")

    # Run the benchmark
    results = utils.run_benchmark(
        log_message, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    cleanup_logging_and_file(temp_log)

    return results


def benchmark_direct_logeverything(
    iterations: int = 1000, warmup: int = 100, verbose: bool = False
) -> Dict[str, Any]:
    """
    Benchmark direct LogEverything logging for comparison.
    """
    temp_log = tempfile.NamedTemporaryFile(delete=False)
    logger = _create_silent_logger(temp_log)

    # Define the function to benchmark
    def log_message():
        logger.info("This is a LogEverything message")

    # Run the benchmark
    results = utils.run_benchmark(
        log_message, iterations=iterations, warmup=warmup, verbose=verbose
    )

    # Cleanup
    cleanup_logging_and_file(temp_log)

    return results


def run_all(verbose: bool = False) -> Dict[str, Any]:
    """
    Run all external logger benchmarks and return combined results.

    Args:
        verbose: Whether to print verbose output during benchmarking

    Returns:
        Dictionary containing all benchmark results
    """
    if verbose:
        print("Running external logger benchmarks with verbose output...")
    else:
        print("Running external logger benchmarks...")

    benchmarks = []

    if verbose:
        print("  - External logger setup")
    benchmarks.append(benchmark_external_logger_setup(verbose=verbose))

    if verbose:
        print("  - Standard Python logging")
    benchmarks.append(benchmark_standard_logging(verbose=verbose))

    if verbose:
        print("  - External logger usage")
    benchmarks.append(benchmark_external_logger_usage(verbose=verbose))

    if verbose:
        print("  - Direct LogEverything")
    benchmarks.append(benchmark_direct_logeverything(verbose=verbose))

    results = {"name": "External Logger Benchmarks", "benchmarks": benchmarks}

    # Save and print results
    filepath = utils.save_benchmark_results(results, "external_loggers", verbose=verbose)

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
