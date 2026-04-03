"""
LogEverything Decorator Enhancement Examples

This example demonstrates the new smart logger selection and registry features
introduced in LogEverything v1.0.0, including the `using` parameter and
automatic logger discovery.
"""

import time

from logeverything import Logger
from logeverything.core import get_active_loggers
from logeverything.decorators import log, log_class, log_function, log_io


def basic_logger_selection_example():
    """Example 1: Basic logger selection with the using parameter"""
    print("=== Example 1: Basic Logger Selection ===")

    # Create named loggers for different components
    api_logger = Logger("api")
    db_logger = Logger("database")
    auth_logger = Logger("authentication")

    # Configure loggers with different settings
    api_logger.configure(level="INFO", visual_mode=True)
    db_logger.configure(level="DEBUG", visual_mode=True)
    auth_logger.configure(level="WARNING", visual_mode=True)

    # Use specific loggers with decorators
    @log(using="api")
    def handle_request(endpoint):
        return f"Processed request to {endpoint}"

    @log_function(using="database")
    def fetch_user(user_id):
        time.sleep(0.01)  # Simulate database query
        return {"id": user_id, "name": f"User{user_id}"}

    @log_io(using="database")
    def save_data(filename, data):
        with open(filename, "w") as f:
            f.write(str(data))
        return True

    @log_class(using="authentication")
    class AuthService:
        def login(self, username):
            return f"Logged in: {username}"

        def logout(self, username):
            return f"Logged out: {username}"

    # Execute functions to see targeted logging
    print("\\n--- API Operations ---")
    handle_request("/users")
    handle_request("/orders")

    print("\\n--- Database Operations ---")
    user = fetch_user(123)
    save_data("user_data.txt", user)

    print("\\n--- Authentication Operations ---")
    auth = AuthService()
    auth.login("alice")
    auth.logout("alice")


def auto_discovery_example():
    """Example 2: Automatic logger discovery"""
    print("\\n\\n=== Example 2: Auto-Discovery ===")

    # Clear existing loggers to start fresh
    from logeverything.core import _active_loggers

    _active_loggers.clear()

    # Scenario 1: Single logger available
    print("\\n--- Single Logger Available ---")
    main_logger = Logger("main")
    main_logger.configure(level="INFO", visual_mode=True)

    @log  # Will automatically use "main" logger
    def process_data(data):
        return f"Processed: {data}"

    process_data("sample_data")

    # Scenario 2: Multiple loggers available
    print("\\n--- Multiple Loggers Available ---")
    service_logger = Logger("service")
    util_logger = Logger("utils")

    @log  # Will show guidance about multiple loggers
    def complex_operation():
        return "Complex operation completed"

    complex_operation()

    # Scenario 3: No loggers configured
    print("\\n--- No Loggers Configured ---")
    _active_loggers.clear()  # Clear all loggers

    @log  # Will create temporary logger
    def emergency_function():
        return "Emergency processing"

    emergency_function()


def error_handling_example():
    """Example 3: Error handling and helpful messages"""
    print("\\n\\n=== Example 3: Error Handling ===")

    # Create some loggers
    Logger("web_server")
    Logger("business_logic")
    Logger("data_access")

    print("\\n--- Available Loggers ---")
    active = get_active_loggers()
    print(f"Active loggers: {list(active.keys())}")

    try:

        @log(using="nonexistent_logger")
        def will_fail():
            return "This won't work"

        will_fail()
    except Exception as e:
        print("\\n--- Error Example ---")
        print(f"Error: {e}")


def real_world_application_example():
    """Example 4: Real-world multi-tier application"""
    print("\\n\\n=== Example 4: Real-World Application ===")

    # Setup loggers for different application layers
    web_logger = Logger("web_layer")
    business_logger = Logger("business_layer")
    data_logger = Logger("data_layer")

    # Configure each layer differently
    web_logger.configure(level="INFO", visual_mode=True, use_symbols=True)
    business_logger.configure(level="DEBUG", visual_mode=True, use_symbols=True)
    data_logger.configure(level="DEBUG", visual_mode=True, use_symbols=True)

    # Web layer - API controllers
    @log_class(using="web_layer")
    class UserController:
        def __init__(self):
            self.user_service = UserService()

        def get_user(self, user_id):
            return self.user_service.fetch_user(user_id)

        def create_user(self, user_data):
            return self.user_service.create_user(user_data)

    # Business layer - Service classes
    @log_class(using="business_layer")
    class UserService:
        def __init__(self):
            self.repository = UserRepository()

        def fetch_user(self, user_id):
            # Business logic validation
            if user_id <= 0:
                raise ValueError("Invalid user ID")
            return self.repository.get_user(user_id)

        def create_user(self, user_data):
            # Validation and business rules
            validated_data = self._validate_user_data(user_data)
            return self.repository.save_user(validated_data)

        def _validate_user_data(self, data):
            # Validation logic
            if not data.get("email"):
                raise ValueError("Email is required")
            return data

    # Data layer - Repository classes
    @log_class(using="data_layer")
    class UserRepository:
        def get_user(self, user_id):
            # Simulate database query
            time.sleep(0.005)
            return {"id": user_id, "name": f"User{user_id}", "email": f"user{user_id}@example.com"}

        def save_user(self, user_data):
            # Simulate database insert
            time.sleep(0.01)
            user_data["id"] = 999
            return user_data

    # Execute the full flow
    print("\\n--- Full Application Flow ---")
    controller = UserController()

    # Fetch existing user
    user = controller.get_user(123)
    print(f"Fetched user: {user}")

    # Create new user
    new_user_data = {"name": "Alice", "email": "alice@example.com"}
    created_user = controller.create_user(new_user_data)
    print(f"Created user: {created_user}")


def performance_monitoring_example():
    """Example 5: Performance monitoring with decorators"""
    print("\\n\\n=== Example 5: Performance Monitoring ===")

    # Setup performance logger
    perf_logger = Logger("performance")
    perf_logger.configure(
        level="DEBUG", visual_mode=True, log_arguments=True, log_return_values=True
    )

    @log_function(
        using="performance", log_arguments=True, log_return_values=True, log_entry_exit=True
    )
    def cpu_intensive_task(iterations):
        """Simulate CPU-intensive work with performance logging"""
        result = 0
        for i in range(iterations):
            result += i**2
        return {"result": result, "iterations": iterations}

    @log_io(using="performance")
    def file_operation(filename, data_size):
        """Simulate file I/O with performance tracking"""
        data = "x" * data_size
        with open(filename, "w") as f:
            f.write(data)
        return len(data)

    print("\\n--- Performance Monitoring ---")
    cpu_result = cpu_intensive_task(10000)
    file_result = file_operation("test_perf.txt", 1000)

    # Cleanup
    import os

    try:
        os.remove("test_perf.txt")
    except:
        pass


def cleanup_example():
    """Clean up temporary files created during examples"""
    import os

    files_to_remove = ["user_data.txt", "test_perf.txt"]

    for filename in files_to_remove:
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    print("LogEverything Decorator Enhancement Examples")
    print("=" * 50)

    try:
        basic_logger_selection_example()
        auto_discovery_example()
        error_handling_example()
        real_world_application_example()
        performance_monitoring_example()
    finally:
        cleanup_example()

    print("\\n\\nAll examples completed!")
    print("\\nKey Features Demonstrated:")
    print("• Smart logger selection with 'using' parameter")
    print("• Automatic logger discovery and registration")
    print("• Helpful error messages and guidance")
    print("• Multi-tier application logging")
    print("• Performance monitoring integration")
    print("• Zero-configuration defaults")
