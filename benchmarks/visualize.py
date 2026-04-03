"""
Visualization utilities for benchmark results.

This module provides functions to create visualizations of benchmark results
using matplotlib and other plotting libraries.
"""

import glob
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np

# Add parent directory to path to import utils
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def load_benchmark_results(filepath: str) -> Dict[str, Any]:
    """
    Load benchmark results from a JSON file.

    Args:
        filepath: Path to the benchmark results JSON file

    Returns:
        Dict containing the benchmark results
    """
    with open(filepath, "r") as f:
        return json.load(f)


def find_benchmark_files(results_dir: str = "results", pattern: str = "*.json") -> List[str]:
    """
    Find benchmark result files in the results directory.

    Args:
        results_dir: Directory to search for results
        pattern: File pattern to match

    Returns:
        List of file paths
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(base_dir, results_dir)
    return glob.glob(os.path.join(results_path, pattern))


def plot_benchmark_comparison(
    results: List[Dict[str, Any]],
    metric: str = "avg_time",
    title: str = "Benchmark Comparison",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Plot a comparison of benchmark results.

    Args:
        results: List of benchmark result dictionaries
        metric: Metric to compare (e.g., 'avg_time', 'ops_per_second')
        title: Title for the plot
        save_path: Path to save the plot, or None to display it

    Returns:
        Matplotlib figure object
    """
    # Extract data for plotting
    data = []

    for result in results:
        if "benchmarks" in result:
            # Multiple benchmarks in one result
            for benchmark in result["benchmarks"]:
                if metric in benchmark:
                    name = f"{result.get('name', 'Unknown')}: {benchmark['function']}"
                    value = benchmark[metric]
                    data.append((name, value))
        else:
            # Single benchmark result
            if metric in result:
                name = result.get("function", "Unknown")
                value = result[metric]
                data.append((name, value))

    # Sort by value
    data.sort(key=lambda x: x[1])

    # Create plot
    fig, ax = plt.subplots(figsize=(10, max(6, len(data) * 0.4)))

    names = [item[0] for item in data]
    values = [item[1] for item in data]

    # Format values for milliseconds if using time metrics
    if metric in ["avg_time", "median_time", "min_time", "max_time"]:
        values_ms = [v * 1000 for v in values]  # Convert to milliseconds
        bars = ax.barh(names, values_ms)
        ax.set_xlabel(f"{metric} (ms)")
    else:
        bars = ax.barh(names, values)
        ax.set_xlabel(metric)

    # Add value annotations
    for i, bar in enumerate(bars):
        if metric in ["avg_time", "median_time", "min_time", "max_time"]:
            # Format time values
            value_text = f"{values[i] * 1000:.3f} ms"
        elif metric == "ops_per_second":
            # Format ops/sec with thousands separators
            value_text = f"{values[i]:,.0f}"
        else:
            value_text = f"{values[i]}"

        ax.text(bar.get_width() * 1.01, bar.get_y() + bar.get_height() / 2, value_text, va="center")

    ax.set_title(title)
    ax.grid(axis="x", linestyle="--", alpha=0.7)

    plt.tight_layout()

    # Save or show the plot
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

    return fig


