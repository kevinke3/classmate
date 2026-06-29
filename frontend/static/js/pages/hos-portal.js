/* Head of Studies Portal */
const API = '/api/hos';
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
    dashboard: ['Academic Dashboard', 'Academic management and performance monitoring'],
    examinations: ['Examinations', 'Exam scheduling and management'],
    results: ['Results & Rankings', 'Exam results and merit lists'],
    targets: ['Academic Targets', 'Performance targets and goals'],
    interventions: ['Interventions', 'Student academic interventions'],
    curriculum: ['Curriculum', 'Curriculum progress and monitoring'],
    reports: ['Reports & Analytics', 'Academic analysis and reports'],
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
        dashboard: loadDashboard, examinations: loadExams, results: loadResultsSection,
        targets: loadTargets, interventions: loadInterventions,
        curriculum: loadCurriculum, reports: () => {},
    };
    if (loaders[section]) loaders[section]();
}

/* Dashboard */
let chartClassPerf, chartGrades, chartSubjects;
function loadDashboard() {
    apiGet(API + '/dashboard').then(d => {
        document.getElementById('kpiStudents').textContent = d.total_students;
        document.getElementById('kpiMean').textContent = d.overall_mean;
        document.getElementById('kpiPassRate').textContent = d.pass_rate + '%';
        document.getElementById('kpiInterventions').textContent = d.active_interventions;
        document.getElementById('summExams').textContent = d.total_exams;
        document.getElementById('summSubjects').textContent = d.total_subjects;
        document.getElementById('summCoverage').textContent = d.avg_syllabus_coverage + '%';

        if (chartClassPerf) chartClassPerf.destroy();
        const ctx1 = document.getElementById('chartClassPerformance');
        if (ctx1 && d.class_performance.length) {
            chartClassPerf = new Chart(ctx1, {
                type: 'bar',
                data: {
                    labels: d.class_performance.map(c => c.class_name),
                    datasets: [{ label: 'Mean Score', data: d.class_performance.map(c => c.mean_score), backgroundColor: '#E63946', borderRadius: 6 }]
                },
                options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, max: 100 } } }
            });
        }

        if (chartGrades) chartGrades.destroy();
        const ctx2 = document.getElementById('chartGrades');
        if (ctx2 && d.grade_distribution.length) {
            chartGrades = new Chart(ctx2, {
                type: 'doughnut',
                data: {
                    labels: d.grade_distribution.map(g => 'Grade ' + g.grade),
                    datasets: [{ data: d.grade_distribution.map(g => g.count), backgroundColor: ['#10b981','#3b82f6','#f59e0b','#ef4444','#6b7280'] }]
                },
                options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
            });
        }

        if (chartSubjects) chartSubjects.destroy();
        const ctx3 = document.getElementById('chartSubjects');
        if (ctx3 && d.subject_performance.length) {
            chartSubjects = new Chart(ctx3, {
                type: 'bar',
                data: {
                    labels: d.subject_performance.map(s => s.subject_name),
                    datasets: [{ label: 'Mean Score', data: d.subject_performance.map(s => s.mean_score), backgroundColor: '#3b82f6', borderRadius: 6 }]
                },
                options: { responsive: true, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, max: 100 } } }
            });
        }
    });
}

/* Examinations */
function loadExams() {
    apiGet(API + '/examinations').then(data => {
        document.getElementById('examsBody').innerHTML = data.map(e => `
            <tr>
                <td>${e.name}</td>
                <td>${e.exam_type}</td>
                <td>${e.term || 'N/A'}</td>
                <td>${e.start_date || 'N/A'}</td>
                <td>${e.end_date || 'N/A'}</td>
                <td><span class="status-badge ${e.status}">${e.status}</span></td>
                <td><button class="btn btn-sm btn-outline" onclick="viewExamResults(${e.id})">Results</button></td>
            </tr>
        `).join('') || '<tr><td colspan="7" class="text-center text-muted">No examinations</td></tr>';

        const filter = document.getElementById('resultExamFilter');
        if (filter) {
            filter.innerHTML = '<option value="">Select Examination</option>' +
                data.map(e => `<option value="${e.id}">${e.name}</option>`).join('');
        }
    });
}

function showExamModal() {
    document.getElementById('modalTitle').textContent = 'Schedule Examination';
    document.getElementById('modalBody').innerHTML = `
        <form id="examForm" onsubmit="submitExam(event)">
            <div class="form-group"><label>Name</label><input type="text" name="name" required></div>
            <div class="form-row">
                <div class="form-group">
                    <label>Type</label>
                    <select name="exam_type"><option>Mid-Term</option><option>End-Term</option><option>Mock</option><option>CAT</option></select>
                </div>
                <div class="form-group">
                    <label>Term</label>
                    <select name="term"><option>Term 1</option><option>Term 2</option><option>Term 3</option></select>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group"><label>Start Date</label><input type="date" name="start_date" required></div>
                <div class="form-group"><label>End Date</label><input type="date" name="end_date" required></div>
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%">Schedule</button>
        </form>
    `;
    openModal();
}

