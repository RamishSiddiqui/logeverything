#!/usr/bin/env python3
"""
Rotation Handlers Example

Demonstrates LogEverything's built-in file rotation handlers for
production-safe log management.  Both size-based and time-based
rotation are shown, each paired with JSONLineFormatter for
dashboard-compatible structured output.

Key Techniques Demonstrated:
- FileHandler with max_size and backup_count (size-based rotation)
- TimedRotatingFileHandler with when/retention_days (time-based rotation)
- Gzip compression of rotated files
- JSONLineFormatter for dashboard-compatible JSONL output
- Combining rotation + structured output for the dashboard data directory
"""

import logging
import sys
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from logeverything import Logger
from logeverything.decorators import log
from logeverything.handlers import FileHandler, JSONLineFormatter, TimedRotatingFileHandler


def main():
    print("=== Rotation Handlers Demo ===\n")

    # ----------------------------------------------------------------
    # 1. Size-Based Rotation
    # ----------------------------------------------------------------
    print("1. Size-Based Rotation (FileHandler)")
    print("-" * 45)

    size_logger = Logger("size_rotation", auto_setup=False)

    handler = FileHandler(
        "logs/app.jsonl",
        max_size=5 * 1024 * 1024,  # 5 MB per file
        backup_count=3,  # keep app.jsonl.1, .2, .3
        compress=True,  # gzip the most recent rotated file
    )
    handler.setFormatter(JSONLineFormatter(source="my_service"))
    size_logger.add_handler(handler)

    size_logger.info("Application started")
    size_logger.debug("Size-based rotation: files rotate when they exceed 5 MB")
    size_logger.warning("Old files beyond backup_count are deleted automatically")

    print("  Handler: FileHandler('logs/app.jsonl', max_size=5MB, backup_count=3)")
    print("  Rotated files: app.jsonl.1, app.jsonl.2, app.jsonl.3 (+ .gz)")

    # ----------------------------------------------------------------
    # 2. Time-Based Rotation
    # ----------------------------------------------------------------
    print("\n2. Time-Based Rotation (TimedRotatingFileHandler)")
    print("-" * 50)

    time_logger = Logger("time_rotation", auto_setup=False)

    handler = TimedRotatingFileHandler(
        "logs/daily.jsonl",
        when="midnight",  # rotate at midnight (also: "hourly", "weekly")
        retention_days=30,  # delete files older than 30 days
        compress=True,  # gzip rotated files
    )
    handler.setFormatter(JSONLineFormatter(source="my_service"))
    time_logger.add_handler(handler)

    time_logger.info("Application started")
    time_logger.debug("Time-based rotation: a new file starts each day at midnight")
    time_logger.warning("Files older than retention_days are cleaned up automatically")

    print("  Handler: TimedRotatingFileHandler('logs/daily.jsonl', when='midnight')")
    print("  Rotated files: daily.jsonl.2026-02-22, daily.jsonl.2026-02-21, ...")

    # ----------------------------------------------------------------
    # 3. Dashboard Integration — writing to the data directory
    # ----------------------------------------------------------------
    print("\n3. Dashboard Integration")
    print("-" * 45)

    dashboard_logger = Logger("dashboard_writer", auto_setup=False)

    handler = TimedRotatingFileHandler(
        "~/.logeverything/data/app.jsonl",  # dashboard's default data directory
        when="midnight",
        retention_days=7,
        compress=True,
    )
    handler.setFormatter(JSONLineFormatter(source="my_app"))
    dashboard_logger.add_handler(handler)

    @log(using="dashboard_writer")
    def process_order(order_id):
        dashboard_logger.info(f"Processing order {order_id}")
        validate_order(order_id)
        return "completed"

    @log(using="dashboard_writer")
    def validate_order(order_id):
        dashboard_logger.info(f"Order {order_id} validated")

    process_order("ORD-001")

    print("  Logs written to ~/.logeverything/data/app.jsonl")
    print("  Dashboard auto-discovers *.jsonl and *.jsonl.* (including .gz)")
    print("  Hierarchy fields (call_id, parent_call_id, indent_level) included")

    # ----------------------------------------------------------------
    # 4. Multiple Rotation Handlers on One Logger
    # ----------------------------------------------------------------
    print("\n4. Multiple Rotation Handlers on One Logger")
    print("-" * 50)

    multi_logger = Logger("multi_rotation", auto_setup=False)

    # Human-readable console output
    from logeverything.handlers import ConsoleHandler

    console = ConsoleHandler()
    console.setLevel(logging.INFO)
    multi_logger.add_handler(console)

    # Structured JSONL with daily rotation (for the dashboard)
    jsonl_handler = TimedRotatingFileHandler(
        "logs/structured.jsonl",
        when="midnight",
        retention_days=30,
    )
    jsonl_handler.setFormatter(JSONLineFormatter(source="multi_rotation"))
    multi_logger.add_handler(jsonl_handler)

    # Plain text with size-based rotation (for grep/tail)
    text_handler = FileHandler(
        "logs/plaintext.log",
        max_size=10 * 1024 * 1024,
        backup_count=5,
    )
    text_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    )
    multi_logger.add_handler(text_handler)

    multi_logger.info("This message goes to console, JSONL, and plain text")
    multi_logger.error("Errors appear in all three destinations")

    print("  Console: human-readable (INFO+)")
    print("  logs/structured.jsonl: dashboard-compatible JSONL (daily rotation)")
    print("  logs/plaintext.log: plain text for grep/tail (size rotation)")

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    print("\n" + "=" * 50)
    print("Rotation Handler Summary:")
    print()
    print("  FileHandler(max_size=, backup_count=, compress=)")
    print("    - Rotates when file exceeds max_size bytes")
    print("    - Keeps up to backup_count rotated files")
    print()
    print("  TimedRotatingFileHandler(when=, retention_days=, compress=)")
    print("    - when: 'midnight', 'hourly', or 'weekly'")
    print("    - Deletes files older than retention_days")
    print()
    print("  Both support compress=True for gzip compression.")
    print("  Pair with JSONLineFormatter for dashboard-compatible output.")


if __name__ == "__main__":
    main()
