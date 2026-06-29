/* Deputy Headteacher Portal */
const API = '/api/deputy';
const token = localStorage.getItem('token') || localStorage.getItem('access_token');
const headers = { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token };

function apiGet(url) { return fetch(url, { headers }).then(r => r.json()); }
function apiPost(url, data) { return fetch(url, { method: 'POST', headers, body: JSON.stringify(data) }).then(r => r.json()); }
function apiPut(url, data) { return fetch(url, { method: 'PUT', headers, body: JSON.stringify(data) }).then(r => r.json()); }
function apiDelete(url) { return fetch(url, { method: 'DELETE', headers }).then(r => r.json()); }

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
            const section = item.dataset.section;
            switchSection(section);
        });
    });
}

const sectionTitles = {
    dashboard: ['Operations Dashboard', 'School operational management center'],
    students: ['Student Management', 'Admissions, transfers and student records'],
    discipline: ['Discipline Management', 'Incident recording and case management'],
    staff: ['Staff Supervision', 'Teacher management and monitoring'],
    allocations: ['Class Teacher Allocation', 'Assign teachers to classes'],
    attendance: ['Teacher Attendance', 'Daily teacher attendance monitoring'],
    leaves: ['Leave Requests', 'Review and approve leave applications'],
    welfare: ['Student Welfare', 'Student wellbeing and welfare cases'],
    duties: ['Duty Roster', 'Teacher duty assignments and schedules'],
    reports: ['Reports & Analytics', 'Operational reports and analysis'],
};

function switchSection(section) {
    document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const el = document.getElementById('section-' + section);
    if (el) el.classList.add('active');
    const nav = document.querySelector(`.nav-item[data-section="${section}"]`);
    if (nav) nav.classList.add('active');
    const titles = sectionTitles[section] || ['', ''];
    document.getElementById('pageTitle').textContent = titles[0];
    document.getElementById('pageSubtitle').textContent = titles[1];

    const loaders = {
        dashboard: loadDashboard, students: loadStudents, discipline: loadDiscipline,
        staff: loadStaff, allocations: loadAllocations, attendance: loadTeacherAttendance,
        leaves: loadLeaves, welfare: loadWelfare, duties: loadDuties, reports: () => {},
    };
    if (loaders[section]) loaders[section]();
}

/* Dashboard */
function loadDashboard() {
    apiGet(API + '/dashboard').then(d => {
        document.getElementById('kpiStudents').textContent = d.total_students;
        document.getElementById('kpiTeachers').textContent = d.total_teachers;
        document.getElementById('kpiDiscipline').textContent = d.open_discipline;
        document.getElementById('kpiLeaves').textContent = d.pending_leaves;
        document.getElementById('summStudentAtt').textContent = d.student_attendance_rate + '%';
        document.getElementById('summTeacherAtt').textContent = d.teacher_attendance_rate + '%';
        document.getElementById('summWelfare').textContent = d.open_welfare;
        document.getElementById('summClasses').textContent = d.total_classes;

        renderDisciplineChart(d.discipline_by_category);
        renderEnrollmentChart(d.students_by_class);
        renderRecentDiscipline(d.recent_discipline);
        renderRecentLeaves(d.recent_leaves);
    });
}

let chartDiscipline, chartEnrollment;
function renderDisciplineChart(data) {
    if (chartDiscipline) chartDiscipline.destroy();
    const ctx = document.getElementById('chartDiscipline');
    if (!ctx) return;
    chartDiscipline = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.category),
            datasets: [{ data: data.map(d => d.count), backgroundColor: ['#3b82f6','#f59e0b','#ef4444','#10b981','#8b5cf6','#ec4899'] }]
        },
        options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
    });
}

function renderEnrollmentChart(data) {
    if (chartEnrollment) chartEnrollment.destroy();
    const ctx = document.getElementById('chartEnrollment');
    if (!ctx) return;
    chartEnrollment = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.class_name),
            datasets: [{ label: 'Students', data: data.map(d => d.count), backgroundColor: '#E63946', borderRadius: 6 }]
        },
        options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });
}

function renderRecentDiscipline(items) {
    const el = document.getElementById('recentDiscipline');
    el.innerHTML = items.length ? items.map(d => `
        <div class="activity-item">
            <span class="activity-text"><strong>${d.student_name}</strong> - ${d.category}</span>
            <span class="activity-meta"><span class="status-badge ${d.severity}">${d.severity}</span></span>
        </div>
    `).join('') : '<p class="text-muted text-center">No recent cases</p>';
}

