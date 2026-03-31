Smart Decorators
================

LogEverything's decorator system provides automatic function logging with zero configuration. The **smart decorator** automatically detects what it's decorating and applies appropriate logging behavior, with intelligent logger selection and customizable output.

🎯 **Core Concept**
-------------------

The ``@log`` decorator is a **universal smart decorator** that automatically detects:

- **Functions** vs **Classes** vs **Methods**
- **Sync** vs **Async** functions
- **I/O operations** vs **Regular functions**
- **Available loggers** and selects the most appropriate one
- **Logger types** and casts between sync/async as needed

It then applies the most appropriate logging strategy for optimal performance and usefulness. **In most cases, ``@log`` is the only decorator you need** - it intelligently handles all scenarios.

💡 **Why Use @log Instead of Specific Decorators?**
---------------------------------------------------

The ``@log`` decorator provides **all the functionality** of the specific decorators (``@log_function``, ``@log_class``, ``@log_io``, etc.) with additional intelligence:

- **Universal Application**: Works on functions, classes, async functions, sync functions
- **Intelligent Type Casting**: Automatically handles sync/async logger and function mismatches
- **Smart Detection**: Automatically detects I/O operations, class methods, and function types
- **Simplified API**: One decorator to learn instead of multiple specific ones
- **Future-Proof**: New detection capabilities are automatically available

**Recommendation**: Use ``@log`` for all your logging needs. Use specific decorators only when you need explicit control over the decoration behavior.

🔍 **Smart Logger Selection**
-----------------------------

All decorators now feature **intelligent logger selection** with the ``using`` parameter:

**Automatic Selection (Default):**
   - Searches for existing LogEverything loggers in your application
   - Falls back to creating a standard logger if none found
   - Provides helpful guidance when issues occur

**Explicit Selection:**
   - Use ``using="logger_name"`` to specify a particular logger
   - Clear error messages when the specified logger doesn't exist
   - Suggestions for available alternatives

**Lazy Resolution:**
   - Logger lookup happens at runtime, not import time
   - Allows decorators to work even when loggers are created later

🚀 **Universal Decorator (@log) - Recommended**
-----------------------------------------------

The ``@log`` decorator is your **one-stop solution** for automatic logging with intelligent logger selection and type casting:

Basic Function Decoration
--------------------------

.. executable-code::

   from logeverything.decorators import log

   @log
   def calculate_total(price, tax_rate=0.1):
       """Calculate total price with tax."""
       tax = price * tax_rate
       total = price + tax
       return round(total, 2)

   # Function execution is automatically logged
   result = calculate_total(99.99, 0.08)
   print(f"Total: ${result}")

**What the decorator logged:**
   - Function entry with arguments ``price=99.99, tax_rate=0.08``
   - Execution time in milliseconds
   - Return value ``107.99``

Using Specific Loggers
----------------------

You can specify which logger to use with the ``using`` parameter:

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log

   # Create multiple loggers
   api_logger = Logger("API", level="DEBUG")
   db_logger = Logger("Database", level="INFO")

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

Automatic Logger Detection
--------------------------

When no logger is specified, the decorator automatically finds the best available logger:

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log

   # Create a logger
   main_logger = Logger("MainApp")

   @log  # Automatically finds and uses MainApp logger
   def process_data(data):
       """Process data with automatic logger selection."""
       return [item.upper() for item in data]

   result = process_data(["apple", "banana", "cherry"])
   print(f"Processed: {result}")

Error Handling and Guidance
---------------------------

The decorator provides helpful error messages and suggestions:

.. executable-code::

   from logeverything.decorators import log

   # This will show available loggers if the specified one doesn't exist
   try:
       @log(using="NonExistentLogger")
       def test_function():
           pass

       test_function()
   except Exception as e:
       print(f"Error caught: {e}")
       # The error message includes suggestions for available loggers

Async Function Detection
-------------------------

The smart decorator automatically detects async functions with logger selection:

.. executable-code::
   :async:

   import asyncio
   from logeverything import Logger
   from logeverything.decorators import log

   # Create an async-specific logger
   async_logger = Logger("AsyncApp", level="DEBUG")

   @log(using="AsyncApp")  # Use specific logger for async operations
   async def fetch_user_data(user_id):
       """Fetch user data asynchronously."""
       # Simulate async database call
       await asyncio.sleep(0.1)
       return {"id": user_id, "name": f"User {user_id}", "active": True}

   @log  # Automatically detects async and finds available logger
   async def process_user(user_id):
       """Process user with multiple async operations."""
       user_data = await fetch_user_data(user_id)

       # Simulate processing
       await asyncio.sleep(0.05)
       user_data["processed"] = True

       return user_data

   # Test async function logging
   result = await process_user(123)
   print(f"Processed user: {result}")

Class Decoration
----------------