def plot_time_comparison(results: Dict[str, Any], save_path: Optional[str] = None) -> plt.Figure:
    """
    Create a grouped bar chart comparing time metrics for each benchmark.

    Args:
        results: Benchmark results dictionary with multiple benchmarks
        save_path: Path to save the plot, or None to display it

    Returns:
        Matplotlib figure object
    """
    if "benchmarks" not in results:
        raise ValueError("Expected results with multiple benchmarks")

    benchmarks = results["benchmarks"]

    # Extract data
    names = [b.get("function", "Unknown") for b in benchmarks]
    avg_times = [b.get("avg_time", 0) * 1000 for b in benchmarks]  # ms
    median_times = [b.get("median_time", 0) * 1000 for b in benchmarks]  # ms
    min_times = [b.get("min_time", 0) * 1000 for b in benchmarks]  # ms
    max_times = [b.get("max_time", 0) * 1000 for b in benchmarks]  # ms

    # Set up the figure
    fig, ax = plt.subplots(figsize=(12, max(6, len(names) * 0.6)))

    # Set width of bars
    bar_width = 0.2

    # Set position of bars on x axis
    r1 = np.arange(len(names))
    r2 = [x + bar_width for x in r1]
    r3 = [x + bar_width for x in r2]
    r4 = [x + bar_width for x in r3]

    # Make the plot
    ax.barh(r1, avg_times, bar_width, label="Average")
    ax.barh(r2, median_times, bar_width, label="Median")
    ax.barh(r3, min_times, bar_width, label="Min")
    ax.barh(r4, max_times, bar_width, label="Max")

    # Add labels
    ax.set_xlabel("Time (ms)")
    ax.set_title(f"Time Metrics - {results.get('name', 'Unknown')}")
    ax.set_yticks([r + bar_width * 1.5 for r in range(len(names))])
    ax.set_yticklabels(names)

    # Add a legend
    ax.legend(loc="best")

    # Add grid for readability
    ax.grid(axis="x", linestyle="--", alpha=0.7)

    plt.tight_layout()

    # Save or show the plot
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

    return fig


