# Context Managers

This directory contains examples demonstrating LogEverything's powerful context manager features for automatic logging, resource management, and hierarchical logging contexts.

## Examples in this category:

### 1. **advanced_context_managers_example.py** ⭐
- **Comprehensive context manager guide**
- Basic log contexts for operation grouping
- Performance monitoring with automatic timing
- Error handling with exception catching/logging
- Nested contexts for complex workflows
- Custom context managers with resource cleanup
- Transaction-like patterns and concurrent contexts
- **Best complete reference for context managers**

### 2. **context_managers_comprehensive.py**
- Complete overview of all context manager types
- Real-world usage patterns
- Integration with LogEverything features

### 3. **context_managers_example.py**
- Basic context manager introduction
- Simple usage patterns
- Getting started with contexts

### 4. **fastapi_context_managers.py**
- FastAPI-specific context patterns
- Request/response context management
- Async context handling

### 5. **django_context_managers.py**
- Django framework integration
- View-level context management
- Database transaction contexts

### 6. **sqlalchemy_context_managers.py**
- Database session management
- Transaction contexts with logging
- Connection pool monitoring

### 7. **pytorch_context_managers.py**
- PyTorch model training contexts
- GPU resource management
- Training loop logging

### 8. **tensorflow_context_managers.py**
- TensorFlow model contexts
- Session and graph management
- Training and inference logging

## Key Concepts Covered:

### Basic Context Management
- **log_context**: Group related operations with automatic start/end logging
- **performance_context**: Automatic timing and performance monitoring
- **error_context**: Exception handling and error logging
- **Nested contexts**: Hierarchical operation organization

### Advanced Patterns
- **Custom context managers**: Resource management with logging
- **Async contexts**: Async resource handling (`__aenter__`/`__aexit__`)
- **Transaction patterns**: Database-like transaction logging
- **Concurrent contexts**: Multiple contexts running simultaneously

### Resource Management
- **Database connections**: Automatic connection management
- **File operations**: File handling with cleanup logging
- **Network resources**: API connections and cleanup
- **GPU/Hardware**: Resource allocation and monitoring

### Framework Integration
- **Web frameworks**: Request/response lifecycle logging
- **ML frameworks**: Training and inference contexts
- **Database ORMs**: Session and transaction management
- **Cloud services**: Resource provisioning and cleanup

## Quick Start - Context Managers:

```python
from logeverything import Logger
from logeverything.contexts import log_context, performance_context, error_context

logger = Logger("context_app")

# Basic operation grouping
with log_context("Processing user data", logger=logger):
    logger.info("Fetching user from database")
    logger.info("Validating user permissions")
    logger.info("Processing complete")

# Automatic performance monitoring
with performance_context("Database operation", logger=logger):
    # This will automatically log execution time
    time.sleep(0.1)  # Simulated work

# Error handling with logging
with error_context("Risky operation", logger=logger, reraise=False):
    logger.info("Starting risky operation")
    raise ValueError("Something went wrong!")  # Logged but not re-raised

# Nested contexts for complex workflows
with log_context("User registration", logger=logger):
    with performance_context("Input validation", logger=logger):
        # Validation logic
        pass

    with error_context("Database creation", logger=logger):
        # Database operations
        pass

    with log_context("Email notification", logger=logger):
        # Email sending
        pass
```

## Advanced Custom Context Manager:

```python
from logeverything import Logger
import contextlib

class DatabaseConnection:
    """Custom context manager with comprehensive logging."""

    def __init__(self, db_name):
        self.db_name = db_name
        self.logger = Logger(f"db.{db_name}")
        self.connection = None

    def __enter__(self):
        self.logger.info(f"Connecting to database: {self.db_name}")
        # Simulate connection
        self.connection = f"connection_to_{self.db_name}"
        self.logger.info(f"Connected to {self.db_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(f"Database error: {exc_val}")

        self.logger.info(f"Closing connection to {self.db_name}")
        self.connection = None
        return False  # Don't suppress exceptions

# Usage
with DatabaseConnection("users_db") as db:
    # Database operations with automatic logging
    pass
```

## Async Context Managers:

```python
import asyncio
from logeverything import AsyncLogger

class AsyncDatabaseConnection:
    """Async context manager for database connections."""

    def __init__(self, db_name):
        self.db_name = db_name
        self.logger = AsyncLogger(f"async_db.{db_name}")

    async def __aenter__(self):
        await self.logger.info(f"Async connecting to {self.db_name}")
        await asyncio.sleep(0.1)  # Simulate async connection
        await self.logger.info(f"Async connected to {self.db_name}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.logger.error(f"Async database error: {exc_val}")
        await self.logger.info(f"Async closing connection to {self.db_name}")

# Usage
async def main():
    async with AsyncDatabaseConnection("async_users_db") as db:
        # Async database operations
        pass

asyncio.run(main())
```

## Framework-Specific Patterns:

### FastAPI Request Context
```python
from fastapi import FastAPI, Request
from logeverything import AsyncLogger
from logeverything.contexts import log_context

app = FastAPI()

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    logger = AsyncLogger("fastapi")

    async with log_context(f"{request.method} {request.url.path}", logger=logger):
        response = await call_next(request)
        await logger.info(f"Response: {response.status_code}")
        return response
```

### Django View Context
```python
from django.http import JsonResponse
from logeverything import Logger
from logeverything.contexts import performance_context

def user_view(request):
    logger = Logger("django.views")

    with performance_context("User view processing", logger=logger):
        # View logic here
        return JsonResponse({"status": "success"})
```

### ML Training Context
```python
import torch
from logeverything import Logger
from logeverything.contexts import log_context, performance_context

def train_model():
    logger = Logger("ml.training")

    with log_context("Model training session", logger=logger):
        with performance_context("Data loading", logger=logger):
            # Load training data
            pass

        for epoch in range(10):
            with performance_context(f"Epoch {epoch+1}", logger=logger):
                # Training loop
                pass
```

## Recommended Learning Path:

1. **Start with**: `context_managers_example.py` - Basic concepts
2. **Comprehensive**: `advanced_context_managers_example.py` - All patterns
3. **Framework-specific**: Choose examples based on your tech stack
4. **Custom patterns**: Implement your own context managers

## Benefits of Context Managers:

### ✅ Automatic Logging
- **Start/end logging**: Automatic operation boundaries
- **Performance timing**: Built-in execution time measurement
- **Error handling**: Exception logging and management
- **Resource cleanup**: Guaranteed cleanup with logging

### ✅ Code Organization
- **Operation grouping**: Logical operation boundaries
- **Nested workflows**: Hierarchical process representation
- **Consistent patterns**: Standardized logging approaches
- **Readability**: Clear operation scope visualization

### ✅ Production Benefits
- **Debugging**: Clear operation tracing
- **Performance monitoring**: Automatic timing collection
- **Error tracking**: Comprehensive exception logging
- **Audit trails**: Complete operation history

## Next Steps:

After mastering context managers:
- **05_web_frameworks/** - Apply contexts in web applications
- **06_data_science/** - Use contexts in ML/data pipelines
- **08_advanced/** - Production context management patterns
