Profiles and Configuration
==========================

LogEverything provides a powerful profiling system that allows you to define, save, and reuse logging configurations across different environments and use cases.

Overview
--------

Profiles enable you to:

- **Environment-Specific Configs**: Different settings for development, staging, production
- **Use-Case Specific Configs**: Specialized configurations for APIs, background jobs, data processing
- **Team Consistency**: Share standardized logging configurations across your team
- **Quick Switching**: Easily switch between different logging behaviors

Understanding Profiles
----------------------

A profile is a named configuration that includes:

- **Log Level**: Minimum level for messages to be output
- **Format**: How log messages are structured and displayed
- **Handlers**: Where log messages are sent (console, file, external services)
- **Filters**: Rules for including/excluding specific messages
- **Metadata**: Additional context included with messages

Built-in Profiles
-----------------

LogEverything comes with several pre-configured profiles:

Development Profile
~~~~~~~~~~~~~~~~~~~

Optimized for local development with verbose output:

.. code-block:: python

    from logeverything import Logger

    # Use the development profile
    logger = Logger(profile="development")

    logger.debug("Detailed debug information")
    logger.info("General information")
    logger.warning("Warning message")
    logger.error("Error occurred")

Output:

.. code-block:: text

    2024-01-15 10:30:15.123 | DEBUG | main.py:15 | Detailed debug information
    2024-01-15 10:30:15.124 | INFO  | main.py:16 | General information
    2024-01-15 10:30:15.125 | WARN  | main.py:17 | Warning message
    2024-01-15 10:30:15.126 | ERROR | main.py:18 | Error occurred

Production Profile
~~~~~~~~~~~~~~~~~~

Optimized for production with structured output:

.. code-block:: python

    from logeverything import Logger

    # Use the production profile
    logger = Logger(profile="production")

    logger.bind(extra={"user_id": 12345, "ip": "192.168.1.1"}).info("User logged in")
    logger.bind(extra={"error_code": "DB001"}).error("Database connection failed")

Output:

.. code-block:: json

    {"timestamp": "2024-01-15T10:30:15.123Z", "level": "INFO", "message": "User logged in", "user_id": 12345, "ip": "192.168.1.1"}
    {"timestamp": "2024-01-15T10:30:15.124Z", "level": "ERROR", "message": "Database connection failed", "error_code": "DB001"}

Testing Profile
~~~~~~~~~~~~~~~

Optimized for testing with minimal output:

.. code-block:: python

    from logeverything import Logger

    # Use the testing profile
    logger = Logger(profile="testing")

    logger.debug("Debug info")  # Won't be shown
    logger.info("Test started")  # Won't be shown
    logger.error("Test failed")  # Will be shown

Output:

.. code-block:: text

    ERROR | Test failed

API Profile
~~~~~~~~~~~

Optimized for API services with request tracking:

.. code-block:: python

    from logeverything import Logger

    # Use the API profile
    logger = Logger(profile="api")

    logger.bind(extra={
        "method": "GET",
        "path": "/users/123",
        "status_code": 200,
        "response_time": 45
    }).info("GET /users/123")

Distributed Profile
~~~~~~~~~~~~~~~~~~~~

Optimized for multi-process and microservice deployments with log transport:

.. code-block:: python

    from logeverything import Logger

    # Use the distributed profile
    logger = Logger(profile="distributed")

    # Pair with an HTTP transport to ship logs to the dashboard
    from logeverything.transport.http import HTTPTransportHandler
    handler = HTTPTransportHandler("http://dashboard:8999/api/ingest/logs")
    logger.add_handler(handler)

    logger.info("This is logged to console, JSON, and shipped to the dashboard")

The distributed profile uses INFO level, console + JSON handlers, enables
async mode, and disables visual formatting for clean structured output suitable
for central collection.

.. seealso::

   :doc:`transport` for details on HTTP, TCP, and UDP log transports.

   :doc:`integrations` for framework middleware that auto-manages correlation IDs.

Custom Profiles
---------------

Creating Custom Profiles
~~~~~~~~~~~~~~~~~~~~~~~~

Define your own profiles for specific needs:

.. code-block:: python

    from logeverything import Logger, Profile

    # Define a custom profile
    custom_profile = Profile(
        name="data_processing",
        level="INFO",
        format="{timestamp} | {level} | {module} | {message}",
        include_caller=True,
        timestamp_format="%Y-%m-%d %H:%M:%S",
        handlers=["console", "file"],
        file_path="data_processing.log"
    )

    # Use the custom profile
    logger = Logger(profile=custom_profile)

    logger.info("Processing started")
    logger.info("Processed 1000 records")
    logger.warning("Skipped 5 invalid records")

