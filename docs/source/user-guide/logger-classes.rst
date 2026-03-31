Logger Classes
==============

LogEverything provides two main logger classes: ``Logger`` for synchronous applications and ``AsyncLogger`` for async applications. Both provide the same intuitive API while being optimized for their respective contexts.

🏛️ **Logger Architecture**
---------------------------

Both logger classes inherit from ``BaseLogger`` and provide:

- **Automatic configuration** with intelligent environment detection
- **Structured logging** with additional context fields
- **Context managers** for hierarchical logging
- **Visual formatting** with colors, symbols, and indentation
- **Performance optimization** with configurable profiles

Logger Class (Synchronous)
---------------------------

The ``Logger`` class is designed for synchronous applications and provides a clean, simple interface.

Basic Usage
-----------

.. executable-code::

   from logeverything import Logger

   # Create a logger with automatic configuration
   log = Logger("my_app")

   # Basic logging methods
   log.debug("Debug information")
   log.info("Application started")
   log.warning("Warning message")
   log.error("Error occurred")
   log.critical("Critical system error")

Constructor Options
-------------------

.. executable-code::

   from logeverything import Logger

   # Simple logger with defaults
   simple_log = Logger("simple")

   # Logger with custom name and configuration
   custom_log = Logger(
       name="custom_app",
       auto_setup=True,  # Automatically configure (default: True)
       level="DEBUG",
       visual_mode=True,
       use_symbols=True,
       profile="development"
   )

   # Test both loggers
   simple_log.info("Simple logger message")
   custom_log.info("Custom logger message")

Configuration
-------------

Configure loggers with the ``configure()`` method:

.. executable-code::

   from logeverything import Logger

   log = Logger("configurable")

   # Basic configuration
   log.configure(
       level="INFO",
       visual_mode=True,
       use_symbols=True,
       use_colors=True
   )

   log.info("✨ Logger configured with visual enhancements")

   # Advanced configuration
   log.configure(
       profile="development",
       handlers=["console", "file"],
       file_path="app.log",
       async_mode=False,
       log_entry_exit=True
   )

   log.info("🔧 Advanced configuration applied")

Environment Detection
----------------------

Loggers automatically detect and adapt to your environment:

.. executable-code::

   from logeverything import Logger

   # Create logger - it auto-detects environment
   log = Logger("environment_demo")

   log.info("Logger automatically detected environment and applied optimal settings")

   # Manual override if needed
   log.configure(
       level="DEBUG",
       format="%(asctime)s | %(levelname)s | %(message)s"
   )

   log.debug("Environment settings overridden")

Structured Logging
-------------------

Add structured data to your logs using the ``.bind()`` method:

.. executable-code::

   from logeverything import Logger

   log = Logger("structured")

   # Logging with additional fields
   log.bind(user_id=12345,
           username="john_doe",
           ip_address="192.168.1.100",
           session_id="abc123").info("User logged in")

   # Bind context for consistent fields
   user_log = log.bind(user_id=12345, session_id="abc123")
   user_log.bind(product_id=789).info("Product viewed")
   user_log.bind(product_id=789, quantity=2).info("Item added to cart")
   user_log.bind(total_amount=99.99).info("Checkout initiated")

.. seealso::

   For comprehensive information about binding behavior, registry management,
   memory safety, and advanced binding patterns, see:

   :doc:`binding-registry`

Context Managers
----------------

Use context managers for hierarchical logging:

.. executable-code::

   from logeverything import Logger

   log = Logger("context_demo")
   log.configure(visual_mode=True, use_symbols=True)

   # Simple context
   with log.context("Data Processing"):
       log.info("🚀 Processing started")
       log.info("📁 Loading data files")
       log.info("✅ Processing completed")

   # Nested contexts
   with log.context("E-commerce Order"):
       log.info("📦 Processing order #12345")

       with log.context("Inventory Check"):
           log.info("🔍 Checking item availability")
           log.info("✅ Items in stock")

       with log.context("Payment Processing"):
           log.info("💳 Processing payment")
           log.info("✅ Payment successful")

       with log.context("Shipping"):
           log.info("📦 Creating shipping label")
           log.info("🚚 Order dispatched")

   log.info("🎉 Order completed successfully")

AsyncLogger Class (Asynchronous)
---------------------------------

The ``AsyncLogger`` class is specifically optimized for async applications with **6.8x better performance**.

Basic Async Usage
-----------------

.. executable-code::
   :async:

   from logeverything.asyncio import AsyncLogger
   import asyncio

   # Create async logger (automatically enables async_mode=True)
   log = AsyncLogger("async_app")

   # Basic async logging
   log.info("🚀 Async application started")

   # Simulate async operations
   await asyncio.sleep(0.1)
   log.info("⚡ Async operation completed")

High-Performance Async Methods
-------------------------------

AsyncLogger provides async-optimized methods:

.. executable-code::
   :async:

   from logeverything.asyncio import AsyncLogger
   import asyncio

   log = AsyncLogger("performance_demo")

   # Use async methods for better performance
   await log.ainfo("High-performance async info")
   await log.adebug("High-performance async debug")
   await log.awarning("High-performance async warning")
   await log.aerror("High-performance async error")
   await log.aexception("High-performance async exception")

   # Regular methods also work (slightly less optimized)
   log.info("Regular info method")

Async Configuration
-------------------

Configure AsyncLogger for optimal performance:

.. executable-code::
   :async:

   from logeverything.asyncio import AsyncLogger

   log = AsyncLogger("high_performance")

   # Configure for high-throughput applications
   await log.configure(
       level="INFO",
       async_queue_size=10000,     # Large queue for high volume
       async_flush_interval=0.05,  # Fast flush for responsiveness
       visual_mode=True,
       use_symbols=True
   )

   log.info("⚡ High-performance async logging configured")

