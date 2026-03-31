File Rotation
=============

In production, log files grow unbounded and eventually fill disks.
LogEverything provides two rotation strategies: **size-based** and
**time-based**.  Both support optional **gzip compression** of rotated files.

Size-based Rotation
-------------------

The built-in :class:`~logeverything.handlers.handlers.FileHandler` supports
size-based rotation when you pass the ``max_size`` parameter.  When the active
log file exceeds ``max_size`` bytes the handler shifts files
(``app.log`` -> ``app.log.1`` -> ``app.log.2`` ...) and opens a fresh
``app.log``.

.. code-block:: python

   from logeverything.handlers import FileHandler

   handler = FileHandler(
       "logs/app.log",
       max_size=10_485_760,   # 10 MB
       backup_count=5,        # keep app.log.1 ... app.log.5
       compress=True,         # gzip the most recent rotated file
   )

**Parameters:**

.. list-table::
   :header-rows: 1

   * - Parameter
     - Default
     - Description
   * - ``filename``
     - *(required)*
     - Path to the log file
   * - ``max_size``
     - ``None``
     - Maximum file size in bytes before rotation (``None`` disables rotation)
   * - ``backup_count``
     - ``5``
     - Number of rotated backup files to keep
   * - ``compress``
     - ``False``
     - Gzip the most recent rotated file in a background thread
   * - ``encoding``
     - ``"utf-8"``
     - File encoding

Time-based Rotation
-------------------

:class:`~logeverything.handlers.handlers.TimedRotatingFileHandler` rotates at
time boundaries — daily at midnight, every hour, or every week.  Old files
beyond the retention window are automatically deleted.

.. code-block:: python

   from logeverything.handlers import TimedRotatingFileHandler

   handler = TimedRotatingFileHandler(
       "logs/app.log",
       when="midnight",       # rotate daily at midnight
       retention_days=30,     # keep 30 days of logs
       compress=True,         # gzip rotated files
   )

Rotated files are named with a date suffix based on the ``when`` interval:

- ``midnight`` — ``app.log.2026-02-23``
- ``hourly`` — ``app.log.2026-02-23-14``
- ``weekly`` — ``app.log.2026-08``

**Parameters:**

.. list-table::
   :header-rows: 1

   * - Parameter
     - Default
     - Description
   * - ``filename``
     - *(required)*
     - Path to the log file
   * - ``when``
     - ``"midnight"``
     - Rotation interval: ``"midnight"``, ``"hourly"``, or ``"weekly"``
   * - ``interval``
     - ``1``
     - Multiplier for *when* (reserved for future use)
   * - ``retention_days``
     - ``30``
     - Delete rotated files older than this many days
   * - ``compress``
     - ``False``
     - Gzip rotated files in a background thread
   * - ``encoding``
     - ``"utf-8"``
     - File encoding

Compression
-----------

Both handlers support gzip compression of rotated files.  When
``compress=True``, the handler spawns a background daemon thread that
compresses the rotated file (``app.log.1`` -> ``app.log.1.gz``) without
blocking the logging path.

Choosing a Strategy
-------------------

.. list-table::
   :header-rows: 1

   * - Criterion
     - Size-based
     - Time-based
   * - Predictable file sizes
     - Yes
     - No (depends on log volume)
   * - Predictable file count
     - Yes (``backup_count``)
     - No (depends on ``retention_days``)
   * - Easy date-based lookup
     - No
     - Yes (date in filename)
   * - Good for high-volume
     - Yes
     - Yes
   * - Automatic cleanup
     - Yes (oldest backup dropped)
     - Yes (files older than ``retention_days`` deleted)

**Rule of thumb:** Use **time-based** rotation when you need to find logs by
date (most production deployments).  Use **size-based** rotation when you need
to cap disk usage to a fixed amount.

Using with a Logger
-------------------

Rotation handlers are standard handlers — add them to any logger:

.. code-block:: python

   from logeverything import Logger
   from logeverything.handlers import TimedRotatingFileHandler

   log = Logger("my_app")
   handler = TimedRotatingFileHandler(
       "logs/my_app.log",
       when="midnight",
       retention_days=14,
       compress=True,
   )
   log.add_handler(handler)
   log.info("This message is written to a rotating log file")

Dashboard Integration
---------------------

Rotation handlers write plain text by default, which the LogEverything
dashboard cannot read.  Attach a :class:`~logeverything.handlers.handlers.JSONLineFormatter`
to produce **JSON Lines** output that the dashboard's Local Connection mode
picks up automatically — including rotated files.

**Time-based rotation:**

.. code-block:: python

   from logeverything import Logger
   from logeverything.handlers import TimedRotatingFileHandler, JSONLineFormatter

   handler = TimedRotatingFileHandler(
       "monitoring_data/logs/app.jsonl",
       when="midnight",
       retention_days=30,
       compress=True,
   )
   handler.setFormatter(JSONLineFormatter(source="my_service"))

   log = Logger("my_app")
   log.add_handler(handler)
   log.info("Dashboard will see this message")

**Size-based rotation:**

.. code-block:: python

   from logeverything import Logger
   from logeverything.handlers import FileHandler, JSONLineFormatter

   handler = FileHandler(
       "monitoring_data/logs/app.jsonl",
       max_size=10_485_760,  # 10 MB
       backup_count=5,
       compress=True,
   )
   handler.setFormatter(JSONLineFormatter(source="my_service"))

   log = Logger("my_app")
   log.add_handler(handler)

The ``source`` parameter is optional — it tags every log record so the
dashboard can filter by service name.

.. seealso::

   :doc:`custom-handlers-guide`
      Avoiding duplicate log messages and adding custom handlers.

   :doc:`../api/handlers`
      Full API reference for all handler classes.
