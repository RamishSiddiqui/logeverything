LogEverything Documentation
===========================

.. image:: https://img.shields.io/pypi/v/logeverything.svg
   :target: https://pypi.org/project/logeverything/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/logeverything.svg
   :target: https://pypi.org/project/logeverything/
   :alt: Python versions

.. image:: https://img.shields.io/github/actions/workflow/status/logeverything/logeverything/ci.yml?branch=master
   :target: https://github.com/logeverything/logeverything/actions
   :alt: Build Status

.. image:: https://codecov.io/gh/logeverything/logeverything/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/logeverything/logeverything
   :alt: Coverage

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License: MIT

**High-performance, production-ready Python logging with zero configuration.**

LogEverything is a comprehensive, high-performance Python logging library designed to provide detailed logging with minimal code changes and exceptional performance. Simply add decorators to your functions for automatic, comprehensive logging with industry-leading performance.

✨ **Key Features**
--------------------

🚀 **High Performance**
  - **10k ops/sec** core logging throughput
  - **7.9k ops/sec** print capture throughput
  - **454 ops/sec** async-native logging with task isolation
  - **<0.5ms** decorator overhead
  - **Zero overhead** when logging is disabled

🛡️ **Smart & Safe**
  - **Zero configuration** - works immediately with intelligent defaults
  - **Automatic thread safety** with smart isolation
  - **Async task isolation** prevents logging contamination

🎨 **Beautiful Output**
  - Rich visual formatting with colors and symbols
  - Cross-platform terminal support
  - Hierarchical indentation and aligned columns

⚡ **Modern API**
  - **Unified @log decorator** that adapts to any context
  - **Smart logger selection** with the ``using`` parameter
  - **Intelligent type casting** between sync/async loggers and functions
  - **AsyncLogger** class for async applications
  - **Drop-in replacement** for Python's logging module

🔗 **Smart Binding**
  - **Loguru-style binding** with ``log.bind(key=value)``
  - **Registry-safe** - bound loggers don't pollute global registry
  - **Memory-safe** - automatic cleanup with no manual management
  - **Additive context** - chain bindings for rich structured data

🔗 **Distributed & Framework Integrations**
  - **Correlation IDs** propagated across requests and threads
  - **ASGI / WSGI middleware** for FastAPI, Starlette, Flask, Django
  - **Celery** signal-based task logging with correlation propagation
  - **Log transports** (HTTP, TCP, UDP) ship logs to a central collector

📊 **Monitoring Dashboard**
  - Multi-page layout with sidebar navigation (Overview, Logs, Operations, System)
  - Web-based dashboard with CPU/memory trend charts and log distribution
  - **Hierarchical log tree view** with expand/collapse and duration badges
  - Operation analytics with failure rates and duration tracking
  - Time-range filtering, full-text log search, and JSON data export
  - Auto-refresh toggle, keyboard shortcuts, dark/light themes

🌐 **Production Ready**
  - Comprehensive test suite with 65% coverage (395 tests)
  - Structured logging with JSON output
  - Monitoring API with ingestion endpoint and real-time WebSocket streaming

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install logeverything

Basic Usage
~~~~~~~~~~~

**Logger Classes** (Recommended)

.. executable-code::

   from logeverything import Logger

   # Simple logging
   log = Logger("my_app")
   log.info("Application started")
   log.warning("This is a warning")
   log.error("Something went wrong")

**Structured Logging with Binding**

.. executable-code::

   from logeverything import Logger

   # Create a base logger
   log = Logger("api_service")

   # Bind context for structured logging
   user_log = log.bind(user_id=12345, session_id="abc123")
   user_log.info("User logged in")

   # Chain bindings for richer context
   request_log = user_log.bind(request_id="req-789", endpoint="/api/users")
   request_log.info("Processing API request")

   # Original logger unchanged
   log.info("Service status check")

**Smart Decorators**

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log

   # Create a logger
   app_logger = Logger("my_app")

   @log(using="my_app")  # Use specific logger
   def calculate_total(a, b):
       """Calculate total with targeted logging."""
       return a + b

   @log  # Automatic logger selection
   def process_data(items):
       """Process data with automatic logger selection."""
       return [item * 2 for item in items]

   result1 = calculate_total(5, 10)
   result2 = process_data([1, 2, 3])
   print(f"Results: {result1}, {result2}")

**Async Applications**

.. executable-code::
   :async:

   import asyncio
   from logeverything.asyncio import AsyncLogger

   async def main():
       log = AsyncLogger("async_app")

       log.info("Starting async operation")
       await asyncio.sleep(0.1)  # Simulate async work
       log.info("Operation completed")

       return "Done"

   result = await main()
   print(f"Result: {result}")

Performance Comparison
~~~~~~~~~~~~~~~~~~~~~~

LogEverything delivers solid performance across all logging operations:

.. list-table:: Performance Benchmarks
   :header-rows: 1

   * - Component
     - Throughput
     - Avg Latency
   * - Core Logging
     - **10,027 ops/sec**
     - **0.10 ms**
   * - Print Capture
     - **7,896 ops/sec**
     - **0.13 ms**
   * - Async Logging (decorator)
     - **454 ops/sec**
     - **2.20 ms**
   * - Async Queue Handler
     - **7,565 ops/sec**
     - **0.13 ms**
   * - Decorator Overhead (@log_function)
     - **2,500 ops/sec**
     - **0.40 ms**

Why LogEverything?
------------------

**Zero Configuration**
  Works immediately with intelligent defaults that adapt to your environment

**High Performance**
  Industry-leading performance with automatic optimizations and fast-path execution

**Thread Safe**
  Automatic isolation prevents logging contamination in concurrent applications

**Beautiful Output**
  Color themes, visual hierarchy, Unicode symbols, and smart formatting

**Async Optimized**
  Native async/await support with 6.8x performance improvement

**Production Ready**
  Optimized for high-throughput applications and web services

Documentation
-------------

.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   installation
   quickstart
   tutorial

.. toctree::
   :maxdepth: 1
   :caption: User Guide

   user-guide/logger-classes
   user-guide/decorators
   user-guide/profiles
   user-guide/custom-handlers-guide
   user-guide/context-managers
   user-guide/print-capture
   user-guide/binding-registry
   user-guide/async-logging
   user-guide/async-sync-best-practices
   user-guide/correlation
   user-guide/integrations
   user-guide/transport
   user-guide/rotation-handlers
   user-guide/cli

.. toctree::
   :maxdepth: 1
   :caption: Monitoring Dashboard

   user-guide/dashboard
   user-guide/remote-logging

.. toctree::
   :maxdepth: 1
   :caption: Advanced Topics

   advanced/performance
   advanced/production
   advanced/examples/index
   user-guide/migration-async-messages

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/core
   api/correlation
   api/hierarchy
   api/handlers
   api/integrations
   api/transport
   api/profiles
   api/asyncio
   api/monitoring

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