function renderRecentLeaves(items) {
    const el = document.getElementById('recentLeaves');
    el.innerHTML = items.length ? items.map(l => `
        <div class="activity-item">
            <span class="activity-text"><strong>${l.teacher_name}</strong> - ${l.leave_type}</span>
            <span class="activity-meta"><span class="status-badge ${l.status}">${l.status}</span></span>
        </div>
    `).join('') : '<p class="text-muted text-center">No recent requests</p>';
}

/* Students */
function loadStudents() {
    apiGet('/api/students/?per_page=200').then(d => {
        const students = d.students || d;
        const body = document.getElementById('studentsBody');
        body.innerHTML = students.map(s => `
            <tr>
                <td>${s.full_name}</td>
                <td>${s.admission_number}</td>
                <td>${s.class_id || 'N/A'}</td>
                <td>${s.gender || 'N/A'}</td>
                <td><span class="status-badge ${s.status}">${s.status}</span></td>
                <td><button class="btn btn-sm btn-outline" onclick="viewStudentDiscipline(${s.id})">View</button></td>
            </tr>
        `).join('');
    });
}

/* Discipline */
function loadDiscipline() {
    const status = document.getElementById('disciplineFilter')?.value || '';
    apiGet(API + '/discipline' + (status ? '?status=' + status : '')).then(data => {
        document.getElementById('disciplineBody').innerHTML = data.map(d => `
            <tr>
                <td>${d.incident_date}</td>
                <td>${d.student_name}</td>
                <td>${d.category}</td>
                <td><span class="status-badge ${d.severity}">${d.severity}</span></td>
                <td><span class="status-badge ${d.status}">${d.status}</span></td>
                <td>
                    ${d.status === 'open' ? `<button class="btn btn-sm btn-success" onclick="resolveDiscipline(${d.id})">Resolve</button>` : ''}
                </td>
            </tr>
        `).join('') || '<tr><td colspan="6" class="text-center text-muted">No records found</td></tr>';
    });
}

function showDisciplineModal() {
    document.getElementById('modalTitle').textContent = 'Record Discipline Incident';
    apiGet('/api/students/?per_page=200').then(d => {
        const students = d.students || d;
        document.getElementById('modalBody').innerHTML = `
            <form id="disciplineForm" onsubmit="submitDiscipline(event)">
                <div class="form-group">
                    <label>Student</label>
                    <select name="student_id" required>${students.map(s => `<option value="${s.id}">${s.full_name} (${s.admission_number})</option>`).join('')}</select>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Category</label>
                        <select name="category" required>
                            <option>Misconduct</option><option>Truancy</option><option>Bullying</option>
                            <option>Fighting</option><option>Property Damage</option><option>Academic Dishonesty</option>
                            <option>Insubordination</option><option>Other</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Severity</label>
                        <select name="severity"><option value="minor">Minor</option><option value="major">Major</option><option value="critical">Critical</option></select>
                    </div>
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea name="description" required></textarea>
                </div>
                <div class="form-group">
                    <label>Action Taken</label>
                    <textarea name="action_taken"></textarea>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Suspension Days</label>
                        <input type="number" name="suspension_days" value="0" min="0">
                    </div>
                    <div class="form-group">
                        <label>Refer to Counseling</label>
                        <select name="counseling_referred"><option value="false">No</option><option value="true">Yes</option></select>
                    </div>
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%">Record Incident</button>
            </form>
        `;
        openModal();
    });
}

function submitDiscipline(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    apiPost(API + '/discipline', {
        student_id: parseInt(f.get('student_id')),
        category: f.get('category'),
        severity: f.get('severity'),
        description: f.get('description'),
        action_taken: f.get('action_taken'),
        suspension_days: parseInt(f.get('suspension_days')),
        counseling_referred: f.get('counseling_referred') === 'true',
    }).then(() => { closeModal(); loadDiscipline(); });
}

function resolveDiscipline(id) {
    const notes = prompt('Resolution notes:');
    if (notes !== null) {
        apiPut(API + '/discipline/' + id, { status: 'resolved', resolution_notes: notes }).then(() => loadDiscipline());
    }
}

