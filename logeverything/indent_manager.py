"""
Unified Indent Manager for LogEverything.

This module provides a centralized, thread-safe, async-aware indentation system
that replaces the separate sync/async indentation mechanisms throughout the codebase.

Key Features:
- Unified API for sync and async contexts
- Thread-local and context-variable support
- Performance optimized with caching
- Visual formatting with customizable symbols
- Automatic sync/async detection
- Context isolation for multiprocessing
- Backward compatibility with existing APIs
"""

import asyncio
import itertools
import os
import threading
import time as _time
import weakref
from contextlib import contextmanager
from typing import Any, Dict, Optional, Tuple

# Try to import contextvars for async support
try:
    from contextvars import ContextVar, Token

    HAS_CONTEXTVARS = True
except ImportError:
    HAS_CONTEXTVARS = False
    ContextVar = None
    Token = None


class IndentContext:
    """
    Thread-local and async-aware context for indentation tracking.
    """

    def __init__(self) -> None:
        self.level: int = 0
        self.isolation_id: Optional[int] = None
        self.created_at: Optional[int] = None
        # Visual formatting preferences
        self.use_symbols: Optional[bool] = None
        self.visual_mode: bool = False
        self.use_indent: bool = False
        self.force_ascii: bool = False
        self.indent_char: str = "     "  # Increased default spacing
        self.indent_level: int = 2
        # Call stack for hierarchy tracking
        self.call_stack: list = []
        # Cached execution ID (computed once per context)
        self.execution_id_str: Optional[str] = None


# Monotonic counter for generating locally-unique call IDs (no syscall overhead)
_call_id_counter = itertools.count(1)


