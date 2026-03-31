Print Capture and Integration
=============================

LogEverything provides seamless integration with existing codebases through its print capture functionality and integration capabilities with popular Python libraries and frameworks.

Print Capture
-------------

Overview
~~~~~~~~

Print capture allows you to:

- **Intercept Print Statements**: Automatically capture existing `print()` calls
- **Unified Logging**: Merge print output with structured logging
- **Legacy Code Integration**: Add logging to existing code without modifications
- **Debugging Support**: Capture debug prints for analysis

Basic Print Capture
~~~~~~~~~~~~~~~~~~~

Capture all print statements:

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    # Enable print capture
    with logger.capture_prints():
        print("This will be captured by the logger")
        print("So will this")

        # Regular logging still works
        logger.info("Regular log message")

Output:

.. code-block:: text

    2024-01-15 10:30:15 | INFO  | This will be captured by the logger
    2024-01-15 10:30:15 | INFO  | So will this
    2024-01-15 10:30:15 | INFO  | Regular log message

Selective Print Capture
~~~~~~~~~~~~~~~~~~~~~~~

Capture only specific print patterns:

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    # Only capture prints containing "DEBUG"
    with logger.capture_prints(pattern="DEBUG"):
        print("Regular print - not captured")
        print("DEBUG: This will be captured")
        print("Another regular print")
        print("DEBUG: This will also be captured")

Level-Based Print Capture
~~~~~~~~~~~~~~~~~~~~~~~~~

Assign different log levels based on print content:

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    # Configure level mapping
    level_mapping = {
        "ERROR": "error",
        "WARNING": "warning",
        "DEBUG": "debug",
        "default": "info"
    }

    with logger.capture_prints(level_mapping=level_mapping):
        print("Regular message")  # -> INFO level
        print("ERROR: Something went wrong")  # -> ERROR level
        print("WARNING: Be careful")  # -> WARNING level
        print("DEBUG: Detailed info")  # -> DEBUG level

Contextual Print Capture
~~~~~~~~~~~~~~~~~~~~~~~~

Add context to captured print statements:

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    def process_user_data(user_id):
        with logger.capture_prints(extra={"user_id": user_id, "module": "user_processing"}):
            print(f"Processing user {user_id}")
            print("Validation completed")
            print("Data saved successfully")

    process_user_data(12345)

Advanced Print Capture
----------------------

Custom Print Handlers
~~~~~~~~~~~~~~~~~~~~~

Define custom handling for captured prints:

.. code-block:: python

    from logeverything import Logger
    import re

    logger = Logger()

    def custom_print_handler(text, logger):
        """Custom handler for print statements"""
        # Parse SQL queries
        if text.startswith("SQL:"):
            logger.bind(extra={"type": "sql_query"}).debug(text)
        # Parse API calls
        elif "API:" in text:
            logger.bind(extra={"type": "api_call"}).info(text)
        # Parse errors
        elif re.search(r"error|exception|failed", text, re.IGNORECASE):
            logger.bind(extra={"type": "error"}).error(text)
        else:
            logger.bind(extra={"type": "general"}).info(text)

    with logger.capture_prints(handler=custom_print_handler):
        print("SQL: SELECT * FROM users WHERE id = ?")
        print("API: GET /users/123")
        print("Error: Connection failed")
        print("Regular message")

Print Redirection
~~~~~~~~~~~~~~~~~

Redirect prints to different outputs:

.. code-block:: python

    from logeverything import Logger
    import sys

    logger = Logger()

    # Redirect to file while maintaining console output
    with logger.capture_prints(redirect_to="debug.log", maintain_console=True):
        print("This goes to both console and file")

    # Redirect to logger only (suppress console)
    with logger.capture_prints(suppress_console=True):
        print("This only goes to the logger")

Temporary Print Suppression
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Temporarily suppress print statements:

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    print("This will be shown")

    with logger.suppress_prints():
        print("This will be suppressed")
        print("So will this")

    print("This will be shown again")

Library Integration
-------------------

