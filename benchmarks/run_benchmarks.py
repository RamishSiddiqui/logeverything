"""
Main runner script for LogEverything benchmarks.
"""

import argparse
import importlib
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

# Add parent directory to path to import logeverything and local modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import benchmarks.utils as utils

# Available benchmark modules
BENCHMARK_MODULES = [
    "core_logging",
    "async_logging",
    "context_managers",
    "decorators",
    "external_loggers",
    "print_capture",
]

# Global verbose flag for benchmarks
VERBOSE = False


def run_benchmarks(modules: Optional[List[str]] = None, verbose: bool = False) -> Dict[str, Any]:
    """
    Run selected benchmark modules.

    Args:
        modules: List of module names to run, or None to run all
        verbose: Whether to print verbose output during benchmarking

    Returns:
        Dict with combined results
    """
    # Set global verbose flag
    global VERBOSE
    VERBOSE = verbose

    start_time = time.time()

    if modules is None:
        modules = BENCHMARK_MODULES

    # Filter modules to ensure they exist
    valid_modules = [m for m in modules if m in BENCHMARK_MODULES]

    if not valid_modules:
        print("No valid benchmark modules specified.")
        print(f"Available modules: {', '.join(BENCHMARK_MODULES)}")
        return {}

    if verbose:
        print(f"Running benchmarks: {', '.join(valid_modules)}")
        print("=" * 80)
    else:
        print("Running benchmarks...")

    all_results = []
    for module_name in valid_modules:
        try:
            # Import the module and run its benchmarks
            module = importlib.import_module(f"benchmarks.{module_name}")
            results = module.run_all(verbose=verbose)
            all_results.append(results)
            if verbose:
                print(f"\nCompleted {module_name} benchmarks.")
                print("-" * 80)
        except Exception as e:
            print(f"\nError running {module_name} benchmarks: {e}")

    end_time = time.time()

    # Combine all results
    combined_results = {
        "name": "LogEverything Complete Benchmark Suite",
        "modules": [r["name"] for r in all_results],
        "runtime": end_time - start_time,
        "timestamp": utils.get_system_info()["date"],
        "system_info": utils.get_system_info(),
    }

    # Save combined results
    filepath = utils.save_benchmark_results(combined_results, "all_benchmarks", verbose=verbose)

    if verbose:
        print("\nAll benchmarks completed!")
        print(f"Total runtime: {combined_results['runtime']:.2f} seconds")

    print(f"Combined results saved to: {filepath}")

    # Print summary of results (verbose mode controlled by parameter)
    for result in all_results:
        # Use non-verbose mode when verbose=False to get just a summary
        utils.print_benchmark_results(result, verbose=verbose)

    return combined_results


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run LogEverything benchmarks")

    parser.add_argument(
        "--modules",
        nargs="+",
        choices=BENCHMARK_MODULES + ["all"],
        default=["all"],
        help="Benchmark modules to run",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output during benchmarking"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Handle 'all' option
    modules = None if "all" in args.modules else args.modules

    run_benchmarks(modules, verbose=args.verbose)
