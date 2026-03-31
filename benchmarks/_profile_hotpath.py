"""
Profile the LogEverything decorator hot path.

Uses cProfile to identify bottlenecks in @log_function decorator overhead
by running 1000 calls against a file-only logger (no console output).

Usage:
    .venv/Scripts/python.exe benchmarks/_profile_hotpath.py
"""

import cProfile
import os
import pstats
import sys
import tempfile

from logeverything import Logger
from logeverything.decorators import log_function

# ---------------------------------------------------------------------------
# 1. Set up a minimal file-only logger
# ---------------------------------------------------------------------------


# Create a temp file so file I/O is real but we don't clutter the repo
_tmp = tempfile.NamedTemporaryFile(suffix=".log", delete=False, prefix="le_profile_")
LOG_FILE = _tmp.name
_tmp.close()

logger = Logger("hotpath_bench", auto_setup=False)
logger.configure(
    level="DEBUG",
    handlers=["file"],
    file_path=LOG_FILE,
    visual_mode=False,
    use_symbols=False,
)

# ---------------------------------------------------------------------------
# 2. Decorated target function (intentionally trivial so overhead dominates)
# ---------------------------------------------------------------------------


@log_function(using="hotpath_bench")
def add(a: int, b: int) -> int:
    """Trivial function -- all measured time is decorator overhead."""
    return a + b


# ---------------------------------------------------------------------------
# 3. Warm up (let caches and lazy imports settle)
# ---------------------------------------------------------------------------
for _ in range(5):
    add(0, 0)

# ---------------------------------------------------------------------------
# 4. Profile 1000 calls
# ---------------------------------------------------------------------------
NUM_CALLS = 1000

print(f"Profiling {NUM_CALLS} calls to @log_function-decorated `add()`")
print(f"Log output -> {LOG_FILE}")
print("=" * 80)

profiler = cProfile.Profile()
profiler.enable()

for i in range(NUM_CALLS):
    add(i, i + 1)

profiler.disable()

# ---------------------------------------------------------------------------
# 5. Print top 30 by tottime
# ---------------------------------------------------------------------------
stats = pstats.Stats(profiler, stream=sys.stdout)
stats.strip_dirs()
stats.sort_stats("tottime")
print("\n--- Top 30 by tottime ---\n")
stats.print_stats(30)

# Also show cumulative view for the wrapper entry points
print("\n--- Top 30 by cumulative time ---\n")
stats.sort_stats("cumulative")
stats.print_stats(30)

# Cleanup
try:
    os.unlink(LOG_FILE)
except OSError:
    pass

print(f"\nDone. Temp log file removed: {LOG_FILE}")
