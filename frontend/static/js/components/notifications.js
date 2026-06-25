document.addEventListener('DOMContentLoaded', () => {
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationPanel = document.getElementById('notificationPanel');
    const notificationBadge = document.getElementById('notificationBadge');
    const notificationList = document.getElementById('notificationList');

    if (notificationBtn) {
        notificationBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            notificationPanel.classList.toggle('open');
            if (notificationPanel.classList.contains('open')) {
                loadNotifications();
            }
        });
    }

    document.addEventListener('click', (e) => {
        if (notificationPanel && !notificationPanel.contains(e.target) && e.target !== notificationBtn) {
            notificationPanel.classList.remove('open');
        }
    });

    const markAllBtn = document.querySelector('.mark-all-read');
    if (markAllBtn) {
        markAllBtn.addEventListener('click', async () => {
            await api.put('/notifications/mark-all-read');
            if (notificationBadge) notificationBadge.style.display = 'none';
            loadNotifications();
        });
    }

    async function loadNotifications() {
        try {
            const response = await api.get('/notifications/?per_page=10');
            if (response && response.notifications) {
                renderNotifications(response.notifications);
                if (response.unread_count > 0) {
                    notificationBadge.textContent = response.unread_count;
                    notificationBadge.style.display = 'flex';
                } else {
                    notificationBadge.style.display = 'none';
                }
            }
        } catch (error) {
            renderSampleNotifications();
        }
    }

    function renderNotifications(notifications) {
        if (!notificationList) return;

        if (notifications.length === 0) {
            notificationList.innerHTML = `
                <div class="empty-state" style="padding: 32px;">
                    <i class="icon-bell-off"></i>
                    <p>No notifications</p>
                </div>
            `;
            return;
        }

        notificationList.innerHTML = notifications.map(n => `
            <div class="notification-item ${n.is_read ? '' : 'unread'}">
                <div class="notification-icon" style="background: rgba(230, 57, 70, 0.08); color: var(--color-accent);">
                    <i class="icon-bell"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${n.title}</div>
                    <div class="notification-body">${n.body || ''}</div>
                    <div class="notification-time">${formatTime(n.created_at)}</div>
                </div>
            </div>
        `).join('');
    }

    function renderSampleNotifications() {
        if (!notificationList) return;
        notificationList.innerHTML = `
            <div class="notification-item unread">
                <div class="notification-icon" style="background: rgba(230, 57, 70, 0.08); color: var(--color-accent);">
                    <i class="icon-bell"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">New assignment posted</div>
                    <div class="notification-body">Mathematics - Chapter 5 Review</div>
                    <div class="notification-time">2 min ago</div>
                </div>
            </div>
            <div class="notification-item unread">
                <div class="notification-icon" style="background: rgba(16, 185, 129, 0.08); color: var(--color-success);">
                    <i class="icon-check-circle"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">Fee payment received</div>
                    <div class="notification-body">KES 25,000 confirmed via M-Pesa</div>
                    <div class="notification-time">15 min ago</div>
                </div>
            </div>
            <div class="notification-item">
                <div class="notification-icon" style="background: rgba(59, 130, 246, 0.08); color: var(--color-info);">
                    <i class="icon-calendar"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">Exam schedule updated</div>
                    <div class="notification-body">End of term exams start June 30</div>
                    <div class="notification-time">1 hour ago</div>
                </div>
            </div>
        `;
    }

    function formatTime(isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);

        if (diff < 60) return 'Just now';
        if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
        return date.toLocaleDateString();
    }

    renderSampleNotifications();
});
