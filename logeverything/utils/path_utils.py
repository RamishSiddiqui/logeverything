"""
Path utility functions for the LogEverything library.
"""

import os
from typing import Dict, Optional

# Cache for get_relative_path() with default base_path (most common hot path).
# Bounded to 500 entries to prevent unbounded growth; cleared on overflow.
_relative_path_cache: Dict[str, str] = {}


def get_relative_path(absolute_path: str, base_path: Optional[str] = None) -> str:
    """
    Convert an absolute path to a relative path for cleaner log output.

    Args:
        absolute_path: The absolute file path
        base_path: Optional base path to calculate relative path from.
                  If None, uses current working directory.

    Returns:
        str: Relative path from base directory, or just filename if outside base
    """
    # Fast path: check cache for default base_path case (most common in decorators)
    if base_path is None:
        cached = _relative_path_cache.get(absolute_path)
        if cached is not None:
            return cached

    try:
        # Convert to string if it's not already (handles Mock objects in tests)
        if not isinstance(absolute_path, str):
            absolute_path = str(absolute_path)  # type: ignore[unreachable]

        # Use provided base path or current working directory
        if base_path is None:
            base_path = os.getcwd()

        # Try to get relative path from base directory
        rel_path = os.path.relpath(absolute_path, base_path)

        # If the relative path starts with many "../", just use the filename
        if rel_path.startswith(".."):
            result = os.path.basename(absolute_path)
        else:
            result = rel_path

    except (ValueError, OSError, TypeError):
        # Fallback to just the filename if relpath fails
        result = os.path.basename(str(absolute_path))

    # Cache the result for default base_path case
    if base_path is None or base_path == os.getcwd():
        if len(_relative_path_cache) > 500:
            _relative_path_cache.clear()
        _relative_path_cache[absolute_path] = result

    return result


def get_filename_only(path: str) -> str:
    """
    Get just the filename from a path (cross-platform).

    Args:
        path: The file path

    Returns:
        str: Just the filename part
    """
    return os.path.basename(path)