def plot_benchmark_history(
    benchmark_name: str,
    metric: str = "avg_time",
    results_dir: str = "results",
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Plot benchmark metric history over time for a specific benchmark.

    Args:
        benchmark_name: Base name of the benchmark files
        metric: Metric to track over time
        results_dir: Directory containing the benchmark results
        title: Title for the plot, or None for default
        save_path: Path to save the plot, or None to display it

    Returns:
        Matplotlib figure object
    """
    # Find all matching benchmark files
    pattern = f"{benchmark_name}_*.json"
    files = find_benchmark_files(results_dir, pattern)

    if not files:
        raise ValueError(f"No benchmark files found for '{benchmark_name}'")

    # Extract timestamps and metric values
    data = []

    for file in files:
        result = load_benchmark_results(file)

        # Get timestamp from the result or from the filename
        timestamp_str = result.get(
            "timestamp", os.path.basename(file).split("_", 1)[1].split(".")[0]
        )

        try:
            # Try to parse ISO format
            timestamp = datetime.fromisoformat(timestamp_str)
        except ValueError:
            try:
                # Try to parse from filename format (YYYYMMDD_HHMMSS)
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            except ValueError:
                # Use file modification time as fallback
                timestamp = datetime.fromtimestamp(os.path.getmtime(file))

        # Extract the metric value
        if "benchmarks" in result:
            # Average the metric across all benchmarks
            values = [b.get(metric, 0) for b in result["benchmarks"]]
            avg_value = sum(values) / len(values) if values else 0
            data.append((timestamp, avg_value))
        else:
            value = result.get(metric, 0)
            data.append((timestamp, value))

    # Sort by timestamp
    data.sort(key=lambda x: x[0])

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))

    timestamps = [item[0] for item in data]
    values = [item[1] for item in data]

    # Plot the metric history
    if metric in ["avg_time", "median_time", "min_time", "max_time"]:
        values_ms = [v * 1000 for v in values]  # Convert to milliseconds
        ax.plot(timestamps, values_ms, marker="o")
        ax.set_ylabel(f"{metric} (ms)")
    else:
        ax.plot(timestamps, values, marker="o")
        ax.set_ylabel(metric)

    # Format x-axis for dates
    fig.autofmt_xdate()

    # Set title
    if title is None:
        title = f"{benchmark_name} - {metric} over time"
    ax.set_title(title)

    # Add grid
    ax.grid(True, linestyle="--", alpha=0.7)

    plt.tight_layout()

    # Save or show the plot
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

    return fig


def generate_benchmark_report(
    results_dir: str = "results", report_dir: str = "results/reports", latest_only: bool = True
) -> str:
    """
    Generate a comprehensive report of all benchmarks.

    Args:
        results_dir: Directory containing benchmark results
        report_dir: Directory to save the report and charts
        latest_only: If True, only include the latest result for each benchmark type

    Returns:
        Path to the generated report
    """
    # Ensure report directory exists
    base_dir = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(base_dir, report_dir)
    os.makedirs(report_path, exist_ok=True)

    # Find all benchmark files
    all_files = find_benchmark_files(results_dir)

    # Group by benchmark type
    benchmark_types = {}

    for file in all_files:
        basename = os.path.basename(file)
        benchmark_type = basename.split("_", 1)[0]

        if benchmark_type not in benchmark_types:
            benchmark_types[benchmark_type] = []

        benchmark_types[benchmark_type].append(file)

    # For each type, get the latest file
    latest_files = {}
    all_results = {}

    for benchmark_type, files in benchmark_types.items():
        sorted_files = sorted(files, key=lambda f: os.path.getmtime(f), reverse=True)
        latest_files[benchmark_type] = sorted_files[0]

        # Load all results
        if latest_only:
            # Only load the latest file
            result = load_benchmark_results(sorted_files[0])
            all_results[benchmark_type] = [result]
        else:
            # Load all files for this type
            all_results[benchmark_type] = [load_benchmark_results(f) for f in sorted_files]

    # Generate plots for each benchmark type
    plot_paths = {}

    for benchmark_type, results in all_results.items():
        # Only use the latest result for the time comparison plot
        latest_result = results[0]

        if "benchmarks" in latest_result:
            # Create time comparison plot
            time_plot_path = os.path.join(report_path, f"{benchmark_type}_times.png")
            plot_time_comparison(latest_result, time_plot_path)
            plot_paths[f"{benchmark_type}_times"] = time_plot_path

            # Create operations per second plot
            ops_plot_path = os.path.join(report_path, f"{benchmark_type}_ops.png")
            fig = plt.figure(figsize=(10, 6))

            # Extract function names and ops per second
            functions = [b.get("function", "Unknown") for b in latest_result["benchmarks"]]
            ops = [b.get("ops_per_second", 0) for b in latest_result["benchmarks"]]

            # Sort by ops per second (descending)
            sorted_data = sorted(zip(functions, ops), key=lambda x: x[1], reverse=True)
            functions = [x[0] for x in sorted_data]
            ops = [x[1] for x in sorted_data]

            # Plot bars
            plt.barh(functions, ops)
            plt.xlabel("Operations per second")
            plt.title(f"{benchmark_type} - Operations per second")
            plt.grid(axis="x", linestyle="--", alpha=0.7)

            # Add value annotations
            for i, v in enumerate(ops):
                plt.text(v * 1.01, i, f"{v:,.0f}", va="center")

            plt.tight_layout()
            plt.savefig(ops_plot_path)
            plt.close(fig)

            plot_paths[f"{benchmark_type}_ops"] = ops_plot_path

    # Generate history plots for metrics over time (if latest_only is False)
    if not latest_only:
        for benchmark_type in benchmark_types:
            history_plot_path = os.path.join(report_path, f"{benchmark_type}_history.png")
            try:
                plot_benchmark_history(
                    benchmark_type,
                    "avg_time",
                    results_dir,
                    title=f"{benchmark_type} - Average Time History",
                    save_path=history_plot_path,
                )
                plot_paths[f"{benchmark_type}_history"] = history_plot_path
            except Exception as e:
                print(f"Could not generate history plot for {benchmark_type}: {e}")

    # Generate HTML report
    now = datetime.now()
    report_file = os.path.join(
        report_path, f"benchmark_report_{now.strftime('%Y%m%d_%H%M%S')}.html"
    )

    with open(report_file, "w") as f:
        f.write("<!DOCTYPE html>\n")
        f.write("<html>\n<head>\n")
        f.write("<title>LogEverything Benchmark Report</title>\n")
        f.write("<style>\n")
        f.write("body { font-family: Arial, sans-serif; margin: 20px; }\n")
        f.write("h1, h2 { color: #333; }\n")
        f.write(".container { max-width: 1200px; margin: 0 auto; }\n")
        f.write(".plot { margin: 20px 0; text-align: center; }\n")
        f.write(".plot img { max-width: 100%; height: auto; }\n")
        f.write(".system-info { background-color: #f8f8f8; padding: 10px; border-radius: 5px; }\n")
        f.write(
            ".benchmark-section { margin: 30px 0; border-top: 1px solid #ddd; padding-top: 20px; }\n"
        )
        f.write("</style>\n</head>\n<body>\n")
        f.write("<div class='container'>\n")

        # Header
        f.write("<h1>LogEverything Benchmark Report</h1>\n")
        f.write(f"<p>Generated on {now.strftime('%Y-%m-%d %H:%M:%S')}</p>\n")

        # System info from the latest benchmark
        if latest_files:
            sample_result = load_benchmark_results(list(latest_files.values())[0])
            if "system_info" in sample_result:
                system_info = sample_result["system_info"]
                f.write("<div class='system-info'>\n")
                f.write("<h2>System Information</h2>\n")
                f.write(f"<p>Platform: {system_info.get('platform', 'Unknown')}</p>\n")
                f.write(f"<p>Python: {system_info.get('python_version', 'Unknown')}</p>\n")
                f.write(f"<p>CPU: {system_info.get('cpu', 'Unknown')}</p>\n")
                f.write(f"<p>Memory: {system_info.get('memory', 'Unknown')}</p>\n")
                f.write("</div>\n")

        # Plots for each benchmark type
        for benchmark_type in sorted(benchmark_types.keys()):
            f.write("<div class='benchmark-section'>\n")
            f.write(f"<h2>{benchmark_type}</h2>\n")

            # Time metrics plot
            if f"{benchmark_type}_times" in plot_paths:
                plot_path = os.path.relpath(plot_paths[f"{benchmark_type}_times"], report_path)
                f.write("<div class='plot'>\n")
                f.write("<h3>Time Metrics</h3>\n")
                f.write(f"<img src='{plot_path}' alt='{benchmark_type} Time Metrics'>\n")
                f.write("</div>\n")

            # Operations per second plot
            if f"{benchmark_type}_ops" in plot_paths:
                plot_path = os.path.relpath(plot_paths[f"{benchmark_type}_ops"], report_path)
                f.write("<div class='plot'>\n")
                f.write("<h3>Operations Per Second</h3>\n")
                f.write(f"<img src='{plot_path}' alt='{benchmark_type} Operations Per Second'>\n")
                f.write("</div>\n")

            # History plot
            if f"{benchmark_type}_history" in plot_paths:
                plot_path = os.path.relpath(plot_paths[f"{benchmark_type}_history"], report_path)
                f.write("<div class='plot'>\n")
                f.write("<h3>Performance History</h3>\n")
                f.write(f"<img src='{plot_path}' alt='{benchmark_type} Performance History'>\n")
                f.write("</div>\n")

            f.write("</div>\n")

        f.write("</div>\n")
        f.write("</body>\n</html>")

    return report_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate benchmark visualizations and reports")
    parser.add_argument(
        "--report", action="store_true", help="Generate a comprehensive HTML report"
    )
    parser.add_argument(
        "--history", action="store_true", help="Include benchmark history in the report"
    )
    parser.add_argument("--benchmark", type=str, help="Plot a specific benchmark result")
    parser.add_argument(
        "--metric",
        type=str,
        default="avg_time",
        help="Metric to visualize (avg_time, ops_per_second, etc.)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output during processing"
    )

    args = parser.parse_args()
    # Set verbose mode if requested
    if args.verbose:
        globals()["VERBOSE"] = True
        print("Verbose mode enabled for visualization.")

    if args.report:
        report_path = generate_benchmark_report(latest_only=not args.history)
        print(f"Report generated: {report_path}")

    elif args.benchmark:
        # Find the latest file for this benchmark
        pattern = f"{args.benchmark}_*.json"
        files = find_benchmark_files(pattern=pattern)

        if not files:
            print(f"No benchmark files found for '{args.benchmark}'")
            sys.exit(1)

        # Sort by modification time, newest first
        latest_file = sorted(files, key=lambda f: os.path.getmtime(f), reverse=True)[0]
        result = load_benchmark_results(latest_file)

        if "benchmarks" in result:
            plot_time_comparison(result)
        else:
            print(f"Visualization not available for benchmark: {latest_file}")

    else:
        parser.print_help()
