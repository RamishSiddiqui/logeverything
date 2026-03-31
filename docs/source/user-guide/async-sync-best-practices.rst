Async/Sync Best Practices & Shared Logger Behavior
=====================================================

This guide explains LogEverything's intelligent sync/async compatibility system, shared logger creation, and performance best practices when mixing sync and async logging patterns.

🧠 **Understanding Shared Logger Creation**
-------------------------------------------

When you use a sync Logger with async functions (or vice versa), LogEverything automatically creates **shared loggers** for optimal performance and compatibility.

**How It Works:**

1. **At Decoration Time**: The ``@log`` decorator is applied but no shared logger is created yet
2. **At Execution Time**: When the decorated function runs, LogEverything detects the async/sync mismatch
3. **Automatic Creation**: A shared logger is created with the name pattern ``{original_name}_async_shared`` or ``{original_name}_sync_shared``
4. **Configuration Inheritance**: The shared logger inherits all settings from the original logger
5. **Registry Management**: Both loggers are maintained in the global registry for reuse

**Example of Shared Logger Creation:**

.. executable-code::
   :async:

   import asyncio
   from logeverything import Logger
   from logeverything.decorators import log
   from logeverything.core import _active_loggers

   # Step 1: Create sync logger
   sync_logger = Logger("MyApp")
   sync_logger.configure(async_mode=True)  # Enable async compatibility
   print(f"Initial loggers: {list(_active_loggers.keys())}")

   # Step 2: Define async function (no shared logger created yet)
   @log(using="MyApp")
   async def fetch_data(item_id):
       await asyncio.sleep(0.1)  # Simulate async I/O
       return f"data_{item_id}"

   print(f"After decoration: {list(_active_loggers.keys())}")

   # Step 3: Execute async function (shared logger created now)
   result = await fetch_data(123)
   print(f"After execution: {list(_active_loggers.keys())}")
   print(f"Result: {result}")

**Output Explanation:**
   - Initial: ``['MyApp']`` - Only your sync logger
   - After decoration: ``['MyApp']`` - Still just your sync logger
   - After execution: ``['MyApp', 'MyApp_async_shared']`` - Shared logger created on demand

🔧 **Performance Characteristics**
----------------------------------

Understanding the performance implications of different logging patterns:

**Pure Sync Logging (Fastest for sync code):**
   - Logger: ``Logger("app")``
   - Functions: Sync functions only
   - Performance: No async overhead, direct logging
   - Use case: Traditional applications, scripts, sync APIs

**Pure Async Logging (Fastest for async code):**
   - Logger: ``AsyncLogger("app")``
   - Functions: Async functions primarily
   - Performance: Optimized for async from the start
   - Use case: FastAPI apps, async microservices, real-time systems

**Mixed Logging with Shared Creation:**
   - Logger: ``Logger("app", async_mode=True)`` or ``AsyncLogger("app")``
   - Functions: Mix of sync and async
   - Performance: Slight overhead for shared logger creation
   - Use case: Applications transitioning to async, mixed workloads

**Performance Benchmark Results:**

.. code-block:: text

   Logger Type                    | Creation Time | Execution Overhead
   -------------------------------|---------------|-------------------
   Pure Logger (sync only)       |    42ms       |    None
   Pure AsyncLogger (async only)  |     5ms       |    None
   Logger + async_mode + mixed    |    12ms       |    ~2-3ms (first call)

   Shared logger creation happens once per unique name pattern.

📋 **Best Practices**
---------------------

**Choose the Right Logger Type:**

.. code-block:: python

   # ✅ For pure sync applications
   from logeverything import Logger
   log = Logger("sync_app")

   # ✅ For pure async applications
   from logeverything.asyncio import AsyncLogger
   log = AsyncLogger("async_app")

   # ✅ For mixed sync/async applications
   from logeverything import Logger
   log = Logger("mixed_app")
   log.configure(async_mode=True)  # Enable async compatibility

**Timing Best Practices:**

.. code-block:: python

   # ✅ GOOD: Create loggers before decorators
   from logeverything import Logger

   logger = Logger("my_app")
   logger.configure(async_mode=True)

   @log(using="my_app")
   async def my_function():
       pass

   # ❌ AVOID: Decorators before logger creation
   @log(using="not_created_yet")  # May cause temporary logger creation
   async def my_function():
       pass

   logger = Logger("not_created_yet")  # Created too late

**Configuration Best Practices:**

.. code-block:: python

   # ✅ Configure async_mode when you'll use async functions
   sync_logger = Logger("app")
   sync_logger.configure(
       async_mode=True,        # Enable async compatibility
       level="INFO",
       profile="production"
   )

   # ✅ AsyncLogger is automatically async-ready
   async_logger = AsyncLogger("app")
   async_logger.configure(
       level="INFO",
       profile="production"
   )

**Decorator Usage Best Practices:**

