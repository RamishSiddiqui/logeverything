// LogEverything Dashboard — Main JavaScript

document.addEventListener('DOMContentLoaded', function () {
    applyTheme(localStorage.getItem('theme') || 'theme-dark');
    applySidebarState();
    setupWebSocket();
});

// --- Theme ---

function applyTheme(theme) {
    document.body.classList.remove('theme-dark', 'theme-light');
    document.body.classList.add(theme);
    localStorage.setItem('theme', theme);
}

function toggleTheme() {
    var current = localStorage.getItem('theme') || 'theme-dark';
    applyTheme(current === 'theme-dark' ? 'theme-light' : 'theme-dark');

    // Recreate charts with new theme colors
    if (typeof recreateCharts === 'function') {
        recreateCharts();
    }
}

// --- Sidebar ---

function toggleSidebar() {
    var isNarrow = window.innerWidth <= 1024;
    if (isNarrow) {
        document.body.classList.toggle('sidebar-open');
    } else {
        document.body.classList.toggle('sidebar-collapsed');
        localStorage.setItem('sidebarCollapsed', document.body.classList.contains('sidebar-collapsed') ? '1' : '0');
    }
}

function applySidebarState() {
    if (window.innerWidth > 1024 && localStorage.getItem('sidebarCollapsed') === '1') {
        document.body.classList.add('sidebar-collapsed');
    }
}

// --- WebSocket ---

var _ws = null;
var _wsRetryDelay = 1000;

function setupWebSocket() {
    try {
        var protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        var url = protocol + '//' + window.location.host + '/ws';
        _ws = new WebSocket(url);

        _ws.onopen = function () {
            _wsRetryDelay = 1000;
        };

        _ws.onmessage = function (event) {
            try {
                var data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (e) {
                // ignore parse errors
            }
        };

        _ws.onclose = function () {
            _wsRetryDelay = Math.min(_wsRetryDelay * 1.5, 10000);
            setTimeout(setupWebSocket, _wsRetryDelay);
        };

        _ws.onerror = function () {};
    } catch (e) {
        setTimeout(setupWebSocket, 3000);
    }
}

function handleWebSocketMessage(data) {
    if (data.type === 'stats_update') {
        // HTMX polling handles stats refresh; WebSocket is a bonus trigger
        var sysCard = document.querySelector('[hx-get="/partials/system-stats"]');
        var monCard = document.querySelector('[hx-get="/partials/monitoring-stats"]');
        if (sysCard && typeof htmx !== 'undefined') htmx.trigger(sysCard, 'load');
        if (monCard && typeof htmx !== 'undefined') htmx.trigger(monCard, 'load');
    } else if (data.type === 'log_batch') {
        handleLogBatch(data);
    }
}

// --- Trace Modal ---

function openTraceModal() {
    var modal = document.getElementById('trace-modal');
    if (modal) {
        modal.classList.add('is-open');
        document.body.style.overflow = 'hidden';
    }
}

function closeTraceModal() {
    var modal = document.getElementById('trace-modal');
    if (modal) {
        modal.classList.remove('is-open');
        document.body.style.overflow = '';
    }
}

// --- HTML Escaping ---

function escapeHtml(text) {
    if (!text) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

// --- Real-time Log Batch Handler ---

function handleLogBatch(data) {
    var tbody = document.getElementById('logs-table-body');
    if (!tbody) return;

    var logs = data.logs || [];
    var source = data.source || '';
    var count = logs.length;

    for (var i = logs.length - 1; i >= 0; i--) {
        var log = logs[i];
        var row = document.createElement('tr');

        var level = (log.level || '').toUpperCase();
        var rowClass = 'log-row--new';
        if (level === 'ERROR' || level === 'CRITICAL') {
            rowClass += ' log-row--error';
        } else if (level === 'WARNING') {
            rowClass += ' log-row--warning';
        }
        row.className = rowClass;

        // Badge class
        var badgeLevel = 'debug';
        if (level === 'ERROR') badgeLevel = 'error';
        else if (level === 'CRITICAL') badgeLevel = 'critical';
        else if (level === 'WARNING') badgeLevel = 'warning';
        else if (level === 'INFO') badgeLevel = 'info';

        // Source cell
        var sourceHtml = '<span class="text-tertiary">&mdash;</span>';
        if (log.source) {
            sourceHtml = '<span class="badge badge--outline badge--sm">' + escapeHtml(log.source) + '</span>';
        }

        // Correlation ID cell
        var corrHtml = '<span class="text-tertiary">&mdash;</span>';
        if (log.correlation_id) {
            var shortId = escapeHtml(log.correlation_id.substring(0, 12)) + '...';
            corrHtml = '<a href="#" class="correlation-link"'
                + ' hx-get="/partials/trace/' + encodeURIComponent(log.correlation_id) + '"'
                + ' hx-target="#trace-modal-body"'
                + ' hx-swap="innerHTML"'
                + ' onclick="openTraceModal()">'
                + shortId + '</a>';
        }

        // Timestamp
        var ts = (log.timestamp || '').replace('T', ' ').substring(0, 19);

        row.innerHTML =
            '<td><span class="badge badge--' + badgeLevel + '">' + escapeHtml(level) + '</span></td>'
            + '<td>' + sourceHtml + '</td>'
            + '<td class="font-mono text-sm">' + escapeHtml(log.message || '') + '</td>'
            + '<td>' + escapeHtml(log.logger || '') + '</td>'
            + '<td>' + corrHtml + '</td>'
            + '<td class="text-tertiary">' + escapeHtml(ts) + '</td>';

        tbody.insertBefore(row, tbody.firstChild);

        if (typeof htmx !== 'undefined') {
            htmx.process(row);
        }
    }

    // Trim to max 50 rows
    while (tbody.children.length > 50) {
        tbody.removeChild(tbody.lastChild);
    }

    // Show real-time indicator
    if (count > 0) {
        var indicator = document.getElementById('logs-realtime-indicator');
        if (indicator) {
            var label = count + ' new';
            if (source) label += ' from ' + source;
            indicator.textContent = label;
            indicator.style.display = 'inline-flex';
            setTimeout(function () {
                indicator.style.display = 'none';
            }, 3000);
        }
    }
}
