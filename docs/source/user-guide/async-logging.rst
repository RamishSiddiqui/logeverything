Async Logging
=============

LogEverything provides high-performance async logging optimized for modern Python applications. This guide covers async logging patterns, the AsyncLogger class, and performance optimization techniques.

🚀 **Why Async Logging?**
--------------------------

**Performance Benefits:**
   - **454 ops/sec** async-native logging with task isolation
   - **Non-blocking** - doesn't slow down your application
   - **Concurrent processing** - multiple log operations simultaneously
   - **Queue-based** - background processing for heavy logging

**Perfect for:**
   - Web applications (FastAPI, aiohttp, Django async views)
   - High-throughput systems (data processing, API servers)
   - Real-time applications (chat, gaming, streaming)
   - Microservices with async communication
   - Data pipelines and ML training

.. seealso::

   📋 **Mixing Sync and Async Logging?**

   When using both sync loggers and async functions (or vice versa), LogEverything automatically creates **shared loggers** for optimal compatibility. See :doc:`async-sync-best-practices` for detailed information about shared logger creation, performance implications, and best practices for mixed sync/async applications.

⚡ **AsyncLogger Class**
------------------------

The ``AsyncLogger`` class is specifically optimized for async applications:

Basic Usage
-----------

.. executable-code::
   :async:

   from logeverything.asyncio import AsyncLogger
   import asyncio

   # AsyncLogger automatically enables async_mode=True
   log = AsyncLogger("async_app")

   log.info("🚀 Async application started")

   # Simulate async operations
   await asyncio.sleep(0.1)
   log.info("⚡ Async operation completed")

High-Performance Async Methods
-------------------------------

AsyncLogger provides async-optimized methods for maximum performance:

.. executable-code::
   :async:

   from logeverything.asyncio import AsyncLogger
   import asyncio

   async def high_performance_logging():
       log = AsyncLogger("high_perf")

       # Use async methods for best performance (6.8x faster)
       await log.ainfo("High-performance async info")
       await log.adebug("High-performance async debug")
       await log.awarning("High-performance async warning")
       await log.aerror("High-performance async error")

       # Regular methods also work (slightly less optimized)
       log.info("Regular sync method")

       return "Logging completed"

   result = await high_performance_logging()
   print(f"Result: {result}")

Configuration for Performance
-----------------------------

Configure AsyncLogger for optimal performance:

.. executable-code::
   :async:

   from logeverything.asyncio import AsyncLogger

   async def configure_performance():
       log = AsyncLogger("optimized")

       # Configure for high-throughput applications
       await log.configure(
           level="INFO",
           async_queue_size=10000,     # Large queue for high volume
           async_flush_interval=0.05,  # Fast flush for responsiveness
           visual_mode=True,
           use_symbols=True
       )

       log.info("⚡ High-performance async logging configured")

       # Test high-volume logging
       for i in range(100):
           log.info(f"High-volume log {i}")

       return "Configuration complete"

   result = await configure_performance()
   print(f"Result: {result}")

🔄 **Intelligent Type Casting with Async**
--------------------------------------------

LogEverything automatically handles sync/async logger mismatches, making it easy to integrate async logging into existing applications:

Sync Loggers with Async Functions
----------------------------------

You can use regular (sync) loggers with async functions seamlessly:

.. executable-code::
   :async:

   import asyncio
   from logeverything import Logger  # Regular sync logger
   from logeverything.decorators import log

   # Create a regular sync logger
   sync_logger = Logger("mixed_service", level="INFO")

   @log(using="mixed_service")  # Automatically casts sync logger for async compatibility
   async def async_data_fetch(resource_id):
       """Async function using sync logger - works automatically."""
       await asyncio.sleep(0.1)  # Simulate async database fetch
       return {"id": resource_id, "data": "fetched_data", "timestamp": "2024-01-01"}

   @log(using="mixed_service")  # Same logger works with both sync and async
   def sync_data_validate(data):
       """Sync function using the same logger."""
       return data.get("id") is not None and len(data.get("data", "")) > 0

   # Both functions work with the same logger
   data = await async_data_fetch(123)
   is_valid = sync_data_validate(data)
   print(f"Data valid: {is_valid}")

Async Loggers with Sync Functions
----------------------------------

AsyncLoggers also work seamlessly with sync functions:

.. executable-code::

   from logeverything.asyncio import AsyncLogger
   from logeverything.decorators import log

   # Create an async logger
   async_logger = AsyncLogger("async_service", level="DEBUG")

   @log(using="async_service")  # Automatically casts async logger for sync compatibility
   def sync_computation(x, y):
       """Sync function using async logger - works automatically."""
       result = (x ** 2) + (y ** 2)
       return {"result": result, "inputs": [x, y]}

   @log(using="async_service")  # Same logger can be used in mixed environments
   def sync_formatter(data):
       """Sync formatting function."""
       return f"Result: {data['result']} from inputs {data['inputs']}"

   # Sync functions work with async logger
   computed = sync_computation(3, 4)
   formatted = sync_formatter(computed)
   print(formatted)

Mixed Application Pattern
-------------------------

Real-world applications often mix sync and async code. Type casting makes this seamless:

.. executable-code::
   :async:

   import asyncio
   from logeverything import Logger
   from logeverything.decorators import log

   # Single logger for the entire application
   app_logger = Logger("UserApplication", level="INFO")

   @log(using="UserApplication")
   def validate_user_input(user_data):
       """Sync validation - fast and simple."""
       required_fields = ["username", "email"]
       return all(field in user_data for field in required_fields)

   @log(using="UserApplication")
   async def save_user_to_database(user_data):
       """Async database operation."""
       await asyncio.sleep(0.1)  # Simulate async database save
       user_id = hash(user_data["username"]) % 10000
       return {"user_id": user_id, "status": "saved"}

   @log(using="UserApplication")
   def send_welcome_email(user_id):
       """Sync email sending (using sync email library)."""
       # Simulate email sending
       return f"Welcome email sent to user {user_id}"

   async def process_user_registration(user_data):
       """Complete user registration pipeline mixing sync/async."""

       # Step 1: Sync validation
       if not validate_user_input(user_data):
           return {"error": "Invalid user data"}

       # Step 2: Async database save
       save_result = await save_user_to_database(user_data)

       # Step 3: Sync email (using existing sync email library)
       email_result = send_welcome_email(save_result["user_id"])

       return {"success": True, "user_id": save_result["user_id"], "email": email_result}

   # Test the mixed pipeline
   user_data = {"username": "alice", "email": "alice@example.com"}
   result = await process_user_registration(user_data)
   print(f"Registration result: {result}")

**Benefits of Type Casting:**

- **No Code Changes**: Existing sync code works with async loggers
- **Gradual Migration**: Add async functionality without changing logging setup
- **Consistent Logging**: Single logger handles entire application regardless of sync/async mix
- **Zero Configuration**: Automatic detection and conversion
- **Performance Optimized**: Casting is cached for minimal overhead

🏃‍♂️ **Concurrent Async Logging**
-------------------------------------

Process multiple async operations with concurrent logging:

.. executable-code::
   :async:

   from logeverything.asyncio import AsyncLogger
   import asyncio
   import random

   async def process_user_request(user_id: int, log: AsyncLogger):
       """Process a user request with async logging."""
       await log.ainfo(f"📨 Processing request for user {user_id}")

       # Simulate async work with random duration
       work_time = random.uniform(0.05, 0.15)
       await asyncio.sleep(work_time)

       # Simulate different outcomes
       if random.random() > 0.8:  # 20% chance of warning
           await log.awarning(f"⚠️  Slow processing for user {user_id}", duration=work_time)
       else:
           await log.ainfo(f"✅ Request completed for user {user_id}", duration=work_time)

       return {"user_id": user_id, "status": "completed", "duration": work_time}

   async def concurrent_processing():
       log = AsyncLogger("concurrent_demo")

       # Process multiple users concurrently
       user_ids = range(1, 11)  # 10 users
       tasks = [process_user_request(user_id, log) for user_id in user_ids]

       log.info(f"🚀 Starting concurrent processing of {len(tasks)} requests")
       start_time = asyncio.get_event_loop().time()

       results = await asyncio.gather(*tasks)

       end_time = asyncio.get_event_loop().time()
       total_time = end_time - start_time

       log.bind(requests=len(results),
             total_time=f"{total_time:.3f}s",
             throughput=f"{len(results)/total_time:.1f} req/s").info(f"🎉 Concurrent processing completed")

       return results

   results = await concurrent_processing()
   print(f"Processed {len(results)} requests concurrently")

📊 **Async Context Managers**
------------------------------

Use async context managers for hierarchical async logging:

.. executable-code::
   :async:

   from logeverything.asyncio import AsyncLogger
   import asyncio

   async def data_pipeline_demo():
       """Demonstrate async context managers in a data pipeline."""
       log = AsyncLogger("data_pipeline")

       async with log.context("Data Processing Pipeline"):
           await log.ainfo("🚀 Starting async data pipeline")

           # Data fetching phase
           async with log.context("Data Fetching"):
               await log.ainfo("📡 Connecting to data sources")
               await asyncio.sleep(0.1)  # Simulate API calls

               await log.ainfo("📥 Fetching user data")
               await asyncio.sleep(0.1)  # Simulate data fetch

               await log.ainfo("📥 Fetching product data")
               await asyncio.sleep(0.1)  # Simulate data fetch

               await log.ainfo("✅ Data fetching completed")

           # Data processing phase
           async with log.context("Data Processing"):
               await log.ainfo("⚙️  Starting data transformation")
               await asyncio.sleep(0.15)  # Simulate processing

               await log.ainfo("🔗 Joining datasets")
               await asyncio.sleep(0.1)  # Simulate joins

               await log.ainfo("📊 Calculating aggregations")
               await asyncio.sleep(0.1)  # Simulate calculations

               await log.ainfo("✅ Data processing completed")

           # Data validation phase
           async with log.context("Data Validation"):
               await log.ainfo("🔍 Validating data quality")
               await asyncio.sleep(0.05)  # Simulate validation

               await log.awarning("⚠️  Found 3 invalid records")
               await log.ainfo("🧹 Cleaning invalid data")
               await asyncio.sleep(0.05)  # Simulate cleaning

               await log.ainfo("✅ Data validation completed")

           await log.ainfo("🎉 Pipeline completed successfully")

   await data_pipeline_demo()

⚙️ **Async Decorators**
------------------------

Use async-optimized decorators for automatic function logging:

.. executable-code::
   :async:

   from logeverything.decorators import log
   from logeverything.asyncio import async_log_function
   import asyncio

   # Smart decorator automatically detects async functions
   @log
   async def fetch_user_profile(user_id: int):
       """Fetch user profile asynchronously."""
       await asyncio.sleep(0.1)  # Simulate database query
       return {
           "user_id": user_id,
           "name": f"User {user_id}",
           "profile": {"preferences": {}, "settings": {}}
       }

   # Explicit async decorator for fine control
   @async_log_function
   async def update_user_profile(user_id: int, updates: dict):
       """Update user profile asynchronously."""
       await asyncio.sleep(0.05)  # Simulate database update
       return {"user_id": user_id, "updated_fields": list(updates.keys())}

   async def test_async_decorators():
       # Test both decorated functions
       profile = await fetch_user_profile(123)

       updates = {"theme": "dark", "notifications": True}
       update_result = await update_user_profile(123, updates)

       print(f"Profile: {profile}")
       print(f"Update result: {update_result}")

   await test_async_decorators()

🏗️ **Async Class Logging**
----------------------------

Log all methods of async classes automatically:

.. executable-code::
   :async:

   from logeverything.asyncio import async_log_class
   import asyncio

   @async_log_class
   class AsyncUserService:
       """Async user service with automatic method logging."""

       def __init__(self, name: str):
           self.name = name
           self.processed_count = 0

       async def authenticate(self, username: str, password: str):
           """Authenticate user asynchronously."""
           await asyncio.sleep(0.05)  # Simulate auth check

           # Simple authentication simulation
           is_valid = len(password) >= 8
           self.processed_count += 1

           return {"valid": is_valid, "token": f"token_{username}" if is_valid else None}

       async def get_user_data(self, user_id: int):
           """Get user data asynchronously."""
           await asyncio.sleep(0.1)  # Simulate database query
           self.processed_count += 1

           return {
               "user_id": user_id,
               "username": f"user_{user_id}",
               "email": f"user{user_id}@example.com",
               "active": True
           }

       async def update_user(self, user_id: int, updates: dict):
           """Update user asynchronously."""
           await asyncio.sleep(0.08)  # Simulate database update
           self.processed_count += 1

           return {"user_id": user_id, "updated": True, "changes": updates}

       def get_stats(self):
           """Get service statistics (sync method)."""
           return {"service": self.name, "processed": self.processed_count}

   async def test_async_class():
       service = AsyncUserService("UserService_v1")

       # All async methods are automatically logged
       auth_result = await service.authenticate("alice", "secretpassword")
       user_data = await service.get_user_data(123)
       update_result = await service.update_user(123, {"active": False})

       # Sync method also logged
       stats = service.get_stats()

       print(f"Auth: {auth_result}")
       print(f"User: {user_data}")
       print(f"Update: {update_result}")
       print(f"Stats: {stats}")

   await test_async_class()

🔥 **Performance Comparison**
-----------------------------

