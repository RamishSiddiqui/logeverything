"""
Tests for timed and size-based rotation handlers with compression support.

Covers TimedRotatingFileHandler and FileHandler compress functionality.
"""

import gzip
import logging
import os
import shutil
import tempfile
import time

import pytest

from logeverything.handlers import FileHandler, TimedRotatingFileHandler


@pytest.fixture()
def tmp_log_dir():
    """Create a temporary directory for log files and clean up afterwards."""
    dirpath = tempfile.mkdtemp()
    yield dirpath
    shutil.rmtree(dirpath, ignore_errors=True)


class TestTimedRotatingFileHandler:
    """Tests for TimedRotatingFileHandler."""

    def test_timed_rollover_renames_with_date_suffix(self, tmp_log_dir):
        """Force rollover by setting _rollover_at to the past and verify date-suffixed file."""
        import datetime as _dt

        log_path = os.path.join(tmp_log_dir, "app.log")
        handler = TimedRotatingFileHandler(log_path, when="midnight")

        # Write an initial record so the base file exists
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="before rollover",
            args=(),
            exc_info=None,
        )
        handler.emit(record)
        assert os.path.exists(log_path)

        # Force rollover by moving the deadline into the past
        handler._rollover_at = _dt.datetime.now() - _dt.timedelta(seconds=1)

        record2 = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="after rollover",
            args=(),
            exc_info=None,
        )
        handler.emit(record2)

        # The rotated file should carry today's date suffix
        today_suffix = _dt.datetime.now().strftime("%Y-%m-%d")
        rotated_candidates = [
            f for f in os.listdir(tmp_log_dir) if today_suffix in f and f != "app.log"
        ]
        assert len(rotated_candidates) >= 1, (
            f"Expected a rotated file with suffix {today_suffix}, found: {os.listdir(tmp_log_dir)}"
        )

        # The base file should still exist (reopened after rollover)
        assert os.path.exists(log_path)
        handler.close()

    def test_retention_deletes_old_files(self, tmp_log_dir):
        """Create fake old rotated files and verify they are deleted on rollover."""
        import datetime as _dt

        log_path = os.path.join(tmp_log_dir, "app.log")
        handler = TimedRotatingFileHandler(log_path, when="midnight", retention_days=7)

        # Write something so the base file exists
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="seed",
            args=(),
            exc_info=None,
        )
        handler.emit(record)

        # Create a fake old rotated file with an old modification time
        old_file = os.path.join(tmp_log_dir, "app.log.2020-01-01")
        with open(old_file, "w") as f:
            f.write("old data")
        # Set mtime to 60 days ago
        old_ts = time.time() - 60 * 86400
        os.utime(old_file, (old_ts, old_ts))

        # Create a recent rotated file that should NOT be deleted
        recent_file = os.path.join(tmp_log_dir, "app.log.recent")
        with open(recent_file, "w") as f:
            f.write("recent data")

        # Force rollover
        handler._rollover_at = _dt.datetime.now() - _dt.timedelta(seconds=1)
        record2 = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="trigger cleanup",
            args=(),
            exc_info=None,
        )
        handler.emit(record2)

        # Old file should be gone
        assert not os.path.exists(old_file), "Old rotated file should have been deleted"
        # Recent file should remain
        assert os.path.exists(recent_file), "Recent rotated file should not be deleted"
        handler.close()

    def test_compressed_rotation_creates_gz(self, tmp_log_dir):
        """Verify that compress=True produces a .gz file after rollover."""
        import datetime as _dt

        log_path = os.path.join(tmp_log_dir, "app.log")
        handler = TimedRotatingFileHandler(log_path, when="midnight", compress=True)

        # Write initial data
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="data to compress",
            args=(),
            exc_info=None,
        )
        handler.emit(record)

        # Force rollover
        handler._rollover_at = _dt.datetime.now() - _dt.timedelta(seconds=1)
        record2 = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="post rollover",
            args=(),
            exc_info=None,
        )
        handler.emit(record2)

        # Give the background thread a moment to finish
        time.sleep(1.0)

        gz_files = [f for f in os.listdir(tmp_log_dir) if f.endswith(".gz")]
        assert len(gz_files) >= 1, (
            f"Expected at least one .gz file, found: {os.listdir(tmp_log_dir)}"
        )

        # Verify the .gz file is a valid gzip archive
        gz_path = os.path.join(tmp_log_dir, gz_files[0])
        with gzip.open(gz_path, "rb") as f:
            content = f.read()
        assert b"data to compress" in content
        handler.close()

    def test_invalid_when_raises_value_error(self, tmp_log_dir):
        """Passing an invalid 'when' value should raise ValueError."""
        log_path = os.path.join(tmp_log_dir, "app.log")
        with pytest.raises(ValueError, match="Invalid 'when' value"):
            TimedRotatingFileHandler(log_path, when="invalid")


class TestFileHandlerCompress:
    """Tests for FileHandler size-based rotation with compress support."""

    def test_size_rotation_with_compress(self, tmp_log_dir):
        """Test existing FileHandler with compress=True and small max_size."""
        log_path = os.path.join(tmp_log_dir, "sized.log")
        handler = FileHandler(
            log_path,
            max_size=100,
            backup_count=3,
            compress=True,
        )

        # Write enough data to trigger rotation
        for i in range(20):
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=f"Line {i}: padding to exceed max_size threshold easily {'x' * 50}",
                args=(),
                exc_info=None,
            )
            handler.emit(record)

        # Give background compression thread time to finish
        time.sleep(1.0)

        files = os.listdir(tmp_log_dir)
        gz_files = [f for f in files if f.endswith(".gz")]
        assert len(gz_files) >= 1, (
            f"Expected at least one .gz file from size-based rotation, found: {files}"
        )

        # Verify the .gz file is a valid gzip archive
        gz_path = os.path.join(tmp_log_dir, gz_files[0])
        with gzip.open(gz_path, "rb") as f:
            content = f.read()
        assert len(content) > 0
        handler.close()
