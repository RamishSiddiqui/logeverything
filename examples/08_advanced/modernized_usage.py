#!/usr/bin/env python3
"""
LogEverything Modernized Usage Patterns
=======================================

This example demonstrates modern Python patterns and best practices
when using LogEverything with contemporary frameworks and libraries.

Features demonstrated:
- Type hints and dataclasses
- Context managers and async/await
- Modern error handling patterns
- Integration with popular libraries
- Performance-conscious logging
"""

import asyncio
import contextlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from logeverything import AsyncLogger, Logger, get_logger
from logeverything.decorators import log

# =============================================================================
# 1. TYPE-ANNOTATED LOGGER SETUP
# =============================================================================

# Modern logger creation with type hints
app_logger: Logger = get_logger("ModernApp")
async_logger: AsyncLogger = AsyncLogger("AsyncModernApp")


@dataclass
class UserData:
    """📊 Modern dataclass with logging integration"""

    name: str
    email: str
    age: int
    preferences: Dict[str, Any]

    def __post_init__(self):
        self.logger = get_logger(f"User_{self.name}")
        self.logger.info(f"✅ Created user profile for {self.name}")


# =============================================================================
# 2. MODERN ASYNC PATTERNS
# =============================================================================


@log(logger=async_logger, include_performance=True)
async def fetch_user_data(user_id: int) -> Optional[UserData]:
    """🔄 Modern async data fetching with error handling"""
    try:
        # Simulate API call
        await asyncio.sleep(0.1)

        if user_id <= 0:
            raise ValueError(f"Invalid user ID: {user_id}")

        # Simulate data return
        return UserData(
            name=f"User_{user_id}",
            email=f"user{user_id}@example.com",
            age=25 + (user_id % 50),
            preferences={"theme": "dark", "notifications": True},
        )

    except ValueError as e:
        async_logger.error(f"❌ Validation error: {e}")
        return None
    except Exception as e:
        async_logger.error(f"❌ Unexpected error: {e}")
        return None