function submitExam(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    apiPost(API + '/examinations', {
        name: f.get('name'), exam_type: f.get('exam_type'),
        term: f.get('term'), start_date: f.get('start_date'), end_date: f.get('end_date'),
    }).then(() => { closeModal(); loadExams(); });
}

/* Results */
function loadResultsSection() { loadExams(); }

function loadExamResults() {
    const eid = document.getElementById('resultExamFilter')?.value;
    if (!eid) return;
    viewExamResults(eid);
}

function viewExamResults(eid) {
    apiGet(API + '/examinations/' + eid + '/results').then(d => {
        const content = document.getElementById('resultsContent');
        if (!d.results || !d.results.length) {
            content.innerHTML = '<p class="text-muted text-center" style="padding:40px">No results for this examination</p>';
            return;
        }
        content.innerHTML = `
            <div class="summary-grid" style="margin-bottom:20px">
                <div class="summary-card"><div class="summary-label">Exam</div><div class="summary-value">${d.exam.name}</div></div>
                <div class="summary-card"><div class="summary-label">Students</div><div class="summary-value">${d.total_students}</div></div>
            </div>
            <div class="data-table-wrapper">
                <table class="data-table">
                    <thead><tr><th>Rank</th><th>Student</th><th>Adm. No.</th><th>Total</th><th>Mean</th><th>Subjects</th></tr></thead>
                    <tbody>${d.results.map(r => `
                        <tr>
                            <td><strong>${r.rank}</strong></td>
                            <td>${r.student_name}</td>
                            <td>${r.admission_number}</td>
                            <td>${r.total}</td>
                            <td>${r.mean}</td>
                            <td>${r.subjects.map(s => s.subject + ': ' + s.marks).join(', ')}</td>
                        </tr>
                    `).join('')}</tbody>
                </table>
            </div>
        `;
    });
}

/* Targets */
function loadTargets() {
    apiGet(API + '/targets').then(data => {
        document.getElementById('targetsBody').innerHTML = data.map(t => `
            <tr>
                <td>${t.class_name}</td>
                <td>${t.subject_name}</td>
                <td>${t.target_mean || '-'}</td>
                <td>${t.actual_mean || '-'}</td>
                <td>${t.target_pass_rate ? t.target_pass_rate + '%' : '-'}</td>
                <td>${t.actual_pass_rate ? t.actual_pass_rate + '%' : '-'}</td>
            </tr>
        `).join('') || '<tr><td colspan="6" class="text-center text-muted">No targets set</td></tr>';
    });
}

function showTargetModal() {
    document.getElementById('modalTitle').textContent = 'Set Academic Target';
    Promise.all([
        apiGet('/api/academics/classes'),
        apiGet('/api/academics/subjects')
    ]).then(([cData, sData]) => {
        const classes = cData.classes || cData || [];
        const subjects = sData.subjects || sData || [];
        document.getElementById('modalBody').innerHTML = `
            <form id="targetForm" onsubmit="submitTarget(event)">
                <div class="form-row">
                    <div class="form-group">
                        <label>Class</label>
                        <select name="class_id"><option value="">All Classes</option>${classes.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}</select>
                    </div>
                    <div class="form-group">
                        <label>Subject</label>
                        <select name="subject_id"><option value="">Overall</option>${subjects.map(s => `<option value="${s.id}">${s.name}</option>`).join('')}</select>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Target Mean</label><input type="number" name="target_mean" step="0.1" min="0" max="100"></div>
                    <div class="form-group"><label>Target Pass Rate (%)</label><input type="number" name="target_pass_rate" step="0.1" min="0" max="100"></div>
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%">Set Target</button>
            </form>
        `;
        openModal();
    });
}

function submitTarget(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    apiPost(API + '/targets', {
        class_id: f.get('class_id') ? parseInt(f.get('class_id')) : null,
        subject_id: f.get('subject_id') ? parseInt(f.get('subject_id')) : null,
        target_mean: parseFloat(f.get('target_mean')) || null,
        target_pass_rate: parseFloat(f.get('target_pass_rate')) || null,
    }).then(() => { closeModal(); loadTargets(); });
}

