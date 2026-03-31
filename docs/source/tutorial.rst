Tutorial: Building a Complete Application
=========================================

This tutorial will guide you through building a complete application using LogEverything's features, from basic logging to advanced async patterns.

🎯 **What We'll Build**
-----------------------

We'll create a **User Management API** that demonstrates:

- Basic logging with Logger classes
- Smart decorators for automatic function logging
- Async logging for high-performance operations
- Context managers for hierarchical logging
- Error handling and structured logging
- Web application integration

🏗️ **Project Setup**
---------------------

First, let's set up our project structure:

.. code-block:: bash

   mkdir user-management-api
   cd user-management-api
   pip install "logeverything[fastapi]"

Create the basic structure:

.. code-block:: python

   # main.py - Our main application
   # models.py - Data models
   # services.py - Business logic
   # database.py - Database operations

📊 **Step 1: Basic Logging Setup**
-----------------------------------

Let's start with basic logging configuration and multiple loggers:

.. executable-code::

   # config.py - Logging configuration
   from logeverything import Logger

   # Create specialized loggers for different components
   app_log = Logger("user_management")
   db_log = Logger("database")
   api_log = Logger("api")
   auth_log = Logger("authentication")

   # Configure the main application logger
   app_log.configure(
       level="INFO",
       visual_mode=True,
       use_symbols=True,
       use_colors=True,
       profile="development"  # Use development profile
   )

   # Configure database logger for detailed debugging
   db_log.configure(
       level="DEBUG",
       visual_mode=True
   )

   # Configure API logger for request tracking
   api_log.configure(
       level="INFO",
       use_symbols=True
   )

   # Test the loggers
   app_log.info("🚀 User Management API starting up")
   db_log.debug("� Database connection initialized")
   api_log.info("🌐 API endpoints registered")
   auth_log.info("🔐 Authentication system ready")

🏗️ **Step 2: Data Models with Targeted Logging**
-------------------------------------------------

Create data models with smart decorator logger selection:

.. executable-code::

   # models.py - User data models with targeted logging
   from logeverything import Logger
   from logeverything.decorators import log
   from dataclasses import dataclass
   from typing import Optional
   import datetime

   # First, create the named loggers that decorators will use
   user_mgmt_log = Logger("user_management")
   auth_log = Logger("authentication")

   @dataclass
   class User:
       id: int
       username: str
       email: str
       created_at: datetime.datetime
       is_active: bool = True

   @log(using="user_management")  # Use the main app logger
   class UserValidator:
       """Validates user data with targeted logging."""

       def validate_email(self, email: str) -> bool:
           """Validate email format."""
           return "@" in email and "." in email.split("@")[1]

       def validate_username(self, username: str) -> bool:
           """Validate username format."""
           return len(username) >= 3 and username.isalnum()

       def validate_user(self, user_data: dict) -> bool:
           """Validate complete user data."""
           if not self.validate_email(user_data.get("email", "")):
               return False
           if not self.validate_username(user_data.get("username", "")):
               return False
           return True

   # Alternative: method-level logger selection
   class SecurityValidator:
       """Validator with method-specific logger routing."""

       @log(using="authentication")  # Route to auth logger
       def validate_password_strength(self, password: str) -> bool:
           """Validate password strength."""
           return len(password) >= 8 and any(c.isdigit() for c in password)

       @log(using="user_management")  # Route to main logger
       def validate_profile_data(self, profile: dict) -> bool:
           """Validate user profile data."""
           required_fields = ["username", "email"]
           return all(field in profile for field in required_fields)

   # Test the validators
   validator = UserValidator()
   security_validator = SecurityValidator()

   test_data = {"username": "john_doe", "email": "john@example.com"}
   is_valid = validator.validate_user(test_data)
   is_strong = security_validator.validate_password_strength("SecurePass123")
   is_complete = security_validator.validate_profile_data(test_data)

   print(f"User data is valid: {is_valid}")
   print(f"Password is strong: {is_strong}")
   print(f"Profile is complete: {is_complete}")

💾 **Step 3: Database Operations with Targeted Logging**
---------------------------------------------------------

Create database operations with targeted logging and context:

