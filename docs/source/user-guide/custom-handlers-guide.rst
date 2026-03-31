.. _custom-handlers-guide:

Avoiding Duplicate Log Messages
================================

When adding custom handlers to a LogEverything Logger you may see every
message printed twice — once by LogEverything's default handler and once by
yours.  This page explains why it happens, how to fix it, and how to add
custom handlers cleanly.


The Problem
-----------

When you create a Logger and call ``add_handler()``, you might see output
like this:

.. code-block:: text

   2025-08-08 18:25:09 | INFO | json_app:196 | User login          # LogEverything's default handler
   [DB] Stored log: INFO - User login                              # Your custom handler

This happens because LogEverything's Logger automatically creates default
handlers during initialisation, and your custom handlers are added on top.


Why This Happens
----------------

LogEverything's Logger is designed for zero-configuration usage.  When you
create an instance:

1. **Auto-setup** — the Logger calls ``_auto_configure()`` internally.
2. **Environment detection** — it detects the runtime environment (script,
   web app, notebook, etc.).
3. **Default handlers** — it creates appropriate handlers (usually a console
   handler).
4. **Your handlers** — when you call ``add_handler()``, your handler is added
   alongside the existing ones.

The result: **both** LogEverything's default handlers **and** your custom
handlers process every log message.


Solutions
---------

Use ``auto_setup=False`` (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Prevent any automatic handler creation by disabling auto-setup:

.. code-block:: python

   from logeverything import Logger
   import logging

   # Create logger with NO automatic setup
   logger = Logger("my_app", auto_setup=False)

   # Add only your custom handlers (use UTF-8 encoding for Unicode compatibility)
   custom_handler = logging.FileHandler("custom.log", encoding="utf-8")
   logger.add_handler(custom_handler)

   logger.info("This message goes only to your custom handler")

Use ``handlers=[]``
~~~~~~~~~~~~~~~~~~~

Specify an empty handlers list to prevent default handler creation:

.. code-block:: python

   from logeverything import Logger

   # Create logger with no default handlers
   logger = Logger("my_app", handlers=[])

   # Add your custom handlers
   custom_handler = logging.StreamHandler()
   logger.add_handler(custom_handler)

Clear Existing Handlers
~~~~~~~~~~~~~~~~~~~~~~~

Create a logger normally, then clear its handlers before adding custom ones:

.. code-block:: python

   from logeverything import Logger
   import logging

   logger = Logger("my_app")
   logger.logger.handlers.clear()

   custom_handler = logging.FileHandler("custom.log", encoding="utf-8")
   logger.add_handler(custom_handler)

.. note::

   Use ``encoding="utf-8"`` for file handlers to ensure Unicode symbols from
   LogEverything's visual formatting are properly saved.

Mixed Approach
~~~~~~~~~~~~~~

Keep LogEverything's visual formatting for the console and add custom handlers
for specific purposes:

.. code-block:: python

   from logeverything import Logger

   # Keep LogEverything's default console formatting
   logger = Logger("my_app", level="DEBUG", visual_mode=True)

   # Add a custom handler for errors only
   error_handler = logging.FileHandler("errors.log", encoding="utf-8")
   error_handler.setLevel(logging.ERROR)
   logger.add_handler(error_handler)

   logger.info("Console only (LogEverything formatting)")
   logger.error("Console + error file (both handlers)")


Custom JSON Output
------------------

.. tip::

   If you need JSON output for the dashboard or structured logging, use the
   built-in :class:`~logeverything.handlers.handlers.JSONLineFormatter` instead
   of writing your own formatter.  It produces dashboard-compatible JSON Lines
   output and works with any handler, including rotation handlers.  See
   :doc:`rotation-handlers` for examples.

   The hand-rolled example below is useful if you need **full control** over
   the JSON schema.

.. code-block:: python

   import json
   import datetime
   import logging
   from logeverything import Logger

   class JSONFormatter(logging.Formatter):
       def format(self, record):
           return json.dumps({
               "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
               "level": record.levelname,
               "logger": record.name,
               "message": record.getMessage(),
               "module": record.module,
               "function": record.funcName,
               "line": record.lineno,
           })

   # Create logger with NO auto-setup
   json_logger = Logger("json_app", auto_setup=False)

   # Add custom JSON file handler
   json_handler = logging.FileHandler("app.json", encoding="utf-8")
   json_handler.setFormatter(JSONFormatter())
   json_logger.add_handler(json_handler)

   json_logger.info("Application started")
   json_logger.error("Something went wrong")


Performance Comparison
----------------------

.. list-table::
   :header-rows: 1

   * - Approach
     - Handler Count
     - Performance
     - Use Case
   * - Default Logger
     - 1--2
     - Fast
     - Standard logging
   * - Logger + Custom (wrong)
     - 3--4
     - Slower
     - Causes duplicates
   * - ``auto_setup=False`` + Custom
     - 1
     - Fastest
     - Pure custom logging
   * - Mixed approach
     - 2--3
     - Good
     - Best of both worlds


Best Practices
--------------

**Pure custom logging:**

.. code-block:: python

   logger = Logger("app", auto_setup=False)

**Mixed LogEverything + custom:**

.. code-block:: python

   logger = Logger("app", visual_mode=True)
   error_db_handler = DatabaseHandler()
   error_db_handler.setLevel(logging.ERROR)
   logger.add_handler(error_db_handler)

**Migrating from stdlib logging:**

.. code-block:: python

   logger = Logger("app", auto_setup=False)
   # Add your existing handlers unchanged


Common Mistakes
---------------

**Don't do this:**

.. code-block:: python

   # This creates duplicate output
   logger = Logger("app")  # Creates default console handler
   custom_handler = logging.StreamHandler()  # Another console handler!
   logger.add_handler(custom_handler)  # Now you have 2 console handlers

**Do this instead:**

.. code-block:: python

   # Option 1: Pure custom
   logger = Logger("app", auto_setup=False)
   custom_handler = logging.StreamHandler()
   logger.add_handler(custom_handler)

   # Option 2: Clear first
   logger = Logger("app")
   logger.logger.handlers.clear()
   custom_handler = logging.StreamHandler()
   logger.add_handler(custom_handler)


Debugging Handler Issues
------------------------

To see what handlers are attached to your logger:

.. code-block:: python

   from logeverything import Logger

   logger = Logger("debug_app")

   print("Handlers:")
   for i, handler in enumerate(logger.logger.handlers):
       print(f"  {i}: {type(handler).__name__} - {handler}")

   print(f"Total handlers: {len(logger.logger.handlers)}")

Example output:

.. code-block:: text

   Handlers:
     0: StreamHandler - <StreamHandler <stderr> (INFO)>
     1: FileHandler - <FileHandler 'app.log' (DEBUG)>
   Total handlers: 2


Summary
-------

- **Duplicate logging** happens when LogEverything's default handlers and your
  custom handlers both process messages.
- Use ``auto_setup=False`` when you want complete control over handlers.
- Use ``handlers=[]`` to prevent default handler creation.
- Use ``logger.handlers.clear()`` to remove existing handlers after creation.
- The **mixed approach** works well for keeping LogEverything's visual
  formatting while adding custom handlers for specific purposes.
- For JSON output, prefer the built-in ``JSONLineFormatter`` over a
  hand-rolled formatter.
