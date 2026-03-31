"""
Integration tests for the benchmarking system.

This script runs all benchmark components and verifies their integration.
"""

import argparse
import importlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import compare
import optimize

# Import benchmark modules
import run_benchmarks
import utils
import visualize


def test_full_benchmarking_workflow() -> bool:
    """
    Test the complete benchmarking workflow.

    Returns:
        bool: True if all tests pass, False otherwise
    """
    print("\n===== TESTING BENCHMARKING WORKFLOW =====")

    # Create a temporary directory for test results
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Created temporary directory: {temp_dir}")

        # Run a minimal benchmark suite (1 module with reduced iterations)
        print("\n1. Running minimal benchmark suite...")

        # Import one benchmark module and modify its parameters for quicker testing
        try:
            core_module = importlib.import_module("core_logging")
            # Patch the module to use fewer iterations
            core_module.benchmark_simple_logging.__defaults__ = (10, 2)  # type: ignore

            # Run the benchmark
            results = core_module.run_all()

            # Save to the temp directory
            temp_results_dir = os.path.join(temp_dir, "results")
            os.makedirs(temp_results_dir, exist_ok=True)

            # Get the saved benchmark file
            original_path = Path(results["benchmarks"][0]["filepath"])
            filename = original_path.name

            # Copy to our temp directory
            with open(original_path, "r") as f:
                result_data = json.load(f)

            benchmark_path = os.path.join(temp_results_dir, filename)
            with open(benchmark_path, "w") as f:
                json.dump(result_data, f)

            print(f"Saved benchmark results to: {benchmark_path}")

            # Run a second benchmark with slight modifications for comparison
            print("\n2. Running second benchmark for comparison...")
            results2 = core_module.run_all()

            # Save with a different timestamp
            original_path2 = Path(results2["benchmarks"][0]["filepath"])
            with open(original_path2, "r") as f:
                result_data2 = json.load(f)

            # Modify the timestamp to simulate a different run
            result_data2["timestamp"] = "20250612_235959"

            benchmark_path2 = os.path.join(temp_results_dir, "core_logging_20250612_235959.json")
            with open(benchmark_path2, "w") as f:
                json.dump(result_data2, f)

            print(f"Saved second benchmark results to: {benchmark_path2}")

            # Test visualization
            print("\n3. Testing visualization...")
            report_dir = os.path.join(temp_dir, "reports")
            os.makedirs(report_dir, exist_ok=True)

            # Generate a report
            report_path = visualize.generate_benchmark_report(
                results_dir=temp_results_dir, report_dir=report_dir, latest_only=False
            )

            print(f"Generated visualization report: {report_path}")

            # Test comparison
            print("\n4. Testing benchmark comparison...")

            # Compare the two benchmark runs
            comparison = compare.compare_benchmark_runs(
                "core_logging", baseline_index=1, current_index=0, results_dir=temp_results_dir
            )

            print("Comparison results:")
            compare.print_comparison_summary(comparison)

            # Save comparison results
            comparison_path = os.path.join(temp_dir, "comparison.json")
            compare.save_comparison_report(comparison, comparison_path)

            print(f"Saved comparison report to: {comparison_path}")

            # Test optimization
            print("\n5. Testing optimization analysis...")

            # Generate optimization report
            optimization_report = optimize.generate_optimization_report(temp_results_dir)

            print("Optimization recommendations:")
            optimize.print_optimization_report(optimization_report)

            # Save optimization report
            optimization_path = os.path.join(temp_dir, "optimization.json")
            optimize.save_optimization_report(optimization_report, optimization_path)

            print(f"Saved optimization report to: {optimization_path}")

            print("\n===== ALL TESTS PASSED =====")
            return True

        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback

            traceback.print_exc()
            return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the benchmarking system integration")
    args = parser.parse_args()

    success = test_full_benchmarking_workflow()

    if not success:
        sys.exit(1)
