// LogEverything Dashboard — Charts (Chart.js)

var _cpuMemoryChart = null;
var _logLevelChart = null;
var _chartHours = 24;
var _chartRefreshInterval = null;

function getChartColors() {
    var style = getComputedStyle(document.body);
    return {
        cpu: style.getPropertyValue('--accent-primary').trim() || '#6366f1',
        memory: style.getPropertyValue('--accent-live').trim() || '#06b6d4',
        grid: style.getPropertyValue('--border-subtle').trim() || '#1e2132',
        text: style.getPropertyValue('--text-tertiary').trim() || '#555a72',
        success: style.getPropertyValue('--color-success').trim() || '#22c55e',
        warning: style.getPropertyValue('--color-warning').trim() || '#eab308',
        error: style.getPropertyValue('--color-error').trim() || '#ef4444',
        info: style.getPropertyValue('--color-info').trim() || '#6366f1',
        debug: style.getPropertyValue('--color-debug').trim() || '#8186a0',
        critical: style.getPropertyValue('--color-critical').trim() || '#f43f5e',
    };
}

// --- CPU / Memory Trend Chart ---

function initCpuMemoryChart(canvas) {
    if (!canvas) return;
    var colors = getChartColors();

    _cpuMemoryChart = new Chart(canvas, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'CPU %',
                    data: [],
                    borderColor: colors.cpu,
                    backgroundColor: colors.cpu + '10',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.3,
                    fill: true,
                },
                {
                    label: 'Memory %',
                    data: [],
                    borderColor: colors.memory,
                    backgroundColor: colors.memory + '10',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.3,
                    fill: true,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                x: {
                    type: 'time',
                    time: { tooltipFormat: 'MMM d, HH:mm:ss' },
                    grid: { color: colors.grid },
                    ticks: { color: colors.text, maxTicksLimit: 8 },
                },
                y: {
                    min: 0,
                    max: 100,
                    grid: { color: colors.grid },
                    ticks: { color: colors.text, callback: function (v) { return v + '%'; } },
                },
            },
            plugins: {
                legend: { labels: { color: colors.text, usePointStyle: true, pointStyle: 'circle' } },
            },
        },
    });
}

function loadCpuMemoryData(hours) {
    if (!_cpuMemoryChart) return;
    var h = hours || _chartHours;

    fetch('/api/system-metrics-history?hours=' + h + '&max_points=200')
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var metrics = data.metrics || [];
            var cpuData = [];
            var memData = [];

            for (var i = 0; i < metrics.length; i++) {
                var m = metrics[i];
                var ts = m.timestamp;
                cpuData.push({ x: ts, y: m.cpu_percent || 0 });
                memData.push({ x: ts, y: m.memory_percent || 0 });
            }

            _cpuMemoryChart.data.datasets[0].data = cpuData;
            _cpuMemoryChart.data.datasets[1].data = memData;
            _cpuMemoryChart.update('none');
        })
        .catch(function () {});
}

// --- Log Level Distribution Chart ---

function initLogLevelChart(canvas) {
    if (!canvas) return;
    var colors = getChartColors();

    _logLevelChart = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            datasets: [{
                data: [0, 0, 0, 0, 0],
                backgroundColor: [colors.debug, colors.info, colors.warning, colors.error, colors.critical],
                borderWidth: 0,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: colors.text, usePointStyle: true, pointStyle: 'circle', padding: 12 },
                },
            },
        },
    });
}

function loadLogLevelData(hours) {
    if (!_logLevelChart) return;
    var url = '/api/log-level-distribution';
    if (hours) url += '?hours=' + hours;

    fetch(url)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            _logLevelChart.data.datasets[0].data = [
                data.DEBUG || 0,
                data.INFO || 0,
                data.WARNING || 0,
                data.ERROR || 0,
                data.CRITICAL || 0,
            ];
            _logLevelChart.update('none');
        })
        .catch(function () {});
}

// --- Refresh / Recreate ---

function refreshCharts(hours) {
    if (hours !== undefined) _chartHours = hours;
    loadCpuMemoryData(_chartHours);
    loadLogLevelData(_chartHours);
}

function recreateCharts() {
    // Destroy existing instances
    if (_cpuMemoryChart) { _cpuMemoryChart.destroy(); _cpuMemoryChart = null; }
    if (_logLevelChart) { _logLevelChart.destroy(); _logLevelChart = null; }

    var cpuCanvas = document.getElementById('cpu-memory-chart');
    var logCanvas = document.getElementById('log-level-chart');

    initCpuMemoryChart(cpuCanvas);
    initLogLevelChart(logCanvas);
    refreshCharts(_chartHours);
}

// --- Init on DOMContentLoaded ---

document.addEventListener('DOMContentLoaded', function () {
    var cpuCanvas = document.getElementById('cpu-memory-chart');
    var logCanvas = document.getElementById('log-level-chart');

    if (typeof Chart !== 'undefined') {
        initCpuMemoryChart(cpuCanvas);
        initLogLevelChart(logCanvas);
        refreshCharts(_chartHours);

        // Auto-refresh chart data every 30 seconds
        _chartRefreshInterval = setInterval(function () {
            refreshCharts(_chartHours);
        }, 30000);
    }
});
