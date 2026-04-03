# Changelog

All notable changes to LogEverything will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2](https://github.com/RamishSiddiqui/logeverything/compare/v0.1.1...v0.1.2) (2026-04-03)


### Bug Fixes

* add environment release for PyPI trusted publishing ([2bd0c31](https://github.com/RamishSiddiqui/logeverything/commit/2bd0c313d3ec4ad57b5f41f57ae1d19845495e5c))
* add release environment and trigger build via whitespace update ([9a724e7](https://github.com/RamishSiddiqui/logeverything/commit/9a724e72783514d6deae82b0f42671c47b607439))

## [0.1.1](https://github.com/RamishSiddiqui/logeverything/compare/v0.1.0...v0.1.1) (2026-04-03)


### Bug Fixes

* setup release please and trigger v0.1.1 ([#3](https://github.com/RamishSiddiqui/logeverything/issues/3)) ([9007dad](https://github.com/RamishSiddiqui/logeverything/commit/9007dad96c5e38428918d8c18c3021b5ba41b751))


### Documentation

* Update badges in index.rst to use correct GitHub repo and branch ([d41551c](https://github.com/RamishSiddiqui/logeverything/commit/d41551c1d0aa6af601a3c569faae5370811e0f6f))

## [Unreleased]

### Added
- **Monitoring dashboard** — Multi-page web dashboard (Overview, Logs, Operations, System) with sidebar navigation, hierarchical log tree view, pagination, filtering, dark/light themes, and real-time WebSocket updates
- **Remote logging guide** — End-to-end documentation for shipping logs to the dashboard via HTTP transport
- **`JSONLineFormatter`** — A `logging.Formatter` that produces dashboard-compatible JSON Lines output; works with any handler including rotation handlers
- **Rotated JSONL file discovery** — Dashboard Local Connection mode now reads both active (`*.jsonl`) and rotated (`*.jsonl.*`) log files automatically

### Performance
- **2x faster `@log_function` decorator** (2,500 ops/sec / 0.40ms vs 1,208 ops/sec / 0.83ms previously)
  - Cached monitoring module import — eliminated per-call `importlib` overhead (was 37% of decorator time)
  - TTL-cached async context detection — `_is_async_context()` result cached per-thread with 50ms TTL, reducing 5 `asyncio.get_running_loop()` calls per invocation to ~1
  - Cached `get_relative_path()` — bounded dict cache avoids repeated `os.path.relpath()` for the same source file
  - Disabled stdlib `findCaller` stack walk — decorators already compute source info, so the redundant stack walk is skipped
- **Reduced `_get_context()` calls from 13 to 4 per decorated function**
  - Compound `IndentManager.decorator_enter()` / `decorator_exit()` methods replace 5 separate calls (get_indent_string + push_call + increment / decrement + pop_call) with 2, each doing a single context lookup
  - Compound `IndentManager.get_hierarchy_snapshot()` replaces 4 separate `HierarchyFilter` calls (get_level, current_call_id, parent_call_id, get_execution_id) with 1
- **Cached `execution_id` per thread** — `os.getpid()` + `threading.get_ident()` + f-string formatting computed once at context creation instead of per log record
- **`PrettyFormatter.formatTime()` cache** — Same-second log records reuse the formatted timestamp string, eliminating redundant `time.localtime()` + `time.strftime()` calls
- **In-place record modification in `PrettyFormatter.format()`** — Avoids `logging.makeLogRecord(record.__dict__)` copy per record; saves/restores fields directly
- **Pre-computed `_SERIALIZABLE_TYPES` tuple** in `JSONHandler` and `JSONLineFormatter` — avoids rebuilding the isinstance check tuple on every `emit()`/`format()` call
- **Monotonic counter for call IDs** — `generate_call_id()` uses `itertools.count()` + thread ident instead of `os.urandom(6).hex()`, eliminating syscall overhead

## [0.2.0] - 2026-02-23

### Added
- **`TimedRotatingFileHandler`** — Time-based rotation (midnight, hourly, weekly) with gzip compression and configurable retention
- **`compress` parameter on `FileHandler`** — Gzip compression of size-rotated log files
- **CLI tool** — `logeverything version`, `logeverything doctor`, `logeverything init` commands; also available via `python -m logeverything`
- **Fuzzy-match error messages** — Decorator `using=` lookup now suggests close matches with "Did you mean?" when a logger name is not found
- **Benchmark CI job** — GitHub Actions runs benchmarks after tests and compares against baseline thresholds stored in `benchmarks/baseline.json`
- **Structured hierarchy fields** — `HierarchyFilter` injects `indent_level`, `call_id`, `parent_call_id`, `log_type`, and `execution_id` into every log record for downstream consumers
- **Call stack tracking** in `IndentManager` — `push_call()` / `pop_call()` maintain a per-context call stack alongside indent levels
- **`py.typed` marker** — PEP 561 support for downstream type checkers
- **Transport test suite** — Buffer (100%), HTTP (91%), TCP (83%), UDP (64%) coverage
- **Monitoring storage test suite** — Init, CRUD, cleanup, thread-safety tests
- **Integration pipeline test** — Logger → HTTPTransport → payload verification end-to-end test
- **Rotation handler tests** — Timed rollover, retention, compression
- **CLI tests** — Version, doctor, module invocation (`python -m logeverything`)

### Removed
- 7 empty monitoring stubs (`cli.py`, `config.py`, `dashboard_server.py`, `data_storage.py`, `metrics_collector.py`, `operation_tracker.py`, `websocket_server.py`) and `monitoring/fastapi_dashboard/` directory

### Fixed
- **`py.typed`** now correctly included in wheel via `[options.package_data]` in `setup.cfg`
- **Windows Unicode Support**: Fixed UnicodeEncodeError on Windows console when using visual formatting with Unicode symbols
  - FileHandler now defaults to UTF-8 encoding instead of system default (cp1252)
  - Logger.configure() file handler creation now explicitly uses UTF-8 encoding
  - Core setup_logging() function now creates file handlers with UTF-8 encoding
  - Enhanced ConsoleHandler and FileHandler with comprehensive Unicode error handling and ASCII fallback
  - Automatic symbol replacement for non-Unicode terminals
  - Zero configuration required — works out-of-the-box on all Windows systems
- Bug in environment detection where notebook detection wasn't properly prioritized
- Issue with VisualLoggingContext not correctly applying visual mode settings

### Changed
- Tests: 314 → 379 passing
- Coverage: 56% → 65%

## [1.0.0] - Unreleased (Future)

### 🔄 MAJOR: Complete API Modernization
- **Complete codebase modernization** — LogEverything uses its own logger interface throughout
- **Drop-in replacement** — No longer depends on Python's logging module for core functionality
- **Unified smart decorator** — Single `@log` decorator that automatically detects functions, classes, and async code
- **Own level constants** — `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` constants provided by LogEverything
- **Own logger interface** — `get_logger()` function returns LogEverything's own logger instances
- **Smart context detection** — Automatically adapts behavior based on what it's decorating
- **Backward compatibility** — Old API (`log_function`, `log_class`, `log_io`) still works but deprecated

### 🚀 Performance Improvements (Continued)
- **53x faster print capture** (216,558 ops/sec vs 4,055 previously)
- **6.8x faster async logging** (265-301 ops/sec vs 39.73 previously)
- **1.55x faster async queue handler** (11,111 ops/sec vs 7,182 previously)
- **Optimized smart decorator** with intelligent caching and lazy evaluation
- **Fast-path execution** when logging is disabled for zero overhead

### 🛡️ Enhanced Isolation & Safety
- **Automatic thread isolation** — Zero-configuration thread safety
- **Async task isolation** — Context-aware async task separation using contextvars
- **Smart activation** — Isolation only activates when concurrent execution detected
- **Thread leak detection** — Built-in detection and prevention of thread leaks

### 🔧 New Features
- **AsyncLogger class** — Optimized for async applications with 6.8x performance improvement
- **Async-specific methods** — `ainfo()`, `adebug()`, `aexception()` methods for optimal async performance
- **Async context managers** — `async with log.context()` for hierarchical async logging
- **Built-in task isolation** — Automatic async task isolation prevents logging contamination
- **Smart decorator API** — `@log` works on functions, classes, methods, and async functions automatically
- **Logger registry** — Automatic registration and discovery with `using="logger_name"` parameter
- **Correlation IDs** — Request-scoped correlation with framework middleware
- **Log transports** — HTTP, TCP, UDP transports for shipping logs to remote collectors

### 📚 Documentation Updates
- Comprehensive Sphinx documentation with Furo theme
- AsyncLogger documentation with migration guides
- Dashboard guide with screenshots
- Remote logging end-to-end guide
- API reference for all modules

### 🐛 Bug Fixes
- **Test isolation** — Fixed test interference issues between test runs
- **Async handler cleanup** — Proper cleanup of async handlers to prevent leaks
- **Logger name prefixing** — Consistent logger naming across all modules
- **Color/symbol handling** — Fixed formatter color and symbol parameter handling
- **Import consistency** — All imports now use LogEverything's interfaces

### ⚠️ Breaking Changes
- **Recommended API change** — While old API still works, new `@log` decorator is strongly recommended
- **Level constants** — Recommended to use LogEverything's constants instead of logging module constants
- **Logger interface** — Recommended to use LogEverything's `get_logger()` instead of `logging.getLogger()`

### 🔄 Migration Path
```python
# Old way (still works but deprecated)
from logeverything import log_function, log_class
from logeverything.async_logging import async_log_function
import logging

@log_function
def func(): pass

@async_log_function  # Deprecated
async def async_func(): pass

# New way (recommended)
from logeverything import log, Logger, AsyncLogger, DEBUG, INFO

@log  # Works on everything!
def func(): pass

# For async applications - two options:
# Option 1: AsyncLogger class (recommended for async apps)
async def main():
    log = AsyncLogger("my_app")
    await log.ainfo("Async logging")
    await log.close()

# Option 2: Decorator approach (works for mixed sync/async)
@log
async def async_func(): pass

logger = Logger(__name__)  # LogEverything's interface
```

## [0.4.0] - 2025-06-21

### 🚀 Performance Improvements
- **53x faster print capture** (0.2466ms → 0.0046ms per operation, ~216,558 ops/sec)
  - Optimized logger caching with intelligent isolation
  - Fast-path execution for silent mode
  - Reduced string operation overhead
- **6.8x faster async logging** with non-blocking queue handlers
  - Async contextvars for proper isolation
  - Worker thread management for background processing
  - Optimized queue buffering and flush intervals
- **Core logging optimizations** with less than 1ms overhead per function call
  - Cached function metadata and logger instances
  - Optimized string building and concatenation
  - Lazy evaluation of expensive operations

### 🔒 Automatic Isolation
- **Smart isolation detection** — automatically enables isolation only in concurrent environments
- **Thread-safe context isolation** — each thread gets its own logging context
- **Process-safe isolation** — multiprocess applications maintain separate states
- **Print capture isolation** — prevents cross-contamination between threads
- **Logger cache isolation** — concurrent threads get separate logger instances
- **Zero configuration required** — works transparently without setup

### 🛠️ Internal Improvements
- Enhanced error handling and cleanup in async queue handlers
- Improved thread leak detection and prevention
- Better memory management for isolation contexts
- Optimized context variable usage in async environments
- Comprehensive test coverage for isolation scenarios

### 🧪 Testing & Quality
- All 226 tests passing with 84% code coverage
- Fixed test isolation issues that were affecting test reliability
- Enhanced benchmarking suite for performance validation
- Added concurrent usage testing and validation

### 📖 Documentation
- Added comprehensive Performance & Isolation guide
- Updated README with performance metrics and isolation examples
- Enhanced API documentation with isolation behavior
- Migration guide for upgrading from v0.3.x

## [0.3.0] - 2025-06-01

### Added
- Configuration simplification with environment auto-detection
- Optional dependencies with specialized extras (`pip install logeverything[fastapi]`)
- Smart unified `@log` decorator that auto-detects function/method/class type
- Configuration profiles (development, production, minimal)
- Top-level imports simplification
- Context managers: `LoggingContext`, `VerboseLoggingContext`, `QuietLoggingContext`, `VisualLoggingContext`, `TemporaryHandlerContext`

### Changed
- Core API simplified with consistent naming patterns
- Improved documentation with better examples
- Reduced configuration complexity

### Fixed
- Improved handling of optional dependencies
- Fixed environment detection edge cases
- Ensured profiles work correctly with auto-detection

## [0.2.0-alpha] - 2025-05-26

### Added
- Performance optimizations for reducing logging overhead
- Logger caching for improved performance
- Indentation string caching for faster log formatting
- Special optimized paths for test functions

### Changed
- Improved JSONHandler implementation for better handling of extra attributes
- Optimized log_function decorator with early exit paths
- Reduced overhead of logging by >90% in high-frequency calls
- Improved thread-local initialization to reduce overhead

### Fixed
- JSONHandler now properly stores extra attributes in the "extra" dictionary
- Fixed performance issues in logging overhead
- Fixed thread context initialization to avoid redundant operations

## [0.1.0] - 2025-04-15

### Added
- Core logging framework with thread and process safety
- Function logging decorators (`@log_function`, `@log_io`)
- Class logging decorator (`@log_class`)
- Multiple output handlers: ConsoleHandler, FileHandler, JSONHandler
- Hierarchical function call tracking with indentation
- Performance monitoring capabilities
- Cross-platform support (Windows, macOS, Linux)
