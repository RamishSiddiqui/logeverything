// LogEverything Dashboard — Tree View

var _treeLoaded = false;

// Toggle a single tree node (expand/collapse children)
function toggleTreeNode(headerEl) {
    var node = headerEl.closest('.tree-node');
    if (!node) return;

    var children = node.querySelector('.tree-children');
    var toggle = node.querySelector('.tree-toggle');
    if (!children) return;

    var isOpen = children.style.display !== 'none';
    children.style.display = isOpen ? 'none' : 'block';
    if (toggle) {
        toggle.classList.toggle('tree-toggle--open', !isOpen);
    }
}

// Expand all tree nodes
function expandAllTreeNodes() {
    var children = document.querySelectorAll('.tree-children');
    var toggles = document.querySelectorAll('.tree-toggle');
    for (var i = 0; i < children.length; i++) {
        children[i].style.display = 'block';
    }
    for (var j = 0; j < toggles.length; j++) {
        toggles[j].classList.add('tree-toggle--open');
    }
}

// Collapse all tree nodes
function collapseAllTreeNodes() {
    var children = document.querySelectorAll('.tree-children');
    var toggles = document.querySelectorAll('.tree-toggle');
    for (var i = 0; i < children.length; i++) {
        children[i].style.display = 'none';
    }
    for (var j = 0; j < toggles.length; j++) {
        toggles[j].classList.remove('tree-toggle--open');
    }
}

// Toggle between flat and tree log views
function toggleLogView(mode) {
    var flatView = document.getElementById('logs-flat-view');
    var treeView = document.getElementById('logs-tree-view');
    var paginationControls = document.getElementById('pagination-controls');
    var toggleBtns = document.querySelectorAll('.view-toggle__btn');

    if (!flatView || !treeView) return;

    // Update toggle button states
    for (var i = 0; i < toggleBtns.length; i++) {
        var btn = toggleBtns[i];
        if (btn.getAttribute('data-mode') === mode) {
            btn.classList.add('view-toggle__btn--active');
        } else {
            btn.classList.remove('view-toggle__btn--active');
        }
    }

    if (mode === 'tree') {
        flatView.style.display = 'none';
        treeView.style.display = 'block';
        // Hide pagination (tree view doesn't paginate)
        if (paginationControls) paginationControls.style.display = 'none';

        // Always reload tree with current filters
        var treeContent = document.getElementById('logs-tree-content');
        if (treeContent && typeof htmx !== 'undefined') {
            // Use _buildTreeUrl from dashboard.js which includes current filters
            var treeUrl = (typeof _buildTreeUrl === 'function') ? _buildTreeUrl() : '/partials/logs-tree';
            htmx.ajax('GET', treeUrl, '#logs-tree-content');
        }
        _treeLoaded = true;
    } else {
        flatView.style.display = 'block';
        treeView.style.display = 'none';
        // Show pagination controls again
        if (paginationControls) paginationControls.style.display = '';
    }
}
