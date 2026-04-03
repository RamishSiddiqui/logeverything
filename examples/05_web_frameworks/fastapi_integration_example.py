#!/usr/bin/env python3
"""
FastAPI Integration Example

This example shows how to integrate LogEverything with FastAPI for
comprehensive web application logging, including request/response logging,
dependency injection, middleware, and background tasks.
"""

import asyncio
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from logeverything import AsyncLogger, configure
from logeverything.decorators import log


# Simulate FastAPI components (in real usage, import from fastapi)
class Request:
    """Simulate FastAPI Request object."""

    def __init__(self, method: str, url: str, headers: dict = None):
        self.method = method
        self.url = url
        self.headers = headers or {}
        self.client = type("Client", (), {"host": "127.0.0.1"})()


class Response:
    """Simulate FastAPI Response object."""

    def __init__(self, content: Any, status_code: int = 200):
        self.content = content
        self.status_code = status_code


# Global logger for FastAPI app
app_logger = AsyncLogger("fastapi_app")


# Dependency injection for request logging
async def get_request_logger(request: Request) -> AsyncLogger:
    """Dependency that provides a request-specific logger."""
    request_id = str(uuid.uuid4())[:8]
    logger = AsyncLogger(f"request.{request_id}")

    # Add request context to all logs
    await logger.info(
        f"Request started: {request.method} {request.url}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host,
        },
    )

    return logger


# Middleware for request/response logging
async def logging_middleware(request: Request, call_next):
    """Middleware that logs all requests and responses."""
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]

    # Add request ID to request state (simulated)
    request.state = type("State", (), {"request_id": request_id})()

    await app_logger.info(
        f"[{request_id}] Incoming request: {request.method} {request.url}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url),
            "user_agent": request.headers.get("user-agent", "unknown"),
        },
    )

    try:
        # Process request
        response = await call_next(request)

        # Log successful response
        duration = time.time() - start_time
        await app_logger.info(
            f"[{request_id}] Response: {response.status_code} in {duration:.3f}s",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            },
        )

        return response

    except Exception as e:
        # Log error response
        duration = time.time() - start_time
        await app_logger.error(
            f"[{request_id}] Request failed in {duration:.3f}s: {str(e)}",
            extra={
                "request_id": request_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "duration_ms": round(duration * 1000, 2),
            },
        )
        raise


