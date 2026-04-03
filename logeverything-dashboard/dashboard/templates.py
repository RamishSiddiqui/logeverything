"""
HTML Templates for the LogEverything Dashboard
"""


def get_base_template() -> str:
    """Get the base HTML template."""
    return """
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/daisyui@4.4.19/dist/full.min.css" rel="stylesheet" type="text/css">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/htmx.org@1.9.9"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Manrope', sans-serif; }
        .fade-in { animation: fadeIn 0.3s ease-in; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    </style>
</head>
<body class="bg-base-100 text-base-content">
    <div class="navbar bg-base-200 shadow-lg">
        <div class="flex-1">
            <a class="btn btn-ghost text-xl font-bold">📊 LogEverything Dashboard</a>
        </div>
        <div class="flex-none">
            <div class="badge badge-primary">Offline Mode</div>
        </div>
    </div>

    <div class="container mx-auto p-4">
        {{ content }}
    </div>

    <script>
        // Auto-refresh every 30 seconds in offline mode
        setInterval(() => {
            if (document.querySelector('[hx-get]')) {
                htmx.trigger(document.body, 'refresh');
            }
        }, 30000);
    </script>
</body>
</html>
"""


def get_dashboard_template() -> str:
    """Get the main dashboard template."""
    return """
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
    <!-- Session Info -->
    <div class="card bg-base-200 shadow-xl">
        <div class="card-body">
            <h2 class="card-title">📋 Session Info</h2>
            <div class="space-y-2">
                <div><strong>Session ID:</strong> {{ session.session_id or 'Unknown' }}</div>
                <div><strong>PID:</strong> {{ session.pid or 'N/A' }}</div>
                <div><strong>Started:</strong> {{ session.start_time or 'Unknown' }}</div>
            </div>
        </div>
    </div>

    <!-- Data Status -->
    <div class="card bg-base-200 shadow-xl">
        <div class="card-body">
            <h2 class="card-title">💾 Data Status</h2>
            <div class="space-y-2">
                <div class="flex justify-between">
                    <span>Database:</span>
                    <div class="badge {{ 'badge-success' if data_status.has_database else 'badge-error' }}">
                        {{ 'Available' if data_status.has_database else 'Missing' }}
                    </div>
                </div>
                <div class="flex justify-between">
                    <span>Log Files:</span>
                    <div class="badge badge-info">{{ data_status.log_files_count }}</div>
                </div>
                <div class="flex justify-between">
                    <span>Total Logs:</span>
                    <div class="badge badge-primary">{{ statistics.total_logs }}</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Error Stats -->
    <div class="card bg-base-200 shadow-xl">
        <div class="card-body">
            <h2 class="card-title">⚠️ Error Statistics</h2>
            <div class="space-y-2">
                <div class="flex justify-between">
                    <span>Error Logs:</span>
                    <div class="badge {{ 'badge-error' if statistics.error_logs > 0 else 'badge-success' }}">
                        {{ statistics.error_logs }}
                    </div>
                </div>
                <div class="flex justify-between">
                    <span>Error Rate:</span>
                    <div class="badge {{ 'badge-error' if statistics.error_rate > 10 else 'badge-warning' if statistics.error_rate > 0 else 'badge-success' }}">
                        {{ "%.1f"|format(statistics.error_rate) }}%
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Recent Logs -->
<div class="card bg-base-200 shadow-xl mb-6">
    <div class="card-body">
        <h2 class="card-title">📝 Recent Logs</h2>
        <div class="overflow-x-auto">
            <table class="table table-zebra">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Level</th>
                        <th>Logger</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody>
                    {% for log in recent_logs %}
                    <tr>
                        <td class="text-sm">{{ log.timestamp[:19] if log.timestamp else 'N/A' }}</td>
                        <td>
                            <div class="badge
                                {{ 'badge-error' if log.level == 'ERROR' else
                                   'badge-warning' if log.level == 'WARNING' else
                                   'badge-info' if log.level == 'INFO' else
                                   'badge-ghost' }}">
                                {{ log.level }}
                            </div>
                        </td>
                        <td class="text-sm">{{ log.logger or 'unknown' }}</td>
                        <td class="text-sm">{{ log.message[:100] }}{{ '...' if log.message and log.message|length > 100 else '' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <div class="card-actions justify-end">
            <button class="btn btn-primary btn-sm" hx-get="/logs" hx-target="#main-content">
                View All Logs
            </button>
        </div>
    </div>
</div>

<!-- Refresh Controls -->
<div class="text-center">
    <button class="btn btn-outline" hx-get="/" hx-target="body">
        🔄 Refresh Dashboard
    </button>
</div>
"""


def get_logs_template() -> str:
    """Get the logs page template."""
    return """
<div class="flex justify-between items-center mb-6">
    <h1 class="text-3xl font-bold">📝 Application Logs</h1>
    <button class="btn btn-outline" hx-get="/" hx-target="body">
        ← Back to Dashboard
    </button>
</div>

<!-- Log Analysis -->
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
    <div class="card bg-base-200 shadow-xl">
        <div class="card-body">
            <h3 class="card-title">📊 Log Levels</h3>
            <div class="space-y-2">
                {% for level, count in analysis.levels.items() %}
                <div class="flex justify-between">
                    <span>{{ level }}</span>
                    <div class="badge
                        {{ 'badge-error' if level == 'ERROR' else
                           'badge-warning' if level == 'WARNING' else
                           'badge-info' if level == 'INFO' else
                           'badge-ghost' }}">
                        {{ count }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <div class="card bg-base-200 shadow-xl">
        <div class="card-body">
            <h3 class="card-title">🏷️ Top Loggers</h3>
            <div class="space-y-2">
                {% for logger, count in analysis.loggers.items()[:5] %}
                <div class="flex justify-between">
                    <span class="text-sm">{{ logger }}</span>
                    <div class="badge badge-primary">{{ count }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <div class="card bg-base-200 shadow-xl">
        <div class="card-body">
            <h3 class="card-title">⏰ Activity</h3>
            <div class="text-center">
                <div class="stat-value text-primary">{{ analysis.total_analyzed }}</div>
                <div class="stat-desc">Total logs analyzed</div>
            </div>
        </div>
    </div>
</div>

<!-- Log Table -->
<div class="card bg-base-200 shadow-xl">
    <div class="card-body">
        <h3 class="card-title">Recent Log Entries</h3>
        <div class="overflow-x-auto max-h-96">
            <table class="table table-zebra table-pin-rows">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Level</th>
                        <th>Logger</th>
                        <th>Message</th>
                        <th>Correlation ID</th>
                    </tr>
                </thead>
                <tbody>
                    {% for log in logs %}
                    <tr class="hover">
                        <td class="text-xs">{{ log.timestamp if log.timestamp else 'N/A' }}</td>
                        <td>
                            <div class="badge badge-sm
                                {{ 'badge-error' if log.level == 'ERROR' else
                                   'badge-warning' if log.level == 'WARNING' else
                                   'badge-info' if log.level == 'INFO' else
                                   'badge-ghost' }}">
                                {{ log.level }}
                            </div>
                        </td>
                        <td class="text-xs">{{ log.logger or 'unknown' }}</td>
                        <td class="text-sm max-w-md truncate">{{ log.message or 'No message' }}</td>
                        <td class="text-xs font-mono">{{ log.correlation_id or '-' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
"""
