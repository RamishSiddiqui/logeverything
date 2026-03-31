.. _remote-logging:

Remote Logging to the Dashboard
================================

This guide walks through shipping logs from one or more application processes
to the LogEverything monitoring dashboard over the network.  By the end you
will have:

1. A running dashboard receiving logs in real time.
2. An application sending structured logs via HTTP transport.
3. Correlation IDs linking related log entries across requests.


Architecture
------------

.. code-block:: text

   ┌─────────────────────────┐           ┌──────────────────────────┐
   │  Application Process    │           │  Dashboard (port 3001)   │
   │                         │   HTTP    │                          │
   │  Logger                 │  POST     │  POST /api/ingest/logs   │
   │   + ConsoleHandler      │──────────►│   ↓                      │
   │   + HTTPTransportHandler│  (batch)  │  SQLite storage          │
   │                         │           │   ↓                      │
   └─────────────────────────┘           │  WebSocket broadcast     │
                                         │   ↓                      │
   ┌─────────────────────────┐           │  Browser (live view)     │
   │  Another Process        │──────────►│                          │
   └─────────────────────────┘           └──────────────────────────┘

Logs are batched in memory, flushed every few seconds, and retried
automatically on failure.  The dashboard stores them in SQLite and pushes
updates to any connected browser via WebSocket.

.. tip::

   **Single-machine alternative:** If your application and the dashboard run on
   the same host, you can skip the HTTP transport entirely.  Use
   ``JSONLineFormatter`` with a rotation handler to write JSONL files directly
   into the dashboard's data directory — the dashboard's Local Connection mode
   will pick them up automatically.  See
   :doc:`rotation-handlers` for setup details.


Step 1 — Start the Dashboard
-----------------------------

.. code-block:: bash

   cd logeverything-dashboard
   pip install -r requirements.txt
   python run_dashboard.py

The dashboard starts on **http://localhost:3001**.  Verify it is running:

.. code-block:: bash

   curl -s http://localhost:3001/api/health
   # {"status": "healthy", ...}

The ingestion endpoint is at ``POST http://localhost:3001/api/ingest/logs``.


Step 2 — Add HTTP Transport to Your Application
------------------------------------------------

Install LogEverything in the application environment (transports use only the
standard library — no extra dependencies):

.. code-block:: bash

   pip install logeverything

Then configure a logger with both a local handler (console) and the HTTP
transport:

.. code-block:: python

   from logeverything import Logger
   from logeverything.transport.http import HTTPTransportHandler

   # Create a logger
   log = Logger("my_app")
   log.configure(level="DEBUG")

   # Add the HTTP transport pointing at the dashboard
   transport = HTTPTransportHandler(
       endpoint="http://localhost:3001/api/ingest/logs",
       source_name="my-app",       # identifies this process in the dashboard
       batch_size=25,              # send every 25 records (or on flush)
       flush_interval=2.0,         # flush at least every 2 seconds
   )
   log.add_handler(transport)

   # Logs now go to console AND the dashboard
   log.info("Application started")
   log.warning("Disk usage at 89%")

Within 2 seconds the dashboard's **Logs** page will show these entries with
source ``my-app``.


Step 3 — Add Decorators for Automatic Tracing
----------------------------------------------

The ``@log`` decorator automatically captures function inputs, outputs, and
timing.  Combined with the transport handler, this data flows to the dashboard:

.. code-block:: python

   from logeverything import Logger
   from logeverything.decorators import log
   from logeverything.transport.http import HTTPTransportHandler

   app_log = Logger("order_service")
   app_log.configure(level="DEBUG")
   app_log.add_handler(HTTPTransportHandler(
       endpoint="http://localhost:3001/api/ingest/logs",
       source_name="order-service",
   ))

   @log(using="order_service")
   def validate_order(order_id, items):
       if not items:
           raise ValueError("Empty order")
       return True

   @log(using="order_service")
   def process_payment(order_id, amount):
       return {"status": "charged", "amount": amount}

   @log(using="order_service")
   def handle_order(order_id, items, amount):
       validate_order(order_id, items)
       process_payment(order_id, amount)
       app_log.info(f"Order {order_id} completed")

   handle_order("ORD-123", ["widget", "gadget"], 49.99)

The dashboard's **Tree** view will reconstruct the call hierarchy:

.. code-block:: text

   ▶ handle_order(order_id='ORD-123', ...) — 12.3 ms
       ▶ validate_order(order_id='ORD-123', ...) — 0.1 ms
       ▶ process_payment(order_id='ORD-123', ...) — 0.8 ms
       INFO  Order ORD-123 completed

.. note::

   The tree view requires the ``HierarchyFilter`` (auto-attached by default)
   and the ``JSONHandler`` or HTTP transport to preserve the hierarchy fields.


Step 4 — Correlation IDs for Request Tracing
---------------------------------------------

For web applications, add framework middleware to generate correlation IDs
that link all logs within a single request.  These IDs are included
automatically in every transported record.

**FastAPI example:**

