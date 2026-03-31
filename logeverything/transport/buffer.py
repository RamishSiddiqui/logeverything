"""
Shared batching / retry buffer for LogEverything transports.

Provides a thread-safe queue with a background flush thread, batching,
exponential-backoff retry, and configurable back-pressure policy.
Follows the same daemon-thread pattern as ``AsyncQueueHandler``.
"""

import logging
import threading
import time
from collections import deque
from typing import Any, Callable, Dict, List, Literal, Optional

logger = logging.getLogger(__name__)


class LogBuffer:
    """
    Thread-safe log buffer with background batched flushing.

    Args:
        send_batch: Callable that accepts a ``List[Dict]`` and ships them.
                    Must raise on failure so the buffer can retry.
        max_buffer_size: Maximum number of records to hold in memory.
        batch_size: Number of records per batch sent to ``send_batch``.
        flush_interval: Seconds between automatic flush attempts.
        max_retries: How many times to retry a failed batch (with backoff).
        backpressure: What to do when the buffer is full — ``"drop"`` silently
                      discards the oldest records; ``"block"`` waits for space.
    """

    def __init__(
        self,
        send_batch: Callable[[List[Dict[str, Any]]], None],
        max_buffer_size: int = 10000,
        batch_size: int = 100,
        flush_interval: float = 5.0,
        max_retries: int = 3,
        backpressure: Literal["drop", "block"] = "drop",
    ):
        self._send_batch = send_batch
        self._max_buffer_size = max_buffer_size
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._max_retries = max_retries
        self._backpressure = backpressure

        self._queue: deque = deque(maxlen=max_buffer_size if backpressure == "drop" else None)
        self._lock = threading.Lock()
        self._not_full = threading.Condition(self._lock)
        self._not_empty = threading.Condition(self._lock)

        self._closed = False
        self._flush_thread: Optional[threading.Thread] = None
        self._start_flush_thread()

    # --- Public API ---

    def put(self, record: Dict[str, Any]) -> None:
        """Add a serialised log record to the buffer."""
        if self._closed:
            return

        with self._lock:
            if self._backpressure == "block":
                while len(self._queue) >= self._max_buffer_size and not self._closed:
                    self._not_full.wait(timeout=1.0)
            self._queue.append(record)
            self._not_empty.notify()

    def flush(self) -> None:
        """Immediately drain the buffer and send all batches."""
        self._drain()

    def close(self) -> None:
        """Flush remaining records and stop the background thread."""
        self._closed = True
        # Wake up the flush thread so it can exit
        with self._lock:
            self._not_empty.notify_all()
            self._not_full.notify_all()
        if self._flush_thread and self._flush_thread.is_alive():
            self._flush_thread.join(timeout=10.0)
        # Final drain
        self._drain()

    # --- Internals ---

    def _start_flush_thread(self) -> None:
        self._flush_thread = threading.Thread(
            target=self._flush_loop, name="logeverything-buffer-flush", daemon=True
        )
        self._flush_thread.start()

    def _flush_loop(self) -> None:
        while not self._closed:
            with self._lock:
                self._not_empty.wait(timeout=self._flush_interval)
            if self._closed and not self._queue:
                break
            self._drain()

    def _drain(self) -> None:
        """Pull batches from the queue and send them."""
        while True:
            batch = self._take_batch()
            if not batch:
                break
            self._send_with_retry(batch)

    def _take_batch(self) -> List[Dict[str, Any]]:
        with self._lock:
            batch: List[Dict[str, Any]] = []
            for _ in range(min(self._batch_size, len(self._queue))):
                batch.append(self._queue.popleft())
            if batch and self._backpressure == "block":
                self._not_full.notify_all()
            return batch

    def _send_with_retry(self, batch: List[Dict[str, Any]]) -> None:
        delay = 0.5
        for attempt in range(self._max_retries + 1):
            try:
                self._send_batch(batch)
                return
            except Exception:
                if attempt == self._max_retries:
                    logger.warning(
                        "LogBuffer: dropping %d records after %d retries",
                        len(batch),
                        self._max_retries,
                    )
                    return
                time.sleep(delay)
                delay = min(delay * 2, 30.0)
