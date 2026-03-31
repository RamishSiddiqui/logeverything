"""
LogEverything Monitoring Integration Example

Demonstrates how to set up LogEverything for monitoring and observability,
using JSONLineFormatter with rotation handlers for structured, dashboard-
compatible output.

Features demonstrated:
- JSONLineFormatter for structured logging
- Rotation handlers for production log management
- Operation metrics collection and structured logging
- System health monitoring and alerting
- Dashboard-ready log formats with hierarchy fields
"""

import asyncio
import logging
import random
import time
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from logeverything import AsyncLogger, Logger, get_logger
from logeverything.decorators import log
from logeverything.handlers import (
    ConsoleHandler,
    FileHandler,
    JSONLineFormatter,
    TimedRotatingFileHandler,
)

# =============================================================================
# 1. MONITORING DATA STRUCTURES
# =============================================================================


@dataclass
class OperationMetrics:
    """Operation metrics for monitoring."""

    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: str = "running"
    input_size: Optional[int] = None
    output_size: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def finish(self, status: str = "success", error: Optional[Exception] = None):
        """Complete the operation measurement."""
        self.end_time = datetime.now(timezone.utc)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status

        if error:
            self.error_message = str(error)
            self.status = "error"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return asdict(self)


@dataclass
class SystemMetrics:
    """System health metrics."""

    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    active_connections: int
    timestamp: datetime

    @classmethod
    def collect(cls) -> "SystemMetrics":
        """Collect current system metrics (simulated)."""
        return cls(
            cpu_usage_percent=random.uniform(10, 90),
            memory_usage_percent=random.uniform(30, 80),
            disk_usage_percent=random.uniform(20, 70),
            active_connections=random.randint(5, 50),
            timestamp=datetime.now(timezone.utc),
        )


# =============================================================================
# 2. MONITORING LOGGER SETUP
# =============================================================================


class MonitoringLogger:
    """Logger configured for monitoring integration using rotation + JSONL."""

    def __init__(self, service_name: str):
        self.service_name = service_name

        # Application logger — console + rotating JSONL for the dashboard
        self.app_logger = Logger(f"app.{service_name}", auto_setup=False)

        console = ConsoleHandler()
        console.setLevel(logging.INFO)
        self.app_logger.add_handler(console)

        app_jsonl = TimedRotatingFileHandler(
            f"logs/{service_name}_app.jsonl",
            when="midnight",
            retention_days=30,
            compress=True,
        )
        app_jsonl.setFormatter(JSONLineFormatter(source=service_name))
        self.app_logger.add_handler(app_jsonl)

        # Metrics logger — JSONL only (no console noise)
        self.metrics_logger = Logger(f"metrics.{service_name}", auto_setup=False)

        metrics_jsonl = TimedRotatingFileHandler(
            f"logs/{service_name}_metrics.jsonl",
            when="midnight",
            retention_days=30,
            compress=True,
        )
        metrics_jsonl.setFormatter(JSONLineFormatter(source=f"{service_name}.metrics"))
        self.metrics_logger.add_handler(metrics_jsonl)

        # Error logger — console + size-rotated file for alerting
        self.error_logger = Logger(f"errors.{service_name}", auto_setup=False)
        self.error_logger.add_handler(console)

        error_file = FileHandler(
            f"logs/{service_name}_errors.jsonl",
            max_size=10 * 1024 * 1024,  # 10 MB
            backup_count=5,
        )
        error_file.setFormatter(JSONLineFormatter(source=f"{service_name}.errors"))
        error_file.setLevel(logging.WARNING)
        self.error_logger.add_handler(error_file)

        self.app_logger.info(f"Monitoring logger initialized for {service_name}")

    def log_operation(self, metrics: OperationMetrics):
        """Log operation metrics in structured format."""
        metrics_data = metrics.to_dict()

        # Structured format for dashboard consumption
        self.metrics_logger.info("operation_completed", extra=metrics_data)

        # Human-readable summary
        if metrics.status == "success":
            self.app_logger.info(
                f"{metrics.operation_name} completed in {metrics.duration_ms:.2f}ms"
            )
        elif metrics.status == "error":
            self.app_logger.error(f"{metrics.operation_name} failed: {metrics.error_message}")

    def log_system_metrics(self, metrics: SystemMetrics):
        """Log system health metrics."""
        metrics_data = asdict(metrics)
        self.metrics_logger.info("system_metrics", extra=metrics_data)

        # Alert on high resource usage
        if metrics.cpu_usage_percent > 80:
            self.error_logger.warning(f"High CPU usage: {metrics.cpu_usage_percent:.1f}%")


