// LogEverything Dashboard — Connection Management

var connections = [];
var activeConnectionId = null;

document.addEventListener('DOMContentLoaded', function () {
    initializeConnectionManagement();
});

function initializeConnectionManagement() {
    var btn = document.getElementById('connection-button');
    if (btn) {
        btn.addEventListener('click', openConnectionModal);
    }
    loadConnections();
}

// --- Modal Open / Close ---

function openConnectionModal() {
    var modal = document.getElementById('connection-modal');
    if (modal) {
        modal.classList.add('is-open');
        document.body.style.overflow = 'hidden';
        showConnectionsList();
    }
}

function closeConnectionModal() {
    var modal = document.getElementById('connection-modal');
    if (modal) {
        modal.classList.remove('is-open');
        document.body.style.overflow = '';
    }
}

// --- Tab Navigation ---

function setActiveTab(tabId) {
    ['tab-connections-list', 'tab-add-connection', 'tab-edit-connection'].forEach(function (id) {
        var el = document.getElementById(id);
        if (el) {
            if (id === tabId) {
                el.style.borderBottom = '2px solid var(--accent-primary)';
                el.style.color = 'var(--text-primary)';
            } else {
                el.style.borderBottom = 'none';
                el.style.color = '';
            }
        }
    });
}

function showConnectionsList() {
    document.getElementById('connections-list-view').style.display = 'block';
    document.getElementById('add-connection-view').style.display = 'none';
    document.getElementById('edit-connection-view').style.display = 'none';
    document.getElementById('tab-edit-connection').style.display = 'none';
    document.getElementById('connection-modal-title').textContent = 'Manage Connections';
    setActiveTab('tab-connections-list');
    loadConnections();
}

function showAddConnection() {
    document.getElementById('connections-list-view').style.display = 'none';
    document.getElementById('add-connection-view').style.display = 'block';
    document.getElementById('edit-connection-view').style.display = 'none';
    document.getElementById('tab-edit-connection').style.display = 'none';
    document.getElementById('connection-modal-title').textContent = 'Add New Connection';
    setActiveTab('tab-add-connection');

    var form = document.getElementById('add-connection-form');
    if (form) form.reset();
    toggleConnectionFields();
}

function showEditConnection(connectionId) {
    document.getElementById('connections-list-view').style.display = 'none';
    document.getElementById('add-connection-view').style.display = 'none';
    document.getElementById('edit-connection-view').style.display = 'block';
    document.getElementById('tab-edit-connection').style.display = 'inline-block';
    document.getElementById('connection-modal-title').textContent = 'Edit Connection';
    setActiveTab('tab-edit-connection');

    if (connectionId) {
        loadConnectionDetails(connectionId);
    }
}

// --- API ---

async function loadConnections() {
    try {
        var response = await fetch('/api/connections');
        var data = await response.json();
        connections = data.connections || [];
        activeConnectionId = data.active ? data.active.id : null;
        renderConnectionsList();
    } catch (e) {
        console.error('Error loading connections:', e);
    }
}

function renderConnectionsList() {
    var tbody = document.getElementById('connections-table-body');
    var noConn = document.getElementById('no-connections');
    var tableContainer = document.getElementById('connections-table-container');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (connections.length === 0) {
        if (noConn) noConn.style.display = 'block';
        if (tableContainer) tableContainer.style.display = 'none';
        return;
    }

    if (noConn) noConn.style.display = 'none';
    if (tableContainer) tableContainer.style.display = 'block';

    connections.forEach(function (conn) {
        var isActive = conn.id === activeConnectionId;
        var row = document.createElement('tr');

        var details = conn.type === 'local'
            ? escapeHtml(conn.data_dir || '')
            : escapeHtml(conn.base_url || '');

        var statusBadge = isActive
            ? '<span class="badge badge--success badge--sm">Active</span>'
            : '<span class="badge badge--outline badge--sm">Inactive</span>';

        var actions = '<div class="btn-group">'
            + '<button class="btn btn-ghost btn-xs" onclick="editConnection(\'' + conn.id + '\')">Edit</button>';

        if (!isActive) {
            actions += '<button class="btn btn-primary btn-xs" onclick="activateConnection(\'' + conn.id + '\')">Activate</button>';
        }
        actions += '</div>';

        row.innerHTML =
            '<td><strong>' + escapeHtml(conn.name) + '</strong><br><span class="text-tertiary text-xs">' + escapeHtml(conn.type) + '</span></td>'
            + '<td class="font-mono text-xs truncate" style="max-width: 200px;">' + details + '</td>'
            + '<td>' + statusBadge + '</td>'
            + '<td>' + actions + '</td>';

        tbody.appendChild(row);
    });
}