/* Interventions */
function loadInterventions() {
    apiGet(API + '/interventions').then(data => {
        document.getElementById('interventionsBody').innerHTML = data.map(i => `
            <tr>
                <td>${i.student_name}</td>
                <td>${i.subject_name || 'General'}</td>
                <td>${i.intervention_type}</td>
                <td>${i.current_score || '-'}</td>
                <td>${i.target_score || '-'}</td>
                <td><span class="status-badge ${i.status}">${i.status}</span></td>
            </tr>
        `).join('') || '<tr><td colspan="6" class="text-center text-muted">No interventions</td></tr>';
    });
}

function showInterventionModal() {
    document.getElementById('modalTitle').textContent = 'Add Intervention';
    apiGet('/api/students/?per_page=200').then(d => {
        const students = d.students || d;
        document.getElementById('modalBody').innerHTML = `
            <form id="intForm" onsubmit="submitIntervention(event)">
                <div class="form-group">
                    <label>Student</label>
                    <select name="student_id" required>${students.map(s => `<option value="${s.id}">${s.full_name} (${s.admission_number})</option>`).join('')}</select>
                </div>
                <div class="form-group">
                    <label>Type</label>
                    <select name="intervention_type"><option>Remedial Classes</option><option>Mentoring</option><option>Extra Tutorials</option><option>Parent Conference</option><option>Special Assessment</option></select>
                </div>
                <div class="form-group"><label>Description</label><textarea name="description" required></textarea></div>
                <div class="form-row">
                    <div class="form-group"><label>Current Score</label><input type="number" name="current_score" step="0.1"></div>
                    <div class="form-group"><label>Target Score</label><input type="number" name="target_score" step="0.1"></div>
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%">Add</button>
            </form>
        `;
        openModal();
    });
}

function submitIntervention(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    apiPost(API + '/interventions', {
        student_id: parseInt(f.get('student_id')),
        intervention_type: f.get('intervention_type'),
        description: f.get('description'),
        current_score: parseFloat(f.get('current_score')) || null,
        target_score: parseFloat(f.get('target_score')) || null,
    }).then(() => { closeModal(); loadInterventions(); });
}

/* Curriculum */
function loadCurriculum() {
    apiGet('/api/senior-teacher/syllabus').then(data => {
        const grid = document.getElementById('curriculumGrid');
        grid.innerHTML = data.map(s => {
            const pct = s.percentage || 0;
            const cls = pct >= 70 ? 'good' : pct >= 40 ? 'average' : 'poor';
            return `
                <div class="info-card">
                    <h4>${s.subject_name} - ${s.class_name}</h4>
                    <p>${s.teacher_name}</p>
                    <div style="margin-top:12px">
                        <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">
                            <span>Coverage</span><span>${pct}%</span>
                        </div>
                        <div class="progress-bar"><div class="progress-fill ${cls}" style="width:${pct}%"></div></div>
                        <p style="font-size:12px;margin-top:4px">${s.covered_topics}/${s.total_topics} topics</p>
                    </div>
                </div>
            `;
        }).join('') || '<p class="text-muted text-center">No curriculum data</p>';
    });
}

/* Reports */
function loadClassReport() {
    const output = document.getElementById('reportOutput');
    output.style.display = 'block';
    document.getElementById('reportTitle').textContent = 'Class Performance Report';
    apiGet(API + '/reports/class-performance').then(data => {
        document.getElementById('reportContent').innerHTML = `
            <div class="data-table-wrapper">
                <table class="data-table">
                    <thead><tr><th>Class</th><th>Students</th><th>Mean</th><th>Pass Rate</th><th>Highest</th><th>Lowest</th></tr></thead>
                    <tbody>${data.map(c => `
                        <tr><td>${c.class_name}</td><td>${c.student_count}</td><td>${c.mean_score}</td><td>${c.pass_rate}%</td><td>${c.highest}</td><td>${c.lowest}</td></tr>
                    `).join('')}</tbody>
                </table>
            </div>
        `;
    });
}

function loadSubjectReport() {
    const output = document.getElementById('reportOutput');
    output.style.display = 'block';
    document.getElementById('reportTitle').textContent = 'Subject Analysis Report';
    apiGet(API + '/reports/subject-analysis').then(data => {
        document.getElementById('reportContent').innerHTML = `
            <div class="data-table-wrapper">
                <table class="data-table">
                    <thead><tr><th>Subject</th><th>Students</th><th>Mean</th><th>Pass Rate</th><th>Highest</th><th>Lowest</th></tr></thead>
                    <tbody>${data.map(s => `
                        <tr><td>${s.subject_name}</td><td>${s.total_students}</td><td>${s.mean_score}</td><td>${s.pass_rate}%</td><td>${s.highest}</td><td>${s.lowest}</td></tr>
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
