"""
Tests for logeverything.monitoring.storage.MonitoringStorage.

Covers initialization, metrics storage/retrieval, log storage/querying,
data cleanup, session management, and thread safety.

Requires psutil to be installed.
"""

import json
import os
import shutil
import sqlite3
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

psutil = pytest.importorskip("psutil")

from logeverything.monitoring.metrics import OperationMetrics, SystemMetrics  # noqa: E402
from logeverything.monitoring.storage import MonitoringStorage  # noqa: E402

# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def _make_system_metrics(**overrides) -> SystemMetrics:
    """Return a ``SystemMetrics`` instance with sensible defaults.

    Any keyword argument overrides the corresponding field.
    """
    defaults = dict(
        timestamp=datetime.now(timezone.utc).isoformat(),
        cpu_percent=25.0,
        cpu_count=8,
        cpu_freq_current=2400.0,
        load_average=[1.0, 0.8, 0.6],
        memory_total=16_000_000_000,
        memory_available=8_000_000_000,
        memory_used=8_000_000_000,
        memory_percent=50.0,
        swap_total=4_000_000_000,
        swap_used=1_000_000_000,
        swap_percent=25.0,
        disk_total=500_000_000_000,
        disk_used=250_000_000_000,
        disk_free=250_000_000_000,
        disk_percent=50.0,
        disk_read_bytes=1_000_000,
        disk_write_bytes=2_000_000,
        disk_read_count=500,
        disk_write_count=300,
        network_bytes_sent=5_000_000,
        network_bytes_recv=10_000_000,
        network_packets_sent=1000,
        network_packets_recv=2000,
        process_cpu_percent=5.0,
        process_memory_rss=100_000_000,
        process_memory_vms=200_000_000,
        process_memory_percent=0.6,
        process_num_threads=4,
        process_num_fds=None,
        boot_time=1_700_000_000.0,
        uptime_seconds=86400.0,
    )
    defaults.update(overrides)
    return SystemMetrics(**defaults)


def _make_operation_metrics(**overrides) -> OperationMetrics:
    """Return an ``OperationMetrics`` instance with sensible defaults."""
    defaults = dict(
        timestamp=datetime.now(timezone.utc).isoformat(),
        operation_id="op_001",
        operation_name="test_operation",
        duration_seconds=0.5,
        cpu_time=0.1,
        memory_delta=1024,
        success=True,
        error_message=None,
        custom_metrics=None,
    )
    defaults.update(overrides)
    return OperationMetrics(**defaults)


# ============================================================================
# Test classes
# ============================================================================