Concurrent Async Logging
-------------------------

Process multiple async operations concurrently:

.. executable-code::
   :async:

   from logeverything.asyncio import AsyncLogger
   import asyncio

   async def process_user(user_id: int, log: AsyncLogger):
       """Process a user with async logging."""
       await log.ainfo(f"Processing user {user_id}")
       await asyncio.sleep(0.1)  # Simulate work
       await log.ainfo(f"User {user_id} processing completed")
       return f"User {user_id} processed"

   async def concurrent_processing():
       log = AsyncLogger("concurrent_demo")

       # Process multiple users concurrently
       tasks = [process_user(i, log) for i in range(5)]
       results = await asyncio.gather(*tasks)

       log.info(f"🎉 Processed {len(results)} users concurrently")
       return results

   results = await concurrent_processing()
   print(f"Results: {len(results)} users processed")

Async Context Managers
-----------------------

Use async context managers for hierarchical async logging:

.. executable-code::
   :async:

   from logeverything.asyncio import AsyncLogger
   import asyncio

   async def async_context_demo():
       log = AsyncLogger("async_context")

       # Async context manager
       async with log.context("Async Data Pipeline"):
           await log.ainfo("🚀 Starting async pipeline")

           async with log.context("Data Fetching"):
               await log.ainfo("📡 Fetching data from API")
               await asyncio.sleep(0.1)  # Simulate API call
               await log.ainfo("✅ Data fetched successfully")

           async with log.context("Data Processing"):
               await log.ainfo("⚙️  Processing data")
               await asyncio.sleep(0.1)  # Simulate processing
               await log.ainfo("✅ Data processed")

           await log.ainfo("🎉 Pipeline completed")

   await async_context_demo()

Performance Comparison
----------------------

Here's a performance comparison between Logger and AsyncLogger:

.. executable-code::
   :async:

   import asyncio
   import time
   from logeverything import Logger
   from logeverything.asyncio import AsyncLogger

   async def performance_comparison():
       # Test parameters
       num_logs = 100

       # Sync logger performance
       sync_log = Logger("sync_perf")
       start_time = time.time()

       for i in range(num_logs):
           sync_log.info(f"Sync log message {i}")

       sync_time = time.time() - start_time

       # Async logger performance
       async_log = AsyncLogger("async_perf")
       start_time = time.time()

       # Create tasks for concurrent logging
       tasks = [async_log.ainfo(f"Async log message {i}") for i in range(num_logs)]
       await asyncio.gather(*tasks)

       async_time = time.time() - start_time

       # Calculate performance improvement
       if async_time > 0:
           speedup = sync_time / async_time
           print(f"Sync logging: {sync_time:.4f}s")
           print(f"Async logging: {async_time:.4f}s")
           print(f"Speedup: {speedup:.1f}x faster with AsyncLogger!")
       else:
           print("Async logging was too fast to measure!")

   await performance_comparison()

Best Practices
--------------

Choosing the Right Logger
--------------------------

.. code-block:: python

   # Use Logger for synchronous applications
   from logeverything import Logger
   log = Logger("sync_app")

   # Use AsyncLogger for async applications
   from logeverything.asyncio import AsyncLogger
   log = AsyncLogger("async_app")

Configuration Patterns
-----------------------

.. code-block:: python

   # Development configuration
   log.configure(
       profile="development",
       level="DEBUG",
       visual_mode=True,
       use_symbols=True
   )

   # Production configuration
   log.configure(
       profile="production",
       level="WARNING",
       visual_mode=False,
       handlers=["file", "console"]
   )

   # High-performance async configuration
   await async_log.configure(
       async_queue_size=10000,
       async_flush_interval=0.05,
       level="INFO"
   )

Error Handling
--------------

.. code-block:: python

   # Logger handles exceptions automatically
   try:
       risky_operation()
   except Exception as e:
       log.exception("Operation failed")  # Includes traceback
       log.bind(error=str(e).error("Operation failed"))  # Custom message

Memory Management
-----------------

.. code-block:: python

   # For long-running applications, clean up resources
   async def cleanup():
       await async_log.close()  # Clean up async resources

   # Use context managers for automatic cleanup
   async with AsyncLogger("temp") as log:
       log.info("Temporary logging context")
       # Automatically cleaned up

API Reference
-------------

Logger Methods
--------------

.. code-block:: python

   # Logging methods
   log.debug(message, **kwargs)
   log.info(message, **kwargs)
   log.warning(message, **kwargs)
   log.error(message, **kwargs)
   log.critical(message, **kwargs)
   log.exception(message, **kwargs)  # Includes traceback

   # Configuration
   log.configure(**options)

   # Context management
   log.context(name, **context)
   log.bind(**context)

AsyncLogger Methods
-------------------

.. code-block:: python

   # High-performance async methods
   await log.ainfo(message, **kwargs)
   await log.adebug(message, **kwargs)
   await log.awarning(message, **kwargs)
   await log.aerror(message, **kwargs)
   await log.aexception(message, **kwargs)

   # Standard methods (also work)
   log.info(message, **kwargs)

   # Async configuration
   await log.configure(**options)

   # Async context management
   async with log.context(name, **context):
       pass

See Also
--------

- :doc:`decorators` - Automatic function logging with decorators
- :doc:`async-logging` - Advanced async logging patterns
- :doc:`context-managers` - Detailed context manager usage
- :doc:`../advanced/performance` - Performance optimization guide