The smart decorator detects classes and logs all public methods with logger selection:

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log

   # Create a user management logger
   user_logger = Logger("UserManagement", level="INFO")

   @log(using="UserManagement")  # All methods use this logger
   class UserManager:
       """User management with automatic method logging."""

       def __init__(self):
           self.users = {}
           self.next_id = 1

       def create_user(self, username, email):
           """Create a new user."""
           user_id = self.next_id
           self.next_id += 1

           self.users[user_id] = {
               "id": user_id,
               "username": username,
               "email": email,
               "active": True
           }
           return user_id

       def get_user(self, user_id):
           """Get user by ID."""
           return self.users.get(user_id)

       def deactivate_user(self, user_id):
           """Deactivate a user."""
           if user_id in self.users:
               self.users[user_id]["active"] = False
               return True
           return False

   # Alternative: automatic logger detection for classes
   @log  # Automatically finds best available logger
   class ProductManager:
       """Product management with automatic logger selection."""

       def __init__(self):
           self.products = {}

       def add_product(self, name, price):
           """Add a new product."""
           product_id = len(self.products) + 1
           self.products[product_id] = {"name": name, "price": price}
           return product_id

   # All methods are automatically logged with specified loggers
   user_manager = UserManager()
   product_manager = ProductManager()

   user_id = user_manager.create_user("alice", "alice@example.com")
   product_id = product_manager.add_product("Widget", 19.99)

   user = user_manager.get_user(user_id)
   print(f"Created user: {user}")
   print(f"Created product ID: {product_id}")

I/O Operation Detection
-----------------------

The smart decorator detects I/O operations and applies specialized logging:

.. executable-code::

   from logeverything.decorators import log
   import tempfile
   import os

   @log  # Automatically detects I/O operation
   def save_user_data(filename, user_data):
       """Save user data to file."""
       with open(filename, 'w') as f:
           f.write(f"User: {user_data['username']}\nEmail: {user_data['email']}\n")
       return filename

   @log  # Automatically detects I/O operation
   def load_user_data(filename):
       """Load user data from file."""
       with open(filename, 'r') as f:
           lines = f.readlines()

       data = {}
       for line in lines:
           if line.startswith("User: "):
               data['username'] = line.replace("User: ", "").strip()
           elif line.startswith("Email: "):
               data['email'] = line.replace("Email: ", "").strip()

       return data

   # Test I/O logging
   with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
       temp_filename = f.name

   try:
       user_data = {"username": "bob", "email": "bob@example.com"}
       saved_file = save_user_data(temp_filename, user_data)
       loaded_data = load_user_data(temp_filename)
       print(f"Loaded data: {loaded_data}")
   finally:
       os.unlink(temp_filename)

🔧 **Explicit Decorators**
---------------------------

For fine-grained control, use explicit decorators with the ``using`` parameter:

@log_function
-------------

Explicitly log functions with custom options and logger selection:

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log_function

   # Create specific loggers for different purposes
   calc_logger = Logger("Calculator", level="DEBUG")

   @log_function(using="Calculator", level="DEBUG", include_args=True, include_result=True)
   def complex_calculation(x, y, operation="add"):
       """Perform complex calculation with detailed logging."""
       if operation == "add":
           result = x + y
       elif operation == "multiply":
           result = x * y
       elif operation == "power":
           result = x ** y
       else:
           raise ValueError(f"Unsupported operation: {operation}")

       return result

   # Alternative: automatic logger selection with custom options
   @log_function(level="INFO", include_args=True, include_result=False)
   def simple_calculation(a, b):
       """Simple calculation with automatic logger selection."""
       return a + b

   # Test with different operations
   result1 = complex_calculation(5, 3, "add")      # Uses Calculator logger
   result2 = complex_calculation(4, 2, "power")    # Uses Calculator logger
   result3 = simple_calculation(10, 5)             # Uses automatic logger selection

   print(f"Results: {result1}, {result2}, {result3}")

@log_class
-----------

Explicitly log all class methods with logger selection:

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log_class

   # Create a database-specific logger
   db_logger = Logger("Database", level="INFO")

   @log_class(using="Database", level="INFO", include_private=False)
   class DatabaseConnection:
       """Database connection with explicit method logging."""

       def __init__(self, host, port=5432):
           self.host = host
           self.port = port
           self.connected = False
           self._connection_id = None

       def connect(self):
           """Establish database connection."""
           self.connected = True
           self._connection_id = f"{self.host}:{self.port}:12345"
           return self._connection_id

       def execute_query(self, sql, params=None):
           """Execute SQL query."""
           if not self.connected:
               raise RuntimeError("Not connected to database")

           # Simulate query execution
           return {"rows": 42, "sql": sql}

       def disconnect(self):
           """Close database connection."""
           self.connected = False
           self._connection_id = None

       def _internal_method(self):
           """Private method (not logged due to include_private=False)."""
           return "internal"

   # Alternative: automatic logger with class-specific settings
   @log_class(level="DEBUG", include_private=True)
   class CacheManager:
       """Cache manager with automatic logger selection."""

       def __init__(self):
           self.cache = {}

       def get(self, key):
           """Get item from cache."""
           return self.cache.get(key)

       def set(self, key, value):
           """Set item in cache."""
           self.cache[key] = value

   # Test class logging with different loggers
   db = DatabaseConnection("localhost", 5432)        # Uses Database logger
   cache = CacheManager()                            # Uses automatic logger selection

   connection_id = db.connect()
   result = db.execute_query("SELECT * FROM users")
   db.disconnect()

   cache.set("user:123", {"name": "Alice"})
   user_data = cache.get("user:123")

   print(f"Query result: {result}")
   print(f"Cache data: {user_data}")

@log_io
-------

