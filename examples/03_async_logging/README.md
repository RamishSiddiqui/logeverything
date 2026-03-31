# Async Logging

This directory contains examples demonstrating LogEverything's high-performance async logging capabilities.

## Examples in this category:

### 1. **high_performance_async_example.py** ⭐
- **Complete async logging guide**
- Performance comparison (sync vs async) - up to 6.8x faster!
- Concurrent logging from multiple coroutines
- Async function decorators and error handling
- Batched logging for high throughput
- Async context managers
- **Best comprehensive async logging reference**

### 2. **async_web_app_example.py** ⭐
- **Real-world web application simulation**
- Request/response middleware logging
- Background task processing with queues
- Application metrics and monitoring
- Structured logging with extra fields
- Concurrent request processing
- **Perfect for web application async patterns**

### 3. **logger_comparison.py**
- Direct comparison between `Logger` and `AsyncLogger`
- Performance differences and use cases
- When to use sync vs async logging
- Migration patterns

### 4. **async_logger_example.py**
- Basic `AsyncLogger` usage and patterns
- Async logging fundamentals
- Simple async operations

### 5. **async_context_demo.py**
- Async context managers with logging
- Resource management in async environments
- Async database connections and operations

### 6. **async_context_explanation.py**
- Detailed explanation of async context concepts
- Best practices for async context management
- Common patterns and pitfalls

### 7. **async_context_test.py**
- Testing async logging functionality
- Async testing patterns
- Validation of async logging behavior

## Key Concepts Covered:

### Performance Benefits
- **6.8x faster** than traditional sync logging
- **Non-blocking operations**: Doesn't slow down your application
- **Concurrent processing**: Multiple log operations simultaneously
- **Batched operations**: High-throughput logging for data-intensive apps

### Async Patterns
- **AsyncLogger**: Drop-in replacement for standard Logger
- **Async decorators**: `@log` works seamlessly with async functions
- **Concurrent logging**: Multiple coroutines logging simultaneously
- **Background tasks**: Queue-based processing for heavy logging

### Web Application Integration
- **Middleware logging**: Request/response tracking
- **Dependency injection**: Request-specific loggers
- **Background workers**: Async task processing
- **Performance monitoring**: Real-time metrics and alerting

### Context Management
- **Async context managers**: Resource cleanup in async environments
- **Database connections**: Proper async resource management
- **Error handling**: Exception logging in async contexts

## Performance Comparison:

```python
# Sync logging (traditional)
logger = Logger("sync_app")
for i in range(1000):
    logger.info(f"Log message {i}")  # Blocks on each call

# Async logging (LogEverything)
async_logger = AsyncLogger("async_app")
tasks = []
for i in range(1000):
    task = async_logger.info(f"Log message {i}")  # Non-blocking
    tasks.append(task)
await asyncio.gather(*tasks)  # 6.8x faster!
```

## Recommended Learning Path:

1. **Start here**: `logger_comparison.py` - Understand sync vs async
2. **Core concepts**: `high_performance_async_example.py` - Master async patterns
3. **Real-world**: `async_web_app_example.py` - See practical applications
4. **Specialized**: Other examples for specific use cases

## Quick Start - Async Logging:

```python
import asyncio
from logeverything import AsyncLogger

async def main():
    # Create async logger
    log = AsyncLogger("async_app")

    # Async logging (non-blocking)
    await log.info("Application started")
    await log.debug("Debug information")
    await log.warning("Warning message")

    # Concurrent logging
    tasks = [
        log.info(f"Processing item {i}")
        for i in range(100)
    ]
    await asyncio.gather(*tasks)  # All logged concurrently!

# Run async application
asyncio.run(main())
```

## When to Use Async Logging:

### ✅ Perfect for:
- **Web applications** (FastAPI, aiohttp, Django async views)
- **High-throughput systems** (data processing, API servers)
- **Real-time applications** (chat, gaming, streaming)
- **Microservices** (async communication, event processing)
- **Data pipelines** (ETL, ML training, batch processing)

### ⚠️ Consider sync logging for:
- **Simple scripts** (short-running, low log volume)
- **Legacy applications** (already sync-based)
- **Debug/development** (when simplicity is preferred)

## Performance Tips:

1. **Use batching** for high-volume logging
2. **Avoid blocking operations** in async contexts
3. **Use structured logging** with extra fields
4. **Monitor performance** with built-in metrics
5. **Handle exceptions** properly in async contexts

## Next Steps:

After mastering async logging, explore:
- **04_context_managers/** - Advanced async context patterns
- **05_web_frameworks/** - FastAPI/aiohttp integration
- **08_advanced/** - Production-ready async architectures