# API route handlers with logging
class UserAPI:
    """User management API with comprehensive logging."""

    def __init__(self):
        self.logger = AsyncLogger("api.users")
        self.users: Dict[str, dict] = {}

    @log
    async def create_user(self, user_data: dict, request_logger: AsyncLogger = None) -> Response:
        """Create a new user."""
        logger = request_logger or self.logger

        # Validate input
        if not user_data.get("name"):
            await logger.error("User creation failed: name is required")
            return Response({"error": "Name is required"}, 400)

        if not user_data.get("email"):
            await logger.error("User creation failed: email is required")
            return Response({"error": "Email is required"}, 400)

        # Check if user already exists
        existing_user = next(
            (u for u in self.users.values() if u["email"] == user_data["email"]), None
        )
        if existing_user:
            await logger.warning(f"User creation failed: email {user_data['email']} already exists")
            return Response({"error": "Email already exists"}, 409)

        # Create user
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "name": user_data["name"],
            "email": user_data["email"],
            "created_at": time.time(),
            "active": True,
        }

        # Simulate database save
        await asyncio.sleep(0.1)
        self.users[user_id] = user

        await logger.info(
            f"User created successfully: {user['name']} ({user['email']})",
            extra={"user_id": user_id, "action": "create_user", "user_email": user["email"]},
        )

        return Response(user, 201)

    @log
    async def get_user(self, user_id: str, request_logger: AsyncLogger = None) -> Response:
        """Get user by ID."""
        logger = request_logger or self.logger

        await logger.debug(f"Looking up user: {user_id}")

        # Simulate database lookup
        await asyncio.sleep(0.05)

        if user_id not in self.users:
            await logger.warning(f"User not found: {user_id}")
            return Response({"error": "User not found"}, 404)

        user = self.users[user_id]
        await logger.info(
            f"User retrieved: {user['name']}", extra={"user_id": user_id, "action": "get_user"}
        )

        return Response(user)

    @log
    async def list_users(
        self, skip: int = 0, limit: int = 10, request_logger: AsyncLogger = None
    ) -> Response:
        """List users with pagination."""
        logger = request_logger or self.logger

        await logger.debug(f"Listing users: skip={skip}, limit={limit}")

        # Simulate database query
        await asyncio.sleep(0.08)

        users_list = list(self.users.values())[skip : skip + limit]

        await logger.info(
            f"Retrieved {len(users_list)} users (skip={skip}, limit={limit})",
            extra={"action": "list_users", "count": len(users_list), "skip": skip, "limit": limit},
        )

        return Response(
            {"users": users_list, "total": len(self.users), "skip": skip, "limit": limit}
        )

    @log
    async def update_user(
        self, user_id: str, update_data: dict, request_logger: AsyncLogger = None
    ) -> Response:
        """Update user information."""
        logger = request_logger or self.logger

        if user_id not in self.users:
            await logger.warning(f"Update failed: user not found: {user_id}")
            return Response({"error": "User not found"}, 404)

        user = self.users[user_id]
        old_data = user.copy()

        # Update user data
        user.update(update_data)
        user["updated_at"] = time.time()

        # Log what changed
        changes = []
        for key, new_value in update_data.items():
            old_value = old_data.get(key)
            if old_value != new_value:
                changes.append(f"{key}: {old_value} -> {new_value}")

        await logger.info(
            f"User updated: {user['name']} - Changes: {', '.join(changes)}",
            extra={"user_id": user_id, "action": "update_user", "changes": changes},
        )

        return Response(user)

    @log
    async def delete_user(self, user_id: str, request_logger: AsyncLogger = None) -> Response:
        """Delete user."""
        logger = request_logger or self.logger

        if user_id not in self.users:
            await logger.warning(f"Delete failed: user not found: {user_id}")
            return Response({"error": "User not found"}, 404)

        user = self.users.pop(user_id)

        await logger.info(
            f"User deleted: {user['name']} ({user['email']})",
            extra={"user_id": user_id, "action": "delete_user", "user_email": user["email"]},
        )

        return Response({"message": "User deleted successfully"})


