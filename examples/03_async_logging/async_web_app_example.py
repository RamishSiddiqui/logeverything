#!/usr/bin/env python3
"""
Async Web Application Logging Example

This example shows how to integrate LogEverything's async logging
in real-world web applications, including request tracking,
middleware logging, and background task logging.
"""

import asyncio
import sys
import time
import uuid
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from logeverything import AsyncLogger, configure
from logeverything.decorators import log


# Simulate web framework components
class Request:
    """Simulate HTTP request object."""

    def __init__(self, method, path, user_id=None):
        self.method = method
        self.path = path
        self.user_id = user_id
        self.request_id = str(uuid.uuid4())[:8]
        self.timestamp = time.time()


class Response:
    """Simulate HTTP response object."""

    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self.data = data


# Async middleware for request logging
async def logging_middleware(request, handler):
    """Middleware that logs all requests and responses."""
    request_log = AsyncLogger("middleware.requests")

    # Log incoming request
    await request_log.info(
        f"[{request.request_id}] {request.method} {request.path}",
        extra={
            "request_id": request.request_id,
            "method": request.method,
            "path": request.path,
            "user_id": request.user_id,
        },
    )

    start_time = time.time()

    try:
        # Call the actual handler
        response = await handler(request)
        duration = time.time() - start_time

        # Log successful response
        await request_log.info(
            f"[{request.request_id}] Response {response.status_code} in {duration:.3f}s",
            extra={
                "request_id": request.request_id,
                "status_code": response.status_code,
                "duration_ms": duration * 1000,
            },
        )

        return response

    except Exception as e:
        duration = time.time() - start_time

        # Log error response
        await request_log.error(
            f"[{request.request_id}] Error after {duration:.3f}s: {e}",
            extra={
                "request_id": request.request_id,
                "error": str(e),
                "duration_ms": duration * 1000,
            },
        )

        raise


# API handlers with async logging
class UserAPI:
    """User management API with comprehensive logging."""

    def __init__(self):
        self.logger = AsyncLogger("api.users")
        self.users = {}  # Simulate database

    @log
    async def get_users(self, request):
        """Get all users."""
        await asyncio.sleep(0.05)  # Simulate DB query
        return Response(200, list(self.users.values()))

    @log
    async def get_user(self, request, user_id):
        """Get specific user."""
        await self.logger.debug(f"Looking up user {user_id}")
        await asyncio.sleep(0.03)  # Simulate DB query

        if user_id not in self.users:
            await self.logger.warning(f"User {user_id} not found")
            return Response(404, {"error": "User not found"})

        user = self.users[user_id]
        await self.logger.info(f"Retrieved user {user_id}: {user['name']}")
        return Response(200, user)

    @log
    async def create_user(self, request, user_data):
        """Create new user."""
        user_id = str(uuid.uuid4())[:8]

        # Validate user data
        if not user_data.get("name"):
            await self.logger.error("User creation failed: name is required")
            return Response(400, {"error": "Name is required"})

        # Simulate database save
        await asyncio.sleep(0.1)

        user = {
            "id": user_id,
            "name": user_data["name"],
            "email": user_data.get("email", ""),
            "created_at": time.time(),
        }

        self.users[user_id] = user

        await self.logger.info(
            f"Created user {user_id}: {user['name']}",
            extra={"user_id": user_id, "action": "create_user"},
        )

        return Response(201, user)

    @log
    async def delete_user(self, request, user_id):
        """Delete user."""
        if user_id not in self.users:
            await self.logger.warning(f"Attempt to delete non-existent user {user_id}")
            return Response(404, {"error": "User not found"})

        user = self.users.pop(user_id)
        await self.logger.info(
            f"Deleted user {user_id}: {user['name']}",
            extra={"user_id": user_id, "action": "delete_user"},
        )

        return Response(204)


