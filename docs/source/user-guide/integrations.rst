Framework Integrations
======================

LogEverything ships middleware and extensions for popular Python web frameworks
and task queues.  Each integration automatically manages
:doc:`correlation IDs <correlation>`, logs request start/end with timing, and
injects the correlation header into responses.

All framework imports are guarded with ``try/except`` — no framework is a
required dependency of LogEverything.

ASGI Middleware (FastAPI / Starlette / Quart)
---------------------------------------------

The generic ASGI middleware works with **any** ASGI application.

.. code-block:: python

   from starlette.applications import Starlette
   from logeverything.integrations.asgi import LogEverythingASGIMiddleware

   app = Starlette()
   app.add_middleware(LogEverythingASGIMiddleware)

**Per-request behaviour:**

1. Extracts or generates a correlation ID from the ``X-Request-ID`` header.
2. Sets correlation context (method, path, client IP).
3. Logs ``>>> GET /api/users (client=10.0.0.1)`` at request start.
4. Wraps the response to capture the status code and inject the
   ``X-Request-ID`` header.
5. Logs ``<<< GET /api/users 200 (45.2ms)`` at request end.
6. Clears correlation context.

Configuration
~~~~~~~~~~~~~

.. code-block:: python

   LogEverythingASGIMiddleware(
       app,
       logger_name="logeverything.http",       # logger used for request logs
       exclude_paths=("/health", "/metrics"),   # paths to skip
       request_id_header="X-Request-ID",        # header name
       log_request_body=False,                  # log request body (expensive)
       log_response_body=False,                 # log response body (expensive)
   )

FastAPI
-------

A thin subclass of the ASGI middleware with FastAPI-friendly defaults (also
excludes ``/docs`` and ``/openapi.json``):

.. code-block:: python

   from fastapi import FastAPI
   from logeverything.integrations.fastapi import LogEverythingMiddleware

   app = FastAPI()
   app.add_middleware(LogEverythingMiddleware)

Dependency-Injected Request Logger
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``get_request_logger()`` to get a logger already bound to the current
correlation ID in any endpoint:

.. code-block:: python

   from fastapi import Depends, FastAPI
   from logeverything.integrations.fastapi import (
       LogEverythingMiddleware,
       get_request_logger,
   )

   app = FastAPI()
   app.add_middleware(LogEverythingMiddleware)

   @app.get("/users")
   async def list_users(log=Depends(get_request_logger())):
       log.info("Fetching users")        # auto-includes correlation_id
       users = await fetch_users()
       log.info("Returning %d users", len(users))
       return users

WSGI Middleware (Flask / Django / Bottle)
-----------------------------------------

The generic WSGI middleware follows the same pattern as ASGI but is
synchronous:

.. code-block:: python

   from logeverything.integrations.wsgi import LogEverythingWSGIMiddleware

   # Wrap any WSGI app
   app = LogEverythingWSGIMiddleware(my_wsgi_app)

Flask Extension
---------------

The Flask extension uses ``before_request`` / ``after_request`` /
``teardown_request`` hooks and supports the application factory pattern:

.. code-block:: python

   from flask import Flask
   from logeverything.integrations.flask import LogEverythingFlask

   # Direct initialisation
   app = Flask(__name__)
   LogEverythingFlask(app)

   # Or factory pattern
   le = LogEverythingFlask()

   def create_app():
       app = Flask(__name__)
       le.init_app(app)
       return app

Timing is stored in ``flask.g`` so that ``after_request`` can calculate
duration.  The correlation header is automatically added to responses.

Django Middleware
-----------------

Add the middleware to your ``MIDDLEWARE`` list:

.. code-block:: python

   # settings.py
   MIDDLEWARE = [
       # ... other middleware
       "logeverything.integrations.django.LogEverythingDjangoMiddleware",
       # ... other middleware
   ]

Optional settings (all have sensible defaults):

.. code-block:: python

   # settings.py
   LOGEVERYTHING_LOGGER_NAME = "logeverything.http"
   LOGEVERYTHING_EXCLUDE_PATHS = {"/health", "/metrics"}
   LOGEVERYTHING_REQUEST_ID_HEADER = "X-Request-ID"

The middleware also implements ``process_exception`` so unhandled exceptions
are logged with the correlation context before Django's default handler runs.

Celery Task Logging
-------------------

Connect to Celery signals to automatically log task lifecycle with
correlation propagation through chains and groups:

.. code-block:: python

   from celery import Celery
   from logeverything.integrations.celery import setup_celery_logging

   app = Celery("myapp")
   setup_celery_logging(app)

   @app.task
   def process_order(order_id):
       # Correlation ID is set automatically (uses task_id or propagated ID)
       print(f"Processing order {order_id}")

**Signals wired:**

- ``task_prerun`` — sets correlation ID, logs task start.
- ``task_postrun`` — logs task completion with duration.
- ``task_failure`` — logs exception with correlation.
- ``task_retry`` — logs retry reason.
- ``before_task_publish`` — injects correlation ID into task headers so
  chained / grouped tasks inherit the caller's ID.

Installing Optional Dependencies
---------------------------------

The integrations themselves have no hard requirements beyond the standard
library and LogEverything.  To actually *use* them you need the respective
framework installed:

.. code-block:: bash

   pip install logeverything[integrations]   # installs aiohttp
   pip install logeverything[celery]         # installs celery

Or install frameworks directly:

.. code-block:: bash

   pip install fastapi uvicorn   # for ASGI/FastAPI
   pip install flask             # for Flask
   pip install django            # for Django
   pip install celery            # for Celery

.. seealso::

   :doc:`correlation`
      How correlation IDs work under the hood.

   :doc:`transport`
      Shipping correlated logs to a central dashboard.

   :doc:`../api/integrations`
      Full API reference for all integration modules.
