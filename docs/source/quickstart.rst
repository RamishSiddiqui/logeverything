Quick Start Guide
=================

This guide will get you up and running with LogEverything in 5 minutes.

🏃‍♂️ **Zero Configuration Start**
----------------------------------

LogEverything works immediately with zero configuration:

.. executable-code::

   from logeverything import Logger

   # Create a logger - auto-detects your environment
   log = Logger("my_app")

   # Start logging immediately
   log.info("Application started")
   log.warning("This is a warning")
   log.error("Something went wrong")
   log.debug("Debug information")

**What happened?**
   - LogEverything auto-detected your environment (script/web/notebook)
   - Applied optimal defaults for your context
   - Provided beautiful, readable output

⚡ **Smart Decorators**
-----------------------

Add automatic function logging with a single decorator:

.. executable-code::

   from logeverything.decorators import log

   @log
   def calculate_total(items, tax_rate=0.1):
       """Calculate total with tax."""
       subtotal = sum(items)
       tax = subtotal * tax_rate
       return subtotal + tax

   # Function execution is automatically logged
   total = calculate_total([10.99, 5.99, 15.99], tax_rate=0.08)
   print(f"Total: ${total:.2f}")

**What the decorator does:**
   - Logs function entry with arguments
   - Logs execution time
   - Logs return value
   - Handles exceptions automatically
   - Automatically finds the best available logger

🎯 **Targeted Logging with Specific Loggers**
----------------------------------------------

Use the ``using`` parameter to target specific loggers:

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log

   # Create specialized loggers
   api_logger = Logger("API", level="INFO")
   db_logger = Logger("Database", level="DEBUG")

   @log(using="API")  # Use the API logger
   def fetch_user_data(user_id):
       """Fetch user data from API."""
       return {"id": user_id, "name": f"User {user_id}"}

   @log(using="Database")  # Use the Database logger
   def save_user_data(user_data):
       """Save user data to database."""
       return f"Saved user {user_data['id']}"

   # Each function uses its specified logger
   user = fetch_user_data(123)
   result = save_user_data(user)
   print(f"Operation completed: {result}")

**Benefits of explicit logger selection:**
   - Route different operations to appropriate loggers
   - Control log levels per component
   - Better organization and filtering
   - Clear separation of concerns

🚀 **Async Applications**
--------------------------

For async applications, use AsyncLogger for 6.8x better performance:

.. executable-code::
   :async:

   import asyncio
   from logeverything.asyncio import AsyncLogger

   async def fetch_user_data(user_id):
       """Simulate fetching user data."""
       log = AsyncLogger("user_service")

       user_log = log.bind(user_id=user_id)
       user_log.info("Fetching user data")
       await asyncio.sleep(0.1)  # Simulate async operation

       user_data = {"id": user_id, "name": f"User {user_id}"}
       user_log.info("User data retrieved")
       return user_data

   # Process multiple users concurrently
   users = await asyncio.gather(
       fetch_user_data(1),
       fetch_user_data(2),
       fetch_user_data(3)
   )

   print(f"Retrieved {len(users)} users")

🧠 **Intelligent Type Casting**
--------------------------------

LogEverything automatically handles sync/async logger and function mismatches:

.. executable-code::
   :async:

   import asyncio
   from logeverything import Logger  # Sync logger
   from logeverything.decorators import log

   # Create a sync logger
   sync_logger = Logger("mixed_app")

   @log(using="mixed_app")  # Sync logger with async function - automatically handled!
   async def async_process(data):
       """Async function using sync logger - works seamlessly."""
       await asyncio.sleep(0.1)
       return f"processed_{data}"

   @log(using="mixed_app")  # Same logger works with sync functions too
   def sync_validate(result):
       """Sync function using the same logger."""
       return len(result) > 5

   # Both functions work with the same logger regardless of sync/async nature
   result = await async_process("data")
   is_valid = sync_validate(result)
   print(f"Result: {result}, Valid: {is_valid}")

**What happened?**
   - LogEverything detected the sync logger with async function mismatch
   - Automatically created an async-compatible logger with same configuration
   - Both sync and async functions work seamlessly with intelligent casting
   - Zero configuration required - works transparently

🎨 **Visual Enhancement**
-------------------------

Enable beautiful visual formatting:

.. executable-code::

   from logeverything import Logger

   # Enable visual mode for beautiful output
   log = Logger("visual_demo")
   log.configure(
       visual_mode=True,
       use_symbols=True,
       use_colors=True
   )

   log.info("✨ Visual mode enabled")
   log.warning("⚠️  This is a warning")
   log.error("❌ Something went wrong")
   log.debug("🔍 Debug information")

