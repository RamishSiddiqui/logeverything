#!/usr/bin/env python3
"""
Hierarchy Fields Example

This example demonstrates LogEverything's structured hierarchy fields that are
automatically injected into every log record by the @log decorator. These fields
enable downstream consumers (JSON handlers, dashboards) to reconstruct the
function call tree without parsing indentation strings.

Fields injected:
- indent_level: Current nesting depth (0 = top-level)
- call_id: Unique 12-char hex ID for this function call
- parent_call_id: call_id of the enclosing function call
- log_type: "call_entry", "call_exit", or "message"
- execution_id: Thread/task execution context identifier

Key Techniques Demonstrated:
- Inspecting hierarchy fields on log records
- Using HierarchyFilter with standard Python logging
- Nested function calls with automatic call stack tracking
- JSON output with promoted hierarchy fields
"""

import json
import logging
import sys
from pathlib import Path

# Ensure stdout can handle unicode on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from logeverything import Logger
from logeverything.decorators import log
from logeverything.hierarchy import HierarchyFilter

# ---------------------------------------------------------------------------
# 1. Inspecting hierarchy fields via a custom handler
# ---------------------------------------------------------------------------


class RecordInspector(logging.Handler):
    """A handler that captures log records for inspection."""

    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


def demonstrate_hierarchy_fields():
    """Show hierarchy fields on nested decorated functions."""
    print("1. Hierarchy Fields on Nested Calls")
    print("-" * 40)

    app = Logger("hierarchy_demo")
    inspector = RecordInspector()
    app._logger.addHandler(inspector)

    @log(using="hierarchy_demo")
    def outer(x):
        app.info(f"Processing {x} in outer")
        return inner(x * 2)

    @log(using="hierarchy_demo")
    def inner(y):
        app.info(f"Processing {y} in inner")
        return y + 1

    result = outer(5)
    print(f"\nResult: {result}")
    print(f"\nCaptured {len(inspector.records)} log records:\n")

    print(f"{'log_type':<12} {'indent':>6} {'call_id':>10} {'parent':>10}  message")
    print("-" * 80)
    for r in inspector.records:
        log_type = getattr(r, "log_type", "?")
        indent = getattr(r, "indent_level", "?")
        call_id = getattr(r, "call_id", "")[:8] or "-"
        parent = getattr(r, "parent_call_id", "")[:8] or "-"
        # Strip leading whitespace/emoji from decorated messages for clean display
        msg = r.getMessage().strip()[:45]
        print(f"{log_type:<12} {indent:>6} {call_id:>10} {parent:>10}  {msg}")

    print()

    # Clean up
    app._logger.removeHandler(inspector)


# ---------------------------------------------------------------------------
# 2. Using HierarchyFilter with plain Python logging
# ---------------------------------------------------------------------------


def demonstrate_hierarchy_filter_standalone():
    """Show HierarchyFilter used outside of LogEverything loggers."""
    print("\n2. HierarchyFilter with Standard Python Logging")
    print("-" * 50)

    # Create a standard Python logger
    py_logger = logging.getLogger("standalone_hierarchy_demo")
    py_logger.setLevel(logging.DEBUG)
    py_logger.propagate = False

    # Attach the HierarchyFilter
    py_logger.addFilter(HierarchyFilter())

    # Custom formatter that uses hierarchy fields
    class HierarchyFormatter(logging.Formatter):
        def format(self, record):
            indent = "  " * getattr(record, "indent_level", 0)
            log_type = getattr(record, "log_type", "message")
            call_id = getattr(record, "call_id", "")[:8]
            prefix = f"[{log_type:<10}]" if log_type != "message" else " " * 12
            cid = f" ({call_id})" if call_id else ""
            return f"{prefix} {indent}{record.getMessage()}{cid}"

    handler = logging.StreamHandler()
    handler.setFormatter(HierarchyFormatter())
    py_logger.addHandler(handler)

    py_logger.info("This is a top-level message")
    py_logger.info("HierarchyFilter injects fields into every record")

    print()

    # Clean up
    py_logger.removeHandler(handler)
    py_logger.removeFilter(py_logger.filters[0])


# ---------------------------------------------------------------------------
# 3. JSON output with hierarchy fields
# ---------------------------------------------------------------------------


def demonstrate_json_hierarchy():
    """Show hierarchy fields promoted to top-level JSON keys."""
    print("\n3. JSON Output with Hierarchy Fields")
    print("-" * 40)

    app = Logger("json_hierarchy_demo")
    inspector = RecordInspector()
    app._logger.addHandler(inspector)

    @log(using="json_hierarchy_demo")
    def api_handler(request_id):
        app.info(f"Handling request {request_id}")
        return validate_input(request_id)

    @log(using="json_hierarchy_demo")
    def validate_input(request_id):
        app.info(f"Validating {request_id}")
        return True

    api_handler("req-001")

    print("\nJSON-style output (as JSONHandler would emit):\n")
    for r in inspector.records:
        entry = {
            "message": r.getMessage()[:60],
            "level": r.levelname,
            "indent_level": getattr(r, "indent_level", 0),
            "call_id": getattr(r, "call_id", "")[:12],
            "parent_call_id": getattr(r, "parent_call_id", "")[:12],
            "log_type": getattr(r, "log_type", "message"),
        }
        print(json.dumps(entry, indent=2))
        print()

    # Clean up
    app._logger.removeHandler(inspector)


# ---------------------------------------------------------------------------
# 4. Deep nesting to show call stack tracking
# ---------------------------------------------------------------------------


def demonstrate_deep_nesting():
    """Show call stack tracking through multiple nesting levels."""
    print("\n4. Deep Nesting — Call Stack Tracking")
    print("-" * 40)

    app = Logger("nesting_demo")
    inspector = RecordInspector()
    app._logger.addHandler(inspector)

    @log(using="nesting_demo")
    def level_1():
        app.info("In level 1")
        return level_2()

    @log(using="nesting_demo")
    def level_2():
        app.info("In level 2")
        return level_3()

    @log(using="nesting_demo")
    def level_3():
        app.info("In level 3 (deepest)")
        return 42

    result = level_1()
    print(f"\nResult: {result}")
    print(f"\nCall tree ({len(inspector.records)} records):\n")

    for r in inspector.records:
        log_type = getattr(r, "log_type", "message")
        indent = getattr(r, "indent_level", 0)
        prefix = "  " * indent

        if log_type == "call_entry":
            symbol = ">"
        elif log_type == "call_exit":
            symbol = "<"
        else:
            symbol = "|"

        msg = r.getMessage()[:50]
        print(f"  depth={indent}  {prefix}{symbol} {msg}")

    print()

    # Clean up
    app._logger.removeHandler(inspector)


def main():
    print("=== Hierarchy Fields Demo ===\n")

    demonstrate_hierarchy_fields()
    demonstrate_hierarchy_filter_standalone()
    demonstrate_json_hierarchy()
    demonstrate_deep_nesting()

    print("Key Concepts Demonstrated:")
    print("- Hierarchy fields (indent_level, call_id, parent_call_id, log_type)")
    print("- HierarchyFilter auto-attached to Logger instances")
    print("- HierarchyFilter usable with standard Python logging")
    print("- JSON output with promoted hierarchy fields")
    print("- Call stack tracking through deep nesting")
    print("\nThese fields power the dashboard's hierarchical tree view.")
    print("See: docs/source/user-guide/dashboard.rst")


if __name__ == "__main__":
    main()