FastAPI Integration
~~~~~~~~~~~~~~~~~~~

Integrate with FastAPI applications:

.. code-block:: python

    from fastapi import FastAPI, Request
    from logeverything import Logger
    import time

    app = FastAPI()
    logger = Logger(profile="api")

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()

        # Log request
        logger.bind(extra={
            "method": request.method,
            "url": str(request.url).info("Request started"),
            "client_ip": request.client.host
        })

        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        logger.bind(extra={
            "status_code": response.status_code,
            "process_time": process_time
        }).info("Request completed")

        return response

    @app.get("/users/{user_id}")
    async def get_user(user_id: int):
        logger.info(f"Fetching user {user_id}")
        # Simulate user lookup
        return {"user_id": user_id, "name": "John Doe"}

Django Integration
~~~~~~~~~~~~~~~~~~

Integrate with Django projects:

.. code-block:: python

    # settings.py
    from logeverything import Logger

    # Configure LogEverything as Django's logger
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'logeverything': {
                'level': 'DEBUG',
                'class': 'logeverything.handlers.DjangoHandler',
                'profile': 'production'
            },
        },
        'root': {
            'handlers': ['logeverything'],
        },
    }

    # views.py
    from logeverything import Logger
    from django.http import JsonResponse

    logger = Logger()

    def user_view(request, user_id):
        logger.bind(extra={
            "user_id": user_id,
            "ip": request.META.get('REMOTE_ADDR').info("User view accessed"),
            "user_agent": request.META.get('HTTP_USER_AGENT')
        })

        # Your view logic here
        return JsonResponse({"user_id": user_id})

Flask Integration
~~~~~~~~~~~~~~~~~

Integrate with Flask applications:

.. code-block:: python

    from flask import Flask, request, g
    from logeverything import Logger
    import uuid

    app = Flask(__name__)
    logger = Logger(profile="api")

    @app.before_request
    def before_request():
        g.request_id = str(uuid.uuid4())[:8]

        logger.bind(extra={
            "request_id": g.request_id,
            "method": request.method,
            "path": request.path,
            "ip": request.remote_addr
        }).info("Request started")

    @app.after_request
    def after_request(response):
        logger.bind(extra={
            "request_id": g.request_id,
            "status_code": response.status_code,
            "content_length": response.content_length
        }).info("Request completed")
        return response

    @app.route("/users/<int:user_id>")
    def get_user(user_id):
        logger.bind(extra={"request_id": g.request_id}).info(f"Fetching user {user_id}")
        return {"user_id": user_id, "name": "John Doe"}

Celery Integration
~~~~~~~~~~~~~~~~~~

Integrate with Celery for background tasks:

.. code-block:: python

    from celery import Celery
    from logeverything import Logger

    app = Celery('tasks')
    logger = Logger(profile="background_job")

    @app.task
    def process_user_data(user_id):
        task_id = process_user_data.request.id

        logger.bind(extra={
            "task_id": task_id,
            "user_id": user_id,
            "task_name": "process_user_data"
        }).info("Task started")

        try:
            # Simulate processing
            import time
            time.sleep(5)

            logger.bind(extra={
                "task_id": task_id,
                "user_id": user_id
            }).info("Task completed successfully")

            return {"status": "completed", "user_id": user_id}

        except Exception as e:
            logger.bind(extra={
                "task_id": task_id,
                "user_id": user_id,
                "error": str(e).error("Task failed")
            })
            raise

SQLAlchemy Integration
~~~~~~~~~~~~~~~~~~~~~~

Log database operations:

.. code-block:: python

    from sqlalchemy import create_engine, event
    from logeverything import Logger

    logger = Logger()
    engine = create_engine("sqlite:///example.db")

    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        logger.bind(extra={
            "sql": statement,
            "parameters": parameters,
            "executemany": executemany
        }).debug("SQL Query")

    @event.listens_for(engine, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        logger.bind(extra={
            "rowcount": cursor.rowcount if hasattr(cursor, 'rowcount').debug("SQL Query completed") else None
        })

Requests Integration
~~~~~~~~~~~~~~~~~~~~

Log HTTP requests:

.. code-block:: python

    import requests
    from logeverything import Logger

    logger = Logger()

    class LoggingHTTPAdapter(requests.adapters.HTTPAdapter):
        def send(self, request, **kwargs):
            logger.bind(extra={
                "method": request.method,
                "url": request.url,
                "headers": dict(request.headers).info("HTTP Request")
            })

            response = super().send(request, **kwargs)

            logger.bind(extra={
                "status_code": response.status_code,
                "content_length": len(response.content).info("HTTP Response"),
                "response_time": response.elapsed.total_seconds()
            })

            return response

    # Use the logging adapter
    session = requests.Session()
    session.mount("http://", LoggingHTTPAdapter())
    session.mount("https://", LoggingHTTPAdapter())

    response = session.get("https://api.example.com/users")

Testing Integration
-------------------

Pytest Integration
~~~~~~~~~~~~~~~~~~

Integrate with pytest for test logging:

.. code-block:: python

    # conftest.py
    import pytest
    from logeverything import Logger

    @pytest.fixture
    def logger():
        """Provide a test logger"""
        return Logger(profile="testing")

    @pytest.fixture(autouse=True)
    def log_test_execution(request, logger):
        """Automatically log test execution"""
        test_name = request.node.name

        logger.info(f"Test started: {test_name}")

        def finalizer():
            if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
                logger.error(f"Test failed: {test_name}")
            else:
                logger.info(f"Test passed: {test_name}")

        request.addfinalizer(finalizer)

    # test_example.py
    def test_user_creation(logger):
        logger.info("Creating test user")
        # Test logic here
        assert True

Unittest Integration
~~~~~~~~~~~~~~~~~~~~

Integrate with unittest:

.. code-block:: python

    import unittest
    from logeverything import Logger

    class TestUserOperations(unittest.TestCase):
        def setUp(self):
            self.logger = Logger(profile="testing")
            self.logger.info(f"Setting up test: {self._testMethodName}")

        def tearDown(self):
            self.logger.info(f"Tearing down test: {self._testMethodName}")

        def test_user_creation(self):
            self.logger.info("Testing user creation")
            # Test logic here
            self.assertTrue(True)

    if __name__ == '__main__':
        unittest.main()

Legacy Code Integration
-----------------------

Gradual Migration
~~~~~~~~~~~~~~~~~

Gradually add logging to existing code:

.. code-block:: python

    from logeverything import Logger

    # Existing function
    def process_order(order_id):
        # Add logging without changing logic
        logger = Logger()
        logger.info(f"Processing order {order_id}")

        # Original code
        print(f"Order {order_id} processing...")  # This gets captured

        try:
            # Business logic
            validate_order(order_id)
            charge_payment(order_id)
            ship_order(order_id)

            logger.info(f"Order {order_id} completed successfully")
            print(f"Order {order_id} completed")  # This gets captured too

        except Exception as e:
            logger.error(f"Order {order_id} failed: {e}")
            print(f"Error processing order {order_id}: {e}")  # Captured
            raise

Monkey Patching
~~~~~~~~~~~~~~~

Replace print globally for legacy integration:

.. code-block:: python

    from logeverything import Logger
    import builtins

    # Set up global logger
    global_logger = Logger()

    # Store original print
    original_print = builtins.print

    def logged_print(*args, **kwargs):
        """Replace print with logged version"""
        # Convert print arguments to string
        message = " ".join(str(arg) for arg in args)

        # Log the message
        global_logger.bind(extra={"source": "print"}).info(message)

        # Also call original print if needed
        original_print(*args, **kwargs)

    # Replace print globally
    builtins.print = logged_print

    # Now all print statements are logged
    print("This will be logged")
    print("So will this")

Configuration and Best Practices
--------------------------------

Print Capture Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    # Configure print capture behavior
    print_config = {
        "level": "INFO",                    # Default level for prints
        "include_source": True,             # Include source file/line
        "pattern": None,                    # Pattern to match (regex)
        "exclude_pattern": None,            # Pattern to exclude
        "max_length": 1000,                 # Maximum message length
        "encoding": "utf-8",                # Text encoding
        "errors": "replace"                 # Error handling
    }

    with logger.capture_prints(**print_config):
        print("Configured print capture")

Performance Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    # For high-volume print capture, use buffering
    with logger.capture_prints(buffer_size=1000, flush_interval=5.0):
        for i in range(10000):
            print(f"Message {i}")

Integration Best Practices
--------------------------

1. **Gradual Migration**: Start with print capture, then gradually replace with proper logging
2. **Performance Monitoring**: Monitor performance impact of print capture in high-volume scenarios
3. **Configuration Management**: Use profiles to manage different integration settings
4. **Error Handling**: Ensure integration doesn't break existing functionality
5. **Testing**: Test integration thoroughly in development environments
6. **Documentation**: Document integration points for team members

Common Integration Patterns
---------------------------

API Gateway Pattern
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from logeverything import Logger

    class APIGateway:
        def __init__(self):
            self.logger = Logger(profile="api_gateway")

        async def handle_request(self, request):
            request_id = generate_request_id()

            # Log request
            self.logger.bind(extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.path,
                "headers": dict(request.headers).info("API Request")
            })

            try:
                # Process request
                response = await self.process_request(request)

                # Log successful response
                self.logger.bind(extra={
                    "request_id": request_id,
                    "status": response.status,
                    "response_time": response.response_time
                }).info("API Response")

                return response

            except Exception as e:
                # Log error
                self.logger.bind(extra={
                    "request_id": request_id,
                    "error": str(e).error("API Error"),
                    "error_type": type(e).__name__
                })
                raise

