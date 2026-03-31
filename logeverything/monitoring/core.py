"""
LogEverything Monitoring Core - Clean Implementation
"""

import atexit
import os
import signal
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class MonitoringSystem:
    """
    Simple, clean monitoring system for LogEverything.
    """

    def __init__(
        self,
        output_dir: str = "./monitoring_data",
        enable_api: bool = True,
        api_port: int = 8999,
        metrics_interval: float = 5.0,
    ):
        self.output_dir = Path(output_dir)
        self.enable_api = enable_api
        self.api_port = api_port
        self.metrics_interval = metrics_interval

        # State tracking
        self.is_running = False
        self.start_time = None

        # Components (lazy loaded to avoid circular imports)
        self.logger = None
        self.metrics_collector = None
        self.api_server = None
        self.storage = None

        # Setup
        self._setup_output_directory()
        self._register_shutdown_handlers()

    def _setup_output_directory(self):
        """Create the output directory structure."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)

        # Create session info
        import json

        session_info = {
            "session_id": f"session_{int(time.time())}",
            "start_time": datetime.now().isoformat(),
            "pid": os.getpid(),
            "working_directory": str(Path.cwd()),
        }

        with open(self.output_dir / "session_info.json", "w") as f:
            json.dump(session_info, f, indent=2)

    def _register_shutdown_handlers(self):
        """Register handlers for clean shutdown."""
        atexit.register(self.stop)

        def signal_handler(signum, frame):
            self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def start(self):
        """Start the monitoring system."""
        if self.is_running:
            return

        self.start_time = time.time()

        # Lazy import to avoid circular dependencies
        from .logger import StructuredLogger
        from .metrics import MetricsCollector
        from .storage import MonitoringStorage

        # Initialize components
        self.storage = MonitoringStorage(self.output_dir)
        self.logger = StructuredLogger("logeverything.monitoring", storage=self.storage)
        self.metrics_collector = MetricsCollector(storage=self.storage)

        # Start API server if enabled
        if self.enable_api:
            try:
                from .api_server import MonitoringAPIServer

                self.api_server = MonitoringAPIServer(
                    port=self.api_port,
                    storage=self.storage,
                    metrics_collector=self.metrics_collector,
                    logger=self.logger,
                )
                self.api_server.start()
            except ImportError:
                if self.logger:
                    self.logger.warning("FastAPI not available, API server disabled")

        self.is_running = True

        if self.logger:
            self.logger.info(
                "Monitoring system started",
                extra={
                    "output_dir": str(self.output_dir),
                    "api_enabled": self.enable_api,
                    "api_port": self.api_port if self.enable_api else None,
                },
            )

    def stop(self):
        """Stop the monitoring system."""
        if not self.is_running:
            return

        self.is_running = False

        # Stop API server
        if self.api_server:
            self.api_server.stop()

        # Log shutdown
        if self.logger:
            duration = time.time() - self.start_time if self.start_time else 0
            self.logger.info(
                "Monitoring system stopped", extra={"session_duration_seconds": duration}
            )

        # Clean up
        if self.storage:
            self.storage.close_session()

    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            "is_running": self.is_running,
            "start_time": self.start_time,
            "uptime_seconds": time.time() - self.start_time if self.start_time else 0,
            "output_dir": str(self.output_dir),
            "api_enabled": self.enable_api,
            "api_port": self.api_port if self.enable_api else None,
        }

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# Global monitoring instance
_global_monitoring_system = None


def start_monitoring(
    output_dir: str = "./monitoring_data",
    enable_api: bool = True,
    api_port: int = 8999,
    metrics_interval: float = 5.0,
) -> MonitoringSystem:
    """
    Start the global monitoring system.
    """
    global _global_monitoring_system

    if _global_monitoring_system and _global_monitoring_system.is_running:
        return _global_monitoring_system

    _global_monitoring_system = MonitoringSystem(
        output_dir=output_dir,
        enable_api=enable_api,
        api_port=api_port,
        metrics_interval=metrics_interval,
    )

    _global_monitoring_system.start()
    return _global_monitoring_system


def stop_monitoring():
    """Stop the global monitoring system."""
    global _global_monitoring_system

    if _global_monitoring_system:
        _global_monitoring_system.stop()
        _global_monitoring_system = None


def get_monitoring_system() -> Optional[MonitoringSystem]:
    """Get the current global monitoring system."""
    return _global_monitoring_system
