#!/usr/bin/env python
"""Check benchmark results against baseline thresholds.

Runs lightweight benchmarks for each module defined in ``baseline.json`` and
verifies that every metric meets its minimum ops/sec threshold.  Exits
non-zero if any regression is detected.

Usage::

    python benchmarks/check_baseline.py
"""

import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

# Ensure the project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASELINE_PATH = Path(__file__).parent / "baseline.json"

# ---------------------------------------------------------------------------
# Per-module micro-benchmarks
# ---------------------------------------------------------------------------

N_ITERATIONS = 100_000  # iterations for tight loops
N_DECORATOR_ITERATIONS = 50_000
N_CONTEXT_ITERATIONS = 50_000
N_ASYNC_ITERATIONS = 10_000
N_PRINT_ITERATIONS = 50_000


def _make_null_logger(name: str) -> logging.Logger:
    """Return a stdlib logger that discards all output (fast)."""
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger


def run_core_logging_bench() -> Dict[str, float]:
    """Benchmark raw logging throughput with a NullHandler."""
    logger = _make_null_logger("bench_core")

    # simple_info_message
    start = time.perf_counter()
    for _ in range(N_ITERATIONS):
        logger.info("benchmark message %s", 42)
    elapsed = time.perf_counter() - start
    simple_ops = N_ITERATIONS / elapsed

    # formatted_message (slightly heavier formatting)
    start = time.perf_counter()
    for _ in range(N_ITERATIONS):
        logger.info("user=%s action=%s duration=%.3f", "alice", "login", 0.123)
    elapsed = time.perf_counter() - start
    formatted_ops = N_ITERATIONS / elapsed

    return {
        "simple_info_message": simple_ops,
        "formatted_message": formatted_ops,
    }


def run_decorators_bench() -> Dict[str, float]:
    """Benchmark the @log_function decorator overhead."""
    from logeverything.core import setup_logging
    from logeverything.decorators import log_function

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".log")
    tmp.close()
    try:
        setup_logging(profile="silent", file_path=tmp.name)

        @log_function
        def add(a: int, b: int) -> int:
            return a + b

        # decorated_function_call
        start = time.perf_counter()
        for _ in range(N_DECORATOR_ITERATIONS):
            add(1, 2)
        elapsed = time.perf_counter() - start
        func_ops = N_DECORATOR_ITERATIONS / elapsed

        # class_decoration (decorate + instantiate)
        from logeverything.decorators import log_class

        @log_class
        class Greeter:
            def greet(self, name: str) -> str:
                return f"hi {name}"

        start = time.perf_counter()
        for _ in range(N_DECORATOR_ITERATIONS):
            Greeter().greet("world")
        elapsed = time.perf_counter() - start
        class_ops = N_DECORATOR_ITERATIONS / elapsed

    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    return {
        "decorated_function_call": func_ops,
        "class_decoration": class_ops,
    }


def run_context_managers_bench() -> Dict[str, float]:
    """Benchmark LoggingContext enter/exit."""
    from logeverything.contexts import LoggingContext
    from logeverything.core import setup_logging

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".log")
    tmp.close()
    try:
        setup_logging(profile="silent", file_path=tmp.name)

        start = time.perf_counter()
        for _ in range(N_CONTEXT_ITERATIONS):
            with LoggingContext():
                pass
        elapsed = time.perf_counter() - start
        ctx_ops = N_CONTEXT_ITERATIONS / elapsed
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    return {"logging_context": ctx_ops}


def run_async_logging_bench() -> Dict[str, float]:
    """Benchmark async log message throughput."""
    import asyncio

    from logeverything.core import get_logger, setup_logging

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".log")
    tmp.close()
    try:
        setup_logging(profile="silent", file_path=tmp.name)
        logger = get_logger("bench_async")

        async def _log_n(n: int) -> None:
            for _ in range(n):
                logger.info("async bench msg")

        start = time.perf_counter()
        asyncio.run(_log_n(N_ASYNC_ITERATIONS))
        elapsed = time.perf_counter() - start
        ops = N_ASYNC_ITERATIONS / elapsed
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    return {"async_log_message": ops}


def run_print_capture_bench() -> Dict[str, float]:
    """Benchmark print-capture overhead."""
    from logeverything.capture.print_capture import capture_print
    from logeverything.core import get_logger, setup_logging

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".log")
    tmp.close()
    try:
        setup_logging(profile="silent", file_path=tmp.name)
        logger = get_logger("bench_print")

        start = time.perf_counter()
        with capture_print(logger_name=logger.name):
            for _ in range(N_PRINT_ITERATIONS):
                print("bench")  # noqa: T201
        elapsed = time.perf_counter() - start
        ops = N_PRINT_ITERATIONS / elapsed
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    return {"captured_print": ops}


# ---------------------------------------------------------------------------
# Registry of module name -> runner
# ---------------------------------------------------------------------------

MODULE_RUNNERS: Dict[str, Any] = {
    "core_logging": run_core_logging_bench,
    "decorators": run_decorators_bench,
    "context_managers": run_context_managers_bench,
    "async_logging": run_async_logging_bench,
    "print_capture": run_print_capture_bench,
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    with open(BASELINE_PATH) as f:
        baseline = json.load(f)

    results: Dict[str, Dict[str, float]] = {}
    for module, runner in MODULE_RUNNERS.items():
        print(f"Running {module} benchmarks ...")
        try:
            results[module] = runner()
        except Exception as exc:
            print(f"  ERROR running {module}: {exc}")
            results[module] = {}

    print()
    print("=" * 70)
    print("Baseline check results")
    print("=" * 70)

    failed = False
    for module, thresholds in baseline.items():
        if module.startswith("_"):
            continue
        if not isinstance(thresholds, dict):
            # Legacy flat format -- skip gracefully
            continue
        if module not in results:
            print(f"  SKIP  {module} (no benchmark runner)")
            continue
        for metric, min_ops in thresholds.items():
            actual = results[module].get(metric, 0)
            if actual >= min_ops:
                status = "PASS"
            else:
                status = "FAIL"
                failed = True
            print(f"  {status}  {module}.{metric}: {actual:,.0f} ops/s (min: {min_ops:,})")

    print("=" * 70)
    if failed:
        print("RESULT: FAIL -- one or more benchmarks below baseline")
    else:
        print("RESULT: PASS -- all benchmarks meet baseline thresholds")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