# Background task processing
class BackgroundTasks:
    """Background task processor for FastAPI."""

    def __init__(self):
        self.logger = AsyncLogger("background_tasks")
        self.task_queue = asyncio.Queue()
        self.running = False

    async def add_task(self, task_func, *args, **kwargs):
        """Add a background task."""
        task_id = str(uuid.uuid4())[:8]
        task = {
            "id": task_id,
            "func": task_func,
            "args": args,
            "kwargs": kwargs,
            "created_at": time.time(),
        }

        await self.task_queue.put(task)
        await self.logger.info(f"Background task queued: {task_id}")
        return task_id

    async def process_tasks(self):
        """Process background tasks."""
        self.running = True
        await self.logger.info("Background task processor started")

        while self.running:
            try:
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                await self._execute_task(task)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                await self.logger.error(f"Task processor error: {e}")

    async def _execute_task(self, task):
        """Execute a single background task."""
        task_id = task["id"]
        start_time = time.time()

        try:
            await self.logger.info(f"Executing background task: {task_id}")

            # Execute the task function
            result = await task["func"](*task["args"], **task["kwargs"])

            duration = time.time() - start_time
            await self.logger.info(
                f"Background task completed: {task_id} in {duration:.3f}s",
                extra={"task_id": task_id, "duration_ms": round(duration * 1000, 2)},
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            await self.logger.error(
                f"Background task failed: {task_id} after {duration:.3f}s - {e}",
                extra={"task_id": task_id, "error": str(e)},
            )
            raise

    async def stop(self):
        """Stop the task processor."""
        self.running = False
        await self.logger.info("Background task processor stopped")


# Background task functions
async def send_welcome_email(user_email: str, user_name: str):
    """Send welcome email to new user."""
    email_logger = AsyncLogger("email_service")

    await email_logger.info(f"Sending welcome email to {user_email}")

    # Simulate email sending
    await asyncio.sleep(0.2)

    await email_logger.info(f"Welcome email sent successfully to {user_name}")


async def generate_user_report(user_id: str):
    """Generate user activity report."""
    report_logger = AsyncLogger("report_service")

    await report_logger.info(f"Generating report for user {user_id}")

    # Simulate report generation
    await asyncio.sleep(0.5)

    await report_logger.info(f"User report generated for {user_id}")


# Application setup and simulation
async def simulate_fastapi_app():
    """Simulate a complete FastAPI application."""
    print("=== FastAPI Integration Simulation ===\n")

    # Initialize components
    user_api = UserAPI()
    background_tasks = BackgroundTasks()

    # Start background task processor
    task_processor = asyncio.create_task(background_tasks.process_tasks())

    print("1. User Management API")
    print("-" * 25)

    # Simulate API requests with middleware
    async def simulate_request(method: str, url: str, handler, *args):
        """Simulate a FastAPI request with middleware."""
        request = Request(method, url, {"user-agent": "TestClient/1.0"})

        # Simulate middleware processing
        async def call_next(req):
            return await handler(*args)

        return await logging_middleware(request, call_next)

    # Create users
    user1_response = await simulate_request(
        "POST",
        "/users",
        user_api.create_user,
        {"name": "Alice Johnson", "email": "alice@example.com"},
    )

    user2_response = await simulate_request(
        "POST", "/users", user_api.create_user, {"name": "Bob Smith", "email": "bob@example.com"}
    )

    # Add background tasks for welcome emails
    if user1_response.status_code == 201:
        await background_tasks.add_task(send_welcome_email, "alice@example.com", "Alice Johnson")

    if user2_response.status_code == 201:
        await background_tasks.add_task(send_welcome_email, "bob@example.com", "Bob Smith")

    # List users
    await simulate_request("GET", "/users", user_api.list_users, 0, 10)

    # Get specific user
    user_id = user1_response.content["id"] if user1_response.status_code == 201 else "unknown"
    await simulate_request("GET", f"/users/{user_id}", user_api.get_user, user_id)

    # Update user
    await simulate_request(
        "PUT", f"/users/{user_id}", user_api.update_user, user_id, {"name": "Alice Johnson-Smith"}
    )

    # Generate user report (background task)
    await background_tasks.add_task(generate_user_report, user_id)

    print("\n2. Error Handling")
    print("-" * 20)

    # Simulate errors
    try:
        # Duplicate email
        await simulate_request(
            "POST",
            "/users",
            user_api.create_user,
            {"name": "Charlie", "email": "alice@example.com"},
        )
    except Exception:
        pass

    try:
        # Missing data
        await simulate_request(
            "POST", "/users", user_api.create_user, {"email": "incomplete@example.com"}
        )
    except Exception:
        pass

    try:
        # Non-existent user
        await simulate_request("GET", "/users/nonexistent", user_api.get_user, "nonexistent")
    except Exception:
        pass

    print("\n3. Background Task Processing")
    print("-" * 35)

    # Let background tasks process
    await asyncio.sleep(1.0)

    # Add more background tasks
    for i in range(3):
        await background_tasks.add_task(generate_user_report, f"user_{i}")

    # Wait for tasks to complete
    await asyncio.sleep(2.0)

    # Cleanup
    await background_tasks.stop()
    task_processor.cancel()

    try:
        await task_processor
    except asyncio.CancelledError:
        pass

    print("\n✓ FastAPI integration simulation complete!")


async def main():
    """Main function."""
    print("=== FastAPI Integration Demo ===\n")

    # Configure logging for FastAPI integration
    configure(level="INFO", visual_mode=True, use_symbols=True, format_type="detailed")

    await simulate_fastapi_app()

    print("\nFastAPI Integration Features Demonstrated:")
    print("- Request/response middleware logging")
    print("- Dependency injection for request loggers")
    print("- API endpoint logging with decorators")
    print("- Structured logging with extra fields")
    print("- Background task processing and logging")
    print("- Error handling and logging")
    print("- User management with audit logging")
    print("- Performance monitoring (request duration)")
    print("- Email service integration logging")
    print("- Report generation logging")


if __name__ == "__main__":
    asyncio.run(main())
