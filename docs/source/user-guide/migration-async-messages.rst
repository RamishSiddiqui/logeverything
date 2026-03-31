AsyncLogger Auto-Detection Messages - Migration Guide
=======================================================

If you're seeing new AsyncLogger auto-detection messages in your LogEverything applications, this guide explains what's happening and how to handle them.

🔍 **What You're Seeing**
-------------------------

Messages like these in your application output:

.. code-block:: text

   2025-08-08 18:01:14 | INFO | logeverything | AsyncLogger: Auto-detected environment: script
   2025-08-08 18:01:14 | INFO | logeverything | AsyncLogger: Applied async-optimized configuration for script environment
   2025-08-08 18:01:14 | INFO | logeverything | AsyncLogger: Using high-performance async logging

🎯 **Why This Happens**
-----------------------

These messages appear when LogEverything automatically creates **shared AsyncLogger** instances to handle async functions with sync loggers:

**Your Setup:**
   - You have a sync ``Logger`` with ``async_mode=True``
   - You have async functions decorated with ``@log(using="logger_name")``

**What LogEverything Does:**
   1. Detects async function execution with sync logger
   2. Creates a shared ``AsyncLogger`` named ``{original_name}_async_shared``
   3. The new AsyncLogger prints its auto-configuration messages

**This Is Normal and Expected Behavior** ✅

🛠 **Migration Options**
-----------------------

**Option 1: Keep Current Setup (Recommended)**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Your current setup is working correctly. The messages simply confirm that LogEverything is optimizing your async logging automatically.

**No changes needed** - your application performance is already optimized.

**Option 2: Use Pure AsyncLogger for Async-Heavy Apps**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your application is primarily async, consider using ``AsyncLogger`` directly:

.. code-block:: python

   # Before (sync logger with async functions)
   from logeverything import Logger
   logger = Logger("my_app", async_mode=True)

   # After (pure async logger)
   from logeverything.asyncio import AsyncLogger
   logger = AsyncLogger("my_app")

**Benefits:**
   - No shared logger creation overhead
   - Optimized for async from the start
   - Fewer auto-detection messages

**Option 3: Explicit Configuration (Quieter Messages)**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reduce message verbosity with explicit configuration:

.. code-block:: python

   from logeverything import Logger

   logger = Logger("my_app")
   logger.configure(
       level="INFO",
       profile="production",  # Explicit profile reduces auto-detection messages
       async_mode=True
   )

**Option 4: Suppress Messages Entirely**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you prefer no auto-detection messages at all:

.. code-block:: python

   from logeverything import Logger

   # Suppress auto-detection messages
   logger = Logger("my_app", level="INFO", profile="custom")
   logger.configure(
       async_mode=True,
       suppress_auto_detection=True  # If this option exists
   )

   # Or set logging level to WARNING to hide INFO messages
   logger.configure(level="WARNING", async_mode=True)

📊 **Performance Impact**
--------------------------

**Shared Logger Creation:** Minimal one-time cost (~2-3ms) when first async function executes

**No Performance Degradation:** Your application performance is the same or better

**Memory Usage:** Negligible - shared loggers are reused across async functions

🔧 **Best Practices Going Forward**
-------------------------------------

**For New Applications:**

.. code-block:: python

   # Async-heavy applications
   from logeverything.asyncio import AsyncLogger
   logger = AsyncLogger("app_name")

   # Mixed sync/async applications
   from logeverything import Logger
   logger = Logger("app_name", async_mode=True)

   # Pure sync applications
   from logeverything import Logger
   logger = Logger("app_name")

**Timing Best Practices:**

.. code-block:: python

   # ✅ GOOD: Create logger before decorators
   logger = Logger("my_app", async_mode=True)

   @log(using="my_app")
   async def my_function():
       pass

   # ❌ AVOID: Decorators before logger exists
   @log(using="my_app")  # Logger doesn't exist yet
   async def my_function():
       pass

   logger = Logger("my_app")  # Too late

🚨 **When to Take Action**
----------------------------

**Action Required If:**
   - You see many different ``_async_shared`` loggers being created
   - Shared logger creation happens frequently in tight loops
   - You have performance concerns

**No Action Needed If:**
   - Messages appear once per logger name
   - Your application performance is acceptable
   - You're just seeing the messages for the first time

**Troubleshooting Steps:**

.. code-block:: python

   # Check active loggers
   from logeverything.core import _active_loggers
   print("Active loggers:", list(_active_loggers.keys()))

   # Should see patterns like:
   # ['my_app', 'my_app_async_shared']  # Normal
   # ['temp_1_async_shared', 'temp_2_async_shared', ...]  # Problem

📈 **Benefits of This System**
-------------------------------

✅ **Automatic Optimization:** Your async functions get optimized logging without code changes

✅ **Backward Compatibility:** Existing sync loggers work with new async functions

✅ **Performance:** Shared loggers are reused, preventing resource waste

✅ **Zero Configuration:** Works automatically without manual async logger management

✅ **Intelligent:** Only creates shared loggers when actually needed

🔄 **Version Migration Notes**
-------------------------------

If you're upgrading LogEverything versions:

**Previous Behavior:** Async functions might have used sync logging with reduced performance

**New Behavior:** Async functions automatically get async-optimized shared loggers

**Impact:** Better performance, more informative messages, no breaking changes

**Recommendation:** No immediate action required - monitor and optimize over time

🎯 **Quick Decision Matrix**
-----------------------------

**Choose Pure AsyncLogger If:**
   - Application is >80% async functions
   - You want minimal message output
   - Performance is critical

**Keep Current Setup If:**
   - Application mixes sync and async
   - Current performance is acceptable
   - You prefer zero configuration

**Add Explicit Configuration If:**
   - You want to control message verbosity
   - You have specific logging requirements
   - You're building production applications

For detailed technical information, see :doc:`async-sync-best-practices`.
