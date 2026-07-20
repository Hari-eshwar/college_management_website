document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    initSidebar();
    initNotifications();
    initTooltips();
});

function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    const toggle = document.getElementById('themeToggle');
    if (toggle) {
        toggle.innerHTML = savedTheme === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        toggle.addEventListener('click', function() {
            const current = document.documentElement.getAttribute('data-bs-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-bs-theme', next);
            localStorage.setItem('theme', next);
            this.innerHTML = next === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
            showToast('Theme changed to ' + next + ' mode', 'info');
        });
    }
}

function initSidebar() {
    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (toggle && sidebar) {
        toggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
            if (overlay) overlay.classList.toggle('show');
        });
    }
    if (overlay) {
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('open');
            overlay.classList.remove('show');
        });
    }
}

function initNotifications() {
    const bell = document.getElementById('notificationBell');
    if (!bell) return;
    loadNotificationCount();
    setInterval(loadNotificationCount, 30000);
    bell.addEventListener('click', function() {
        fetchNotifications();
    });
}

function loadNotificationCount() {
    const badge = document.getElementById('notifBadge');
    if (!badge) return;
    const role = document.querySelector('.role-badge');
    if (!role) return;
    const endpoint = role.classList.contains('faculty') ? '/faculty/notifications' : '/student/notifications';
    fetch(endpoint)
        .then(r => r.json())
        .then(data => {
            const unread = data.filter(n => !n.is_read).length;
            if (unread > 0) {
                badge.textContent = unread;
                badge.style.display = 'inline';
            } else {
                badge.style.display = 'none';
            }
        })
        .catch(() => {});
}

function fetchNotifications() {
    const role = document.querySelector('.role-badge');
    if (!role) return;
    const endpoint = role.classList.contains('faculty') ? '/faculty/notifications' : '/student/notifications';
    fetch(endpoint)
        .then(r => r.json())
        .then(data => {
            const unread = data.filter(n => !n.is_read);
            if (unread.length === 0) {
                showToast('No new notifications', 'info');
                return;
            }
            unread.forEach(n => {
                showToast(n.title + ': ' + n.message, 'info');
                if (role.classList.contains('faculty')) {
                    fetch('/faculty/notifications/read/' + n.id, { method: 'POST' }).catch(() => {});
                }
            });
            loadNotificationCount();
        })
        .catch(() => {});
}

function initTooltips() {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        new bootstrap.Tooltip(el);
    });
}

function showToast(message, type) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const colorMap = { success: 'text-bg-success', danger: 'text-bg-danger', warning: 'text-bg-warning', info: 'text-bg-primary' };
    const bg = colorMap[type] || 'text-bg-primary';
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center border-0 ' + bg;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.innerHTML = '<div class="d-flex"><div class="toast-body">' + message + '</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';
    container.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { autohide: true, delay: 4000 });
    bsToast.show();
    toast.addEventListener('hidden.bs.toast', function() { toast.remove(); });
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatTime(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}

function getStatusBadge(status) {
    const colors = { Present: 'success', Late: 'warning', Absent: 'danger', Pending: 'warning', Approved: 'success', Rejected: 'danger' };
    return '<span class="badge bg-' + (colors[status] || 'secondary') + '">' + status + '</span>';
}