Saving and Loading Profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Save profiles to files for reuse:

.. code-block:: python

    from logeverything import Logger, Profile

    # Create a profile
    profile = Profile(
        name="analytics",
        level="DEBUG",
        format="[{timestamp}] {level}: {message}",
        include_metadata=True
    )

    # Save to file
    profile.save("analytics_profile.json")

    # Load from file
    loaded_profile = Profile.load("analytics_profile.json")
    logger = Logger(profile=loaded_profile)

Profile Configuration Options
-----------------------------

Level Settings
~~~~~~~~~~~~~~

.. code-block:: python

    from logeverything import Profile

    profile = Profile(
        name="verbose",
        level="DEBUG",           # Minimum level to log
        console_level="INFO",    # Different level for console output
        file_level="DEBUG"       # Different level for file output
    )

Format Settings
~~~~~~~~~~~~~~~

.. code-block:: python

    profile = Profile(
        name="detailed",
        format="{timestamp} | {level:>8} | {module}:{function}:{line} | {message}",
        timestamp_format="%Y-%m-%d %H:%M:%S.%f",
        include_caller=True,
        include_metadata=True,
        colorize=True
    )

Handler Settings
~~~~~~~~~~~~~~~~

.. code-block:: python

    profile = Profile(
        name="multi_output",
        handlers=["console", "file", "syslog"],
        file_path="app.log",
        file_rotation="daily",
        file_max_size="10MB",
        syslog_address=("localhost", 514)
    )

Environment-Based Profiles
--------------------------

Automatically select profiles based on environment:

.. code-block:: python

    import os
    from logeverything import Logger

    # Get environment
    env = os.getenv("ENVIRONMENT", "development")

    # Environment-specific profiles
    profiles = {
        "development": "development",
        "staging": "production",
        "production": "production"
    }

    logger = Logger(profile=profiles.get(env, "development"))
    logger.info(f"Logger initialized for {env} environment")

Profile Inheritance
-------------------

Create profiles that inherit from base profiles:

.. code-block:: python

    from logeverything import Profile

    # Base profile
    base_profile = Profile(
        name="base",
        level="INFO",
        format="{timestamp} | {level} | {message}",
        handlers=["console"]
    )

    # Inherit and override specific settings
    api_profile = Profile(
        name="api",
        parent=base_profile,
        include_metadata=True,
        handlers=["console", "file"],
        file_path="api.log"
    )

    # Background job profile inheriting from base
    job_profile = Profile(
        name="background_job",
        parent=base_profile,
        level="WARNING",  # Override level
        format="JOB | {timestamp} | {level} | {message}"  # Override format
    )

Dynamic Profile Switching
-------------------------

Switch profiles at runtime:

.. code-block:: python

    from logeverything import Logger

    logger = Logger(profile="development")
    logger.info("Development mode logging")

    # Switch to production profile
    logger.switch_profile("production")
    logger.info("Now using production profile")

    # Switch to custom profile
    custom_profile = Profile(name="debug", level="DEBUG")
    logger.switch_profile(custom_profile)
    logger.debug("Debug information now visible")

Profile Validation
------------------

Validate profile configurations:

.. code-block:: python

    from logeverything import Profile

    try:
        profile = Profile(
            name="invalid",
            level="INVALID_LEVEL",  # This will raise an error
            format="{invalid_field}"  # This will also raise an error
        )
    except ValueError as e:
        print(f"Profile validation error: {e}")

    # Check if profile is valid
    profile = Profile(name="test", level="INFO")
    if profile.is_valid():
        print("Profile is valid")
    else:
        print("Profile has errors:", profile.get_errors())

Team Configuration
------------------

Share profiles across your team using configuration files:

**team_profiles.yaml**:

.. code-block:: yaml

    development:
      level: DEBUG
      format: "{timestamp} | {level:>8} | {module} | {message}"
      handlers: [console]
      colorize: true

    production:
      level: INFO
      format: '{"timestamp": "{timestamp}", "level": "{level}", "message": "{message}"}'
      handlers: [console, file]
      file_path: "/var/log/app.log"
      include_metadata: true

    testing:
      level: ERROR
      format: "{level} | {message}"
      handlers: [console]

**Loading team profiles**:

