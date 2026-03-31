Performance and Optimization
============================

LogEverything is designed for high-performance logging with minimal overhead. This guide covers performance optimization techniques, benchmarking, and best practices for production environments.

Performance Overview
--------------------

LogEverything achieves high performance through:

- **Lazy Evaluation**: Messages are formatted only when necessary
- **Efficient Buffering**: Smart buffering reduces I/O operations
- **Async Operations**: Non-blocking logging for async applications
- **Minimal Allocations**: Optimized memory usage patterns
- **Fast Filtering**: Early filtering of messages below threshold levels

Benchmarking
------------

Basic Performance Test
~~~~~~~~~~~~~~~~~~~~~~

Compare LogEverything with standard library logging:

.. code-block:: python

    import time
    import logging
    from logeverything import Logger

    def benchmark_stdlib():
        """Benchmark standard library logging"""
        logger = logging.getLogger('test')
        logger.setLevel(logging.INFO)

        start = time.time()
        for i in range(100000):
            logger.info(f"Message {i}")
        end = time.time()

        return end - start

    def benchmark_logeverything():
        """Benchmark LogEverything"""
        logger = Logger()

        start = time.time()
        for i in range(100000):
            logger.info(f"Message {i}")
        end = time.time()

        return end - start

    # Run benchmarks
    stdlib_time = benchmark_stdlib()
    logeverything_time = benchmark_logeverything()

    print(f"Standard library: {stdlib_time:.2f}s")
    print(f"LogEverything: {logeverything_time:.2f}s")
    print(f"Speedup: {stdlib_time / logeverything_time:.2f}x")

Async Performance Test
~~~~~~~~~~~~~~~~~~~~~~

Test async logging performance:

.. code-block:: python

    import asyncio
    import time
    from logeverything import AsyncLogger

    async def benchmark_async_logging():
        """Benchmark async logging performance"""
        logger = AsyncLogger()

        start = time.time()

        # Create many concurrent logging tasks
        tasks = []
        for i in range(1000):
            tasks.append(logger.info(f"Async message {i}"))

        await asyncio.gather(*tasks)

        end = time.time()
        return end - start

    # Run async benchmark
    async_time = asyncio.run(benchmark_async_logging())
    print(f"Async logging time: {async_time:.2f}s")

Memory Usage Analysis
~~~~~~~~~~~~~~~~~~~~~

Monitor memory usage during logging:

.. code-block:: python

    import tracemalloc
    from logeverything import Logger

    def memory_benchmark():
        """Analyze memory usage"""
        tracemalloc.start()

        logger = Logger()

        # Take initial snapshot
        snapshot1 = tracemalloc.take_snapshot()

        # Perform logging
        for i in range(10000):
            logger.bind(extra={"index": i}).info(f"Memory test message {i}")

        # Take final snapshot
        snapshot2 = tracemalloc.take_snapshot()

        # Analyze differences
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')

        print("Memory usage analysis:")
        for stat in top_stats[:10]:
            print(stat)

    memory_benchmark()

Optimization Techniques
-----------------------

Lazy Formatting
~~~~~~~~~~~~~~~

Use lazy formatting to avoid string operations when messages are filtered:

.. code-block:: python

    from logeverything import Logger

    logger = Logger(level="INFO")  # DEBUG messages will be filtered

    # Inefficient: String formatting happens even when filtered
    expensive_data = get_expensive_data()
    logger.debug(f"Debug data: {expensive_data}")  # Formatted but filtered

    # Efficient: Use lambda for lazy evaluation
    logger.debug(lambda: f"Debug data: {get_expensive_data()}")  # Not evaluated when filtered

    # Efficient: Use extra data
    logger.bind(extra={"data": lambda: get_expensive_data().debug("Debug data available")})

Efficient Message Construction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Build messages efficiently:

.. code-block:: python

    from logeverything import Logger

    logger = Logger()

    # Inefficient: Multiple string concatenations
    def log_user_activity_slow(user_id, action, details):
        message = "User " + str(user_id) + " performed " + action
        if details:
            message += " with details: " + str(details)
        logger.info(message)

    # Efficient: Use f-strings and structured data
    def log_user_activity_fast(user_id, action, details):
        logger.bind(extra={
            "user_id": user_id,
            "action": action,
            "details": details
        }).info(f"User {user_id} performed {action}")

    # Benchmark the difference
    import time

    start = time.time()
    for i in range(10000):
        log_user_activity_slow(i, "login", {"ip": "192.168.1.1"})
    slow_time = time.time() - start

    start = time.time()
    for i in range(10000):
        log_user_activity_fast(i, "login", {"ip": "192.168.1.1"})
    fast_time = time.time() - start

    print(f"Slow method: {slow_time:.2f}s")
    print(f"Fast method: {fast_time:.2f}s")
    print(f"Speedup: {slow_time / fast_time:.2f}x")