.. executable-code::

   # database.py - Database operations with targeted logging
   from logeverything import Logger
   from logeverything.decorators import log
   import asyncio
   import random

   # Create the required loggers first
   database_logger = Logger("database")
   database_logger.configure(visual_mode=True, use_symbols=True)
   auth_logger = Logger("authentication")
   auth_logger.configure(visual_mode=True, use_symbols=True)

   class UserDatabase:
       def __init__(self):
           self.log = Logger("database")
           self.log.configure(visual_mode=True, use_symbols=True)
           self.users = {}  # Simple in-memory storage
           self.next_id = 1

       @log(using="database")  # Explicitly use database logger
       def create_user(self, user_data: dict) -> int:
           """Create a new user."""
           with self.log.context("User Creation"):
               user_log = self.log.bind(username=user_data["username"])
               user_log.info("📝 Creating new user")

               user_id = self.next_id
               self.next_id += 1

               self.users[user_id] = {
                   "id": user_id,
                   "username": user_data["username"],
                   "email": user_data["email"],
                   "created_at": "2025-06-29T00:00:00",
                   "is_active": True
               }

               user_id_log = self.log.bind(user_id=user_id)
               user_id_log.info("✅ User created successfully")
               return user_id

       @log(using="database")  # Explicitly use database logger
       def get_user(self, user_id: int) -> dict:
           """Retrieve a user by ID."""
           with self.log.context("User Retrieval"):
               lookup_log = self.log.bind(user_id=user_id)
               lookup_log.info("🔍 Looking up user")

               if user_id not in self.users:
                   lookup_log.warning("⚠️  User not found")
                   return None

               user = self.users[user_id]
               user_log = self.log.bind(username=user["username"])
               user_log.info("✅ User found")
               return user

       @log(using="database")  # Explicitly use database logger
       def list_users(self) -> list:
           """List all users."""
           with self.log.context("User Listing"):
               count = len(self.users)
               self.log.info(f"📋 Retrieving {count} users")
               return list(self.users.values())

   # Alternative: Mixed logger routing for different operations
   class AuditableUserDatabase:
       """Database with different loggers for different operations."""

       def __init__(self):
           self.users = {}
           self.next_id = 1

       @log(using="database")  # Use database logger for CRUD
       def create_user(self, user_data: dict) -> int:
           """Create user with database logging."""
           user_id = self.next_id
           self.next_id += 1
           self.users[user_id] = {**user_data, "id": user_id}
           return user_id

       @log(using="authentication")  # Use auth logger for security operations
       def authenticate_user(self, username: str, password: str) -> bool:
           """Authenticate user with security logging."""
           # Simplified authentication for demo
           return len(password) >= 8

   # Test the databases
   db = UserDatabase()
   audit_db = AuditableUserDatabase()

   user_id = db.create_user({"username": "alice", "email": "alice@example.com"})
   user = db.get_user(user_id)
   all_users = db.list_users()

   audit_id = audit_db.create_user({"username": "bob", "email": "bob@example.com"})
   is_authenticated = audit_db.authenticate_user("bob", "SecurePass123")

   print(f"Created user: {user}")
   print(f"Authentication result: {is_authenticated}")

🚀 **Step 4: Async Services for Performance**
----------------------------------------------

Create high-performance async services:

.. executable-code::
   :async:

   # services.py - Async business logic
   import asyncio
   from logeverything.asyncio import AsyncLogger
   from logeverything.decorators import log

   # Simple mock database for this example
   class UserDatabase:
       def __init__(self):
           self.users = {}
           self.next_id = 1

       def create_user(self, user_data):
           user_id = self.next_id
           self.next_id += 1
           self.users[user_id] = {**user_data, "id": user_id}
           return user_id

   class UserService:
       def __init__(self):
           self.log = AsyncLogger("user_service")
           self.database = UserDatabase()  # From previous step

       @log  # Smart decorator works with async functions
       async def process_user_registration(self, user_data: dict) -> dict:
           """Process user registration with async logging."""
           async with self.log.context("User Registration"):
               user_log = self.log.bind(username=user_data["username"])
               user_log.info("🔄 Processing registration")

               # Simulate validation (async)
               await self._validate_user_async(user_data)

               # Simulate email verification (async)
               await self._send_verification_email(user_data["email"])

               # Create user in database (sync call)
               user_id = self.database.create_user(user_data)

               # Simulate user profile setup (async)
               profile = await self._setup_user_profile(user_id)

               result_log = self.log.bind(user_id=user_id)
               result_log.info("✅ Registration completed")
               return {"user_id": user_id, "profile": profile}

       async def _validate_user_async(self, user_data: dict):
           """Async user validation."""
           self.log.info("🔍 Validating user data")
           await asyncio.sleep(0.1)  # Simulate async validation
           self.log.info("✅ User data is valid")

       async def _send_verification_email(self, email: str):
           """Simulate sending verification email."""
           email_log = self.log.bind(email=email)
           email_log.info("📧 Sending verification email")
           await asyncio.sleep(0.2)  # Simulate email service call
           self.log.info("✅ Verification email sent")

       async def _setup_user_profile(self, user_id: int) -> dict:
           """Setup user profile."""
           profile_log = self.log.bind(user_id=user_id)
           profile_log.info("👤 Setting up user profile")
           await asyncio.sleep(0.1)  # Simulate profile creation

           profile = {"user_id": user_id, "preferences": {}, "settings": {}}
           self.log.info("✅ Profile setup completed")
           return profile

       @log
       async def batch_process_users(self, user_list: list) -> list:
           """Process multiple users concurrently."""
           async with self.log.context("Batch Processing"):
               self.log.info(f"🔄 Processing {len(user_list)} users")

               # Process all users concurrently (6.8x faster with AsyncLogger)
               tasks = [self.process_user_registration(user) for user in user_list]
               results = await asyncio.gather(*tasks)

               count_log = self.log.bind(count=len(results))
               count_log.info("✅ Batch processing completed")
               return results

   # Test the async service
   async def test_service():
       service = UserService()

       # Single user registration
       user_data = {"username": "bob", "email": "bob@example.com"}
       result = await service.process_user_registration(user_data)

       # Batch processing
       batch_users = [
           {"username": "charlie", "email": "charlie@example.com"},
           {"username": "diana", "email": "diana@example.com"}
       ]
       batch_results = await service.batch_process_users(batch_users)

       print(f"Single user result: {result}")
       print(f"Batch results: {len(batch_results)} users processed")

   await test_service()

🌐 **Step 5: Web API with FastAPI Integration**
------------------------------------------------

Create a web API with integrated logging:

.. executable-code::
   :async:

   # main.py - FastAPI-style API logging simulation
   import time
   import asyncio
   from logeverything import Logger
   from logeverything.decorators import log

   # Mock classes for dependencies (since we can't run FastAPI here)
   class MockRequest:
       def __init__(self, method, url, client_host):
           self.method = method
           self.url = url
           self.client = type('obj', (object,), {'host': client_host})

   class MockResponse:
       def __init__(self, status_code):
           self.status_code = status_code

   # Reuse our previous classes
   class UserDatabase:
       def __init__(self):
           self.users = {}
           self.next_id = 1

       def create_user(self, user_data):
           user_id = self.next_id
           self.next_id += 1
           self.users[user_id] = {**user_data, "id": user_id}
           return user_id

       def get_user(self, user_id):
           return self.users.get(user_id)

   class UserService:
       def __init__(self):
           self.database = UserDatabase()

       async def process_user_registration(self, user_data):
           user_id = self.database.create_user(user_data)
           return {"user_id": user_id, "profile": {"preferences": {}}}

   # Initialize API logging
   api_log = Logger("api")
   api_log.configure(
       level="INFO",
       visual_mode=False,  # Structured logs for production
       handlers=["console"]
   )

   # Simulate request middleware logging
   async def log_request(request):
       """Simulate FastAPI middleware logging."""
       start_time = time.time()

       # Log incoming request
       request_log = api_log.bind(
           method=request.method,
           url=str(request.url),
           client=request.client.host
       )
       request_log.info("🌐 Request received")

       # Simulate processing
       await asyncio.sleep(0.1)
       response = MockResponse(200)

       # Log response
       process_time = time.time() - start_time
       response_log = api_log.bind(
           status_code=response.status_code,
           process_time=f"{process_time:.3f}s"
       )
       response_log.info("📤 Request completed")

       return response

   # Simulate API endpoints
   @log
   async def create_user_endpoint(user_data: dict):
       """Simulate POST /users/ endpoint."""
       try:
           service = UserService()
           result = await service.process_user_registration(user_data)

           success_log = api_log.bind(user_id=result["user_id"])
           success_log.info("✅ User created via API")
           return result
       except Exception as e:
           error_log = api_log.bind(error=str(e))
           error_log.error("❌ User creation failed")
           raise e

   @log
   async def get_user_endpoint(user_id: int):
       """Simulate GET /users/{user_id} endpoint."""
       db = UserDatabase()
       db.create_user({"username": "test_user", "email": "test@example.com"})  # Add test user

       user = db.get_user(user_id)
       if not user:
           not_found_log = api_log.bind(user_id=user_id)
           not_found_log.warning("🔍 User not found via API")
           raise Exception("User not found")
       return user

   # Test the API simulation
   async def test_api():
       # Simulate incoming requests
       create_request = MockRequest("POST", "/users/", "192.168.1.100")
       get_request = MockRequest("GET", "/users/1", "192.168.1.100")

       # Test user creation
       await log_request(create_request)
       user_data = {"username": "alice", "email": "alice@example.com"}
       result = await create_user_endpoint(user_data)
       print(f"Created user: {result}")

       # Test user retrieval
       await log_request(get_request)
       user = await get_user_endpoint(1)
       print(f"Retrieved user: {user}")

   await test_api()