class TestStorageInit(unittest.TestCase):
    """Verify that MonitoringStorage.__init__ sets up the expected directory structure,
    database file, tables, and session record."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_creates_subdirectories(self):
        """Init must create logs/, metrics/, and operations/ under base_dir."""
        base = Path(self.tmpdir) / "monitoring"
        MonitoringStorage(base)

        self.assertTrue((base / "logs").is_dir())
        self.assertTrue((base / "metrics").is_dir())
        self.assertTrue((base / "operations").is_dir())

    def test_creates_database_file(self):
        """Init must create monitoring.db inside base_dir."""
        base = Path(self.tmpdir) / "monitoring"
        MonitoringStorage(base)

        db_path = base / "monitoring.db"
        self.assertTrue(db_path.exists())

    def test_creates_four_tables(self):
        """The database must contain system_metrics, operation_metrics, sessions, and logs."""
        base = Path(self.tmpdir) / "monitoring"
        MonitoringStorage(base)

        conn = sqlite3.connect(base / "monitoring.db")
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = sorted(row[0] for row in cursor.fetchall())
        conn.close()

        self.assertIn("system_metrics", tables)
        self.assertIn("operation_metrics", tables)
        self.assertIn("sessions", tables)
        self.assertIn("logs", tables)

    def test_records_session(self):
        """Init must insert a row into the sessions table with the current session_id."""
        base = Path(self.tmpdir) / "monitoring"
        storage = MonitoringStorage(base)

        conn = sqlite3.connect(base / "monitoring.db")
        cursor = conn.execute(
            "SELECT session_id, start_time, pid FROM sessions WHERE session_id = ?",
            (storage.session_id,),
        )
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], storage.session_id)
        # start_time should be a non-empty string
        self.assertTrue(len(row[1]) > 0)
        # pid should be the current process
        self.assertEqual(row[2], os.getpid())


class TestStoreAndRetrieveMetrics(unittest.TestCase):
    """Test storing and retrieving system and operation metrics."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = MonitoringStorage(Path(self.tmpdir) / "monitoring")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # -- system metrics --

    def test_store_and_get_system_metrics(self):
        """store_metrics followed by get_recent_metrics should return the stored data."""
        metrics = _make_system_metrics(cpu_percent=42.0, memory_percent=60.0)
        self.storage.store_metrics(metrics)

        results = self.storage.get_recent_metrics(limit=10)
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0]["cpu_percent"], 42.0)
        self.assertAlmostEqual(results[0]["memory_percent"], 60.0)

    def test_get_recent_metrics_respects_limit(self):
        """get_recent_metrics should return at most ``limit`` rows."""
        for i in range(5):
            self.storage.store_metrics(_make_system_metrics(cpu_percent=float(i)))

        results = self.storage.get_recent_metrics(limit=3)
        self.assertEqual(len(results), 3)

    def test_get_recent_metrics_ordered_desc(self):
        """Results should be ordered by timestamp descending (most recent first)."""
        ts_old = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
        ts_new = datetime.now(timezone.utc).isoformat()

        self.storage.store_metrics(_make_system_metrics(timestamp=ts_old, cpu_percent=1.0))
        self.storage.store_metrics(_make_system_metrics(timestamp=ts_new, cpu_percent=99.0))

        results = self.storage.get_recent_metrics(limit=10)
        self.assertEqual(len(results), 2)
        # First result should be the newer one
        self.assertAlmostEqual(results[0]["cpu_percent"], 99.0)

    def test_full_data_json_stored(self):
        """full_data column should contain the complete SystemMetrics as JSON."""
        m = _make_system_metrics(cpu_percent=42.0)
        self.storage.store_metrics(m)
        results = self.storage.get_recent_metrics(limit=1)
        full_data = json.loads(results[0]["full_data"])
        self.assertAlmostEqual(full_data["cpu_percent"], 42.0)

    # -- operation metrics --

    def test_store_and_get_operations(self):
        """store_operation_metrics + get_recent_operations round-trip."""
        op = _make_operation_metrics(operation_name="my_op", duration_seconds=1.5, success=True)
        self.storage.store_operation_metrics(op)

        results = self.storage.get_recent_operations(limit=10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["operation_name"], "my_op")
        self.assertAlmostEqual(results[0]["duration_seconds"], 1.5)

    def test_get_recent_operations_respects_limit(self):
        """get_recent_operations should cap rows at the requested limit."""
        for i in range(5):
            self.storage.store_operation_metrics(_make_operation_metrics(operation_id=f"op_{i}"))

        results = self.storage.get_recent_operations(limit=2)
        self.assertEqual(len(results), 2)

    def test_operation_custom_metrics_serialised(self):
        """custom_metrics dict should round-trip through JSON serialisation."""
        op = _make_operation_metrics(custom_metrics={"key": "value", "num": 42})
        self.storage.store_operation_metrics(op)
        results = self.storage.get_recent_operations(limit=1)
        custom = json.loads(results[0]["custom_metrics"])
        self.assertEqual(custom["key"], "value")
        self.assertEqual(custom["num"], 42)

    # -- operation summary aggregation --

    def test_operation_summary_aggregation(self):
        """get_operation_summary should compute correct aggregates."""
        now = datetime.now(timezone.utc).isoformat()

        self.storage.store_operation_metrics(
            _make_operation_metrics(
                timestamp=now, operation_name="alpha", duration_seconds=1.0, success=True
            )
        )
        self.storage.store_operation_metrics(
            _make_operation_metrics(
                timestamp=now,
                operation_name="alpha",
                duration_seconds=3.0,
                success=False,
                error_message="boom",
            )
        )
        self.storage.store_operation_metrics(
            _make_operation_metrics(
                timestamp=now, operation_name="beta", duration_seconds=2.0, success=True
            )
        )

        summary = self.storage.get_operation_summary(hours=24)
        self.assertEqual(summary["total_operations"], 3)
        self.assertEqual(summary["successful_operations"], 2)
        self.assertEqual(summary["failed_operations"], 1)
        self.assertAlmostEqual(summary["average_duration"], 2.0)
        self.assertAlmostEqual(summary["max_duration"], 3.0)
        # top_operations should list the grouped operation names
        top_names = [op["name"] for op in summary["top_operations"]]
        self.assertIn("alpha", top_names)
        self.assertIn("beta", top_names)

    def test_operation_summary_empty(self):
        """get_operation_summary on an empty database should return zeroed values."""
        summary = self.storage.get_operation_summary(hours=24)
        self.assertEqual(summary["total_operations"], 0)
        self.assertEqual(summary["successful_operations"], 0)
        self.assertEqual(summary["failed_operations"], 0)
        self.assertEqual(summary["average_duration"], 0)
        self.assertEqual(summary["max_duration"], 0)
        self.assertEqual(summary["top_operations"], [])

    # -- system trends averaging --

    def test_system_trends_averaging(self):
        """get_system_trends should compute correct averages and maximums."""
        now = datetime.now(timezone.utc).isoformat()

        self.storage.store_metrics(
            _make_system_metrics(
                timestamp=now, cpu_percent=20.0, memory_percent=40.0, disk_percent=30.0
            )
        )
        self.storage.store_metrics(
            _make_system_metrics(
                timestamp=now, cpu_percent=40.0, memory_percent=60.0, disk_percent=50.0
            )
        )

        trends = self.storage.get_system_trends(hours=24)
        self.assertAlmostEqual(trends["avg_cpu_percent"], 30.0)
        self.assertAlmostEqual(trends["max_cpu_percent"], 40.0)
        self.assertAlmostEqual(trends["avg_memory_percent"], 50.0)
        self.assertAlmostEqual(trends["max_memory_percent"], 60.0)
        self.assertAlmostEqual(trends["avg_disk_percent"], 40.0)
        self.assertEqual(trends["sample_count"], 2)

    def test_system_trends_empty(self):
        """get_system_trends on an empty database should return zeroed values."""
        trends = self.storage.get_system_trends(hours=24)
        self.assertEqual(trends["avg_cpu_percent"], 0)
        self.assertEqual(trends["max_cpu_percent"], 0)
        self.assertEqual(trends["sample_count"], 0)