Buffering Configuration
~~~~~~~~~~~~~~~~~~~~~~~

Optimize buffering for your use case:

.. code-block:: python

    from logeverything import Logger

    # High-throughput configuration
    high_throughput_logger = Logger(
        buffer_size=10000,        # Large buffer
        flush_interval=5.0,       # Flush every 5 seconds
        async_writing=True        # Use async I/O
    )

    # Low-latency configuration
    low_latency_logger = Logger(
        buffer_size=1,            # No buffering
        flush_interval=0,         # Immediate flush
        async_writing=False       # Synchronous I/O
    )

    # Balanced configuration
    balanced_logger = Logger(
        buffer_size=1000,         # Moderate buffer
        flush_interval=1.0,       # Flush every second
        async_writing=True        # Async I/O for better performance
    )

Level-Based Optimization
~~~~~~~~~~~~~~~~~~~~~~~~

Optimize based on log levels:

.. code-block:: python

    from logeverything import Logger

    logger = Logger(level="INFO")

    # Check level before expensive operations
    if logger.is_debug_enabled():
        expensive_debug_data = perform_expensive_calculation()
        logger.debug(f"Debug data: {expensive_debug_data}")

    # Use level guards for complex formatting
    if logger.is_level_enabled("DEBUG"):
        complex_message = format_complex_debug_message()
        logger.debug(complex_message)

Async Optimization
------------------

Async Logger Performance
~~~~~~~~~~~~~~~~~~~~~~~~

Optimize async logging patterns:

.. code-block:: python

    import asyncio
    from logeverything import AsyncLogger

    async def optimized_async_logging():
        logger = AsyncLogger(
            buffer_size=5000,         # Large buffer for async
            batch_size=100,           # Process in batches
            queue_size=10000          # Large queue for high throughput
        )

        # Batch logging operations
        messages = [f"Message {i}" for i in range(1000)]

        # Efficient: Use gather for concurrent logging
        await asyncio.gather(*[
            logger.info(msg) for msg in messages
        ])

        # Efficient: Use create_task for fire-and-forget
        tasks = [
            asyncio.create_task(logger.info(msg))
            for msg in messages
        ]

        # Wait for completion
        await asyncio.gather(*tasks)

Background Processing
~~~~~~~~~~~~~~~~~~~~~

Use background tasks for heavy logging operations:

.. code-block:: python

    import asyncio
    from logeverything import AsyncLogger

    class BackgroundLogger:
        def __init__(self):
            self.logger = AsyncLogger()
            self.queue = asyncio.Queue(maxsize=10000)
            self.processor_task = None

        async def start(self):
            """Start background processing"""
            self.processor_task = asyncio.create_task(self._process_queue())

        async def stop(self):
            """Stop background processing"""
            await self.queue.put(None)  # Sentinel value
            if self.processor_task:
                await self.processor_task

        async def log(self, level, message, **kwargs):
            """Queue log message for background processing"""
            try:
                await self.queue.put((level, message, kwargs))
            except asyncio.QueueFull:
                # Handle queue full scenario
                await self.logger.warning("Log queue full, dropping message")

        async def _process_queue(self):
            """Background processor"""
            while True:
                item = await self.queue.get()
                if item is None:  # Sentinel value
                    break

                level, message, kwargs = item

                # Process log message
                if level == "info":
                    await self.logger.info(message, **kwargs)
                elif level == "error":
                    await self.logger.error(message, **kwargs)
                # ... other levels

                self.queue.task_done()

    # Usage
    async def main():
        bg_logger = BackgroundLogger()
        await bg_logger.start()

        # Fast, non-blocking logging
        await bg_logger.log("info", "Fast message")
        await bg_logger.log("error", "Error message")

        await bg_logger.stop()

    asyncio.run(main())

Production Optimization
-----------------------

Configuration for Production
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Optimize configuration for production environments:

.. code-block:: python

    from logeverything import Logger, Profile

    # Production profile with optimizations
    production_profile = Profile(
        name="production_optimized",
        level="INFO",                    # Filter debug messages
        format='{"timestamp":"{timestamp}","level":"{level}","message":"{message}"}',
        include_caller=False,            # Disable caller info for performance
        include_stack_trace=False,       # Disable stack traces
        buffer_size=10000,              # Large buffer
        flush_interval=5.0,             # Batch writes
        compress_logs=True,             # Compress log files
        rotate_logs=True,               # Enable log rotation
        max_file_size="100MB",          # Rotate at 100MB
        backup_count=10                 # Keep 10 backup files
    )

    logger = Logger(profile=production_profile)

