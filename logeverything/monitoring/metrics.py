"""
System Metrics Collection for LogEverything Monitoring

Collects comprehensive system and application metrics including:
- CPU usage, memory, disk I/O, network I/O
- Process-specific metrics
- Custom application metrics
- Performance counters
"""

import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psutil


@dataclass
class SystemMetrics:
    """Comprehensive system metrics snapshot."""

    # Timestamp
    timestamp: str

    # CPU metrics
    cpu_percent: float
    cpu_count: int
    cpu_freq_current: Optional[float]
    load_average: Optional[List[float]]

    # Memory metrics
    memory_total: int
    memory_available: int
    memory_used: int
    memory_percent: float
    swap_total: int
    swap_used: int
    swap_percent: float

    # Disk metrics
    disk_total: int
    disk_used: int
    disk_free: int
    disk_percent: float
    disk_read_bytes: int
    disk_write_bytes: int
    disk_read_count: int
    disk_write_count: int

    # Network metrics
    network_bytes_sent: int
    network_bytes_recv: int
    network_packets_sent: int
    network_packets_recv: int

    # Process metrics
    process_cpu_percent: float
    process_memory_rss: int
    process_memory_vms: int
    process_memory_percent: float
    process_num_threads: int
    process_num_fds: Optional[int]

    # System info
    boot_time: float
    uptime_seconds: float


@dataclass
class OperationMetrics:
    """Metrics for a specific operation or function call."""

    timestamp: str
    operation_id: str
    operation_name: str
    duration_seconds: float
    cpu_time: Optional[float]
    memory_delta: Optional[int]
    success: bool
    error_message: Optional[str]
    custom_metrics: Optional[Dict[str, Any]]


