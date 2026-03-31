"""
Tests for the LogBuffer batching and retry buffer.

Covers basic operations, exponential-backoff retry, back-pressure policies,
thread safety, and automatic flush behaviour.
"""

import threading
import time
from unittest.mock import MagicMock, patch

from logeverything.transport.buffer import LogBuffer

# ---------------------------------------------------------------------------
# TestLogBufferBasicOperations
# ---------------------------------------------------------------------------


class TestLogBufferBasicOperations:
    """Verify core put / flush / close semantics."""

    def test_put_queues_records(self):
        """put() should append records to the internal queue."""
        send = MagicMock()
        buf = LogBuffer(send_batch=send, flush_interval=999)
        try:
            buf.put({"msg": "a"})
            buf.put({"msg": "b"})
            assert len(buf._queue) == 2
        finally:
            buf.close()

    def test_flush_drains_all_records(self):
        """flush() should send every queued record immediately."""
        sent_batches = []
        send = MagicMock(side_effect=lambda batch: sent_batches.append(list(batch)))
        buf = LogBuffer(send_batch=send, batch_size=10, flush_interval=999)
        try:
            for i in range(5):
                buf.put({"i": i})
            buf.flush()
            all_records = [rec for batch in sent_batches for rec in batch]
            assert len(all_records) == 5
            assert len(buf._queue) == 0
        finally:
            buf.close()

    def test_close_drains_remaining(self):
        """close() should flush any remaining records before stopping."""
        sent_batches = []
        send = MagicMock(side_effect=lambda batch: sent_batches.append(list(batch)))
        buf = LogBuffer(send_batch=send, batch_size=10, flush_interval=999)
        for i in range(3):
            buf.put({"i": i})
        buf.close()

        all_records = [rec for batch in sent_batches for rec in batch]
        assert len(all_records) == 3

    def test_put_after_close_is_noop(self):
        """put() on a closed buffer should silently discard the record."""
        send = MagicMock()
        buf = LogBuffer(send_batch=send, flush_interval=999)
        buf.close()

        buf.put({"msg": "late"})
        assert len(buf._queue) == 0


# ---------------------------------------------------------------------------
# TestLogBufferRetry
# ---------------------------------------------------------------------------


class TestLogBufferRetry:
    """Verify exponential-backoff retry logic in _send_with_retry."""

    @patch("logeverything.transport.buffer.time.sleep")
    def test_exponential_backoff_delays(self, mock_sleep):
        """On repeated failures the delay should double: 0.5, 1.0, 2.0."""
        send = MagicMock(side_effect=Exception("boom"))
        buf = LogBuffer(send_batch=send, max_retries=3, flush_interval=999)
        try:
            buf.put({"msg": "fail"})
            buf.flush()

            delays = [call.args[0] for call in mock_sleep.call_args_list]
            assert delays == [0.5, 1.0, 2.0]
        finally:
            buf.close()

    @patch("logeverything.transport.buffer.time.sleep")
    def test_no_retry_on_success(self, mock_sleep):
        """When send_batch succeeds on the first attempt, sleep is never called."""
        send = MagicMock()
        buf = LogBuffer(send_batch=send, max_retries=3, flush_interval=999)
        try:
            buf.put({"msg": "ok"})
            buf.flush()
            mock_sleep.assert_not_called()
        finally:
            buf.close()

    @patch("logeverything.transport.buffer.time.sleep")
    def test_send_called_max_retries_plus_one(self, mock_sleep):
        """send_batch should be called max_retries + 1 times total on persistent failure."""
        send = MagicMock(side_effect=Exception("boom"))
        max_retries = 3
        buf = LogBuffer(send_batch=send, max_retries=max_retries, flush_interval=999)
        try:
            buf.put({"msg": "fail"})
            buf.flush()
            assert send.call_count == max_retries + 1
        finally:
            buf.close()


# ---------------------------------------------------------------------------
# TestLogBufferBackpressure
# ---------------------------------------------------------------------------


class TestLogBufferBackpressure:
    """Verify drop and block back-pressure policies."""

    def test_drop_mode_discards_oldest(self):
        """In drop mode the deque maxlen silently drops the oldest records."""
        send = MagicMock()
        buf = LogBuffer(
            send_batch=send,
            max_buffer_size=3,
            backpressure="drop",
            flush_interval=999,
        )
        try:
            for i in range(5):
                buf.put({"i": i})

            # Only the most recent 3 should remain (deque maxlen behaviour)
            remaining = list(buf._queue)
            assert len(remaining) == 3
            assert remaining[0]["i"] == 2
            assert remaining[1]["i"] == 3
            assert remaining[2]["i"] == 4
        finally:
            buf.close()

    def test_block_mode_unblocks_after_drain(self):
        """In block mode put() should block until space is available.

        The background flush thread's ``_take_batch`` pops records from the
        queue *before* calling ``send_batch``, so gating ``send_batch``
        alone is insufficient to keep the queue full.

        Strategy: stop the background flush thread, fill the queue to
        capacity with direct ``deque.append`` (bypassing ``put`` which
        notifies the flush thread), then verify that a ``put()`` from
        another thread blocks until we manually drain.
        """
        sent_batches = []
        send = MagicMock(side_effect=lambda batch: sent_batches.append(list(batch)))
        buf = LogBuffer(
            send_batch=send,
            max_buffer_size=2,
            batch_size=2,
            backpressure="block",
            flush_interval=999,
        )
        try:
            # Stop the flush thread so it cannot interfere
            buf._closed = True
            with buf._lock:
                buf._not_empty.notify_all()
            buf._flush_thread.join(timeout=5.0)
            # Re-open the buffer for the rest of the test
            buf._closed = False

            # Fill the queue to capacity directly (no notify)
            with buf._lock:
                buf._queue.append({"i": 0})
                buf._queue.append({"i": 1})

            unblocked = threading.Event()

            def blocked_put():
                buf.put({"i": 2})
                unblocked.set()

            t = threading.Thread(target=blocked_put)
            t.start()

            # The third put should be blocked because the queue is full
            assert not unblocked.wait(timeout=0.5)

            # Drain the queue so the blocked put can proceed
            buf.flush()
            assert unblocked.wait(timeout=3.0)
            t.join(timeout=3.0)
        finally:
            buf.close()


# ---------------------------------------------------------------------------
# TestLogBufferThreadSafety
# ---------------------------------------------------------------------------


class TestLogBufferThreadSafety:
    """Verify thread-safe concurrent access."""

    def test_concurrent_puts_all_received(self):
        """5 threads x 100 records each should produce exactly 500 records."""
        received = []
        lock = threading.Lock()

        def send(batch):
            with lock:
                received.extend(batch)

        buf = LogBuffer(send_batch=send, batch_size=50, flush_interval=999)

        def produce(tid):
            for j in range(100):
                buf.put({"tid": tid, "j": j})

        threads = [threading.Thread(target=produce, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        buf.close()
        assert len(received) == 500


# ---------------------------------------------------------------------------
# TestLogBufferAutoFlush
# ---------------------------------------------------------------------------


class TestLogBufferAutoFlush:
    """Verify the background flush thread fires automatically."""

    def test_auto_flush_sends_within_interval(self):
        """With a short flush_interval the background thread should drain the queue."""
        send = MagicMock()
        buf = LogBuffer(send_batch=send, flush_interval=0.05)
        try:
            buf.put({"msg": "auto"})
            # Wait long enough for at least one flush cycle
            time.sleep(0.3)
            assert send.called
        finally:
            buf.close()