Explicitly log I/O operations with logger selection:

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log_io
   import json
   import tempfile
   import os

   # Create an I/O-specific logger
   io_logger = Logger("FileOps", level="INFO")

   @log_io(using="FileOps", level="INFO", log_args=True)
   def save_config(config_data, filename):
       """Save configuration to JSON file."""
       with open(filename, 'w') as f:
           json.dump(config_data, f, indent=2)
       return os.path.getsize(filename)

   @log_io(using="FileOps", level="INFO", log_args=True)
   def load_config(filename):
       """Load configuration from JSON file."""
       with open(filename, 'r') as f:
           return json.load(f)

   # Alternative: automatic logger selection for I/O
   @log_io(level="DEBUG", log_args=False)  # Uses automatic logger selection
   def backup_file(source, destination):
       """Backup file with automatic logging."""
       with open(source, 'r') as src, open(destination, 'w') as dst:
           dst.write(src.read())
       return destination

   # Test I/O logging with different loggers
   with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
       temp_filename = f.name

   try:
       config = {"database": {"host": "localhost", "port": 5432}, "debug": True}
       file_size = save_config(config, temp_filename)        # Uses FileOps logger
       loaded_config = load_config(temp_filename)            # Uses FileOps logger
       print(f"Config loaded: {loaded_config}")
       print(f"File size: {file_size} bytes")
   finally:
       os.unlink(temp_filename)

⚡ **Async-Specific Decorators**
--------------------------------

For async applications, use async-optimized decorators with logger selection:

@async_log_function
-------------------

.. executable-code::
   :async:

   from logeverything import Logger
   from logeverything.asyncio import async_log_function
   import asyncio

   # Create an async-specific logger
   async_logger = Logger("AsyncProcessor", level="INFO")

   @async_log_function(using="AsyncProcessor")
   async def process_batch(items, batch_size=10):
       """Process items in batches asynchronously."""
       results = []

       for i in range(0, len(items), batch_size):
           batch = items[i:i + batch_size]

           # Simulate async processing
           await asyncio.sleep(0.05)
           processed_batch = [item.upper() for item in batch]
           results.extend(processed_batch)

       return results

   # Alternative: automatic logger selection for async functions
   @async_log_function(level="DEBUG", include_args=True)
   async def fetch_data_async(url):
       """Fetch data asynchronously with automatic logger selection."""
       await asyncio.sleep(0.1)  # Simulate network call
       return f"Data from {url}"

   # Test async function logging
   items = ["apple", "banana", "cherry", "date", "elderberry"]
   results = await process_batch(items, batch_size=2)      # Uses AsyncProcessor logger
   data = await fetch_data_async("https://api.example.com") # Uses automatic logger

   print(f"Processed items: {results}")
   print(f"Fetched data: {data}")

@async_log_class
----------------

.. executable-code::
   :async:

   from logeverything import Logger
   from logeverything.asyncio import async_log_class
   import asyncio

   # Create logger for async data processing
   async_data_logger = Logger("AsyncDataProcessor", level="DEBUG")

   @async_log_class(using="AsyncDataProcessor")
   class AsyncDataProcessor:
       """Async data processor with automatic method logging."""

       def __init__(self, name):
           self.name = name
           self.processed_count = 0

       async def process_item(self, item):
           """Process a single item."""
           await asyncio.sleep(0.01)  # Simulate async work
           self.processed_count += 1
           return f"processed_{item}"

       async def process_batch(self, items):
           """Process multiple items concurrently."""
           tasks = [self.process_item(item) for item in items]
           results = await asyncio.gather(*tasks)
           return results

       def get_stats(self):
           """Get processing statistics."""
           return {"name": self.name, "processed": self.processed_count}

   # Alternative: automatic logger selection for async classes
   @async_log_class(level="INFO", include_private=False)
   class AsyncCacheManager:
       """Async cache manager with automatic logger selection."""

       def __init__(self):
           self.cache = {}

       async def get_async(self, key):
           """Get item from cache asynchronously."""
           await asyncio.sleep(0.01)  # Simulate async cache lookup
           return self.cache.get(key)

       async def set_async(self, key, value):
           """Set item in cache asynchronously."""
           await asyncio.sleep(0.01)  # Simulate async cache write
           self.cache[key] = value

   # Test async class logging with different loggers
   processor = AsyncDataProcessor("BatchProcessor")         # Uses AsyncDataProcessor logger
   cache_manager = AsyncCacheManager()                      # Uses automatic logger selection

   items = ["item1", "item2", "item3"]
   results = await processor.process_batch(items)
   stats = processor.get_stats()

   await cache_manager.set_async("key1", "value1")
   cached_value = await cache_manager.get_async("key1")

   print(f"Results: {results}")
   print(f"Stats: {stats}")
   print(f"Cached value: {cached_value}")

🎛️ **Decorator Configuration**
-------------------------------

Customize decorator behavior with options and logger selection:

Configuration Options
---------------------

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log_function

   # Create a detailed debugging logger
   debug_logger = Logger("DebugApp", level="DEBUG")

   # Custom configuration options with specific logger
   @log_function(
       using="DebugApp",        # Use specific logger
       level="DEBUG",           # Log level
       include_args=True,       # Log function arguments
       include_result=True,     # Log return value
       include_time=True,       # Log execution time
       include_source=True,     # Log source file and line
       max_arg_length=100      # Truncate long arguments
   )
   def detailed_function(data, config=None):
       """Function with detailed logging configuration."""
       if config is None:
           config = {"mode": "default"}

       processed = f"Processed {len(data)} items with {config['mode']} mode"
       return processed

   # Alternative: automatic logger with custom configuration
   @log_function(
       level="INFO",            # Uses automatic logger selection
       include_args=True,
       include_result=False,
       max_arg_length=50
   )
   def simple_detailed_function(items):
       """Function with automatic logger and custom settings."""
       return f"Processed {len(items)} items"

   # Test detailed logging
   test_data = ["item1", "item2", "item3", "item4", "item5"]
   result1 = detailed_function(test_data, {"mode": "advanced"})  # Uses DebugApp logger
   result2 = simple_detailed_function(test_data)                # Uses automatic logger

   print(f"Results: {result1}, {result2}")

