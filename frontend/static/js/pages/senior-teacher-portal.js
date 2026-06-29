/* Senior Teacher Portal */
const API = '/api/senior-teacher';
const token = localStorage.getItem('token') || localStorage.getItem('access_token');
const headers = { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token };

function apiGet(url) { return fetch(url, { headers }).then(r => r.json()); }
function apiPost(url, data) { return fetch(url, { method: 'POST', headers, body: JSON.stringify(data) }).then(r => r.json()); }

document.addEventListener('DOMContentLoaded', () => {
    if (!token) { window.location.href = '/login'; return; }
    initSidebar();
    initNavigation();
    loadDashboard();
});

function initSidebar() {
    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    if (toggle) toggle.addEventListener('click', () => sidebar.classList.toggle('collapsed'));
    const logout = document.getElementById('logoutBtn');
    if (logout) logout.addEventListener('click', e => {
        e.preventDefault(); localStorage.clear(); window.location.href = '/login';
    });
}

function initNavigation() {
    document.querySelectorAll('.nav-item[data-section]').forEach(item => {
        item.addEventListener('click', e => {
            e.preventDefault();
            switchSection(item.dataset.section);
        });
    });
}

const sectionTitles = {
    dashboard: ['Instructional Dashboard', 'Teacher leadership and supervision'],
    'lesson-plans': ['Lesson Plans', 'Monitor and review lesson planning'],
    schemes: ['Schemes of Work', 'Term planning and curriculum delivery'],
    observations: ['Classroom Observations', 'Teaching quality assessment'],
    syllabus: ['Syllabus Coverage', 'Curriculum progress tracking'],
    announcements: ['Announcements', 'School-wide communications'],
    events: ['Events', 'School calendar and event management'],
    reports: ['Reports & Analytics', 'Teacher performance analysis'],
};

function switchSection(section) {
    document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const el = document.getElementById('section-' + section);
    if (el) el.classList.add('active');
    const nav = document.querySelector(`.nav-item[data-section="${section}"]`);
    if (nav) nav.classList.add('active');
    const t = sectionTitles[section] || ['', ''];
    document.getElementById('pageTitle').textContent = t[0];
    document.getElementById('pageSubtitle').textContent = t[1];

    const loaders = {
        dashboard: loadDashboard, 'lesson-plans': loadLessonPlans,
        schemes: loadSchemes, observations: loadObservations,
        syllabus: loadSyllabus, announcements: loadAnnouncements,
        events: loadEvents, reports: () => {},
    };
    if (loaders[section]) loaders[section]();
}

/* Dashboard */
let chartLessons;
function loadDashboard() {
    apiGet(API + '/dashboard').then(d => {
        document.getElementById('kpiTeachers').textContent = d.total_teachers;
        document.getElementById('kpiLessons').textContent = d.total_lessons;
        document.getElementById('kpiLessonRate').textContent = d.lesson_completion_rate + '%';
        document.getElementById('kpiCoverage').textContent = d.avg_syllabus_coverage + '%';
        document.getElementById('summCompleted').textContent = d.completed_lessons;
        document.getElementById('summObservations').textContent = d.pending_observations;
        document.getElementById('summSchemes').textContent = d.total_schemes;

        if (chartLessons) chartLessons.destroy();
        const ctx = document.getElementById('chartLessons');
        if (ctx && d.lessons_by_status.length) {
            chartLessons = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: d.lessons_by_status.map(l => l.status),
                    datasets: [{ data: d.lessons_by_status.map(l => l.count), backgroundColor: ['#10b981','#3b82f6','#f59e0b','#ef4444','#8b5cf6'] }]
                },
                options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
            });
        }

        const obsEl = document.getElementById('recentObservations');
        obsEl.innerHTML = d.recent_observations.length ? d.recent_observations.map(o => `
            <div class="activity-item">
                <span class="activity-text"><strong>${o.teacher_name}</strong> - Rating: ${o.overall_rating || 'N/A'}/5</span>
                <span class="activity-meta">${o.observation_date}</span>
            </div>
        `).join('') : '<p class="text-muted text-center">No observations yet</p>';
    });
}

/* Lesson Plans */
function loadLessonPlans() {
    const tid = document.getElementById('lpTeacherFilter')?.value || '';
    apiGet(API + '/lesson-plans' + (tid ? '?teacher_id=' + tid : '')).then(data => {
        document.getElementById('lessonPlansBody').innerHTML = data.map(lp => `
            <tr>
                <td>${lp.lesson_date || 'N/A'}</td>
                <td>${lp.teacher_name}</td>
                <td>${lp.subject_name}</td>
                <td>${lp.class_name}</td>
                <td>${lp.topic}</td>
                <td><span class="status-badge ${lp.status}">${lp.status}</span></td>
                <td>
                    ${lp.status === 'planned' ? `<button class="btn btn-sm btn-success" onclick="reviewLesson(${lp.id})">Review</button>` : ''}
                </td>
            </tr>
        `).join('') || '<tr><td colspan="7" class="text-center text-muted">No lesson plans found</td></tr>';
    });
}

