# LogEverything Dashboard

A modern, standalone monitoring dashboard for LogEverything systems.

> **Note**: This is designed to be used as a git submodule within LogEverything projects.

## ✨ Features

- **SCSS Styling**: Modern SCSS architecture with automatic compilation
- **Multiple Connections**: Configure and switch between local and API connections via the UI
- **Connection Testing**: Test connections before saving them to ensure they work
- **Theme Toggle**: Switch between dark and light themes
- **Modular UI**: Clean, modular components for better maintainability
- **Enhanced Modals**: Improved modal interactivity and accessibility
- **Professional Notifications**: Toast notifications for user feedback

### Analytics & Visualization (New)

- **CPU/Memory Trend Chart**: Chart.js time-series line chart showing system resource usage over time
- **Log Level Distribution**: Doughnut chart breaking down log entries by level (DEBUG through CRITICAL)
- **Operation Analytics**: Top operations table with counts, avg duration, failure counts, and failure rate percentages
- **Time-Range Filtering**: Global 1h / 6h / 24h / 7d selector that filters charts, operations, logs, and analytics simultaneously
- **Full-Text Log Search**: Search across log messages with the filter bar (keyboard shortcut: `/`)
- **Data Export**: One-click JSON export of all dashboard data for the selected time range
- **Auto-Refresh Toggle**: Pause/resume all HTMX polling and chart auto-refresh (keyboard shortcut: `r`)
- **System Detail Modal**: Expandable view showing swap, disk I/O, threads, file descriptors, uptime, and session info
- **Error Message Display**: Failed operations show truncated error text inline in the operations table
- **Keyboard Shortcuts**: `r` toggle refresh, `/` focus search, `e` export, `Escape` close modals

## 🎨 SCSS Integration

The dashboard now uses SCSS for styling, providing better organization and maintainability:

### SCSS Structure

- `dashboard/static/scss/main.scss`: Main entry point
- `dashboard/static/scss/_variables.scss`: Global variables (colors, fonts, spacing)
- `dashboard/static/scss/_base.scss`: Base styles
- `dashboard/static/scss/_layout.scss`: Layout components
- `dashboard/static/scss/components/`: Component-specific styles
  - `_analytics.scss` - Compact tables, analytics stat rows
  - `_badges.scss` - Status and level badges
  - `_buttons.scss` - Buttons and icon buttons
  - `_cards.scss` - Summary and content cards
  - `_charts.scss` - Chart.js container sizing
  - `_connections.scss` - Connection management UI
  - `_forms.scss` - Form inputs and selects
  - `_header.scss` - Dashboard header and controls
  - `_logs_filter.scss` - Log filter bar
  - `_modals.scss` - Modal dialogs
  - `_tables.scss` - Data tables
  - `_time_range.scss` - Time-range selector pills
  - `_toast.scss` - Toast notifications
  - `_trace.scss` - Trace view
- `dashboard/static/scss/themes/`: Theme-specific styles
  - `_dark.scss`
  - `_light.scss`
- `dashboard/static/scss/_utilities.scss`: Utility classes

### SCSS Compilation

The SCSS files are automatically compiled to CSS when the dashboard is started using the provided script:

```bash
python run_dashboard.py
```

This script:
1. Compiles SCSS to CSS at startup
2. Watches for changes and recompiles automatically
3. Starts the dashboard server

For manual compilation:

```bash
python -m dashboard.compile_scss
```

To watch for changes:

```bash
python -m dashboard.compile_scss --watch
```

## 🔌 Connection Management

The dashboard supports multiple connections with a professional user interface:

### Features

- **Connection Types**: Support for both local file-based and remote API connections
- **Connection Testing**: Test connections before saving to ensure they work properly
- **Connection Switching**: Easily switch between configured connections
- **Persistent Storage**: Connections are saved and loaded automatically
- **Modal Interface**: Professional, accessible modal UI for managing connections

### How to Use

1. Click the "Connections" button in the header
2. The modal will open showing your existing connections
3. Click "New Connection" to add a connection
4. Fill in the required fields:
   - For local connections: name, data directory, and optionally database file
   - For API connections: name, API URL, and optionally API key
