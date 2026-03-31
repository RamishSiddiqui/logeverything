"""
Tests for the HTTPTransportHandler.

Covers record serialisation, HTTP POST payload structure, API-key authentication,
emit queuing, and close-flushes-buffer behaviour.
"""

import json
import logging
from unittest.mock import MagicMock, patch

from logeverything.transport.http import HTTPTransportHandler


class TestHTTPRecordToDict:
    """Verify _record_to_dict produces the expected structure."""

    def test_record_to_dict_structure(self):
        """The dict must contain timestamp, level, logger, message, and source."""
        handler = HTTPTransportHandler(
            endpoint="http://localhost:8999/api/ingest/logs",
            source_name="test-app",
            flush_interval=999,
        )
        try:
            record = logging.LogRecord(
                name="test.logger",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="hello",
                args=None,
                exc_info=None,
            )
            result = handler._record_to_dict(record)

            assert "timestamp" in result
            assert result["level"] == "INFO"
            assert result["logger"] == "test.logger"
            assert result["message"] == "hello"
            assert result["source"] == "test-app"
        finally:
            handler.close()


class TestHTTPSendBatch:
    """Verify the HTTP POST payload and headers."""

    @patch("logeverything.transport.http.urllib.request.urlopen")
    def test_send_batch_posts_correct_payload(self, mock_urlopen):
        """The POST body must be JSON with keys 'logs' and 'source'."""
        handler = HTTPTransportHandler(
            endpoint="http://localhost:8999/api/ingest/logs",
            source_name="test-app",
            flush_interval=999,
        )
        try:
            handler._send_batch([{"msg": "test"}])

            mock_urlopen.assert_called_once()
            req = mock_urlopen.call_args[0][0]
            body = json.loads(req.data.decode("utf-8"))

            assert "logs" in body
            assert "source" in body
            assert body["logs"] == [{"msg": "test"}]
            assert body["source"] == "test-app"
        finally:
            handler.close()

    @patch("logeverything.transport.http.urllib.request.urlopen")
    def test_api_key_sent_as_bearer_token(self, mock_urlopen):
        """When api_key is set the Authorization header must be 'Bearer <key>'."""
        handler = HTTPTransportHandler(
            endpoint="http://localhost:8999/api/ingest/logs",
            api_key="secret",
            source_name="test-app",
            flush_interval=999,
        )
        try:
            handler._send_batch([{"msg": "auth-test"}])

            mock_urlopen.assert_called_once()
            req = mock_urlopen.call_args[0][0]
            assert req.get_header("Authorization") == "Bearer secret"
        finally:
            handler.close()


class TestHTTPEmitAndClose:
    """Verify emit queues records and close flushes them."""

    @patch("logeverything.transport.http.urllib.request.urlopen")
    def test_emit_queues_record(self, mock_urlopen):
        """emit() followed by close() should trigger urlopen."""
        handler = HTTPTransportHandler(
            endpoint="http://localhost:8999/api/ingest/logs",
            source_name="test-app",
            flush_interval=999,
        )
        record = logging.LogRecord(
            name="test.logger",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="warn-msg",
            args=None,
            exc_info=None,
        )
        handler.emit(record)
        handler.close()
        assert mock_urlopen.called

    @patch("logeverything.transport.http.urllib.request.urlopen")
    def test_close_flushes_buffer(self, mock_urlopen):
        """close() must send all remaining records."""
        handler = HTTPTransportHandler(
            endpoint="http://localhost:8999/api/ingest/logs",
            source_name="test-app",
            flush_interval=999,
        )
        for i in range(3):
            record = logging.LogRecord(
                name="test.logger",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg=f"msg-{i}",
                args=None,
                exc_info=None,
            )
            handler.emit(record)
        handler.close()

        # Collect all POSTed log entries
        all_logs = []
        for call in mock_urlopen.call_args_list:
            req = call[0][0]
            body = json.loads(req.data.decode("utf-8"))
            all_logs.extend(body["logs"])

        assert len(all_logs) == 3