class TestStoreLogs(unittest.TestCase):
    """Test log storage and filtered retrieval."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = MonitoringStorage(Path(self.tmpdir) / "monitoring")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_store_log_single(self):
        """store_log should persist a single log entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "INFO",
            "logger": "mylogger",
            "message": "hello world",
            "correlation_id": "req-123",
            "source": "app",
        }
        self.storage.store_log(entry)

        logs = self.storage.get_logs(limit=10)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["message"], "hello world")
        self.assertEqual(logs[0]["level"], "INFO")

    def test_store_logs_batch_returns_count(self):
        """store_logs_batch should return the number of records stored."""
        entries = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "DEBUG",
                "message": f"msg {i}",
            }
            for i in range(5)
        ]
        count = self.storage.store_logs_batch(entries, source="batch_src")
        self.assertEqual(count, 5)

        logs = self.storage.get_logs(limit=100)
        self.assertEqual(len(logs), 5)

    def test_store_logs_batch_applies_default_source(self):
        """When a log entry has no source, store_logs_batch should use the provided default."""
        entries = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "message": "no source field",
            },
        ]
        self.storage.store_logs_batch(entries, source="default_source")

        logs = self.storage.get_logs(limit=10)
        self.assertEqual(logs[0]["source"], "default_source")

    def test_get_logs_filter_by_level(self):
        """get_logs with a level filter should only return matching rows."""
        self.storage.store_log(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "ERROR",
                "message": "err",
            }
        )
        self.storage.store_log(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "message": "info",
            }
        )

        error_logs = self.storage.get_logs(limit=100, level="ERROR")
        self.assertEqual(len(error_logs), 1)
        self.assertEqual(error_logs[0]["message"], "err")

    def test_get_logs_filter_by_level_case_insensitive(self):
        """get_logs should accept lowercase level and match case-insensitively."""
        self.storage.store_log(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "WARNING",
                "message": "warn",
            }
        )

        results = self.storage.get_logs(limit=100, level="warning")
        self.assertEqual(len(results), 1)

    def test_get_logs_filter_by_source(self):
        """get_logs with a source filter should only return matching rows."""
        self.storage.store_log(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "message": "from A",
                "source": "A",
            }
        )
        self.storage.store_log(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "message": "from B",
                "source": "B",
            }
        )

        a_logs = self.storage.get_logs(limit=100, source="A")
        self.assertEqual(len(a_logs), 1)
        self.assertEqual(a_logs[0]["message"], "from A")

    def test_get_logs_filter_by_correlation_id(self):
        """get_logs with a correlation_id filter should only return matching rows."""
        self.storage.store_log(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "message": "corr match",
                "correlation_id": "abc-123",
            }
        )
        self.storage.store_log(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "message": "no match",
                "correlation_id": "xyz-999",
            }
        )

        filtered = self.storage.get_logs(limit=100, correlation_id="abc-123")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["message"], "corr match")

    def test_get_logs_combined_filters(self):
        """get_logs should support combining multiple filters."""
        self.storage.store_log(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "ERROR",
                "message": "target",
                "source": "svc",
                "correlation_id": "c1",
            }
        )
        self.storage.store_log(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "message": "other",
                "source": "svc",
                "correlation_id": "c1",
            }
        )

        filtered = self.storage.get_logs(
            limit=100, level="ERROR", source="svc", correlation_id="c1"
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["message"], "target")

    def test_get_logs_by_correlation(self):
        """get_logs_by_correlation returns all entries for the given correlation_id."""
        cid = "request-42"
        for i in range(3):
            self.storage.store_log(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": "INFO",
                    "message": f"step {i}",
                    "correlation_id": cid,
                }
            )
        # Also store an unrelated log
        self.storage.store_log(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "message": "unrelated",
                "correlation_id": "other",
            }
        )

        results = self.storage.get_logs_by_correlation(cid)
        self.assertEqual(len(results), 3)
        for row in results:
            self.assertEqual(row["correlation_id"], cid)

    def test_get_logs_by_correlation_ordered_asc(self):
        """get_logs_by_correlation should return results ordered by timestamp ascending."""
        cid = "req-asc"
        ts_old = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
        ts_new = datetime.now(timezone.utc).isoformat()

        self.storage.store_log(
            {"timestamp": ts_new, "level": "INFO", "message": "second", "correlation_id": cid}
        )
        self.storage.store_log(
            {"timestamp": ts_old, "level": "INFO", "message": "first", "correlation_id": cid}
        )

        results = self.storage.get_logs_by_correlation(cid)
        self.assertEqual(results[0]["message"], "first")
        self.assertEqual(results[1]["message"], "second")


