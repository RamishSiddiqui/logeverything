# Web Framework Integration Examples

This directory contains examples showing how to integrate LogEverything with popular web frameworks.

## FastAPI Examples

### Basic FastAPI Integration (`fastapi_example.py`)

A comprehensive example demonstrating LogEverything integration with FastAPI, featuring:

- **Structured Logging**: Request-scoped logging with bound context
- **Context Managers**: Hierarchical logging for different operation phases
- **Error Handling**: Proper logging of validation errors and exceptions
- **Visual Symbols**: Enhanced readability with hierarchical symbols
- **Nested Contexts**: Database operations and response preparation tracking

#### Requirements

```bash
pip install fastapi uvicorn logeverything
```

#### Running the Example

```bash
# Start the development server
uvicorn fastapi_example:app --reload

# Or run directly
python fastapi_example.py
```

Then visit:
- `http://localhost:8000/` - Root endpoint
- `http://localhost:8000/users/123` - Get user example
- `http://localhost:8000/users/123/posts` - Get user posts with nested contexts
- `http://localhost:8000/users/404` - Error handling example

#### Sample Output

When you visit `http://localhost:8000/users/123`, you'll see output like:

```
[INFO] 2024-01-15 14:30:22 | api | API request received | endpoint="/users" user_id=123
[DEBUG] 2024-01-15 14:30:22 | api | ┌─► Database Lookup
[DEBUG] 2024-01-15 14:30:22 | api | │   Querying user database | endpoint="/users" user_id=123
[INFO] 2024-01-15 14:30:22 | api | │   User found successfully | endpoint="/users" user_id=123
[INFO] 2024-01-15 14:30:22 | api | ┌─► Response Preparation
[DEBUG] 2024-01-15 14:30:22 | api | │   Preparing response data | endpoint="/users" user_id=123
[DEBUG] 2024-01-15 14:30:22 | api | │   Added metadata to response | endpoint="/users" user_id=123
[INFO] 2024-01-15 14:30:22 | api | Returning user data | endpoint="/users" user_id=123 user_count=1 response_size=156
```

### Other FastAPI Examples

- `fastapi_integration.py` - Basic integration patterns
- `fastapi_integration_example.py` - Additional integration techniques

## Flask Examples

- `flask_integration_contexts.py` - Flask integration with context managers

## Django Examples

- `django_integration.py` - Django framework integration

## Key Features Demonstrated

### 1. Request-Scoped Logging
```python
request_log = log.bind(endpoint="/users", user_id=user_id)
request_log.info("API request received")
```

### 2. Context Managers for Operations
```python
with request_log.context("Database Lookup"):
    request_log.debug("Querying user database")
    # Database operations here
    request_log.success("User found successfully")
```

### 3. Structured Data Logging
```python
request_log.bind(user_count=1, response_size=len(str(user_data))).info("Returning user data")
```

### 4. Error Handling
```python
if user_id <= 0:
    request_log.bind(user_id=user_id).error("Invalid user ID provided")
    raise HTTPException(status_code=400, detail="User ID must be positive")
```

## Configuration Options

All examples support LogEverything's configuration options:

```python
log = Logger("api",
            use_symbols=True,     # Enable hierarchical symbols
            visual_mode=True,     # Enhanced visual formatting
            use_colors=True,      # Colored output
            log_level="DEBUG")    # Set logging level
```

## Best Practices

1. **Use Bound Loggers**: Create request-scoped loggers with `.bind()`
2. **Context Managers**: Group related operations for better visualization
3. **Structured Data**: Include relevant metadata in log messages
4. **Appropriate Levels**: Use DEBUG for detailed operations, INFO for important events
5. **Error Context**: Always log errors with relevant context data

## Integration Tips

- Use middleware for automatic request/response logging
- Bind request IDs or user context to loggers
- Leverage async logging for high-throughput applications
- Configure log levels based on environment (DEBUG in dev, INFO in prod)
