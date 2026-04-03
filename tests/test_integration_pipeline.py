"""Integration test: full logging pipeline through HTTP transport."""

import json
import logging
from unittest.mock import patch


class TestHTTPPipeline:
    """End-to-end: Python logger -> HTTPTransportHandler -> mock HTTP endpoint."""

    @patch("logeverything.transport.http.urllib.request.urlopen")
    def test_logger_to_http_transport(self, mock_urlopen):
        """A log record emitted via a standard logger reaches the HTTP endpoint."""
        from logeverything.transport.http import HTTPTransportHandler

        handler = HTTPTransportHandler(
            endpoint="http://localhost:8999/api/ingest/logs",
            source_name="integration-test",
            flush_interval=999,
            batch_size=50,
        )
        try:
            py_logger = logging.getLogger("integration_test_pipeline")
            py_logger.handlers.clear()
            py_logger.addHandler(handler)
            py_logger.setLevel(logging.DEBUG)
            py_logger.propagate = False

            py_logger.info("hello from integration test")
            handler.flush()

            assert mock_urlopen.called
            # Aggregate all logs across potential multiple calls
            all_logs = []
            for call in mock_urlopen.call_args_list:
                req = call[0][0]
                body = json.loads(req.data.decode("utf-8"))
                assert body["source"] == "integration-test"
                all_logs.extend(body["logs"])
            assert len(all_logs) >= 1
            assert all_logs[0]["message"] == "hello from integration test"
            assert all_logs[0]["level"] == "INFO"
        finally:
            py_logger.removeHandler(handler)
            handler.close()

    @patch("logeverything.transport.http.urllib.request.urlopen")
    def test_multiple_records_batched(self, mock_urlopen):
        """Multiple records are batched and sent via HTTP POST(s)."""
        from logeverything.transport.http import HTTPTransportHandler

        handler = HTTPTransportHandler(
            endpoint="http://localhost:8999/api/ingest/logs",
            source_name="batch-test",
            flush_interval=999,
            batch_size=50,
        )
        try:
            py_logger = logging.getLogger("integration_test_batch")
            py_logger.handlers.clear()
            py_logger.addHandler(handler)
            py_logger.setLevel(logging.DEBUG)
            py_logger.propagate = False

            for i in range(5):
                py_logger.info(f"msg-{i}")

            handler.flush()

            assert mock_urlopen.called
            # The background flush thread may split records across multiple
            # HTTP calls, so aggregate all logs from every call.
            all_logs = []
            for call in mock_urlopen.call_args_list:
                req = call[0][0]
                body = json.loads(req.data.decode("utf-8"))
                all_logs.extend(body["logs"])
            assert len(all_logs) == 5
        finally:
            py_logger.removeHandler(handler)
            handler.close()

    @patch("logeverything.transport.http.urllib.request.urlopen")
    def test_logeverything_logger_to_http(self, mock_urlopen):
        """A LogEverything Logger instance works with HTTPTransportHandler."""
        from logeverything import Logger
        from logeverything.transport.http import HTTPTransportHandler

        handler = HTTPTransportHandler(
            endpoint="http://localhost:8999/api/ingest/logs",
            source_name="le-integration",
            flush_interval=999,
            batch_size=50,
        )
        try:
            logger = Logger("integration_le", auto_setup=True)
            # Access the underlying Python logger and add transport handler
            logger._logger.addHandler(handler)

            logger.info("from logeverything Logger")
            handler.flush()

            assert mock_urlopen.called
            # Aggregate all logs across potential multiple calls
            all_logs = []
            for call in mock_urlopen.call_args_list:
                req = call[0][0]
                body = json.loads(req.data.decode("utf-8"))
                all_logs.extend(body["logs"])
            assert len(all_logs) >= 1
            found = any(
                "from logeverything Logger" in entry.get("message", "") for entry in all_logs
            )
            assert found, f"Expected message not found in {all_logs}"
        finally:
            handler.close()