@log(logger=async_logger)
async def process_users_batch(user_ids: List[int]) -> List[UserData]:
    """⚡ Modern batch processing with concurrency"""
    async with async_logger.context("Batch Processing"):
        async_logger.info(f"ℹ️ Processing {len(user_ids)} users concurrently")

        # Modern concurrent processing
        tasks = [fetch_user_data(uid) for uid in user_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        users = [r for r in results if isinstance(r, UserData)]
        async_logger.info(f"✅ Successfully processed {len(users)}/{len(user_ids)} users")

        return users


# =============================================================================
# 3. CONTEXT MANAGER PATTERNS
# =============================================================================


@contextlib.asynccontextmanager
async def database_transaction():
    """💾 Modern async context manager for database operations"""
    async with async_logger.context("Database Transaction"):
        async_logger.info("🔄 Starting transaction")
        try:
            # Simulate database connection
            await asyncio.sleep(0.05)
            yield "db_connection"
            async_logger.info("✅ Transaction committed")
        except Exception as e:
            async_logger.error(f"❌ Transaction rolled back: {e}")
            raise
        finally:
            async_logger.info("🔄 Connection closed")


# =============================================================================
# 4. MODERN ERROR HANDLING AND LOGGING
# =============================================================================


class ModernService:
    """🏢 Modern service class with comprehensive logging"""

    def __init__(self, service_name: str):
        self.name = service_name
        self.logger = get_logger(f"Service_{service_name}")
        self.logger.info(f"🚀 Initialized service: {service_name}")

    @log
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """✅ Modern validation with detailed logging"""
        required_fields = ["name", "email"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            self.logger.warning(f"⚠️ Missing required fields: {missing_fields}")
            return False

        self.logger.info(f"✅ Input validation passed for: {data.get('name')}")
        return True

    @log(include_performance=True)
    async def process_with_retry(self, data: Dict[str, Any], max_retries: int = 3) -> bool:
        """🔄 Modern retry pattern with exponential backoff"""
        for attempt in range(max_retries):
            try:
                async with self.logger.context(f"Attempt {attempt + 1}"):
                    # Simulate processing
                    await asyncio.sleep(0.1)

                    # Simulate occasional failure
                    if attempt == 0 and data.get("name") == "FailFirst":
                        raise ConnectionError("Simulated connection failure")

                    self.logger.info("✅ Processing successful")
                    return True

            except Exception as e:
                wait_time = 2**attempt  # Exponential backoff
                self.logger.warning(f"⚠️ Attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    self.logger.info(f"🔄 Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"❌ All {max_retries} attempts failed")
                    return False


# =============================================================================
# 5. PERFORMANCE-CONSCIOUS LOGGING
# =============================================================================


@log(include_performance=True)
def fibonacci_optimized(n: int, memo: Optional[Dict[int, int]] = None) -> int:
    """📊 Modern memoized fibonacci with performance logging"""
    if memo is None:
        memo = {}

    if n in memo:
        return memo[n]

    if n <= 1:
        return n

    result = fibonacci_optimized(n - 1, memo) + fibonacci_optimized(n - 2, memo)
    memo[n] = result
    return result


@log
async def performance_comparison():
    """📈 Modern performance comparison demonstration"""
    sizes = [3, 5, 10]

    for size in sizes:
        # Time the operation
        start_time = time.perf_counter()
        result = fibonacci_optimized(size)
        end_time = time.perf_counter()

        app_logger.info(
            f"📊 Fibonacci({size}) = {result}, took {end_time - start_time:.6f} seconds"
        )


# =============================================================================
# 6. INTEGRATION WITH MODERN PATTERNS
# =============================================================================


async def modern_pipeline_example():
    """🔄 Modern data processing pipeline"""
    async with async_logger.context("Modern Pipeline"):
        # Step 1: Fetch data
        user_ids = [1, 2, 3, 4, 5]
        users = await process_users_batch(user_ids)

        # Step 2: Process with service
        service = ModernService("UserProcessor")

        async with database_transaction() as db:
            for user in users:
                user_data = {"name": user.name, "email": user.email, "age": user.age}

                if service.validate_input(user_data):
                    success = await service.process_with_retry(user_data)
                    if success:
                        user.logger.info("✅ User processing completed")


# =============================================================================
# 7. MODERN CONFIGURATION PATTERNS
# =============================================================================


def setup_modern_logging() -> Dict[str, Logger]:
    """⚙️ Modern logging configuration with multiple loggers"""

    # Application logger with structured output
    app_logger = Logger(
        "ModernApp",
        console=True,
        file_path=Path("logs/modern_app.log"),
        json_file=Path("logs/modern_app.json"),
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )

    # Performance logger for metrics
    perf_logger = Logger(
        "Performance",
        console=False,
        file_path=Path("logs/performance.log"),
        json_file=Path("logs/performance.json"),
    )

    # Error logger for debugging
    error_logger = Logger("Errors", console=True, file_path=Path("logs/errors.log"), level="ERROR")

    return {"app": app_logger, "performance": perf_logger, "errors": error_logger}


# =============================================================================
# 8. MAIN DEMONSTRATION
# =============================================================================


async def main():
    """🚀 Main demonstration of modern usage patterns"""
    print("🔵 LogEverything Modernized Usage Demo")
    print("=" * 50)

    # Setup modern logging
    loggers = setup_modern_logging()
    app_logger.info("⚙️ Modern logging configuration complete")

    print("\n1️⃣ Type-annotated async data fetching:")
    user = await fetch_user_data(1)
    if user:
        print(f"   📊 Fetched: {user.name} ({user.email})")

    print("\n2️⃣ Concurrent batch processing:")
    users = await process_users_batch([1, 2, 3])
    print(f"   📦 Processed {len(users)} users")

    print("\n3️⃣ Modern service with retry logic:")
    service = ModernService("DemoService")
    test_data = {"name": "TestUser", "email": "test@example.com"}
    success = await service.process_with_retry(test_data)
    print(f"   ✅ Service processing: {'Success' if success else 'Failed'}")

    print("\n4️⃣ Performance monitoring:")
    await performance_comparison()

    print("\n5️⃣ Complete modern pipeline:")
    await modern_pipeline_example()


if __name__ == "__main__":
    print("🔵 Starting modern usage patterns demonstration...")
    asyncio.run(main())
    print("\n✅ Modern usage patterns demonstration complete!")
    print("📚 These patterns showcase LogEverything in modern Python applications.")
