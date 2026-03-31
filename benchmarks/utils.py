"""
Benchmark utilities for LogEverything.

This module contains utility functions for benchmarking the LogEverything library.
"""

import datetime
import json
import os
import platform
import statistics
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import psutil

# Ensure we can import logeverything
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def get_system_info() -> Dict[str, str]:
    """
    Get information about the system.

    Returns:
        Dict[str, str]: System information
    """
    cpu_info = platform.processor() or "Unknown CPU"
    try:
        cpu_count = psutil.cpu_count(logical=False)
        cpu_logical = psutil.cpu_count(logical=True)
        cpu_details = f"{cpu_info} ({cpu_count} physical cores, {cpu_logical} logical cores)"
    except:
        cpu_details = cpu_info

    mem_info = "Unknown"
    try:
        mem = psutil.virtual_memory()
        mem_info = f"{mem.total / (1024**3):.2f} GB"
    except:
        pass

    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu": cpu_details,
        "memory": mem_info,
        "date": datetime.datetime.now().isoformat(),
    }


def time_execution(func: Callable, *args, **kwargs) -> Tuple[float, Any]:
    """
    Time the execution of a function.

    Args:
        func: Function to time
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        Tuple[float, Any]: Time in seconds and function result
    """
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    return end_time - start_time, result


