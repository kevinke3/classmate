document.addEventListener('DOMContentLoaded', () => {
    if (!auth.requireAuth()) return;

    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const teacherRole = user.teacher_role || 'class_teacher';

    initRoleBadge(user);
    initTabs(user);
    loadProfile();
    loadQuickActions(user);

    if (user.can_message_parents) loadParents();
    if (user.can_manage_announcements) loadAnnouncements();
    if (user.can_manage_events) loadEvents();

    initEventHandlers(user);
});

function initRoleBadge(user) {
    const badge = document.getElementById('roleBadge');
    const badgeText = document.getElementById('roleBadgeText');
    if (badge && badgeText) {
        badgeText.textContent = user.teacher_role_display || 'Teacher';
        const roleColors = {
            'class_teacher': 'info',
            'head_of_studies': 'warning',
            'senior_teacher': 'success',
            'deputy': 'accent'
        };
        badge.classList.add(roleColors[user.teacher_role] || 'info');
    }
}

function initTabs(user) {
    if (user.can_message_parents) {
        document.getElementById('tabMessaging').style.display = '';
    }
    if (user.can_manage_academics) {
        document.getElementById('tabAcademics').style.display = '';
    }
    if (user.can_manage_announcements) {
        document.getElementById('tabAnnouncements').style.display = '';
    }
    if (user.can_manage_events) {
        document.getElementById('tabEvents').style.display = '';
    }

    document.querySelectorAll('.portal-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.portal-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            const tabId = tab.dataset.tab;
            document.getElementById('content-' + tabId).classList.add('active');

            if (tabId === 'academics' && user.can_manage_academics) {
                loadAcademicsOverview();
            }
        });
    });
}

function loadQuickActions(user) {
    const container = document.getElementById('quickActions');
    let html = `
        <button class="quick-action-btn" onclick="window.location.href='/attendance'">
            <i class="lucide-calendar-check"></i>
            <span>Mark Attendance</span>
        </button>
    `;

    if (user.can_message_parents) {
        html += `
            <button class="quick-action-btn" onclick="switchTab('messaging')">
                <i class="lucide-message-square"></i>
                <span>Message Parents</span>
            </button>
        `;
    }
    if (user.can_manage_academics) {
        html += `
            <button class="quick-action-btn" onclick="switchTab('academics')">
                <i class="lucide-graduation-cap"></i>
                <span>Manage Academics</span>
            </button>
        `;
    }
    if (user.can_manage_announcements) {
        html += `
            <button class="quick-action-btn" onclick="switchTab('announcements')">
                <i class="lucide-megaphone"></i>
                <span>Post Announcement</span>
            </button>
        `;
    }
    if (user.can_manage_events) {
        html += `
            <button class="quick-action-btn" onclick="switchTab('events')">
                <i class="lucide-calendar-plus"></i>
                <span>Create Event</span>
            </button>
        `;
    }

    html += `
        <button class="quick-action-btn" onclick="window.location.href='/messages'">
            <i class="lucide-mail"></i>
            <span>Messages</span>
        </button>
    `;

    container.innerHTML = html;
}

function switchTab(tabName) {
    const tab = document.querySelector(`.portal-tab[data-tab="${tabName}"]`);
    if (tab) tab.click();
}

async function loadProfile() {
    try {
        const data = await api.get('/teachers/me');
        if (data.teacher) {
            const classes = data.classes || [];
            document.getElementById('statClasses').textContent = classes.length;
            const totalStudents = classes.reduce((sum, c) => sum + (c.student_count || 0), 0);
            document.getElementById('statStudents').textContent = totalStudents;

            let classHtml = '';
            if (classes.length === 0) {
                classHtml = '<div class="empty-state">No classes assigned yet</div>';
            } else {
                const colors = ['accent', 'info', 'success', 'warning'];
                classes.forEach((cls, i) => {
                    const color = colors[i % colors.length];
                    const initials = cls.name.split(' ').map(w => w[0]).join('').slice(0, 2);
                    classHtml += `
                        <div class="student-card" style="margin-bottom: 8px;">
                            <div class="student-card-header">
                                <div class="student-card-avatar" style="background: rgba(var(--color-${color}-rgb, 230, 57, 70), 0.08); color: var(--color-${color});">${initials}</div>
                                <div>
                                    <div class="student-card-name">${cls.name}</div>
                                    <div class="student-card-id">${cls.student_count} Students${cls.is_class_teacher ? ' - Class Teacher' : ''}</div>
                                </div>
                            </div>
                        </div>
                    `;
                });
            }
            document.getElementById('myClassesList').innerHTML =
                `<div class="student-cards" style="grid-template-columns: 1fr;">${classHtml}</div>`;
        }
    } catch (err) {
        console.error('Failed to load profile:', err);
    }
}

