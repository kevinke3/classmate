/* Class Teacher Portal */
const API = '/api/class-teacher';
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
    dashboard: ['Class Dashboard', 'Classroom management and student welfare'],
    students: ['My Students', 'Student profiles and records'],
    attendance: ['Attendance', 'Daily attendance management'],
    behavior: ['Behavior Tracking', 'Student behavior records'],
    counseling: ['Counseling', 'Counseling sessions and notes'],
    parents: ['Parent Messages', 'Communication with parents'],
    reports: ['Reports', 'Class reports and analytics'],
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
        dashboard: loadDashboard, students: loadStudents,
        attendance: initAttendance, behavior: loadBehavior,
        counseling: loadCounseling, parents: loadParents, reports: () => {},
    };
    if (loaders[section]) loaders[section]();
}

/* Dashboard */
function loadDashboard() {
    apiGet(API + '/dashboard').then(d => {
        document.getElementById('kpiStudents').textContent = d.student_count;
        document.getElementById('kpiAttendance').textContent = d.attendance_rate + '%';
        document.getElementById('kpiAvgScore').textContent = d.avg_score;
        document.getElementById('kpiDiscipline').textContent = d.open_discipline;
        document.getElementById('summHomework').textContent = d.homework_pending;
        document.getElementById('summFees').textContent = d.unpaid_invoices;
        document.getElementById('summPresent').textContent = d.today_present + '/' + d.today_total;

        const badge = document.getElementById('classBadge');
        if (badge && d.class_names.length) badge.textContent = d.class_names.join(', ');

        const el = document.getElementById('recentBehavior');
        el.innerHTML = d.recent_behavior.length ? d.recent_behavior.map(b => `
            <div class="activity-item">
                <span class="activity-text"><strong>${b.student_name}</strong> - ${b.category}
                    <span class="status-badge ${b.behavior_type}">${b.behavior_type}</span></span>
                <span class="activity-meta">${b.date}</span>
            </div>
        `).join('') : '<p class="text-muted text-center">No recent records</p>';
    });
}

/* Students */
let allStudents = [];
function loadStudents() {
    apiGet(API + '/students').then(data => {
        allStudents = data;
        renderStudentCards(data);
    });
    const search = document.getElementById('studentSearch');
    if (search) search.oninput = () => {
        const q = search.value.toLowerCase();
        renderStudentCards(allStudents.filter(s =>
            s.full_name.toLowerCase().includes(q) || s.admission_number.toLowerCase().includes(q)
        ));
    };
}

function renderStudentCards(students) {
    document.getElementById('studentCards').innerHTML = students.map(s => `
        <div class="info-card">
            <h4>${s.full_name}</h4>
            <p>${s.admission_number}</p>
            <p>Gender: ${s.gender || 'N/A'} | Status: <span class="status-badge ${s.status}">${s.status}</span></p>
            <div class="card-footer">
                <button class="btn btn-sm btn-outline" onclick="viewStudentProfile(${s.id})">Profile</button>
            </div>
        </div>
    `).join('') || '<p class="text-muted text-center">No students found</p>';
}

function viewStudentProfile(sid) {
    apiGet(API + '/students/' + sid + '/profile').then(d => {
        document.getElementById('modalTitle').textContent = d.student.full_name + ' - Profile';
        document.getElementById('modalBody').innerHTML = `
            <div class="summary-grid" style="margin-bottom:16px">
                <div class="summary-card"><div class="summary-label">Attendance</div><div class="summary-value">${d.attendance_rate}%</div></div>
                <div class="summary-card"><div class="summary-label">Fee Status</div><div class="summary-value">${d.fee_cleared ? 'Cleared' : 'KES ' + (d.outstanding || 0).toLocaleString()}</div></div>
            </div>
            <h4 style="margin-bottom:8px">Recent Grades</h4>
            ${d.grades.length ? `<div class="data-table-wrapper"><table class="data-table">
                <thead><tr><th>Subject</th><th>Marks</th><th>Grade</th></tr></thead>
                <tbody>${d.grades.slice(0, 10).map(g => `<tr><td>${g.subject_name}</td><td>${g.marks}</td><td>${g.grade}</td></tr>`).join('')}</tbody>
            </table></div>` : '<p class="text-muted">No grades</p>'}
            <h4 style="margin:16px 0 8px">Discipline</h4>
            ${d.discipline.length ? d.discipline.map(di => `
                <div class="activity-item"><span class="activity-text">${di.category} - <span class="status-badge ${di.severity}">${di.severity}</span></span><span class="activity-meta">${di.incident_date}</span></div>
            `).join('') : '<p class="text-muted">No discipline records</p>'}
            <h4 style="margin:16px 0 8px">Behavior</h4>
            ${d.behaviors.length ? d.behaviors.map(b => `
                <div class="activity-item"><span class="activity-text">${b.category} - <span class="status-badge ${b.behavior_type}">${b.behavior_type}</span></span><span class="activity-meta">${b.date}</span></div>
            `).join('') : '<p class="text-muted">No behavior records</p>'}
        `;
        openModal();
    });
}