/* Staff */
function loadStaff() {
    apiGet('/api/teachers/').then(data => {
        const teachers = data.teachers || data;
        document.getElementById('staffGrid').innerHTML = teachers.map(t => `
            <div class="info-card">
                <h4>${t.full_name}</h4>
                <p>${t.employee_id} - ${t.department || 'N/A'}</p>
                <p>Role: ${t.teacher_role_display}</p>
                <p>Status: <span class="status-badge ${t.status}">${t.status}</span></p>
            </div>
        `).join('');
    });
}

/* Allocations */
function loadAllocations() {
    apiGet(API + '/allocations').then(data => {
        document.getElementById('allocationsBody').innerHTML = data.map(a => `
            <tr>
                <td>${a.teacher_name}</td>
                <td>${a.class_name}</td>
                <td>${a.stream_name || 'All'}</td>
                <td>${a.academic_year}</td>
                <td><span class="status-badge ${a.is_active ? 'active' : 'resolved'}">${a.is_active ? 'Active' : 'Inactive'}</span></td>
                <td>${a.is_active ? `<button class="btn btn-sm btn-danger" onclick="removeAllocation(${a.id})">Remove</button>` : ''}</td>
            </tr>
        `).join('') || '<tr><td colspan="6" class="text-center text-muted">No allocations found</td></tr>';
    });
}

function showAllocationModal() {
    document.getElementById('modalTitle').textContent = 'New Class Teacher Allocation';
    Promise.all([
        apiGet('/api/teachers/'),
        apiGet('/api/academics/classes')
    ]).then(([tData, cData]) => {
        const teachers = tData.teachers || tData;
        const classes = cData.classes || cData || [];
        document.getElementById('modalBody').innerHTML = `
            <form id="allocationForm" onsubmit="submitAllocation(event)">
                <div class="form-group">
                    <label>Teacher</label>
                    <select name="teacher_id" required>${teachers.map(t => `<option value="${t.id}">${t.full_name} (${t.employee_id})</option>`).join('')}</select>
                </div>
                <div class="form-group">
                    <label>Class</label>
                    <select name="class_id" required>${classes.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}</select>
                </div>
                <div class="form-group">
                    <label>Academic Year</label>
                    <input type="text" name="academic_year" value="${new Date().getFullYear()}" required>
                </div>
                <div class="form-group">
                    <label>Notes</label>
                    <textarea name="notes"></textarea>
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%">Allocate</button>
            </form>
        `;
        openModal();
    });
}

function submitAllocation(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    apiPost(API + '/allocations', {
        teacher_id: parseInt(f.get('teacher_id')),
        class_id: parseInt(f.get('class_id')),
        academic_year: f.get('academic_year'),
        notes: f.get('notes'),
    }).then(res => {
        if (res.error) { alert(res.error); return; }
        closeModal(); loadAllocations();
    });
}

function removeAllocation(id) {
    if (confirm('Remove this allocation?')) {
        apiDelete(API + '/allocations/' + id).then(() => loadAllocations());
    }
}

/* Teacher Attendance */
function loadTeacherAttendance() {
    const d = document.getElementById('attDate')?.value || new Date().toISOString().split('T')[0];
    apiGet(API + '/teacher-attendance?date=' + d).then(data => {
        document.getElementById('teacherAttBody').innerHTML = data.map(a => `
            <tr>
                <td>${a.teacher_name}</td>
                <td>${a.employee_id}</td>
                <td><span class="status-badge ${a.status === 'present' ? 'active' : 'pending'}">${a.status}</span></td>
                <td>${a.remarks || '-'}</td>
            </tr>
        `).join('') || '<tr><td colspan="4" class="text-center text-muted">No records for this date</td></tr>';
    });
}

function showAttendanceModal() {
    document.getElementById('modalTitle').textContent = 'Mark Teacher Attendance';
    apiGet('/api/teachers/').then(data => {
        const teachers = data.teachers || data;
        document.getElementById('modalBody').innerHTML = `
            <form id="attForm" onsubmit="submitTeacherAtt(event)">
                <div class="form-group">
                    <label>Teacher</label>
                    <select name="teacher_id" required>${teachers.map(t => `<option value="${t.id}">${t.full_name}</option>`).join('')}</select>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Status</label>
                        <select name="status"><option value="present">Present</option><option value="absent">Absent</option><option value="late">Late</option></select>
                    </div>
                    <div class="form-group">
                        <label>Date</label>
                        <input type="date" name="date" value="${new Date().toISOString().split('T')[0]}">
                    </div>
                </div>
                <div class="form-group"><label>Remarks</label><textarea name="remarks"></textarea></div>
                <button type="submit" class="btn btn-primary" style="width:100%">Save</button>
            </form>
        `;
        openModal();
    });
}