🛡️ **Step 6: Error Handling and Monitoring**
----------------------------------------------

Add comprehensive error handling:

.. executable-code::

   # monitoring.py - Error handling and monitoring
   from logeverything import Logger
   from logeverything.decorators import log
   import traceback

   class ErrorHandler:
       def __init__(self):
           self.log = Logger("error_handler")
           self.log.configure(visual_mode=True, use_symbols=True)

       @log
       def handle_validation_error(self, error: Exception, context: dict):
           """Handle validation errors."""
           with self.log.context("Validation Error"):
               error_log = self.log.bind(
                   error_type=type(error).__name__,
                   error_message=str(error),
                   **context
               )
               error_log.error("❌ Validation failed")

       @log
       def handle_database_error(self, error: Exception, operation: str):
           """Handle database errors."""
           with self.log.context("Database Error"):
               db_error_log = self.log.bind(
                   operation=operation,
                   error_type=type(error).__name__,
                   error_message=str(error)
               )
               db_error_log.error("💾 Database operation failed")

               # Log full traceback for debugging
               traceback_log = self.log.bind(traceback=traceback.format_exc())
               traceback_log.debug("🔍 Full traceback")

       @log
       def monitor_performance(self, operation: str, duration: float, **metrics):
           """Monitor performance metrics."""
           with self.log.context("Performance Monitoring"):
               perf_log = self.log.bind(
                   operation=operation,
                   duration=f"{duration:.3f}s",
                   **metrics
               )

               if duration > 1.0:  # Slow operation warning
                   perf_log.warning("🐌 Slow operation detected")
               else:
                   perf_log.info("⚡ Operation completed")

   # Test error handling
   error_handler = ErrorHandler()

   # Simulate different types of errors
   try:
       raise ValueError("Invalid email format")
   except ValueError as e:
       error_handler.handle_validation_error(e, {"field": "email", "value": "invalid-email"})

   # Monitor performance
   error_handler.monitor_performance("user_creation", 0.5, user_count=1)
   error_handler.monitor_performance("batch_processing", 2.1, user_count=100)

📊 **Step 7: Putting It All Together**
---------------------------------------

Create a complete application that demonstrates all features:

