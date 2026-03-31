# LogEverything Roadmap

> Last updated: February 24, 2026

This document outlines the planned direction for LogEverything. Priorities may shift based on community feedback and contributor interest. Items are grouped by release milestone, ordered roughly by priority within each phase.

Each item includes technical context so any contributor can pick it up and implement it without guessing at intent or approach.

---

## Current State (v0.2.0)

### What's solid

| Area | Details |
|------|---------|
| **Core engine** | `Logger`, `AsyncLogger`, `BaseLogger` ABC, `IndentManager` with thread-local + contextvars |
| **Decorators** | `@log` (smart auto-detect), `@log_function`, `@log_class`, `@log_io` with `using=` param; fuzzy-match "Did you mean?" errors |
| **Handlers** | `ConsoleHandler`, `FileHandler` (with size rotation + gzip), `TimedRotatingFileHandler`, `JSONHandler`, `JSONLineFormatter`, `EnhancedConsoleHandler`, `PrettyFormatter` |
| **Async** | `AsyncLogger`, `AsyncQueueHandler`, async decorators, async context managers with task isolation |
| **Integrations** | FastAPI, Flask, Django, Celery, generic ASGI, generic WSGI middleware |
| **Transports** | HTTP, TCP, UDP handlers with `LogBuffer` (batching, retry, backpressure) |
| **Correlation** | `CorrelationFilter`, `set_correlation_id()`, `propagate_context()` for thread executors |
| **Hierarchy** | `HierarchyFilter` injecting `indent_level`, `call_id`, `parent_call_id`, `log_type`, `execution_id` |
| **Dashboard** | Multi-page web UI (Overview, Logs, Operations, System) with sidebar, tree view, pagination, WebSocket |
| **CLI** | `logeverything version`, `logeverything doctor`, `logeverything init` |
| **Tests** | 395 passing, 65% coverage |
| **Examples** | 64 scripts across 10 categories |

### What's not

- **No cloud integrations** — `setup.cfg` declares `cloud` extras (boto3, google-cloud-logging, azure-monitor) but no handler code exists
- **No structured events** — Logging is string-based; no native dict/event API
- **No OpenTelemetry** — No OTLP export, no trace context bridging
- **No distributed tracing** — Correlation IDs are local; no cross-service propagation protocol

---

## v0.2.0 — Foundation Hardening (Complete)

All v0.2.0 items have been implemented and shipped. Tests: 395 passing, 65% coverage.

### Testing & Quality

- [x] **Transport test suite** — `test_buffer.py` (100%), `test_transport_http.py` (91%), `test_transport_tcp.py` (83%), `test_transport_udp.py` (64%)
- [x] **Storage test suite** — `test_monitoring_storage.py` covering init, CRUD, cleanup, thread-safety
- [x] **Integration test harness** — `test_integration_pipeline.py` verifying Logger -> HTTPTransport -> payload end-to-end
- [x] **Benchmark CI** — GitHub Actions job runs benchmarks after tests, compares against `benchmarks/baseline.json`, fails if any result drops below 80% of baseline

### File Rotation Handlers

- [x] **Size-based rotation with gzip** — `FileHandler` gained `max_size`, `backup_count`, and `compress` parameters
- [x] **`TimedRotatingFileHandler`** — Time-based rotation (`midnight`, `hourly`, `weekly`) with `retention_days` and `compress`
- [x] **Compressed rotation** — Background daemon thread gzips rotated files without blocking the logging path
- [x] **Rotation handler tests** — `test_rotation_handlers.py` covering timed rollover, retention, compression
- [x] **`JSONLineFormatter`** — A `logging.Formatter` that produces dashboard-compatible JSON Lines output; works with any handler including rotation handlers
- [x] **Dashboard rotated file discovery** — Local connections now find both active (`*.jsonl`) and rotated (`*.jsonl.*`) files, including gzipped archives

### Monitoring Module Cleanup

- [x] Deleted 7 empty monitoring stubs (`cli.py`, `config.py`, `dashboard_server.py`, `data_storage.py`, `metrics_collector.py`, `operation_tracker.py`, `websocket_server.py`)
- [x] Deleted `monitoring/fastapi_dashboard/` directory (dashboard lives in the separate `logeverything-dashboard/` subproject)

### Developer Experience

- [x] **CLI tool** — `logeverything version`, `logeverything doctor`, `logeverything init` with `console_scripts` entry point and `python -m logeverything` support
- [x] **Better error messages** — Fuzzy-match "Did you mean?" suggestions using `difflib.get_close_matches()` when `@log(using=...)` can't find a logger
- [x] **`py.typed` packaging fix** — `[options.package_data]` in `setup.cfg` now correctly includes the marker in wheels
- [x] **CLI tests** — `test_cli.py` covering version output, doctor checks, and module invocation

### Documentation

- [x] **New user-guide pages** — `rotation-handlers.rst` (size/time rotation, compression, dashboard integration) and `cli.rst` (version, doctor, init commands)
- [x] **Doc structure cleanup** — Renamed `custom-handlers-guide.rst` title to "Avoiding Duplicate Log Messages"; removed emoji from section headers for consistency across all RST files
- [x] **JSONLineFormatter coverage** — Added to README, CHANGELOG, dashboard.rst, correlation.rst, custom-handlers-guide.rst, and remote-logging.rst
- [x] **Updated examples** — `custom_handlers_example.py` uses `JSONLineFormatter` as primary approach; new `rotation_handlers_example.py`; `monitoring_integration_example.py` and `production_logging_architecture.py` updated with rotation handlers

---

## v0.3.0 — Structured Logging & Observability

Focus: native structured events and integration with the observability ecosystem.

### Structured Logging

#### Event-based API

**Problem:** All logging in LogEverything is string-based (`log.info("User signed up")`). Structured logging — emitting key-value pairs as first-class data — is essential for log aggregation, querying, and dashboards. Currently the only way to attach structured data is via `log.bind()`, which sets context but doesn't change the log call itself.

**What to build:**

Add a new method to `Logger` and `AsyncLogger`:

```python
def event(self, event_name: str, level: int = INFO, **data: Any) -> None:
    """
    Emit a structured log event.

    Args:
        event_name: Dot-separated event identifier (e.g. "user.signup", "order.payment.failed")
        level: Log level (default INFO)
        **data: Arbitrary key-value pairs attached to the event

    Example:
        log.event("user.signup", user_id=123, plan="pro", source="google_ads")
    """
```

**Implementation in `logger.py`:**

```python
def event(self, event_name, level=logging.INFO, **data):
    record = self._logger.makeRecord(
        self._logger.name, level, "(event)", 0, event_name, (), None
    )
    record._structured = data          # Picked up by JSONHandler (already reads _structured)
    record._event_name = event_name    # Queryable field
    self._logger.handle(record)
```

**Why this works:** The `JSONHandler.emit()` method at `handlers.py:244` already checks `getattr(record, "_structured", None)` and merges it into the top-level JSON output. This means structured events will automatically serialize correctly to JSON without modifying the handler.

**Dashboard impact:** The dashboard's ingestion endpoint and logs table would display event data as expandable JSON in the message column.

#### Processor chain

**Problem:** Users need to transform, enrich, or filter log records before they reach handlers — strip PII, add request context, rename fields for downstream compatibility, sample high-volume events. Currently there's no hook between record creation and handler emission.

**What to build:**

A processor pipeline inspired by structlog's design, but integrated with Python's logging infrastructure:

```python
# New file: logeverything/processors.py

class ProcessorChain:
    """
    Ordered list of callables that transform log records before emission.
    Each processor receives a dict and returns a dict (or None to drop the record).
    """
    def __init__(self):
        self._processors = []

    def add(self, processor: Callable[[dict], Optional[dict]]) -> None:
        self._processors.append(processor)

    def process(self, event_dict: dict) -> Optional[dict]:
        for proc in self._processors:
            event_dict = proc(event_dict)
            if event_dict is None:
                return None  # Record dropped
        return event_dict
```

**Built-in processors to ship:**
- `add_timestamp` — Adds ISO 8601 timestamp if not present
- `add_caller_info` — Adds `file`, `line`, `function` from the call stack
- `add_hostname` — Adds `hostname` and `pid`
- `redact_patterns` — Regex-based PII redaction (see Security section in v0.4.0)
- `rename_fields` — Map LogEverything field names to external schemas (e.g., `level` → `severity` for GCP)
- `sample_events` — Probabilistic sampling: only emit 1 in N records for high-volume event types

**Integration point:** Attach the chain to `Logger` via `log.configure(processors=[...])`. The chain runs inside a custom `logging.Filter` that intercepts records before they reach handlers.

#### Schema enforcement

**Problem:** In large codebases, structured events drift — one team logs `user_id`, another logs `userId`, a third logs `uid`. Without validation, dashboards and queries silently break.

**What to build:**

```python
from logeverything import Logger

log = Logger("payments")
log.configure(event_schema={
    "payment.processed": {
        "required": ["order_id", "amount", "currency"],
        "optional": ["discount_code", "payment_method"],
    },
    "payment.failed": {
        "required": ["order_id", "error_code", "error_message"],
    },
})

# This works:
log.event("payment.processed", order_id="ORD-1", amount=49.99, currency="USD")

# This warns (missing required field 'amount'):
log.event("payment.processed", order_id="ORD-1", currency="USD")

# This warns (unexpected field 'user_name'):
log.event("payment.processed", order_id="ORD-1", amount=49.99, currency="USD", user_name="Bob")
```

**Implementation:** A processor in the chain that validates `_event_name` against the schema dict. Violations emit a warning-level log (not an exception — logging should never crash the application).

---

### OpenTelemetry Integration

**Problem:** OpenTelemetry (OTel) is the industry standard for observability. Teams using Jaeger, Grafana Tempo, Datadog, or Honeycomb expect logs to carry `trace_id` and `span_id` so they can correlate logs with distributed traces. LogEverything has its own `correlation_id` but doesn't bridge to the OTel ecosystem.

**New file:** `logeverything/integrations/opentelemetry.py`

**Optional dependency:** Add `opentelemetry` extras in `setup.cfg`:
```ini
opentelemetry =
    opentelemetry-api>=1.20.0
    opentelemetry-sdk>=1.20.0
```

#### OTLP log exporter

Ship LogEverything logs as OTLP `LogRecord` protobuf messages to any OTel-compatible backend.

```python
from logeverything.integrations.opentelemetry import OTLPLogHandler

handler = OTLPLogHandler(
    endpoint="http://otel-collector:4317",  # gRPC endpoint
    service_name="my-app",
    resource_attributes={"deployment.environment": "production"},
)
log.add_handler(handler)
```

**Implementation approach:**
- Use `opentelemetry.sdk._logs.LoggerProvider` and `OTLPLogExporter` from the OTel SDK
- Map LogEverything levels to OTel severity numbers (DEBUG=5, INFO=9, WARNING=13, ERROR=17, CRITICAL=21)
- Include LogEverything-specific attributes: `logeverything.call_id`, `logeverything.indent_level`, `logeverything.log_type`
- Batch export using OTel's built-in `BatchLogRecordProcessor`

#### Trace context injection

Automatically read `trace_id` and `span_id` from the active OTel span and attach them to every log record.

```python
from logeverything.integrations.opentelemetry import OTelContextFilter

log = Logger("my_app")
log._logger.addFilter(OTelContextFilter())
# Now every log record has record.otel_trace_id and record.otel_span_id
```

**Implementation:** Similar pattern to `CorrelationFilter` in `correlation.py:87-113`:
```python
class OTelContextFilter(logging.Filter):
    def filter(self, record):
        span = trace.get_current_span()
        ctx = span.get_span_context()
        record.otel_trace_id = format(ctx.trace_id, '032x') if ctx.trace_id else ""
        record.otel_span_id = format(ctx.span_id, '016x') if ctx.span_id else ""
        record.otel_trace_flags = ctx.trace_flags
        return True
```