class TestCleanup(unittest.TestCase):
    """Test data cleanup and session closing."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = MonitoringStorage(Path(self.tmpdir) / "monitoring")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_cleanup_old_data_deletes_old_rows(self):
        """cleanup_old_data should remove rows whose timestamp is older than the threshold."""
        # Insert a metric with a very old timestamp
        old_ts = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        recent_ts = datetime.now(timezone.utc).isoformat()

        self.storage.store_metrics(_make_system_metrics(timestamp=old_ts))
        self.storage.store_metrics(_make_system_metrics(timestamp=recent_ts))

        self.storage.store_operation_metrics(_make_operation_metrics(timestamp=old_ts))
        self.storage.store_operation_metrics(_make_operation_metrics(timestamp=recent_ts))

        # Cleanup rows older than 30 days
        self.storage.cleanup_old_data(days=30)

        # Only the recent rows should survive
        metrics = self.storage.get_recent_metrics(limit=100)
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0]["timestamp"], recent_ts)

        ops = self.storage.get_recent_operations(limit=100)
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0]["timestamp"], recent_ts)

    def test_cleanup_old_data_deletes_old_sessions(self):
        """cleanup_old_data should also remove old session rows."""
        db_path = self.storage.db_path

        # Manually insert a very old session
        conn = sqlite3.connect(db_path)
        old_start = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        conn.execute(
            "INSERT INTO sessions (session_id, start_time, pid) VALUES (?, ?, ?)",
            ("old_session", old_start, os.getpid()),
        )
        conn.commit()
        conn.close()

        self.storage.cleanup_old_data(days=30)

        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT session_id FROM sessions WHERE session_id = 'old_session'")
        row = cursor.fetchone()
        conn.close()

        self.assertIsNone(row, "Old session should have been deleted")

    def test_close_session_sets_end_time(self):
        """close_session should populate the end_time column for the current session."""
        self.storage.close_session()

        conn = sqlite3.connect(self.storage.db_path)
        cursor = conn.execute(
            "SELECT end_time FROM sessions WHERE session_id = ?",
            (self.storage.session_id,),
        )
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertIsNotNone(row[0], "end_time should be set after close_session")
        self.assertTrue(len(row[0]) > 0, "end_time should be a non-empty ISO string")


class TestThreadSafety(unittest.TestCase):
    """Verify that concurrent writes do not corrupt the database."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = MonitoringStorage(Path(self.tmpdir) / "monitoring")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_concurrent_metric_inserts(self):
        """5 threads each inserting 20 metrics should yield 100 total rows without errors."""
        errors = []
        num_threads = 5
        inserts_per_thread = 20

        def _insert_metrics(thread_idx):
            try:
                for i in range(inserts_per_thread):
                    self.storage.store_metrics(
                        _make_system_metrics(cpu_percent=float(thread_idx * 100 + i))
                    )
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_insert_metrics, args=(t,)) for t in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        self.assertEqual(errors, [], f"Threads raised errors: {errors}")

        results = self.storage.get_recent_metrics(limit=200)
        self.assertEqual(len(results), num_threads * inserts_per_thread)

    def test_concurrent_operation_inserts(self):
        """5 threads each inserting 20 operations should yield 100 total rows."""
        errors = []
        num_threads = 5
        inserts_per_thread = 20

        def _insert_operations(thread_idx):
            try:
                for i in range(inserts_per_thread):
                    self.storage.store_operation_metrics(
                        _make_operation_metrics(
                            operation_id=f"op_{thread_idx}_{i}",
                            operation_name=f"thread_{thread_idx}",
                        )
                    )
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=_insert_operations, args=(t,)) for t in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        self.assertEqual(errors, [], f"Threads raised errors: {errors}")

        results = self.storage.get_recent_operations(limit=200)
        self.assertEqual(len(results), num_threads * inserts_per_thread)

    def test_concurrent_log_inserts(self):
        """5 threads each inserting 20 logs should yield 100 total rows."""
        errors = []
        num_threads = 5
        inserts_per_thread = 20

        def _insert_logs(thread_idx):
            try:
                for i in range(inserts_per_thread):
                    self.storage.store_log(
                        {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "level": "INFO",
                            "message": f"thread {thread_idx} msg {i}",
                            "source": f"thread_{thread_idx}",
                        }
                    )
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_insert_logs, args=(t,)) for t in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        self.assertEqual(errors, [], f"Threads raised errors: {errors}")

        results = self.storage.get_logs(limit=200)
        self.assertEqual(len(results), num_threads * inserts_per_thread)


if __name__ == "__main__":
    unittest.main()