/* Attendance */
function initAttendance() {
    const dateEl = document.getElementById('attDate');
    if (dateEl && !dateEl.value) dateEl.value = new Date().toISOString().split('T')[0];
    loadAttendance();
}

function loadAttendance() {
    const d = document.getElementById('attDate')?.value || new Date().toISOString().split('T')[0];
    Promise.all([apiGet(API + '/students'), apiGet(API + '/attendance?date=' + d)]).then(([students, att]) => {
        const attMap = {};
        att.forEach(a => { attMap[a.student_id] = a; });
        const body = document.getElementById('attendanceBody');
        body.innerHTML = students.map(s => {
            const record = attMap[s.id];
            const status = record ? record.status : '';
            return `<tr>
                <td>${s.full_name}</td>
                <td>${s.admission_number}</td>
                <td>
                    <select class="filter-select att-select" data-student="${s.id}" data-class="${s.class_id || 0}">
                        <option value="">--</option>
                        <option value="present" ${status === 'present' ? 'selected' : ''}>Present</option>
                        <option value="absent" ${status === 'absent' ? 'selected' : ''}>Absent</option>
                        <option value="late" ${status === 'late' ? 'selected' : ''}>Late</option>
                    </select>
                </td>
                <td><input type="text" class="search-input att-remarks" data-student="${s.id}" style="min-width:120px" value="${record?.remarks || ''}" placeholder="Remarks"></td>
            </tr>`;
        }).join('');
        document.getElementById('saveAttendance').style.display = students.length ? '' : 'none';
    });
}

function saveAttendance() {
    const d = document.getElementById('attDate')?.value || new Date().toISOString().split('T')[0];
    const records = [];
    document.querySelectorAll('.att-select').forEach(sel => {
        if (sel.value) {
            const remarkEl = document.querySelector(`.att-remarks[data-student="${sel.dataset.student}"]`);
            records.push({
                student_id: parseInt(sel.dataset.student),
                class_id: parseInt(sel.dataset.class),
                status: sel.value,
                remarks: remarkEl?.value || '',
            });
        }
    });
    if (!records.length) { alert('No attendance to save'); return; }
    apiPost(API + '/attendance', { date: d, records }).then(r => {
        alert(r.message || 'Saved');
        loadAttendance();
    });
}

/* Behavior */
function loadBehavior() {
    apiGet(API + '/behavior').then(data => {
        document.getElementById('behaviorBody').innerHTML = data.map(b => `
            <tr>
                <td>${b.date}</td>
                <td>${b.student_name}</td>
                <td><span class="status-badge ${b.behavior_type}">${b.behavior_type}</span></td>
                <td>${b.category}</td>
                <td>${(b.description || '').substring(0, 60)}</td>
                <td>${b.points >= 0 ? '+' : ''}${b.points}</td>
            </tr>
        `).join('') || '<tr><td colspan="6" class="text-center text-muted">No behavior records</td></tr>';
    });
}

function showBehaviorModal() {
    document.getElementById('modalTitle').textContent = 'Record Behavior';
    apiGet(API + '/students').then(data => {
        document.getElementById('modalBody').innerHTML = `
            <form id="behaviorForm" onsubmit="submitBehavior(event)">
                <div class="form-group">
                    <label>Student</label>
                    <select name="student_id" required>${data.map(s => `<option value="${s.id}">${s.full_name}</option>`).join('')}</select>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Type</label>
                        <select name="behavior_type"><option value="positive">Positive</option><option value="negative">Negative</option></select>
                    </div>
                    <div class="form-group">
                        <label>Category</label>
                        <select name="category"><option>Academic</option><option>Conduct</option><option>Leadership</option><option>Sports</option><option>Attendance</option></select>
                    </div>
                </div>
                <div class="form-group"><label>Description</label><textarea name="description" required></textarea></div>
                <div class="form-group"><label>Points</label><input type="number" name="points" value="0"></div>
                <button type="submit" class="btn btn-primary" style="width:100%">Save</button>
            </form>
        `;
        openModal();
    });
}

function submitBehavior(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    apiPost(API + '/behavior', {
        student_id: parseInt(f.get('student_id')),
        behavior_type: f.get('behavior_type'),
        category: f.get('category'),
        description: f.get('description'),
        points: parseInt(f.get('points')),
    }).then(() => { closeModal(); loadBehavior(); });
}

/* Counseling */
function loadCounseling() {
    apiGet(API + '/counseling').then(data => {
        document.getElementById('counselingBody').innerHTML = data.map(c => `
            <tr>
                <td>${c.session_date}</td>
                <td>${c.student_name}</td>
                <td>${c.category}</td>
                <td>${(c.summary || '').substring(0, 60)}</td>
                <td>${c.follow_up_date || '-'}</td>
                <td><span class="status-badge ${c.status}">${c.status}</span></td>
            </tr>
        `).join('') || '<tr><td colspan="6" class="text-center text-muted">No counseling records</td></tr>';
    });
}