5. Test the connection using the "Test Connection" button
6. Save your connection
7. Use the "Activate" button to switch to a different connection

### Connection Types

#### Local Connections
- Access log files and data stored on the local file system
- Automatically discovers both active (`*.jsonl`) and rotated (`*.jsonl.*`) log files, including gzipped archives
- Specify the data directory where log files are located
- Optionally specify a custom database file name

#### API Connections
- Connect to a remote LogEverything API endpoint
- Specify the base URL of the API
- Optionally provide an API key for authentication
- Choose whether to verify SSL certificates

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- LogEverything core package installed
- Git for submodule management

### Installation

1. **Add as submodule** (from LogEverything project root):
   ```bash
   git submodule add https://github.com/your-org/logeverything-dashboard.git logeverything-dashboard
   cd logeverything-dashboard
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure integration**:
   ```bash
   cp config/settings.example.yaml config/settings.yaml
   # Edit config/settings.yaml to match your LogEverything setup
   ```

4. **Start dashboard**:
   ```bash
   python run_dashboard.py
   ```

### Development Mode

```bash
# Start with auto-reload
python run_dashboard.py

# Access at http://localhost:3001
```

## ⚙️ Configuration

### LogEverything Integration

Create `config/settings.yaml`:

```yaml
# LogEverything API Integration
logeverything:
  api_url: "http://localhost:8080/api/v1"
  api_key: "${LOGEVERYTHING_API_KEY}"
  timeout: 30
  
# Dashboard Settings
dashboard:
  title: "LogEverything Dashboard"
  refresh_interval: 5
  max_operations: 1000

# Server Configuration  
server:
  host: "127.0.0.1"
  port: 8000
  workers: 1
```

### Environment Variables

```bash
# Core Integration
export LOGEVERYTHING_API_URL="http://localhost:8080/api/v1"
export LOGEVERYTHING_API_KEY="your-api-key"

# Dashboard Settings
export DASHBOARD_HOST="0.0.0.0"
export DASHBOARD_PORT="8000"
export DASHBOARD_TITLE="My LogEverything Dashboard"

# Security
export SECRET_KEY="your-secret-key"
export CORS_ORIGINS="http://localhost:3000,https://mydomain.com"
```

## 🔌 API Integration

The dashboard connects to LogEverything through standardized API endpoints:

### Required LogEverything API Endpoints

```python
# These endpoints should be implemented in the main LogEverything package
GET  /api/v1/health              # Health check
GET  /api/v1/metrics             # System metrics (CPU, memory, etc.)
GET  /api/v1/operations          # Recent operations list
GET  /api/v1/loggers             # Active logger instances
GET  /api/v1/stats               # Performance statistics
POST /api/v1/operations/clear    # Clear operations (optional)
WS   /api/v1/events              # Real-time event stream (optional)
```

### Data Formats

#### Metrics Response
```json
{
  "cpu_usage": 25.5,
  "memory_usage": 67.2,
  "active_loggers": 3,
  "uptime_seconds": 86400,
  "timestamp": "2025-07-02T10:30:00Z"
}
```

#### Operations Response
```json
{
  "total": 1500,
  "recent": [
    {
      "id": "op-123",
      "name": "Data Processing",
      "status": "success",
      "timestamp": "2025-07-02T10:29:45Z",
      "duration_ms": 125,
      "details": "Processed 50 log entries",
      "logger_name": "main.processor"
    }
  ]
}
```

## 📊 API Endpoints

### HTMX Partials
- `GET /partials/system-stats` — System CPU/memory/disk summary card
- `GET /partials/monitoring-stats` — Operations count and success rate card
- `GET /partials/logs-stats` — Log totals and source badges card
- `GET /partials/operations-summary-card` — Quick operation metrics card
- `GET /partials/operations?hours=&operation_name=` — Operations table with filters
- `GET /partials/logs?level=&source=&q=&hours=` — Logs table with search and filters
- `GET /partials/operation-analytics?hours=` — Top operations analytics table
- `GET /partials/system-detail` — Detailed system metrics modal content

### JSON APIs
- `GET /api/system-metrics-history?hours=24&max_points=200` — Time-series data for charts
- `GET /api/system-detail` — Full system metrics from latest snapshot
- `GET /api/operations/summary?hours=24` — Aggregated operation analytics
- `GET /api/log-level-distribution?hours=` — Log count by level
- `GET /api/session-info` — Current session metadata
- `GET /api/export?hours=24` — Full data export as JSON file download

## 🔧 Development

### Project Structure

```
logeverything-dashboard/
├── dashboard/                  # Main application package
│   ├── __init__.py
│   ├── main.py                # FastAPI app, routes (HTMX partials + API)
│   ├── models.py              # Pydantic models
│   ├── services.py            # MonitoringService (DB/JSONL/API queries)
│   ├── connections.py         # Multi-source connection management
│   ├── connection_routes.py   # Connection API routes
│   ├── compile_scss.py        # SCSS → CSS compiler + watcher
│   ├── templates/             # Jinja2 templates
│   │   ├── dashboard.html     # Main page
│   │   └── partials/          # HTMX partial templates
│   └── static/
│       ├── css/styles.css     # Compiled CSS
│       ├── js/
│       │   ├── main.js        # Theme toggle, toasts, core UI
│       │   ├── connections.js # Connection modal logic
│       │   ├── charts.js      # Chart.js initialization & data loading
│       │   └── dashboard.js   # Time-range, auto-refresh, export, shortcuts
│       └── scss/              # SCSS source files
├── run_dashboard.py           # Entry point (compiles SCSS, starts server)
└── requirements.txt           # Python dependencies
```

### Building and Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Compile SCSS
python -m dashboard.compile_scss

# Start the dashboard
python run_dashboard.py
```

