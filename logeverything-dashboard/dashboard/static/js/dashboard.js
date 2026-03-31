// LogEverything Dashboard — Dashboard Controls

var _autoRefreshPaused = false;
var _savedTriggers = {};

// =====================================================================
// Log Filters & Pagination — persistent bar in logs.html
// =====================================================================

var _currentPageSize = 25;  // default page size
var _currentOffset = 0;     // current page offset

/** Collect filter query params (shared by flat + tree views). */
function _buildFilterParams() {
    var parts = [];

    // Level pills
    var activePills = document.querySelectorAll('#level-pills .level-pill--active');
    var levels = [];
    for (var i = 0; i < activePills.length; i++) {
        levels.push(activePills[i].getAttribute('data-level'));
    }
    if (levels.length) parts.push('level=' + encodeURIComponent(levels.join(',')));

    // Text inputs
    var source = document.getElementById('filter-source');
    if (source && source.value.trim()) parts.push('source=' + encodeURIComponent(source.value.trim()));

    var corr = document.getElementById('filter-correlation');
    if (corr && corr.value.trim()) parts.push('correlation_id=' + encodeURIComponent(corr.value.trim()));

    var search = document.getElementById('filter-search');
    if (search && search.value.trim()) parts.push('q=' + encodeURIComponent(search.value.trim()));

    // Hours (set by time-range selector, null = no time filter)
    if (_currentHours !== null) {
        parts.push('hours=' + _currentHours);
    }

    return parts;
}

/** Build the /partials/logs URL from filters + pagination state. */
function _buildLogsUrl() {
    var parts = _buildFilterParams();

    // Pagination
    parts.push('limit=' + _currentPageSize);
    if (_currentOffset > 0) parts.push('offset=' + _currentOffset);

    var url = '/partials/logs';
    if (parts.length) url += '?' + parts.join('&');
    return url;
}

/** Build the /partials/logs-tree URL from filters. */
function _buildTreeUrl() {
    var parts = _buildFilterParams();
    var url = '/partials/logs-tree';
    if (parts.length) url += '?' + parts.join('&');
    return url;
}

/** Sync the #logs-content hx-get URL with the current filter state.
 *  Called after every filter change so auto-refresh honours filters. */
function _syncLogsUrl() {
    var el = document.getElementById('logs-content');
    if (!el) return;
    var url = _buildLogsUrl();
    el.setAttribute('hx-get', url);
    if (typeof htmx !== 'undefined') htmx.process(el);
}

/** Toggle a level pill on/off. */
function toggleLevelPill(btn) {
    btn.classList.toggle('level-pill--active');
    _syncLogsUrl();
}

/** Apply button: sync URL and fetch immediately. */
function applyLogFilters() {
    _currentOffset = 0; // Reset to first page on new filter
    _syncLogsUrl();

    // Fetch whichever view is currently active
    var treeView = document.getElementById('logs-tree-view');
    if (treeView && treeView.style.display !== 'none') {
        // Tree view is active — reload tree with filters
        var treeUrl = _buildTreeUrl();
        if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', treeUrl, '#logs-tree-content');
        }
    } else {
        // Flat view
        var url = _buildLogsUrl();
        if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', url, '#logs-content');
        }
    }
}

/** Clear button: deselect all pills, clear inputs, fetch unfiltered. */
function clearLogFilters() {
    // Deselect pills
    var pills = document.querySelectorAll('#level-pills .level-pill--active');
    for (var i = 0; i < pills.length; i++) {
        pills[i].classList.remove('level-pill--active');
    }
    // Clear text inputs
    var ids = ['filter-source', 'filter-correlation', 'filter-search'];
    for (var j = 0; j < ids.length; j++) {
        var el = document.getElementById(ids[j]);
        if (el) el.value = '';
    }
    // Reset pagination
    _currentOffset = 0;
    // Reset URL and fetch
    _syncLogsUrl();

    var treeView = document.getElementById('logs-tree-view');
    if (treeView && treeView.style.display !== 'none') {
        if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', '/partials/logs-tree', '#logs-tree-content');
        }
    } else {
        if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', _buildLogsUrl(), '#logs-content');
        }
    }
}

