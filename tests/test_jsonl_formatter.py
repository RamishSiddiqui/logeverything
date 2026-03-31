"""
Tests for JSONLineFormatter — a logging.Formatter that outputs dashboard-compatible
JSON Lines records.
"""

import json
import logging
import os
import shutil
import tempfile

import pytest

from logeverything.handlers import FileHandler, JSONLineFormatter, TimedRotatingFileHandler


@pytest.fixture()
def tmp_log_dir():
    """Create a temporary directory for log files and clean up afterwards."""
    dirpath = tempfile.mkdtemp()
    yield dirpath
    shutil.rmtree(dirpath, ignore_errors=True)


def _make_record(msg="hello", level=logging.INFO, name="test", **extras):
    """Create a LogRecord with optional extra attributes."""
    record = logging.LogRecord(
        name=name,
        level=level,
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=None,
    )
    for key, value in extras.items():
        setattr(record, key, value)
    return record


class TestJSONLineFormatterOutput:
    """Tests for basic JSON output structure."""

    def test_valid_json_with_expected_fields(self):
        """Output is valid JSON containing the required top-level fields."""
        fmt = JSONLineFormatter()
        record = _make_record("test message")
        result = fmt.format(record)

        # No trailing newline — the handler adds it
        assert not result.endswith("\n")

        data = json.loads(result)
        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert data["message"] == "test message"
        assert "timestamp" in data
        assert "thread" in data
        assert "process" in data

    def test_hierarchy_fields_present(self):
        """Hierarchy attributes on the record appear in the JSON output."""
        fmt = JSONLineFormatter()
        record = _make_record(
            "entry",
            indent_level=2,
            call_id="abc123",
            parent_call_id="parent1",
            log_type="call_entry",
            execution_id="exec-1",
        )
        data = json.loads(fmt.format(record))

        assert data["indent_level"] == 2
        assert data["call_id"] == "abc123"
        assert data["parent_call_id"] == "parent1"
        assert data["log_type"] == "call_entry"
        assert data["execution_id"] == "exec-1"

    def test_correlation_id_from_record(self):
        """correlation_id set on the record is included in output."""
        fmt = JSONLineFormatter()
        record = _make_record("correlated", correlation_id="req-42")
        data = json.loads(fmt.format(record))

        assert data["correlation_id"] == "req-42"

    def test_source_parameter(self):
        """The 'source' constructor parameter tags every record."""
        fmt = JSONLineFormatter(source="my_service")
        record = _make_record("tagged")
        data = json.loads(fmt.format(record))

        assert data["source"] == "my_service"

    def test_include_extras_false_suppresses_extra(self):
        """Setting include_extras=False omits the extra dict entirely."""
        fmt = JSONLineFormatter(include_extras=False)
        record = _make_record("no extras", custom_field="value")
        data = json.loads(fmt.format(record))

        assert "extra" not in data

    def test_structured_data_promoted(self):
        """_structured dict on the record is promoted to top-level keys."""
        fmt = JSONLineFormatter()
        record = _make_record("structured")
        record._structured = {"request_path": "/api/v1", "status_code": 200}
        data = json.loads(fmt.format(record))

        assert data["request_path"] == "/api/v1"
        assert data["status_code"] == 200


class TestJSONLineFormatterIntegration:
    """Integration tests with file-based handlers."""

    def test_filehandler_writes_valid_jsonl(self, tmp_log_dir):
        """FileHandler + JSONLineFormatter produces a valid JSONL file."""
        log_path = os.path.join(tmp_log_dir, "app.jsonl")
        handler = FileHandler(log_path)
        handler.setFormatter(JSONLineFormatter(source="integration"))

        logger = logging.getLogger("test_jsonl_fh")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        try:
            logger.info("first line")
            logger.warning("second line")
            handler.flush()

            with open(log_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            assert len(lines) == 2
            for line in lines:
                data = json.loads(line)
                assert "timestamp" in data
                assert data["source"] == "integration"
        finally:
            logger.removeHandler(handler)
            handler.close()

    def test_timed_rotating_handler_writes_valid_jsonl(self, tmp_log_dir):
        """TimedRotatingFileHandler + JSONLineFormatter writes valid JSONL after rollover."""
        import datetime as _dt

        log_path = os.path.join(tmp_log_dir, "app.jsonl")
        handler = TimedRotatingFileHandler(log_path, when="midnight")
        handler.setFormatter(JSONLineFormatter(source="rotating"))

        logger = logging.getLogger("test_jsonl_trfh")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        try:
            logger.info("before rollover")
            handler.flush()

            # Force a rollover by moving the deadline into the past
            handler._rollover_at = _dt.datetime.now() - _dt.timedelta(seconds=1)
            logger.info("after rollover")
            handler.flush()

            # The active file should have valid JSONL
            with open(log_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            assert len(lines) >= 1
            for line in lines:
                data = json.loads(line)
                assert data["source"] == "rotating"

            # A rotated file should also have valid JSONL
            rotated_files = [
                f
                for f in os.listdir(tmp_log_dir)
                if f.startswith("app.jsonl.") and not f.endswith(".gz")
            ]
            assert len(rotated_files) >= 1
            rotated_path = os.path.join(tmp_log_dir, rotated_files[0])
            with open(rotated_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line.strip())
                        assert data["source"] == "rotating"
        finally:
            logger.removeHandler(handler)
            handler.close()