function showCounselingModal() {
    document.getElementById('modalTitle').textContent = 'New Counseling Session';
    apiGet(API + '/students').then(data => {
        document.getElementById('modalBody').innerHTML = `
            <form id="counselForm" onsubmit="submitCounseling(event)">
                <div class="form-group">
                    <label>Student</label>
                    <select name="student_id" required>${data.map(s => `<option value="${s.id}">${s.full_name}</option>`).join('')}</select>
                </div>
                <div class="form-group">
                    <label>Category</label>
                    <select name="category"><option>Academic</option><option>Behavioral</option><option>Personal</option><option>Family</option><option>Career</option></select>
                </div>
                <div class="form-group"><label>Summary</label><textarea name="summary" required></textarea></div>
                <div class="form-group"><label>Recommendations</label><textarea name="recommendations"></textarea></div>
                <div class="form-group"><label>Follow-up Date</label><input type="date" name="follow_up_date"></div>
                <button type="submit" class="btn btn-primary" style="width:100%">Save</button>
            </form>
        `;
        openModal();
    });
}

function submitCounseling(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    apiPost(API + '/counseling', {
        student_id: parseInt(f.get('student_id')),
        category: f.get('category'),
        summary: f.get('summary'),
        recommendations: f.get('recommendations'),
        follow_up_date: f.get('follow_up_date') || null,
    }).then(() => { closeModal(); loadCounseling(); });
}

/* Parents */
function loadParents() {
    apiGet(API + '/parents').then(data => {
        document.getElementById('parentCards').innerHTML = data.map(p => `
            <div class="info-card">
                <h4>${p.full_name}</h4>
                <p>${p.email}</p>
                <p>Child: ${p.student_name || 'N/A'}</p>
                <div class="card-footer">
                    <button class="btn btn-sm btn-primary" onclick="showMessageModal(${p.id}, '${p.full_name}')">Message</button>
                </div>
            </div>
        `).join('') || '<p class="text-muted text-center">No parents found</p>';
    });
}

function showMessageModal(parentId, parentName) {
    document.getElementById('modalTitle').textContent = 'Message ' + parentName;
    document.getElementById('modalBody').innerHTML = `
        <form id="msgForm" onsubmit="sendMessage(event, ${parentId})">
            <div class="form-group"><label>Subject</label><input type="text" name="subject" value="Message from Class Teacher"></div>
            <div class="form-group"><label>Message</label><textarea name="body" required rows="5"></textarea></div>
            <button type="submit" class="btn btn-primary" style="width:100%">Send Message</button>
        </form>
    `;
    openModal();
}

function sendMessage(e, parentId) {
    e.preventDefault();
    const f = new FormData(e.target);
    apiPost(API + '/message-parent', {
        parent_id: parentId,
        subject: f.get('subject'),
        body: f.get('body'),
    }).then(r => {
        alert(r.message || 'Sent');
        closeModal();
    });
}

/* Reports */
function loadAttendanceReport() {
    const output = document.getElementById('reportOutput');
    output.style.display = 'block';
    document.getElementById('reportTitle').textContent = 'Attendance Summary';
    apiGet(API + '/reports/attendance').then(data => {
        document.getElementById('reportContent').innerHTML = `
            <div class="data-table-wrapper">
                <table class="data-table">
                    <thead><tr><th>Student</th><th>Adm. No.</th><th>Days</th><th>Present</th><th>Absent</th><th>Rate</th></tr></thead>
                    <tbody>${data.map(r => `
                        <tr><td>${r.student_name}</td><td>${r.admission_number}</td><td>${r.total_days}</td><td>${r.present}</td><td>${r.absent}</td>
                        <td><div style="display:flex;align-items:center;gap:8px"><div class="progress-bar" style="width:80px"><div class="progress-fill ${r.rate >= 80 ? 'good' : r.rate >= 60 ? 'average' : 'poor'}" style="width:${r.rate}%"></div></div>${r.rate}%</div></td></tr>
                    `).join('')}</tbody>
                </table>
            </div>
        `;
    });
}

function loadPerformanceReport() {
    const output = document.getElementById('reportOutput');
    output.style.display = 'block';
    document.getElementById('reportTitle').textContent = 'Performance Report';
    apiGet(API + '/reports/performance').then(data => {
        document.getElementById('reportContent').innerHTML = `
            <div class="data-table-wrapper">
                <table class="data-table">
                    <thead><tr><th>Rank</th><th>Student</th><th>Adm. No.</th><th>Subjects</th><th>Average</th><th>Highest</th><th>Lowest</th></tr></thead>
                    <tbody>${data.map(r => `
                        <tr><td><strong>${r.rank}</strong></td><td>${r.student_name}</td><td>${r.admission_number}</td><td>${r.subjects_count}</td><td>${r.average}</td><td>${r.highest}</td><td>${r.lowest}</td></tr>
                    `).join('')}</tbody>
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