.. code-block:: python

   from fastapi import FastAPI, Depends
   from logeverything import Logger
   from logeverything.integrations.fastapi import (
       LogEverythingMiddleware,
       get_request_logger,
   )
   from logeverything.transport.http import HTTPTransportHandler

   app = FastAPI()
   app.add_middleware(LogEverythingMiddleware)

   # Configure the logger with transport
   log = Logger("api")
   log.configure(level="DEBUG")
   log.add_handler(HTTPTransportHandler(
       endpoint="http://localhost:3001/api/ingest/logs",
       source_name="api-server",
   ))

   @app.get("/orders/{order_id}")
   async def get_order(order_id: str, rlog=Depends(get_request_logger)):
       rlog.info(f"Fetching order {order_id}")
       order = await fetch_order(order_id)
       rlog.info(f"Found order with {len(order['items'])} items")
       return order

Each request gets a unique correlation ID (from the ``X-Request-ID`` header or
auto-generated).  In the dashboard, click any **correlation ID** link in the
logs table to see the full request trace in the trace modal.


Step 5 — Multiple Processes
---------------------------

Each process uses a different ``source_name`` so the dashboard can distinguish
them.  All processes point at the same dashboard endpoint:

.. code-block:: python

   # worker-1.py
   transport = HTTPTransportHandler(
       endpoint="http://dashboard-host:3001/api/ingest/logs",
       source_name="worker-1",
   )

   # worker-2.py
   transport = HTTPTransportHandler(
       endpoint="http://dashboard-host:3001/api/ingest/logs",
       source_name="worker-2",
   )

   # api-server.py
   transport = HTTPTransportHandler(
       endpoint="http://dashboard-host:3001/api/ingest/logs",
       source_name="api-server",
   )

In the dashboard, use the **Source** filter on the Logs page to isolate logs
from a specific process, or leave it blank to see all sources interleaved.


Transport Options
-----------------

HTTP is the primary transport and the only one the dashboard natively accepts.
TCP and UDP are available for custom collectors.

.. list-table::
   :header-rows: 1

   * - Transport
     - Use case
     - Reliability
   * - ``HTTPTransportHandler``
     - Dashboard integration
     - High (retry + acknowledgement)
   * - ``TCPTransportHandler``
     - Private network collectors
     - High (persistent socket, auto-reconnect)
   * - ``UDPTransportHandler``
     - High-volume, loss-tolerant
     - Best-effort

See :doc:`transport` for full configuration options and comparison.


Configuration Reference
-----------------------

``HTTPTransportHandler`` accepts these parameters:

.. list-table::
   :header-rows: 1

   * - Parameter
     - Default
     - Description
   * - ``endpoint``
     - *(required)*
     - Dashboard URL (``http://host:3001/api/ingest/logs``)
   * - ``api_key``
     - ``None``
     - Bearer token for ``Authorization`` header
   * - ``source_name``
     - ``"pid-<PID>"``
     - Process identifier shown in the dashboard
   * - ``batch_size``
     - ``50``
     - Records per HTTP request
   * - ``flush_interval``
     - ``2.0``
     - Seconds between automatic flushes
   * - ``max_retries``
     - ``3``
     - Retry count with exponential backoff
   * - ``timeout``
     - ``10.0``
     - HTTP request timeout in seconds


Troubleshooting
---------------

**Logs not appearing in the dashboard**

1. Verify the dashboard is running: ``curl http://localhost:3001/api/health``
2. Check the endpoint URL matches exactly —
   ``http://localhost:3001/api/ingest/logs`` (note: ``/api/ingest/logs``, not
   ``/api/logs``).
3. Ensure your application has run long enough for the flush interval to
   trigger (default 2 seconds), or call ``transport.flush()`` explicitly.
4. Check application stderr for transport retry warnings.

**Logs arrive but with wrong source**

The ``source_name`` parameter on ``HTTPTransportHandler`` controls the value.
If not set, it defaults to ``"pid-<PID>"``.

**Correlation IDs missing**

Add the framework middleware (``LogEverythingMiddleware`` for FastAPI) to
auto-generate correlation IDs.  Without it, logs will have an empty
correlation ID column in the dashboard.

**Tree view shows flat list instead of hierarchy**

The tree view requires structured hierarchy fields (``indent_level``,
``call_id``, etc.).  These are added automatically when:

- The ``@log`` decorator wraps your functions.
- ``HierarchyFilter`` is attached to the logger (auto-attached by default in
  ``Logger`` and ``AsyncLogger``).

If you only call ``log.info(...)`` without decorators, logs appear as flat
messages in the tree view.

**High memory usage**

Lower ``batch_size`` and ``flush_interval`` to send smaller, more frequent
batches.  If the dashboard is unreachable, the buffer grows until the
back-pressure policy kicks in (default: ``"drop"`` discards oldest records).


.. seealso::

   :doc:`transport`
      Full transport configuration and protocol details.

   :doc:`dashboard`
      Dashboard UI guide with screenshots and API reference.

   :doc:`correlation`
      Correlation ID propagation across threads and async tasks.

   :doc:`integrations`
      Framework middleware for FastAPI, Flask, Django, and Celery.