async function loadParents() {
    try {
        const data = await api.get('/teachers/my-class-parents');
        const parents = data.parents || [];
        const select = document.getElementById('parentSelect');
        const list = document.getElementById('parentsList');

        if (parents.length === 0) {
            select.innerHTML = '<option value="">No parents found for your class</option>';
            list.innerHTML = '<div class="empty-state">No parents linked to students in your class</div>';
            return;
        }

        select.innerHTML = '<option value="">Select a parent...</option>';
        let listHtml = '';

        parents.forEach(p => {
            const parent = p.parent;
            const children = p.children || [];
            const childNames = children.map(c => c.name).join(', ');
            select.innerHTML += `<option value="${parent.user_id}">${parent.full_name} (Parent of ${childNames})</option>`;

            listHtml += `
                <div class="parent-card">
                    <div class="parent-card-header">
                        <div class="parent-avatar">${parent.full_name.charAt(0)}</div>
                        <div>
                            <div class="parent-name">${parent.full_name}</div>
                            <div class="parent-children">Children: ${childNames}</div>
                        </div>
                    </div>
                </div>
            `;
        });

        list.innerHTML = listHtml;
    } catch (err) {
        console.error('Failed to load parents:', err);
    }
}

async function loadAcademicsOverview() {
    try {
        const data = await api.get('/teachers/academics/overview');
        document.getElementById('statAssignments').textContent = data.total_assignments || 0;
        document.getElementById('statExams').textContent = data.total_exams || 0;

        let overviewHtml = `
            <div class="academic-stats">
                <div class="academic-stat">
                    <span class="academic-stat-value">${data.total_classes || 0}</span>
                    <span class="academic-stat-label">Classes</span>
                </div>
                <div class="academic-stat">
                    <span class="academic-stat-value">${data.total_subjects || 0}</span>
                    <span class="academic-stat-label">Subjects</span>
                </div>
                <div class="academic-stat">
                    <span class="academic-stat-value">${data.total_exams || 0}</span>
                    <span class="academic-stat-label">Exams</span>
                </div>
                <div class="academic-stat">
                    <span class="academic-stat-value">${data.total_assignments || 0}</span>
                    <span class="academic-stat-label">Assignments</span>
                </div>
            </div>
        `;
        document.getElementById('academicOverview').innerHTML = overviewHtml;

        let examsHtml = '';
        const exams = data.recent_exams || [];
        if (exams.length === 0) {
            examsHtml = '<div class="empty-state">No examinations yet</div>';
        } else {
            exams.forEach(exam => {
                examsHtml += `
                    <div class="exam-card">
                        <div class="exam-name">${exam.name}</div>
                        <div class="exam-meta">
                            <span class="exam-type">${exam.exam_type}</span>
                            <span class="exam-date">${exam.start_date || 'TBD'}</span>
                            <span class="exam-status status-${exam.status}">${exam.status}</span>
                        </div>
                    </div>
                `;
            });
        }
        document.getElementById('recentExams').innerHTML = examsHtml;
    } catch (err) {
        console.error('Failed to load academics:', err);
        document.getElementById('academicOverview').innerHTML = '<div class="empty-state">Unable to load academic data</div>';
    }
}

