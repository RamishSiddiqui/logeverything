#!/usr/bin/env python3
"""
Comprehensive benchmarking suite for LogEverything performance testing.
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List

import logeverything


class LogEverythingBenchmark:
    """Comprehensive benchmark suite for LogEverything."""

    def __init__(self):
        self.results: Dict[str, Any] = {}

    def benchmark_basic_logging(self, iterations: int = 10000) -> Dict[str, float]:
        """Benchmark basic logging performance."""
        logeverything.setup_logging(
            level="INFO", handlers=["console"], capture_print=False, visual_mode=False
        )

        logger = logeverything.get_logger("benchmark")

        # Warm up
        for _ in range(100):
            logger.info("warmup")

        # Benchmark
        start = time.time()
        for i in range(iterations):
            logger.info(f"Message {i}")
        end = time.time()

        total_time = end - start
        return {
            "total_time": total_time,
            "ops_per_second": iterations / total_time,
            "ms_per_op": (total_time / iterations) * 1000,
        }

    def benchmark_decorator_performance(self, iterations: int = 1000) -> Dict[str, float]:
        """Benchmark decorator performance."""
        logeverything.setup_logging(
            level="INFO", handlers=["console"], log_entry_exit=True, visual_mode=False
        )

        @logeverything.log
        def simple_function(x: int) -> int:
            return x * 2

        # Warm up
        for _ in range(10):
            simple_function(42)

        # Benchmark
        start = time.time()
        for i in range(iterations):
            simple_function(i)
        end = time.time()

        total_time = end - start
        return {
            "total_time": total_time,
            "ops_per_second": iterations / total_time,
            "ms_per_op": (total_time / iterations) * 1000,
        }

    def benchmark_print_capture(self, iterations: int = 10000) -> Dict[str, float]:
        """Benchmark print capture performance."""
        logeverything.setup_logging(
            level="INFO", handlers=["console"], capture_print=True, visual_mode=False
        )

        # Warm up
        for _ in range(100):
            print("warmup")

        # Benchmark
        start = time.time()
        for i in range(iterations):
            print(f"Print message {i}")
        end = time.time()

        total_time = end - start
        return {
            "total_time": total_time,
            "ops_per_second": iterations / total_time,
            "ms_per_op": (total_time / iterations) * 1000,
        }

    async def benchmark_async_logging(self, iterations: int = 1000) -> Dict[str, float]:
        """Benchmark async logging performance."""
        logeverything.setup_logging(
            level="INFO", async_mode=True, handlers=["async_queue"], visual_mode=False
        )

        @logeverything.async_log_function
        async def async_function(x: int) -> int:
            await asyncio.sleep(0.001)  # Simulate async work
            return x * 2

        # Warm up
        for _ in range(10):
            await async_function(42)

        # Benchmark
        start = time.time()
        tasks = [async_function(i) for i in range(iterations)]
        await asyncio.gather(*tasks)
        end = time.time()

        total_time = end - start
        return {
            "total_time": total_time,
            "ops_per_second": iterations / total_time,
            "ms_per_op": (total_time / iterations) * 1000,
        }

    def benchmark_concurrent_logging(
        self, num_threads: int = 10, ops_per_thread: int = 1000
    ) -> Dict[str, float]:
        """Benchmark concurrent logging performance."""
        logeverything.setup_logging(level="INFO", handlers=["console"], visual_mode=False)

        def worker_function(worker_id: int):
            logger = logeverything.get_logger(f"worker_{worker_id}")
            for i in range(ops_per_thread):
                logger.info(f"Worker {worker_id} message {i}")

        # Benchmark
        start = time.time()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_function, i) for i in range(num_threads)]
            for future in futures:
                future.result()
        end = time.time()

        total_ops = num_threads * ops_per_thread
        total_time = end - start
        return {
            "total_time": total_time,
            "total_operations": total_ops,
            "ops_per_second": total_ops / total_time,
            "ms_per_op": (total_time / total_ops) * 1000,
            "threads": num_threads,
        }

    def benchmark_memory_usage(self, iterations: int = 10000) -> Dict[str, Any]:
        """Benchmark memory usage."""
        import os

        import psutil

        process = psutil.Process(os.getpid())

        # Initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        logeverything.setup_logging(level="INFO", handlers=["console"], visual_mode=False)

        # Create many loggers and log messages
        for i in range(iterations):
            logger = logeverything.get_logger(f"test_logger_{i % 100}")  # Cycle through 100 loggers
            logger.info(f"Message {i}")

        # Final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Get LogEverything memory usage
        memory_usage = logeverything.core.get_memory_usage()

        return {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": final_memory - initial_memory,
            "logeverything_caches": memory_usage,
        }

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmarks and return results."""
        print("🚀 Running LogEverything Benchmark Suite...")

        benchmarks = [
            ("basic_logging", self.benchmark_basic_logging, {}),
            ("decorator_performance", self.benchmark_decorator_performance, {}),
            ("print_capture", self.benchmark_print_capture, {}),
            ("concurrent_logging", self.benchmark_concurrent_logging, {}),
            ("memory_usage", self.benchmark_memory_usage, {}),
        ]

        results = {}

        for name, func, kwargs in benchmarks:
            print(f"📊 Running {name} benchmark...")
            try:
                if asyncio.iscoroutinefunction(func):
                    result = asyncio.run(func(**kwargs))
                else:
                    result = func(**kwargs)
                results[name] = result
                print(f"✅ {name}: {result.get('ops_per_second', 0):.2f} ops/sec")
            except Exception as e:
                print(f"❌ {name} failed: {e}")
                results[name] = {"error": str(e)}

        # Run async benchmark separately
        print("📊 Running async_logging benchmark...")
        try:
            async_result = asyncio.run(self.benchmark_async_logging())
            results["async_logging"] = async_result
            print(f"✅ async_logging: {async_result.get('ops_per_second', 0):.2f} ops/sec")
        except Exception as e:
            print(f"❌ async_logging failed: {e}")
            results["async_logging"] = {"error": str(e)}

        self.results = results
        return results

    def generate_report(self) -> str:
        """Generate a performance report."""
        if not self.results:
            return "No benchmark results available. Run benchmarks first."

        report = []
        report.append("# LogEverything Performance Benchmark Report")
        report.append("")

        for benchmark_name, result in self.results.items():
            if "error" in result:
                report.append(f"## {benchmark_name.replace('_', ' ').title()}")
                report.append(f"❌ **Error**: {result['error']}")
                report.append("")
                continue

            report.append(f"## {benchmark_name.replace('_', ' ').title()}")

            if "ops_per_second" in result:
                report.append(
                    f"- **Performance**: {result['ops_per_second']:.2f} operations/second"
                )
                report.append(f"- **Latency**: {result['ms_per_op']:.4f} ms/operation")

            if "total_time" in result:
                report.append(f"- **Total Time**: {result['total_time']:.4f} seconds")

            if "memory_increase_mb" in result:
                report.append(f"- **Memory Usage**: {result['memory_increase_mb']:.2f} MB increase")
                report.append(
                    f"- **Logger Cache**: {result['logeverything_caches']['logger_cache_size']} entries"
                )

            if "threads" in result:
                report.append(f"- **Concurrency**: {result['threads']} threads")

            report.append("")

        return "\n".join(report)


if __name__ == "__main__":
    benchmark = LogEverythingBenchmark()
    results = benchmark.run_all_benchmarks()

    print("\n" + "=" * 80)
    print(benchmark.generate_report())

    # Save results
    import json

    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n📁 Results saved to benchmark_results.json")
