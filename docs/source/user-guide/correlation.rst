Correlation IDs & Request Context
=================================

LogEverything provides async-safe, thread-safe correlation ID propagation that
lets you trace a single request across middleware, services, tasks, and log
transports.  It uses ``contextvars.ContextVar`` — the same mechanism behind
the :doc:`../user-guide/async-logging` indentation system — so it works
transparently in both sync and async code.

Overview
--------

A **correlation ID** is a unique string (16 hex chars by default) that
follows a unit of work from start to finish.  All log records produced
during that work carry the same ID, making it trivial to filter or search
for every log line belonging to a single HTTP request, Celery task, or
business operation.

Quick Start
-----------

.. executable-code::

   from logeverything.correlation import (
       set_correlation_id,
       get_correlation_id,
       clear_correlation,
   )

   # Generate a correlation ID for this context
   cid = set_correlation_id()
   print(f"Generated: {cid}  (len={len(cid)})")

   # Read it back
   print(f"Current:   {get_correlation_id()}")

   # Or supply your own
   set_correlation_id("my-custom-req-id")
   print(f"Custom:    {get_correlation_id()}")

   # Clean up at end of request / task
   clear_correlation()
   print(f"After clear: '{get_correlation_id()}'")

Request Context
---------------

Besides the correlation ID you can attach request-level metadata (method,
path, client IP) which is available to any code in the same context:

.. code-block:: python

   from logeverything.correlation import set_request_context, get_request_context

   set_request_context({
       "method": "POST",
       "path": "/api/users",
       "client_ip": "10.0.0.42",
   })

   ctx = get_request_context()
   print(ctx["method"])   # "POST"
   print(ctx["path"])     # "/api/users"

Automatic Injection with CorrelationFilter
------------------------------------------

:class:`~logeverything.correlation.CorrelationFilter` is a standard
``logging.Filter`` that injects ``correlation_id``, ``request_method``, and
``request_path`` into every ``LogRecord`` that passes through a handler.

.. code-block:: python

   import logging
   from logeverything.correlation import CorrelationFilter, set_correlation_id

   # Attach the filter to any handler or logger
   handler = logging.StreamHandler()
   handler.addFilter(CorrelationFilter())

   fmt = logging.Formatter("%(asctime)s [%(correlation_id)s] %(message)s")
   handler.setFormatter(fmt)

   logger = logging.getLogger("myapp")
   logger.addHandler(handler)
   logger.setLevel(logging.DEBUG)

   set_correlation_id("abc123def456")
   logger.info("This log line carries the correlation ID")

Built-in Handler Support
~~~~~~~~~~~~~~~~~~~~~~~~

When a correlation ID is active, LogEverything's own handlers automatically
include it:

- **JSONHandler** — adds a ``"correlation_id"`` field to every JSON record.
- **JSONLineFormatter** — includes ``"correlation_id"`` in each JSON Lines
  record, making correlation IDs available in the dashboard and rotated log
  files.
- **PrettyFormatter** — appends ``[req:abc123de]`` (first 8 chars) to every
  formatted line.

No extra configuration is needed — just set the correlation ID and it appears.

Thread Propagation
------------------

``contextvars`` are scoped to the current async task or thread.  When you
dispatch work to a ``ThreadPoolExecutor`` or a plain ``threading.Thread`` the
correlation ID will not follow automatically.  Use the
:func:`~logeverything.correlation.propagate_context` decorator to copy the
current context into the new thread:

.. code-block:: python

   from concurrent.futures import ThreadPoolExecutor
   from logeverything.correlation import (
       propagate_context,
       set_correlation_id,
       get_correlation_id,
   )

   set_correlation_id("parent-ctx")

   @propagate_context
   def background_work():
       # This runs in a pool thread but sees the parent's correlation ID
       print(f"In thread: {get_correlation_id()}")   # "parent-ctx"

   with ThreadPoolExecutor() as pool:
       pool.submit(background_work)

Integration with Middleware
---------------------------

You rarely need to call ``set_correlation_id()`` yourself.  The
:doc:`integrations` middleware (ASGI, WSGI, Flask, Django, Celery) does it
automatically for every incoming request or task — see that guide for
details.

.. seealso::

   :doc:`integrations`
      Framework middleware that auto-manages correlation IDs.

   :doc:`transport`
      Log transports that ship correlation IDs to the dashboard.

   :doc:`../api/correlation`
      Full API reference for ``logeverything.correlation``.
