document.addEventListener('DOMContentLoaded', () => {
    if (!auth.requireAuth()) return;

    const cardViewBtn = document.getElementById('cardViewBtn');
    const tableViewBtn = document.getElementById('tableViewBtn');
    const studentCards = document.getElementById('studentCards');
    const studentTable = document.getElementById('studentTable');
    const searchInput = document.getElementById('searchInput');
    const addStudentBtn = document.getElementById('addStudentBtn');
    const studentCount = document.getElementById('studentCount');

    if (studentCount) {
        studentCount.textContent = document.querySelectorAll('.student-card').length;
    }

    if (cardViewBtn) {
        cardViewBtn.addEventListener('click', () => {
            cardViewBtn.classList.add('active');
            tableViewBtn.classList.remove('active');
            studentCards.style.display = 'grid';
            studentTable.style.display = 'none';
        });
    }

    if (tableViewBtn) {
        tableViewBtn.addEventListener('click', () => {
            tableViewBtn.classList.add('active');
            cardViewBtn.classList.remove('active');
            studentCards.style.display = 'none';
            studentTable.style.display = 'block';
            loadStudentTable();
        });
    }

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const cards = document.querySelectorAll('.student-card');
            cards.forEach(card => {
                const name = card.querySelector('.student-card-name').textContent.toLowerCase();
                const id = card.querySelector('.student-card-id').textContent.toLowerCase();
                card.style.display = (name.includes(query) || id.includes(query)) ? '' : 'none';
            });
        });
    }

    if (addStudentBtn) {
        addStudentBtn.addEventListener('click', () => {
            showAddStudentModal();
        });
    }

    loadStudents();
});

async function loadStudents() {
    try {
        const response = await api.get('/students/?per_page=50');
        if (response && response.students && response.students.length > 0) {
            renderStudentCards(response.students);
        }
    } catch (error) {
        // Use sample data
    }
}

function renderStudentCards(students) {
    const container = document.getElementById('studentCards');
    if (!container || students.length === 0) return;

    container.innerHTML = students.map((student, i) => `
        <div class="student-card animate-fade-in" style="animation-delay: ${i * 0.05}s">
            <div class="student-card-header">
                <div class="student-card-avatar">${getInitials(student.full_name)}</div>
                <div>
                    <div class="student-card-name">${student.full_name}</div>
                    <div class="student-card-id">${student.admission_number}</div>
                </div>
            </div>
            <div class="student-card-details">
                <div class="student-detail">
                    <span class="student-detail-label">Class</span>
                    <span class="student-detail-value">${student.class_name || 'N/A'}</span>
                </div>
                <div class="student-detail">
                    <span class="student-detail-label">Status</span>
                    <span class="badge badge-${student.status === 'active' ? 'success' : 'warning'}">${student.status}</span>
                </div>
            </div>
        </div>
    `).join('');

    document.getElementById('studentCount').textContent = students.length;
}

function loadStudentTable() {
    const tbody = document.getElementById('studentTableBody');
    if (!tbody) return;

    const cards = document.querySelectorAll('.student-card');
    tbody.innerHTML = '';

    cards.forEach(card => {
        const name = card.querySelector('.student-card-name').textContent;
        const id = card.querySelector('.student-card-id').textContent;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><div class="user-cell"><div class="user-cell-avatar">${getInitials(name)}</div><div class="user-cell-info"><span class="user-cell-name">${name}</span></div></div></td>
            <td>${id}</td>
            <td>-</td>
            <td>-</td>
            <td><span class="badge badge-success">Active</span></td>
            <td><button class="btn btn-ghost btn-sm">View</button></td>
        `;
        tbody.appendChild(row);
    });
}

function showAddStudentModal() {
    const overlay = document.getElementById('modalOverlay');
    overlay.classList.add('active');
    overlay.innerHTML = `
        <div class="modal animate-scale-in">
            <div class="modal-header">
                <h3 class="modal-title">Add New Student</h3>
                <button class="modal-close" onclick="closeModal()"><i class="lucide-x"></i></button>
            </div>
            <div class="modal-body">
                <form id="addStudentForm">
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">First Name</label>
                            <input type="text" id="studentFirstName" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Last Name</label>
                            <input type="text" id="studentLastName" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">Admission Number</label>
                            <input type="text" id="studentAdmNo" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Class</label>
                            <select id="studentClass">
                                <option value="">Select class</option>
                                <option value="1">Form 1</option>
                                <option value="2">Form 2</option>
                                <option value="3">Form 3</option>
                                <option value="4">Form 4</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Guardian Name</label>
                        <input type="text" id="guardianName">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Guardian Phone</label>
                        <input type="tel" id="guardianPhone">
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline" onclick="closeModal()">Cancel</button>
                <button class="btn btn-primary" onclick="submitStudent()">Add Student</button>
            </div>
        </div>
    `;
}

function closeModal() {
    const overlay = document.getElementById('modalOverlay');
    overlay.classList.remove('active');
    overlay.innerHTML = '';
}

async function submitStudent() {
    const data = {
        first_name: document.getElementById('studentFirstName').value,
        last_name: document.getElementById('studentLastName').value,
        admission_number: document.getElementById('studentAdmNo').value,
        class_id: document.getElementById('studentClass').value || null,
        guardian_name: document.getElementById('guardianName').value,
        guardian_phone: document.getElementById('guardianPhone').value
    };

    try {
        const response = await api.post('/students/', data);
        if (response.student) {
            closeModal();
            loadStudents();
        }
    } catch (error) {
        console.error('Error adding student:', error);
    }
}

function getInitials(name) {
    if (!name) return '?';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}