See the performance difference between sync and async logging:

.. executable-code::
   :async:

   import asyncio
   import time
   from logeverything import Logger
   from logeverything.asyncio import AsyncLogger

   async def performance_benchmark():
       """Benchmark sync vs async logging performance."""
       num_operations = 50  # Reduced for demo

       print("🏁 Starting performance benchmark...")

       # Sync logging benchmark
       sync_log = Logger("sync_benchmark")
       start_time = time.time()

       for i in range(num_operations):
           sync_log.info(f"Sync operation {i}")

       sync_time = time.time() - start_time

       # Async logging benchmark
       async_log = AsyncLogger("async_benchmark")
       start_time = time.time()

       # Create concurrent logging tasks
       tasks = [
           async_log.ainfo(f"Async operation {i}")
           for i in range(num_operations)
       ]
       await asyncio.gather(*tasks)

       async_time = time.time() - start_time

       # Calculate results
       if async_time > 0:
           speedup = sync_time / async_time
           throughput_sync = num_operations / sync_time
           throughput_async = num_operations / async_time

           print(f"\n📊 Performance Results:")
           print(f"Sync logging:   {sync_time:.4f}s  ({throughput_sync:.1f} ops/sec)")
           print(f"Async logging:  {async_time:.4f}s  ({throughput_async:.1f} ops/sec)")
           print(f"Speedup:        {speedup:.1f}x faster with AsyncLogger! 🚀")
       else:
           print("Async logging was too fast to measure! ⚡")

   await performance_benchmark()

🌐 **Web Framework Integration**
--------------------------------

AsyncLogger works seamlessly with async web frameworks:

FastAPI Example
---------------

.. code-block:: python

   from fastapi import FastAPI
   from logeverything.asyncio import AsyncLogger
   import asyncio

   app = FastAPI()
   api_log = AsyncLogger("fastapi_app")

   @app.middleware("http")
   async def logging_middleware(request, call_next):
       await api_log.ainfo("🌐 Request received",
                          method=request.method,
                          url=str(request.url))

       start_time = time.time()
       response = await call_next(request)
       process_time = time.time() - start_time

       await api_log.ainfo("📤 Request completed",
                          status=response.status_code,
                          duration=f"{process_time:.3f}s")

       return response

   @app.get("/users/{user_id}")
   async def get_user(user_id: int):
       await api_log.ainfo("👤 Getting user", user_id=user_id)

       # Simulate async database query
       await asyncio.sleep(0.1)
       user = {"id": user_id, "name": f"User {user_id}"}

       await api_log.ainfo("✅ User retrieved", user=user)
       return user

aiohttp Example
---------------

.. code-block:: python

   from aiohttp import web
   from logeverything.asyncio import AsyncLogger

   async def create_app():
       app = web.Application()
       app['logger'] = AsyncLogger("aiohttp_app")

       async def hello_handler(request):
           log = request.app['logger']
           name = request.match_info.get('name', 'World')

           await log.ainfo("👋 Handling hello request", name=name)
           return web.json_response({"message": f"Hello, {name}!"})

       app.router.add_get('/hello/{name}', hello_handler)
       return app

📈 **Structured Async Logging**
--------------------------------

Use structured logging with async applications using ``.bind()`` for persistent context:

.. seealso::

   For detailed information about binding behavior, registry management,
   and best practices, see :doc:`binding-registry`

.. executable-code::
   :async:

   from logeverything.asyncio import AsyncLogger
   import asyncio
   import uuid

   async def e_commerce_order_processing():
       """Demonstrate structured async logging in e-commerce."""
       log = AsyncLogger("ecommerce")

       # Generate request context
       request_id = str(uuid.uuid4())[:8]
       user_id = 12345

       # Bind context for all subsequent logs
       order_log = log.bind(request_id=request_id, user_id=user_id)

       async with order_log.context("Order Processing"):
           await order_log.ainfo("🛒 Order processing started",
                                order_id="ORD-001",
                                items_count=3,
                                total_amount=99.99)

           # Inventory check
           async with order_log.context("Inventory Check"):
               await order_log.ainfo("📦 Checking inventory")
               await asyncio.sleep(0.1)  # Simulate inventory check

               await order_log.ainfo("✅ Inventory available",
                                    available_items=3,
                                    reserved_items=3)

           # Payment processing
           async with order_log.context("Payment Processing"):
               await order_log.ainfo("💳 Processing payment",
                                    payment_method="credit_card",
                                    amount=99.99)
               await asyncio.sleep(0.15)  # Simulate payment processing

               await order_log.ainfo("✅ Payment successful",
                                    transaction_id="TXN-12345",
                                    status="approved")

           # Shipping
           async with order_log.context("Shipping"):
               await order_log.ainfo("📦 Creating shipping label")
               await asyncio.sleep(0.05)  # Simulate shipping

               await order_log.ainfo("🚚 Order shipped",
                                    tracking_number="TRACK-67890",
                                    carrier="FastShip",
                                    estimated_delivery="2025-07-01")

           await order_log.ainfo("🎉 Order processing completed",
                                order_status="shipped",
                                processing_time="0.3s")

   await e_commerce_order_processing()

