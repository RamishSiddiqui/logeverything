"""
Data Storage for LogEverything Monitoring

Handles persistent storage of logs, metrics, and operational data
in an organized, queryable format.
"""

import json
import sqlite3
import threading
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .metrics import OperationMetrics, SystemMetrics


class MonitoringStorage:
    """
    Efficient storage system for monitoring data.

    Features:
    - SQLite for structured data (metrics, operations)
    - JSON Lines for logs (human readable, streamable)
    - Automatic data rotation and cleanup
    - Thread-safe operations
    - Fast querying and aggregation
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / "logs"
        self.metrics_dir = self.base_dir / "metrics"
        self.operations_dir = self.base_dir / "operations"

        # Ensure directories exist
        for dir_path in [self.logs_dir, self.metrics_dir, self.operations_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # SQLite database for structured data
        self.db_path = self.base_dir / "monitoring.db"
        self._db_lock = threading.Lock()

        # Initialize database
        self._init_database()

        # Track current session
        self.session_id = f"session_{int(time.time())}"
        self._log_session_start()

    def _init_database(self):
        """Initialize SQLite database with required tables."""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)

            # System metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent REAL,
                    network_bytes_sent INTEGER,
                    network_bytes_recv INTEGER,
                    process_memory_rss INTEGER,
                    process_cpu_percent REAL,
                    full_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Operation metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS operation_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    operation_id TEXT NOT NULL,
                    operation_name TEXT NOT NULL,
                    duration_seconds REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    cpu_time REAL,
                    memory_delta INTEGER,
                    custom_metrics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    pid INTEGER,
                    working_directory TEXT,
                    config TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Ingested logs table (populated by transport handlers via the API)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp TEXT,
                    level TEXT,
                    logger TEXT,
                    message TEXT,
                    correlation_id TEXT,
                    source TEXT,
                    thread_id INTEGER,
                    process_id INTEGER,
                    extra TEXT
                )
            """)

            # Create indexes for performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp"
                " ON system_metrics(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_system_metrics_session"
                " ON system_metrics(session_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_operation_metrics_timestamp"
                " ON operation_metrics(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_operation_metrics_session"
                " ON operation_metrics(session_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_operation_metrics_name"
                " ON operation_metrics(operation_name)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_correlation ON logs(correlation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_source ON logs(source)")

            conn.commit()
            conn.close()

    def _log_session_start(self):
        """Log the start of a new monitoring session."""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """
                INSERT INTO sessions (session_id, start_time, pid, working_directory)
                VALUES (?, ?, ?, ?)
            """,
                (
                    self.session_id,
                    datetime.now(timezone.utc).isoformat(),
                    __import__("os").getpid(),
                    str(Path.cwd()),
                ),
            )
            conn.commit()
            conn.close()

    def store_metrics(self, metrics: SystemMetrics):
        """Store system metrics to database."""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """
                INSERT INTO system_metrics (
                    session_id, timestamp, cpu_percent, memory_percent, disk_percent,
                    network_bytes_sent, network_bytes_recv, process_memory_rss,
                    process_cpu_percent, full_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    self.session_id,
                    metrics.timestamp,
                    metrics.cpu_percent,
                    metrics.memory_percent,
                    metrics.disk_percent,
                    metrics.network_bytes_sent,
                    metrics.network_bytes_recv,
                    metrics.process_memory_rss,
                    metrics.process_cpu_percent,
                    json.dumps(asdict(metrics)),
                ),
            )
            conn.commit()
            conn.close()

    def store_operation_metrics(self, metrics: OperationMetrics):
        """Store operation metrics to database."""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """
                INSERT INTO operation_metrics (
                    session_id, timestamp, operation_id, operation_name,
                    duration_seconds, success, error_message, cpu_time,
                    memory_delta, custom_metrics
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    self.session_id,
                    metrics.timestamp,
                    metrics.operation_id,
                    metrics.operation_name,
                    metrics.duration_seconds,
                    metrics.success,
                    metrics.error_message,
                    metrics.cpu_time,
                    metrics.memory_delta,
                    json.dumps(metrics.custom_metrics) if metrics.custom_metrics else None,
                ),
            )
            conn.commit()
            conn.close()

    def get_recent_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent system metrics."""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                """
                SELECT * FROM system_metrics
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (self.session_id, limit),
            )

            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results

    def get_recent_operations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent operation metrics."""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                """
                SELECT * FROM operation_metrics
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (self.session_id, limit),
            )

            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results

    def get_operation_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get operation summary statistics."""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)

            # Total operations
            cursor = conn.execute(
                """
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                       SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
                       AVG(duration_seconds) as avg_duration,
                       MAX(duration_seconds) as max_duration
                FROM operation_metrics
                WHERE session_id = ?
                AND datetime(timestamp) > datetime('now', '-{} hours')
            """.format(hours),
                (self.session_id,),
            )

            row = cursor.fetchone()

            # Top operations by count
            cursor = conn.execute(
                """
                SELECT operation_name, COUNT(*) as count,
                       AVG(duration_seconds) as avg_duration
                FROM operation_metrics
                WHERE session_id = ?
                AND datetime(timestamp) > datetime('now', '-{} hours')
                GROUP BY operation_name
                ORDER BY count DESC
                LIMIT 10
            """.format(hours),
                (self.session_id,),
            )

            top_operations = [
                {"name": row[0], "count": row[1], "avg_duration": row[2]}
                for row in cursor.fetchall()
            ]

            conn.close()

            return {
                "total_operations": row[0] or 0,
                "successful_operations": row[1] or 0,
                "failed_operations": row[2] or 0,
                "average_duration": row[3] or 0,
                "max_duration": row[4] or 0,
                "top_operations": top_operations,
            }

    def get_system_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get system metrics trends."""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)

            cursor = conn.execute(
                """
                SELECT AVG(cpu_percent) as avg_cpu,
                       MAX(cpu_percent) as max_cpu,
                       AVG(memory_percent) as avg_memory,
                       MAX(memory_percent) as max_memory,
                       AVG(disk_percent) as avg_disk,
                       COUNT(*) as sample_count
                FROM system_metrics
                WHERE session_id = ?
                AND datetime(timestamp) > datetime('now', '-{} hours')
            """.format(hours),
                (self.session_id,),
            )

            row = cursor.fetchone()
            conn.close()

            return {
                "avg_cpu_percent": row[0] or 0,
                "max_cpu_percent": row[1] or 0,
                "avg_memory_percent": row[2] or 0,
                "max_memory_percent": row[3] or 0,
                "avg_disk_percent": row[4] or 0,
                "sample_count": row[5] or 0,
            }

    def store_log(self, log_entry: Dict[str, Any]) -> None:
        """Store a single log record into the logs table."""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """
                INSERT INTO logs
                    (session_id, timestamp, level, logger, message,
                     correlation_id, source, thread_id, process_id, extra)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    self.session_id,
                    log_entry.get("timestamp", ""),
                    log_entry.get("level", ""),
                    log_entry.get("logger", ""),
                    log_entry.get("message", ""),
                    log_entry.get("correlation_id", ""),
                    log_entry.get("source", ""),
                    log_entry.get("thread"),
                    log_entry.get("process"),
                    json.dumps(log_entry.get("extra")) if log_entry.get("extra") else None,
                ),
            )
            conn.commit()
            conn.close()

    def store_logs_batch(self, logs: List[Dict[str, Any]], source: str = "") -> int:
        """Store a batch of log records into the logs table.

        Args:
            logs: List of log record dicts.
            source: Default source identifier if not present in each entry.

        Returns:
            Number of records stored.
        """
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            for entry in logs:
                conn.execute(
                    """
                    INSERT INTO logs
                        (session_id, timestamp, level, logger, message,
                         correlation_id, source, thread_id, process_id, extra)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        self.session_id,
                        entry.get("timestamp", ""),
                        entry.get("level", ""),
                        entry.get("logger", ""),
                        entry.get("message", ""),
                        entry.get("correlation_id", ""),
                        entry.get("source", source),
                        entry.get("thread"),
                        entry.get("process"),
                        json.dumps(
                            {
                                k: v
                                for k, v in entry.items()
                                if k
                                not in {
                                    "timestamp",
                                    "level",
                                    "logger",
                                    "message",
                                    "correlation_id",
                                    "source",
                                    "thread",
                                    "process",
                                }
                            }
                        )
                        or None,
                    ),
                )
            conn.commit()
            conn.close()
        return len(logs)

    def get_logs(
        self,
        limit: int = 100,
        level: str = "",
        correlation_id: str = "",
        source: str = "",
    ) -> List[Dict[str, Any]]:
        """Query the logs table with optional filters.

        Args:
            limit: Maximum number of records to return.
            level: Filter by log level (e.g. ``"ERROR"``).
            correlation_id: Filter by correlation / request ID.
            source: Filter by source identifier.

        Returns:
            List of log record dicts, most recent first.
        """
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            clauses: List[str] = []
            params: List[Any] = []

            if level:
                clauses.append("level = ?")
                params.append(level.upper())
            if correlation_id:
                clauses.append("correlation_id = ?")
                params.append(correlation_id)
            if source:
                clauses.append("source = ?")
                params.append(source)

            where = ""
            if clauses:
                where = "WHERE " + " AND ".join(clauses)

            cursor = conn.execute(
                f"SELECT * FROM logs {where} ORDER BY timestamp DESC LIMIT ?",
                params + [limit],
            )

            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results

    def get_logs_by_correlation(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Return all log entries for a correlation ID, ordered by time."""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                "SELECT * FROM logs WHERE correlation_id = ? ORDER BY timestamp ASC",
                (correlation_id,),
            )

            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results

    def cleanup_old_logs(self, max_files: int):
        """Clean up old log files to prevent disk space issues."""
        log_files = list(self.logs_dir.glob("app_logs_*.jsonl"))

        if len(log_files) > max_files:
            # Sort by modification time and remove oldest
            log_files.sort(key=lambda f: f.stat().st_mtime)
            files_to_remove = log_files[:-max_files]

            for file_path in files_to_remove:
                try:
                    file_path.unlink()
                except OSError:
                    pass  # File might be in use, skip

    def cleanup_old_data(self, days: int = 30):
        """Clean up old data from database."""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)

            # Clean old metrics
            conn.execute("""
                DELETE FROM system_metrics
                WHERE datetime(timestamp) < datetime('now', '-{} days')
            """.format(days))

            conn.execute("""
                DELETE FROM operation_metrics
                WHERE datetime(timestamp) < datetime('now', '-{} days')
            """.format(days))

            # Clean old sessions
            conn.execute("""
                DELETE FROM sessions
                WHERE datetime(start_time) < datetime('now', '-{} days')
            """.format(days))

            conn.commit()
            conn.close()

    def close_session(self):
        """Mark the current session as ended."""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """
                UPDATE sessions
                SET end_time = ?
                WHERE session_id = ?
            """,
                (datetime.now(timezone.utc).isoformat(), self.session_id),
            )
            conn.commit()
            conn.close()

    def export_data(self, output_file: str, format: str = "json"):
        """Export monitoring data to file."""
        data = {
            "session_id": self.session_id,
            "export_time": datetime.now(timezone.utc).isoformat(),
            "metrics": self.get_recent_metrics(limit=10000),
            "operations": self.get_recent_operations(limit=10000),
            "summary": {
                "operation_summary": self.get_operation_summary(),
                "system_trends": self.get_system_trends(),
            },
        }

        output_path = Path(output_file)

        if format.lower() == "json":
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        return output_path
