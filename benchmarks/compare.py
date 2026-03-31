"""
Benchmark comparison utility.

This script helps compare benchmark results between different runs to identify performance changes.
"""

import argparse
import glob
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path to import utils
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import utils


def find_benchmark_files(benchmark_type: str, results_dir: str = "results") -> List[str]:
    """
    Find benchmark result files for a specific benchmark type.

    Args:
        benchmark_type: The benchmark type (e.g., 'core_logging')
        results_dir: Directory to search for results

    Returns:
        List of file paths sorted by date (newest first)
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(base_dir, results_dir)
    pattern = os.path.join(results_path, f"{benchmark_type}_*.json")

    files = glob.glob(pattern)
    # Sort by modification time (newest first)
    return sorted(files, key=lambda f: os.path.getmtime(f), reverse=True)


def load_benchmark(file_path: str) -> Dict[str, Any]:
    """
    Load benchmark results from a file.

    Args:
        file_path: Path to the benchmark results file

    Returns:
        Benchmark results dictionary
    """
    with open(file_path, "r") as f:
        return json.load(f)


def format_change(change_pct: float) -> str:
    """
    Format a percentage change with color indication.

    Args:
        change_pct: Percentage change

    Returns:
        Formatted string with color indication
    """
    if change_pct < 0:
        # Improvement (negative change = faster)
        return f"\033[92m{change_pct:.2%}\033[0m"  # Green
    elif change_pct > 0:
        # Regression (positive change = slower)
        return f"\033[91m+{change_pct:.2%}\033[0m"  # Red
    else:
        # No change
        return f"{change_pct:.2%}"


def print_comparison_summary(comparison: Dict[str, Any]) -> None:
    """
    Print a summary of the comparison results.

    Args:
        comparison: Comparison results from utils.compare_benchmarks()
    """
    if "comparisons" in comparison:
        # Multiple benchmarks comparison
        print("\nCOMPARISON SUMMARY")
        print("=" * 80)
        print(f"Total benchmarks: {comparison['summary']['total']}")
        print(f"Improved: {comparison['summary']['improved']}")
        print(f"Regressed: {comparison['summary']['regressed']}")
        print(f"Unchanged: {comparison['summary']['unchanged']}")
        print("=" * 80)

        # Print detailed comparisons
        print("\nDETAILED COMPARISON")
        print("-" * 80)
        print(f"{'Function':<40} {'Baseline':<12} {'Current':<12} {'Change':<10}")
        print("-" * 80)

        for comp in comparison["comparisons"]:
            func_name = comp["function"]
            baseline = comp["baseline_time"] * 1000  # convert to ms
            current = comp["current_time"] * 1000  # convert to ms
            change_pct = comp["change_pct"]

            print(
                f"{func_name:<40} {baseline:<12.3f}ms {current:<12.3f}ms {format_change(change_pct)}"
            )
    else:
        # Single benchmark comparison
        baseline = comparison["baseline_time"] * 1000  # convert to ms
        current = comparison["current_time"] * 1000  # convert to ms
        change_pct = comparison["change_pct"]

        print("\nSINGLE BENCHMARK COMPARISON")
        print("=" * 80)
        print(f"Function: {comparison['function']}")
        print(f"Baseline: {baseline:.3f} ms")
        print(f"Current:  {current:.3f} ms")
        print(f"Change:   {format_change(change_pct)}")
        print("=" * 80)


def compare_benchmark_runs(
    benchmark_type: str,
    baseline_index: int = 1,
    current_index: int = 0,
    results_dir: str = "results",
    threshold: float = 0.05,
) -> Dict[str, Any]:
    """
    Compare two benchmark runs of the same type.

    Args:
        benchmark_type: The benchmark type (e.g., 'core_logging')
        baseline_index: Index of the baseline benchmark file (1 = previous run)
        current_index: Index of the current benchmark file (0 = latest run)
        results_dir: Directory containing benchmark results
        threshold: Threshold for considering a change significant

    Returns:
        Comparison results
    """
    # Find benchmark files
    files = find_benchmark_files(benchmark_type, results_dir)

    if len(files) <= baseline_index:
        raise ValueError(
            f"Not enough benchmark files found for '{benchmark_type}'. "
            f"Found {len(files)}, but need at least {baseline_index + 1}"
        )

    # Load benchmark results
    baseline_file = files[baseline_index]
    current_file = files[current_index]

    baseline = load_benchmark(baseline_file)
    current = load_benchmark(current_file)

    # Compare benchmarks
    comparison = utils.compare_benchmarks(baseline, current, threshold)

    # Add metadata
    baseline_time = datetime.fromtimestamp(os.path.getmtime(baseline_file)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    current_time = datetime.fromtimestamp(os.path.getmtime(current_file)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    comparison["metadata"] = {
        "benchmark_type": benchmark_type,
        "baseline_file": os.path.basename(baseline_file),
        "current_file": os.path.basename(current_file),
        "baseline_time": baseline_time,
        "current_time": current_time,
    }

    return comparison


def save_comparison_report(comparison: Dict[str, Any], output_file: str) -> None:
    """
    Save a comparison report to a JSON file.

    Args:
        comparison: Comparison results
        output_file: Path to save the report
    """
    with open(output_file, "w") as f:
        json.dump(comparison, f, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare benchmark results between different runs")
    parser.add_argument("benchmark_type", help="Type of benchmark to compare (e.g., core_logging)")
    parser.add_argument(
        "--baseline", type=int, default=1, help="Index of baseline benchmark (1 = previous run)"
    )
    parser.add_argument(
        "--current", type=int, default=0, help="Index of current benchmark (0 = latest run)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.05,
        help="Threshold for considering a change significant (default: 0.05 = 5%%)",
    )
    parser.add_argument(
        "--save", type=str, default=None, help="Save comparison report to the specified file"
    )
    parser.add_argument(
        "--list", action="store_true", help="List available benchmark files for the specified type"
    )

    args = parser.parse_args()

    # Handle list option
    if args.list:
        files = find_benchmark_files(args.benchmark_type)
        print(f"Available benchmark files for '{args.benchmark_type}':")
        for i, file in enumerate(files):
            mtime = datetime.fromtimestamp(os.path.getmtime(file)).strftime("%Y-%m-%d %H:%M:%S")
            print(f"{i}: {os.path.basename(file)} ({mtime})")
        sys.exit(0)

    # Compare benchmarks
    try:
        comparison = compare_benchmark_runs(
            args.benchmark_type, args.baseline, args.current, threshold=args.threshold
        )

        # Print summary
        print(f"\nComparing {args.benchmark_type} benchmarks:")
        print(
            f"Baseline: {comparison['metadata']['baseline_file']} ({comparison['metadata']['baseline_time']})"
        )
        print(
            f"Current:  {comparison['metadata']['current_file']} ({comparison['metadata']['current_time']})"
        )
        print(f"Threshold for significant change: {args.threshold:.2%}")

        print_comparison_summary(comparison)

        # Save report if requested
        if args.save:
            save_comparison_report(comparison, args.save)
            print(f"\nComparison report saved to: {args.save}")

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