function submitTeacherAtt(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    apiPost(API + '/teacher-attendance', {
        teacher_id: parseInt(f.get('teacher_id')),
        status: f.get('status'),
        date: f.get('date'),
        remarks: f.get('remarks'),
    }).then(() => { closeModal(); loadTeacherAttendance(); });
}

/* Leaves */
function loadLeaves() {
    apiGet(API + '/leaves').then(data => {
        document.getElementById('leavesBody').innerHTML = data.map(l => `
            <tr>
                <td>${l.teacher_name}</td>
                <td>${l.leave_type}</td>
                <td>${l.start_date}</td>
                <td>${l.end_date}</td>
                <td><span class="status-badge ${l.status}">${l.status}</span></td>
                <td>
                    ${l.status === 'pending' ? `
                        <button class="btn btn-sm btn-success" onclick="approveLeave(${l.id})">Approve</button>
                        <button class="btn btn-sm btn-danger" onclick="rejectLeave(${l.id})">Reject</button>
                    ` : ''}
                </td>
            </tr>
        `).join('') || '<tr><td colspan="6" class="text-center text-muted">No leave requests</td></tr>';
    });
}

function approveLeave(id) { apiPost(API + '/leaves/' + id + '/approve', {}).then(() => loadLeaves()); }
function rejectLeave(id) {
    const reason = prompt('Rejection reason:');
    if (reason !== null) apiPost(API + '/leaves/' + id + '/reject', { reason }).then(() => loadLeaves());
}

/* Welfare */
function loadWelfare() {
    apiGet(API + '/welfare').then(data => {
        document.getElementById('welfareBody').innerHTML = data.map(w => `
            <tr>
                <td>${w.student_name}</td>
                <td>${w.category}</td>
                <td><span class="status-badge ${w.priority}">${w.priority}</span></td>
                <td><span class="status-badge ${w.status}">${w.status}</span></td>
                <td><button class="btn btn-sm btn-outline" onclick="updateWelfare(${w.id})">Update</button></td>
            </tr>
        `).join('') || '<tr><td colspan="5" class="text-center text-muted">No welfare records</td></tr>';
    });
}

function showWelfareModal() {
    document.getElementById('modalTitle').textContent = 'New Welfare Record';
    apiGet('/api/students/?per_page=200').then(d => {
        const students = d.students || d;
        document.getElementById('modalBody').innerHTML = `
            <form id="welfareForm" onsubmit="submitWelfare(event)">
                <div class="form-group">
                    <label>Student</label>
                    <select name="student_id" required>${students.map(s => `<option value="${s.id}">${s.full_name}</option>`).join('')}</select>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Category</label>
                        <select name="category"><option>Health</option><option>Family</option><option>Financial</option><option>Academic</option><option>Social</option><option>Other</option></select>
                    </div>
                    <div class="form-group">
                        <label>Priority</label>
                        <select name="priority"><option value="low">Low</option><option value="medium" selected>Medium</option><option value="high">High</option></select>
                    </div>
                </div>
                <div class="form-group"><label>Description</label><textarea name="description" required></textarea></div>
                <div class="form-group"><label>Action Taken</label><textarea name="action_taken"></textarea></div>
                <button type="submit" class="btn btn-primary" style="width:100%">Save Record</button>
            </form>
        `;
        openModal();
    });
}

function submitWelfare(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    apiPost(API + '/welfare', {
        student_id: parseInt(f.get('student_id')),
        category: f.get('category'),
        priority: f.get('priority'),
        description: f.get('description'),
        action_taken: f.get('action_taken'),
    }).then(() => { closeModal(); loadWelfare(); });
}

function updateWelfare(id) {
    const status = prompt('New status (open/resolved):');
    if (status) apiPut(API + '/welfare/' + id, { status }).then(() => loadWelfare());
}

