"""
LogEverything Monitoring System

A robust, comprehensive monitoring solution that automatically tracks:
- All function calls and their performance
- System metrics (CPU, memory, disk, network)
- Application logs in structured format
- Real-time API for dashboard integration
- Persistent storage for historical analysis

Simple Usage:
    from logeverything.monitoring import start_monitoring, stop_monitoring

    # Start monitoring with auto-configuration
    start_monitoring(output_dir="./monitoring_data")

    # Your application code here...

    # Stop monitoring (optional - auto-stops on exit)
    stop_monitoring()

Advanced Usage:
    from logeverything.monitoring import MonitoringSystem

    monitor = MonitoringSystem(
        output_dir="./monitoring_data",
        enable_api=True,
        api_port=8999,
        metrics_interval=5.0
    )

    with monitor:
        # Your application code here
        pass
"""

from .api_server import MonitoringAPIServer
from .core import MonitoringSystem, get_monitoring_system, start_monitoring, stop_monitoring
from .logger import OperationTracker, StructuredLogger, set_correlation_context
from .metrics import MetricsCollector, OperationMetrics, PerformanceTracker, SystemMetrics

__all__ = [
    # Core functions
    "start_monitoring",
    "stop_monitoring",
    "get_monitoring_system",
    # Main classes
    "MonitoringSystem",
    "StructuredLogger",
    "MetricsCollector",
    "MonitoringAPIServer",
    # Data classes
    "SystemMetrics",
    "OperationMetrics",
    # Utilities
    "OperationTracker",
    "PerformanceTracker",
    "set_correlation_context",
]