📊 **Context Managers**
------------------------

Use context managers for hierarchical logging:

.. executable-code::

   from logeverything import Logger

   log = Logger("data_processor")
   log.configure(visual_mode=True, use_symbols=True)

   # Context manager for hierarchical logging
   with log.context("Data Processing Pipeline"):
       log.info("🚀 Starting pipeline")

       with log.context("Data Loading"):
           log.info("📁 Loading CSV files")
           log.info("✅ Loaded 1,000 records")

       with log.context("Data Validation"):
           log.info("🔍 Validating data integrity")
           log.warning("⚠️  Found 5 invalid records")
           log.info("🧹 Cleaned invalid data")

       with log.context("Data Processing"):
           log.info("⚙️  Applying transformations")
           log.info("📊 Generating statistics")
           log.info("✅ Processing completed")

   log.info("🎉 Pipeline finished successfully")

🔧 **Configuration Profiles**
------------------------------

Use pre-configured profiles for different environments:

.. executable-code::

   from logeverything import Logger

   # Development profile - detailed logging
   dev_log = Logger("dev_app")
   dev_log.configure(profile="development")
   dev_log.info("Development mode logging")

   # Production profile - optimized performance
   prod_log = Logger("prod_app")
   prod_log.configure(profile="production")
   prod_log.info("Production mode logging")

📦 **Structured Logging**
--------------------------

Add structured data to your logs:

.. executable-code::

   from logeverything import Logger

   log = Logger("ecommerce")

   # Structured logging with bound context
   user_log = log.bind(
       user_id=12345,
       username="john_doe",
       ip_address="192.168.1.100",
       session_id="abc123"
   )
   user_log.info("User login successful")

   # Additional context binding
   session_log = log.bind(user_id=12345, session_id="abc123")
   product_log = session_log.bind(product_id=789, category="electronics")
   product_log.info("Product viewed")

   cart_log = session_log.bind(product_id=789, quantity=2)
   cart_log.info("Item added to cart")

🛡️ **Error Handling**
-----------------------

Automatic exception logging:

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log

   logger = Logger("error_demo")

   @log
   def divide_numbers(a, b):
       """Divide two numbers with automatic error logging."""
       return a / b

   # This will automatically log the exception
   try:
       result = divide_numbers(10, 0)
   except ZeroDivisionError:
       logger.info("Exception was automatically logged by decorator")

🌐 **Web Applications**
------------------------

Perfect for web frameworks:

.. executable-code::

   # FastAPI Example
   from fastapi import FastAPI
   from logeverything import Logger

   app = FastAPI()
   log = Logger("api")

   @app.get("/users/{user_id}")
   async def get_user(user_id: int):
       request_log = log.bind(endpoint="/users", user_id=user_id)
       request_log.info("API request received")

       # Simulate database lookup
       with request_log.context("Database Lookup"):
           request_log.debug("Querying user database")
           # Simulated user data
           user_data = {"user_id": user_id, "name": "John Doe", "email": "john@example.com"}
           request_log.info("User found successfully")

       request_log.bind(user_count=1).info("Returning user data")
       return user_data

   # Demonstrate the logging by calling the function
   import asyncio
   result = asyncio.run(get_user(123))
   print(f"API returned: {result}")

⚙️ **Next Steps**
------------------

Now that you've seen the basics, explore more advanced features:

1. **📚 User Guide**: Dive deeper into logger classes, decorators, and async logging
2. **🎨 Visual Formatting**: Learn about themes, colors, and custom formatting
3. **⚡ Performance**: Optimize for high-throughput applications
4. **🌐 Web Integration**: Integrate with FastAPI, Django, and Flask
5. **🔧 Configuration**: Master profiles, handlers, and custom setups

**Common Patterns:**

.. code-block:: python

   # Simple application logging
   from logeverything import Logger
   log = Logger("my_app")

   # Async application logging
   from logeverything.asyncio import AsyncLogger
   log = AsyncLogger("my_async_app")

   # Function decoration
   from logeverything.decorators import log
   @log
   def my_function(): pass

   # Context management
   with log.context("Operation"):
       # code here

📖 **Learn More**
------------------

- :doc:`user-guide/logger-classes` - Master Logger and AsyncLogger
- :doc:`user-guide/decorators` - Advanced decorator usage
- :doc:`user-guide/async-logging` - High-performance async patterns
- :doc:`advanced/performance` - Performance optimization
- :doc:`api/core` - Complete API reference