## 🐳 Deployment

### Docker

```bash
# Build image
docker build -t logeverything-dashboard .

# Run container
docker run -p 8000:8000 \
  -e LOGEVERYTHING_API_URL=http://host.docker.internal:8080/api/v1 \
  logeverything-dashboard
```

### Docker Compose

```yaml
version: '3.8'
services:
  logeverything-dashboard:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOGEVERYTHING_API_URL=http://logeverything:8080/api/v1
      - DASHBOARD_TITLE=Production Dashboard
    depends_on:
      - logeverything
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: logeverything-dashboard
spec:
  replicas: 2
  selector:
    matchLabels:
      app: logeverything-dashboard
  template:
    metadata:
      labels:
        app: logeverything-dashboard
    spec:
      containers:
      - name: dashboard
        image: logeverything-dashboard:latest
        ports:
        - containerPort: 8000
        env:
        - name: LOGEVERYTHING_API_URL
          value: "http://logeverything-service:8080/api/v1"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
```

## 🔄 Submodule Workflow

### For Dashboard Developers

```bash
# Clone dashboard repository for development
git clone https://github.com/your-org/logeverything-dashboard.git
cd logeverything-dashboard

# Make changes and commit
git add .
git commit -m "Add new feature"
git push origin main
```

### For LogEverything Project Maintainers

```bash
# Update dashboard to latest version
cd logeverything-dashboard
git pull origin main
cd ..
git add logeverything-dashboard
git commit -m "Update dashboard to v1.2.3"

# Or update to specific version
cd logeverything-dashboard
git checkout v1.2.3
cd ..
git add logeverything-dashboard
git commit -m "Update dashboard to v1.2.3"
```

### For End Users

```bash
# Clone LogEverything project with dashboard
git clone --recursive https://github.com/your-org/logeverything.git

# Or if already cloned
git submodule update --init --recursive
```

## 📚 Documentation

- [Configuration Guide](docs/configuration.md)
- [API Integration](docs/api-integration.md)
- [Deployment Guide](docs/deployment.md)
- [Development Setup](docs/development.md)
- [Submodule Management](docs/submodules.md)

## 🤝 Contributing

1. Fork the dashboard repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

For LogEverything core integration changes, contribute to the main LogEverything repository.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 [Documentation](https://docs.logeverything.io/dashboard)
- 🐛 [Issues](https://github.com/your-org/logeverything-dashboard/issues)
- 💬 [Discussions](https://github.com/your-org/logeverything/discussions)

---

**Part of the LogEverything ecosystem** 🌟

