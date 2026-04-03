"""
Hierarchy Filter for LogEverything.

Provides a logging filter that injects structured hierarchy fields into every LogRecord,
enabling downstream consumers (JSON handlers, dashboards) to reconstruct call trees.

Fields injected:
- ``indent_level``: Current nesting depth (int)
- ``call_id``: Unique identifier for the current function call (str)
- ``parent_call_id``: call_id of the enclosing function call (str)
- ``execution_id``: Unique identifier for the current thread/task context (str)
- ``log_type``: One of "message", "call_entry", "call_exit" (str)
"""

import logging

from .indent_manager import get_indent_manager


class HierarchyFilter(logging.Filter):
    """
    A logging filter that auto-injects hierarchy context into every LogRecord.

    Usage::

        import logging
        from logeverything.hierarchy import HierarchyFilter

        handler = logging.StreamHandler()
        handler.addFilter(HierarchyFilter())
        logger = logging.getLogger("myapp")
        logger.addHandler(handler)
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Inject hierarchy fields into the log record."""
        indent_mgr = get_indent_manager()
        level, call_id, parent_call_id, execution_id = indent_mgr.get_hierarchy_snapshot()
        record.indent_level = level
        record.call_id = call_id
        record.parent_call_id = parent_call_id
        record.execution_id = execution_id
        # log_type defaults to "message"; decorators override via extra={}
        if not hasattr(record, "log_type"):
            record.log_type = "message"
        return True