function reviewLesson(id) {
    const notes = prompt('Review notes:');
    if (notes !== null) {
        apiPost(API + '/lesson-plans/' + id + '/review', { status: 'reviewed', notes }).then(() => loadLessonPlans());
    }
}

/* Schemes */
function loadSchemes() {
    apiGet(API + '/schemes').then(data => {
        document.getElementById('schemesBody').innerHTML = data.map(s => `
            <tr>
                <td>${s.teacher_name}</td>
                <td>${s.subject_name}</td>
                <td>${s.class_name}</td>
                <td>${s.term}</td>
                <td>Week ${s.week_number || '-'}</td>
                <td>${s.topic}</td>
                <td><span class="status-badge ${s.status}">${s.status}</span></td>
            </tr>
        `).join('') || '<tr><td colspan="7" class="text-center text-muted">No schemes found</td></tr>';
    });
}

/* Observations */
function loadObservations() {
    apiGet(API + '/observations').then(data => {
        document.getElementById('observationsBody').innerHTML = data.map(o => `
            <tr>
                <td>${o.observation_date}</td>
                <td>${o.teacher_name}</td>
                <td>${o.subject_name || 'N/A'}</td>
                <td>
                    <div class="rating">${[1,2,3,4,5].map(i => `<span class="rating-star ${i <= (o.overall_rating||0) ? 'filled' : ''}">&#9733;</span>`).join('')}</div>
                </td>
                <td>${(o.strengths || '').substring(0, 50)}${(o.strengths||'').length > 50 ? '...' : ''}</td>
                <td><button class="btn btn-sm btn-outline" onclick="viewObservation(${o.id})">View</button></td>
            </tr>
        `).join('') || '<tr><td colspan="6" class="text-center text-muted">No observations yet</td></tr>';
    });
}

function showObservationModal() {
    document.getElementById('modalTitle').textContent = 'New Classroom Observation';
    apiGet('/api/teachers/').then(data => {
        const teachers = data.teachers || data;
        document.getElementById('modalBody').innerHTML = `
            <form id="obsForm" onsubmit="submitObservation(event)">
                <div class="form-group">
                    <label>Teacher</label>
                    <select name="teacher_id" required>${teachers.map(t => `<option value="${t.id}">${t.full_name}</option>`).join('')}</select>
                </div>
                <div class="form-group"><label>Date</label><input type="date" name="observation_date" value="${new Date().toISOString().split('T')[0]}" required></div>
                <div class="form-row">
                    <div class="form-group"><label>Lesson Delivery (1-5)</label><input type="number" name="lesson_delivery" min="1" max="5"></div>
                    <div class="form-group"><label>Student Engagement (1-5)</label><input type="number" name="student_engagement" min="1" max="5"></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Classroom Mgmt (1-5)</label><input type="number" name="classroom_management" min="1" max="5"></div>
                    <div class="form-group"><label>Overall Rating (1-5)</label><input type="number" name="overall_rating" min="1" max="5" required></div>
                </div>
                <div class="form-group"><label>Strengths</label><textarea name="strengths"></textarea></div>
                <div class="form-group"><label>Areas for Improvement</label><textarea name="areas_for_improvement"></textarea></div>
                <div class="form-group"><label>Recommendations</label><textarea name="recommendations"></textarea></div>
                <button type="submit" class="btn btn-primary" style="width:100%">Save Observation</button>
            </form>
        `;
        openModal();
    });
}

function submitObservation(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    apiPost(API + '/observations', {
        teacher_id: parseInt(f.get('teacher_id')),
        observation_date: f.get('observation_date'),
        lesson_delivery: parseInt(f.get('lesson_delivery')) || null,
        student_engagement: parseInt(f.get('student_engagement')) || null,
        classroom_management: parseInt(f.get('classroom_management')) || null,
        overall_rating: parseInt(f.get('overall_rating')),
        strengths: f.get('strengths'),
        areas_for_improvement: f.get('areas_for_improvement'),
        recommendations: f.get('recommendations'),
    }).then(() => { closeModal(); loadObservations(); });
}

/* Syllabus */
function loadSyllabus() {
    apiGet(API + '/syllabus').then(data => {
        document.getElementById('syllabusBody').innerHTML = data.map(s => {
            const pct = s.percentage || 0;
            const cls = pct >= 70 ? 'good' : pct >= 40 ? 'average' : 'poor';
            return `<tr>
                <td>${s.teacher_name}</td>
                <td>${s.subject_name}</td>
                <td>${s.class_name}</td>
                <td>
                    <div style="display:flex;align-items:center;gap:8px">
                        <div class="progress-bar" style="width:100px"><div class="progress-fill ${cls}" style="width:${pct}%"></div></div>
                        <span>${pct}%</span>
                    </div>
                </td>
                <td>${s.covered_topics}/${s.total_topics}</td>
                <td>${s.remarks || '-'}</td>
            </tr>`;
        }).join('') || '<tr><td colspan="6" class="text-center text-muted">No coverage data</td></tr>';
    });
}

/* Announcements */
function loadAnnouncements() {
    apiGet('/api/teachers/announcements').then(data => {
        const items = data.announcements || data;
        document.getElementById('announcementsGrid').innerHTML = items.map(a => `
            <div class="info-card">
                <h4>${a.title}</h4>
                <p>${a.body}</p>
                <p class="text-muted" style="font-size:12px;margin-top:8px">By ${a.author_name} - ${new Date(a.created_at).toLocaleDateString()}</p>
            </div>
        `).join('') || '<p class="text-muted text-center">No announcements</p>';
    });
}

function showAnnouncementModal() {
    document.getElementById('modalTitle').textContent = 'Post Announcement';
    document.getElementById('modalBody').innerHTML = `
        <form id="annForm" onsubmit="submitAnnouncement(event)">
            <div class="form-group"><label>Title</label><input type="text" name="title" required></div>
            <div class="form-group"><label>Content</label><textarea name="body" required></textarea></div>
            <div class="form-group">
                <label>Target</label>
                <select name="target_role"><option value="">All</option><option value="teacher">Teachers</option><option value="parent">Parents</option></select>
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%">Post</button>
        </form>
    `;
    openModal();
}

function submitAnnouncement(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    apiPost('/api/teachers/announcements', {
        title: f.get('title'), body: f.get('body'), target_role: f.get('target_role'),
    }).then(() => { closeModal(); loadAnnouncements(); });
}

/* Events */
function loadEvents() {
    apiGet('/api/teachers/events').then(data => {
        const items = data.events || data;
        document.getElementById('eventsGrid').innerHTML = items.map(ev => `
            <div class="info-card">
                <h4>${ev.title}</h4>
                <p>${ev.description || ''}</p>
                <p><strong>Date:</strong> ${new Date(ev.event_date).toLocaleDateString()}</p>
                <p>${ev.location ? '<strong>Location:</strong> ' + ev.location : ''}</p>
            </div>
        `).join('') || '<p class="text-muted text-center">No events</p>';
    });
}

function showEventModal() {
    document.getElementById('modalTitle').textContent = 'Create Event';
    document.getElementById('modalBody').innerHTML = `
        <form id="eventForm" onsubmit="submitEvent(event)">
            <div class="form-group"><label>Title</label><input type="text" name="title" required></div>
            <div class="form-group"><label>Description</label><textarea name="description"></textarea></div>
            <div class="form-row">
                <div class="form-group"><label>Date & Time</label><input type="datetime-local" name="event_date" required></div>
                <div class="form-group"><label>Location</label><input type="text" name="location"></div>
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%">Create</button>
        </form>
    `;
    openModal();
}

function submitEvent(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    apiPost('/api/teachers/events', {
        title: f.get('title'), description: f.get('description'),
        event_date: f.get('event_date'), location: f.get('location'),
    }).then(() => { closeModal(); loadEvents(); });
}

/* Reports */
function loadTeacherPerformanceReport() {
    const output = document.getElementById('reportOutput');
    const title = document.getElementById('reportTitle');
    const content = document.getElementById('reportContent');
    output.style.display = 'block';
    title.textContent = 'Teacher Performance Report';

    apiGet(API + '/reports/teacher-performance').then(data => {
        content.innerHTML = `
            <div class="data-table-wrapper">
                <table class="data-table">
                    <thead><tr>
                        <th>Teacher</th><th>Dept</th><th>Lessons</th><th>Completion</th>
                        <th>Avg Rating</th><th>Syllabus</th>
                    </tr></thead>
                    <tbody>${data.map(t => {
                        const covCls = t.avg_syllabus_coverage >= 70 ? 'good' : t.avg_syllabus_coverage >= 40 ? 'average' : 'poor';
                        return `<tr>
                            <td>${t.teacher_name}</td>
                            <td>${t.department || 'N/A'}</td>
                            <td>${t.completed_lessons}/${t.total_lessons}</td>
                            <td>${t.lesson_rate}%</td>
                            <td><div class="rating">${[1,2,3,4,5].map(i => `<span class="rating-star ${i <= Math.round(t.avg_observation_rating) ? 'filled' : ''}">&#9733;</span>`).join('')}</div></td>
                            <td><div style="display:flex;align-items:center;gap:8px"><div class="progress-bar" style="width:80px"><div class="progress-fill ${covCls}" style="width:${t.avg_syllabus_coverage}%"></div></div>${t.avg_syllabus_coverage}%</div></td>
                        </tr>`;
                    }).join('')}</tbody>
                </table>
            </div>
        `;
    });
}

/* Modal Helpers */
function openModal() { document.getElementById('modalOverlay').classList.add('active'); }
function closeModal() { document.getElementById('modalOverlay').classList.remove('active'); }
document.getElementById('modalOverlay')?.addEventListener('click', e => {
    if (e.target === e.currentTarget) closeModal();
});