class MetricsCollector:
    """
    High-performance metrics collector with minimal overhead.

    Collects system metrics at regular intervals and provides
    operation-level performance tracking.
    """

    def __init__(self, storage: Optional[Any] = None, collection_interval: float = 5.0):
        self.storage = storage
        self.collection_interval = collection_interval
        self.total_collected = 0

        # Cache frequently accessed objects
        self._process = psutil.Process()
        self._last_disk_io = None
        self._last_network_io = None

        # Thread safety
        self._lock = threading.Lock()

        # Performance tracking
        self._operation_metrics: List[OperationMetrics] = []
        self._max_operation_metrics = 10000

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect comprehensive system metrics."""
        timestamp = datetime.now(timezone.utc).isoformat()

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        cpu_freq_current = cpu_freq.current if cpu_freq else None

        # Load average (Unix only)
        try:
            load_avg = list(psutil.getloadavg())
        except (AttributeError, OSError):
            load_avg = None

        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Disk metrics
        disk_usage = psutil.disk_usage("/")
        disk_io = psutil.disk_io_counters()

        # Network metrics
        network_io = psutil.net_io_counters()

        # Process metrics
        try:
            process_cpu = self._process.cpu_percent()
            process_memory = self._process.memory_info()
            process_memory_percent = self._process.memory_percent()
            process_threads = self._process.num_threads()

            # File descriptors (Unix only)
            try:
                process_fds = self._process.num_fds()
            except (AttributeError, psutil.AccessDenied):
                process_fds = None

        except psutil.NoSuchProcess:
            # Process might have died, reinitialize
            self._process = psutil.Process()
            process_cpu = 0.0
            process_memory = psutil.Process().memory_info()
            process_memory_percent = 0.0
            process_threads = 1
            process_fds = None

        # System uptime
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time

        metrics = SystemMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            cpu_count=cpu_count,
            cpu_freq_current=cpu_freq_current,
            load_average=load_avg,
            memory_total=memory.total,
            memory_available=memory.available,
            memory_used=memory.used,
            memory_percent=memory.percent,
            swap_total=swap.total,
            swap_used=swap.used,
            swap_percent=swap.percent,
            disk_total=disk_usage.total,
            disk_used=disk_usage.used,
            disk_free=disk_usage.free,
            disk_percent=disk_usage.percent,
            disk_read_bytes=disk_io.read_bytes if disk_io else 0,
            disk_write_bytes=disk_io.write_bytes if disk_io else 0,
            disk_read_count=disk_io.read_count if disk_io else 0,
            disk_write_count=disk_io.write_count if disk_io else 0,
            network_bytes_sent=network_io.bytes_sent if network_io else 0,
            network_bytes_recv=network_io.bytes_recv if network_io else 0,
            network_packets_sent=network_io.packets_sent if network_io else 0,
            network_packets_recv=network_io.packets_recv if network_io else 0,
            process_cpu_percent=process_cpu,
            process_memory_rss=process_memory.rss,
            process_memory_vms=process_memory.vms,
            process_memory_percent=process_memory_percent,
            process_num_threads=process_threads,
            process_num_fds=process_fds,
            boot_time=boot_time,
            uptime_seconds=uptime,
        )

        # Store metrics
        if self.storage:
            self.storage.store_metrics(metrics)

        with self._lock:
            self.total_collected += 1

        return metrics

    def record_operation(
        self,
        operation_id: str,
        operation_name: str,
        duration_seconds: float,
        success: bool = True,
        error_message: Optional[str] = None,
        custom_metrics: Optional[Dict[str, Any]] = None,
        cpu_time: Optional[float] = None,
        memory_delta: Optional[int] = None,
    ) -> None:
        """Record metrics for a completed operation."""

        metrics = OperationMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            operation_id=operation_id,
            operation_name=operation_name,
            duration_seconds=duration_seconds,
            cpu_time=cpu_time,
            memory_delta=memory_delta,
            success=success,
            error_message=error_message,
            custom_metrics=custom_metrics,
        )

        with self._lock:
            self._operation_metrics.append(metrics)

            # Limit memory usage
            if len(self._operation_metrics) > self._max_operation_metrics:
                self._operation_metrics = self._operation_metrics[
                    -self._max_operation_metrics // 2 :
                ]

        # Store metrics
        if self.storage:
            self.storage.store_operation_metrics(metrics)

    def get_recent_operations(self, limit: int = 100) -> List[OperationMetrics]:
        """Get recent operation metrics."""
        with self._lock:
            return self._operation_metrics[-limit:] if self._operation_metrics else []

    def get_system_summary(self) -> Dict[str, Any]:
        """Get a summary of current system state."""
        try:
            current_metrics = self.collect_system_metrics()

            return {
                "timestamp": current_metrics.timestamp,
                "system": {
                    "cpu_percent": current_metrics.cpu_percent,
                    "memory_percent": current_metrics.memory_percent,
                    "disk_percent": current_metrics.disk_percent,
                    "uptime_hours": current_metrics.uptime_seconds / 3600,
                },
                "process": {
                    "cpu_percent": current_metrics.process_cpu_percent,
                    "memory_mb": current_metrics.process_memory_rss / (1024 * 1024),
                    "memory_percent": current_metrics.process_memory_percent,
                    "threads": current_metrics.process_num_threads,
                },
                "monitoring": {
                    "total_metrics_collected": self.total_collected,
                    "recent_operations": len(self._operation_metrics),
                },
            }
        except Exception as e:
            return {
                "error": f"Failed to collect metrics: {e}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


class PerformanceTracker:
    """Context manager for tracking operation performance."""

    def __init__(
        self,
        metrics_collector: MetricsCollector,
        operation_name: str,
        operation_id: Optional[str] = None,
        custom_metrics: Optional[Dict[str, Any]] = None,
    ):
        self.metrics_collector = metrics_collector
        self.operation_name = operation_name
        self.operation_id = operation_id or f"op_{int(time.time() * 1000)}"
        self.custom_metrics = custom_metrics or {}

        self.start_time: Optional[float] = None
        self.start_memory: Optional[int] = None
        self.start_cpu_time: Optional[float] = None

    def __enter__(self) -> str:
        self.start_time = time.time()

        # Record starting memory usage
        try:
            process = psutil.Process()
            self.start_memory = process.memory_info().rss
            self.start_cpu_time = process.cpu_times().user + process.cpu_times().system
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.start_memory = None
            self.start_cpu_time = None

        return self.operation_id

    def __exit__(
        self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Any
    ) -> None:
        duration = time.time() - self.start_time if self.start_time else 0.0
        success = exc_type is None
        error_message = str(exc_val) if exc_val else None

        # Calculate resource deltas
        memory_delta: Optional[int] = None
        cpu_delta: Optional[float] = None

        try:
            process = psutil.Process()
            if self.start_memory:
                current_memory = process.memory_info().rss
                memory_delta = current_memory - self.start_memory

            if self.start_cpu_time:
                current_cpu_time = process.cpu_times().user + process.cpu_times().system
                cpu_delta = current_cpu_time - self.start_cpu_time

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        self.metrics_collector.record_operation(
            operation_id=self.operation_id,
            operation_name=self.operation_name,
            duration_seconds=duration,
            success=success,
            error_message=error_message,
            custom_metrics=self.custom_metrics,
            cpu_time=cpu_delta,
            memory_delta=memory_delta,
        )