Resource Monitoring
~~~~~~~~~~~~~~~~~~~

Monitor logging resource usage:

.. code-block:: python

    import psutil
    import threading
    import time
    from logeverything import Logger

    class ResourceMonitor:
        def __init__(self, logger):
            self.logger = logger
            self.monitoring = False
            self.monitor_thread = None

        def start_monitoring(self):
            """Start resource monitoring"""
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor)
            self.monitor_thread.start()

        def stop_monitoring(self):
            """Stop resource monitoring"""
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join()

        def _monitor(self):
            """Monitor resources in background"""
            while self.monitoring:
                # Get current process info
                process = psutil.Process()

                # Memory usage
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024

                # CPU usage
                cpu_percent = process.cpu_percent()

                # File descriptors (Unix only)
                try:
                    fd_count = process.num_fds()
                except AttributeError:
                    fd_count = 0

                # Log resource usage
                self.logger.bind(extra={
                    "memory_mb": memory_mb,
                    "cpu_percent": cpu_percent,
                    "file_descriptors": fd_count
                }).debug("Resource usage")

                time.sleep(60)  # Monitor every minute

    # Usage
    logger = Logger()
    monitor = ResourceMonitor(logger)
    monitor.start_monitoring()

    # Your application code here
    time.sleep(300)  # Run for 5 minutes

    monitor.stop_monitoring()

Memory Management
~~~~~~~~~~~~~~~~~

Manage memory usage in long-running applications:

.. code-block:: python

    from logeverything import Logger
    import gc
    import weakref

    class MemoryEfficientLogger:
        def __init__(self):
            self.logger = Logger()
            self.message_cache = weakref.WeakValueDictionary()
            self.cache_hits = 0
            self.cache_misses = 0

        def log_with_caching(self, level, message_template, **kwargs):
            """Log with message template caching"""
            cache_key = (level, message_template)

            if cache_key in self.message_cache:
                formatted_template = self.message_cache[cache_key]
                self.cache_hits += 1
            else:
                formatted_template = self._format_template(message_template)
                self.message_cache[cache_key] = formatted_template
                self.cache_misses += 1

            # Format final message
            final_message = formatted_template.format(**kwargs)

            # Log the message
            getattr(self.logger, level)(final_message)

        def _format_template(self, template):
            """Format message template"""
            # Expensive formatting operation
            return template.replace("{", "{{").replace("}", "}}")

        def get_cache_stats(self):
            """Get cache performance statistics"""
            total = self.cache_hits + self.cache_misses
            hit_rate = self.cache_hits / total if total > 0 else 0

            return {
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate": hit_rate,
                "cache_size": len(self.message_cache)
            }

        def cleanup_cache(self):
            """Force cache cleanup"""
            gc.collect()
            stats = self.get_cache_stats()
            self.logger.bind(extra=stats).debug("Cache cleanup completed")

High-Throughput Patterns
------------------------

Batch Processing
~~~~~~~~~~~~~~~~

Process logs in batches for better performance:

.. code-block:: python

    from logeverything import Logger
    import threading
    import queue
    import time

    class BatchLogger:
        def __init__(self, batch_size=1000, flush_interval=5.0):
            self.logger = Logger()
            self.batch_size = batch_size
            self.flush_interval = flush_interval
            self.batch = []
            self.batch_lock = threading.Lock()
            self.last_flush = time.time()

        def log(self, level, message, **kwargs):
            """Add log entry to batch"""
            entry = (level, message, kwargs, time.time())

            with self.batch_lock:
                self.batch.append(entry)

                # Check if we should flush
                should_flush = (
                    len(self.batch) >= self.batch_size or
                    time.time() - self.last_flush >= self.flush_interval
                )

                if should_flush:
                    self._flush_batch()

        def _flush_batch(self):
            """Flush current batch"""
            if not self.batch:
                return

            # Process batch
            for level, message, kwargs, timestamp in self.batch:
                getattr(self.logger, level)(message, **kwargs)

            # Clear batch
            self.batch.clear()
            self.last_flush = time.time()

        def flush(self):
            """Manually flush batch"""
            with self.batch_lock:
                self._flush_batch()

    # Usage
    batch_logger = BatchLogger(batch_size=500, flush_interval=2.0)

    # High-volume logging
    for i in range(10000):
        batch_logger.log("info", f"Message {i}")

    # Ensure all messages are flushed
    batch_logger.flush()

Lock-Free Logging
~~~~~~~~~~~~~~~~~

Use lock-free patterns for maximum throughput:

.. code-block:: python

    import threading
    import queue
    from logeverything import Logger

    class LockFreeLogger:
        def __init__(self, num_workers=4):
            self.logger = Logger()
            self.num_workers = num_workers
            self.queues = [queue.Queue() for _ in range(num_workers)]
            self.workers = []
            self.running = True

            # Start worker threads
            for i in range(num_workers):
                worker = threading.Thread(target=self._worker, args=(i,))
                worker.start()
                self.workers.append(worker)

        def log(self, level, message, **kwargs):
            """Distribute log entries across workers"""
            # Use thread ID to select queue (lock-free distribution)
            thread_id = threading.get_ident()
            queue_index = thread_id % self.num_workers

            # Add to queue (thread-safe)
            self.queues[queue_index].put((level, message, kwargs))

        def _worker(self, worker_id):
            """Worker thread for processing log entries"""
            work_queue = self.queues[worker_id]

            while self.running:
                try:
                    level, message, kwargs = work_queue.get(timeout=1.0)
                    getattr(self.logger, level)(message, **kwargs)
                    work_queue.task_done()
                except queue.Empty:
                    continue

        def shutdown(self):
            """Shutdown all workers"""
            self.running = False
            for worker in self.workers:
                worker.join()

    # Usage
    lock_free_logger = LockFreeLogger(num_workers=4)

    # High-concurrency logging
    def worker_function(worker_id):
        for i in range(1000):
            lock_free_logger.log("info", f"Worker {worker_id} message {i}")

    # Start multiple threads
    threads = []
    for i in range(10):
        thread = threading.Thread(target=worker_function, args=(i,))
        thread.start()
        threads.append(thread)

    # Wait for completion
    for thread in threads:
        thread.join()

    lock_free_logger.shutdown()

Profiling and Debugging
-----------------------

Performance Profiling
~~~~~~~~~~~~~~~~~~~~~

Profile logging performance:

.. code-block:: python

    import cProfile
    import pstats
    from logeverything import Logger

    def profile_logging():
        """Profile logging performance"""
        logger = Logger()

        # Create profiler
        profiler = cProfile.Profile()

        # Start profiling
        profiler.enable()

        # Perform logging operations
        for i in range(10000):
            logger.bind(extra={"index": i}).info(f"Performance test message {i}")

        # Stop profiling
        profiler.disable()

        # Analyze results
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(20)  # Show top 20 functions

    profile_logging()

Memory Profiling
~~~~~~~~~~~~~~~~

Profile memory usage:

.. code-block:: python

    from memory_profiler import profile
    from logeverything import Logger

    @profile
    def memory_test():
        """Memory usage profiling"""
        logger = Logger()

        # Test memory usage patterns
        messages = []
        for i in range(1000):
            message = f"Memory test message {i}" * 10  # Larger messages
            logger.info(message)
            messages.append(message)  # Keep references

        # Clear references
        messages.clear()

    memory_test()

Best Practices Summary
----------------------

1. **Use Appropriate Log Levels**: Filter unnecessary messages early
2. **Lazy Evaluation**: Use lambdas for expensive message construction
3. **Structured Logging**: Use extra data instead of string formatting
4. **Buffering**: Configure appropriate buffer sizes for your use case
5. **Async Patterns**: Use AsyncLogger for async applications
6. **Resource Monitoring**: Monitor memory and CPU usage in production
7. **Batch Processing**: Process logs in batches for high throughput
8. **Profiling**: Regular performance profiling in development
9. **Configuration**: Optimize configuration for production environments
10. **Testing**: Performance test under realistic conditions

Performance Checklist
---------------------

Development Phase:
- [ ] Profile logging performance
- [ ] Test with realistic data volumes
- [ ] Optimize message construction
- [ ] Configure appropriate buffering
- [ ] Test async patterns if applicable

Production Deployment:
- [ ] Use production-optimized profiles
- [ ] Monitor resource usage
- [ ] Set up log rotation
- [ ] Configure appropriate log levels
- [ ] Test failover scenarios

Monitoring:
- [ ] Track logging throughput
- [ ] Monitor memory usage
- [ ] Check for log queue backups
- [ ] Verify log delivery
- [ ] Monitor error rates

API Reference
-------------

Performance Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:method:: Logger.__init__(buffer_size=1000, flush_interval=1.0, async_writing=True)

    Initialize logger with performance settings.

    :param buffer_size: Size of the internal buffer
    :type buffer_size: int
    :param flush_interval: Time between buffer flushes
    :type flush_interval: float
    :param async_writing: Enable async I/O
    :type async_writing: bool

.. py:method:: Logger.is_level_enabled(level)
    :no-index:

    Check if a log level is enabled.

    :param level: Log level to check
    :type level: str
    :returns: True if level is enabled
    :rtype: bool

.. py:method:: Logger.get_performance_stats()

    Get performance statistics.

    :returns: Performance metrics
    :rtype: dict