# Background task processing
class TaskProcessor:
    """Background task processor with async logging."""

    def __init__(self):
        self.logger = AsyncLogger("background.tasks")
        self.task_queue = asyncio.Queue()
        self.running = False

    async def add_task(self, task_type, data):
        """Add task to processing queue."""
        task_id = str(uuid.uuid4())[:8]
        task = {"id": task_id, "type": task_type, "data": data, "created_at": time.time()}

        await self.task_queue.put(task)
        await self.logger.info(f"Queued task {task_id}: {task_type}")
        return task_id

    async def process_tasks(self):
        """Process tasks from queue."""
        self.running = True
        await self.logger.info("Task processor started")

        while self.running:
            try:
                # Wait for task with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                await self._process_single_task(task)

            except asyncio.TimeoutError:
                # No tasks available, continue loop
                continue
            except Exception as e:
                await self.logger.error(f"Task processor error: {e}")

    async def _process_single_task(self, task):
        """Process a single task."""
        task_id = task["id"]
        task_type = task["type"]

        await self.logger.info(f"Processing task {task_id}: {task_type}")
        start_time = time.time()

        try:
            # Simulate different task types
            if task_type == "email":
                await self._send_email(task["data"])
            elif task_type == "report":
                await self._generate_report(task["data"])
            elif task_type == "cleanup":
                await self._cleanup_data(task["data"])
            else:
                raise ValueError(f"Unknown task type: {task_type}")

            duration = time.time() - start_time
            await self.logger.info(
                f"Completed task {task_id} in {duration:.3f}s",
                extra={"task_id": task_id, "duration_ms": duration * 1000},
            )

        except Exception as e:
            duration = time.time() - start_time
            await self.logger.error(
                f"Failed task {task_id} after {duration:.3f}s: {e}",
                extra={"task_id": task_id, "error": str(e)},
            )

    async def _send_email(self, email_data):
        """Simulate sending email."""
        await asyncio.sleep(0.2)  # Simulate email sending
        await self.logger.debug(f"Email sent to {email_data.get('to', 'unknown')}")

    async def _generate_report(self, report_data):
        """Simulate generating report."""
        await asyncio.sleep(0.5)  # Simulate report generation
        await self.logger.debug(f"Report generated: {report_data.get('type', 'unknown')}")

    async def _cleanup_data(self, cleanup_data):
        """Simulate data cleanup."""
        await asyncio.sleep(0.1)  # Simulate cleanup
        await self.logger.debug(f"Cleaned up {cleanup_data.get('records', 0)} records")

    async def stop(self):
        """Stop task processor."""
        self.running = False
        await self.logger.info("Task processor stopped")


# Application metrics and monitoring
class MetricsCollector:
    """Collect and log application metrics."""

    def __init__(self):
        self.logger = AsyncLogger("metrics")
        self.request_count = 0
        self.error_count = 0
        self.response_times = []

    async def record_request(self, duration, status_code):
        """Record request metrics."""
        self.request_count += 1
        self.response_times.append(duration)

        if status_code >= 400:
            self.error_count += 1

    async def log_metrics(self):
        """Log current metrics."""
        if not self.response_times:
            return

        avg_response_time = sum(self.response_times) / len(self.response_times)
        error_rate = (self.error_count / self.request_count) * 100

        await self.logger.info(
            f"Metrics: {self.request_count} requests, "
            f"{avg_response_time:.3f}s avg response, "
            f"{error_rate:.1f}% error rate",
            extra={
                "request_count": self.request_count,
                "avg_response_time": avg_response_time,
                "error_rate": error_rate,
            },
        )

        # Reset metrics
        self.request_count = 0
        self.error_count = 0
        self.response_times = []