Performance Options
-------------------

.. executable-code::

   from logeverything.decorators import log

   # Performance-optimized logging
   @log(
       level="INFO",           # Higher level = less overhead
       include_args=False,     # Skip argument logging for performance
       include_result=False,   # Skip result logging for performance
       include_time=True       # Keep timing for performance monitoring
   )
   def high_performance_function(data):
       """High-performance function with minimal logging overhead."""
       return sum(x * 2 for x in data)

   # Test performance logging
   large_data = list(range(1000))
   result = high_performance_function(large_data)
   print(f"Sum result: {result}")

🎨 **Advanced Patterns**
------------------------

Method-Level Decoration with Logger Selection
----------------------------------------------

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log

   # Create specialized loggers
   auth_logger = Logger("Authentication", level="INFO")
   api_logger = Logger("APIClient", level="DEBUG")

   class ApiClient:
       """API client with selective method logging."""

       def __init__(self, base_url):
           self.base_url = base_url

       @log(using="Authentication")  # Use Authentication logger
       def authenticate(self, username, password):
           """Authenticate with the API."""
           # Simulate authentication
           token = f"token_{username}_{hash(password) % 10000}"
           return {"token": token, "expires": "2025-12-31"}

       @log(using="APIClient")  # Use APIClient logger
       def make_request(self, endpoint, method="GET", data=None):
           """Make API request."""
           # Simulate API request
           response = {
               "status": 200,
               "endpoint": endpoint,
               "method": method,
               "data": data
           }
           return response

       @log  # Use automatic logger selection
       def get_status(self):
           """Get client status."""
           return {"status": "connected", "base_url": self.base_url}

       def _internal_method(self):
           """Internal method without logging."""
           return "internal data"

   # Test selective method logging with different loggers
   client = ApiClient("https://api.example.com")
   auth_result = client.authenticate("user123", "password")    # Uses Authentication logger
   api_result = client.make_request("/users/123", "GET")       # Uses APIClient logger
   status = client.get_status()                                # Uses automatic logger

   print(f"Auth: {auth_result}")
   print(f"API: {api_result}")
   print(f"Status: {status}")

Multi-Logger Hierarchical Setup
-------------------------------

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log_function, log_class

   # Create hierarchical loggers
   main_logger = Logger("App", level="INFO")
   db_logger = Logger("App.Database", level="DEBUG")  # Child of App
   cache_logger = Logger("App.Cache", level="WARNING")  # Child of App

   @log_function(using="App.Database")
   def database_operation(query):
       """Database operation with specific logger."""
       return f"Executed: {query}"

   @log_function(using="App.Cache")
   def cache_operation(key, value=None):
       """Cache operation with specific logger."""
       if value:
           return f"Set {key} = {value}"
       return f"Get {key}"

   @log_class(using="App")
   class ApplicationService:
       """Main application service using root logger."""

       def process_request(self, request_data):
           """Process a request using multiple subsystems."""
           # Use database
           db_result = database_operation(f"SELECT * FROM users WHERE id = {request_data['user_id']}")

           # Use cache
           cache_result = cache_operation(f"user:{request_data['user_id']}", "cached_data")

           return {"db": db_result, "cache": cache_result}

   # Test hierarchical logging
   service = ApplicationService()
   result = service.process_request({"user_id": 123})
   print(f"Service result: {result}")

Conditional Logging
-------------------

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log_function
   import os

   # Create conditional loggers
   debug_logger = Logger("DebugMode", level="DEBUG")
   prod_logger = Logger("Production", level="WARNING")

   # Conditional logger selection based on environment
   debug_mode = os.getenv("DEBUG", "false").lower() == "true"
   selected_logger = "DebugMode" if debug_mode else "Production"

   @log_function(
       using=selected_logger,
       level="DEBUG" if debug_mode else "INFO",
       include_args=debug_mode,
       include_result=debug_mode
   )
   def environment_aware_function(data):
       """Function that logs differently based on environment."""
       return f"Processed {len(data)} items"

   # Alternative: dynamic logger selection
   @log_function(
       using=lambda: "DebugMode" if debug_mode else "Production",
       level="INFO"
   )
   def dynamic_logger_function(items):
       """Function with dynamic logger selection."""
       return [item.upper() for item in items]

   # Test environment-aware logging
   result1 = environment_aware_function([1, 2, 3, 4, 5])
   result2 = dynamic_logger_function(["a", "b", "c"])

   print(f"Results: {result1}, {result2}")

