# LogEverything Benchmarks

This directory contains benchmark tests for the LogEverything library. These benchmarks measure the performance of various components of the library to identify areas for optimization.

## Running Benchmarks

To run all benchmarks (with summary output only):

```bash
make benchmark
```

To run all benchmarks with detailed/verbose output:

```bash
make benchmark-verbose
```

To run a specific benchmark module:

```bash
# Run a specific benchmark module (summary output)
make benchmark-core_logging
make benchmark-async_logging
make benchmark-context_managers
make benchmark-decorators
make benchmark-print_capture

# Run with detailed/verbose output
make benchmark-core_logging-verbose
make benchmark-async_logging-verbose
make benchmark-context_managers-verbose
make benchmark-decorators-verbose
make benchmark-print_capture-verbose
```

## Direct Python Execution

You can also run benchmarks directly with Python:

```bash
# Run all benchmarks
python benchmarks/run_benchmarks.py

# Run specific modules
python benchmarks/run_benchmarks.py --modules core_logging

# Run with verbose output
python benchmarks/run_benchmarks.py --verbose
python benchmarks/run_benchmarks.py --modules print_capture --verbose
```

## Analyzing Benchmark Results

The benchmarking system includes tools for visualizing and comparing benchmark results:

```bash
# Generate an HTML report with visualizations
make benchmark-report

# Generate a report with historical data
make benchmark-report-history

# Compare two runs of a specific benchmark
make benchmark-compare MODULE=core_logging

# Visualize a specific benchmark
make benchmark-visualize MODULE=core_logging

# Get optimization recommendations
make benchmark-optimize

# Generate and save an optimization report
make benchmark-optimize-report
```

You can also use the Python scripts directly:

```bash
# Visualize benchmark results
python benchmarks/visualize.py --benchmark core_logging --metric avg_time

# Compare benchmark runs
python benchmarks/compare.py core_logging --baseline 1 --current 0

# List available benchmark files for comparison
python benchmarks/compare.py core_logging --list

# Generate optimization recommendations
python benchmarks/optimize.py --save results/optimization_report.json
```

## Available Benchmark Modules

1. **core_logging.py** - Benchmarks for core logging functionality
   - Simple logging operations
   - Structured logging with additional context
   - Log decorator usage

2. **async_logging.py** - Benchmarks for async logging functionality
   - AsyncQueueHandler performance
   - Async logging setup
   - Concurrent async logging

3. **context_managers.py** - Benchmarks for context managers
   - `log_context` performance
   - `timed_context` performance
   - `capture_logs` performance
   - Nested context managers

4. **decorators.py** - Benchmarks for decorators
   - `@log` decorator performance
   - `@timed` decorator performance
   - `@log_exceptions` decorator performance
   - `@retry` decorator performance
   - `@smart_log` decorator performance
   - Stacked decorators performance

5. **external_loggers.py** - Benchmarks for external logger integration
   - External logger setup
   - Standard Python logging performance (baseline)
   - External logger usage
   - Direct LogEverything usage for comparison

6. **print_capture.py** - Benchmarks for print capture functionality
   - Print with capture enabled
   - Print without capture (baseline)
   - Context manager print capture
   - Start/stop print capture

## Benchmark Results

Benchmark results are saved in the `benchmarks/results` directory as JSON files. Each file includes:
- Benchmark name and timestamp
- System information (platform, Python version, CPU, memory)
- Benchmark metrics (average time, median time, standard deviation, min/max time, operations per second)

## Utilities

The `utils.py` module provides several utility functions for running and managing benchmarks:
- `time_execution()` - Times the execution of a function
- `run_benchmark()` - Runs a benchmark with multiple iterations and warmup
- `save_benchmark_results()` - Saves benchmark results to a JSON file
- `print_benchmark_results()` - Prints benchmark results in a readable format
- `compare_benchmarks()` - Compares benchmark results between runs
- `get_system_info()` - Gets system information for benchmark context
