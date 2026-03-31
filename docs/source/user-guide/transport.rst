Log Transport
=============

LogEverything provides network transport handlers that ship structured log
records from your application processes to the :ref:`dashboard <dashboard-ingestion>` or any
central collector.  Each transport is a ``logging.Handler`` subclass — add it
to any logger's handler list and records flow automatically.

Overview
--------

.. code-block:: text

   Application Process             Network              Dashboard / Collector
   ┌────────────────────┐                               ┌────────────────────┐
   │ Logger + Handlers   │──── HTTP POST (batched) ────►│ POST /api/ingest   │
   │ - ConsoleHandler    │──── TCP (newline JSON)  ────►│     /logs          │
   │ - HTTPTransport     │──── UDP (datagrams)     ────►│                    │
   └────────────────────┘                               └────────────────────┘

All transports share a common internal buffer
(:class:`~logeverything.transport.buffer.LogBuffer`) that provides:

- **Batching** — records are grouped before being sent.
- **Background flushing** — a daemon thread drains the buffer periodically.
- **Exponential-backoff retry** — failed sends are retried automatically.
- **Back-pressure** — configurable ``"drop"`` (default) or ``"block"`` policy
  when the buffer is full.

HTTP Transport (primary)
------------------------

Uses only the standard library (``urllib.request``) — zero external deps.
POSTs batched JSON to the dashboard's ``POST /api/ingest/logs`` endpoint.

.. executable-code::

   from logeverything.transport.http import HTTPTransportHandler

   handler = HTTPTransportHandler(
       endpoint="http://localhost:8999/api/ingest/logs",
       batch_size=50,
       flush_interval=2.0,
       source_name="web-worker-1",
   )
   print(f"Created: {handler}")
   print(f"Endpoint: {handler.endpoint}")
   print(f"Source: {handler.source_name}")
   handler.close()

**Usage with a logger:**

.. code-block:: python

   from logeverything import Logger
   from logeverything.transport.http import HTTPTransportHandler

   log = Logger("myapp")
   transport = HTTPTransportHandler(
       "http://dashboard:8999/api/ingest/logs",
       api_key="secret",              # sent as Authorization: Bearer <key>
       source_name="api-server-1",
   )
   log.add_handler(transport)

   log.info("This goes to console AND the dashboard")

**All options:**

.. list-table::
   :header-rows: 1

   * - Parameter
     - Default
     - Description
   * - ``endpoint``
     - *(required)*
     - URL to POST batched logs to
   * - ``api_key``
     - ``None``
     - Optional Bearer token
   * - ``batch_size``
     - ``50``
     - Records per HTTP request
   * - ``flush_interval``
     - ``2.0``
     - Seconds between automatic flushes
   * - ``source_name``
     - ``"pid-<PID>"``
     - Identifier for this process
   * - ``max_retries``
     - ``3``
     - Retry count for failed POSTs
   * - ``timeout``
     - ``10.0``
     - HTTP request timeout in seconds

TCP Transport
-------------

Newline-delimited JSON over a persistent TCP socket.  Suitable for
high-reliability use within a private network.

.. code-block:: python

   from logeverything.transport.tcp import TCPTransportHandler

   handler = TCPTransportHandler(
       host="collector.internal",
       port=5140,
       batch_size=100,
       flush_interval=5.0,
   )

The socket reconnects automatically on failure.

UDP Transport
-------------

Fire-and-forget JSON datagrams.  Each record is sent as a single UDP packet
(up to ~64 KB).  Suitable for high-throughput scenarios where occasional loss
is acceptable.

.. code-block:: python

   from logeverything.transport.udp import UDPTransportHandler

   handler = UDPTransportHandler(
       host="collector.internal",
       port=5141,
       max_packet_size=65000,
   )

.. _dashboard-ingestion:

Dashboard Ingestion
-------------------

The LogEverything monitoring API server and the standalone dashboard both
expose a ``POST /api/ingest/logs`` endpoint:

.. code-block:: text

   POST /api/ingest/logs
   Content-Type: application/json

   {
     "logs": [
       {
         "timestamp": "2025-02-17T12:00:00",
         "level": "INFO",
         "logger": "myapp",
         "message": "User logged in",
         "correlation_id": "a1b2c3d4e5f67890",
         "thread": 12345,
         "process": 6789,
         "source": "api-server-1"
       }
     ],
     "source": "api-server-1"
   }

   → {"accepted": 1}

The dashboard stores logs in SQLite and broadcasts to connected WebSocket
clients for real-time display.

**Query endpoints:**

- ``GET /api/logs?limit=100&level=ERROR&correlation_id=abc&source=worker-1``
- ``GET /api/logs/trace/{correlation_id}`` — returns all log entries for a
  single correlation ID, ordered by time.

Choosing a Transport
--------------------

.. list-table::
   :header-rows: 1

   * - Transport
     - Protocol
     - Reliability
     - Throughput
     - Deps
     - Best for
   * - HTTP
     - HTTP POST
     - High (retry + ack)
     - Medium
     - stdlib only
     - Dashboard integration
   * - TCP
     - TCP stream
     - High (persistent)
     - High
     - stdlib only
     - Private network collectors
   * - UDP
     - UDP datagram
     - Best-effort
     - Very high
     - stdlib only
     - High-volume, loss-tolerant

Installing
----------

All transports use only the standard library — no extra dependencies.

.. code-block:: bash

   pip install logeverything   # transports included

.. seealso::

   :doc:`correlation`
      How correlation IDs are included in every transported record.

   :doc:`integrations`
      Middleware that auto-generates correlation IDs for requests.

   :doc:`../api/transport`
      Full API reference for all transport classes.
