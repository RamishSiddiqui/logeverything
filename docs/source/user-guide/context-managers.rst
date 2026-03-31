Context Managers
================

LogEverything provides powerful context managers that allow you to temporarily modify logging behavior, capture output, and manage logging scope with clean, Pythonic syntax.

Overview
--------

Context managers in LogEverything enable:

- **Temporary Configuration**: Modify logger settings within a specific scope
- **Output Capture**: Capture and redirect log output programmatically
- **Scope Management**: Create isolated logging environments
- **Resource Cleanup**: Automatic restoration of previous settings

Basic Context Managers
----------------------

Temporary Level Changes
~~~~~~~~~~~~~~~~~~~~~~~

Temporarily change the logging level for a specific code block:

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    # Normal logging level
    logger.info("This will be shown")
    logger.debug("This won't be shown (default level is INFO)")

    # Temporarily change to DEBUG level
    with logger.level("DEBUG"):
        logger.info("This will be shown")
        logger.debug("Now this will also be shown!")

    # Back to original level
    logger.debug("This won't be shown again")

Output:

.. code-block:: text

    2024-01-15 10:30:15 | INFO  | This will be shown
    2024-01-15 10:30:15 | INFO  | This will be shown
    2024-01-15 10:30:15 | DEBUG | Now this will also be shown!

Temporary Format Changes
~~~~~~~~~~~~~~~~~~~~~~~~

Change the output format temporarily:

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    logger.info("Default format")

    with logger.format("{timestamp} [{level}] {message}"):
        logger.info("Custom format")
        logger.warning("Another custom format message")

    logger.info("Back to default format")

Output Capture
--------------

String Capture
~~~~~~~~~~~~~~

Capture log output as a string:

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    with logger.capture() as captured:
        logger.info("This will be captured")
        logger.warning("So will this")
        logger.error("And this too")

    print("Captured output:")
    print(captured.getvalue())

Output:

.. code-block:: text

    Captured output:
    2024-01-15 10:30:15 | INFO  | This will be captured
    2024-01-15 10:30:15 | WARN  | So will this
    2024-01-15 10:30:15 | ERROR | And this too

List Capture
~~~~~~~~~~~~

Capture log entries as structured data:

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    with logger.capture_list() as captured:
        logger.info("First message")
        logger.bind(extra={"user_id": 123}).error("Error message")
        logger.debug("Debug info")

    for entry in captured:
        print(f"Level: {entry.level}, Message: {entry.message}")
        if hasattr(entry, 'extra'):
            print(f"Extra data: {entry.extra}")

File Capture
~~~~~~~~~~~~

Capture output to a file temporarily:

.. code-block:: python

    from logeverything import Logger
    import tempfile
    import os

    logger = Logger()

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        with logger.capture_to_file(temp_file.name):
            logger.info("This goes to the file")
            logger.error("So does this")

    # Read the captured content
    with open(temp_file.name, 'r') as f:
        content = f.read()
        print("File content:")
        print(content)

    os.unlink(temp_file.name)  # Clean up

Advanced Context Managers
-------------------------

Silent Logging
~~~~~~~~~~~~~~

Temporarily disable all output:

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    logger.info("This will be shown")

    with logger.silent():
        logger.info("This won't be shown")
        logger.error("Neither will this")

    logger.info("This will be shown again")

Scoped Configuration
~~~~~~~~~~~~~~~~~~~~

Create a temporary logger configuration:

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    config = {
        'level': 'DEBUG',
        'format': '[{level}] {message}',
        'include_timestamp': False
    }

    logger.info("Original settings")

    with logger.configure(**config):
        logger.debug("Debug with custom format")
        logger.info("Info with custom format")

    logger.info("Back to original settings")

Conditional Logging
~~~~~~~~~~~~~~~~~~~

Enable logging only when a condition is met:

.. code-block:: python

    from logeverything import Logger

    logger = Logger()
    debug_mode = True

    with logger.when(debug_mode):
        logger.debug("This only logs when debug_mode is True")

    debug_mode = False
    with logger.when(debug_mode):
        logger.debug("This won't log now")

Async Context Managers
----------------------

AsyncLogger also supports context managers for async code:

.. code-block:: python

    import asyncio
    from logeverything import AsyncLogger

    async def example():
        logger = AsyncLogger()

        async with logger.level("DEBUG"):
            await logger.info("Async context manager")
            await logger.debug("Debug in async context")

        async with logger.capture() as captured:
            await logger.info("Captured async message")
            await logger.error("Async error message")

        print("Captured:", captured.getvalue())

    asyncio.run(example())

Nested Context Managers
-----------------------

