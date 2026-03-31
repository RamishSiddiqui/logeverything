"""
Optimization strategies for LogEverything based on benchmark results.

This module provides functions to analyze benchmark results and suggest
optimization strategies for different components of the library.
"""

import glob
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path to import utils
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import utils


def load_latest_benchmarks(results_dir: str = "results") -> Dict[str, Dict]:
    """
    Load the latest benchmark results for each benchmark type.

    Args:
        results_dir: Directory containing benchmark results

    Returns:
        Dict mapping benchmark type to the latest benchmark results
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(base_dir, results_dir)
    all_files = glob.glob(os.path.join(results_path, "*.json"))

    # Group files by benchmark type
    grouped_files = {}
    for file in all_files:
        base_name = os.path.basename(file)
        benchmark_type = base_name.split("_", 1)[0]

        if benchmark_type not in grouped_files:
            grouped_files[benchmark_type] = []

        grouped_files[benchmark_type].append(file)

    # Get the latest file for each type
    latest_benchmarks = {}
    for benchmark_type, files in grouped_files.items():
        latest_file = max(files, key=os.path.getmtime)
        with open(latest_file, "r") as f:
            latest_benchmarks[benchmark_type] = json.load(f)

    return latest_benchmarks


def find_slowest_components(
    benchmarks: Dict[str, Dict], n: int = 5
) -> List[Tuple[str, str, float]]:
    """
    Find the slowest components across all benchmarks.

    Args:
        benchmarks: Dict mapping benchmark type to benchmark results
        n: Number of slow components to return

    Returns:
        List of (benchmark_type, function_name, avg_time) tuples
    """
    slow_components = []

    for benchmark_type, results in benchmarks.items():
        if "benchmarks" in results:
            for benchmark in results["benchmarks"]:
                function_name = benchmark.get("function", "Unknown")
                avg_time = benchmark.get("avg_time", 0)

                slow_components.append((benchmark_type, function_name, avg_time))

    # Sort by average time (descending)
    slow_components.sort(key=lambda x: x[2], reverse=True)

    # Return top N slowest components
    return slow_components[:n]


def analyze_optimization_opportunities(benchmarks: Dict[str, Dict]) -> Dict[str, List[str]]:
    """
    Analyze benchmark results and suggest optimization opportunities.

    Args:
        benchmarks: Dict mapping benchmark type to benchmark results

    Returns:
        Dict mapping component areas to optimization suggestions
    """
    suggestions = {
        "async_logging": [],
        "core_logging": [],
        "context_managers": [],
        "decorators": [],
        "external_loggers": [],
        "print_capture": [],
        "general": [],
    }

    # Find the slowest components
    slow_components = find_slowest_components(benchmarks)

    # Add general suggestions
    suggestions["general"] = [
        "Consider implementing a thread pool for background tasks",
        "Use caching for frequently accessed configuration",
        "Optimize string formatting in logging calls",
        "Review thread synchronization mechanisms",
        "Consider using more efficient data structures for message handling",
    ]

    # Analyze async_logging performance
    if "async_logging" in benchmarks:
        async_results = benchmarks["async_logging"]
        if "benchmarks" in async_results:
            async_benchmarks = {b["function"]: b for b in async_results["benchmarks"]}

            if "benchmark_async_queue_handler" in async_benchmarks:
                queue_time = async_benchmarks["benchmark_async_queue_handler"].get("avg_time", 0)
                if queue_time > 0.0005:  # More than 0.5ms
                    suggestions["async_logging"].append(
                        "Optimize AsyncQueueHandler by using a more efficient queue implementation"
                    )
                    suggestions["async_logging"].append(
                        "Consider implementing a thread pool for the AsyncQueueHandler"
                    )

            if "benchmark_concurrent_async_logging" in async_benchmarks:
                concurrent_time = async_benchmarks["benchmark_concurrent_async_logging"].get(
                    "avg_time", 0
                )
                if concurrent_time > 0.05:  # More than 50ms
                    suggestions["async_logging"].append(
                        "Improve concurrent async logging performance by optimizing queue processing"
                    )
                    suggestions["async_logging"].append(
                        "Consider using asyncio.Queue instead of standard Queue for async operations"
                    )

    # Analyze core_logging performance
    if "core_logging" in benchmarks:
        core_results = benchmarks["core_logging"]
        if "benchmarks" in core_results:
            core_benchmarks = {b["function"]: b for b in core_results["benchmarks"]}

            if "benchmark_structured_logging" in core_benchmarks:
                struct_time = core_benchmarks["benchmark_structured_logging"].get("avg_time", 0)
                if struct_time > 0.0005:  # More than 0.5ms
                    suggestions["core_logging"].append(
                        "Optimize structured logging by using lazy evaluation of expensive objects"
                    )
                    suggestions["core_logging"].append(
                        "Consider caching serialized representations of common objects"
                    )

            if "benchmark_log_decorator" in core_benchmarks:
                decorator_time = core_benchmarks["benchmark_log_decorator"].get("avg_time", 0)
                if decorator_time > 0.001:  # More than 1ms
                    suggestions["core_logging"].append(
                        "Optimize the @log decorator to reduce overhead"
                    )
                    suggestions["core_logging"].append(
                        "Implement selective logging for decorated functions based on log level"
                    )

    # Analyze context_managers performance
    if "context_managers" in benchmarks:
        ctx_results = benchmarks["context_managers"]
        if "benchmarks" in ctx_results:
            ctx_benchmarks = {b["function"]: b for b in ctx_results["benchmarks"]}

            if "benchmark_timed_context" in ctx_benchmarks:
                timed_ctx_time = ctx_benchmarks["benchmark_timed_context"].get("avg_time", 0)
                if timed_ctx_time > 0.0005:  # More than 0.5ms
                    suggestions["context_managers"].append(
                        "Optimize timed_context by reducing the overhead of time tracking"
                    )

            if "benchmark_capture_logs" in ctx_benchmarks:
                capture_time = ctx_benchmarks["benchmark_capture_logs"].get("avg_time", 0)
                if capture_time > 0.001:  # More than 1ms
                    suggestions["context_managers"].append(
                        "Improve capture_logs performance by using a more efficient log capture mechanism"
                    )

    # Analyze decorators performance
    if "decorators" in benchmarks:
        dec_results = benchmarks["decorators"]
        if "benchmarks" in dec_results:
            dec_benchmarks = {b["function"]: b for b in dec_results["benchmarks"]}

            if "benchmark_smart_log_decorator" in dec_benchmarks:
                smart_log_time = dec_benchmarks["benchmark_smart_log_decorator"].get("avg_time", 0)
                if smart_log_time > 0.001:  # More than 1ms
                    suggestions["decorators"].append(
                        "Optimize smart_log decorator by implementing caching of analyzed function signatures"
                    )

            if "benchmark_stacked_decorators" in dec_benchmarks:
                stacked_time = dec_benchmarks["benchmark_stacked_decorators"].get("avg_time", 0)
                if stacked_time > 0.002:  # More than 2ms
                    suggestions["decorators"].append(
                        "Reduce overhead in stacked decorators by combining decorator functionality"
                    )
                    suggestions["decorators"].append(
                        "Implement a unified decorator that combines logging, timing, and exception handling"
                    )

    # Analyze print_capture performance
    if "print_capture" in benchmarks:
        print_results = benchmarks["print_capture"]
        if "benchmarks" in print_results:
            print_benchmarks = {b["function"]: b for b in print_results["benchmarks"]}

            if (
                "benchmark_print_with_capture" in print_benchmarks
                and "benchmark_print_without_capture" in print_benchmarks
            ):
                with_capture = print_benchmarks["benchmark_print_with_capture"].get("avg_time", 0)
                without_capture = print_benchmarks["benchmark_print_without_capture"].get(
                    "avg_time", 0
                )

                if with_capture > without_capture * 2:  # More than 2x slower
                    suggestions["print_capture"].append(
                        "Optimize print capture mechanism to reduce overhead"
                    )
                    suggestions["print_capture"].append(
                        "Consider implementing a more efficient sys.stdout replacement"
                    )

    # Analyze external_loggers performance
    if "external_loggers" in benchmarks:
        ext_results = benchmarks["external_loggers"]
        if "benchmarks" in ext_results:
            ext_benchmarks = {b["function"]: b for b in ext_results["benchmarks"]}

            if (
                "benchmark_external_logger_usage" in ext_benchmarks
                and "benchmark_direct_logeverything" in ext_benchmarks
            ):
                ext_time = ext_benchmarks["benchmark_external_logger_usage"].get("avg_time", 0)
                direct_time = ext_benchmarks["benchmark_direct_logeverything"].get("avg_time", 0)

                if ext_time > direct_time * 1.5:  # More than 50% slower
                    suggestions["external_loggers"].append(
                        "Optimize external logger integration to reduce overhead"
                    )
                    suggestions["external_loggers"].append(
                        "Consider caching logger lookups for external loggers"
                    )

    return suggestions


def generate_optimization_report(results_dir: str = "results") -> Dict[str, Any]:
    """
    Generate a comprehensive optimization report based on benchmark results.

    Args:
        results_dir: Directory containing benchmark results

    Returns:
        Dict containing the optimization report
    """
    # Load latest benchmarks
    benchmarks = load_latest_benchmarks(results_dir)

    if not benchmarks:
        return {"error": "No benchmark results found", "recommendations": []}

    # Find slowest components
    slow_components = find_slowest_components(benchmarks, n=10)

    # Get optimization suggestions
    suggestions = analyze_optimization_opportunities(benchmarks)

    # Create prioritized recommendations
    prioritized_recommendations = []

    # Add recommendations for the slowest components
    for benchmark_type, function_name, avg_time in slow_components:
        component_category = benchmark_type.replace("_", " ").title()
        function_display = function_name.replace("benchmark_", "")

        # Add specific recommendations for this component
        component_suggestions = []
        if benchmark_type in suggestions and suggestions[benchmark_type]:
            for suggestion in suggestions[benchmark_type]:
                if function_display in suggestion.lower() or function_name in suggestion.lower():
                    component_suggestions.append(suggestion)

        # If no specific suggestions, add general ones
        if not component_suggestions and benchmark_type in suggestions:
            component_suggestions = suggestions[benchmark_type][:2]  # Take top 2

        prioritized_recommendations.append(
            {
                "component": component_category,
                "function": function_display,
                "avg_time": avg_time,
                "avg_time_ms": avg_time * 1000,  # Convert to ms
                "suggestions": component_suggestions,
            }
        )

    # Add general recommendations
    general_recommendations = {"general": suggestions["general"]}

    # Create the final report
    report = {
        "timestamp": utils.get_system_info()["date"],
        "system_info": utils.get_system_info(),
        "slowest_components": prioritized_recommendations,
        "general_recommendations": general_recommendations,
        "component_specific_recommendations": {
            k: v for k, v in suggestions.items() if k != "general" and v
        },
    }

    return report


def print_optimization_report(report: Dict[str, Any]) -> None:
    """
    Print an optimization report in a readable format.

    Args:
        report: Optimization report dict
    """
    if "error" in report:
        print(f"Error: {report['error']}")
        return

    print("\n" + "=" * 80)
    print("LOGEVERYTHING OPTIMIZATION REPORT")
    print("=" * 80)

    # Print system info
    if "system_info" in report:
        info = report["system_info"]
        print(f"Generated on: {info.get('date', 'Unknown')}")
        print(f"Platform: {info.get('platform', 'Unknown')}")
        print(f"Python: {info.get('python_version', 'Unknown')}")

    print("\n" + "=" * 80)
    print("PERFORMANCE HOTSPOTS")
    print("=" * 80)

    # Print slowest components
    if "slowest_components" in report:
        for i, comp in enumerate(report["slowest_components"], 1):
            print(f"{i}. {comp['component']}: {comp['function']}")
            print(f"   Average time: {comp['avg_time_ms']:.3f} ms")

            if comp["suggestions"]:
                print("   Suggested optimizations:")
                for suggestion in comp["suggestions"]:
                    print(f"   - {suggestion}")

            print()

    print("=" * 80)
    print("GENERAL OPTIMIZATION RECOMMENDATIONS")
    print("=" * 80)

    # Print general recommendations
    if "general_recommendations" in report and "general" in report["general_recommendations"]:
        for suggestion in report["general_recommendations"]["general"]:
            print(f"- {suggestion}")

    print("\n" + "=" * 80)
    print("COMPONENT-SPECIFIC RECOMMENDATIONS")
    print("=" * 80)

    # Print component-specific recommendations
    if "component_specific_recommendations" in report:
        for component, suggestions in report["component_specific_recommendations"].items():
            if suggestions:
                print(f"\n{component.replace('_', ' ').title()}:")
                for suggestion in suggestions:
                    print(f"- {suggestion}")

    print("\n" + "=" * 80)


def save_optimization_report(report: Dict[str, Any], output_file: str) -> None:
    """
    Save an optimization report to a JSON file.

    Args:
        report: Optimization report dict
        output_file: Path to save the report
    """
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate optimization recommendations based on benchmark results"
    )
    parser.add_argument(
        "--save", type=str, default=None, help="Save optimization report to the specified file"
    )
    parser.add_argument(
        "--results-dir", type=str, default="results", help="Directory containing benchmark results"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output during processing"
    )

    args = parser.parse_args()
    # Generate report
    report = generate_optimization_report(args.results_dir)

    # Print report
    print_optimization_report(report)

    # Save report if requested
    if args.save:
        save_optimization_report(report, args.save)
        print(f"\nOptimization report saved to: {args.save}")

    # Pass verbose flag to global context
    if args.verbose:
        # Add to a global variable that could be imported by other modules
        globals()["VERBOSE"] = True
        print("Verbose mode enabled for optimization processing.")
