#!/usr/bin/env python3
"""
Clean Async Services Example - Properly Configured Logging
==========================================================

This example shows how to create high-performance async services with clean,
properly formatted logging output.

Key improvements:
- Proper logger registration with the decorator system
- Clean output formatting
- No context bleeding between operations
- Consistent async logging throughout
"""

import asyncio

from logeverything.asyncio import AsyncLogger
from logeverything.core import register_logger
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
        # Create and register the async logger
        self.log = AsyncLogger("user_service", level="INFO")
        # Register with the decorator system to avoid fallback to standard logger
        register_logger("user_service", self.log)

        self.database = UserDatabase()

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
        email_log.info("✅ Verification email sent")

    async def _setup_user_profile(self, user_id: int) -> dict:
        """Setup user profile."""
        profile_log = self.log.bind(user_id=user_id)
        profile_log.info("👤 Setting up user profile")
        await asyncio.sleep(0.1)  # Simulate profile creation

        profile = {"user_id": user_id, "preferences": {}, "settings": {}}
        profile_log.info("✅ Profile setup completed")
        return profile

    @log
    async def batch_process_users(self, user_list: list) -> list:
        """Process multiple users concurrently."""
        async with self.log.context("Batch Processing"):
            batch_log = self.log.bind(batch_size=len(user_list))
            batch_log.info(f"🔄 Processing {len(user_list)} users")

            # Process all users concurrently
            tasks = [self.process_user_registration(user) for user in user_list]
            results = await asyncio.gather(*tasks)

            batch_log.info("✅ Batch processing completed")
            return results


async def demo_clean_async_services():
    """Demonstrate clean async service logging."""
    print("🚀 Clean Async Services Demo")
    print("=" * 50)

    # Create service with properly registered logger
    service = UserService()

    print("\n📝 Single User Registration:")
    print("-" * 30)

    # Single user registration
    user_data = {"username": "alice", "email": "alice@example.com"}
    result = await service.process_user_registration(user_data)

    print("\n📝 Batch User Processing:")
    print("-" * 30)

    # Batch processing
    batch_users = [
        {"username": "bob", "email": "bob@example.com"},
        {"username": "charlie", "email": "charlie@example.com"},
        {"username": "diana", "email": "diana@example.com"},
    ]
    batch_results = await service.batch_process_users(batch_users)

    print("\n📊 Results Summary:")
    print("-" * 30)
    print(f"✅ Single user result: {result}")
    print(f"✅ Batch results: {len(batch_results)} users processed")

    # Show the clean data
    for i, user_result in enumerate(batch_results, 1):
        print(f"   User {i}: ID {user_result['user_id']}")


if __name__ == "__main__":
    asyncio.run(demo_clean_async_services())