Context managers can be nested for complex scenarios:

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    logger.info("Normal logging")

    with logger.level("DEBUG"):
        logger.debug("Debug level enabled")

        with logger.format("[{level}] {message}"):
            logger.debug("Custom format + debug level")

            with logger.capture() as captured:
                logger.info("Captured with custom format")

        logger.debug("Back to default format, still debug level")

    logger.debug("Back to original level (won't show)")
    logger.info("Normal logging resumed")

Custom Context Managers
-----------------------

Create your own context managers for specific use cases:

.. code-block:: python

    from logeverything import Logger
    from contextlib import contextmanager

    logger = Logger()

    @contextmanager
    def performance_logging():
        import time
        start_time = time.time()

        with logger.level("DEBUG"):
            logger.debug("Performance monitoring started")
            try:
                yield
            finally:
                duration = time.time() - start_time
                logger.info(f"Operation completed in {duration:.2f} seconds")

    # Usage
    with performance_logging():
        # Your code here
        import time
        time.sleep(1)  # Simulate work

Error Handling in Context Managers
----------------------------------

Context managers handle errors gracefully:

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    try:
        with logger.capture() as captured:
            logger.info("Before error")
            raise ValueError("Something went wrong")
            logger.info("This won't execute")
    except ValueError as e:
        logger.error(f"Caught error: {e}")
        print("Captured before error:", captured.getvalue())

Best Practices
--------------

1. **Use Specific Scopes**: Keep context manager scopes as small as possible
2. **Avoid Deep Nesting**: Too many nested context managers can be hard to read
3. **Handle Exceptions**: Always consider what happens if code inside the context raises an exception
4. **Resource Cleanup**: Context managers automatically restore previous settings
5. **Performance**: Context managers have minimal overhead but avoid unnecessary nesting in tight loops

Common Patterns
---------------

Request Logging
~~~~~~~~~~~~~~~

Log all operations during a request with correlation ID:

.. code-block:: python

    from logeverything import Logger
    import uuid

    logger = Logger()

    def handle_request(data):
        request_id = str(uuid.uuid4())[:8]

        with logger.extra(request_id=request_id):
            logger.bind(extra={"data": data}).info("Request started")

            try:
                # Process request
                result = process_data(data)
                logger.info("Request completed successfully")
                return result
            except Exception as e:
                logger.error(f"Request failed: {e}")
                raise

Testing with Captured Output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Verify log output in tests:

.. code-block:: python

    from logeverything import Logger

    def test_user_login():
        logger = Logger()

        with logger.capture_list() as captured:
            # Code under test
            login_user("john_doe")

        # Verify logging
        assert len(captured) == 2
        assert captured[0].level == "INFO"
        assert "login attempt" in captured[0].message
        assert captured[1].level == "INFO"
        assert "login successful" in captured[1].message

Debugging with Temporary Verbosity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Increase verbosity for debugging specific sections:

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    def complex_operation():
        logger.info("Starting complex operation")

        # Enable debug logging for this specific part
        with logger.level("DEBUG"):
            logger.debug("Step 1: Initialize")
            step1()

            logger.debug("Step 2: Process")
            step2()

            logger.debug("Step 3: Finalize")
            step3()

        logger.info("Complex operation completed")

API Reference
-------------

Logger Context Managers
~~~~~~~~~~~~~~~~~~~~~~~

.. py:method:: Logger.level(level)

    Temporarily change the logging level.

    :param level: New logging level ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    :type level: str
    :returns: Context manager
    :rtype: ContextManager

.. py:method:: Logger.format(format_string)

    Temporarily change the log format.

    :param format_string: New format string
    :type format_string: str
    :returns: Context manager
    :rtype: ContextManager

.. py:method:: Logger.capture()

    Capture log output as a string.

    :returns: Context manager yielding StringIO object
    :rtype: ContextManager[StringIO]

.. py:method:: Logger.capture_list()

    Capture log entries as structured data.

    :returns: Context manager yielding list of log entries
    :rtype: ContextManager[List[LogEntry]]

.. py:method:: Logger.capture_to_file(filename)

    Capture log output to a file.

    :param filename: Path to output file
    :type filename: str
    :returns: Context manager
    :rtype: ContextManager

.. py:method:: Logger.silent()

    Temporarily disable all log output.

    :returns: Context manager
    :rtype: ContextManager

.. py:method:: Logger.configure(**kwargs)

    Temporarily change multiple configuration options.

    :param kwargs: Configuration options
    :returns: Context manager
    :rtype: ContextManager

.. py:method:: Logger.when(condition)

    Enable logging only when condition is True.

    :param condition: Boolean condition
    :type condition: bool
    :returns: Context manager
    :rtype: ContextManager
