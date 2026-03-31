"""
Data Models for LogEverything Dashboard
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SystemStats(BaseModel):
    """System statistics model."""

    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_in: int = 0
    network_out: int = 0
    process_memory: float = 0.0
    timestamp: str = ""


class MonitoringStats(BaseModel):
    """Monitoring statistics model."""

    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_logs: int = 0


class LogEvent(BaseModel):
    """Log event model."""

    timestamp: str
    level: str
    logger: str
    message: str
    correlation_id: Optional[str] = None
    thread_id: Optional[int] = None
    process_id: Optional[int] = None
    source: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    duration_ms: Optional[float] = None
    operation: Optional[Dict[str, Any]] = None
    exception: Optional[Dict[str, Any]] = None


class OperationEvent(BaseModel):
    """Operation event model."""

    timestamp: str
    operation_id: str
    operation_name: str
    duration_seconds: float
    success: bool
    error_message: Optional[str] = None


class TopOperation(BaseModel):
    """Summary of a single operation type."""

    name: str = ""
    count: int = 0
    avg_duration: float = 0.0
    failures: int = 0


class OperationSummary(BaseModel):
    """Aggregated operation analytics."""

    total: int = 0
    successful: int = 0
    failed: int = 0
    avg_duration: float = 0.0
    max_duration: float = 0.0
    top_operations: List[TopOperation] = []


class DashboardData(BaseModel):
    """Complete dashboard data model."""

    system_stats: SystemStats
    monitoring_stats: MonitoringStats
    recent_operations: List[OperationEvent]
    recent_logs: List[LogEvent]
    session_info: Dict[str, Any]
