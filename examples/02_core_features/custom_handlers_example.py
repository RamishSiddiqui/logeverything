#!/usr/bin/env python3
"""
Custom Handlers and Formatters Example

This example demonstrates how to create and use custom handlers and formatters
with LogEverything for specialized logging needs.

IMPORTANT: To avoid duplicate log messages, use auto_setup=False when creating
Logger instances that will use custom handlers. This prevents LogEverything's
automatic console handler creation.

Key Techniques Demonstrated:
- JSONLineFormatter for dashboard-compatible structured output
- Custom database handler simulation
- Multiple handlers with different log levels
- Custom colored formatter with ANSI colors
- Hand-rolled JSON formatter (when you need full schema control)
- Preventing duplicate output with auto_setup=False
"""

import datetime
import json
import logging
import sys
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from logeverything import Logger
from logeverything.handlers import ConsoleHandler, FileHandler, JSONLineFormatter


class DatabaseHandler(logging.Handler):
    """Custom handler that simulates writing to a database."""

    def __init__(self):
        super().__init__()
        self.logs = []  # Simulate database storage

    def emit(self, record):
        try:
            log_entry = {
                "timestamp": datetime.datetime.fromtimestamp(record.created),
                "level": record.levelname,
                "message": self.format(record),
                "logger_name": record.name,
            }
            self.logs.append(log_entry)
            # In real implementation, this would write to actual database
            print(f"[DB] Stored log: {record.levelname} - {record.getMessage()}")
        except Exception:
            self.handleError(record)

    def get_logs(self, level=None):
        """Retrieve logs from simulated database."""
        if level:
            return [log for log in self.logs if log["level"] == level]
        return self.logs


def main():
    print("=== Custom Handlers and Formatters Demo ===\n")

    # ----------------------------------------------------------------
    # 1. JSONLineFormatter — the built-in way to get structured output
    # ----------------------------------------------------------------
    print("1. JSONLineFormatter with File Handler (Recommended)")
    print("-" * 55)

    json_logger = Logger("json_app", auto_setup=False)
    json_handler = FileHandler("structured.jsonl")
    json_handler.setFormatter(JSONLineFormatter(source="my_service"))
    json_logger.add_handler(json_handler)

    json_logger.info("User login", extra={"user_id": 12345, "request_id": "req-abc-123"})
    json_logger.warning("High memory usage", extra={"memory_percent": 85.2})
    json_logger.error(
        "Database connection failed", extra={"db_host": "localhost", "retry_count": 3}
    )

    print("  JSON Lines logs written to structured.jsonl")
    print("  (Dashboard-compatible — includes hierarchy fields, correlation IDs)")

    # ----------------------------------------------------------------
    # 2. Custom Database Handler
    # ----------------------------------------------------------------
    print("\n2. Custom Database Handler")
    print("-" * 40)

    db_logger = Logger("database_app", auto_setup=False)
    db_handler = DatabaseHandler()
    db_logger.add_handler(db_handler)

    db_logger.info("Application started")
    db_logger.warning("Cache miss for key: user_profile_123")
    db_logger.error("Failed to process payment")
    db_logger.info("User logout")

    all_logs = db_handler.get_logs()
    error_logs = db_handler.get_logs("ERROR")

    print(f"  Total logs in database: {len(all_logs)}")
    print(f"  Error logs: {len(error_logs)}")

    # ----------------------------------------------------------------
    # 3. Multiple Handlers with Different Levels
    # ----------------------------------------------------------------
    print("\n3. Multiple Handlers with Different Levels")
    print("-" * 40)

    multi_logger = Logger("multi_handler_app", auto_setup=False)

    # Console handler for INFO and above
    console_handler = ConsoleHandler()
    console_handler.setLevel(logging.INFO)

    # File handler for DEBUG and above — with JSONL format
    file_handler = FileHandler("debug.jsonl")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONLineFormatter(source="multi_handler_app"))

    # Database handler for ERROR and above
    error_db_handler = DatabaseHandler()
    error_db_handler.setLevel(logging.ERROR)

    multi_logger.add_handler(console_handler)
    multi_logger.add_handler(file_handler)
    multi_logger.add_handler(error_db_handler)

    multi_logger.debug("Debug information (file only)")
    multi_logger.info("Info message (console + file)")
    multi_logger.warning("Warning message (console + file)")
    multi_logger.error("Error message (all handlers)")

    print("  Logs distributed across handlers based on levels")

    # ----------------------------------------------------------------
    # 4. Custom Colored Formatter
    # ----------------------------------------------------------------
    print("\n4. Custom Colored Formatter")
    print("-" * 40)

    class ColoredFormatter(logging.Formatter):
        """Formatter that adds ANSI color codes."""

        COLORS = {
            "DEBUG": "\033[36m",  # Cyan
            "INFO": "\033[32m",  # Green
            "WARNING": "\033[33m",  # Yellow
            "ERROR": "\033[31m",  # Red
            "CRITICAL": "\033[35m",  # Magenta
        }
        RESET = "\033[0m"

        def format(self, record):
            color = self.COLORS.get(record.levelname, "")
            record.levelname = f"{color}{record.levelname}{self.RESET}"
            return super().format(record)

    colored_logger = Logger("colored_app", auto_setup=False)
    colored_handler = ConsoleHandler()
    colored_handler.setFormatter(
        ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    colored_logger.add_handler(colored_handler)

    colored_logger.debug("Debug message in cyan")
    colored_logger.info("Info message in green")
    colored_logger.warning("Warning message in yellow")
    colored_logger.error("Error message in red")

    # ----------------------------------------------------------------
    # 5. Hand-Rolled JSON Formatter (full schema control)
    # ----------------------------------------------------------------
    print("\n5. Hand-Rolled JSON Formatter (Full Schema Control)")
    print("-" * 55)
    print("  Use this only when JSONLineFormatter's schema doesn't fit your needs.\n")

    class CustomJSONFormatter(logging.Formatter):
        """Custom JSON formatter with a completely custom schema."""

        def format(self, record):
            return json.dumps(
                {
                    "ts": datetime.datetime.fromtimestamp(record.created).isoformat(),
                    "sev": record.levelname[0],  # Single-char severity
                    "src": f"{record.module}.{record.funcName}:{record.lineno}",
                    "msg": record.getMessage(),
                }
            )

    custom_logger = Logger("custom_json_app", auto_setup=False)
    custom_handler = FileHandler("custom_schema.jsonl")
    custom_handler.setFormatter(CustomJSONFormatter())
    custom_logger.add_handler(custom_handler)

    custom_logger.info("Application started")
    custom_logger.error("Something went wrong")

    print("  Custom-schema logs written to custom_schema.jsonl")
    print("  (Not dashboard-compatible — use JSONLineFormatter for that)")

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    print("\n" + "=" * 55)
    print("Files created:")
    print("  structured.jsonl  — JSONLineFormatter (dashboard-compatible)")
    print("  debug.jsonl       — Multi-handler JSONL output")
    print("  custom_schema.jsonl — Hand-rolled custom JSON schema")
    print()
    print("Key takeaways:")
    print("  - Use JSONLineFormatter for structured/dashboard output")
    print("  - Use auto_setup=False to prevent duplicate log messages")
    print("  - Write a custom Formatter only when you need a custom schema")


if __name__ == "__main__":
    main()
