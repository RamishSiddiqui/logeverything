"""
🚀 Step 4: Async Services for Performance (FIXED VERSION)
Create high-performance async services with proper logging isolation.
"""

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
        # Create a dedicated async logger for this service
        self.log = AsyncLogger("UserService", level="INFO")
        # Register the logger globally so decorators can find it
        import logeverything.core as core

        core.register_logger("UserService", self.log)
        self.database = UserDatabase()

    @log(using="UserService")  # Use the specific logger
    async def process_user_registration(self, user_data: dict) -> dict:
        """Process user registration with async logging."""
        # Use proper async context with isolation
        async with self.log.context(f"Registration-{user_data['username']}"):
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
        email_log.info("✅ Verification email sent")

    async def _setup_user_profile(self, user_id: int) -> dict:
        """Setup user profile."""
        profile_log = self.log.bind(user_id=user_id)
        profile_log.info("👤 Setting up user profile")
        await asyncio.sleep(0.1)  # Simulate profile creation

        profile = {"user_id": user_id, "preferences": {}, "settings": {}}
        profile_log.info("✅ Profile setup completed")
        return profile

    @log(using="UserService")  # Use the same logger for consistency
    async def batch_process_users(self, user_list: list) -> list:
        """Process multiple users concurrently with proper isolation."""
        async with self.log.context("BatchProcessing"):
            batch_log = self.log.bind(batch_size=len(user_list))
            batch_log.info(f"🔄 Processing {len(user_list)} users")

            # Process all users concurrently with proper isolation
            tasks = []
            for i, user in enumerate(user_list):
                # Each task gets its own isolated context
                task = asyncio.create_task(
                    self._process_single_user_isolated(user, i), name=f"user-{user['username']}-{i}"
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks)

            batch_log.info("✅ Batch processing completed")
            return results

    async def _process_single_user_isolated(self, user_data: dict, index: int) -> dict:
        """Process a single user with isolated logging context."""
        # Create isolated context for each user
        context_name = f"User-{index}-{user_data['username']}"
        async with self.log.context(context_name):
            return await self.process_user_registration(user_data)


# Alternative: Use a single logger approach for cleaner output
class UserServiceClean:
    def __init__(self):
        # Single logger, no decorator conflicts
        self.log = AsyncLogger("CleanUserService", level="INFO", use_symbols=True)
        # Register the logger globally
        import logeverything.core as core

        core.register_logger("CleanUserService", self.log)
        self.database = UserDatabase()

    async def process_user_registration(self, user_data: dict) -> dict:
        """Process user registration with clean async logging."""
        context_name = f"Registration-{user_data['username']}"
        async with self.log.context(context_name):
            user_log = self.log.bind(username=user_data["username"])
            user_log.info("🔄 Processing registration")

            # All operations with proper logging
            await self._validate_user_async(user_data)
            await self._send_verification_email(user_data["email"])

            user_id = self.database.create_user(user_data)
            profile = await self._setup_user_profile(user_id)

            result_log = self.log.bind(user_id=user_id)
            result_log.info("✅ Registration completed")
            return {"user_id": user_id, "profile": profile}

    async def _validate_user_async(self, user_data: dict):
        """Async user validation."""
        self.log.info("🔍 Validating user data")
        await asyncio.sleep(0.1)
        self.log.info("✅ User data is valid")

    async def _send_verification_email(self, email: str):
        """Simulate sending verification email."""
        email_log = self.log.bind(email=email)
        email_log.info("📧 Sending verification email")
        await asyncio.sleep(0.2)
        email_log.info("✅ Verification email sent")

    async def _setup_user_profile(self, user_id: int) -> dict:
        """Setup user profile."""
        profile_log = self.log.bind(user_id=user_id)
        profile_log.info("👤 Setting up user profile")
        await asyncio.sleep(0.1)

        profile = {"user_id": user_id, "preferences": {}, "settings": {}}
        profile_log.info("✅ Profile setup completed")
        return profile

    async def batch_process_users(self, user_list: list) -> list:
        """Process multiple users concurrently with clean output."""
        async with self.log.context("BatchProcessing"):
            batch_log = self.log.bind(batch_size=len(user_list))
            batch_log.info(f"🔄 Starting batch processing of {len(user_list)} users")

            # Sequential processing with clear logging
            results = []
            for i, user_data in enumerate(user_list):
                result = await self.process_user_registration(user_data)
                results.append(result)

            batch_log.info("✅ All users processed successfully")
            return results

    async def batch_process_users_concurrent(self, user_list: list) -> list:
        """Process multiple users concurrently (advanced version)."""
        async with self.log.context("ConcurrentBatch"):
            batch_log = self.log.bind(batch_size=len(user_list))
            batch_log.info(f"🔄 Starting concurrent processing of {len(user_list)} users")

            # Use semaphore to limit concurrency and reduce log interference
            semaphore = asyncio.Semaphore(2)  # Max 2 concurrent operations

            async def process_with_semaphore(user_data, index):
                async with semaphore:
                    # Add slight delay to reduce log conflicts
                    await asyncio.sleep(index * 0.05)
                    return await self.process_user_registration(user_data)

            tasks = [process_with_semaphore(user, i) for i, user in enumerate(user_list)]
            results = await asyncio.gather(*tasks)

            batch_log.info("✅ Concurrent processing completed")
            return results


# Test both versions
async def test_services():
    print("=" * 60)
    print("🧪 Testing FIXED Async Service with Decorators")
    print("=" * 60)

    service = UserService()

    # Test single user
    print("\n📋 Single User Registration:")
    user_data = {"username": "bob", "email": "bob@example.com"}
    result = await service.process_user_registration(user_data)
    print(f"✅ Result: {result}")

    # Test batch processing
    print("\n📋 Batch Processing:")
    batch_users = [
        {"username": "charlie", "email": "charlie@example.com"},
        {"username": "diana", "email": "diana@example.com"},
    ]
    batch_results = await service.batch_process_users(batch_users)
    print(f"✅ Batch Results: {len(batch_results)} users processed")

    print("\n" + "=" * 60)
    print("🧪 Testing CLEAN Async Service (Recommended)")
    print("=" * 60)

    clean_service = UserServiceClean()

    # Test single user with clean service
    print("\n📋 Single User Registration (Clean):")
    user_data = {"username": "eve", "email": "eve@example.com"}
    result = await clean_service.process_user_registration(user_data)
    print(f"✅ Result: {result}")

    # Test sequential batch processing (cleanest output)
    print("\n📋 Sequential Batch Processing (Clean):")
    batch_users = [
        {"username": "frank", "email": "frank@example.com"},
        {"username": "grace", "email": "grace@example.com"},
    ]
    batch_results = await clean_service.batch_process_users(batch_users)
    print(f"✅ Sequential Results: {len(batch_results)} users processed")

    # Test concurrent with limited parallelism
    print("\n📋 Controlled Concurrent Processing:")
    batch_users = [
        {"username": "henry", "email": "henry@example.com"},
        {"username": "iris", "email": "iris@example.com"},
        {"username": "jack", "email": "jack@example.com"},
    ]
    batch_results = await clean_service.batch_process_users_concurrent(batch_users)
    print(f"✅ Concurrent Results: {len(batch_results)} users processed")


if __name__ == "__main__":
    asyncio.run(test_services())