async function loadAnnouncements() {
    try {
        const data = await api.get('/teachers/announcements');
        const announcements = data.announcements || [];
        const container = document.getElementById('announcementsList');

        if (announcements.length === 0) {
            container.innerHTML = '<div class="empty-state">No announcements yet</div>';
            return;
        }

        let html = '';
        announcements.forEach(ann => {
            const date = new Date(ann.created_at).toLocaleDateString();
            const priorityClass = ann.priority === 'high' ? 'priority-high' : (ann.priority === 'urgent' ? 'priority-urgent' : '');
            html += `
                <div class="announcement-card ${priorityClass}">
                    <div class="announcement-title">${ann.title}</div>
                    <div class="announcement-body">${ann.body}</div>
                    <div class="announcement-meta">
                        <span>By ${ann.author_name || 'Unknown'}</span>
                        <span>${date}</span>
                        ${ann.target_role ? `<span class="announcement-target">${ann.target_role}</span>` : ''}
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;
    } catch (err) {
        console.error('Failed to load announcements:', err);
    }
}

async function loadEvents() {
    try {
        const data = await api.get('/teachers/events');
        const events = data.events || [];
        const container = document.getElementById('eventsList');

        if (events.length === 0) {
            container.innerHTML = '<div class="empty-state">No events yet</div>';
            return;
        }

        let html = '';
        events.forEach(evt => {
            const date = evt.event_date ? new Date(evt.event_date).toLocaleDateString() : 'TBD';
            const time = evt.event_date ? new Date(evt.event_date).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}) : '';
            html += `
                <div class="event-card">
                    <div class="event-date-badge">
                        <span class="event-day">${date}</span>
                        ${time ? `<span class="event-time">${time}</span>` : ''}
                    </div>
                    <div class="event-details">
                        <div class="event-title">${evt.title}</div>
                        <div class="event-meta">
                            ${evt.location ? `<span><i class="lucide-map-pin"></i> ${evt.location}</span>` : ''}
                            ${evt.event_type ? `<span class="event-type-badge">${evt.event_type}</span>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;
    } catch (err) {
        console.error('Failed to load events:', err);
    }
}

function initEventHandlers(user) {
    // Send message to parent
    const sendBtn = document.getElementById('sendMessageBtn');
    if (sendBtn) {
        sendBtn.addEventListener('click', async () => {
            const parentUserId = document.getElementById('parentSelect').value;
            const subject = document.getElementById('msgSubject').value;
            const body = document.getElementById('msgBody').value;

            if (!parentUserId || !body) {
                showStatus('messageStatus', 'Please select a parent and enter a message', 'error');
                return;
            }

            sendBtn.disabled = true;
            sendBtn.innerHTML = '<i class="lucide-loader"></i> Sending...';

            try {
                await api.post('/teachers/message-parent', {
                    parent_user_id: parseInt(parentUserId),
                    subject,
                    body
                });
                showStatus('messageStatus', 'Message sent successfully', 'success');
                document.getElementById('msgSubject').value = '';
                document.getElementById('msgBody').value = '';
                document.getElementById('parentSelect').value = '';
            } catch (err) {
                showStatus('messageStatus', 'Failed to send message', 'error');
            } finally {
                sendBtn.disabled = false;
                sendBtn.innerHTML = '<i class="lucide-send"></i> Send Message';
            }
        });
    }

    // Create exam
    const examBtn = document.getElementById('createExamBtn');
    if (examBtn) {
        examBtn.addEventListener('click', async () => {
            const name = document.getElementById('examName').value;
            const examType = document.getElementById('examType').value;
            const startDate = document.getElementById('examStartDate').value;
            const endDate = document.getElementById('examEndDate').value;

            if (!name) {
                alert('Please enter an exam name');
                return;
            }

            examBtn.disabled = true;
            try {
                await api.post('/teachers/academics/exams', {
                    name,
                    exam_type: examType,
                    start_date: startDate || null,
                    end_date: endDate || null
                });
                document.getElementById('examName').value = '';
                loadAcademicsOverview();
            } catch (err) {
                alert('Failed to create examination');
            } finally {
                examBtn.disabled = false;
            }
        });
    }

    // Post announcement
    const annBtn = document.getElementById('postAnnouncementBtn');
    if (annBtn) {
        annBtn.addEventListener('click', async () => {
            const title = document.getElementById('annTitle').value;
            const body = document.getElementById('annBody').value;
            const target = document.getElementById('annTarget').value;
            const priority = document.getElementById('annPriority').value;

            if (!title || !body) {
                showStatus('annStatus', 'Please enter title and message', 'error');
                return;
            }

            annBtn.disabled = true;
            try {
                await api.post('/teachers/announcements', {
                    title,
                    body,
                    target_role: target,
                    priority
                });
                showStatus('annStatus', 'Announcement posted successfully', 'success');
                document.getElementById('annTitle').value = '';
                document.getElementById('annBody').value = '';
                loadAnnouncements();
            } catch (err) {
                showStatus('annStatus', 'Failed to post announcement', 'error');
            } finally {
                annBtn.disabled = false;
            }
        });
    }

    // Create event
    const eventBtn = document.getElementById('createEventBtn');
    if (eventBtn) {
        eventBtn.addEventListener('click', async () => {
            const title = document.getElementById('eventTitle').value;
            const desc = document.getElementById('eventDesc').value;
            const dateVal = document.getElementById('eventDate').value;
            const timeVal = document.getElementById('eventTime').value;
            const location = document.getElementById('eventLocation').value;
            const eventType = document.getElementById('eventType').value;

            if (!title || !dateVal) {
                showStatus('eventStatus', 'Please enter event title and date', 'error');
                return;
            }

            const eventDate = timeVal ? `${dateVal}T${timeVal}:00` : `${dateVal}T09:00:00`;

            eventBtn.disabled = true;
            try {
                await api.post('/teachers/events', {
                    title,
                    description: desc,
                    event_date: eventDate,
                    location,
                    event_type: eventType
                });
                showStatus('eventStatus', 'Event created successfully', 'success');
                document.getElementById('eventTitle').value = '';
                document.getElementById('eventDesc').value = '';
                document.getElementById('eventDate').value = '';
                document.getElementById('eventTime').value = '';
                document.getElementById('eventLocation').value = '';
                loadEvents();
            } catch (err) {
                showStatus('eventStatus', 'Failed to create event', 'error');
            } finally {
                eventBtn.disabled = false;
            }
        });
    }
}

function showStatus(elementId, message, type) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = message;
        el.className = `message-status ${type}`;
        el.style.display = 'block';
        setTimeout(() => { el.style.display = 'none'; }, 4000);
    }
}
