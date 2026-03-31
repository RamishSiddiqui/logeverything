Logger Binding and Registry Management
======================================

LogEverything provides powerful binding capabilities that allow you to create contextual loggers with additional structured data. This guide explains how binding works, registry management, and best practices for memory-safe logging.

🔗 **Understanding Logger Binding**
-----------------------------------

Logger binding follows the **Loguru-style** pattern where bound loggers share the same name and underlying logger instance, but add contextual information to all log records.

**Key Concepts:**

- **Base Logger**: The original logger instance that's registered in the global registry
- **Bound Logger**: A new logger instance that shares the same name but adds context
- **Registry**: The global store of logger instances for decorator and system use
- **Additive Context**: Each bind operation adds new context while preserving existing context

Basic Binding Example
---------------------

.. executable-code::

   from logeverything import Logger

   # Create a base logger (automatically registered)
   log = Logger("user_service")
   log.info("Service started")  # Basic log

   # Create a bound logger with user context
   user_log = log.bind(user_id=12345, session_id="abc123")
   user_log.info("User logged in")  # Includes user_id and session_id

   # Create another bound logger with additional context
   request_log = user_log.bind(request_id="req-789", endpoint="/api/users")
   request_log.info("Processing request")  # Includes all context: user_id, session_id, request_id, endpoint

   # Original logger is unchanged
   log.info("Service status check")  # Still basic log without extra context

Registry Behavior
-----------------

**Important Registry Rules:**

1. **Only base loggers are registered** in the global registry
2. **Bound loggers are NOT registered** - they exist independently
3. **Bound loggers share the same name** as their base logger
4. **Deleting a bound logger does NOT affect the base logger** or registry

.. executable-code::

   from logeverything import Logger
   from logeverything.core import get_active_loggers

   # Base logger gets registered
   base_log = Logger("payment_service")
   print(f"Active loggers: {list(get_active_loggers().keys())}")  # ['payment_service']

   # Bound loggers are NOT registered
   payment_log = base_log.bind(transaction_id="tx-123")
   order_log = payment_log.bind(order_id="ord-456")

   print(f"Active loggers: {list(get_active_loggers().keys())}")  # Still ['payment_service']
   print(f"Base logger name: {base_log.name}")      # payment_service
   print(f"Bound logger name: {payment_log.name}")  # payment_service (same name!)
   print(f"Order logger name: {order_log.name}")    # payment_service (same name!)

   # All loggers can log, but only base affects registry
   base_log.info("Base logger message")
   payment_log.info("Payment transaction started")
   order_log.info("Order processing payment")

Memory Management
-----------------

LogEverything automatically manages memory for bound loggers:

.. executable-code::

   from logeverything import Logger
   import gc

   def create_bound_loggers():
       """Create bound loggers that will go out of scope."""
       base_log = Logger("memory_test")

       # Create many bound loggers
       for i in range(100):
           bound_log = base_log.bind(iteration=i, timestamp=f"2024-01-{i:02d}")
           bound_log.info(f"Processing iteration {i}")

       # bound_log instances will be garbage collected when function exits
       return base_log

   # Base logger remains in registry
   base_logger = create_bound_loggers()

   # Force garbage collection
   gc.collect()

   # Base logger still works and is registered
   base_logger.info("All bound loggers cleaned up, base logger remains")

   from logeverything.core import get_active_loggers
   print(f"Registry still contains: {list(get_active_loggers().keys())}")

Async Logger Binding
--------------------

AsyncLogger follows the same binding principles as the synchronous Logger:

.. executable-code::
   :async:

   from logeverything.asyncio import AsyncLogger
   import asyncio

   async def async_binding_demo():
       # Base async logger (registered)
       log = AsyncLogger("async_service")
       await log.ainfo("Async service started")

       # Bound async logger (not registered)
       user_log = log.bind(user_id=67890, session_type="async")
       await user_log.ainfo("Async user session started")

       # Chained binding
       request_log = user_log.bind(request_id="async-req-123")
       await request_log.ainfo("Async request processing")

       # All share the same name but have different contexts
       print(f"Base name: {log.name}")          # async_service
       print(f"User log name: {user_log.name}") # async_service
       print(f"Request log name: {request_log.name}") # async_service

   await async_binding_demo()