#### Baggage propagation

Bridge OTel baggage to LogEverything's bound context. When OTel baggage contains `tenant_id=acme`, it should appear in LogEverything's structured output.

**Implementation:** A processor in the chain that reads `opentelemetry.baggage.get_all()` and merges into the record's structured data.

#### Resource attributes

Auto-detect and attach standard OTel resource attributes:
- `service.name` from `OTEL_SERVICE_NAME` env var or `Logger` name
- `service.version` from package metadata
- `host.name` from `socket.gethostname()`
- `container.id` from `/proc/self/cgroup` (Linux) or `HOSTNAME` env var (Docker/K8s)
- `k8s.pod.name`, `k8s.namespace.name` from Downward API env vars

---

### Sentry Integration

**New file:** `logeverything/integrations/sentry.py`

**Optional dependency:**
```ini
sentry =
    sentry-sdk>=1.30.0
```

#### Breadcrumb handler

Every `log.info()`, `log.warning()`, etc. becomes a Sentry breadcrumb (the trail of events leading up to an error).

```python
class SentryBreadcrumbHandler(logging.Handler):
    def emit(self, record):
        sentry_sdk.add_breadcrumb(
            category="logeverything",
            message=record.getMessage(),
            level=record.levelname.lower(),
            data={
                "logger": record.name,
                "correlation_id": getattr(record, "correlation_id", ""),
                "call_id": getattr(record, "call_id", ""),
            },
        )
```

#### Error capture

When `log.error()` or `log.exception()` is called, optionally capture the event in Sentry with full context (bound variables, correlation ID, hierarchy depth).

```python
log.configure(sentry=True)  # Enables automatic Sentry capture for ERROR+
log.error("Payment processing failed", exc_info=True)
# → Sentry receives the exception with LogEverything context as extra data
```

#### Performance spans

The `@log` decorator already measures function duration (`elapsed` in `decorators.py:433`). When Sentry SDK is active, wrap the function execution in a Sentry span:

```python
# In decorators.py, inside log_function wrapper:
if sentry_sdk.is_initialized():
    with sentry_sdk.start_span(op="function", description=func_name):
        result = func(*args, **kwargs)
```

This gives Sentry's Performance tab automatic visibility into every decorated function.

---

### Prometheus Metrics

**New file:** `logeverything/integrations/prometheus.py`

**Optional dependency:**
```ini
prometheus =
    prometheus-client>=0.16.0
```

#### Metrics handler

Expose logging activity as Prometheus metrics, scrapeable by any Prometheus server.

```python
from prometheus_client import Counter, Histogram, Gauge

logs_total = Counter('logeverything_logs_total', 'Total log records', ['level', 'logger'])
function_duration = Histogram('logeverything_function_duration_seconds', 'Decorated function duration', ['function'])
active_loggers = Gauge('logeverything_active_loggers', 'Number of registered loggers')
```

**Integration point:** A `logging.Handler` subclass that updates these metrics on every `emit()`. The handler itself emits nothing — it purely increments counters.

#### `/metrics` endpoint

For users running FastAPI, provide an optional route:

```python
from logeverything.integrations.prometheus import mount_metrics

app = FastAPI()
mount_metrics(app)  # Adds GET /metrics returning Prometheus text format
```

**Implementation:** Uses `prometheus_client.generate_latest()` to produce the scrape response.

---

## v0.4.0 — Cloud & Enterprise

Focus: cloud provider integrations, message queue handlers, and security/compliance features for enterprise deployment.

### Cloud Provider Handlers

**Problem:** `setup.cfg` already declares a `cloud` extras group with `boto3`, `google-cloud-logging`, and `azure-monitor-opentelemetry` as optional dependencies — but no handler code exists to use them. Teams deploying to AWS, GCP, or Azure currently have no way to ship LogEverything logs to their cloud's native logging service without building custom handlers.

**Where it lives:** `logeverything/handlers/cloud/` (new sub-package)

#### AWS CloudWatch Logs

**New file:** `logeverything/handlers/cloud/cloudwatch.py`

```python
class CloudWatchHandler(logging.Handler):
    """
    Ships log records to AWS CloudWatch Logs.

    Args:
        log_group: CloudWatch log group name (e.g. "/app/my-service")
        log_stream: Stream name (defaults to hostname + PID)
        region: AWS region (defaults to AWS_DEFAULT_REGION env var)
        batch_size: Records per PutLogEvents call (max 10,000 per AWS limits)
        flush_interval: Seconds between automatic flushes
    """
```

**Implementation details:**
- Uses `boto3.client('logs')` with `put_log_events()` API
- Each log record becomes a CloudWatch event with `timestamp` (epoch ms) and `message` (JSON string)
- Reuses `LogBuffer` from `transport/buffer.py` for batching and retry — CloudWatch has a rate limit of 5 requests/sec per stream
- Handles the CloudWatch `sequenceToken` requirement: each `put_log_events` must include the sequence token from the previous response
- Creates the log group and stream automatically if they don't exist (`create_log_group()`, `create_log_stream()`)
- Structured data (from `log.event()`) is included in the JSON message body so CloudWatch Insights can query it with `parse @message`

**Auth:** Relies on standard boto3 credential chain (env vars, IAM role, `~/.aws/credentials`). No LogEverything-specific auth config needed.

#### Google Cloud Logging

**New file:** `logeverything/handlers/cloud/gcp.py`

```python
class GCPLoggingHandler(logging.Handler):
    """
    Ships log records to Google Cloud Logging (formerly Stackdriver).

    Args:
        project_id: GCP project ID (defaults to metadata server auto-detection)
        log_name: Log name in Cloud Logging (e.g. "my-app")
        resource_type: Monitored resource type ("global", "gce_instance", "k8s_container")
        labels: Static labels attached to every log entry
    """
```

**Implementation details:**
- Uses `google.cloud.logging.Client()` with its built-in background transport (already batches)
- Maps LogEverything levels to Cloud Logging severity: `DEBUG` → `DEBUG`, `INFO` → `INFO`, `WARNING` → `WARNING`, `ERROR` → `ERROR`, `CRITICAL` → `CRITICAL`
- Structured data is sent as `jsonPayload` (not `textPayload`) so Cloud Logging's advanced queries work: `jsonPayload.user_id = "123"`
- Auto-detects GKE environment and populates `k8s_container` resource labels (cluster, namespace, pod, container) from Downward API env vars
- Includes `correlation_id`, `call_id`, `log_type` as Cloud Logging labels for filtering

#### Azure Monitor

**New file:** `logeverything/handlers/cloud/azure.py`

```python
class AzureMonitorHandler(logging.Handler):
    """
    Ships log records to Azure Monitor (Application Insights / Log Analytics).

    Args:
        connection_string: Application Insights connection string
        workspace_id: Log Analytics workspace ID (alternative to connection_string)
    """
```

**Implementation details:**
- Uses `azure-monitor-opentelemetry-exporter` to emit logs as OTel log records to Azure Monitor
- This bridges nicely with the OTel integration from v0.3.0 — if both are configured, they share the same export pipeline
- Maps structured event data to Azure Monitor custom dimensions
- Includes `correlation_id` as Application Insights operation_Id for end-to-end transaction tracing

#### S3/GCS/Azure Blob archival

**New file:** `logeverything/handlers/cloud/object_storage.py`

For long-term log archival, periodically flush compressed log files to object storage.

```python
class ObjectStorageArchiver:
    """
    Periodically compresses and uploads log files to cloud object storage.

    Args:
        handler: A FileHandler or RotatingFileHandler to archive from
        backend: "s3", "gcs", or "azure_blob"
        bucket: Bucket/container name
        prefix: Path prefix (e.g. "logs/production/")
        archive_interval: How often to archive (default: daily)
        compress: Compression format ("gzip", "zstd", or None)
    """
```

**Partition scheme:** Files are uploaded with time-partitioned paths for efficient querying:
```
s3://my-bucket/logs/production/2026/02/18/my-app-001.json.gz
s3://my-bucket/logs/production/2026/02/18/my-app-002.json.gz
```

This is compatible with AWS Athena, BigQuery external tables, and Azure Data Explorer for ad-hoc SQL queries over archived logs.

---

### Redis & Message Queue Handlers