.. code-block:: python

   # ✅ Use @log for universal compatibility
   from logeverything.decorators import log

   @log  # Automatically selects best available logger
   def any_function():
       pass

   @log(using="specific_logger")  # Use specific logger
   async def async_function():
       pass

🔍 **Understanding Auto-Detection Messages**
--------------------------------------------

When you see messages like "AsyncLogger: Auto-detected environment: script", here's what's happening:

**Why These Messages Appear:**
   1. You created a sync Logger with ``async_mode=True``
   2. An async function with ``@log`` decorator executes
   3. LogEverything creates a shared AsyncLogger for async compatibility
   4. The new AsyncLogger prints its auto-configuration messages

**These Messages Are Normal:**
   - ✅ They indicate the system is working correctly
   - ✅ They show async compatibility was automatically enabled
   - ✅ They help you understand when shared loggers are created
   - ✅ They provide configuration confirmation for the new logger

**Example Output:**

.. code-block:: text

   2025-08-08 18:01:14 | INFO | logeverything | Auto-detected environment: script
   2025-08-08 18:01:14 | INFO | logeverything | Applied optimized default configuration for script environment
   2025-08-08 18:01:14 | INFO | logeverything | AsyncLogger: Auto-detected environment: script
   2025-08-08 18:01:14 | INFO | logeverything | AsyncLogger: Applied async-optimized configuration for script environment
   2025-08-08 18:01:14 | INFO | logeverything | AsyncLogger: Using high-performance async logging

**Message Explanation:**
   - First set: Your original sync Logger auto-configuring
   - Second set: Shared AsyncLogger being created for your async function

**Suppressing Auto-Detection Messages:**

If you prefer quieter startup, configure loggers explicitly:

.. code-block:: python

   # Suppress auto-detection by explicit configuration
   logger = Logger("app", level="INFO", profile="production")
   # or
   logger.configure(level="INFO", profile="production", suppress_auto_detection=True)

⚡ **Migration Strategies**
---------------------------

**Migrating Sync Apps to Async:**

.. code-block:: python

   # Phase 1: Enable async compatibility
   logger = Logger("my_app")
   logger.configure(async_mode=True)

   # Phase 2: Gradually convert functions to async
   @log(using="my_app")
   async def new_async_function():
       pass

   @log(using="my_app")  # Still works with same logger
   def existing_sync_function():
       pass

   # Phase 3: Eventually migrate to AsyncLogger for best performance
   # async_logger = AsyncLogger("my_app")  # When fully async

**Migrating from Other Loggers:**

.. code-block:: python

   # From stdlib logging
   import logging
   old_logger = logging.getLogger("app")

   # To LogEverything (preserves existing functionality)
   from logeverything import Logger
   new_logger = Logger("app", level="INFO")

   # Gradual decorator adoption
   @log(using="app")  # Add decorators incrementally
   def enhanced_function():
       pass

🛠 **Troubleshooting**
---------------------

**Common Issues and Solutions:**

**Issue: "Decorator requested logger 'xyz' but it was not found"**

.. code-block:: python

   # ❌ Problem: Logger created after decorator
   @log(using="my_app")
   def my_function():
       pass

   my_logger = Logger("my_app")  # Too late!

   # ✅ Solution: Create logger first
   my_logger = Logger("my_app")

   @log(using="my_app")
   def my_function():
       pass

**Issue: Unexpected AsyncLogger messages**

.. code-block:: python

   # ❌ You see AsyncLogger messages but only created sync Logger
   # This is normal! It means shared AsyncLogger was created for async functions

   # ✅ This is expected behavior when mixing sync/async
   sync_logger = Logger("app", async_mode=True)

   @log(using="app")
   async def async_func():  # Triggers shared AsyncLogger creation
       pass

**Issue: Performance slower than expected**

.. code-block:: python

   # ❌ Frequent shared logger creation
   for i in range(1000):
       new_logger = Logger(f"temp_{i}", async_mode=True)
       # Creates many shared loggers

   # ✅ Reuse loggers
   app_logger = Logger("app", async_mode=True)

   @log(using="app")  # Single shared logger created once
   async def process_item(item):
       pass

📊 **Monitoring Shared Logger Creation**
-----------------------------------------

You can monitor shared logger creation in your applications:

.. code-block:: python

   from logeverything.core import _active_loggers

   # Monitor logger registry
   print("Active loggers:", list(_active_loggers.keys()))

   # After async function execution, you might see:
   # ['my_app', 'my_app_async_shared']

**Logger Registry Inspection:**

.. code-block:: python

   from logeverything.core import _active_loggers

   def inspect_loggers():
       for name, logger in _active_loggers.items():
           logger_type = type(logger).__name__
           print(f"Logger '{name}': {logger_type}")

   # Example output:
   # Logger 'my_app': Logger
   # Logger 'my_app_async_shared': AsyncLogger

This shared logger system ensures optimal performance while maintaining complete compatibility between sync and async code patterns.
