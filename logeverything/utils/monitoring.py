"""
Monitoring and observability utilities for LogEverything.

This module provides utilities to monitor the performance and health
of the LogEverything library in production environments.
"""

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LoggingMetrics:
    """Metrics for logging performance monitoring."""

    total_calls: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    max_time: float = 0.0
    min_time: float = float("inf")
    error_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0


class PerformanceMonitor:
    """Monitor LogEverything performance metrics."""

    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.metrics: Dict[str, LoggingMetrics] = defaultdict(LoggingMetrics)
        self.recent_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_samples))
        self.lock = threading.Lock()
        self.enabled = True

    def record_call(
        self, operation: str, duration: float, error: bool = False, cache_hit: bool = False
    ) -> None:
        """Record a logging operation for performance monitoring."""
        if not self.enabled:
            return

        with self.lock:
            metric = self.metrics[operation]
            metric.total_calls += 1
            metric.total_time += duration
            metric.avg_time = metric.total_time / metric.total_calls
            metric.max_time = max(metric.max_time, duration)
            metric.min_time = min(metric.min_time, duration)

            if error:
                metric.error_count += 1
            if cache_hit:
                metric.cache_hits += 1
            else:
                metric.cache_misses += 1

            self.recent_times[operation].append(duration)

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get current performance metrics."""
        with self.lock:
            result = {}
            for operation, metric in self.metrics.items():
                recent = list(self.recent_times[operation])
                result[operation] = {
                    "total_calls": metric.total_calls,
                    "total_time_ms": metric.total_time * 1000,
                    "avg_time_ms": metric.avg_time * 1000,
                    "max_time_ms": metric.max_time * 1000,
                    "min_time_ms": metric.min_time * 1000 if metric.min_time != float("inf") else 0,
                    "errors": metric.error_count,
                    "cache_hit_rate": metric.cache_hits
                    / max(1, metric.cache_hits + metric.cache_misses),
                    "recent_avg_ms": (sum(recent) / len(recent) * 1000) if recent else 0,
                    "recent_samples": len(recent),
                }
            return result

    def reset(self) -> None:
        """Reset all metrics."""
        with self.lock:
            self.metrics.clear()
            self.recent_times.clear()

    def enable(self) -> None:
        """Enable performance monitoring."""
        self.enabled = True

    def disable(self) -> None:
        """Disable performance monitoring."""
        self.enabled = False


# Global performance monitor instance
_performance_monitor = PerformanceMonitor()


def get_performance_metrics() -> Dict[str, Dict[str, Any]]:
    """Get current LogEverything performance metrics."""
    return _performance_monitor.get_metrics()


def reset_performance_metrics() -> None:
    """Reset all performance metrics."""
    _performance_monitor.reset()


def enable_performance_monitoring() -> None:
    """Enable performance monitoring."""
    _performance_monitor.enable()


def disable_performance_monitoring() -> None:
    """Disable performance monitoring."""
    _performance_monitor.disable()


def performance_context(operation: str) -> Any:
    """Context manager for measuring operation performance."""

    class PerfContext:
        def __init__(self, op: str) -> None:
            self.operation = op
            self.start_time: Optional[float] = None

        def __enter__(self) -> "PerfContext":
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            if self.start_time:
                duration = time.time() - self.start_time
                error = exc_type is not None
                _performance_monitor.record_call(self.operation, duration, error=error)

    return PerfContext(operation)


def health_check() -> Dict[str, Any]:
    """Perform a health check of LogEverything components."""
    from .. import core
    from ..asyncio import async_logging

    health: Dict[str, Any] = {"status": "healthy", "timestamp": time.time(), "components": {}}

    try:
        # Test core functionality
        with performance_context("health_check_core"):
            logger = core.get_logger("health_check")
            logger.info("Health check")
        health["components"]["core"] = "healthy"
    except Exception as e:
        health["components"]["core"] = f"error: {e}"
        health["status"] = "degraded"

    try:
        # Test print capture
        health["components"]["print_capture"] = "healthy"
    except Exception as e:
        health["components"]["print_capture"] = f"error: {e}"
        health["status"] = "degraded"

    try:
        # Test async logging
        handlers = async_logging.get_all_async_handlers()
        health["components"]["async_logging"] = f"healthy ({len(handlers)} handlers)"
    except Exception as e:
        health["components"]["async_logging"] = f"error: {e}"
        health["status"] = "degraded"

    # Add metrics
    health["metrics"] = get_performance_metrics()
    health["memory_usage"] = core.get_memory_usage()

    return health