**Problem:** In distributed architectures, logs often need to flow through message brokers for fan-out processing (multiple consumers), buffering (handle bursts), or decoupling (producer doesn't wait for consumer). LogEverything currently only supports direct HTTP/TCP/UDP delivery.

**Where it lives:** `logeverything/handlers/queues/` (new sub-package)

#### Redis Streams handler

```python
class RedisStreamHandler(logging.Handler):
    """
    Publishes log records to a Redis Stream.

    Args:
        redis_url: Redis connection URL (e.g. "redis://localhost:6379/0")
        stream_key: Stream name (e.g. "logs:my-app")
        maxlen: Maximum stream length (older entries trimmed automatically)
    """
```

**Why Redis Streams over Pub/Sub:** Streams provide persistence, consumer groups (multiple independent consumers), and acknowledgement. Pub/Sub is fire-and-forget — if no subscriber is connected, the message is lost.

**Implementation:**
- Uses `redis-py` library's `xadd()` for publishing
- Each log record becomes a stream entry with fields matching the JSON schema (`level`, `message`, `logger`, `timestamp`, `correlation_id`, etc.)
- `maxlen` with approximate trimming (`~`) keeps memory bounded
- Consumer groups allow multiple dashboard instances or log processors to read independently

#### Kafka handler

```python
class KafkaHandler(logging.Handler):
    """
    Produces log records to Apache Kafka topics.

    Args:
        bootstrap_servers: Kafka broker addresses (e.g. "localhost:9092")
        topic: Kafka topic name (e.g. "logs.production")
        key_func: Callable that returns a partition key from a log record
                  (default: uses logger name, so logs from the same logger go to the same partition)
        compression: "gzip", "snappy", "lz4", or None
    """
```

**Implementation:**
- Uses `confluent-kafka` Python client (higher performance than `kafka-python`)
- Asynchronous production with delivery callbacks for error handling
- Reuses `LogBuffer` pattern for local batching before Kafka produce calls
- JSON serialization with optional Avro schema registry support (future)

#### RabbitMQ handler

```python
class RabbitMQHandler(logging.Handler):
    """
    Publishes log records to RabbitMQ exchanges.

    Args:
        amqp_url: Connection URL (e.g. "amqp://guest:guest@localhost:5672/")
        exchange: Exchange name (e.g. "logs")
        routing_key_func: Callable returning routing key from record
                          (default: uses log level, e.g. "error", "warning")
    """
```

**Implementation:**
- Uses `pika` library with connection pooling
- Routing key based on log level enables level-based queue routing: errors go to the alerting queue, info goes to the archival queue
- Persistent message delivery (`delivery_mode=2`) ensures logs survive broker restarts

---

### Elasticsearch Integration

**Problem:** Elasticsearch (with Kibana) is the most common log analysis stack. Teams using ELK need LogEverything logs indexed with proper field mappings, data types, and lifecycle policies.

**New file:** `logeverything/handlers/elasticsearch.py`

#### Elasticsearch handler

```python
class ElasticsearchHandler(logging.Handler):
    """
    Bulk-indexes log records into Elasticsearch.

    Args:
        hosts: Elasticsearch hosts (e.g. ["http://localhost:9200"])
        index_pattern: Index name pattern with date (e.g. "logs-{date}")
        api_key: Elasticsearch API key for authentication
        batch_size: Records per bulk request (default 500)
        flush_interval: Seconds between bulk flushes (default 5.0)
    """
```

**Implementation details:**
- Uses `elasticsearch-py` client's `helpers.bulk()` for efficient batch indexing
- Index pattern supports date substitution: `"logs-{date}"` → `"logs-2026.02.18"`
- Automatically creates index templates on first use with correct field mappings:
  - `timestamp`: `date` type
  - `level`: `keyword` (exact match, not analyzed)
  - `message`: `text` (full-text search) + `keyword` sub-field (exact match)
  - `correlation_id`, `call_id`, `source`: `keyword`
  - `indent_level`: `integer`
  - Structured event data: `flattened` type (queryable without mapping explosion)

#### ECS field mapping

[Elastic Common Schema](https://www.elastic.co/guide/en/ecs/current/index.html) is a standardized field naming convention. Mapping LogEverything fields to ECS enables cross-application log analysis and Kibana's built-in visualizations.

| LogEverything field | ECS field | Type |
|---|---|---|
| `timestamp` | `@timestamp` | `date` |
| `level` | `log.level` | `keyword` |
| `message` | `message` | `text` |
| `logger` | `log.logger` | `keyword` |
| `correlation_id` | `trace.id` | `keyword` |
| `source` | `service.name` | `keyword` |
| `call_id` | `span.id` | `keyword` |
| `thread` | `process.thread.id` | `long` |
| `process` | `process.pid` | `long` |

**Implementation:** A `rename_fields` processor (from the processor chain in v0.3.0) that remaps field names before the Elasticsearch handler indexes them.

#### Kibana dashboard templates

Ship pre-built Kibana saved objects (JSON export) that users can import for instant visibility:
- **Log Explorer** — Time-series histogram of log volume by level, with drill-down table
- **Error Dashboard** — Error rate over time, top error messages, correlation ID links
- **Function Performance** — Histogram of `@log` decorated function durations from `call_exit` records

These would live in `extras/kibana/` as `.ndjson` files importable via Kibana's Saved Objects UI.

---

### Security & Compliance

#### PII redaction processor

**Problem:** Logs often inadvertently contain personally identifiable information — email addresses in error messages, credit card numbers in request dumps, IP addresses in access logs. Compliance frameworks (GDPR, HIPAA, PCI-DSS) require this data to be redacted before storage.

**What to build:** A processor for the processor chain (v0.3.0) that regex-matches and redacts sensitive patterns.

```python
from logeverything.processors import redact_patterns

log.configure(processors=[
    redact_patterns(
        patterns={
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "ipv4": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        },
        replacement="[REDACTED:{name}]",  # e.g. "[REDACTED:email]"
        fields=["message"],  # Which record fields to scan (default: message only)
    ),
])
```

**Implementation:** The processor receives the event dict, iterates over configured `fields`, applies `re.sub()` for each pattern, and returns the modified dict. Compiled regex patterns are cached at processor creation time for performance.

**Performance note:** Regex scanning adds overhead. For high-throughput applications, offer a `sampling_rate` parameter that only redacts 1-in-N records (the rest are assumed safe if the application doesn't log PII by design).

#### Encryption at rest

**Problem:** Some compliance frameworks require log files to be encrypted on disk.

**What to build:** An encryption wrapper for `FileHandler` and `RotatingFileHandler`.

```python
class EncryptedFileHandler(FileHandler):
    def __init__(self, filename, encryption_key, algorithm="AES-256-GCM", **kwargs):
        # Encrypts each log line individually (allows line-by-line decryption)
        # OR encrypts the entire file on rotation (better compression ratio)
        ...
```

**Implementation options:**
1. **Per-line encryption** — Each line is independently encrypted with a unique nonce. Allows `grep`-like tools to work on individual lines (after decryption). Uses `cryptography` library's `Fernet` (AES-128-CBC) or `AESGCM`.
2. **Per-file encryption** — The file is written in plaintext, then encrypted on rotation. Simpler, better compression (compress then encrypt). Decryption requires reading the full file.

**Recommendation:** Start with per-file encryption on rotation (option 2) — simpler to implement, works with compressed rotation, and matches how most compliance audits expect encrypted logs.

#### Audit log mode

**Problem:** For regulatory compliance, some logs must be tamper-evident — it should be detectable if someone modifies or deletes log entries after the fact.

**What to build:** A hash-chain mode where each log record includes a cryptographic hash of the previous record, creating a blockchain-like integrity chain.

```python
class AuditHandler(FileHandler):
    def __init__(self, filename, hash_algorithm="sha256", **kwargs):
        self._prev_hash = "0" * 64  # Genesis hash
        ...

    def emit(self, record):
        entry = self._format_record(record)
        entry["_prev_hash"] = self._prev_hash
        entry["_hash"] = hashlib.sha256(
            json.dumps(entry, sort_keys=True).encode()
        ).hexdigest()
        self._prev_hash = entry["_hash"]
        # Write entry to file
        ...
```

**Verification:** A companion function that reads the audit log file and verifies the hash chain:
```python
from logeverything.handlers import verify_audit_log

is_valid, broken_at = verify_audit_log("audit.log")
# is_valid=True if all hashes check out
# broken_at=line_number if tampering detected
```

#### RBAC for dashboard

**Problem:** The monitoring dashboard currently has no authentication — anyone with network access can view all logs. Enterprise deployments need role-based access control.

**What to build (in `logeverything-dashboard/`):**
- Authentication middleware (session-based or JWT)
- Three roles: **viewer** (read-only), **operator** (can clear logs, trigger exports), **admin** (manage connections, users)
- User management page in the dashboard
- API key authentication for the ingestion endpoint (already partially supported via `api_key` parameter in `HTTPTransportHandler`)

**Implementation:** Use FastAPI's dependency injection with `Depends(get_current_user)`. Store users in the existing SQLite database. Support optional LDAP/OAuth integration via config.

---

## v1.0.0 — Stable Release

Focus: production readiness, API stability guarantees, comprehensive testing, distributed tracing, performance hardening, and dashboard v2. This is the first release where downstream projects can depend on LogEverything with a stability contract — every public symbol, parameter, and output format becomes a commitment.

### Graduation Criteria

These conditions **must all be true** before the v1.0.0 tag is cut. Use this checklist as the release gate:

- [ ] All v0.3.0 (Structured Logging & Observability) features shipped, tested, and documented
- [ ] All v0.4.0 (Cloud & Enterprise) features shipped, tested, and documented
- [ ] **90%+ line coverage** on `logeverything/` overall; **95%+** on `logger.py`, `core.py`, `base_logger.py`, `indent_manager.py`, `decorators.py`
- [ ] Full API reference generated from docstrings — every public symbol in `__all__` has a docstring with Args, Returns, Raises, and Example sections
- [ ] No known thread leaks or resource leaks (verified by `conftest.py` thread-leak detection + dedicated stress tests)
- [ ] Performance benchmarks baselined and CI-gated for all critical paths: decorator overhead, JSON serialization, handler emit, indent management
- [ ] Cross-platform CI green: Ubuntu + Windows + macOS × Python 3.8, 3.9, 3.10, 3.11, 3.12
- [ ] Security audit clean: bandit, no hardcoded secrets, no eval/exec, PII redaction tested
- [ ] Zero open bugs labelled `severity:critical` or `severity:high`
- [ ] CHANGELOG.md covers every user-facing change since v0.4.0
- [ ] Migration guide from stdlib `logging` published in docs
- [ ] `logeverything doctor` validates all configuration and reports issues clearly

---

### Testing & Coverage

#### Coverage targets by module

**Problem:** Current coverage is 65% across 395 tests. A 1.0 release needs much higher confidence, especially in core paths that every user touches.

**Target coverage by module:**

| Module | Current (est.) | Target | Priority areas |
|--------|---------------|--------|----------------|
| `logger.py` | ~70% | 95% | `configure()` branches, `bind()` chaining, `opt()` options, `context()` nesting, handler add/remove |
| `core.py` | ~60% | 95% | `get_logger()` cache behavior, `_config` mutation, `_detect_environment()` edge cases, platform detection |
| `base/base_logger.py` | ~75% | 95% | All log levels, `bind()` context inheritance, `_format_message_with_context()`, registry lifecycle |
| `indent_manager.py` | ~80% | 95% | Thread isolation, async isolation, `decorator_enter()`/`decorator_exit()` compound methods, deep nesting (>50 levels) |
| `decorators/decorators.py` | ~70% | 95% | `@log` auto-detection (function, async function, class, static method, classmethod), `using=` lookup + fuzzy match, exception propagation, generator/async generator support |
| `handlers/` | ~60% | 90% | Rotation triggers, compression, UTF-8 encoding on Windows, concurrent writes, handler `close()` cleanup |
| `asyncio/` | ~50% | 90% | `AsyncLogger` task isolation, `AsyncQueueHandler` shutdown, cancellation safety, `contextvars` propagation across `asyncio.gather()` |
| `transport/` | ~80% | 90% | `LogBuffer` backpressure, retry logic, connection failure recovery, TLS handshake |
| `capture/` | ~60% | 85% | Nested `capture_print`, recursive print calls, multithread print capture |
| `integrations/` | ~40% | 85% | FastAPI/Flask/Django middleware with real ASGI/WSGI apps, Celery task lifecycle |

**How to contribute:** Pick a module, run `pytest --cov=logeverything/{module} tests/ --cov-report=term-missing` to see uncovered lines, and write tests targeting those branches. Each test file follows the naming convention `tests/test_{module}.py`.

#### Stress & load tests

**New file:** `tests/test_stress.py`

**Problem:** Unit tests verify correctness at low volume. Production workloads involve thousands of log records per second across multiple threads. We need tests that verify behavior under load.

**What to build:**

```python
# tests/test_stress.py

import threading
import pytest

class TestHighThroughput:
    """Verify no data loss, no deadlocks, no crashes under sustained load."""

    def test_concurrent_logging_10_threads(self, tmp_path):
        """10 threads, 1000 records each, all records appear in output."""
        log = Logger("stress")
        log_file = tmp_path / "stress.jsonl"
        log.configure(handlers=[{"type": "json_file", "path": str(log_file)}])

        errors = []
        def worker(thread_id):
            for i in range(1000):
                log.info(f"thread={thread_id} seq={i}")

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 10_000, f"Expected 10000 records, got {len(lines)}"

    def test_decorator_under_contention(self):
        """@log decorator handles 100 concurrent decorated calls without deadlock."""
        ...

    def test_async_burst(self):
        """1000 concurrent async tasks logging simultaneously."""
        ...

    def test_handler_failure_isolation(self):
        """One broken handler doesn't block other handlers or callers."""
        ...
```

**Markers:** Add `@pytest.mark.slow` so these don't run on every local `make test` — they run in CI only via `pytest -m slow`.

#### Property-based tests

**New file:** `tests/test_properties.py`

**Problem:** Hand-written tests check specific inputs. Property-based tests generate thousands of random inputs to find edge cases humans miss — empty strings, Unicode, extremely long messages, special characters in logger names.

**Dependency:** Add `hypothesis>=6.0` to the `test` extras in `setup.cfg`.

**What to build:**

```python
from hypothesis import given, strategies as st

class TestLoggerProperties:

    @given(name=st.text(min_size=1, max_size=200))
    def test_logger_accepts_any_string_name(self, name):
        """Logger creation should never crash regardless of name content."""
        log = Logger(name)
        assert log.name is not None

    @given(message=st.text(max_size=10000))
    def test_info_accepts_any_string_message(self, message):
        """log.info() should never raise on any string input."""
        log = Logger("prop_test")
        log.info(message)  # Should not raise

    @given(
        level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
        kwargs=st.dictionaries(st.text(min_size=1, max_size=50), st.text(max_size=200), max_size=20),
    )
    def test_bind_accepts_arbitrary_kwargs(self, level, kwargs):
        """bind() should handle any key-value pairs without crashing."""
        log = Logger("prop_test")
        bound = log.bind(**kwargs)
        getattr(bound, level.lower())("test message")
```

**Key properties to verify:**
- Logger creation never raises (any valid Python string as name)
- Logging methods never raise (any string, any kwargs)
- `bind()` context is always preserved across calls
- `IndentManager` indent level is always non-negative
- JSON serialization never produces invalid JSON (for any loggable value)

#### Concurrent correctness tests

**New file:** `tests/test_concurrent.py`

**Problem:** Thread-local and contextvars isolation is critical to correctness. A single bug here means threads see each other's indent levels or correlation IDs — a silent data corruption issue.

**What to build:**

```python
import asyncio
import threading

class TestThreadIsolation:

    def test_indent_levels_isolated_across_threads(self):
        """Each thread's indent level is independent."""
        results = {}

        @log
        def nested_call(depth, thread_id):
            if depth > 0:
                nested_call(depth - 1, thread_id)
            else:
                results[thread_id] = get_current_indent()

        threads = []
        # Thread 0 nests 5 deep, thread 1 nests 10 deep
        for tid, depth in [(0, 5), (1, 10)]:
            t = threading.Thread(target=nested_call, args=(depth, tid))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert results[0] != results[1], "Indent levels should differ between threads"

    def test_correlation_id_isolated_across_threads(self):
        """set_correlation_id in one thread doesn't leak to another."""
        ...

class TestAsyncIsolation:

    @pytest.mark.asyncio
    async def test_indent_levels_isolated_across_tasks(self):
        """Each asyncio task's indent level is independent via contextvars."""
        ...

    @pytest.mark.asyncio
    async def test_correlation_id_isolated_across_tasks(self):
        """set_correlation_id in one task doesn't leak to another."""
        ...
```

---

### API Stability

#### Freeze public API

**What this means:** Every class, function, and parameter in `__all__` (see `logeverything/__init__.py:88-130`) becomes a stability guarantee. Removing or renaming anything requires a major version bump (2.0.0).

**What to document:**
- Create `docs/source/api/stability.rst` listing every public symbol and its stability status
- Mark experimental APIs with `@experimental` decorator that emits a `DeprecationWarning` subclass
- Version the JSON output schema of `JSONHandler` — field additions are minor bumps, field removals are major bumps

#### Deprecation policy

Minimum 2 minor versions of deprecation warnings before removal:
- v1.0.0: `log_function` marked deprecated, emits `DeprecationWarning` on import
- v1.1.0: Warning upgraded to `FutureWarning`
- v1.2.0: Removal allowed

**Implementation:** Use `warnings.warn()` with `stacklevel=2` so the warning points to the caller, not LogEverything internals.

#### Migration tooling

A codemod script using `libcst` (Concrete Syntax Tree) that auto-migrates deprecated API calls:

```bash
logeverything migrate --dry-run src/
# Shows what would change:
#   src/app.py:12  @log_function → @log
#   src/app.py:23  from logeverything import log_function → from logeverything import log

logeverything migrate src/
# Applies changes
```

**Implementation:** Parse Python files with `libcst`, match import statements and decorator usages, replace with new equivalents, write back.

**New file:** `logeverything/cli_migrate.py`

**What to build:**

```python
# logeverything/cli_migrate.py

import libcst as cst

class DeprecatedImportRewriter(cst.CSTTransformer):
    """
    Rewrites deprecated imports:
      from logeverything import log_function  →  from logeverything import log
    """
    RENAMES = {
        "log_function": "log",
        "log_io": "log",
        # Add more as APIs are deprecated
    }

    def visit_ImportFrom(self, node):
        # Check if importing from logeverything
        ...

    def leave_ImportFrom(self, original, updated):
        # Rewrite deprecated names
        ...

class DeprecatedDecoratorRewriter(cst.CSTTransformer):
    """
    Rewrites deprecated decorator usage:
      @log_function  →  @log
      @log_function(using="mylog")  →  @log(using="mylog")
    """
    ...
```

**CLI entry point:** Add `migrate` subcommand to `logeverything/cli.py`:
```python
@cli.command()
@click.argument("path")
@click.option("--dry-run", is_flag=True, help="Show changes without applying them")
def migrate(path, dry_run):
    ...
```

**Testing:** `tests/test_cli_migrate.py` with fixture Python files containing deprecated patterns, verifying the rewriter produces the expected output.

---

### Documentation Completeness

#### API reference auto-generation

**Problem:** The Sphinx docs exist but don't cover every public symbol. Users reading the docs shouldn't have to fall back to source code to understand a parameter or return type.

**What to do:**

1. Ensure every class and function in `__all__` (34 explicit + 75 lazy-loaded in `__init__.py`) has a complete Google-style docstring with `Args`, `Returns`, `Raises`, and `Example` sections.

2. Add `autodoc` directives for modules not yet covered in `docs/source/api/`:

   | Module | File to create | Key symbols to document |
   |--------|---------------|------------------------|
   | `base/base_logger.py` | `api/base_logger.rst` | `BaseLogger`, `debug()`, `info()`, `bind()`, `configure()` |
   | `indent_manager.py` | `api/indent_manager.rst` | `IndentManager`, `decorator_enter()`, `decorator_exit()`, `get_hierarchy_snapshot()` |
   | `transport/buffer.py` | `api/transport.rst` | `LogBuffer`, `HTTPTransportHandler`, `TCPTransportHandler`, `UDPTransportHandler` |
   | `correlation.py` | `api/correlation.rst` | `CorrelationFilter`, `set_correlation_id()`, `get_correlation_id()`, `propagate_context()` |
   | `asyncio/` | `api/async.rst` | `AsyncLogger`, `AsyncQueueHandler`, async decorators |

3. Add `sphinx-autodoc-typehints` (already in `docs` extras) integration so type hints render in the docs without duplicating them in docstrings.

**Verification:** Run `make docs` and confirm zero Sphinx warnings. Every `.. automodule::` directive should resolve without "missing docstring" warnings.

#### Cookbook / recipes guide

**New file:** `docs/source/cookbook.rst`

**Problem:** The existing docs explain individual features but don't show how to combine them for real-world patterns. New users need copy-paste-ready recipes.

**Recipes to include:**

| Recipe | What it demonstrates |
|--------|---------------------|
| **FastAPI with correlation IDs** | Middleware setup, `set_correlation_id()`, JSON logging to file, dashboard ingestion |
| **Celery task logging** | Worker setup, task decorator, correlation propagation across task chains |
| **Multi-service setup** | Two FastAPI services with W3C Trace Context propagation, shared dashboard |
| **Testing with LogEverything** | How to capture and assert on log output in pytest, using `captured_logger()` fixture pattern |
| **Production deployment** | Production profile, `TimedRotatingFileHandler` with gzip, CloudWatch shipping, Sentry integration |
| **Migrating from stdlib logging** | Side-by-side comparison of stdlib patterns and LogEverything equivalents |
| **Custom handler** | Building a handler from scratch (subclass `logging.Handler`, implement `emit()`) |
| **PII-safe logging** | Processor chain with `redact_patterns`, schema enforcement, audit mode |

**Format for each recipe:** Problem statement (2-3 sentences), complete working code (copy-pasteable), expected output, and a "What's happening" section explaining each line.

#### Migration guide from stdlib logging

**New file:** `docs/source/migration.rst`

**Problem:** Most Python developers already use `logging.getLogger()`. They need a clear mapping from stdlib patterns to LogEverything equivalents to adopt the library incrementally.

**Sections to cover:**

```rst
Migration from stdlib logging
=============================

Basic logging
-------------
.. list-table::
   :header-rows: 1

   * - stdlib
     - LogEverything
   * - ``logging.getLogger("myapp")``
     - ``Logger("myapp")``
   * - ``logger.setLevel(logging.DEBUG)``
     - ``log.set_level("DEBUG")``
   * - ``handler = logging.FileHandler("app.log")``
     - ``log.add_file_logging("app.log")``
   * - ``logger.addHandler(handler)``
     - ``log.add_handler(handler)``

Structured context
------------------
.. list-table::
   :header-rows: 1

   * - stdlib (using ``extra={}``)
     - LogEverything (using ``bind()``)
   * - ``logger.info("msg", extra={"user_id": 123})``
     - ``log.bind(user_id=123).info("msg")``

Incremental adoption
--------------------
You don't have to replace everything at once. LogEverything's ``Logger``
wraps a stdlib ``logging.Logger`` internally, so existing handlers,
filters, and formatters continue to work:

.. code-block:: python

   from logeverything import Logger

   log = Logger("myapp")
   # Your existing stdlib handlers still work:
   log._logger.addHandler(your_existing_handler)
```

---

### Configuration Validation

**Problem:** `Logger.configure()` accepts `**kwargs` and silently ignores unknown keys. A user who writes `log.configure(levl="DEBUG")` (typo) gets no feedback — the typo is swallowed and the level stays at the default. At 1.0, configuration errors should be caught early with clear messages.

**What to build:**

#### Config schema and validation

**New file:** `logeverything/config_schema.py`

```python
# logeverything/config_schema.py

from typing import Any, Dict, List, Optional, Set

# Exhaustive set of valid configure() keys
VALID_CONFIG_KEYS: Set[str] = {
    "level", "handlers", "format", "datefmt", "style",
    "propagate", "filters", "processors",
    "visual_mode", "use_symbols", "use_indent", "use_colors",
    "print_capture", "async_mode",
    "queue_size", "flush_interval",
    "event_schema",
    # ... all valid keys
}

# Type expectations for each key
CONFIG_TYPES: Dict[str, type] = {
    "level": (str, int),          # "DEBUG" or 10
    "handlers": (list, tuple),
    "propagate": bool,
    "queue_size": int,
    "flush_interval": (int, float),
    "visual_mode": bool,
    "use_symbols": bool,
    "use_indent": bool,
    "use_colors": bool,
    "print_capture": bool,
    "async_mode": bool,
}

def validate_config(kwargs: Dict[str, Any]) -> List[str]:
    """
    Validate configuration keyword arguments.

    Returns:
        List of warning messages (empty if all valid).

    Raises:
        TypeError: If a value has the wrong type.
    """
    warnings = []
    for key, value in kwargs.items():
        if key not in VALID_CONFIG_KEYS:
            close = difflib.get_close_matches(key, VALID_CONFIG_KEYS, n=1, cutoff=0.6)
            hint = f" Did you mean '{close[0]}'?" if close else ""
            warnings.append(f"Unknown configuration key '{key}'.{hint}")

        expected = CONFIG_TYPES.get(key)
        if expected and not isinstance(value, expected):
            raise TypeError(
                f"configure() '{key}' expects {expected.__name__}, got {type(value).__name__}"
            )
    return warnings
```

**Integration point:** Call `validate_config()` at the top of `Logger.configure()` in `logger.py`. Warnings are emitted via `warnings.warn()` (not logged — to avoid recursion). Type errors raise immediately.

**Fuzzy matching:** Reuse the `difflib.get_close_matches()` pattern already used in the decorator `using=` lookup for "Did you mean?" suggestions.

#### `logeverything doctor` enhancements

**Problem:** The CLI `doctor` command currently checks basic installation. For 1.0, it should validate the runtime configuration and report issues.

**Extend `logeverything/cli.py` `doctor` command:**

```python
def doctor():
    """Diagnose LogEverything configuration and environment."""

    # Existing checks
    check_python_version()
    check_colorama()
    check_optional_deps()

    # New checks for v1.0
    check_handler_health()       # Are all configured handlers writable/reachable?
    check_thread_safety()        # Is IndentManager using the right backend for the detected environment?
    check_circular_imports()     # Any import-time side effects?
    check_log_file_permissions() # Can we write to configured log file paths?
    check_platform_features()    # Unicode support, terminal width, color capability
```

**Output format:** Traffic-light style (PASS / WARN / FAIL) for each check, with actionable fix suggestions for failures.

---

### Plugin & Extension System

**Problem:** LogEverything has integrations for FastAPI, Flask, Django, and Celery in `logeverything/integrations/`, but there's no formal plugin API. Third-party packages can't register handlers, processors, or formatters in a discoverable way. Users building custom integrations have to reach into internals.

#### Plugin interface

**New file:** `logeverything/plugins.py`

**What to build:** A lightweight plugin system using Python entry points (the standard mechanism for plugin discovery in the Python ecosystem):

```python
# logeverything/plugins.py

import importlib.metadata
from typing import Callable, Dict, List, Optional, Protocol

class LogEverythingPlugin(Protocol):
    """Protocol that all plugins must satisfy."""

    name: str
    version: str

    def activate(self, logger_registry: Dict) -> None:
        """Called when the plugin is loaded. Register handlers, processors, etc."""
        ...

    def deactivate(self) -> None:
        """Called on shutdown. Clean up resources."""
        ...


def discover_plugins(group: str = "logeverything.plugins") -> List[LogEverythingPlugin]:
    """
    Discover installed plugins via entry points.

    Third-party packages register plugins in their setup.cfg/pyproject.toml:

        [options.entry_points]
        logeverything.plugins =
            my_plugin = my_package.le_plugin:MyPlugin

    Returns:
        List of instantiated plugin objects.
    """
    plugins = []
    for ep in importlib.metadata.entry_points(group=group):
        plugin_cls = ep.load()
        plugins.append(plugin_cls())
    return plugins


def load_plugins() -> None:
    """Discover and activate all installed plugins. Called once at import time."""
    for plugin in discover_plugins():
        plugin.activate(_logger_cache)
        _active_plugins[plugin.name] = plugin
```

**Entry point groups for extensibility:**

| Group | What it registers | Example |
|-------|------------------|---------|
| `logeverything.plugins` | Full plugin objects | Sentry integration, Datadog integration |
| `logeverything.handlers` | Custom handler classes | `my_package:MyCustomHandler` |
| `logeverything.processors` | Processor callables | `my_package:add_tenant_id` |
| `logeverything.formatters` | Formatter classes | `my_package:CEFFormatter` |

**Discovery timing:** Plugins are discovered lazily on first `get_logger()` call, not at import time, to avoid startup overhead.

#### Plugin testing utilities

**New file:** `logeverything/testing.py`

**Problem:** Plugin authors need a way to test their plugins in isolation without standing up a full LogEverything environment.

```python
# logeverything/testing.py

import io
import logging
from contextlib import contextmanager
from logeverything import Logger

@contextmanager
def capture_logs(logger_name: str = "test", level: str = "DEBUG"):
    """
    Context manager that captures all log output from a LogEverything logger.

    Usage:
        with capture_logs() as captured:
            log = Logger("test")
            log.info("hello")
        assert "hello" in captured.text
        assert len(captured.records) == 1
    """
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(getattr(logging, level))

    log = Logger(logger_name)
    log.add_handler(handler)
    captured = CapturedLogs(stream, [])

    original_emit = handler.emit
    def capturing_emit(record):
        captured.records.append(record)
        original_emit(record)
    handler.emit = capturing_emit

    try:
        yield captured
    finally:
        log.remove_handler(handler)

class CapturedLogs:
    """Container for captured log output."""
    def __init__(self, stream, records):
        self._stream = stream
        self.records = records

    @property
    def text(self):
        return self._stream.getvalue()

    def has_message(self, substring):
        return any(substring in r.getMessage() for r in self.records)

    def count_level(self, level):
        return sum(1 for r in self.records if r.levelname == level)
```

**Export:** Add `capture_logs` and `CapturedLogs` to `__all__` in `__init__.py`.

**Why this matters for 1.0:** A testing utility signals maturity. Libraries like pytest, Flask, and Django all ship test helpers. This makes LogEverything a first-class citizen in test suites.

---

### Graceful Shutdown & Resource Management

**Problem:** When a Python process exits (normally, via `SIGTERM`, or via `KeyboardInterrupt`), buffered log records can be lost. `AsyncQueueHandler` has a background worker thread; transport handlers (`HTTPTransportHandler`, `TCPTransportHandler`) batch records in `LogBuffer`. If the process exits before these buffers flush, the last N records are silently dropped.

#### `atexit` flush

**What to build:**

```python
# In logeverything/core.py, register at module load time:

import atexit

def _shutdown():
    """Flush all handlers and close resources on interpreter exit."""
    for logger in _logger_cache.values():
        for handler in logger._logger.handlers:
            try:
                if hasattr(handler, 'flush'):
                    handler.flush()
                if hasattr(handler, 'close'):
                    handler.close()
            except Exception:
                pass  # Never raise during shutdown

atexit.register(_shutdown)
```

**Files to modify:**
- `logeverything/core.py` — register `atexit` handler
- `logeverything/asyncio/handlers.py` — ensure `AsyncQueueHandler.close()` drains the queue before returning (current implementation: `async_queue_handler.py` has `close()` but it may not wait for the worker thread to finish)
- `logeverything/transport/buffer.py` — ensure `LogBuffer.flush()` blocks until the current batch is sent

**Key constraint:** The `atexit` handler runs in the main thread. `AsyncQueueHandler`'s worker is a daemon thread — daemon threads are killed on exit without cleanup. The fix: make the worker thread non-daemon, or join it in the `atexit` handler with a timeout.

#### Signal handling

**What to build:**

```python
# logeverything/shutdown.py

import signal
import sys

_original_handlers = {}

def install_signal_handlers():
    """Install SIGTERM/SIGINT handlers that flush logs before exit."""
    for sig in (signal.SIGTERM, signal.SIGINT):
        _original_handlers[sig] = signal.getsignal(sig)
        signal.signal(sig, _graceful_exit)

def _graceful_exit(signum, frame):
    """Flush all log buffers, then call the original signal handler."""
    _shutdown()  # Reuse the atexit flush logic
    original = _original_handlers.get(signum)
    if original and callable(original):
        original(signum, frame)
    else:
        sys.exit(128 + signum)
```

**Opt-in, not default:** Signal handler installation is opt-in via `logeverything.install_signal_handlers()` because overriding signal handlers can interfere with frameworks (e.g., Gunicorn, Celery) that install their own. Document this in the cookbook.

#### Resource cleanup verification

**New test:** `tests/test_shutdown.py`

```python
import subprocess
import sys

def test_no_records_lost_on_sigterm(tmp_path):
    """Verify that SIGTERM causes log flush, not data loss."""
    script = tmp_path / "test_app.py"
    script.write_text('''
import time, signal
from logeverything import Logger
from logeverything.shutdown import install_signal_handlers

install_signal_handlers()
log = Logger("test")
log.add_file_logging("{log_file}")

for i in range(100):
    log.info(f"record {{i}}")
time.sleep(60)  # Wait to be killed
'''.format(log_file=str(tmp_path / "out.log").replace("\\", "\\\\")))

    proc = subprocess.Popen([sys.executable, str(script)])
    time.sleep(2)  # Let it write some records
    proc.send_signal(signal.SIGTERM)
    proc.wait(timeout=10)

    lines = (tmp_path / "out.log").read_text().strip().split("\n")
    assert len(lines) == 100, f"Expected 100 records, got {len(lines)}"
```

---

### Thread Safety Audit

**Problem:** LogEverything's `Logger`, `IndentManager`, and `LogBuffer` are used concurrently, but thread safety guarantees aren't documented per-method. Users need to know: "Can I share a `Logger` instance across threads?" (Yes — but is that actually tested under contention?)

#### Document thread safety contracts

**What to do:** Add a `Thread Safety` section to the docstring of every public class:

```python
class Logger(BaseLogger):
    """
    Primary user-facing logger.

    Thread Safety:
        Logger instances are safe to share across threads. All logging methods
        (debug, info, warning, error, critical) are thread-safe. The ``bind()``
        method returns a new bound logger and does not mutate the original.
        ``configure()`` is NOT thread-safe — call it once during setup, before
        spawning threads.

    Async Safety:
        Logger instances are safe to use from multiple asyncio tasks.
        Indentation and correlation context are isolated per-task via contextvars.
    """
```

**Classes to audit and document:**

| Class | Thread-safe? | Notes for docs |
|-------|-------------|----------------|
| `Logger` | Yes (logging methods), No (`configure()`) | Document the configure-once pattern |
| `AsyncLogger` | Yes (all methods) | Uses contextvars internally |
| `IndentManager` | Yes | Thread-local for sync, contextvars for async |
| `LogBuffer` | Yes | Protected by `threading.Lock` |
| `CorrelationFilter` | Yes | Reads from contextvars/thread-local |
| `HierarchyFilter` | Yes | Reads from IndentManager (thread-safe) |
| `PrettyFormatter` | Conditional | `formatTime` cache uses instance state — add `threading.Lock` around cache |

#### Race condition detection in CI

**What to build:** Run the concurrent test suite (from the Testing section above) under [ThreadSanitizer](https://github.com/google/sanitizers) or Python's `faulthandler` with a `SIGALRM`-based deadlock detector:

```yaml
# In .github/workflows/python-ci.yml, add a job:
  thread-safety:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - run: pip install -e ".[test]"
    - run: |
        python -c "import faulthandler; faulthandler.enable()"
        pytest tests/test_concurrent.py tests/test_stress.py -x -v --timeout=60
```

**The `--timeout=60` flag** ensures that if a deadlock occurs, the test fails with a traceback instead of hanging CI forever. Add `pytest-timeout` to `test` extras.

---

### Error Handling Hardening

**Problem:** A logging library must **never** crash the application. If a handler throws, if JSON serialization hits an unserializable object, if a network transport times out — the application must continue running. Currently, some of these paths propagate exceptions to the caller.

#### Handler isolation

**What to build:** Wrap every `handler.emit()` call so that one broken handler can't affect others or the caller:

```python
# In base/base_logger.py or logger.py, override the logging.Logger.callHandlers behavior:

def _safe_emit(handler, record):
    """Emit a record to a handler, swallowing any exception."""
    try:
        handler.emit(record)
    except Exception:
        # Log to stderr as a last resort (never recurse into LogEverything)
        import sys
        try:
            print(
                f"LogEverything: handler {handler.__class__.__name__} failed: "
                f"{sys.exc_info()[1]}",
                file=sys.stderr,
            )
        except Exception:
            pass  # Truly give up — no way to report this
```

**Where this applies:**
- `JSONHandler.emit()` — `json.dumps()` can raise `TypeError` for unserializable objects. Currently handled by the `_safe_serialize()` fallback, but verify coverage of all edge cases (circular references, C extension objects, memoryview).
- `FileHandler.emit()` — Disk full, permission denied, file deleted mid-write. Catch `OSError` and emit to stderr.
- Transport handlers — Network timeout, DNS failure, TLS errors. `LogBuffer` retry logic handles some of this, but verify the error path doesn't raise to the caller.
- `PrettyFormatter.format()` — String formatting with user-provided data can raise. Wrap and fall back to `repr()`.

#### Unserializable object fallback

**Problem:** `log.info("data", extra={"obj": some_c_extension_object})` can crash `JSONHandler` if the object isn't JSON-serializable.

**Current state:** `JSONHandler` has `_safe_serialize()` in `handlers.py` that catches common types. But it uses a whitelist approach — anything not in `_SERIALIZABLE_TYPES` falls through to `json.dumps()` which raises.

**Fix:** Change `_safe_serialize()` to use a blacklist/fallback approach:

```python
def _default_serializer(obj):
    """JSON fallback serializer: try common conversions, then repr()."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return repr(obj)  # Last resort: always works, never raises

# In JSONHandler.emit():
json.dumps(data, default=_default_serializer)
```

This ensures `json.dumps()` **never raises** regardless of what's in the record.

---

### Python Version Support

#### Drop Python 3.7

**Problem:** Python 3.7 reached end-of-life in June 2023. Supporting it prevents using modern features (`:=` walrus operator, `dict` union `|`, `match` statement, `typing` improvements) and adds CI matrix cost.

**What to change:**
- `setup.cfg`: Change `python_requires = >=3.7` to `python_requires = >=3.8`
- `.github/workflows/python-ci.yml`: Remove `'3.7'` from the matrix
- `CHANGELOG.md`: Note the Python 3.7 drop under a "Breaking Changes" heading
- Grep for `sys.version_info` guards and `typing_extensions` imports that were 3.7 workarounds — remove them

#### Add Python 3.12 and 3.13

**What to change:**
- `.github/workflows/python-ci.yml`: Add `'3.12'` and `'3.13'` to the matrix
- Test and fix any breakages from:
  - `importlib.metadata` API changes in 3.12
  - `asyncio` task group changes in 3.12
  - `warnings` module changes in 3.12
  - GIL-related changes in 3.13 (free-threaded build)
- `setup.cfg` classifiers: Add `Programming Language :: Python :: 3.12` and `3.13`

#### Free-threaded Python 3.13 (experimental)

**Problem:** Python 3.13 introduces a free-threaded build (no GIL). LogEverything's thread safety relies on the GIL for some implicit safety (e.g., `dict` operations in `_logger_cache`). Without the GIL, these become data races.

**What to do:**
- Add a CI job that runs tests on `python3.13t` (free-threaded build) with `PYTHON_GIL=0`
- Audit all shared mutable state (`_config`, `_logger_cache`, `_active_loggers`, `IndentManager._thread_local`) for GIL-dependent safety
- Add explicit locks where needed
- Mark this as experimental for v1.0 — full support in v1.1

```yaml
# In .github/workflows/python-ci.yml:
  free-threaded:
    runs-on: ubuntu-latest
    continue-on-error: true  # Experimental, don't gate release
    steps:
    - uses: actions/checkout@v4
    - uses: deadsnakes/action@v3.2.0
      with:
        python-version: '3.13-dev'
        nogil: true
    - run: pip install -e ".[test]"
    - run: PYTHON_GIL=0 pytest tests/ -x -v
```

---

### Distributed Tracing

**Problem:** LogEverything's `correlation_id` works within a single process. In microservice architectures, a single user request spans multiple services. There's no standard mechanism to propagate the correlation ID across HTTP calls, gRPC calls, or message queues.

#### Native trace context (W3C Trace Context)

Implement [W3C Trace Context](https://www.w3.org/TR/trace-context/) propagation — the industry standard for distributed trace headers.

**Outgoing requests:** When an application makes an HTTP call, automatically inject the `traceparent` header:
```
traceparent: 00-<trace_id>-<span_id>-<trace_flags>
```

**Incoming requests:** The existing framework middleware (FastAPI, Flask, Django) already reads `X-Request-ID`. Extend them to also read `traceparent` and extract the trace ID as the correlation ID.

**Implementation in `logeverything/tracing.py`:**
```python
class TraceContext:
    """W3C Trace Context propagation."""

    def inject_headers(self, headers: dict) -> dict:
        """Add traceparent header for outgoing HTTP calls."""
        cid = get_correlation_id()
        span_id = os.urandom(8).hex()
        headers["traceparent"] = f"00-{cid}-{span_id}-01"
        return headers

    def extract_headers(self, headers: dict) -> str:
        """Extract trace_id from incoming traceparent header."""
        tp = headers.get("traceparent", "")
        if tp:
            parts = tp.split("-")
            if len(parts) >= 3:
                return parts[1]  # trace_id
        return headers.get("x-request-id", os.urandom(8).hex())
```

#### Cross-service correlation

Auto-instrument popular HTTP clients to inject trace headers on outgoing calls:

```python
# Automatic instrumentation for requests library
from logeverything.tracing import instrument_requests
instrument_requests()  # Monkey-patches requests.Session to inject traceparent

# Automatic instrumentation for httpx
from logeverything.tracing import instrument_httpx
instrument_httpx()  # Hooks into httpx event system
```

**Implementation for `requests`** (in `logeverything/tracing.py`):

```python
_original_send = None

def instrument_requests():
    """Monkey-patch requests.Session.send to inject traceparent headers."""
    import requests

    global _original_send
    _original_send = requests.Session.send

    def _instrumented_send(self, request, **kwargs):
        tc = TraceContext()
        request.headers = tc.inject_headers(dict(request.headers))
        return _original_send(self, request, **kwargs)

    requests.Session.send = _instrumented_send


def uninstrument_requests():
    """Restore original requests.Session.send."""
    import requests
    if _original_send is not None:
        requests.Session.send = _original_send
```

**Implementation for `httpx`** (uses httpx's event hook system — no monkey-patching):

```python
def instrument_httpx():
    """Register a global event hook on httpx to inject traceparent."""
    import httpx

    def _inject_trace(request: httpx.Request):
        tc = TraceContext()
        for key, value in tc.inject_headers({}).items():
            request.headers[key] = value

    # httpx supports event hooks on Client instances
    _original_init = httpx.Client.__init__

    def _patched_init(self, *args, **kwargs):
        _original_init(self, *args, **kwargs)
        self.event_hooks.setdefault("request", []).append(_inject_trace)

    httpx.Client.__init__ = _patched_init
    # Same for AsyncClient
    _original_async_init = httpx.AsyncClient.__init__

    def _patched_async_init(self, *args, **kwargs):
        _original_async_init(self, *args, **kwargs)
        self.event_hooks.setdefault("request", []).append(_inject_trace)

    httpx.AsyncClient.__init__ = _patched_async_init
```

**For Celery:** Inject `traceparent` into task headers so the trace continues across workers:

```python
from celery.signals import before_task_publish, task_prerun

@before_task_publish.connect
def inject_trace_into_celery_headers(headers, **kwargs):
    tc = TraceContext()
    headers.update(tc.inject_headers({}))

@task_prerun.connect
def extract_trace_from_celery_headers(task, **kwargs):
    traceparent = task.request.get("traceparent", "")
    if traceparent:
        tc = TraceContext()
        trace_id = tc.extract_headers({"traceparent": traceparent})
        set_correlation_id(trace_id)
```

**Testing:** `tests/test_tracing.py` with mock HTTP servers (using `responses` or `respx` libraries) verifying that outgoing requests contain the `traceparent` header and incoming requests extract the trace ID correctly.

#### Trace visualization

**In the dashboard:** Add a waterfall view for distributed traces:

```
Service A: ████████████████████████████  120ms
  Service B:    ██████████████           45ms
    Service C:      ████████              22ms
  Service D:                ███████████  38ms
```

**API endpoint** (in `dashboard/main.py`):

```python
@app.get("/api/traces/{correlation_id}")
async def get_trace(correlation_id: str):
    """Fetch all log records for a trace, grouped by service."""
    logs = db.execute(
        "SELECT * FROM logs WHERE correlation_id = ? ORDER BY timestamp",
        (correlation_id,)
    ).fetchall()

    # Group by source (service name)
    services = {}
    for log_entry in logs:
        source = log_entry["source"] or "unknown"
        if source not in services:
            services[source] = {"first": log_entry["timestamp"], "last": log_entry["timestamp"], "logs": []}
        services[source]["last"] = log_entry["timestamp"]
        services[source]["logs"].append(log_entry)

    # Calculate relative offsets from the earliest timestamp
    trace_start = min(s["first"] for s in services.values())
    spans = []
    for source, data in services.items():
        offset_ms = (parse_ts(data["first"]) - parse_ts(trace_start)).total_seconds() * 1000
        duration_ms = (parse_ts(data["last"]) - parse_ts(data["first"])).total_seconds() * 1000
        spans.append({
            "service": source,
            "offset_ms": offset_ms,
            "duration_ms": max(duration_ms, 1),  # At least 1ms for visibility
            "log_count": len(data["logs"]),
            "has_errors": any(l["level"] in ("ERROR", "CRITICAL") for l in data["logs"]),
        })

    return {"correlation_id": correlation_id, "total_ms": ..., "spans": spans}
```

**Dashboard page:** New template `dashboard/templates/traces.html`:
- Search bar: enter a correlation ID or click one from the Logs page
- Waterfall chart rendered as horizontal bars using inline CSS `width` + `margin-left` percentages (no JS chart library needed)
- Each bar is clickable — expands to show the individual log entries for that service
- Color coding: green for normal spans, red for spans containing errors
- Summary row at the top: total duration, number of services involved, error count

**Navigation integration:**
- In the Logs table, make `correlation_id` values clickable links to `/traces/{correlation_id}`
- Add a "Traces" item to the sidebar navigation

#### Sampling

At high volume, tracing every request is impractical. Implement two sampling strategies:

1. **Head-based sampling** — Decide at request entry whether to trace (e.g., 10% of requests). Set `trace_flags=00` for unsampled requests — they still get correlation IDs but are excluded from the dashboard's trace view.

2. **Tail-based sampling** — Collect all traces but only persist interesting ones (errors, slow requests, specific user IDs). Requires a short buffer of recent traces and a decision function:
   ```python
   def should_persist(trace_logs):
       return any(log.level >= ERROR for log in trace_logs) or trace_duration > 5000
   ```

---

### Performance

#### Zero-copy JSON serialization

**Problem:** `JSONHandler` uses `json.dumps()` from the standard library, which is pure Python and relatively slow. At high throughput (>100k records/sec), JSON serialization becomes the bottleneck.

**What to build:** Conditional use of `orjson` (Rust-based, 10-50x faster) or `msgspec` (C-based, comparable speed) when available:

```python
# In handlers.py JSONHandler:
try:
    import orjson
    def _serialize(data):
        return orjson.dumps(data).decode()  # orjson returns bytes
except ImportError:
    try:
        import msgspec.json
        _encoder = msgspec.json.Encoder()
        def _serialize(data):
            return _encoder.encode(data).decode()
    except ImportError:
        import json
        def _serialize(data):
            return json.dumps(data)
```

**Target:** 500k+ records/sec serialization throughput (current: ~50-100k with stdlib json).

The `json` extras in `setup.cfg` already declares `orjson>=3.5.0`. This just needs the conditional import path in the handler.

#### Memory-mapped file handler

**Problem:** Each `emit()` call does a `file.write()` + selective `file.flush()`, which is two syscalls. At high volume, syscall overhead adds up.

**What to build:** An `MmapFileHandler` that writes to a memory-mapped file region:

```python
import mmap

class MmapFileHandler(FileHandler):
    def __init__(self, filename, mmap_size=64*1024*1024, **kwargs):
        # Pre-allocate a 64MB file and mmap it
        # Writes go to memory, OS flushes to disk asynchronously
        ...
```

**Trade-offs:** Faster writes but more complex file management (need to handle file growth, remapping, and crash recovery). Best suited for high-throughput batch workloads, not general use. Ship as an advanced handler, not the default.

#### Lock-free buffer

**Problem:** `LogBuffer` in `transport/buffer.py` uses `threading.Lock` + `threading.Condition` for thread coordination. Under high contention (many threads logging simultaneously), lock acquisition becomes a bottleneck.

**What to build:** Replace the `deque` + `Lock` with a lock-free ring buffer:

```python
import ctypes

class RingBuffer:
    """Lock-free single-producer/single-consumer ring buffer using atomic operations."""
    def __init__(self, capacity):
        self._capacity = capacity
        self._buffer = [None] * capacity
        self._head = ctypes.c_long(0)  # Producer writes here
        self._tail = ctypes.c_long(0)  # Consumer reads here
```

**Caveat:** Lock-free data structures are notoriously hard to get right. The current `Lock`-based approach works correctly — only pursue this if profiling shows lock contention is a real bottleneck, not a theoretical one. Consider using `queue.SimpleQueue` (Python 3.7+, uses a C-level lock that's cheaper than `threading.Lock`) as a simpler intermediate step.

#### Lazy argument evaluation

**Problem:** `log.debug(f"User {get_user_details(uid)}")` calls `get_user_details()` even when DEBUG logging is disabled. This is wasteful for expensive computations.

**What to build:** A deferred evaluation API:

```python
# Option 1: %-style formatting (already lazy in Python logging)
log.debug("User %s", get_user_details(uid))  # Only evaluates if DEBUG enabled

# Option 2: Lambda-based deferred evaluation (new)
log.debug(lambda: f"User {get_user_details(uid)}")  # Only evaluates if DEBUG enabled

# Option 3: Explicit lazy wrapper (new)
from logeverything import lazy
log.debug("User {details}", details=lazy(get_user_details, uid))
```

**Implementation for Option 2:** In `BaseLogger.debug()`, check if the message argument is callable. If so, only call it if the effective level permits:

```python
def debug(self, msg, *args, **kwargs):
    if self._logger.isEnabledFor(logging.DEBUG):
        if callable(msg):
            msg = msg()
        self._logger.debug(msg, *args, **kwargs)
```

---

### Dashboard v2

#### Saved views

**Problem:** Users repeatedly apply the same filter combinations (e.g., "errors from payment-service in the last hour"). Each time they navigate to the Logs page, they have to re-apply filters.

**What to build:**
- Save button next to the filter bar that persists current filters + view mode + page size as a named view in SQLite
- Dropdown in the sidebar showing saved views
- Share views via URL query parameters: `/logs?view=payment-errors`

**Database schema** (in `dashboard/services.py` or a new `dashboard/models.py`):

```sql
CREATE TABLE IF NOT EXISTS saved_views (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    slug        TEXT    NOT NULL UNIQUE,   -- URL-safe version of name
    filters     TEXT    NOT NULL,          -- JSON: {"level": "ERROR", "source": "payment-service"}
    hours       INTEGER NOT NULL DEFAULT 24,
    view_mode   TEXT    NOT NULL DEFAULT 'list',  -- "list", "tree", "raw"
    page_size   INTEGER NOT NULL DEFAULT 50,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

**API endpoints** (in `dashboard/main.py`):

```python
@app.post("/api/views")
async def create_view(name: str, filters: dict, hours: int = 24, view_mode: str = "list", page_size: int = 50):
    slug = slugify(name)  # "Payment Errors" → "payment-errors"
    db.execute("INSERT INTO saved_views (name, slug, filters, hours, view_mode, page_size) VALUES (?, ?, ?, ?, ?, ?)",
               (name, slug, json.dumps(filters), hours, view_mode, page_size))
    return {"slug": slug}

@app.get("/api/views")
async def list_views():
    rows = db.execute("SELECT slug, name, filters, hours, view_mode, page_size FROM saved_views ORDER BY name").fetchall()
    return [{"slug": r[0], "name": r[1], "filters": json.loads(r[2]), "hours": r[3], "view_mode": r[4], "page_size": r[5]} for r in rows]

@app.delete("/api/views/{slug}")
async def delete_view(slug: str):
    db.execute("DELETE FROM saved_views WHERE slug = ?", (slug,))
```

**Client-side** (in `dashboard/static/js/dashboard.js`):
- "Save View" button in the filter bar that opens a modal for naming the view
- Sidebar renders saved views from `GET /api/views` on page load
- Clicking a saved view applies its filters and navigates to `/logs?view={slug}`
- On `/logs?view={slug}`, the page fetches the view config and pre-populates all filter controls

#### Alerting

**Problem:** The dashboard is passive — you have to look at it to notice problems. Real monitoring requires proactive notifications when things go wrong.

**What to build:**
- Alert rules defined in the dashboard UI: condition + action
- Background task that evaluates rules against recent log data every evaluation interval
- Alert history page showing past alerts, when they fired, and when they resolved
- Integration with the WebSocket system for real-time alert banners in the dashboard

**Database schema:**

```sql
CREATE TABLE IF NOT EXISTS alert_rules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    enabled         INTEGER NOT NULL DEFAULT 1,
    -- Condition
    metric          TEXT    NOT NULL,  -- "error_count", "log_rate", "pattern_match"
    operator        TEXT    NOT NULL,  -- "gt", "lt", "eq"
    threshold       REAL    NOT NULL,  -- e.g. 10
    window_seconds  INTEGER NOT NULL,  -- e.g. 300 (5 minutes)
    filters         TEXT,              -- JSON: {"level": "ERROR", "source": "payment-service"}
    pattern         TEXT,              -- regex for pattern_match metric
    -- Action
    action_type     TEXT    NOT NULL,  -- "webhook", "slack", "email"
    action_config   TEXT    NOT NULL,  -- JSON: {"url": "https://hooks.slack.com/...", "channel": "#alerts"}
    -- Cooldown (avoid alert storms)
    cooldown_seconds INTEGER NOT NULL DEFAULT 300,
    last_fired_at   TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS alert_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id     INTEGER NOT NULL REFERENCES alert_rules(id),
    fired_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    resolved_at TEXT,
    metric_value REAL   NOT NULL,  -- the actual value that triggered the alert
    details     TEXT               -- JSON with context (sample log messages, etc.)
);
```

**Evaluation engine** (new file: `dashboard/alerting.py`):

```python
import asyncio
import aiohttp

class AlertEvaluator:
    """Periodically checks alert rules against log data."""

    def __init__(self, db, interval: int = 30):
        self._db = db
        self._interval = interval

    async def start(self):
        """Run as a background task in the FastAPI app lifespan."""
        while True:
            await self._evaluate_all_rules()
            await asyncio.sleep(self._interval)

    async def _evaluate_all_rules(self):
        rules = self._db.execute(
            "SELECT * FROM alert_rules WHERE enabled = 1"
        ).fetchall()
        for rule in rules:
            value = await self._compute_metric(rule)
            if self._threshold_breached(rule, value):
                if not self._in_cooldown(rule):
                    await self._fire_alert(rule, value)

    async def _compute_metric(self, rule) -> float:
        """Query log counts/rates for the rule's time window and filters."""
        window_start = datetime.utcnow() - timedelta(seconds=rule["window_seconds"])
        filters = json.loads(rule["filters"] or "{}")
        # Build SQL WHERE clause from filters + window
        query = "SELECT COUNT(*) FROM logs WHERE timestamp >= ?"
        params = [window_start.isoformat()]
        if "level" in filters:
            query += " AND level = ?"
            params.append(filters["level"])
        if "source" in filters:
            query += " AND source = ?"
            params.append(filters["source"])
        return self._db.execute(query, params).fetchone()[0]

    async def _fire_alert(self, rule, value):
        """Send notification and record in history."""
        payload = {
            "alert": rule["name"],
            "metric": rule["metric"],
            "value": value,
            "threshold": rule["threshold"],
            "fired_at": datetime.utcnow().isoformat(),
        }
        if rule["action_type"] == "webhook" or rule["action_type"] == "slack":
            config = json.loads(rule["action_config"])
            async with aiohttp.ClientSession() as session:
                await session.post(config["url"], json=payload)

        self._db.execute(
            "INSERT INTO alert_history (rule_id, metric_value, details) VALUES (?, ?, ?)",
            (rule["id"], value, json.dumps(payload)),
        )
        self._db.execute(
            "UPDATE alert_rules SET last_fired_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), rule["id"]),
        )
```

**Dashboard UI:**
- Alert Rules page (`/alerts`): table of rules with enable/disable toggle, create/edit modal
- Alert History page (`/alerts/history`): timeline of past alerts with status (active/resolved)
- Real-time banner: when an alert fires, broadcast via WebSocket to show a dismissible banner at the top of every dashboard page

**Webhook payload format** (for Slack/generic webhooks):
```json
{
  "alert": "High Error Rate",
  "metric": "error_count",
  "value": 47,
  "threshold": 10,
  "window_seconds": 300,
  "filters": {"level": "ERROR", "source": "payment-service"},
  "fired_at": "2026-02-24T14:30:00Z",
  "dashboard_url": "https://dashboard.example.com/logs?level=ERROR&source=payment-service&hours=1"
}

#### Multi-tenant

**Problem:** In organizations with multiple teams, all logs flow into the same dashboard instance. There's no isolation between teams.

**What to build:**
- Tenant concept: each tenant has its own namespace
- Tenant selector in the sidebar
- API key scoped to a tenant — the `api_key` parameter in `HTTPTransportHandler` determines which tenant the logs belong to
- Tenant-specific retention policies

**Database schema changes:**

```sql
CREATE TABLE IF NOT EXISTS tenants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,       -- "payment-team", "platform-team"
    slug            TEXT    NOT NULL UNIQUE,
    api_key         TEXT    NOT NULL UNIQUE,        -- UUID, used by HTTPTransportHandler
    retention_days  INTEGER NOT NULL DEFAULT 30,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Add tenant_id to the logs table (new column or new table per tenant)
ALTER TABLE logs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX idx_logs_tenant ON logs(tenant_id, timestamp);
```

**Approach: row-level filtering** (simpler than separate tables per tenant):
- All logs go into the same `logs` table with a `tenant_id` foreign key
- Every query in `dashboard/services.py` adds `WHERE tenant_id = ?` based on the current session
- The ingestion endpoint (`/api/ingest`) resolves `tenant_id` from the `X-API-Key` header

**Middleware** (in `dashboard/main.py`):

```python
from starlette.middleware.base import BaseHTTPMiddleware

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Resolve tenant from session cookie or API key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            tenant = db.execute("SELECT * FROM tenants WHERE api_key = ?", (api_key,)).fetchone()
        else:
            tenant_slug = request.session.get("tenant")
            tenant = db.execute("SELECT * FROM tenants WHERE slug = ?", (tenant_slug,)).fetchone()

        request.state.tenant = tenant
        response = await call_next(request)
        return response
```

**Client-side:** Tenant selector dropdown in the sidebar header (populated from `GET /api/tenants`). Selecting a tenant stores it in the session and reloads the current page. All dashboard pages read `request.state.tenant` to scope their queries.

#### Log aggregation

**Problem:** When an error occurs in a loop, the dashboard shows 10,000 identical error messages. This wastes screen space and makes it hard to see other events.

**What to build:**
- Pattern detection: group consecutive log messages with the same template
- Display as a single row with a count badge: `"Connection failed to db:5432" (x10,247)`
- Click to expand and see individual entries with timestamps

**Template extraction algorithm** (new file: `dashboard/aggregation.py`):

```python
import re

# Patterns that represent variable data (not structure)
_VARIABLE_PATTERNS = [
    (re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), '{ip}'),           # IPv4
    (re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.I), '{uuid}'),  # UUID
    (re.compile(r'\b[0-9a-f]{24}\b'), '{id}'),                                    # MongoDB ObjectId
    (re.compile(r'\b\d+\.\d+\b'), '{float}'),                                     # Floats
    (re.compile(r'\b\d{4,}\b'), '{num}'),                                          # Numbers (4+ digits)
    (re.compile(r'"[^"]{20,}"'), '{str}'),                                         # Long quoted strings
]

def extract_template(message: str) -> str:
    """
    Replace variable parts of a log message with placeholders.

    Examples:
        "Connection failed to 10.0.1.5:5432"  → "Connection failed to {ip}:5432"
        "User 12345 logged in from 192.168.1.1" → "User {num} logged in from {ip}"
        "Request abc12def-1234-5678-9abc-def012345678 took 123.45ms"
          → "Request {uuid} took {float}ms"
    """
    template = message
    for pattern, replacement in _VARIABLE_PATTERNS:
        template = pattern.sub(replacement, template)
    return template


def aggregate_logs(logs: list, max_gap_seconds: float = 2.0) -> list:
    """
    Group consecutive logs with the same template and level.

    Returns list of:
      {"template": str, "count": int, "first": log, "last": log, "sample": log}
    """
    groups = []
    current_group = None

    for log_entry in logs:
        template = extract_template(log_entry["message"])
        key = (template, log_entry["level"])

        if current_group and current_group["key"] == key:
            time_gap = parse_timestamp(log_entry["timestamp"]) - parse_timestamp(current_group["last"]["timestamp"])
            if time_gap.total_seconds() <= max_gap_seconds:
                current_group["count"] += 1
                current_group["last"] = log_entry
                continue

        # Start a new group
        if current_group:
            groups.append(current_group)
        current_group = {
            "key": key,
            "template": template,
            "count": 1,
            "first": log_entry,
            "last": log_entry,
            "sample": log_entry,
        }

    if current_group:
        groups.append(current_group)
    return groups
```

**Dashboard UI changes:**
- Toggle button "Group similar" in the log filter bar (default: off)
- When enabled, the Logs page calls `aggregate_logs()` on the server before rendering
- Grouped rows show: template text, count badge, timestamp range (first..last), expand chevron
- Clicking expand fetches individual entries from `/api/logs?template={template}&from={first_ts}&to={last_ts}`

**API endpoint:**

```python
@app.get("/api/logs/aggregated")
async def get_aggregated_logs(hours: int = 24, level: Optional[str] = None, source: Optional[str] = None):
    logs = await get_filtered_logs(hours=hours, level=level, source=source)
    groups = aggregate_logs(logs)
    return [
        {"template": g["template"], "count": g["count"],
         "first_at": g["first"]["timestamp"], "last_at": g["last"]["timestamp"],
         "level": g["sample"]["level"], "source": g["sample"].get("source")}
        for g in groups
    ]
```

#### Embedded mode

**Problem:** Some teams already have an admin panel or internal tool. They want to embed the LogEverything dashboard inside it, not run a separate URL.

**What to build:**
- An `<iframe>`-embeddable version of each dashboard page
- `?embed=true` query parameter that hides the sidebar and header, showing only the content
- CORS configuration to allow embedding from approved origins
- PostMessage API for parent-child communication (e.g., parent sends time range changes)

#### Live tail

**Problem:** Developers running a service locally want a `tail -f` experience in the dashboard — new log records stream in real-time without manual refresh. The auto-refresh toggle exists but polls on an interval, which introduces latency and wastes bandwidth when nothing is happening.

**What to build:**
- WebSocket push from the dashboard server to the browser on every new log record
- The existing `WebSocketServer` in `logeverything/monitoring/` already handles connections — extend it to broadcast new records as they arrive
- Client-side: `dashboard/static/js/dashboard.js` subscribes to the WebSocket and prepends new rows to the log table without a full page reload
- Auto-scroll toggle: when enabled, the log view stays pinned to the bottom (newest); when disabled, the user can scroll freely without being interrupted
- Rate limiting: if logs arrive faster than 100/sec, buffer and batch-deliver every 100ms to avoid overwhelming the browser DOM

**Implementation sketch for the server side:**

```python
# In dashboard/connections.py or a new dashboard/live_tail.py:

async def broadcast_log_record(record: dict):
    """Push a new log record to all connected live-tail clients."""
    message = json.dumps({"type": "log", "data": record})
    for ws in _active_websockets:
        try:
            await ws.send_text(message)
        except Exception:
            _active_websockets.discard(ws)
```

**Client-side in `dashboard/static/js/dashboard.js`:**

```javascript
function connectLiveTail() {
    const ws = new WebSocket(`ws://${location.host}/ws/live`);
    ws.onmessage = (event) => {
        const { type, data } = JSON.parse(event.data);
        if (type === "log") {
            prependLogRow(data);
            if (autoScrollEnabled) {
                scrollToBottom();
            }
        }
    };
}
```

#### Export & sharing

**Problem:** Users need to extract log data for incident reports, Slack threads, or Jira tickets. Currently there's no export mechanism — users copy-paste from the browser.

**What to build:**
- Export button on the Logs page that downloads the current filtered view as:
  - **CSV** — For spreadsheet analysis
  - **JSON Lines** — For programmatic processing
  - **Plain text** — For pasting into incident reports
- Copy-to-clipboard button for individual log entries
- Shareable permalink: `/logs?filter=...&from=...&to=...` that encodes the current filter state in the URL so users can share exact views

**Implementation:** Add an `/api/export` endpoint in `dashboard/main.py` that accepts the current filter parameters and streams the response with `Content-Disposition: attachment`:

```python
@app.get("/api/export")
async def export_logs(
    format: str = "jsonl",  # "jsonl", "csv", "text"
    level: Optional[str] = None,
    source: Optional[str] = None,
    hours: int = 24,
):
    logs = await get_filtered_logs(level=level, source=source, hours=hours)
    if format == "csv":
        content = format_as_csv(logs)
        media_type = "text/csv"
    elif format == "text":
        content = format_as_text(logs)
        media_type = "text/plain"
    else:
        content = "\n".join(json.dumps(log) for log in logs)
        media_type = "application/x-ndjson"

    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=logs.{format}"},
    )
```

---

### Release Checklist

A step-by-step checklist for the maintainer cutting the 1.0.0 release. This supplements the graduation criteria above with the mechanical steps:

1. [ ] Create a `release/1.0` branch from `main`
2. [ ] Run the full CI matrix locally: `make all` (clean, format, lint, test, docs, build)
3. [ ] Run stress tests: `pytest tests/test_stress.py tests/test_concurrent.py -v`
4. [ ] Verify coverage: `pytest --cov=logeverything tests/ --cov-fail-under=90`
5. [ ] Verify docs build with zero warnings: `make docs 2>&1 | grep -c WARNING` returns 0
6. [ ] Verify `logeverything doctor` passes all checks
7. [ ] Update `__version__` in `logeverything/__init__.py` to `"1.0.0"`
8. [ ] Finalize CHANGELOG.md: move all Unreleased items under `## [1.0.0] - YYYY-MM-DD`
9. [ ] Update README badges and compatibility table
10. [ ] Commit: `git commit -m "Release v1.0.0"`
11. [ ] Tag: `git tag v1.0.0`
12. [ ] Push: `git push origin main v1.0.0`
13. [ ] Wait for CI: test → build → **approve publish** in GitHub Actions
14. [ ] Verify PyPI release: `pip install logeverything==1.0.0`
15. [ ] Create GitHub Discussion announcing the release with highlights

---

## Future Ideas (Unscheduled)

These are longer-term ideas that may or may not happen depending on community demand. They're included here for inspiration and to collect interest signals.

### Language & Runtime

- **Rust core via PyO3** — Rewrite performance-critical paths (JSON serialization, buffer management, regex-based PII redaction, hash chain computation) in Rust and expose via PyO3 bindings. Target: 10x throughput improvement for the hot path. This is a major undertaking — only justified if Python-level optimizations (orjson, lock-free buffers) prove insufficient.

- **WASM dashboard** — Compile the dashboard's data processing logic to WebAssembly for offline log analysis. Users could drag-and-drop a JSON Lines file into the browser and get the full dashboard experience without a running server. Uses Pyodide or a Rust-based WASM module.

- **GraalPy support** — Verify LogEverything runs on GraalPy (Python on the JVM via GraalVM). This enables Java/Kotlin applications to use LogEverything for unified logging across JVM and Python components. Requires testing: contextvars behavior, threading model, and C extension compatibility.

### AI & ML

- **Anomaly detection** — A lightweight ML model (isolation forest or autoencoder) that trains on normal log patterns and flags anomalies: sudden error spikes, new error messages never seen before, latency outliers, unusual source distributions. Runs as a background task in the dashboard. No external ML dependencies — use scikit-learn or a pure-Python implementation.

- **Log clustering** — Automatically group similar log messages using TF-IDF or sentence embeddings (via `sentence-transformers`). Instead of showing 50 variations of "Connection timeout to {host}", show one cluster with a representative message and count. Useful for the dashboard's log aggregation feature.

- **Natural language queries** — "Show me all errors from the payment service in the last hour" → translates to `SELECT * FROM logs WHERE level='ERROR' AND source='payment-service' AND timestamp > now() - interval '1 hour'`. Uses an LLM API or a local model for query translation. Experimental — accuracy and latency are concerns.

- **Auto-instrumentation** — Use Python's AST module to automatically decorate all functions in a module with `@log` without manual annotation. `logeverything.auto_instrument("my_package")` walks the module tree, wraps all functions, and provides opt-out via `@no_log` decorator. Useful for quick debugging sessions but not recommended for production (too much noise).

### Ecosystem

- **VS Code extension** — Inline log preview (hover over a `@log` decorator to see recent log output), click-to-navigate from log output back to source code (using file:line references in log records), decorator auto-insertion (right-click a function → "Add LogEverything decorator"). Built with the VS Code Extension API + a lightweight language server.

- **GitHub Actions integration** — A GitHub Action that runs after CI tests and posts a log summary as a PR comment: total log count, error count, slowest decorated functions, and any new error messages not seen in the base branch. Helps reviewers understand the runtime behavior of PR changes.

- **Jupyter widget** — An interactive log viewer widget for Jupyter notebooks using `ipywidgets`. Shows logs from the current notebook session with filtering, search, and tree view. Integrates with LogEverything's notebook environment detection (already in `core.py`).

- **Grafana data source plugin** — A Grafana plugin that queries LogEverything's dashboard API or SQLite database directly. Enables displaying LogEverything data alongside Prometheus metrics, traces, and other data sources in Grafana dashboards. Built with the Grafana plugin SDK (Go or TypeScript).

### Protocol & Standards

- **CEF (Common Event Format)** — Handler that formats log records as CEF strings for SIEM systems (Splunk, IBM QRadar, ArcSight). CEF has a fixed header format (`CEF:0|vendor|product|version|event_id|name|severity|extensions`) plus extension key-value pairs. Maps LogEverything fields to CEF extensions.

- **Syslog (RFC 5424)** — Standard syslog handler with structured data elements. Sends log records to a syslog server (rsyslog, syslog-ng) over UDP, TCP, or TLS. Includes structured data IDs for LogEverything-specific fields: `[logeverything@12345 call_id="abc" indent_level="2"]`.

- **GELF (Graylog Extended Log Format)** — Handler for Graylog ingestion over UDP or TCP. GELF is JSON-based with mandatory fields (`version`, `host`, `short_message`, `timestamp`) and arbitrary additional fields prefixed with `_`. LogEverything fields map naturally: `_correlation_id`, `_call_id`, `_log_type`.

- **Fluentd/Fluent Bit forward protocol** — Native handler that speaks the Fluentd forward protocol (MessagePack over TCP). This allows LogEverything to feed directly into Fluentd/Fluent Bit log pipelines without intermediate files or HTTP. Uses the `msgpack` library for serialization.

---

## Contributing

Interested in working on any of these? Open an issue referencing the specific roadmap item, or submit a PR. Items marked with `[ ]` are open for contribution. Priority items for the next release are at the top of each section.

For implementation questions, the technical details in this document should provide enough context to get started. If something is unclear, open a discussion thread.