# =============================================================================
# 3. OPERATION MONITORING CONTEXT
# =============================================================================


class OperationContext:
    """Context manager for monitoring operations."""

    def __init__(self, operation_name: str, monitoring_logger: MonitoringLogger, **metadata):
        self.operation_name = operation_name
        self.monitoring_logger = monitoring_logger
        self.metadata = metadata
        self.metrics = None

    def __enter__(self):
        self.metrics = OperationMetrics(
            operation_name=self.operation_name,
            start_time=datetime.now(timezone.utc),
            metadata=self.metadata,
        )

        self.monitoring_logger.app_logger.info(
            f"Starting {self.operation_name}", extra={"operation_metadata": self.metadata}
        )

        return self.metrics

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.metrics.finish(status="error", error=exc_val)
            self.monitoring_logger.error_logger.error(
                f"{self.operation_name} failed: {exc_val}",
                extra={"traceback": traceback.format_exc()},
            )
        else:
            self.metrics.finish(status="success")

        self.monitoring_logger.log_operation(self.metrics)


# =============================================================================
# 4. MAIN DEMONSTRATION
# =============================================================================


async def main():
    """Comprehensive monitoring integration demonstration."""
    print("LogEverything Monitoring Integration Demo")
    print("=" * 50)

    # Initialize monitoring
    monitoring = MonitoringLogger("DemoService")

    print("\n1. Basic operation monitoring:")

    # Demonstrate operation context
    with OperationContext("data_processing", monitoring, dataset="example.csv") as op:
        monitoring.app_logger.info("Processing sample data")
        op.input_size = 1024 * 100  # 100KB input

        # Simulate processing
        time.sleep(0.1)

        op.output_size = 1024 * 150  # 150KB output
        monitoring.app_logger.info("Data processing completed")

    print("\n2. Error handling with monitoring:")

    try:
        with OperationContext("risky_operation", monitoring) as op:
            # Simulate an error
            raise ValueError("Simulated processing error!")
    except ValueError:
        monitoring.app_logger.info("Error handled gracefully")

    print("\n3. System health monitoring:")

    # Collect and log system metrics
    system_metrics = SystemMetrics.collect()
    monitoring.log_system_metrics(system_metrics)

    print(f"   CPU Usage: {system_metrics.cpu_usage_percent:.1f}%")
    print(f"   Memory Usage: {system_metrics.memory_usage_percent:.1f}%")
    print(f"   Active Connections: {system_metrics.active_connections}")

    print("\n4. Dashboard metrics generation:")

    # Generate sample operations for dashboard
    for i in range(5):
        operation_name = f"sample_operation_{i}"
        status = "success" if random.random() > 0.2 else "error"  # 20% error rate

        try:
            with OperationContext(
                operation_name, monitoring, operation_id=i, batch_size=random.randint(10, 100)
            ) as op:
                # Simulate variable processing time
                await asyncio.sleep(random.uniform(0.01, 0.1))

                if status == "error":
                    raise Exception(f"Simulated error in {operation_name}")
        except Exception:
            pass  # Already handled by OperationContext

    print(f"\nMonitoring demonstration complete!")
    print(f"Check logs/ directory for structured monitoring data:")
    print(f"   DemoService_app.jsonl     — Application logs (JSONL, daily rotation)")
    print(f"   DemoService_metrics.jsonl — Metrics data (JSONL, daily rotation)")
    print(f"   DemoService_errors.jsonl  — Errors and alerts (JSONL, size rotation)")
    print()
    print("All files are dashboard-compatible — point a Local Connection at logs/")


if __name__ == "__main__":
    print("Starting monitoring integration demonstration...")
    asyncio.run(main())
    print("\nThis example shows monitoring integration patterns with LogEverything.")