Best Practices
--------------

**1. Use Binding for Structured Logging**

.. executable-code::

   from logeverything import Logger

   log = Logger("api_server")

   # Good: Create request-scoped logger
   def handle_request(request_id, user_id):
       request_log = log.bind(request_id=request_id, user_id=user_id)

       request_log.info("Request started")
       # ... process request ...
       request_log.info("Request completed")

   # Simulate multiple requests
   handle_request("req-001", 123)
   handle_request("req-002", 456)

**2. Bind Early, Use Throughout**

.. executable-code::

   from logeverything import Logger

   class UserService:
       def __init__(self):
           self.log = Logger("user_service")

       def login_user(self, user_id, session_id):
           # Create user-scoped logger early
           user_log = self.log.bind(user_id=user_id, session_id=session_id)

           user_log.info("Login attempt")

           if self._validate_credentials(user_log):
               user_log.info("Login successful")
               return self._create_session(user_log)
           else:
               user_log.warning("Login failed")
               return None

       def _validate_credentials(self, user_log):
           user_log.debug("Validating credentials")
           return True  # Simplified

       def _create_session(self, user_log):
           user_log.debug("Creating user session")
           return "session_token"

   # Usage
   service = UserService()
   service.login_user(user_id=789, session_id="sess-xyz")

**3. Don't Worry About Cleanup**

.. executable-code::

   from logeverything import Logger

   # ✅ Good: Let bound loggers be garbage collected naturally
   def process_batch(items):
       log = Logger("batch_processor")

       for item in items:
           # Create item-scoped logger
           item_log = log.bind(item_id=item["id"], item_type=item["type"])
           item_log.info("Processing item")

           # item_log will be cleaned up automatically when loop iteration ends

   # ❌ Don't do this: Manual cleanup is unnecessary
   def process_batch_manual_cleanup(items):
       log = Logger("batch_processor")
       bound_loggers = []

       for item in items:
           item_log = log.bind(item_id=item["id"])
           bound_loggers.append(item_log)  # Keeping references unnecessarily
           item_log.info("Processing item")

       # Manual cleanup is not needed
       del bound_loggers

   # Test both approaches
   test_items = [{"id": 1, "type": "A"}, {"id": 2, "type": "B"}]
   process_batch(test_items)

Context vs Binding
------------------

Understand the difference between context managers and binding:

.. executable-code::

   from logeverything import Logger

   log = Logger("comparison_demo")
   log.configure(visual_mode=True, use_symbols=True)

   # Context managers: Hierarchical, temporary, visual indentation
   with log.context("Data Processing"):
       log.info("🚀 Starting data processing")

       with log.context("Validation"):
           log.info("✅ Data validation passed")

       log.info("📊 Processing completed")

   print("\\n" + "="*50 + "\\n")

   # Binding: Persistent context, structured data, same indentation
   batch_log = log.bind(batch_id="batch-123", source="api")
   batch_log.info("📦 Batch processing started")

   item_log = batch_log.bind(item_count=150)
   item_log.info("📋 Items loaded for processing")

   validation_log = item_log.bind(validation_rule="schema_v2")
   validation_log.info("🔍 Running validation")
   validation_log.info("✅ Validation successful")

   # You can combine both approaches
   with batch_log.context("Final Steps"):
       completion_log = batch_log.bind(processed_items=150, failed_items=0)
       completion_log.info("🎉 Batch processing completed successfully")

Advanced Binding Patterns
-------------------------

**Contextual Decorators with Binding**

.. executable-code::

   from logeverything import Logger, log_function

   # Base logger for service
   service_log = Logger("order_service")

   @log_function(using="order_service")
   def process_order(order_id, user_id):
       # Get the logger from the decorator context and bind it
       from logeverything.core import get_logger

       # Create order-scoped logger
       order_log = service_log.bind(order_id=order_id, user_id=user_id)

       order_log.info("Order processing started")

       # Simulate processing
       order_log.info("Inventory checked")
       order_log.info("Payment processed")
       order_log.info("Order fulfillment initiated")

       return {"status": "completed", "order_id": order_id}

   # The decorator will log function entry/exit,
   # while our bound logger provides detailed context
   result = process_order("ord-789", 12345)