def run_benchmark(
    func: Callable,
    iterations: int = 1000,
    warmup: int = 100,
    verbose: bool = False,
    *args,
    **kwargs,
) -> Dict[str, Any]:
    """
    Run a benchmark for a function with multiple iterations.

    Args:
        func: Function to benchmark
        iterations: Number of iterations to run
        warmup: Number of warmup iterations
        verbose: Whether to print detailed progress during benchmarking
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        Dict[str, Any]: Benchmark results
    """
    if verbose:
        print(f"  Running benchmark for {func.__name__}")
        print(f"    Warmup: {warmup} iterations")

    # Warmup
    for i in range(warmup):
        func(*args, **kwargs)
        if verbose and i % (warmup // 10 or 1) == 0 and i > 0:
            print(f"    Completed {i}/{warmup} warmup iterations")

    if verbose:
        print(f"    Main benchmark: {iterations} iterations")

    # Actual benchmark
    times = []
    for i in range(iterations):
        execution_time, _ = time_execution(func, *args, **kwargs)
        times.append(execution_time)

        if verbose and i % (iterations // 10 or 1) == 0 and i > 0:
            print(f"    Completed {i}/{iterations} iterations")

    # Calculate statistics
    avg_time = statistics.mean(times)
    median_time = statistics.median(times)
    stdev_time = statistics.stdev(times) if len(times) > 1 else 0
    min_time = min(times)
    max_time = max(times)

    # Return results
    return {
        "function": func.__name__,
        "iterations": iterations,
        "warmup_iterations": warmup,
        "avg_time": avg_time,
        "median_time": median_time,
        "stdev_time": stdev_time,
        "min_time": min_time,
        "max_time": max_time,
        "ops_per_second": 1 / avg_time if avg_time > 0 else 0,
    }


def save_benchmark_results(
    results: Dict[str, Any], name: str, results_dir: str = "results", verbose: bool = False
) -> str:
    """
    Save benchmark results to a JSON file.

    Args:
        results: Benchmark results
        name: Name of the benchmark
        results_dir: Directory to save results in (relative to benchmarks directory)
        verbose: Whether to print detailed information about saving

    Returns:
        str: Path to the saved results file
    """
    # Ensure results directory exists
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(base_dir, results_dir)
    os.makedirs(results_path, exist_ok=True)

    # Add timestamp to results
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    results["timestamp"] = timestamp

    # Add system info
    results["system_info"] = get_system_info()

    # Save results
    filename = f"{name}_{timestamp}.json"
    filepath = os.path.join(results_path, filename)

    with open(filepath, "w") as f:
        json.dump(results, f, indent=2)

    return filepath


def print_benchmark_results(results: Dict[str, Any], verbose: bool = True) -> None:
    """
    Print benchmark results in a readable format.

    Args:
        results: Benchmark results
        verbose: Whether to print detailed results or just a summary
    """
    print("\n" + "=" * 80)
    print(f"BENCHMARK: {results.get('name', 'Unknown')}")
    print("-" * 80)

    # Always print at least basic system info
    if "system_info" in results:
        info = results["system_info"]
        print(
            f"System: {info.get('platform', 'Unknown')}, "
            f"Python: {info.get('python_version', 'Unknown')}, "
            f"Date: {info.get('date', 'Unknown')}"
        )

        # Print more detailed system info if verbose
        if verbose:
            print(f"CPU:            {info.get('cpu', 'Unknown')}")
            print(f"Memory:         {info.get('memory', 'Unknown')}")

    if not verbose:
        print("-" * 80)
        print("SUMMARY (use --verbose for detailed output):")

    # Print benchmark details
    if "benchmarks" in results:
        for benchmark in results["benchmarks"]:
            function_name = benchmark.get("function", "Unknown")
            avg_time_ms = benchmark.get("avg_time", 0) * 1000
            ops_per_sec = benchmark.get("ops_per_second", 0)

            if verbose:
                print(f"Function:       {function_name}")
                print(f"Iterations:     {benchmark.get('iterations', 0)}")
                print(f"Average time:   {avg_time_ms:.4f} ms")
                print(f"Median time:    {benchmark.get('median_time', 0) * 1000:.4f} ms")
                print(f"Std deviation:  {benchmark.get('stdev_time', 0) * 1000:.4f} ms")
                print(f"Min time:       {benchmark.get('min_time', 0) * 1000:.4f} ms")
                print(f"Max time:       {benchmark.get('max_time', 0) * 1000:.4f} ms")
                print(f"Ops per second: {ops_per_sec:.2f}")
                print("-" * 80)
            else:
                # Just print a summary line for each benchmark
                print(f"{function_name}: {avg_time_ms:.4f} ms/op, {ops_per_sec:.2f} ops/sec")
    else:
        function_name = results.get("function", "Unknown")
        avg_time_ms = results.get("avg_time", 0) * 1000
        ops_per_sec = results.get("ops_per_second", 0)

        if verbose:
            print(f"Function:       {function_name}")
            print(f"Iterations:     {results.get('iterations', 0)}")
            print(f"Average time:   {avg_time_ms:.4f} ms")
            print(f"Median time:    {results.get('median_time', 0) * 1000:.4f} ms")
            print(f"Std deviation:  {results.get('stdev_time', 0) * 1000:.4f} ms")
            print(f"Min time:       {results.get('min_time', 0) * 1000:.4f} ms")
            print(f"Max time:       {results.get('max_time', 0) * 1000:.4f} ms")
            print(f"Ops per second: {ops_per_sec:.2f}")
        else:
            print(f"{function_name}: {avg_time_ms:.4f} ms/op, {ops_per_sec:.2f} ops/sec")

    print("=" * 80 + "\n")


def compare_benchmarks(
    baseline: Dict[str, Any], current: Dict[str, Any], threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Compare two benchmark results and determine if there's a significant difference.

    Args:
        baseline: Baseline benchmark results
        current: Current benchmark results
        threshold: Threshold for considering a change significant (as a fraction)

    Returns:
        Dict[str, Any]: Comparison results
    """
    if "benchmarks" in baseline and "benchmarks" in current:
        # Compare multiple benchmarks
        baseline_map = {b["function"]: b for b in baseline["benchmarks"]}
        current_map = {b["function"]: b for b in current["benchmarks"]}

        comparisons = []
        for func_name, baseline_data in baseline_map.items():
            if func_name in current_map:
                current_data = current_map[func_name]
                baseline_time = baseline_data["avg_time"]
                current_time = current_data["avg_time"]

                if baseline_time > 0:
                    change_pct = (current_time - baseline_time) / baseline_time
                    significant = abs(change_pct) > threshold

                    comparisons.append(
                        {
                            "function": func_name,
                            "baseline_time": baseline_time,
                            "current_time": current_time,
                            "change_pct": change_pct,
                            "significant": significant,
                            "improved": change_pct < 0,
                        }
                    )

        return {
            "comparisons": comparisons,
            "summary": {
                "total": len(comparisons),
                "improved": sum(1 for c in comparisons if c["improved"] and c["significant"]),
                "regressed": sum(1 for c in comparisons if not c["improved"] and c["significant"]),
                "unchanged": sum(1 for c in comparisons if not c["significant"]),
            },
        }
    else:
        # Compare single benchmark
        baseline_time = baseline.get("avg_time", 0)
        current_time = current.get("avg_time", 0)

        if baseline_time > 0:
            change_pct = (current_time - baseline_time) / baseline_time
            significant = abs(change_pct) > threshold

            return {
                "function": baseline.get("function", "Unknown"),
                "baseline_time": baseline_time,
                "current_time": current_time,
                "change_pct": change_pct,
                "significant": significant,
                "improved": change_pct < 0,
            }

        return {"error": "Invalid comparison - baseline time is zero"}
