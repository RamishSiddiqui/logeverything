# LogEverything Monitoring System

A robust, comprehensive monitoring solution that automatically tracks everything in your Python application with minimal setup.

## 🚀 Quick Start

```python
from logeverything.monitoring import start_monitoring

# Start monitoring with one line
start_monitoring(output_dir="./monitoring_data")

# Your application code here - everything is now being monitored!

# That's it! Monitoring auto-stops on exit
```

## ✨ Features

### 📊 **Automatic System Monitoring**
- CPU, memory, disk, and network usage
- Process-specific metrics
- Real-time performance tracking
- Historical data storage

### 📝 **Structured Logging**
- JSON-formatted logs for easy parsing
- Automatic correlation IDs
- Thread-safe operations
- Automatic log rotation

### 🔌 **API Integration**
- RESTful API for dashboard integration
- Real-time data access
- CORS-enabled for web dashboards
- Health checks and status endpoints

### 💾 **Smart Data Storage**
- SQLite for structured metrics
- JSON Lines for logs
- Automatic cleanup and rotation
- Export capabilities

## 🎯 Core Architecture

```
logeverything/monitoring/
├── __init__.py       # Simple interface (start_monitoring, stop_monitoring)
├── core.py          # MonitoringSystem orchestrator
├── logger.py        # StructuredLogger with JSON output
├── metrics.py       # MetricsCollector for system/app metrics
├── storage.py       # MonitoringStorage (SQLite + JSONL)
└── api_server.py    # MonitoringAPIServer for dashboard integration
```

## 📈 Usage Examples

### Basic Monitoring
```python
from logeverything.monitoring import start_monitoring, stop_monitoring

# Start monitoring
monitor = start_monitoring(
    output_dir="./monitoring_data",
    enable_api=True,
    api_port=8999,
    metrics_interval=5.0
)

# Your application code...

# Optional explicit stop (auto-stops on exit)
stop_monitoring()
```

### Advanced Context Manager
```python
from logeverything.monitoring import MonitoringSystem

with MonitoringSystem(output_dir="./monitoring") as monitor:
    # Everything in this block is monitored
    your_application_code()
```

### Custom Metrics and Operations
```python
from logeverything.monitoring import get_monitoring_system

monitor = get_monitoring_system()

# Track custom operations
with monitor.metrics_collector.track_operation("data_processing"):
    process_data()

# Custom logging
monitor.logger.info("Processing started", extra={"batch_size": 1000})
```

## 🌐 Dashboard Integration

The monitoring system provides a REST API that the `logeverything-dashboard` can connect to:

### API Endpoints
- `GET /health` - Health check
- `GET /metrics/system` - Current system metrics
- `GET /metrics/system/recent` - Historical metrics
- `GET /operations/recent` - Recent operations
- `GET /operations/summary` - Operation statistics
- `GET /system/trends` - System trends
- `GET /export` - Export all data

### Dashboard Connection
```python
# Start monitoring with API enabled
start_monitoring(
    output_dir="./monitoring_data",
    enable_api=True,
    api_port=8999
)

# Dashboard connects to: http://localhost:8999
```

## 💡 Key Design Principles

### ✅ **Simple Interface**
- One function to start monitoring everything
- Zero configuration required for basic use
- Sensible defaults for all settings

### ✅ **No Pollution**
- All monitoring code consolidated in `/monitoring/`
- Clean, organized module structure
- No scattered files or configuration

### ✅ **High Performance**
- Minimal overhead on your application
- Background collection of metrics
- Thread-safe operations
- Efficient data storage

### ✅ **Production Ready**
- Automatic cleanup and rotation
- Error handling and recovery
- Resource usage monitoring
- Clean shutdown procedures

## 📂 Output Structure

```
monitoring_data/
├── logs/
│   ├── app_logs_20250702_143021_0001.jsonl
│   └── app_logs_20250702_143021_0002.jsonl
├── monitoring.db (SQLite database)
└── session_info.json
```

### Log Format (JSON Lines)
```json
{
  "timestamp": "2025-07-02T14:30:21.123Z",
  "level": "INFO",
  "logger": "logeverything.monitoring",
  "message": "Operation completed",
  "correlation_id": "op_1719234621123",
  "operation": {
    "operation_id": "op_1719234621123",
    "operation_name": "data_processing",
    "duration_seconds": 1.234
  }
}
```

## 🔧 Configuration Options

```python
start_monitoring(
    output_dir="./monitoring_data",     # Where to store data
    enable_api=True,                    # Enable REST API
    api_port=8999,                      # API server port
    metrics_interval=5.0,               # Metrics collection interval
    max_log_files=100,                  # Max log files to keep
    max_log_size_mb=50                  # Max size per log file
)
```

## 🚀 Integration with LogEverything Dashboard

1. Start monitoring in your application:
```python
start_monitoring(enable_api=True, api_port=8999)
```

2. Launch the dashboard:
```bash
cd logeverything-dashboard
python -m dashboard.main --api-url http://localhost:8999
```

3. View real-time monitoring at: http://localhost:3000

## 🔍 Troubleshooting

### Missing Dependencies
```bash
pip install psutil fastapi uvicorn
```

### Port Already in Use
```python
start_monitoring(api_port=9000)  # Use different port
```

### Permission Issues
```python
start_monitoring(output_dir="./monitoring")  # Use relative path
```

## 📊 What Gets Monitored

### System Metrics
- CPU usage (overall and per-core)
- Memory usage (RAM and swap)
- Disk usage and I/O
- Network usage
- Process-specific metrics

### Application Data
- All function calls and performance
- Error rates and exceptions
- Custom operations and metrics
- Log messages with context

### API Access
- Real-time current metrics
- Historical data queries
- Operation summaries
- System trends and patterns

This monitoring system provides everything you need to understand your application's behavior and performance with minimal setup and maximum insight!