Logger Selection Strategies
---------------------------

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log

   # Create multiple loggers for different strategies
   Logger("Strategy.FastPath", level="WARNING")
   Logger("Strategy.DetailedPath", level="DEBUG")
   Logger("Strategy.DefaultPath", level="INFO")

   @log(using="Strategy.FastPath")
   def fast_processing(data):
       """Fast processing with minimal logging."""
       return len(data)

   @log(using="Strategy.DetailedPath")
   def detailed_processing(data):
       """Detailed processing with verbose logging."""
       result = []
       for item in data:
           processed = item * 2
           result.append(processed)
       return result

   @log  # Automatic selection - will find Strategy.DefaultPath
   def default_processing(data):
       """Default processing with automatic logger selection."""
       return sum(data)

   # Test different logging strategies
   test_data = [1, 2, 3, 4, 5]

   fast_result = fast_processing(test_data)        # Minimal logging
   detailed_result = detailed_processing(test_data)  # Verbose logging
   default_result = default_processing(test_data)   # Automatic logging

   print(f"Results: {fast_result}, {detailed_result}, {default_result}")

🔍 **Debugging and Troubleshooting**
------------------------------------

Exception Handling
------------------

Decorators automatically handle and log exceptions with logger selection:

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log

   # Create an error-specific logger
   error_logger = Logger("ErrorHandling", level="ERROR")

   @log(using="ErrorHandling")
   def risky_operation(value):
       """Operation that might fail."""
       if value < 0:
           raise ValueError("Value cannot be negative")
       elif value == 0:
           raise ZeroDivisionError("Cannot divide by zero")

       return 100 / value

   @log  # Automatic logger selection for error handling
   def safe_operation(value):
       """Safe operation with automatic error logging."""
       try:
           return risky_operation(value)
       except Exception as e:
           return f"Error: {e}"

   # Test exception handling
   try:
       result1 = risky_operation(10)  # Success - logged to ErrorHandling
       print(f"Success: {result1}")
   except Exception:
       pass

   try:
       result2 = risky_operation(-5)  # ValueError - logged to ErrorHandling
   except ValueError:
       print("ValueError was logged by ErrorHandling logger")

   result3 = safe_operation(0)  # Error handled - logged to automatic logger
   print(f"Safe result: {result3}")

Logger Discovery and Debugging
------------------------------

.. executable-code::

   from logeverything import Logger
   from logeverything.core import get_active_loggers, get_logger
   from logeverything.decorators import log

   # Create multiple loggers for testing
   Logger("MainApp", level="INFO")
   Logger("Database", level="DEBUG")
   Logger("Cache", level="WARNING")

   # Function to demonstrate logger discovery
   @log
   def discover_loggers():
       """Function that will use automatic logger discovery."""
       active = get_active_loggers()
       print(f"Active loggers: {list(active.keys())}")

       # Test finding specific loggers
       main_logger = get_logger("MainApp")
       db_logger = get_logger("Database")
       nonexistent = get_logger("NonExistent")

       return {
           "main": main_logger is not None,
           "db": db_logger is not None,
           "nonexistent": nonexistent is not None
       }

   # Test logger discovery
   result = discover_loggers()
   print(f"Logger discovery result: {result}")

Error Messages and Guidance
---------------------------

.. executable-code::

   from logeverything.decorators import log

   # This will demonstrate helpful error messages
   def test_error_guidance():
       """Test error guidance for missing loggers."""
       try:
           @log(using="NonExistentLogger")
           def failing_function():
               """This function uses a non-existent logger."""
               return "This won't work"

           # This will trigger the error with helpful guidance
           failing_function()

       except Exception as e:
           print(f"Helpful error message: {e}")
           # The error includes suggestions for available loggers

   # Uncomment to test error guidance:
   # test_error_guidance()

Decorator Stacking
------------------

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log
   import functools

   # Create a logger for stacked decorators
   timing_logger = Logger("TimingAnalysis", level="INFO")

   def timing_decorator(func):
       """Custom timing decorator."""
       @functools.wraps(func)
       def wrapper(*args, **kwargs):
           import time
           start = time.time()
           result = func(*args, **kwargs)
           duration = time.time() - start
           print(f"Custom timing: {func.__name__} took {duration:.4f}s")
           return result
       return wrapper

   @log(using="TimingAnalysis")  # LogEverything decorator with specific logger
   @timing_decorator             # Custom decorator
   def multi_decorated_function(n):
       """Function with multiple decorators."""
       # Simulate some work
       total = sum(i * i for i in range(n))
       return total

   @timing_decorator  # Custom decorator first
   @log              # LogEverything decorator with automatic selection
   def reverse_stacked_function(n):
       """Function with reversed decorator stack."""
       return sum(range(n))

   # Test decorator stacking
   result1 = multi_decorated_function(1000)      # Uses TimingAnalysis logger
   result2 = reverse_stacked_function(1000)      # Uses automatic logger selection

   print(f"Results: {result1}, {result2}")

🎯 **Best Practices**
----------------------

Choosing the Right Logger Strategy
----------------------------------

.. code-block:: python

   # Use automatic selection for simple cases
   @log
   def simple_function():
       pass

   # Use explicit logger names for specific purposes
   @log(using="Database")
   def database_function():
       pass

   # Use hierarchical logger names for organization
   @log(using="App.Auth.OAuth")
   def oauth_function():
       pass

   # Use conditional selection for environment-aware logging
   logger_name = "Debug" if DEBUG else "Production"
   @log(using=logger_name)
   def environment_function():
       pass

Choosing the Right Decorator
-----------------------------