.. code-block:: python

    from logeverything import Logger, Profile
    import yaml

    # Load team profiles
    with open("team_profiles.yaml", "r") as f:
        team_config = yaml.safe_load(f)

    # Create profiles from config
    profiles = {}
    for name, config in team_config.items():
        profiles[name] = Profile(name=name, **config)

    # Use environment-specific profile
    env = os.getenv("ENVIRONMENT", "development")
    logger = Logger(profile=profiles[env])

Advanced Profile Features
-------------------------

Conditional Logging
~~~~~~~~~~~~~~~~~~~

Enable logging based on conditions:

.. code-block:: python

    from logeverything import Profile

    profile = Profile(
        name="conditional",
        level="DEBUG",
        conditions={
            "user_id": lambda x: x in [1, 2, 3],  # Only log for specific users
            "endpoint": lambda x: x.startswith("/api/"),  # Only log API calls
        }
    )

Custom Formatters
~~~~~~~~~~~~~~~~~

Define custom formatting functions:

.. code-block:: python

    def security_formatter(record):
        if record.level == "ERROR":
            return f"🚨 SECURITY ALERT: {record.message}"
        return f"🔒 {record.level}: {record.message}"

    profile = Profile(
        name="security",
        formatter=security_formatter,
        level="INFO"
    )

Profile Middleware
~~~~~~~~~~~~~~~~~~

Add middleware to process log records:

.. code-block:: python

    def add_request_id(record):
        """Add request ID to all log records"""
        import threading
        request_id = getattr(threading.current_thread(), 'request_id', None)
        if request_id:
            record.extra['request_id'] = request_id
        return record

    profile = Profile(
        name="request_tracking",
        middleware=[add_request_id],
        level="INFO"
    )

Best Practices
--------------

1. **Environment Separation**: Use different profiles for different environments
2. **Naming Convention**: Use descriptive names like "api_production" or "batch_debug"
3. **Documentation**: Document your custom profiles and their use cases
4. **Validation**: Always validate profiles before using them in production
5. **Version Control**: Store profile configurations in version control
6. **Security**: Be careful with sensitive information in profiles (use environment variables)

Common Profile Patterns
-----------------------

Microservice Profile
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    microservice_profile = Profile(
        name="microservice",
        level="INFO",
        format='{"service": "user-service", "timestamp": "{timestamp}", "level": "{level}", "message": "{message}"}',
        include_metadata=True,
        handlers=["console", "elasticsearch"],
        elasticsearch_host="localhost:9200"
    )

Data Pipeline Profile
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    pipeline_profile = Profile(
        name="data_pipeline",
        level="INFO",
        format="{timestamp} | PIPELINE | {level} | {message}",
        handlers=["console", "file"],
        file_path="/var/log/pipeline.log",
        file_rotation="hourly"
    )

Debug Profile
~~~~~~~~~~~~~

.. code-block:: python

    debug_profile = Profile(
        name="debug",
        level="DEBUG",
        format="{timestamp} | {level} | {module}:{function}:{line} | {message}",
        include_caller=True,
        include_stack_trace=True,
        colorize=True
    )

API Reference
-------------

Profile Class
~~~~~~~~~~~~~

.. py:class:: Profile(name, **kwargs)
    :no-index:

    Create a new logging profile.

    :param name: Profile name
    :type name: str
    :param level: Minimum logging level
    :type level: str
    :param format: Log message format string
    :type format: str
    :param handlers: List of output handlers
    :type handlers: List[str]
    :param kwargs: Additional configuration options

.. py:method:: Profile.save(filepath)
    :no-index:

    Save profile to a file.

    :param filepath: Path to save the profile
    :type filepath: str

.. py:classmethod:: Profile.load(filepath)
    :no-index:

    Load profile from a file.

    :param filepath: Path to load the profile from
    :type filepath: str
    :returns: Loaded profile
    :rtype: Profile

.. py:method:: Profile.is_valid()

    Check if profile configuration is valid.

    :returns: True if valid, False otherwise
    :rtype: bool

.. py:method:: Profile.get_errors()

    Get validation errors for the profile.

    :returns: List of validation errors
    :rtype: List[str]

Logger Profile Methods
~~~~~~~~~~~~~~~~~~~~~~

.. py:method:: Logger.switch_profile(profile)

    Switch to a different profile.

    :param profile: Profile name or Profile object
    :type profile: Union[str, Profile]

.. py:method:: Logger.get_current_profile()

    Get the currently active profile.

    :returns: Current profile
    :rtype: Profile

.. py:method:: Logger.list_available_profiles()

    List all available profiles.

    :returns: List of profile names
    :rtype: List[str]
