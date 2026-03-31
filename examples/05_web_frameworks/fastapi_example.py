"""
FastAPI Example with LogEverything Integration

This example demonstrates how to integrate LogEverything with FastAPI
to provide structured logging for web API endpoints.

Run with: uvicorn fastapi_example:app --reload
Then visit: http://localhost:8000/users/123
"""

import time

from fastapi import FastAPI, HTTPException

from logeverything import Logger

# Initialize FastAPI app and logger
app = FastAPI(title="LogEverything FastAPI Demo")
log = Logger("api", use_symbols=True, visual_mode=True)


@app.on_event("startup")
async def startup_event():
    log.info("🚀 FastAPI application starting up")


@app.on_event("shutdown")
async def shutdown_event():
    log.info("🛑 FastAPI application shutting down")


@app.get("/")
async def root():
    """Root endpoint with basic logging."""
    log.info("Root endpoint accessed")
    return {"message": "Welcome to LogEverything FastAPI Demo"}


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user endpoint with detailed logging."""
    request_log = log.bind(endpoint="/users", user_id=user_id)
    request_log.info("API request received")

    # Validate user ID
    if user_id <= 0:
        request_log.bind(user_id=user_id).error("Invalid user ID provided")
        raise HTTPException(status_code=400, detail="User ID must be positive")

    # Simulate database lookup with context manager
    with request_log.context("Database Lookup"):
        request_log.debug("Querying user database")

        # Simulate some processing time
        time.sleep(0.1)

        # Simulate user lookup logic
        if user_id == 404:
            request_log.warning("User not found in database")
            raise HTTPException(status_code=404, detail="User not found")

        # Simulated user data
        user_data = {
            "user_id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com",
            "status": "active",
        }
        request_log.info("User found successfully")

    # Log additional processing
    with request_log.context("Response Preparation"):
        request_log.debug("Preparing response data")
        # Add some metadata
        user_data["retrieved_at"] = time.time()
        request_log.debug("Added metadata to response")

    request_log.bind(user_count=1, response_size=len(str(user_data))).info("Returning user data")
    return user_data


@app.get("/users/{user_id}/posts")
async def get_user_posts(user_id: int, limit: int = 10):
    """Get user posts with nested context logging."""
    request_log = log.bind(endpoint="/users/posts", user_id=user_id, limit=limit)
    request_log.info("Posts request received")

    with request_log.context("User Validation"):
        request_log.debug("Validating user exists")
        if user_id <= 0:
            request_log.error("Invalid user ID")
            raise HTTPException(status_code=400, detail="Invalid user ID")
        request_log.info("User validation passed")

    with request_log.context("Posts Retrieval"):
        request_log.debug("Fetching user posts from database")

        # Nested context for pagination
        with request_log.context("Pagination Setup"):
            request_log.bind(limit=limit).debug("Setting up pagination")
            if limit > 100:
                limit = 100
                request_log.bind(original_limit=limit).warning("Limit capped at 100")

        # Simulate posts data
        posts = [
            {"id": i, "title": f"Post {i}", "content": f"Content for post {i}"}
            for i in range(1, min(limit + 1, 6))
        ]
        request_log.bind(post_count=len(posts)).info("Posts retrieved successfully")

    request_log.bind(total_posts=len(posts)).info("Returning posts data")
    return {"user_id": user_id, "posts": posts, "total": len(posts)}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with logging."""
    log.bind(path=request.url.path, method=request.method, exception=str(exc)).error(
        "Unhandled exception occurred"
    )
    return {"error": "Internal server error", "path": request.url.path}


if __name__ == "__main__":
    import uvicorn

    log.info("Starting FastAPI development server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
