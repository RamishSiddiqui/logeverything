"""
Tests for the UDPTransportHandler.

Covers per-record datagram sending, oversized packet dropping,
and fire-and-forget (zero retries) configuration.
"""

import json
from unittest.mock import MagicMock, patch

from logeverything.transport.udp import UDPTransportHandler


class TestUDPSendBatch:
    """Verify each record is sent as a separate datagram."""

    @patch("logeverything.transport.udp.socket.socket")
    def test_send_batch_sends_individual_datagrams(self, mock_socket_cls):
        """Each record in the batch should produce a separate sendto call."""
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock

        handler = UDPTransportHandler(
            host="localhost",
            port=5141,
            source_name="test-app",
            flush_interval=999,
        )
        try:
            records = [{"msg": "a"}, {"msg": "b"}, {"msg": "c"}]
            handler._send_batch(records)

            assert mock_sock.sendto.call_count == 3
            for i, call in enumerate(mock_sock.sendto.call_args_list):
                data, addr = call[0]
                assert json.loads(data.decode("utf-8")) == records[i]
                assert addr == ("localhost", 5141)
        finally:
            handler.close()


class TestUDPOversizedPacket:
    """Verify packets exceeding max_packet_size are silently dropped."""

    @patch("logeverything.transport.udp.socket.socket")
    def test_oversized_packet_silently_dropped(self, mock_socket_cls):
        """Records whose JSON encoding exceeds max_packet_size must not be sent."""
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock

        handler = UDPTransportHandler(
            host="localhost",
            port=5141,
            source_name="test-app",
            max_packet_size=10,
            flush_interval=999,
        )
        try:
            # This record serialises to well over 10 bytes
            handler._send_batch([{"msg": "this is way too large for the limit"}])
            mock_sock.sendto.assert_not_called()
        finally:
            handler.close()


class TestUDPFireAndForget:
    """Verify the handler is configured with zero retries."""

    @patch("logeverything.transport.udp.socket.socket")
    def test_fire_and_forget_no_retries(self, mock_socket_cls):
        """The internal LogBuffer must have max_retries == 0."""
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock

        handler = UDPTransportHandler(
            host="localhost",
            port=5141,
            source_name="test-app",
            flush_interval=999,
        )
        try:
            assert handler._buffer._max_retries == 0
        finally:
            handler.close()