.. executable-code::
   :async:

   # Complete application demo
   import asyncio
   import traceback
   from logeverything import Logger
   from logeverything.asyncio import AsyncLogger
   from logeverything.decorators import log

   # Required classes from previous steps
   class UserDatabase:
       def __init__(self):
           self.users = {}
           self.next_id = 1

       def create_user(self, user_data):
           user_id = self.next_id
           self.next_id += 1
           self.users[user_id] = {**user_data, "id": user_id}
           return user_id

       def get_user(self, user_id):
           return self.users.get(user_id)

   class UserService:
       def __init__(self):
           self.log = AsyncLogger("user_service")
           self.database = UserDatabase()

       async def process_user_registration(self, user_data):
           user_log = self.log.bind(username=user_data["username"])
           user_log.info("🔄 Processing registration")

           # Simple validation
           if len(user_data["username"]) < 2:
               raise ValueError("Username too short")

           await asyncio.sleep(0.1)  # Simulate async processing
           user_id = self.database.create_user(user_data)

           result_log = self.log.bind(user_id=user_id)
           result_log.info("✅ Registration completed")
           return {"user_id": user_id, "profile": {"preferences": {}}}

       async def batch_process_users(self, user_list):
           async with self.log.context("Batch Processing"):
               self.log.info(f"🔄 Processing {len(user_list)} users")

               tasks = [self.process_user_registration(user) for user in user_list]
               results = await asyncio.gather(*tasks)

               count_log = self.log.bind(count=len(results))
               count_log.info("✅ Batch processing completed")
               return results

   class ErrorHandler:
       def __init__(self):
           self.log = Logger("error_handler")
           self.log.configure(visual_mode=True, use_symbols=True)

       @log
       def handle_validation_error(self, error: Exception, context: dict):
           """Handle validation errors."""
           with self.log.context("Validation Error"):
               error_log = self.log.bind(
                   error_type=type(error).__name__,
                   error_message=str(error),
                   **context
               )
               error_log.error("❌ Validation failed")

       @log
       def monitor_performance(self, operation: str, duration: float, **metrics):
           """Monitor performance metrics."""
           with self.log.context("Performance Monitoring"):
               perf_log = self.log.bind(
                   operation=operation,
                   duration=f"{duration:.3f}s",
                   **metrics
               )

               if duration > 1.0:  # Slow operation warning
                   perf_log.warning("🐌 Slow operation detected")
               else:
                   perf_log.info("⚡ Operation completed")

   async def run_complete_demo():
       """Run a complete demonstration of the User Management API."""

       # Initialize main application logger
       main_log = Logger("user_management_demo")
       main_log.configure(
           visual_mode=True,
           use_symbols=True,
           use_colors=True
       )

       with main_log.context("Application Demo"):
           main_log.info("🚀 Starting User Management API Demo")

           # Initialize services
           service = UserService()
           error_handler = ErrorHandler()

           # Demo 1: Single user registration
           with main_log.context("Demo 1: Single User"):
               user_data = {"username": "demo_user", "email": "demo@example.com"}
               result = await service.process_user_registration(user_data)
               success_log = main_log.bind(user_id=result["user_id"])
               success_log.info("✅ Single user demo completed")

           # Demo 2: Batch processing
           with main_log.context("Demo 2: Batch Processing"):
               batch_users = [
                   {"username": f"user_{i}", "email": f"user{i}@example.com"}
                   for i in range(3)
               ]
               start_time = asyncio.get_event_loop().time()
               batch_results = await service.batch_process_users(batch_users)
               end_time = asyncio.get_event_loop().time()

               duration = end_time - start_time
               error_handler.monitor_performance(
                   "batch_user_processing",
                   duration,
                   user_count=len(batch_users)
               )

           # Demo 3: Error handling
           with main_log.context("Demo 3: Error Handling"):
               try:
                   invalid_user = {"username": "x", "email": "invalid"}
                   await service.process_user_registration(invalid_user)
               except Exception as e:
                   error_handler.handle_validation_error(
                       e,
                       {"username": "x", "email": "invalid"}
                   )

           main_log.info("🎉 Application demo completed successfully")

   # Run the complete demo
   await run_complete_demo()

🎯 **Summary: What You've Learned**
------------------------------------

In this tutorial, you've built a complete User Management API and learned:

**✅ Core Concepts:**
   - Logger classes for different contexts
   - Smart decorators for automatic logging
   - AsyncLogger for high-performance async operations
   - Context managers for hierarchical logging

**✅ Advanced Features:**
   - Structured logging with additional fields
   - Error handling and performance monitoring
   - Web framework integration
   - Production-ready configuration

**✅ Best Practices:**
   - Environment-specific configurations
   - Proper async logging patterns
   - Error handling strategies
   - Performance monitoring

🚀 **Next Steps**
-----------------

Now that you understand the fundamentals, explore these advanced topics:

1. **Performance Optimization**: :doc:`advanced/performance`
2. **Production Deployment**: :doc:`advanced/production`
3. **Print Capture**: :doc:`user-guide/print-capture`
4. **Profiles**: :doc:`user-guide/profiles`

**Complete Code**

You can find the complete tutorial code in our examples repository:
https://github.com/logeverything/logeverything/tree/master/examples/tutorial