🔧 **Best Practices**
---------------------

Async Logger Configuration
---------------------------

.. code-block:: python

   # High-performance configuration for production
   await async_log.configure(
       level="INFO",
       async_queue_size=50000,     # Large queue for high volume
       async_flush_interval=0.1,   # Frequent flushes
       visual_mode=False,          # Disable visual mode for performance
       handlers=["file", "console"]
   )

   # Development configuration
   await async_log.configure(
       level="DEBUG",
       async_queue_size=1000,      # Smaller queue for development
       visual_mode=True,           # Enable visual enhancements
       use_symbols=True,
       use_colors=True
   )

Resource Management
-------------------

.. code-block:: python

   # Always clean up async resources
   async def proper_cleanup():
       log = AsyncLogger("temp")
       try:
           await log.ainfo("Using async logger")
           # Your async operations here
       finally:
           await log.close()  # Clean up resources

   # Or use async context manager
   async def context_manager_cleanup():
       async with AsyncLogger("temp") as log:
           await log.ainfo("Automatic cleanup")
           # Resources automatically cleaned up

Error Handling
--------------

.. code-block:: python

   @async_log_function
   async def safe_async_operation():
       try:
           # Risky async operation
           await risky_async_call()
       except Exception as e:
           # Exception automatically logged by decorator
           await log.aerror("Recovery action taken")
           # Handle the error appropriately

Performance Monitoring
----------------------

.. code-block:: python

   async def monitor_performance():
       log = AsyncLogger("performance")

       start_time = asyncio.get_event_loop().time()

       # Your async operations
       await your_async_operations()

       duration = asyncio.get_event_loop().time() - start_time

       if duration > 1.0:  # Log slow operations
           await log.awarning("Slow operation detected",
                             duration=f"{duration:.3f}s")

🎯 **Common Patterns**
----------------------

Request Processing
------------------

.. code-block:: python

   async def process_api_request(request_data):
       log = AsyncLogger("api")
       request_id = request_data.get("id")

       # Bind request context
       request_log = log.bind(request_id=request_id)

       async with request_log.context("API Request"):
           await request_log.ainfo("Request received")

           # Process request
           result = await process_request(request_data)

           await request_log.ainfo("Request completed",
                                  status="success")
           return result

Batch Processing
----------------

.. code-block:: python

   async def process_batch(items):
       log = AsyncLogger("batch_processor")

       async with log.context("Batch Processing"):
           await log.ainfo(f"Processing {len(items)} items")

           # Process items concurrently
           tasks = [process_item(item, log) for item in items]
           results = await asyncio.gather(*tasks)

           await log.ainfo("Batch completed",
                          items_processed=len(results))
           return results

Background Tasks
----------------

.. code-block:: python

   async def background_worker():
       log = AsyncLogger("worker")

       while True:
           try:
               await log.ainfo("Worker cycle started")

               # Do background work
               await process_queue()

               await asyncio.sleep(30)  # Wait before next cycle
           except Exception as e:
               await log.aerror("Worker error", error=str(e))
               await asyncio.sleep(60)  # Wait longer on error

API Reference
-------------

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
   log.debug(message, **kwargs)
   log.warning(message, **kwargs)
   log.error(message, **kwargs)
   log.exception(message, **kwargs)

   # Configuration and context
   await log.configure(**options)
   async with log.context(name, **context):
       pass

   # Resource management
   await log.close()

Async Decorators
----------------

.. code-block:: python

   # Smart decorator (automatically detects async)
   @log
   async def my_async_function():
       pass

   # Explicit async decorators
   @async_log_function
   async def async_function():
       pass

   @async_log_class
   class AsyncClass:
       pass

See Also
--------

- :doc:`logger-classes` - Logger and AsyncLogger comparison
- :doc:`decorators` - Async decorator usage
- :doc:`../advanced/performance` - Performance optimization
- :doc:`../advanced/production` - Production deployment guide