/* Duties */
function loadDuties() {
    apiGet(API + '/duties').then(data => {
        document.getElementById('dutiesBody').innerHTML = data.map(d => `
            <tr>
                <td>${d.teacher_name}</td>
                <td>${d.duty_type}</td>
                <td>${d.duty_date || '-'}</td>
                <td>${d.start_time || '-'} - ${d.end_time || '-'}</td>
                <td>${d.location || '-'}</td>
                <td><span class="status-badge ${d.status}">${d.status}</span></td>
            </tr>
        `).join('') || '<tr><td colspan="6" class="text-center text-muted">No duties assigned</td></tr>';
    });
}

function showDutyModal() {
    document.getElementById('modalTitle').textContent = 'Assign Duty';
    apiGet('/api/teachers/').then(data => {
        const teachers = data.teachers || data;
        document.getElementById('modalBody').innerHTML = `
            <form id="dutyForm" onsubmit="submitDuty(event)">
                <div class="form-group">
                    <label>Teacher</label>
                    <select name="teacher_id" required>${teachers.map(t => `<option value="${t.id}">${t.full_name}</option>`).join('')}</select>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Duty Type</label>
                        <select name="duty_type"><option>Morning Assembly</option><option>Gate Duty</option><option>Dining Hall</option><option>Dormitory</option><option>Games</option><option>Supervision</option></select>
                    </div>
                    <div class="form-group"><label>Date</label><input type="date" name="duty_date" required></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Start Time</label><input type="time" name="start_time"></div>
                    <div class="form-group"><label>End Time</label><input type="time" name="end_time"></div>
                </div>
                <div class="form-group"><label>Location</label><input type="text" name="location"></div>
                <button type="submit" class="btn btn-primary" style="width:100%">Assign</button>
            </form>
        `;
        openModal();
    });
}

function submitDuty(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    apiPost(API + '/duties', {
        teacher_id: parseInt(f.get('teacher_id')),
        duty_type: f.get('duty_type'),
        duty_date: f.get('duty_date'),
        start_time: f.get('start_time'),
        end_time: f.get('end_time'),
        location: f.get('location'),
    }).then(() => { closeModal(); loadDuties(); });
}

/* Reports */
function loadReport(type) {
    const output = document.getElementById('reportOutput');
    const title = document.getElementById('reportTitle');
    const content = document.getElementById('reportContent');
    output.style.display = 'block';

    if (type === 'discipline') {
        title.textContent = 'Discipline Report';
        apiGet(API + '/reports/discipline').then(d => {
            content.innerHTML = `
                <div class="summary-grid">
                    <div class="summary-card"><div class="summary-label">Total Cases</div><div class="summary-value">${d.total}</div></div>
                    <div class="summary-card"><div class="summary-label">Open</div><div class="summary-value">${d.open}</div></div>
                    <div class="summary-card"><div class="summary-label">Resolved</div><div class="summary-value">${d.resolved}</div></div>
                    <div class="summary-card"><div class="summary-label">Suspension Days</div><div class="summary-value">${d.total_suspension_days}</div></div>
                </div>
                <div class="data-table-wrapper" style="margin-top:16px">
                    <table class="data-table">
                        <thead><tr><th>Category</th><th>Count</th></tr></thead>
                        <tbody>${d.by_category.map(c => `<tr><td>${c.category}</td><td>${c.count}</td></tr>`).join('')}</tbody>
                    </table>
                </div>
            `;
        });
    } else if (type === 'attendance') {
        title.textContent = 'Attendance Report';
        apiGet(API + '/reports/attendance?period=today').then(d => {
            content.innerHTML = `
                <div class="summary-grid">
                    <div class="summary-card"><div class="summary-label">Student Attendance</div><div class="summary-value">${d.student_rate}%</div></div>
                    <div class="summary-card"><div class="summary-label">Students Present</div><div class="summary-value">${d.student_present}/${d.student_total}</div></div>
                    <div class="summary-card"><div class="summary-label">Teacher Attendance</div><div class="summary-value">${d.teacher_rate}%</div></div>
                    <div class="summary-card"><div class="summary-label">Teachers Present</div><div class="summary-value">${d.teacher_present}/${d.teacher_total}</div></div>
                </div>
            `;
        });
    }
}

/* Modal Helpers */
function openModal() { document.getElementById('modalOverlay').classList.add('active'); }
function closeModal() { document.getElementById('modalOverlay').classList.remove('active'); }
document.getElementById('modalOverlay')?.addEventListener('click', e => {
    if (e.target === e.currentTarget) closeModal();
});