class IndentManager:
    """
    Unified indentation manager that handles both sync and async contexts.

    This manager automatically detects whether it's running in a sync or async context
    and uses the appropriate storage mechanism (thread-local vs contextvar).
    """

    def __init__(self) -> None:
        # Thread-local storage for sync contexts
        self._thread_local = threading.local()

        # Context variables for async contexts (if available)
        if HAS_CONTEXTVARS:
            self._async_level: ContextVar[int] = ContextVar("indent_level", default=0)
            self._async_context: ContextVar[IndentContext] = ContextVar(
                "indent_context", default=None
            )
        else:
            self._async_level = None
            self._async_context = None

        # Global configuration from LogEverything config
        self._config: Dict[str, Any] = {}

        # Pre-cached config values for fast access (avoids dict.get() on every call)
        self._cfg_visual_mode: bool = False
        self._cfg_use_indent: bool = False
        self._cfg_use_symbols: bool = False
        self._cfg_force_ascii: bool = False
        self._cfg_indent_level: int = 2
        self._cfg_beautify: bool = True

        # Performance optimization: Cached indent strings
        self._indent_cache: Dict[Tuple, str] = {}

        # Context isolation
        self._isolation_counter: int = 0
        self._isolation_lock = threading.Lock()

        # Weak references to active contexts for cleanup
        self._active_contexts: weakref.WeakSet = weakref.WeakSet()

        # Per-thread TTL cache for _is_async_context() result (~50ms TTL)
        self._async_check_cache = threading.local()

    def _get_isolation_id(self) -> int:
        """Get next isolation ID for context separation."""
        with self._isolation_lock:
            self._isolation_counter += 1
            return self._isolation_counter

    def generate_call_id(self) -> str:
        """Generate a locally-unique call ID using a monotonic counter.

        Uses thread ID + counter for uniqueness without syscall overhead.
        Call IDs only need local uniqueness for hierarchy tracking.

        Returns:
            Unique call ID string
        """
        return f"{threading.get_ident():x}-{next(_call_id_counter)}"

    def _is_async_context(self) -> bool:
        """
        Detect if we're currently in an async context.

        Uses asyncio.get_running_loop() which is a fast C-level check
        instead of expensive frame introspection.

        Returns:
            True if running in async context, False otherwise
        """
        if not HAS_CONTEXTVARS:
            return False
        try:
            asyncio.get_running_loop()
            return True
        except RuntimeError:
            return False

    def _get_thread_context(self) -> IndentContext:
        """Get or create thread-local indent context."""
        if not hasattr(self._thread_local, "context"):
            context = IndentContext()
            context.isolation_id = self._get_isolation_id()
            context.created_at = threading.get_ident()
            context.execution_id_str = (
                f"{os.getpid()}-{threading.get_ident()}-{context.isolation_id or 0}"
            )
            self._thread_local.context = context
            self._active_contexts.add(context)

        return self._thread_local.context

    def _get_async_context(self) -> IndentContext:
        """Get or create async-aware indent context."""
        if not HAS_CONTEXTVARS:
            # Fall back to thread-local storage
            return self._get_thread_context()

        context = self._async_context.get()
        if context is None:
            context = IndentContext()
            context.isolation_id = self._get_isolation_id()
            context.created_at = threading.get_ident()
            context.execution_id_str = (
                f"{os.getpid()}-{threading.get_ident()}-{context.isolation_id or 0}"
            )
            self._async_context.set(context)
            self._active_contexts.add(context)

        return context

    def _get_context(self) -> IndentContext:
        """Get the appropriate context based on sync/async detection.

        Caches the _is_async_context() result per-thread with a ~50ms TTL
        to avoid calling asyncio.get_running_loop() multiple times per
        decorated function invocation.
        """
        now = _time.monotonic()
        cached_time = getattr(self._async_check_cache, "time", 0.0)
        if now - cached_time > 0.05:
            self._async_check_cache.result = HAS_CONTEXTVARS and self._is_async_context()
            self._async_check_cache.time = now

        if self._async_check_cache.result:
            return self._get_async_context()
        else:
            return self._get_thread_context()

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the indent manager with global settings.

        Args:
            config: Configuration dictionary from LogEverything
        """
        self._config = config.copy()
        # Clear cache when configuration changes
        self._indent_cache.clear()
        # Pre-cache config values for fast access
        self._cfg_visual_mode = config.get("visual_mode", False)
        self._cfg_use_indent = config.get("use_indent", False)
        self._cfg_use_symbols = config.get("use_symbols", False)
        self._cfg_force_ascii = config.get("force_ascii", False)
        self._cfg_indent_level = config.get("indent_level", 2)
        self._cfg_beautify = config.get("beautify", True)

    def get_level(self) -> int:
        """
        Get current indentation level.

        Returns:
            Current indentation level (integer)
        """
        return self._get_context().level

    def increment(self) -> int:
        """
        Increment indentation level.

        Returns:
            New indentation level
        """
        context = self._get_context()
        context.level += 1
        return context.level

    def decrement(self) -> int:
        """
        Decrement indentation level.

        Returns:
            New indentation level
        """
        context = self._get_context()
        if context.level > 0:
            context.level -= 1
        return context.level

    def reset(self) -> None:
        """Reset indentation level to 0."""
        context = self._get_context()
        context.level = 0
        context.call_stack = []

    def push_call(self, call_id: str) -> None:
        """Push a call ID onto the call stack for hierarchy tracking."""
        context = self._get_context()
        context.call_stack.append(call_id)

    def pop_call(self) -> Optional[str]:
        """Pop and return the top call ID from the call stack."""
        context = self._get_context()
        if context.call_stack:
            return context.call_stack.pop()
        return None

    def current_call_id(self) -> Optional[str]:
        """Get the current (top) call ID without removing it."""
        context = self._get_context()
        if context.call_stack:
            return context.call_stack[-1]
        return None

    def parent_call_id(self) -> Optional[str]:
        """Get the parent (second-to-top) call ID without removing it."""
        context = self._get_context()
        if len(context.call_stack) >= 2:
            return context.call_stack[-2]
        return None

    def get_indent_string(
        self,
        level: Optional[int] = None,
        visual_mode: Optional[bool] = None,
        use_indent: Optional[bool] = None,
        use_symbols: Optional[bool] = None,
        force_ascii: Optional[bool] = None,
        indent_level: Optional[int] = None,
    ) -> str:
        """
        Get formatted indentation string.

        Args:
            level: Override indentation level (uses current if None)
            visual_mode: Enable visual mode formatting
            use_indent: Enable indentation in visual mode
            use_symbols: Enable symbol-based indentation
            force_ascii: Force ASCII characters
            indent_level: Base indent level (spaces per level)

        Returns:
            Formatted indentation string
        """
        context = self._get_context()

        # Use provided values or fall back to pre-cached config attributes
        if level is None:
            level = context.level
        if level == 0 or not self._cfg_beautify:
            return ""
        if visual_mode is None:
            visual_mode = self._cfg_visual_mode
        if use_indent is None:
            use_indent = self._cfg_use_indent
        if use_symbols is None:
            use_symbols = context.use_symbols
            if use_symbols is None:
                use_symbols = self._cfg_use_symbols
        if force_ascii is None:
            force_ascii = self._cfg_force_ascii
        if indent_level is None:
            indent_level = self._cfg_indent_level

        # Quick path for no indentation (already checked above)
        if level == 0:
            return ""

        # Create cache key
        cache_key = (level, visual_mode, use_indent, use_symbols, force_ascii, indent_level)

        # Check cache first
        if cache_key in self._indent_cache:
            return self._indent_cache[cache_key]

        # Generate indent string
        if visual_mode and use_indent:
            # Visual mode with indentation - increased spacing for better clarity
            if force_ascii:
                indent_char = "|    "  # Increased from "|   " to "|    "
            elif use_symbols:
                # When use_symbols=True, use plain spaces to avoid redundancy
                # with hierarchical symbols (┌─►, └─◄, etc.)
                indent_char = "     "  # Increased from "    " to "     "
            else:
                # Use visual arrows when not using symbols
                indent_char = "   ▶ "  # Increased from "  ▶ " to "   ▶ "

            indent_str = indent_char * level
        else:
            # Standard space-based indentation - increased from 2 to 3 spaces per level
            indent_str = " " * (level * (indent_level + 1))

        # Cache the result
        self._indent_cache[cache_key] = indent_str
        return indent_str

    @contextmanager
    def context(self, levels: int = 1):
        """
        Context manager for temporary indentation level changes.

        Args:
            levels: Number of levels to increment (can be negative)

        Example:
            with indent_manager.context(2):
                # Code here is indented 2 levels deeper
                log_something()
        """
        original_level = self.get_level()

        try:
            # Apply the level change
            context = self._get_context()
            context.level += levels
            yield self
        finally:
            # Restore original level
            context = self._get_context()
            context.level = original_level

    def set_visual_preferences(
        self,
        use_symbols: Optional[bool] = None,
        visual_mode: Optional[bool] = None,
        use_indent: Optional[bool] = None,
        force_ascii: Optional[bool] = None,
    ) -> None:
        """
        Set visual formatting preferences for current context.

        Args:
            use_symbols: Whether to use Unicode symbols
            visual_mode: Enable visual mode
            use_indent: Enable indentation in visual mode
            force_ascii: Force ASCII characters
        """
        context = self._get_context()

        if use_symbols is not None:
            context.use_symbols = use_symbols
        if visual_mode is not None:
            context.visual_mode = visual_mode
        if use_indent is not None:
            context.use_indent = use_indent
        if force_ascii is not None:
            context.force_ascii = force_ascii

    def get_execution_id(self) -> str:
        """
        Get unique execution identifier for current context.

        Returns:
            Unique execution ID string
        """
        context = self._get_context()
        cached = context.execution_id_str
        if cached is not None:
            return cached
        # Fallback for contexts created before caching was added
        process_id = os.getpid()
        thread_id = threading.get_ident()
        isolation_id = context.isolation_id or 0
        context.execution_id_str = f"{process_id}-{thread_id}-{isolation_id}"
        return context.execution_id_str

    def decorator_enter(self, call_id: str) -> Tuple[str, IndentContext]:
        """Compound: get_indent_string + push_call + increment. Single context lookup.

        Used by decorators to replace three separate calls (each doing _get_context())
        with a single context lookup.

        Args:
            call_id: Unique call identifier for hierarchy tracking

        Returns:
            Tuple of (indent_string, context)
        """
        context = self._get_context()
        # get_indent_string inline (uses context.level before increment)
        indent_str = self.get_indent_string(level=context.level)
        # push_call inline
        context.call_stack.append(call_id)
        # increment inline
        context.level += 1
        return indent_str, context

    def decorator_exit(self) -> None:
        """Compound: decrement + pop_call. Single context lookup.

        Used by decorators to replace two separate calls (each doing _get_context())
        with a single context lookup.
        """
        context = self._get_context()
        if context.level > 0:
            context.level -= 1
        if context.call_stack:
            context.call_stack.pop()

    def get_hierarchy_snapshot(self) -> Tuple[int, str, str, str]:
        """Return hierarchy fields with a single context lookup.

        Used by HierarchyFilter to replace 4 separate method calls
        (get_level, current_call_id, parent_call_id, get_execution_id)
        each doing _get_context(), with a single lookup.

        Returns:
            Tuple of (level, call_id, parent_call_id, execution_id)
        """
        context = self._get_context()
        level = context.level
        call_id = context.call_stack[-1] if context.call_stack else ""
        parent_call_id = context.call_stack[-2] if len(context.call_stack) >= 2 else ""
        # Use cached execution_id
        execution_id = context.execution_id_str
        if execution_id is None:
            execution_id = f"{os.getpid()}-{threading.get_ident()}-{context.isolation_id or 0}"
            context.execution_id_str = execution_id
        return level, call_id, parent_call_id, execution_id

    def cleanup(self) -> None:
        """Clean up cached data and contexts."""
        self._indent_cache.clear()

        # Clean up thread-local storage
        try:
            if hasattr(self._thread_local, "context"):
                delattr(self._thread_local, "context")
        except AttributeError:
            pass

    # Backward compatibility methods
    def increment_indent(self) -> None:
        """Backward compatibility: increment indentation."""
        self.increment()

    def decrement_indent(self) -> None:
        """Backward compatibility: decrement indentation."""
        self.decrement()

    def increment_async_indent(self) -> int:
        """Backward compatibility: increment async indentation."""
        return self.increment()

    def decrement_async_indent(self) -> int:
        """Backward compatibility: decrement async indentation."""
        return self.decrement()

    def get_async_indent(self) -> int:
        """Backward compatibility: get async indentation level."""
        return self.get_level()

    def get_current_indent(self) -> str:
        """Backward compatibility: get current indentation string."""
        return self.get_indent_string()


# Global instance
_indent_manager = IndentManager()


# Export functions for backward compatibility
def configure_indent_manager(config: Dict[str, Any]) -> None:
    """Configure the global indent manager."""
    _indent_manager.configure(config)


def get_indent_manager() -> IndentManager:
    """Get the global indent manager instance."""
    return _indent_manager


def increment_indent() -> None:
    """Increment indentation level."""
    _indent_manager.increment()


def decrement_indent() -> None:
    """Decrement indentation level."""
    _indent_manager.decrement()


def get_current_indent() -> str:
    """Get current indentation string."""
    return _indent_manager.get_indent_string()


def increment_async_indent() -> int:
    """Increment async indentation level."""
    return _indent_manager.increment()


def decrement_async_indent() -> int:
    """Decrement async indentation level."""
    return _indent_manager.decrement()


def get_async_indent() -> int:
    """Get async indentation level."""
    return _indent_manager.get_level()


def reset_indent() -> None:
    """Reset indentation level to 0."""
    _indent_manager.reset()


def get_indent_level() -> int:
    """Get current indentation level."""
    return _indent_manager.get_level()


def set_visual_preferences(**kwargs) -> None:
    """Set visual formatting preferences."""
    _indent_manager.set_visual_preferences(**kwargs)


# Context manager for temporary indentation
def indent_context(levels: int = 1):
    """Context manager for temporary indentation."""
    return _indent_manager.context(levels)
