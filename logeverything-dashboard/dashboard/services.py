"""
Dashboard Services for LogEverything Monitoring
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class MonitoringService:
    """Service for reading monitoring data from storage."""

    def __init__(self, settings):
        """Initialize with settings object"""
        from .config import get_connection_manager

        self.settings = settings
        self.connection_manager = get_connection_manager()

        # Get the active connection
        self._update_connection_paths()

        # Create directories if they don't exist
        if self.logs_dir:
            self.logs_dir.mkdir(parents=True, exist_ok=True)

    def _get_jsonl_files(self, logs_dir: Optional[Path] = None) -> List[Path]:
        """Return JSONL log files sorted by modification time (newest first).

        Globs both active (``*.jsonl``) and rotated (``*.jsonl.*``) files,
        excluding compressed ``.gz`` archives which cannot be read as plain
        text.

        Args:
            logs_dir: Directory to scan.  Falls back to ``self.logs_dir``.

        Returns:
            List of Path objects sorted by mtime descending.
        """
        target = logs_dir or self.logs_dir
        if not target or not target.exists():
            return []
        files: List[Path] = []
        files.extend(target.glob("*.jsonl"))
        files.extend(p for p in target.glob("*.jsonl.*") if not p.name.endswith(".gz"))
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return files

    def _update_connection_paths(self):
        """Update paths based on the active connection."""
        active_conn = self.connection_manager.get_active_connection()

        if not active_conn:
            # Use default path from settings
            self.data_dir = Path(self.settings.monitoring_data_dir)
            self.db_path = self.data_dir / "monitoring.db"
            self.logs_dir = self.data_dir / "logs"
            self.connection_type = "local"
            return

        if active_conn.get("type") == "local":
            # Local file-based connection
            self.data_dir = Path(active_conn.get("data_dir", self.settings.monitoring_data_dir))
            self.db_path = self.data_dir / active_conn.get("database_file", "monitoring.db")
            self.logs_dir = self.data_dir / "logs"
            self.connection_type = "local"
        elif active_conn.get("type") == "api":
            # API connection
            self.base_url = active_conn.get("base_url")
            self.api_key = active_conn.get("api_key")
            self.connection_type = "api"
            # No file paths for API connections
            self.data_dir = None
            self.db_path = None
            self.logs_dir = None
        else:
            # Unknown connection type, use default
            self.data_dir = Path(self.settings.monitoring_data_dir)
            self.db_path = self.data_dir / "monitoring.db"
            self.logs_dir = self.data_dir / "logs"
            self.connection_type = "local"

    async def initialize(self):
        """Initialize the monitoring service.

        Called on application startup to prepare monitoring data.
        """
        active_conn = self.connection_manager.get_active_connection()
        conn_name = active_conn.get("name", "Default") if active_conn else "Default"

        print(f"Initializing monitoring service with connection: {conn_name}")

        if self.connection_type == "local":
            # Local file-based connection
            print(f"Using data directory: {self.data_dir}")

            # Create directories if they don't exist
            if self.logs_dir:
                self.logs_dir.mkdir(parents=True, exist_ok=True)

            # Check if we have access to the database
            if self.db_path and self.db_path.exists():
                print(f"Found database at {self.db_path}")
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    print(f"Database tables: {[t[0] for t in tables]}")
                    conn.close()
                except Exception as e:
                    print(f"Error accessing database: {e}")
            else:
                print(f"No database found at {self.db_path}, will use logs only")

            # Check for log files
            if self.logs_dir and self.logs_dir.exists():
                log_files = self._get_jsonl_files()
                print(f"Found {len(log_files)} log files")
                if log_files:
                    print(f"Most recent log file: {log_files[-1].name}")
            else:
                print(f"No logs directory found at {self.logs_dir}")

            # Read session info
            session_file = self.data_dir / "session_info.json"
            if session_file.exists():
                try:
                    with open(session_file, "r") as f:
                        session_info = json.load(f)
                    print(f"Session info: {session_info.get('session_id', 'unknown')}")
                except Exception as e:
                    print(f"Error reading session info: {e}")

        elif self.connection_type == "api":
            # API connection
            print(f"Using API connection: {self.base_url}")
            # TODO: Test API connection by making a request to the health endpoint

        return True

    async def cleanup(self):
        """Clean up resources when shutting down."""
        print("Cleaning up monitoring service resources")

        if self.connection_type == "api":
            # Close any active API sessions
            try:
                # Assuming we might have an active aiohttp session
                # In a real implementation, we would store the session and close it here
                pass
            except Exception as e:
                print(f"Error cleaning up API connection: {e}")

        return True

    async def switch_connection(self, connection_id: str) -> bool:
        """Switch to a different connection.

        This method:
        1. Sets the connection as active in the connection manager
        2. Updates internal paths and connection settings
        3. Re-initializes the service with the new connection

        Args:
            connection_id: ID of the connection to switch to

        Returns:
            bool: True if switch was successful, False otherwise
        """
        print(f"Switching to connection {connection_id}")
        success = self.connection_manager.set_active_connection(connection_id)

        if success:
            # Update internal paths and settings
            self._update_connection_paths()

            # Re-initialize with the new connection
            try:
                await self.initialize()
                print(f"Successfully switched to connection {connection_id}")
                return True
            except Exception as e:
                print(f"Error initializing with new connection: {e}")
                return False

        print(f"Failed to switch to connection {connection_id}")
        return False

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics."""
        try:
            if self.connection_type == "api":
                # For API connections, fetch from the API
                try:
                    import aiohttp

                    url = f"{self.base_url}/api/system-stats"
                    headers = {}

                    if self.api_key:
                        headers["Authorization"] = f"Bearer {self.api_key}"

                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                return data
                            else:
                                print(f"API error: {response.status} - {await response.text()}")
                                return self._get_default_stats()
                except Exception as e:
                    print(f"Error fetching system stats from API: {e}")
                    return self._get_default_stats()

            # For local connections
            if not self.db_path or not self.db_path.exists():
                return self._get_default_stats()

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Get latest system metrics
                cursor.execute(
                    """
                    SELECT * FROM system_metrics
                    ORDER BY timestamp DESC
                    LIMIT 1
                """
                )
                latest = cursor.fetchone()

                if not latest:
                    return self._get_default_stats()

                return {
                    "cpu_usage": latest["cpu_percent"] or 0,
                    "memory_usage": latest["memory_percent"] or 0,
                    "disk_usage": latest["disk_percent"] or 0,
                    "network_in": latest["network_bytes_recv"] or 0,
                    "network_out": latest["network_bytes_sent"] or 0,
                    "process_memory": (latest["process_memory_rss"] or 0) / (1024 * 1024),  # MB
                    "timestamp": latest["timestamp"] or datetime.now().isoformat(),
                }
        except Exception as e:
            print(f"Error getting system stats: {e}")
            return self._get_default_stats()

    def _get_default_stats(self) -> Dict[str, Any]:
        """Return default stats when no data available."""
        return {
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0,
            "network_in": 0,
            "network_out": 0,
            "process_memory": 0,
            "timestamp": datetime.now().isoformat(),
        }

    async def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        try:
            stats = {"total_operations": 0, "successful_operations": 0, "failed_operations": 0}

            if self.db_path.exists():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # Get operation counts
                    cursor.execute(
                        """
                        SELECT
                            COUNT(*) as total,
                            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                            SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed
                        FROM operation_metrics
                    """
                    )
                    row = cursor.fetchone()

                    if row:
                        stats["total_operations"] = row[0] or 0
                        stats["successful_operations"] = row[1] or 0
                        stats["failed_operations"] = row[2] or 0

            # Count log entries
            log_count = 0
            if self.logs_dir.exists():
                for log_file in self._get_jsonl_files():
                    try:
                        with open(log_file, "r") as f:
                            log_count += sum(1 for _ in f)
                    except Exception:
                        pass

            stats["total_logs"] = log_count
            return stats

        except Exception:
            return {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "total_logs": 0,
            }

    def get_recent_operations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent operations."""
        try:
            if not self.db_path.exists():
                return []

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM operation_metrics
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    (limit,),
                )

                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent log entries."""
        try:
            logs = []

            if not self.logs_dir.exists():
                return logs

            # Get the most recent log file
            log_files = self._get_jsonl_files()

            for log_file in log_files:
                if len(logs) >= limit:
                    break

                try:
                    with open(log_file, "r") as f:
                        for line in f:
                            if len(logs) >= limit:
                                break
                            try:
                                log_entry = json.loads(line.strip())
                                logs.append(log_entry)
                            except json.JSONDecodeError:
                                continue
                except Exception:
                    continue

            # Sort by timestamp (most recent first)
            logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return logs[:limit]

        except Exception:
            return []

    def get_session_info(self) -> Dict[str, Any]:
        """Get session information."""
        try:
            session_file = self.data_dir / "session_info.json"
            if session_file.exists():
                with open(session_file, "r") as f:
                    return json.load(f)
        except Exception:
            pass

        return {
            "session_id": "unknown",
            "start_time": datetime.now().isoformat(),
            "working_directory": str(self.data_dir),
            "monitoring_config": {},
        }

    async def get_operations(
        self,
        limit: int = 50,
        offset: int = 0,
        hours: Optional[int] = None,
        operation_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get recent operations with optional time and name filters."""
        try:
            # For API connections, fetch from the API
            if self.connection_type == "api":
                try:
                    import aiohttp

                    url = f"{self.base_url}/api/operations"
                    params: Dict[str, Any] = {"limit": limit, "offset": offset}

                    headers = {}
                    if self.api_key:
                        headers["Authorization"] = f"Bearer {self.api_key}"

                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                return data.get("operations", [])
                            else:
                                print(f"API error: {response.status} - {await response.text()}")
                                return []
                except Exception as e:
                    print(f"Error fetching operations from API: {e}")
                    return []

            # For local connections
            if not self.db_path or not self.db_path.exists():
                return []

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                where_clauses = []
                params_list: list = []

                if hours is not None:
                    where_clauses.append("datetime(timestamp) > datetime('now', ?)")
                    params_list.append(f"-{hours} hours")

                if operation_name:
                    where_clauses.append("operation_name = ?")
                    params_list.append(operation_name)

                where_sql = ""
                if where_clauses:
                    where_sql = "WHERE " + " AND ".join(where_clauses)

                query = f"""
                    SELECT * FROM operation_metrics
                    {where_sql}
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                """
                params_list.extend([limit, offset])

                cursor.execute(query, params_list)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting operations: {e}")
            return []

    async def get_logs(
        self,
        limit: int = 100,
        level: Optional[str] = None,
        correlation_id: Optional[str] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        hours: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get recent log entries with optional filters."""
        try:
            # For API connections, fetch from the API
            if self.connection_type == "api":
                try:
                    import aiohttp

                    url = f"{self.base_url}/api/logs"
                    params: Dict[str, Any] = {"limit": limit}
                    if level:
                        params["level"] = level
                    if correlation_id:
                        params["correlation_id"] = correlation_id
                    if source:
                        params["source"] = source

                    headers = {}
                    if self.api_key:
                        headers["Authorization"] = f"Bearer {self.api_key}"

                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                return data.get("logs", [])
                            else:
                                print(f"API error: {response.status} - {await response.text()}")
                                return []
                except Exception as e:
                    print(f"Error fetching logs from API: {e}")
                    return []

            # Try DB first if available
            if self.db_path and self.db_path.exists():
                try:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.row_factory = sqlite3.Row
                        cursor = conn.cursor()

                        cursor.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name='logs'"
                        )
                        if cursor.fetchone():
                            where_clauses: list = []
                            params_list: list = []

                            if level:
                                levels = [
                                    lvl.strip().upper() for lvl in level.split(",") if lvl.strip()
                                ]
                                if len(levels) == 1:
                                    where_clauses.append("UPPER(level) = ?")
                                    params_list.append(levels[0])
                                elif levels:
                                    placeholders = ",".join("?" for _ in levels)
                                    where_clauses.append(f"UPPER(level) IN ({placeholders})")
                                    params_list.extend(levels)
                            if correlation_id:
                                where_clauses.append("correlation_id = ?")
                                params_list.append(correlation_id)
                            if source:
                                where_clauses.append("source = ?")
                                params_list.append(source)
                            if search:
                                where_clauses.append("message LIKE ?")
                                params_list.append(f"%{search}%")
                            if hours is not None:
                                where_clauses.append("datetime(timestamp) > datetime('now', ?)")
                                params_list.append(f"-{hours} hours")

                            where_sql = ""
                            if where_clauses:
                                where_sql = "WHERE " + " AND ".join(where_clauses)

                            query = f"""
                                SELECT * FROM logs
                                {where_sql}
                                ORDER BY timestamp DESC
                                LIMIT ?
                            """
                            params_list.append(limit)
                            cursor.execute(query, params_list)
                            return [dict(row) for row in cursor.fetchall()]
                except Exception as e:
                    print(f"Error reading logs from DB: {e}")

            # Fall back to JSONL files
            logs = []

            if not self.logs_dir or not self.logs_dir.exists():
                return logs

            cutoff = None
            if hours is not None:
                cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

            log_files = self._get_jsonl_files()

            for log_file in log_files:
                if len(logs) >= limit:
                    break

                try:
                    with open(log_file, "r") as f:
                        for line in f:
                            if len(logs) >= limit:
                                break
                            try:
                                log_entry = json.loads(line.strip())
                                if level:
                                    allowed = {
                                        lvl.strip().upper()
                                        for lvl in level.split(",")
                                        if lvl.strip()
                                    }
                                    if log_entry.get("level", "").upper() not in allowed:
                                        continue
                                if (
                                    correlation_id
                                    and log_entry.get("correlation_id", "") != correlation_id
                                ):
                                    continue
                                if source and log_entry.get("source", "") != source:
                                    continue
                                if (
                                    search
                                    and search.lower() not in log_entry.get("message", "").lower()
                                ):
                                    continue
                                if cutoff and log_entry.get("timestamp", "") < cutoff:
                                    continue
                                logs.append(log_entry)
                            except json.JSONDecodeError:
                                continue
                except Exception as e:
                    print(f"Error reading log file {log_file}: {e}")
                    continue

            logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return logs[:limit]

        except Exception as e:
            print(f"Error getting logs: {e}")
            return []

    async def get_log_stats(self) -> Dict[str, Any]:
        """Get summary statistics about log entries."""
        default = {"total_count": 0, "error_count": 0, "source_count": 0, "sources": []}
        try:
            if self.connection_type == "api":
                try:
                    import aiohttp

                    url = f"{self.base_url}/api/logs"
                    params: Dict[str, Any] = {"limit": 500}
                    headers = {}
                    if self.api_key:
                        headers["Authorization"] = f"Bearer {self.api_key}"

                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                logs = data.get("logs", [])
                                return self._compute_log_stats(logs)
                    return default
                except Exception as e:
                    print(f"Error fetching log stats from API: {e}")
                    return default

            # Try the database first
            if self.db_path and self.db_path.exists():
                try:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.row_factory = sqlite3.Row
                        cursor = conn.cursor()

                        cursor.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name='logs'"
                        )
                        if cursor.fetchone():
                            cursor.execute("SELECT COUNT(*) FROM logs")
                            total = cursor.fetchone()[0]

                            cursor.execute(
                                "SELECT COUNT(*) FROM logs WHERE UPPER(level) IN "
                                "('ERROR', 'CRITICAL')"
                            )
                            errors = cursor.fetchone()[0]

                            cursor.execute(
                                "SELECT DISTINCT source FROM logs "
                                "WHERE source IS NOT NULL AND source != ''"
                            )
                            sources = [row[0] for row in cursor.fetchall()]

                            return {
                                "total_count": total,
                                "error_count": errors,
                                "source_count": len(sources),
                                "sources": sources,
                            }
                except Exception as e:
                    print(f"Error reading log stats from DB: {e}")

            # Fall back to scanning log files
            if not self.logs_dir or not self.logs_dir.exists():
                return default

            total = 0
            errors = 0
            sources_set: set = set()
            log_files = self._get_jsonl_files()
            for log_file in log_files:
                try:
                    with open(log_file, "r") as f:
                        for line in f:
                            try:
                                entry = json.loads(line.strip())
                                total += 1
                                lvl = entry.get("level", "").upper()
                                if lvl in ("ERROR", "CRITICAL"):
                                    errors += 1
                                src = entry.get("source", "")
                                if src:
                                    sources_set.add(src)
                            except json.JSONDecodeError:
                                continue
                except Exception:
                    continue

            return {
                "total_count": total,
                "error_count": errors,
                "source_count": len(sources_set),
                "sources": list(sources_set),
            }
        except Exception as e:
            print(f"Error getting log stats: {e}")
            return default

    def _compute_log_stats(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute stats from a list of log dicts."""
        sources_set: set = set()
        errors = 0
        for entry in logs:
            lvl = entry.get("level", "").upper()
            if lvl in ("ERROR", "CRITICAL"):
                errors += 1
            src = entry.get("source", "")
            if src:
                sources_set.add(src)
        return {
            "total_count": len(logs),
            "error_count": errors,
            "source_count": len(sources_set),
            "sources": list(sources_set),
        }

    def _ensure_hierarchy_columns(self, conn: sqlite3.Connection) -> None:
        """Add hierarchy columns to the logs table if they don't exist yet."""
        hierarchy_cols = [
            "indent_level INTEGER DEFAULT 0",
            "call_id TEXT DEFAULT ''",
            "parent_call_id TEXT DEFAULT ''",
            "log_type TEXT DEFAULT 'message'",
            "execution_id TEXT DEFAULT ''",
        ]
        for col_def in hierarchy_cols:
            try:
                conn.execute(f"ALTER TABLE logs ADD COLUMN {col_def}")
            except sqlite3.OperationalError:
                pass  # Column already exists

    async def store_ingested_logs(self, logs: List[Dict[str, Any]], source: str) -> int:
        """Store logs received from remote transport handlers.

        Args:
            logs: List of log record dicts.
            source: Identifier of the sending process.

        Returns:
            Number of logs stored.
        """
        if self.connection_type != "local" or not self.db_path:
            return 0

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Ensure the logs table exists
                conn.execute(
                    """
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
                        extra TEXT,
                        indent_level INTEGER DEFAULT 0,
                        call_id TEXT DEFAULT '',
                        parent_call_id TEXT DEFAULT '',
                        log_type TEXT DEFAULT 'message',
                        execution_id TEXT DEFAULT ''
                    )
                    """
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)")
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_logs_correlation ON logs(correlation_id)"
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_source ON logs(source)")

                # Migrate existing tables that lack hierarchy columns
                self._ensure_hierarchy_columns(conn)

                for entry in logs:
                    conn.execute(
                        """
                        INSERT INTO logs
                            (session_id, timestamp, level, logger, message,
                             correlation_id, source, thread_id, process_id, extra,
                             indent_level, call_id, parent_call_id, log_type, execution_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            None,
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
                                        "indent_level",
                                        "call_id",
                                        "parent_call_id",
                                        "log_type",
                                        "execution_id",
                                    }
                                }
                            )
                            or None,
                            entry.get("indent_level", 0),
                            entry.get("call_id", ""),
                            entry.get("parent_call_id", ""),
                            entry.get("log_type", "message"),
                            entry.get("execution_id", ""),
                        ),
                    )
                conn.commit()
            return len(logs)
        except Exception as e:
            print(f"Error storing ingested logs: {e}")
            return 0

    async def get_logs_by_correlation(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Return all log entries matching a correlation ID.

        Args:
            correlation_id: The correlation / request ID to filter by.

        Returns:
            List of matching log dicts ordered by timestamp.
        """
        if self.connection_type == "api":
            try:
                import aiohttp

                url = f"{self.base_url}/api/logs/trace/{correlation_id}"
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data.get("logs", [])
                return []
            except Exception as e:
                print(f"Error fetching trace from API: {e}")
                return []

        if not self.db_path or not self.db_path.exists():
            return []

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT * FROM logs
                    WHERE correlation_id = ?
                    ORDER BY timestamp ASC
                    """,
                    (correlation_id,),
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error querying logs by correlation: {e}")
            return []

    async def get_logs_tree(
        self,
        hours: int = 24,
        execution_id: Optional[str] = None,
        limit: int = 500,
        level: Optional[str] = None,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get logs structured as a tree for hierarchical display.

        Builds a tree from flat logs using indent_level and call_id fields.
        Pairs call_entry/call_exit records by call_id to compute durations.

        Returns:
            List of tree root nodes. Each node is::

                {
                    "log": <log record dict>,
                    "children": [<child nodes>],
                    "duration_ms": <float or None>,
                    "is_call": <bool>,
                }
        """
        # Fetch flat logs ordered by timestamp ascending
        logs = await self.get_logs(
            limit=limit,
            hours=hours,
            level=level,
            source=source,
            correlation_id=correlation_id,
            search=search,
        )
        logs.sort(key=lambda x: x.get("timestamp", ""))

        if execution_id:
            logs = [entry for entry in logs if entry.get("execution_id") == execution_id]

        # Index call_exit timestamps by call_id for duration calculation
        exit_times: Dict[str, str] = {}
        entry_times: Dict[str, str] = {}
        for log in logs:
            cid = log.get("call_id", "")
            lt = log.get("log_type", "message")
            if lt == "call_exit" and cid:
                exit_times[cid] = log.get("timestamp", "")
            elif lt == "call_entry" and cid:
                entry_times[cid] = log.get("timestamp", "")

        def _compute_duration(call_id: str) -> Optional[float]:
            start = entry_times.get(call_id)
            end = exit_times.get(call_id)
            if not start or not end:
                return None
            try:
                fmt = "%Y-%m-%dT%H:%M:%S"
                # Handle fractional seconds
                s = start[:19]
                e = end[:19]
                t0 = datetime.strptime(s, fmt)
                t1 = datetime.strptime(e, fmt)
                return round((t1 - t0).total_seconds() * 1000, 2)
            except Exception:
                return None

        # Build tree using a stack-based algorithm on indent_level
        roots: List[Dict[str, Any]] = []
        stack: List[Dict[str, Any]] = []  # nodes at each depth

        for log in logs:
            indent = log.get("indent_level", 0) or 0
            log_type = log.get("log_type", "message")
            call_id = log.get("call_id", "")

            # Skip call_exit records — they're used for duration calc only
            if log_type == "call_exit":
                continue

            is_call = log_type == "call_entry"
            duration = _compute_duration(call_id) if is_call else None

            node: Dict[str, Any] = {
                "log": log,
                "children": [],
                "duration_ms": duration,
                "is_call": is_call,
            }

            # Pop stack until we find the parent for this indent level
            while stack and stack[-1]["log"].get("indent_level", 0) >= indent:
                stack.pop()

            if stack:
                stack[-1]["children"].append(node)
            else:
                roots.append(node)

            # Push this node onto stack if it's a call (has children)
            if is_call:
                stack.append(node)

        return roots

    async def get_system_stats_history(
        self, hours: int = 24, max_points: int = 200
    ) -> Dict[str, Any]:
        """Get historical system metrics for charting."""
        try:
            if not self.db_path or not self.db_path.exists():
                return {"metrics": []}

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT timestamp, cpu_percent, memory_percent, disk_percent,
                           network_bytes_recv, process_memory_rss
                    FROM system_metrics
                    WHERE datetime(timestamp) > datetime('now', ?)
                    ORDER BY timestamp ASC
                    """,
                    (f"-{hours} hours",),
                )
                rows = [dict(r) for r in cursor.fetchall()]

            # Downsample to max_points
            if len(rows) > max_points:
                step = len(rows) / max_points
                rows = [rows[int(i * step)] for i in range(max_points)]

            return {"metrics": rows}
        except Exception as e:
            print(f"Error getting system stats history: {e}")
            return {"metrics": []}

    async def get_detailed_system_stats(self) -> Dict[str, Any]:
        """Get full system metrics from the latest row's full_data JSON."""
        try:
            if not self.db_path or not self.db_path.exists():
                return {}

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM system_metrics ORDER BY timestamp DESC LIMIT 1")
                row = cursor.fetchone()
                if not row:
                    return {}

                data = dict(row)
                # Parse full_data JSON if present
                full_data_raw = data.get("full_data")
                if full_data_raw:
                    try:
                        full_data = (
                            json.loads(full_data_raw)
                            if isinstance(full_data_raw, str)
                            else full_data_raw
                        )
                        data.update(full_data)
                    except (json.JSONDecodeError, TypeError):
                        pass

                return data
        except Exception as e:
            print(f"Error getting detailed system stats: {e}")
            return {}

    async def get_operation_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get aggregated operation analytics."""
        default = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "avg_duration": 0.0,
            "max_duration": 0.0,
            "top_operations": [],
        }
        try:
            if not self.db_path or not self.db_path.exists():
                return default

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                time_filter = f"-{hours} hours"

                # Aggregate totals
                cursor.execute(
                    """
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                           SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
                           AVG(duration_seconds) as avg_duration,
                           MAX(duration_seconds) as max_duration
                    FROM operation_metrics
                    WHERE datetime(timestamp) > datetime('now', ?)
                    """,
                    (time_filter,),
                )
                agg = cursor.fetchone()

                # Top operations
                cursor.execute(
                    """
                    SELECT operation_name,
                           COUNT(*) as count,
                           AVG(duration_seconds) as avg_duration,
                           SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failures
                    FROM operation_metrics
                    WHERE datetime(timestamp) > datetime('now', ?)
                    GROUP BY operation_name
                    ORDER BY count DESC
                    LIMIT 10
                    """,
                    (time_filter,),
                )
                top_ops = [dict(r) for r in cursor.fetchall()]

            return {
                "total": (agg["total"] or 0) if agg else 0,
                "successful": (agg["successful"] or 0) if agg else 0,
                "failed": (agg["failed"] or 0) if agg else 0,
                "avg_duration": round((agg["avg_duration"] or 0), 4) if agg else 0.0,
                "max_duration": round((agg["max_duration"] or 0), 4) if agg else 0.0,
                "top_operations": top_ops,
            }
        except Exception as e:
            print(f"Error getting operation summary: {e}")
            return default

    async def get_log_level_distribution(self, hours: Optional[int] = None) -> Dict[str, int]:
        """Get counts of log entries by level."""
        levels = {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
        try:
            if self.db_path and self.db_path.exists():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='logs'"
                    )
                    if cursor.fetchone():
                        params_list: list = []
                        where = ""
                        if hours is not None:
                            where = "WHERE datetime(timestamp) > datetime('now', ?)"
                            params_list.append(f"-{hours} hours")

                        cursor.execute(
                            f"""
                            SELECT UPPER(level) as level, COUNT(*) as count
                            FROM logs {where}
                            GROUP BY UPPER(level)
                            ORDER BY count DESC
                            """,
                            params_list,
                        )
                        for row in cursor.fetchall():
                            lvl = row[0]
                            if lvl in levels:
                                levels[lvl] = row[1]
                        return levels

            # Fallback to JSONL
            if self.logs_dir and self.logs_dir.exists():
                cutoff = None
                if hours is not None:
                    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
                for log_file in self._get_jsonl_files():
                    try:
                        with open(log_file, "r") as f:
                            for line in f:
                                try:
                                    entry = json.loads(line.strip())
                                    if cutoff and entry.get("timestamp", "") < cutoff:
                                        continue
                                    lvl = entry.get("level", "").upper()
                                    if lvl in levels:
                                        levels[lvl] += 1
                                except json.JSONDecodeError:
                                    continue
                    except Exception:
                        continue
        except Exception as e:
            print(f"Error getting log level distribution: {e}")

        return levels

    async def get_export_data(self, hours: int = 24) -> Dict[str, Any]:
        """Gather all dashboard data for JSON export."""
        try:
            system_stats = await self.get_system_stats()
            history = await self.get_system_stats_history(hours=hours)
            operations = await self.get_operations(limit=500, hours=hours)
            logs = await self.get_logs(limit=500, hours=hours)
            log_stats = await self.get_log_stats()
            op_summary = await self.get_operation_summary(hours=hours)
            session_info = self.get_session_info()

            return {
                "exported_at": datetime.now().isoformat(),
                "time_range_hours": hours,
                "system_stats": system_stats,
                "system_stats_history": history,
                "operation_summary": op_summary,
                "operations": operations,
                "logs": logs,
                "log_stats": log_stats,
                "session_info": session_info,
            }
        except Exception as e:
            print(f"Error building export data: {e}")
            return {"error": str(e)}

    async def test_connection(self, connection_data: Dict[str, Any]) -> tuple[bool, str]:
        """Test a connection configuration.

        Args:
            connection_data: Connection configuration to test

        Returns:
            Tuple of (success, message)
        """
        conn_type = connection_data.get("type")

        if conn_type == "local":
            # Test local connection
            try:
                # Check if the data directory exists
                data_dir = Path(connection_data.get("data_dir", ""))
                if not data_dir.exists():
                    return False, f"Directory not found: {data_dir}"

                if not data_dir.is_dir():
                    return False, f"Path exists but is not a directory: {data_dir}"

                # Check for monitoring database
                db_path = data_dir / connection_data.get("database_file", "monitoring.db")
                logs_dir = data_dir / "logs"

                # Check if either database or logs directory exists
                db_exists = db_path.exists()
                logs_exist = logs_dir.exists() and logs_dir.is_dir()

                if not (db_exists or logs_exist):
                    return (
                        False,
                        f"Neither database ({db_path}) nor logs directory ({logs_dir}) found",
                    )

                # If database exists, check if we can connect to it
                if db_exists:
                    try:
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = cursor.fetchall()
                        conn.close()

                        if not tables:
                            logs_status = "Found" if logs_exist else "Not found"
                            return (
                                True,
                                f"Connected to database but no tables found. "
                                f"Logs directory: {logs_status}",
                            )

                        table_names = [t[0] for t in tables]
                        logs_status = "Found" if logs_exist else "Not found"
                        return (
                            True,
                            f"Connected to database ({len(table_names)} tables). "
                            f"Logs directory: {logs_status}",
                        )
                    except Exception as e:
                        if logs_exist:
                            return (
                                True,
                                f"Database exists but could not be opened: {e}. "
                                "Using logs directory.",
                            )
                        return (
                            False,
                            f"Database exists but could not be opened: {e}. "
                            "No logs directory found.",
                        )

                # If only logs directory exists
                if logs_exist:
                    log_files = self._get_jsonl_files(logs_dir)
                    if not log_files:
                        return True, "Logs directory found but no .jsonl files"
                    return True, f"Found {len(log_files)} log files"

                return False, "Unknown error testing local connection"

            except Exception as e:
                return False, f"Error testing local connection: {e}"

        elif conn_type == "api":
            # Test API connection
            try:
                import aiohttp

                base_url = connection_data.get("base_url")
                if not base_url:
                    return False, "API URL is required"

                # Check if the URL is valid
                if not base_url.startswith(("http://", "https://")):
                    return False, "API URL must start with http:// or https://"

                # Try to connect to the health endpoint
                health_url = f"{base_url.rstrip('/')}/api/health"

                headers = {}
                if connection_data.get("api_key"):
                    headers["Authorization"] = f"Bearer {connection_data.get('api_key')}"

                verify_ssl = connection_data.get("verify_ssl", True)

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            health_url,
                            headers=headers,
                            ssl=verify_ssl,
                            timeout=5,  # Short timeout for the test
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                return (
                                    True,
                                    f"API connection successful: {data.get('status', 'healthy')}",
                                )
                            else:
                                return (
                                    False,
                                    f"API returned status {response.status}: "
                                    f"{await response.text()}",
                                )
                except aiohttp.ClientConnectorError as e:
                    return False, f"Could not connect to API: {e}"
                except aiohttp.ClientResponseError as e:
                    return False, f"API response error: {e}"
                except aiohttp.ClientError as e:
                    return False, f"API client error: {e}"
                except asyncio.TimeoutError:
                    return False, "Connection timed out"

            except Exception as e:
                return False, f"Error testing API connection: {e}"
        else:
            return False, f"Unknown connection type: {conn_type}"


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: List = []

    async def connect(self, websocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: Dict[str, Any], websocket):
        """Send a message to a specific WebSocket."""
        try:
            if isinstance(message, str):
                await websocket.send_text(message)
            else:
                await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        """Broadcast a message to all connected WebSockets."""
        if not self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)

        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_json(self, data: Dict[str, Any]):
        """Broadcast JSON data to all connected WebSockets."""
        await self.broadcast(json.dumps(data))