function escapeHtml(text) {
    if (!text) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

function loadConnectionDetails(connectionId) {
    var conn = connections.find(function (c) { return c.id === connectionId; });
    if (!conn) return;

    document.getElementById('edit-connection-id').value = conn.id;
    document.getElementById('edit-connection-name').value = conn.name;
    document.getElementById('edit-connection-type').value = conn.type === 'local' ? 'Local Files' : 'Remote API';
    document.getElementById('edit-connection-type-hidden').value = conn.type;
    document.getElementById('edit-connection-description').value = conn.description || '';

    if (conn.type === 'local') {
        document.getElementById('edit-local-connection-fields').style.display = 'block';
        document.getElementById('edit-api-connection-fields').style.display = 'none';
        document.getElementById('edit-connection-data-dir').value = conn.data_dir || '';
        document.getElementById('edit-connection-db-file').value = conn.database_file || '';
        document.getElementById('edit-connection-logs-pattern').value = conn.logs_pattern || '*.jsonl';
    } else {
        document.getElementById('edit-local-connection-fields').style.display = 'none';
        document.getElementById('edit-api-connection-fields').style.display = 'block';
        document.getElementById('edit-connection-api-url').value = conn.base_url || '';
        document.getElementById('edit-connection-api-key').value = '';
        document.getElementById('edit-connection-verify-ssl').checked = conn.verify_ssl !== false;
    }
}

function toggleConnectionFields() {
    var radios = document.querySelectorAll('input[name="type"]');
    var selectedType = 'local';
    radios.forEach(function (r) { if (r.checked) selectedType = r.value; });

    var localFields = document.getElementById('local-connection-fields');
    var apiFields = document.getElementById('api-connection-fields');
    if (localFields) localFields.style.display = selectedType === 'local' ? 'block' : 'none';
    if (apiFields) apiFields.style.display = selectedType === 'api' ? 'block' : 'none';
}

function editConnection(connectionId) {
    showEditConnection(connectionId);
}

// --- CRUD ---

async function saveNewConnection(event) {
    event.preventDefault();
    var form = document.getElementById('add-connection-form');
    var formData = new FormData(form);
    var conn = Object.fromEntries(formData.entries());
    conn.created_at = new Date().toISOString();
    if (conn.type === 'api') conn.verify_ssl = formData.has('verify_ssl');

    try {
        var response = await fetch('/api/connections', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(conn)
        });
        if (!response.ok) {
            var err = await response.json();
            throw new Error(err.detail || 'Failed to create connection');
        }
        showToast('Connection created', 'success');
        showConnectionsList();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function saveEditedConnection(event) {
    event.preventDefault();
    var form = document.getElementById('edit-connection-form');
    var formData = new FormData(form);
    var conn = Object.fromEntries(formData.entries());
    var id = conn.id;
    if (conn.type === 'api') conn.verify_ssl = formData.has('verify_ssl');
    if (conn.api_key === '') delete conn.api_key;

    try {
        var response = await fetch('/api/connections/' + id, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(conn)
        });
        if (!response.ok) {
            var err = await response.json();
            throw new Error(err.detail || 'Failed to update connection');
        }
        showToast('Connection updated', 'success');
        showConnectionsList();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function deleteConnection() {
    var id = document.getElementById('edit-connection-id').value;
    if (!confirm('Delete this connection?')) return;

    try {
        var response = await fetch('/api/connections/' + id, { method: 'DELETE' });
        if (!response.ok) {
            var err = await response.json();
            throw new Error(err.detail || 'Failed to delete');
        }
        showToast('Connection deleted', 'success');
        showConnectionsList();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function activateConnection(connectionId) {
    try {
        var response = await fetch('/api/connections/' + connectionId + '/activate', { method: 'POST' });
        if (!response.ok) {
            var err = await response.json();
            throw new Error(err.detail || 'Failed to activate');
        }
        showToast('Connection activated — reloading...', 'success');
        setTimeout(function () { window.location.reload(); }, 1000);
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function testConnection(formType) {
    var form = formType === 'add'
        ? document.getElementById('add-connection-form')
        : document.getElementById('edit-connection-form');
    var formData = new FormData(form);
    var conn = Object.fromEntries(formData.entries());
    if (conn.type === 'api') conn.verify_ssl = formData.has('verify_ssl');

    showToast('Testing connection...', 'info');

    try {
        var response = await fetch('/api/connections/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(conn)
        });
        var result = await response.json();
        if (result.success) {
            showToast(result.message || 'Connection successful', 'success');
        } else {
            showToast(result.message || 'Connection failed', 'error');
        }
    } catch (e) {
        showToast('Test failed: ' + e.message, 'error');
    }
}

// --- Toast Notifications ---

function showToast(message, type) {
    type = type || 'info';
    var container = document.getElementById('toast-container');
    if (!container) return;

    var toast = document.createElement('div');
    toast.className = 'toast toast--' + type;

    toast.innerHTML =
        '<span class="toast__message">' + escapeHtml(message) + '</span>'
        + '<button class="toast__close" onclick="this.parentElement.remove()">'
        + '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>'
        + '</button>'
        + '<div class="toast__progress" style="animation-duration: 4s;"></div>';

    container.appendChild(toast);

    setTimeout(function () {
        toast.classList.add('toast--leaving');
        setTimeout(function () { toast.remove(); }, 300);
    }, 4000);
}
