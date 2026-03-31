"""
Monitoring API Server

Provides a RESTful API for the LogEverything dashboard and external
monitoring tools to access real-time monitoring data.
"""

import json
import threading
from datetime import datetime, timezone

try:
    import uvicorn
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


class MonitoringAPIServer:
    """
    Lightweight API server for monitoring data access.

    Provides endpoints for:
    - Real-time system metrics
    - Operation history and statistics
    - Health checks
    - Data export
    """

    def __init__(self, port: int = 8999, storage=None, metrics_collector=None, logger=None):
        self.port = port
        self.storage = storage
        self.metrics_collector = metrics_collector
        self.logger = logger

        self._server_thread = None
        self._server = None
        self._is_running = False

        if not FASTAPI_AVAILABLE:
            if logger:
                logger.warning("FastAPI not available, API server disabled")
            return

        self._setup_app()

    def _setup_app(self):
        """Setup FastAPI application with routes."""
        if not FASTAPI_AVAILABLE:
            return

        self.app = FastAPI(
            title="LogEverything Monitoring API",
            description="Real-time monitoring data access",
            version="1.0.0",
        )

        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes."""

        @self.app.get("/")
        async def root():
            return {
                "service": "LogEverything Monitoring API",
                "version": "1.0.0",
                "status": "running",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": self._get_uptime(),
                "components": {
                    "storage": "ok" if self.storage else "unavailable",
                    "metrics_collector": "ok" if self.metrics_collector else "unavailable",
                    "logger": "ok" if self.logger else "unavailable",
                },
            }

        @self.app.get("/metrics/system")
        async def get_system_metrics():
            """Get current system metrics."""
            if not self.metrics_collector:
                raise HTTPException(status_code=503, detail="Metrics collector not available")

            try:
                metrics = self.metrics_collector.get_system_summary()
                return JSONResponse(content=metrics)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to collect metrics: {e}")

        @self.app.get("/metrics/system/recent")
        async def get_recent_system_metrics(limit: int = 100):
            """Get recent system metrics from storage."""
            if not self.storage:
                raise HTTPException(status_code=503, detail="Storage not available")

            try:
                metrics = self.storage.get_recent_metrics(limit=limit)
                return JSONResponse(content={"metrics": metrics})
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {e}")

        @self.app.get("/operations/recent")
        async def get_recent_operations(limit: int = 100):
            """Get recent operations."""
            if not self.storage:
                raise HTTPException(status_code=503, detail="Storage not available")

            try:
                operations = self.storage.get_recent_operations(limit=limit)
                return JSONResponse(content={"operations": operations})
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to retrieve operations: {e}")

        @self.app.get("/operations/summary")
        async def get_operations_summary(hours: int = 24):
            """Get operations summary statistics."""
            if not self.storage:
                raise HTTPException(status_code=503, detail="Storage not available")

            try:
                summary = self.storage.get_operation_summary(hours=hours)
                return JSONResponse(content=summary)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get summary: {e}")

        @self.app.get("/system/trends")
        async def get_system_trends(hours: int = 24):
            """Get system metrics trends."""
            if not self.storage:
                raise HTTPException(status_code=503, detail="Storage not available")

            try:
                trends = self.storage.get_system_trends(hours=hours)
                return JSONResponse(content=trends)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get trends: {e}")

        @self.app.get("/export")
        async def export_data(format: str = "json"):
            """Export monitoring data."""
            if not self.storage:
                raise HTTPException(status_code=503, detail="Storage not available")

            try:
                # Create temporary export file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_file = f"monitoring_export_{timestamp}.{format}"

                exported_path = self.storage.export_data(export_file, format=format)

                # Read and return the data
                with open(exported_path, "r") as f:
                    data = json.load(f)

                # Clean up temp file
                exported_path.unlink()

                return JSONResponse(content=data)

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Export failed: {e}")

        @self.app.post("/api/ingest/logs")
        async def ingest_logs(request: Request):
            """Receive batched log records from transport handlers."""
            if not self.storage:
                raise HTTPException(status_code=503, detail="Storage not available")

            try:
                body = await request.json()
                logs = body.get("logs", [])
                source = body.get("source", "unknown")

                if not logs:
                    return JSONResponse(content={"accepted": 0})

                count = self.storage.store_logs_batch(logs, source=source)
                return JSONResponse(content={"accepted": count})
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

        @self.app.get("/api/logs")
        async def get_logs(
            limit: int = 100,
            level: str = "",
            correlation_id: str = "",
            source: str = "",
        ):
            """Query stored logs with optional filters."""
            if not self.storage:
                raise HTTPException(status_code=503, detail="Storage not available")

            try:
                logs = self.storage.get_logs(
                    limit=limit,
                    level=level,
                    correlation_id=correlation_id,
                    source=source,
                )
                return JSONResponse(content={"logs": logs})
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Query failed: {e}")

        @self.app.get("/api/logs/trace/{correlation_id}")
        async def get_log_trace(correlation_id: str):
            """Get all log entries for a specific correlation ID."""
            if not self.storage:
                raise HTTPException(status_code=503, detail="Storage not available")

            try:
                logs = self.storage.get_logs_by_correlation(correlation_id)
                return JSONResponse(content={"correlation_id": correlation_id, "logs": logs})
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Trace query failed: {e}")

        @self.app.get("/status")
        async def get_monitoring_status():
            """Get detailed monitoring system status."""
            status = {
                "api_server": {
                    "running": self._is_running,
                    "port": self.port,
                    "uptime_seconds": self._get_uptime(),
                },
                "components": {
                    "storage": {
                        "available": self.storage is not None,
                        "session_id": (
                            getattr(self.storage, "session_id", None) if self.storage else None
                        ),
                    },
                    "metrics_collector": {
                        "available": self.metrics_collector is not None,
                        "total_collected": (
                            getattr(self.metrics_collector, "total_collected", 0)
                            if self.metrics_collector
                            else 0
                        ),
                    },
                    "logger": {"available": self.logger is not None},
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            return JSONResponse(content=status)

    def _get_uptime(self) -> float:
        """Get server uptime in seconds."""
        if hasattr(self, "_start_time"):
            return datetime.now().timestamp() - self._start_time
        return 0.0

    def start(self):
        """Start the API server in a background thread."""
        if not FASTAPI_AVAILABLE or self._is_running:
            return

        self._start_time = datetime.now().timestamp()

        def run_server():
            try:
                uvicorn.run(
                    self.app,
                    host="0.0.0.0",
                    port=self.port,
                    log_level="warning",  # Reduce log noise
                    access_log=False,
                )
            except Exception as e:
                if self.logger:
                    self.logger.error(f"API server failed: {e}")

        self._server_thread = threading.Thread(target=run_server, daemon=True)
        self._server_thread.start()
        self._is_running = True

        if self.logger:
            self.logger.info(
                f"Monitoring API server started on port {self.port}", extra={"api_port": self.port}
            )

    def stop(self):
        """Stop the API server."""
        if not self._is_running:
            return

        self._is_running = False

        if self.logger:
            self.logger.info("Monitoring API server stopped")

        # Note: uvicorn doesn't have a clean way to stop from another thread
        # The server will stop when the main process exits

    def is_running(self) -> bool:
        """Check if the API server is running."""
        return self._is_running


class SimpleAPIServer:
    """
    Fallback simple HTTP server when FastAPI is not available.
    """

    def __init__(self, port: int = 8999, storage=None, metrics_collector=None, logger=None):
        self.port = port
        self.storage = storage
        self.metrics_collector = metrics_collector
        self.logger = logger
        self._is_running = False

    def start(self):
        """Start simple HTTP server."""
        if self.logger:
            self.logger.info(
                f"FastAPI not available, starting simple HTTP server on port {self.port}",
                extra={"api_port": self.port},
            )

        # Implementation would go here for a simple HTTP server
        # For now, just mark as running
        self._is_running = True

    def stop(self):
        """Stop the server."""
        self._is_running = False

    def is_running(self) -> bool:
        """Check if running."""
        return self._is_running