// =====================================================================
// Pagination
// =====================================================================

/** Set page size from preset buttons. */
function setPageSize(size) {
    _currentPageSize = size;
    _currentOffset = 0;

    // Update active button
    var btns = document.querySelectorAll('.page-size-btn');
    for (var i = 0; i < btns.length; i++) {
        var btnSize = parseInt(btns[i].getAttribute('data-size'), 10);
        if (btnSize === size) {
            btns[i].classList.add('page-size-btn--active');
        } else {
            btns[i].classList.remove('page-size-btn--active');
        }
    }

    // Clear custom input
    var customInput = document.getElementById('custom-page-size');
    if (customInput) customInput.value = '';

    _syncLogsUrl();
    if (typeof htmx !== 'undefined') {
        htmx.ajax('GET', _buildLogsUrl(), '#logs-content');
    }
}

/** Set custom page size from the input field. */
function setCustomPageSize() {
    var input = document.getElementById('custom-page-size');
    if (!input) return;
    var val = parseInt(input.value, 10);
    if (isNaN(val) || val < 1) return;
    if (val > 10000) val = 10000;

    _currentPageSize = val;
    _currentOffset = 0;

    // Deselect all preset buttons
    var btns = document.querySelectorAll('.page-size-btn');
    for (var i = 0; i < btns.length; i++) {
        btns[i].classList.remove('page-size-btn--active');
    }

    _syncLogsUrl();
    if (typeof htmx !== 'undefined') {
        htmx.ajax('GET', _buildLogsUrl(), '#logs-content');
    }
}

/** Navigate to a specific offset (called from Prev/Next buttons in the partial). */
function paginateLogs(offset) {
    if (offset < 0) offset = 0;
    _currentOffset = offset;

    _syncLogsUrl();
    if (typeof htmx !== 'undefined') {
        htmx.ajax('GET', _buildLogsUrl(), '#logs-content');
    }
}

// Keep auto-refresh in sync: whenever #logs-content refreshes via its
// hx-trigger="every 10s", the URL already has the right filters because
// _syncLogsUrl() updates hx-get proactively.
// Also re-sync after each swap in case something drifted.
document.addEventListener('htmx:afterSwap', function (evt) {
    if (evt.detail.target && evt.detail.target.id === 'logs-content') {
        _syncLogsUrl();
    }
});

// =====================================================================
// Time-Range Selector
// =====================================================================

var _currentHours = null; // null = no time filter, set when user clicks a time button

document.addEventListener('DOMContentLoaded', function () {
    var selector = document.getElementById('time-range-selector');
    if (!selector) return;

    var buttons = selector.querySelectorAll('.time-range-btn');
    for (var i = 0; i < buttons.length; i++) {
        buttons[i].addEventListener('click', function () {
            var hours = parseInt(this.getAttribute('data-hours'), 10);
            _currentHours = hours;

            // Update active state
            var all = selector.querySelectorAll('.time-range-btn');
            for (var j = 0; j < all.length; j++) {
                all[j].classList.remove('time-range-btn--active');
            }
            this.classList.add('time-range-btn--active');

            // Update charts
            if (typeof refreshCharts === 'function') {
                refreshCharts(hours);
            }

            // Reload all partials with new time range
            reloadPartialsWithHours(hours);
        });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcut);
});