**Thread-Safe Binding**

.. executable-code::

   from logeverything import Logger
   import threading
   import time

   log = Logger("threaded_service")

   def worker_thread(worker_id, tasks):
       # Each thread gets its own bound logger
       worker_log = log.bind(worker_id=worker_id, thread_name=threading.current_thread().name)

       worker_log.info("Worker started")

       for task_id in tasks:
           # Further bind for each task
           task_log = worker_log.bind(task_id=task_id)
           task_log.info("Processing task")
           time.sleep(0.1)  # Simulate work
           task_log.info("Task completed")

       worker_log.info("Worker finished")

   # Start multiple threads
   threads = []
   for i in range(3):
       tasks = [f"task-{i}-{j}" for j in range(2)]
       t = threading.Thread(target=worker_thread, args=(f"worker-{i}", tasks))
       threads.append(t)
       t.start()

   # Wait for completion
   for t in threads:
       t.join()

   log.info("All workers completed")

Registry Inspection
-------------------

You can inspect the logger registry for debugging:

.. executable-code::

   from logeverything import Logger
   from logeverything.core import get_active_loggers

   # Create several base loggers
   auth_log = Logger("auth_service")
   user_log = Logger("user_service")
   order_log = Logger("order_service")

   # Create bound loggers
   admin_log = auth_log.bind(role="admin")
   guest_log = auth_log.bind(role="guest")
   vip_user_log = user_log.bind(tier="vip")

   # Check registry - only base loggers appear
   active_loggers = get_active_loggers()
   print("Registered loggers:")
   for name, logger in active_loggers.items():
       print(f"  {name}: {logger}")

   print(f"\\nTotal registered: {len(active_loggers)}")
   print(f"Expected: 3 (auth_service, user_service, order_service)")

   # Bound loggers work but aren't registered
   admin_log.info("Admin action performed")
   vip_user_log.info("VIP user activity")

Migration from Other Libraries
------------------------------

If migrating from other logging libraries, here's how LogEverything's binding compares:

**From Python's logging with extra**

.. code-block:: python

   # Old way with Python logging
   import logging
   logger = logging.getLogger("app")
   logger.info("User action", extra={"user_id": 123, "action": "login"})

   # LogEverything way
   from logeverything import Logger
   log = Logger("app")
   user_log = log.bind(user_id=123)
   user_log.info("User action", action="login")  # Cleaner and more reusable

**From Loguru**

.. code-block:: python

   # Loguru
   from loguru import logger
   user_logger = logger.bind(user_id=123)
   user_logger.info("User action")

   # LogEverything (similar pattern!)
   from logeverything import Logger
   log = Logger("app")
   user_log = log.bind(user_id=123)
   user_log.info("User action")

**From structlog**

.. code-block:: python

   # structlog
   import structlog
   logger = structlog.get_logger()
   user_logger = logger.bind(user_id=123)
   user_logger.info("User action")

   # LogEverything
   from logeverything import Logger
   log = Logger("app")
   user_log = log.bind(user_id=123)
   user_log.info("User action")

Summary
-------

**Key Takeaways:**

✅ **Use binding for structured, contextual logging**
✅ **Bound loggers share names but add context**
✅ **Only base loggers are registered in the global registry**
✅ **Memory management is automatic - no manual cleanup needed**
✅ **Binding works the same for both Logger and AsyncLogger**
✅ **Combine binding with context managers for powerful logging patterns**

**Registry Safety:**
- Base loggers: Registered and managed by the system
- Bound loggers: Independent, automatically cleaned up
- No risk of registry pollution or memory leaks
- Thread-safe and async-safe operations

This binding system provides the structured logging benefits of libraries like Loguru and structlog while maintaining LogEverything's performance advantages and visual formatting capabilities.