Microservice Communication
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from logeverything import Logger
    import requests

    class ServiceClient:
        def __init__(self, service_name):
            self.service_name = service_name
            self.logger = Logger(profile="service_client")

        def call_service(self, endpoint, data=None):
            call_id = generate_call_id()

            self.logger.bind(extra={
                "call_id": call_id,
                "service": self.service_name,
                "endpoint": endpoint,
                "data_size": len(str(data).info("Service call started")) if data else 0
            })

            try:
                response = requests.post(f"{self.service_name}/{endpoint}", json=data)

                self.logger.bind(extra={
                    "call_id": call_id,
                    "status_code": response.status_code,
                    "response_size": len(response.content).info("Service call completed")
                })

                return response.json()

            except Exception as e:
                self.logger.bind(extra={
                    "call_id": call_id,
                    "error": str(e).error("Service call failed")
                })
                raise

API Reference
-------------

Print Capture Methods
~~~~~~~~~~~~~~~~~~~~~

.. py:method:: Logger.capture_prints(**kwargs)

    Capture print statements as log messages.

    :param pattern: Regex pattern to match prints
    :type pattern: str, optional
    :param level: Log level for captured prints
    :type level: str, optional
    :param extra: Extra data to include with captured prints
    :type extra: dict, optional
    :returns: Context manager
    :rtype: ContextManager

.. py:method:: Logger.suppress_prints()

    Temporarily suppress print statements.

    :returns: Context manager
    :rtype: ContextManager

.. py:method:: Logger.redirect_prints(target)

    Redirect print statements to a target.

    :param target: Target for redirection (file, logger, etc.)
    :returns: Context manager
    :rtype: ContextManager

Integration Utilities
~~~~~~~~~~~~~~~~~~~~~

.. py:function:: setup_django_integration(profile="production")

    Set up Django integration.

    :param profile: Profile to use for Django logging
    :type profile: str

.. py:function:: setup_fastapi_integration(app, profile="api")

    Set up FastAPI integration.

    :param app: FastAPI application instance
    :param profile: Profile to use for API logging
    :type profile: str

.. py:function:: setup_flask_integration(app, profile="api")

    Set up Flask integration.

    :param app: Flask application instance
    :param profile: Profile to use for API logging
    :type profile: str