.. code-block:: python

   # Use @log for most cases (smart detection with logger selection)
   @log(using="MyLogger")
   def my_function():
       pass

   # Use explicit decorators for specific requirements
   @log_function(using="DebugLogger", level="DEBUG", include_args=True)
   def debug_function():
       pass

   @log_io(using="FileLogger", log_args=True)
   def io_function():
       pass

   # Use async decorators for async functions
   @async_log_function(using="AsyncLogger")
   async def async_function():
       pass

Logger Organization Patterns
----------------------------

.. code-block:: python

   # Module-based organization
   from logeverything import Logger

   # Create loggers for different modules
   Logger("myapp.auth", level="INFO")
   Logger("myapp.database", level="DEBUG")
   Logger("myapp.cache", level="WARNING")

   # Use in decorators
   @log(using="myapp.auth")
   def authenticate():
       pass

   @log(using="myapp.database")
   def db_query():
       pass

   # Feature-based organization
   Logger("UserManagement", level="INFO")
   Logger("PaymentProcessing", level="DEBUG")
   Logger("NotificationService", level="INFO")

Performance Considerations
--------------------------

.. code-block:: python

   # High-performance: minimal logging with specific logger
   @log(using="HighPerf", level="WARNING", include_args=False, include_result=False)
   def high_perf_function():
       pass

   # Development: detailed logging with debug logger
   @log(using="Debug", level="DEBUG", include_args=True, include_result=True)
   def debug_function():
       pass

   # Production: balanced logging with production logger
   @log(using="Production", level="INFO", include_args=False, include_result=False)
   def production_function():
       pass

Security Considerations
-----------------------

.. code-block:: python

   # Avoid logging sensitive data with specific security logger
   @log_function(using="SecurityAudit", include_args=False)  # Don't log passwords
   def authenticate(username, password):
       pass

   # Use custom argument filtering with dedicated logger
   @log_function(using="DataProcessor", max_arg_length=50)  # Truncate long arguments
   def process_sensitive_data(data):
       pass

   # Conditional sensitive data logging
   @log_function(
       using="AuditTrail",
       include_args=not PRODUCTION,  # Only log args in non-production
       include_result=False          # Never log sensitive results
   )
   def handle_payment(payment_data):
       pass

🧠 **Intelligent Type Casting**
-------------------------------

LogEverything features **intelligent type casting** that automatically handles sync/async logger and function mismatches. This ensures seamless compatibility between sync/async loggers and functions without manual configuration.

**Key Features:**

- **Automatic Detection**: Detects sync vs async loggers and functions
- **Smart Conversion**: Converts logger types when needed for compatibility
- **Seamless Operation**: Zero configuration required - works transparently
- **Configuration Preservation**: Maintains logger settings during casting
- **Graceful Fallback**: Falls back safely when casting isn't possible

Sync Logger with Async Functions
---------------------------------

When you have a sync logger but use it with async functions, LogEverything automatically creates an async-compatible logger:

.. seealso::

   📋 **Understanding Shared Logger Creation**

   When mixing sync loggers with async functions, LogEverything creates **shared AsyncLogger** instances with names like ``{original_name}_async_shared``. This happens at function execution time, not decoration time. For detailed information about this behavior, performance implications, auto-detection messages, and best practices, see :doc:`async-sync-best-practices`.

.. executable-code::
   :async:

   import asyncio
   from logeverything import Logger  # Sync logger
   from logeverything.decorators import log

   # Create a sync logger
   sync_logger = Logger("SyncApp", level="DEBUG")

   @log(using="SyncApp")  # Smart decorator handles the conversion
   async def async_data_fetch(user_id):
       """Async function with sync logger - automatically handled."""
       await asyncio.sleep(0.1)  # Simulate async operation
       return {"user_id": user_id, "data": "fetched"}

   @log(using="SyncApp")  # Works seamlessly
   async def async_data_process(data):
       """Another async function using the same sync logger."""
       await asyncio.sleep(0.05)
       return {**data, "processed": True}

   # The decorators automatically cast the sync logger to async-compatible
   result = await async_data_fetch(123)
   final_result = await async_data_process(result)
   print(f"Final result: {final_result}")

Async Logger with Sync Functions
---------------------------------

Similarly, async loggers work seamlessly with sync functions:

.. executable-code::

   from logeverything.asyncio import AsyncLogger  # Async logger
   from logeverything.decorators import log

   # Create an async logger
   async_logger = AsyncLogger("AsyncApp", level="DEBUG")

   @log(using="AsyncApp")  # Smart decorator handles the conversion
   def sync_calculation(x, y):
       """Sync function with async logger - automatically handled."""
       result = x * y + (x ** 2)
       return result

   @log(using="AsyncApp")  # Works seamlessly
   def sync_validation(result):
       """Another sync function using the same async logger."""
       return result > 0 and result < 1000

   # The decorators automatically cast the async logger to sync-compatible
   calc_result = sync_calculation(10, 5)
   is_valid = sync_validation(calc_result)
   print(f"Calculation: {calc_result}, Valid: {is_valid}")

Mixed Usage Patterns
---------------------

You can freely mix sync and async functions with any logger type:

.. executable-code::
   :async:

   import asyncio
   from logeverything import Logger
   from logeverything.decorators import log, log_function, log_class

   # One logger for everything
   app_logger = Logger("MixedApp", level="INFO")

   @log(using="MixedApp")
   def sync_preprocessor(data):
       """Sync preprocessing function."""
       return [item.strip().lower() for item in data]

   @log(using="MixedApp")
   async def async_enricher(items):
       """Async enrichment function."""
       enriched = []
       for item in items:
           await asyncio.sleep(0.01)  # Simulate async enrichment
           enriched.append(f"enriched_{item}")
       return enriched

   @log(using="MixedApp")
   def sync_finalizer(enriched_data):
       """Sync finalization function."""
       return ", ".join(enriched_data)

   # All functions work with the same logger, regardless of sync/async
   raw_data = ["  Apple  ", "  BANANA  ", "  Cherry  "]
   processed = sync_preprocessor(raw_data)
   enriched = await async_enricher(processed)
   final = sync_finalizer(enriched)
   print(f"Pipeline result: {final}")

Explicit Decorator Type Casting
--------------------------------

All specific decorators also support intelligent type casting:

.. executable-code::
   :async:

   import asyncio
   from logeverything import Logger
   from logeverything.decorators import log_function, async_log_function, log_class

   # Create a sync logger
   processor_logger = Logger("DataProcessor", level="DEBUG")

   # Use sync-specific decorator with async function
   @log_function(using="DataProcessor", include_args=True, include_result=True)
   async def async_transform(data):
       """Async function using sync decorator - automatically cast."""
       await asyncio.sleep(0.1)
       return [x.upper() for x in data]

   # Use async-specific decorator with sync function
   @async_log_function(using="DataProcessor", include_args=True)
   def sync_filter(data):
       """Sync function using async decorator - automatically cast."""
       return [x for x in data if len(x) > 3]

   # Both work seamlessly with type casting
   data = ["hello", "world", "python", "async"]
   transformed = await async_transform(data)
   filtered = sync_filter(transformed)
   print(f"Transformed: {transformed}")
   print(f"Filtered: {filtered}")

Class-Level Type Casting
-------------------------

Type casting also works at the class level for mixed method types:

.. executable-code::
   :async:

   import asyncio
   from logeverything.asyncio import AsyncLogger
   from logeverything.decorators import log_class

   # Create an async logger
   service_logger = AsyncLogger("UserService", level="INFO")

   @log_class(using="UserService", include_private=False)
   class UserService:
       """Mixed sync/async class with automatic type casting."""

       def __init__(self):
           self.users = {}
           self.next_id = 1

       def create_user(self, username):
           """Sync method with async logger - automatically cast."""
           user_id = self.next_id
           self.next_id += 1
           self.users[user_id] = {"id": user_id, "username": username}
           return user_id

       async def fetch_user_details(self, user_id):
           """Async method with async logger - works directly."""
           await asyncio.sleep(0.1)  # Simulate async fetch
           base_user = self.users.get(user_id, {})
           return {**base_user, "details": "fetched", "active": True}

       def get_user_count(self):
           """Another sync method - automatically cast."""
           return len(self.users)

   # All methods work seamlessly regardless of sync/async nature
   service = UserService()
   user_id = service.create_user("alice")
   user_details = await service.fetch_user_details(user_id)
   count = service.get_user_count()

   print(f"User details: {user_details}")
   print(f"Total users: {count}")

Performance Considerations
--------------------------

**Efficient Caching**: Type casting is optimized with caching to minimize overhead:

- Logger casting results are cached for reuse
- Type detection happens only once per decorator instance
- Minimal performance impact in production usage

**Lazy Conversion**: Logger conversion happens only when needed:

- No upfront conversion cost
- Conversion occurs at first function call
- Subsequent calls use cached converted logger

**Configuration Preservation**: Original logger settings are maintained:

- Log levels, formatters, and handlers are preserved
- Custom configuration transfers to cast logger
- No loss of logging behavior during casting

Error Handling and Fallbacks
-----------------------------

**Graceful Degradation**: When type casting fails, the system falls back gracefully:

.. executable-code::

   from logeverything import Logger
   from logeverything.decorators import log

   # Create a logger
   robust_logger = Logger("RobustApp", level="INFO")

   @log(using="RobustApp")
   def fallback_example():
       """Function that works even if casting fails."""
       return "This always works - fallback ensures compatibility"

   result = fallback_example()
   print(f"Result: {result}")
   # Even if casting fails, logging continues with appropriate warnings

**Debug Information**: Enable debug logging to see type casting in action:

.. executable-code::

   import logging
   from logeverything import Logger
   from logeverything.decorators import log

   # Enable debug logging to see type casting
   logging.basicConfig(level=logging.DEBUG)

   debug_logger = Logger("DebugApp", level="DEBUG")

   @log(using="DebugApp")
   def debug_function():
       """Function with debug-level type casting visibility."""
       return "Check logs for type casting details"

   result = debug_function()
   # Debug logs will show any type casting operations

Migration from Legacy Code
---------------------------

**Seamless Upgrade**: Existing code works without changes:

- Legacy sync-only code continues to work
- Adding async functions requires no logger changes
- Gradual migration is fully supported

**Backward Compatibility**: All existing decorator patterns remain valid:

- No breaking changes to existing APIs
- Enhanced functionality is opt-in
- Legacy logger configurations are preserved

Best Practices
--------------

**Logger Creation Strategy**:

- Create loggers based on logical application components, not sync/async nature
- Let intelligent type casting handle sync/async compatibility automatically
- Use meaningful logger names that reflect business logic

**Performance Optimization**:

- Reuse loggers across sync/async boundaries for better caching
- Avoid creating unnecessary duplicate loggers for sync/async variants
- Trust the intelligent casting system for optimal performance

**Debugging and Monitoring**:

- Enable debug logging temporarily to understand type casting behavior
- Monitor logger creation and casting in development environments
- Use consistent logger names across mixed sync/async codebases

API Reference
-------------

Smart Decorator
---------------

.. code-block:: python

   @log(using=None, level=None, include_args=None, include_result=None, **options)

**Parameters:**

- ``using`` (str, optional): Name of the logger to use. If None, automatically selects the best available logger.
- ``level`` (str, optional): Log level for this decorator
- ``include_args`` (bool, optional): Whether to log function arguments
- ``include_result`` (bool, optional): Whether to log function return values
- ``**options``: Additional decorator-specific options

**Intelligent Type Casting Features:**

- Automatically detects sync vs async functions and loggers
- Converts logger types when needed for compatibility
- Preserves logger configuration during casting
- Provides graceful fallback when casting fails

Explicit Decorators
-------------------

.. code-block:: python

   @log_function(using=None, level="INFO", include_args=True, include_result=True,
                include_time=True, include_source=True, max_arg_length=300)

   @log_class(using=None, level="INFO", include_private=False, include_special=False)

   @log_io(using=None, level="INFO", log_args=True, log_result=True)

**Common Parameters:**

- ``using`` (str, optional): Logger name for explicit selection with intelligent type casting
- ``level`` (str): Logging level
- Various boolean flags for controlling what gets logged

**Type Casting Support:**

- All explicit decorators support intelligent sync/async type casting
- Sync decorators work seamlessly with async functions and async loggers
- Logger configuration is preserved during automatic type conversion

Async Decorators
----------------

.. code-block:: python

   @async_log_function(using=None, level="INFO", include_args=True, include_result=True)

   @async_log_class(using=None, level="INFO", include_private=False)

**Type Casting Support:**

- Async-specific decorators also support type casting in reverse direction
- Can be used with sync functions and sync loggers
- Automatic conversion ensures compatibility without manual configuration

**Logger Selection Behavior:**

1. **Explicit Selection**: If ``using`` is specified, use that exact logger name with type casting if needed
2. **Automatic Selection**: If ``using`` is None, search for available LogEverything loggers
3. **Type Compatibility**: Automatically cast logger types to match function sync/async nature
4. **Fallback**: If no LogEverything loggers found, create a standard logger proxy
5. **Error Handling**: Clear error messages with suggestions when specified loggers don't exist

.. _structured-hierarchy-fields:

Structured Hierarchy Fields
---------------------------

Every decorated function call automatically injects **structured hierarchy
fields** into log records, enabling downstream consumers (JSON handlers,
dashboards) to reconstruct the call tree without parsing indentation strings.

The fields are:

.. list-table::
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``indent_level``
     - ``int``
     - Current nesting depth (0 = top-level)
   * - ``call_id``
     - ``str``
     - Unique 12-char hex ID for this function call
   * - ``parent_call_id``
     - ``str``
     - ``call_id`` of the enclosing function call (empty at top level)
   * - ``log_type``
     - ``str``
     - ``"call_entry"`` on CALL, ``"call_exit"`` on DONE/ERROR, ``"message"`` for plain logs
   * - ``execution_id``
     - ``str``
     - Thread/task execution context identifier

These fields are automatically promoted to top-level keys when using
:class:`~logeverything.handlers.handlers.JSONHandler`, so JSON log files
contain structured hierarchy data ready for tree-view rendering in the
dashboard.

**Example: Inspecting hierarchy fields on a log record**

.. code-block:: python

   import logging
   from logeverything import Logger
   from logeverything.decorators import log

   # Capture records to inspect hierarchy fields
   class RecordCapture(logging.Handler):
       records = []
       def emit(self, record):
           self.records.append(record)

   app = Logger("hierarchy_demo")
   capture = RecordCapture()
   app._logger.addHandler(capture)

   @log(using="hierarchy_demo")
   def outer():
       @log(using="hierarchy_demo")
       def inner():
           app.info("inside inner")
       inner()

   outer()

   for r in capture.records:
       print(f"[{r.log_type:10}] indent={r.indent_level} "
             f"call_id={r.call_id[:8]}... msg={r.getMessage()[:50]}")

**Example output:**

.. code-block:: text

   [call_entry] indent=0 call_id=a1b2c3d4... msg=-> outer()
   [call_entry] indent=1 call_id=e5f6a7b8... msg=  -> inner()
   [message   ] indent=2 call_id=e5f6a7b8... msg=    inside inner
   [call_exit ] indent=1 call_id=e5f6a7b8... msg=  <- inner (0.12ms)
   [call_exit ] indent=0 call_id=a1b2c3d4... msg=<- outer (0.45ms)

.. seealso::

   :doc:`../api/hierarchy`
      Full API reference for :class:`~logeverything.hierarchy.HierarchyFilter`.

   :doc:`dashboard`
      The monitoring dashboard renders these fields as a collapsible tree view
      on the **Logs** page.


See Also
--------

- :doc:`logger-classes` - Logger and AsyncLogger classes
- :doc:`async-logging` - Advanced async logging patterns
- :doc:`context-managers` - Context manager usage
- :doc:`../advanced/performance` - Performance optimization
- :doc:`../api/hierarchy` - HierarchyFilter API reference