async def simulate_web_application():
    """Simulate a complete web application with async logging."""
    print("=== Async Web Application Simulation ===\n")

    # Initialize components
    user_api = UserAPI()
    task_processor = TaskProcessor()
    metrics = MetricsCollector()

    # Start background task processor
    processor_task = asyncio.create_task(task_processor.process_tasks())

    # Start metrics logging
    async def periodic_metrics():
        while True:
            await asyncio.sleep(5)  # Log metrics every 5 seconds
            await metrics.log_metrics()

    metrics_task = asyncio.create_task(periodic_metrics())

    print("1. Processing API Requests")
    print("-" * 30)

    # Simulate API requests
    requests = [
        (
            Request("POST", "/users"),
            user_api.create_user,
            {"name": "Alice", "email": "alice@example.com"},
        ),
        (
            Request("POST", "/users"),
            user_api.create_user,
            {"name": "Bob", "email": "bob@example.com"},
        ),
        (Request("GET", "/users"), user_api.get_users, None),
        (Request("GET", "/users/user1"), user_api.get_user, "user1"),  # Will fail
        (
            Request("POST", "/users"),
            user_api.create_user,
            {"email": "charlie@example.com"},
        ),  # Missing name
    ]

    # Process requests concurrently
    async def process_request(req, handler, data):
        try:
            start_time = time.time()
            if data:
                response = await logging_middleware(req, lambda r: handler(r, data))
            else:
                response = await logging_middleware(req, handler)
            duration = time.time() - start_time
            await metrics.record_request(duration, response.status_code)
            return response
        except Exception as e:
            duration = time.time() - start_time
            await metrics.record_request(duration, 500)
            raise

    request_tasks = [process_request(req, handler, data) for req, handler, data in requests]
    responses = await asyncio.gather(*request_tasks, return_exceptions=True)

    print(f"✓ Processed {len(responses)} API requests")

    print("\n2. Background Task Processing")
    print("-" * 35)

    # Add background tasks
    task_ids = []
    task_ids.append(
        await task_processor.add_task("email", {"to": "alice@example.com", "subject": "Welcome"})
    )
    task_ids.append(
        await task_processor.add_task("report", {"type": "user_activity", "period": "daily"})
    )
    task_ids.append(await task_processor.add_task("cleanup", {"records": 150, "older_than": "30d"}))
    task_ids.append(
        await task_processor.add_task("email", {"to": "bob@example.com", "subject": "Welcome"})
    )

    # Let tasks process
    await asyncio.sleep(2)

    print(f"✓ Queued and processed {len(task_ids)} background tasks")

    print("\n3. Application Monitoring")
    print("-" * 30)

    # Force metrics logging
    await metrics.log_metrics()

    # Simulate some load
    print("\nSimulating additional load...")

    # Create more users concurrently
    user_creation_tasks = []
    for i in range(10):
        req = Request("POST", "/users", user_id=f"user_{i}")
        task = process_request(
            req, user_api.create_user, {"name": f"User {i}", "email": f"user{i}@example.com"}
        )
        user_creation_tasks.append(task)

    await asyncio.gather(*user_creation_tasks, return_exceptions=True)

    # Add more background tasks
    for i in range(5):
        await task_processor.add_task("email", {"to": f"user{i}@example.com", "subject": "Update"})

    await asyncio.sleep(1)
    await metrics.log_metrics()

    # Cleanup
    await task_processor.stop()
    processor_task.cancel()
    metrics_task.cancel()

    try:
        await asyncio.gather(processor_task, metrics_task)
    except asyncio.CancelledError:
        pass

    print("\n✓ Web application simulation complete!")


async def main():
    """Main function."""
    print("=== Async Web Application Logging Demo ===\n")

    # Configure async logging
    configure(level="INFO", visual_mode=True, use_symbols=True, format_type="detailed")

    await simulate_web_application()

    print("\nFeatures Demonstrated:")
    print("- Request/response middleware logging")
    print("- API endpoint logging with decorators")
    print("- Background task processing with queues")
    print("- Application metrics and monitoring")
    print("- Error handling and logging")
    print("- Concurrent request processing")
    print("- Structured logging with extra fields")
    print("- Real-world async patterns")


if __name__ == "__main__":
    asyncio.run(main())