function reloadPartialsWithHours(hours) {
    if (typeof htmx === 'undefined') return;

    // Helper: reload an HTMX element if it exists on the current page
    function reloadIfPresent(id, baseUrl) {
        var el = document.getElementById(id);
        if (!el) return;
        var url = baseUrl + '?hours=' + hours;
        el.setAttribute('hx-get', url);
        htmx.process(el);
        htmx.ajax('GET', url, '#' + id);
    }

    // Reload operation analytics
    reloadIfPresent('operation-analytics-content', '/partials/operation-analytics');

    // Reload operations table
    reloadIfPresent('operations-content', '/partials/operations');

    // Reset pagination offset on time range change
    _currentOffset = 0;

    // Reload logs — sync filters (including new hours) and fetch
    var treeView = document.getElementById('logs-tree-view');
    if (treeView && treeView.style.display !== 'none') {
        // Tree view is active
        var treeUrl = _buildTreeUrl();
        htmx.ajax('GET', treeUrl, '#logs-tree-content');
    }
    var logsContent = document.getElementById('logs-content');
    if (logsContent) {
        _syncLogsUrl();
        var url = _buildLogsUrl();
        htmx.ajax('GET', url, '#logs-content');
    }

    // Reload system detail if present
    reloadIfPresent('system-detail-content', '/partials/system-detail');
}

// =====================================================================
// Auto-Refresh Toggle
// =====================================================================

function toggleAutoRefresh() {
    var btn = document.getElementById('auto-refresh-toggle');
    _autoRefreshPaused = !_autoRefreshPaused;

    if (_autoRefreshPaused) {
        pauseAutoRefresh();
        if (btn) btn.classList.remove('btn-icon--active');
    } else {
        resumeAutoRefresh();
        if (btn) btn.classList.add('btn-icon--active');
    }
}

function pauseAutoRefresh() {
    var elements = document.querySelectorAll('[hx-trigger]');
    for (var i = 0; i < elements.length; i++) {
        var el = elements[i];
        var trigger = el.getAttribute('hx-trigger');
        if (trigger && trigger.indexOf('every') !== -1) {
            var id = el.id || ('htmx-el-' + i);
            _savedTriggers[id] = trigger;
            var newTrigger = trigger.replace(/,?\s*every\s+\d+s/g, '').replace(/^\s*,\s*/, '');
            if (!newTrigger) newTrigger = 'none';
            el.setAttribute('hx-trigger', newTrigger);
            if (typeof htmx !== 'undefined') htmx.process(el);
        }
    }
    if (typeof _chartRefreshInterval !== 'undefined' && _chartRefreshInterval) {
        clearInterval(_chartRefreshInterval);
    }
}

function resumeAutoRefresh() {
    for (var id in _savedTriggers) {
        var el = document.getElementById(id);
        if (el) {
            el.setAttribute('hx-trigger', _savedTriggers[id]);
            if (typeof htmx !== 'undefined') htmx.process(el);
        }
    }
    _savedTriggers = {};
    if (typeof refreshCharts === 'function' && typeof _chartHours !== 'undefined') {
        _chartRefreshInterval = setInterval(function () {
            refreshCharts(_chartHours);
        }, 30000);
    }
}

// =====================================================================
// Export
// =====================================================================

function exportData() {
    var hours = _currentHours || 24;
    window.location.href = '/api/export?hours=' + hours;
}

// =====================================================================
// System Detail Modal
// =====================================================================

function openSystemDetailModal() {
    var modal = document.getElementById('system-detail-modal');
    if (modal) {
        modal.classList.add('is-open');
        document.body.style.overflow = 'hidden';
    }
}

function closeSystemDetailModal() {
    var modal = document.getElementById('system-detail-modal');
    if (modal) {
        modal.classList.remove('is-open');
        document.body.style.overflow = '';
    }
}

// =====================================================================
// Keyboard Shortcuts
// =====================================================================

function handleKeyboardShortcut(e) {
    var tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

    switch (e.key) {
        case 'r':
            toggleAutoRefresh();
            break;
        case '/':
            e.preventDefault();
            var searchInput = document.getElementById('filter-search');
            if (searchInput) searchInput.focus();
            break;
        case 'e':
            exportData();
            break;
        case 'Escape':
            closeSystemDetailModal();
            if (typeof closeTraceModal === 'function') closeTraceModal();
            break;
    }
}
