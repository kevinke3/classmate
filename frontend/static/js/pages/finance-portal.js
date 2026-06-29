/**
 * Finance Portal - Comprehensive Financial Management System
 */

const API_BASE = '/api/finance';
let token = localStorage.getItem('token');
let currentSection = 'dashboard';
let charts = {};
let studentsCache = [];

// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    if (!token) {
        window.location.href = '/login';
        return;
    }
    initNavigation();
    initModals();
    initEventListeners();
    loadDashboard();
});

function initNavigation() {
    document.querySelectorAll('.nav-item[data-section]').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.dataset.section;
            switchSection(section);
        });
    });

    // Sidebar toggle
    const toggle = document.getElementById('sidebarToggle');
    if (toggle) {
        toggle.addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('collapsed');
        });
    }

    // Logout
    document.getElementById('logoutBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.removeItem('token');
        window.location.href = '/login';
    });
}

function switchSection(section) {
    currentSection = section;
    document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const sectionEl = document.getElementById(`section-${section}`);
    if (sectionEl) sectionEl.classList.add('active');

    const navItem = document.querySelector(`.nav-item[data-section="${section}"]`);
    if (navItem) navItem.classList.add('active');

    // Update header
    const titles = {
        'dashboard': ['Financial Dashboard', 'Real-time financial overview and insights'],
        'fee-structures': ['Fee Structures', 'Manage fee structures by academic year, term, class, and category'],
        'students': ['Student Financial Accounts', 'Search and manage student financial profiles'],
        'payments': ['Payments', 'All fee payments and transactions'],
        'invoices': ['Invoices', 'Manage and track all student invoices'],
        'receipts': ['Receipts', 'All generated payment receipts'],
        'expenses': ['Expenses', 'Track school expenditure and outflows'],
        'reports': ['Reports & Analytics', 'Generate financial reports and analytics'],
        'notifications': ['Notifications', 'Communication history and fee reminders'],
        'settings': ['Finance Settings', 'Configure financial management preferences']
    };

    const [title, subtitle] = titles[section] || ['Finance Portal', ''];
    document.getElementById('pageTitle').textContent = title;
    document.getElementById('pageSubtitle').textContent = subtitle;

    // Load section data
    const loaders = {
        'dashboard': loadDashboard,
        'fee-structures': loadFeeStructures,
        'students': loadStudentAccounts,
        'payments': loadPayments,
        'invoices': loadInvoices,
        'receipts': loadReceipts,
        'expenses': loadExpenses,
        'notifications': loadNotifications,
        'settings': loadSettings
    };
    if (loaders[section]) loaders[section]();
}

function initModals() {
    const overlay = document.getElementById('modalOverlay');
    const close = document.getElementById('modalClose');
    if (close) close.addEventListener('click', closeModal);
    if (overlay) overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeModal();
    });
}

function openModal(title, bodyHTML) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = bodyHTML;
    document.getElementById('modalOverlay').classList.add('active');
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('active');
}

function initEventListeners() {
    // Quick actions
    document.getElementById('btnQuickPayment')?.addEventListener('click', showPaymentModal);
    document.getElementById('btnRecordPayment')?.addEventListener('click', showPaymentModal);
    document.getElementById('btnCreateInvoice')?.addEventListener('click', showInvoiceModal);
    document.getElementById('btnNewInvoice')?.addEventListener('click', showInvoiceModal);
    document.getElementById('btnBulkInvoice')?.addEventListener('click', showBulkInvoiceModal);
    document.getElementById('btnNewFeeStructure')?.addEventListener('click', showFeeStructureModal);
    document.getElementById('btnRecordExpense')?.addEventListener('click', showExpenseModal);
    document.getElementById('btnSendReminder')?.addEventListener('click', showReminderModal);
    document.getElementById('btnAddCategory')?.addEventListener('click', showCategoryModal);
    document.getElementById('btnAddBankAccount')?.addEventListener('click', showBankAccountModal);

    // Student search
    let searchTimeout;
    document.getElementById('studentSearch')?.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => filterStudents(e.target.value), 300);
    });

    // Filters
    document.getElementById('filterPaymentMethod')?.addEventListener('change', loadPayments);
    document.getElementById('filterInvoiceStatus')?.addEventListener('change', loadInvoices);

    // Settings form
    document.getElementById('financeSettingsForm')?.addEventListener('submit', saveFinanceSettings);

    // Report cards
    document.querySelectorAll('.report-card').forEach(card => {
        card.addEventListener('click', () => loadReport(card.dataset.report));
    });
}

// ============================================================
// API HELPERS
// ============================================================

async function apiGet(path) {
    const res = await fetch(`${API_BASE}${path}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.status === 401) { window.location.href = '/login'; return null; }
    return res.json();
}

async function apiPost(path, data) {
    const res = await fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (res.status === 401) { window.location.href = '/login'; return null; }
    return res.json();
}

async function apiPut(path, data) {
    const res = await fetch(`${API_BASE}${path}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (res.status === 401) { window.location.href = '/login'; return null; }
    return res.json();
}

function formatCurrency(amount) {
    return `KES ${Number(amount || 0).toLocaleString()}`;
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

// ============================================================
// DASHBOARD
// ============================================================

async function loadDashboard() {
    const data = await apiGet('/dashboard');
    if (!data) return;

    const { kpis, recent_transactions, monthly_revenue, outstanding_by_class, payment_methods } = data;

    // KPIs
    document.getElementById('kpiToday').textContent = formatCurrency(kpis.collected_today);
    document.getElementById('kpiWeek').textContent = formatCurrency(kpis.collected_week);
    document.getElementById('kpiMonth').textContent = formatCurrency(kpis.collected_month);
    document.getElementById('kpiYear').textContent = formatCurrency(kpis.collected_year);

    // Summary
    document.getElementById('summExpected').textContent = formatCurrency(kpis.total_expected);
    document.getElementById('summCollectionRate').textContent = `${kpis.collection_rate}% collected`;
    document.getElementById('summOutstanding').textContent = formatCurrency(kpis.total_outstanding);
    document.getElementById('summOverdue').textContent = `${kpis.overdue_invoices} overdue invoices`;
    document.getElementById('summNetIncome').textContent = formatCurrency(kpis.net_income);
    document.getElementById('summExpenses').textContent = `Expenses: ${formatCurrency(kpis.total_expenses)}`;
    document.getElementById('summPending').textContent = kpis.pending_invoices;
    document.getElementById('summTotal').textContent = `Total: ${kpis.total_invoices} invoices`;

    // Charts
    renderRevenueChart(monthly_revenue);
    renderOutstandingChart(outstanding_by_class);
    renderMethodsChart(payment_methods);

    // Recent transactions
    renderTransactions(recent_transactions);
}

function renderRevenueChart(data) {
    const ctx = document.getElementById('chartRevenue');
    if (!ctx) return;
    if (charts.revenue) charts.revenue.destroy();

    charts.revenue = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.month),
            datasets: [{
                label: 'Revenue',
                data: data.map(d => d.amount),
                borderColor: '#E63946',
                backgroundColor: 'rgba(230, 57, 70, 0.08)',
                fill: true,
                tension: 0.4,
                borderWidth: 2,
                pointRadius: 4,
                pointBackgroundColor: '#E63946'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { callback: v => `KES ${(v/1000).toFixed(0)}K` }
                }
            }
        }
    });
}

function renderOutstandingChart(data) {
    const ctx = document.getElementById('chartOutstanding');
    if (!ctx) return;
    if (charts.outstanding) charts.outstanding.destroy();

    charts.outstanding = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.class_name),
            datasets: [{
                label: 'Outstanding',
                data: data.map(d => d.amount),
                backgroundColor: '#E63946',
                borderRadius: 6,
                barThickness: 24
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { callback: v => `KES ${(v/1000).toFixed(0)}K` }
                }
            }
        }
    });
}

function renderMethodsChart(data) {
    const ctx = document.getElementById('chartMethods');
    if (!ctx) return;
    if (charts.methods) charts.methods.destroy();

    const colors = ['#E63946', '#2ecc71', '#3498db', '#f39c12', '#9b59b6'];
    charts.methods = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.method.replace('_', ' ')),
            datasets: [{
                data: data.map(d => d.amount),
                backgroundColor: colors.slice(0, data.length),
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'bottom', labels: { font: { size: 11 } } }
            }
        }
    });
}

function renderTransactions(transactions) {
    const container = document.getElementById('recentTransactions');
    if (!transactions.length) {
        container.innerHTML = '<p style="color:#999;font-size:13px;text-align:center;padding:20px;">No recent transactions</p>';
        return;
    }
    container.innerHTML = transactions.map(t => `
        <div class="transaction-item">
            <div class="transaction-info">
                <span class="transaction-name">${t.student_name}</span>
                <span class="transaction-meta">${t.method} - ${formatDate(t.date)}</span>
            </div>
            <span class="transaction-amount">+${formatCurrency(t.amount)}</span>
        </div>
    `).join('');
}

// ============================================================
// FEE STRUCTURES
// ============================================================

async function loadFeeStructures() {
    const data = await apiGet('/fee-structures');
    if (!data) return;

    const tbody = document.getElementById('feeStructuresBody');
    if (!data.fee_structures.length) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#999;">No fee structures defined</td></tr>';
        return;
    }

    tbody.innerHTML = data.fee_structures.map(s => `
        <tr>
            <td><strong>${s.name}</strong></td>
            <td>${s.class_name || 'All'}</td>
            <td>${s.academic_year || '-'}</td>
            <td>${s.term || '-'}</td>
            <td><strong>${formatCurrency(s.total_amount || s.amount)}</strong></td>
            <td>${(s.components || []).length} items</td>
            <td>
                <button class="btn-action" onclick="editFeeStructure(${s.id})" title="Edit"><i class="icon-edit"></i></button>
                <button class="btn-action" onclick="deleteFeeStructure(${s.id})" title="Delete"><i class="icon-trash-2"></i></button>
            </td>
        </tr>
    `).join('');
}

function showFeeStructureModal() {
    const html = `
        <form id="feeStructureForm">
            <div class="form-group">
                <label>Structure Name</label>
                <input type="text" id="fsName" class="form-input" required placeholder="e.g. Term 1 Fees 2026">
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Academic Year</label>
                    <input type="text" id="fsYear" class="form-input" placeholder="2025/2026">
                </div>
                <div class="form-group">
                    <label>Term</label>
                    <select id="fsTerm" class="form-input">
                        <option value="">Select Term</option>
                        <option value="Term 1">Term 1</option>
                        <option value="Term 2">Term 2</option>
                        <option value="Term 3">Term 3</option>
                    </select>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Class (optional)</label>
                    <select id="fsClass" class="form-input">
                        <option value="">All Classes</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Total Amount</label>
                    <input type="number" id="fsAmount" class="form-input" placeholder="0">
                </div>
            </div>
            <div class="form-group">
                <label>Description</label>
                <textarea id="fsDesc" class="form-input" rows="2" placeholder="Optional description"></textarea>
            </div>
            <div class="form-group">
                <label>Due Date</label>
                <input type="date" id="fsDueDate" class="form-input">
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%;margin-top:8px;">Create Fee Structure</button>
        </form>
    `;
    openModal('New Fee Structure', html);
    loadClassesForSelect('fsClass');

    document.getElementById('feeStructureForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            name: document.getElementById('fsName').value,
            academic_year: document.getElementById('fsYear').value || null,
            term: document.getElementById('fsTerm').value || null,
            class_id: document.getElementById('fsClass').value ? parseInt(document.getElementById('fsClass').value) : null,
            amount: parseFloat(document.getElementById('fsAmount').value) || 0,
            description: document.getElementById('fsDesc').value || null,
            due_date: document.getElementById('fsDueDate').value || null
        };
        await apiPost('/fee-structures', payload);
        closeModal();
        loadFeeStructures();
    });
}

async function deleteFeeStructure(id) {
    if (!confirm('Delete this fee structure?')) return;
    await fetch(`${API_BASE}/fee-structures/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    loadFeeStructures();
}

// ============================================================
// STUDENT ACCOUNTS
// ============================================================

async function loadStudentAccounts() {
    const res = await fetch('/api/students', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    studentsCache = data.students || [];
    renderStudentCards(studentsCache);
}

function renderStudentCards(students) {
    const grid = document.getElementById('studentAccountsGrid');
    if (!students.length) {
        grid.innerHTML = '<p style="color:#999;text-align:center;padding:40px;">No students found</p>';
        return;
    }

    grid.innerHTML = students.map(s => `
        <div class="student-account-card" onclick="viewStudentProfile(${s.id})">
            <div class="student-card-header">
                <span class="student-card-name">${s.first_name} ${s.last_name}</span>
                <span class="student-card-adm">${s.admission_number || 'N/A'}</span>
            </div>
            <div class="student-card-class">${s.class_name || 'Not assigned'}</div>
            <div class="student-card-stats">
                <div class="student-stat">
                    <span class="student-stat-label">Status</span>
                    <span class="student-stat-value">${s.status || 'Active'}</span>
                </div>
                <div class="student-stat">
                    <span class="student-stat-label">View Profile</span>
                    <span class="student-stat-value" style="color:#E63946;font-size:12px;">Click to open</span>
                </div>
            </div>
        </div>
    `).join('');
}

function filterStudents(query) {
    const q = query.toLowerCase();
    const filtered = studentsCache.filter(s =>
        `${s.first_name} ${s.last_name}`.toLowerCase().includes(q) ||
        (s.admission_number || '').toLowerCase().includes(q)
    );
    renderStudentCards(filtered);
}

async function viewStudentProfile(studentId) {
    const data = await apiGet(`/student-profile/${studentId}`);
    if (!data) return;

    const { student, balance, payments, invoices, receipts, bursaries, penalties } = data;

    let html = `
        <div class="profile-stats">
            <div class="profile-stat-card">
                <div class="profile-stat-label">Total Invoiced</div>
                <div class="profile-stat-value">${formatCurrency(balance.total_invoiced)}</div>
            </div>
            <div class="profile-stat-card">
                <div class="profile-stat-label">Total Paid</div>
                <div class="profile-stat-value" style="color:#2ecc71;">${formatCurrency(balance.total_paid)}</div>
            </div>
            <div class="profile-stat-card">
                <div class="profile-stat-label">Outstanding</div>
                <div class="profile-stat-value" style="color:#E63946;">${formatCurrency(balance.outstanding)}</div>
            </div>
        </div>
    `;

    // Recent Payments
    if (payments.length) {
        html += `<div class="profile-section"><h4>Recent Payments (${payments.length})</h4>
            <table class="mini-table"><thead><tr><th>Date</th><th>Amount</th><th>Method</th><th>Reference</th></tr></thead><tbody>`;
        html += payments.slice(0, 10).map(p => `
            <tr>
                <td>${formatDate(p.payment_date)}</td>
                <td><strong>${formatCurrency(p.amount_paid)}</strong></td>
                <td>${p.payment_method}</td>
                <td>${p.transaction_id || '-'}</td>
            </tr>
        `).join('');
        html += '</tbody></table></div>';
    }

    // Invoices
    if (invoices.length) {
        html += `<div class="profile-section"><h4>Invoices (${invoices.length})</h4>
            <table class="mini-table"><thead><tr><th>Invoice No</th><th>Amount</th><th>Balance</th><th>Status</th></tr></thead><tbody>`;
        html += invoices.slice(0, 10).map(i => `
            <tr>
                <td>${i.invoice_number}</td>
                <td>${formatCurrency(i.amount)}</td>
                <td>${formatCurrency(i.balance)}</td>
                <td><span class="status-badge ${i.status}">${i.status}</span></td>
            </tr>
        `).join('');
        html += '</tbody></table></div>';
    }

    // Bursaries
    if (bursaries.length) {
        html += `<div class="profile-section"><h4>Bursaries & Discounts (${bursaries.length})</h4>
            <table class="mini-table"><thead><tr><th>Name</th><th>Type</th><th>Amount</th><th>Status</th></tr></thead><tbody>`;
        html += bursaries.map(b => `
            <tr>
                <td>${b.name}</td>
                <td>${b.bursary_type}</td>
                <td>${formatCurrency(b.amount)}</td>
                <td><span class="status-badge ${b.status === 'active' ? 'paid' : 'unpaid'}">${b.status}</span></td>
            </tr>
        `).join('');
        html += '</tbody></table></div>';
    }

    // Actions
    html += `
        <div style="display:flex;gap:8px;margin-top:16px;">
            <button class="btn btn-primary btn-sm" onclick="showPaymentModalFor(${studentId})">Record Payment</button>
            <button class="btn btn-outline btn-sm" onclick="showInvoiceModalFor(${studentId})">Create Invoice</button>
            <button class="btn btn-outline btn-sm" onclick="viewStatement(${studentId})">View Statement</button>
        </div>
    `;

    openModal(`${student.full_name} - ${student.admission_number || ''}`, html);
}

async function viewStatement(studentId) {
    const data = await apiGet(`/student-statement/${studentId}`);
    if (!data) return;

    const { student, entries, summary } = data;
    let html = `
        <div class="profile-stats">
            <div class="profile-stat-card">
                <div class="profile-stat-label">Total Debits</div>
                <div class="profile-stat-value">${formatCurrency(summary.total_debits)}</div>
            </div>
            <div class="profile-stat-card">
                <div class="profile-stat-label">Total Credits</div>
                <div class="profile-stat-value" style="color:#2ecc71;">${formatCurrency(summary.total_credits)}</div>
            </div>
            <div class="profile-stat-card">
                <div class="profile-stat-label">Balance</div>
                <div class="profile-stat-value" style="color:#E63946;">${formatCurrency(summary.closing_balance)}</div>
            </div>
        </div>
        <table class="mini-table"><thead><tr><th>Date</th><th>Description</th><th>Debit</th><th>Credit</th><th>Balance</th></tr></thead><tbody>
    `;
    html += entries.map(e => `
        <tr>
            <td>${formatDate(e.date)}</td>
            <td>${e.description}</td>
            <td>${e.debit ? formatCurrency(e.debit) : '-'}</td>
            <td>${e.credit ? formatCurrency(e.credit) : '-'}</td>
            <td><strong>${formatCurrency(e.balance)}</strong></td>
        </tr>
    `).join('');
    html += '</tbody></table>';

    openModal(`Statement - ${student.full_name}`, html);
}

// ============================================================
// PAYMENTS
// ============================================================

async function loadPayments() {
    const method = document.getElementById('filterPaymentMethod')?.value || '';
    let path = '/payments?per_page=50';
    if (method) path += `&method=${method}`;

    const data = await apiGet(path);
    if (!data) return;

    const tbody = document.getElementById('paymentsBody');
    if (!data.payments.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#999;">No payments found</td></tr>';
        return;
    }

    tbody.innerHTML = data.payments.map(p => `
        <tr>
            <td>${formatDate(p.payment_date)}</td>
            <td>${p.student_name || 'Unknown'}</td>
            <td>${p.admission_number || '-'}</td>
            <td><strong>${formatCurrency(p.amount_paid)}</strong></td>
            <td>${p.payment_method}</td>
            <td>${p.transaction_id || '-'}</td>
        </tr>
    `).join('');
}

function showPaymentModal() {
    showPaymentModalFor(null);
}

function showPaymentModalFor(studentId) {
    const html = `
        <form id="paymentForm">
            <div class="form-group">
                <label>Student</label>
                <select id="payStudentId" class="form-input" required>
                    <option value="">Select student...</option>
                </select>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Amount (KES)</label>
                    <input type="number" id="payAmount" class="form-input" required min="1">
                </div>
                <div class="form-group">
                    <label>Payment Method</label>
                    <select id="payMethod" class="form-input">
                        <option value="cash">Cash</option>
                        <option value="bank_transfer">Bank Transfer</option>
                        <option value="cheque">Cheque</option>
                        <option value="mobile_money">Mobile Money</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label>Transaction Reference</label>
                <input type="text" id="payReference" class="form-input" placeholder="Optional reference number">
            </div>
            <div class="form-group">
                <label>Description</label>
                <input type="text" id="payDescription" class="form-input" placeholder="Fee payment">
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%;margin-top:8px;">Record Payment</button>
        </form>
    `;
    openModal('Record Payment', html);
    loadStudentsForSelect('payStudentId', studentId);

    document.getElementById('paymentForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            student_id: parseInt(document.getElementById('payStudentId').value),
            amount_paid: parseFloat(document.getElementById('payAmount').value),
            payment_method: document.getElementById('payMethod').value,
            transaction_id: document.getElementById('payReference').value || null,
            description: document.getElementById('payDescription').value || 'Fee payment'
        };
        const result = await apiPost('/payments', payload);
        if (result && result.receipt) {
            closeModal();
            showPrintableReceipt(result.receipt);
            if (currentSection === 'payments') loadPayments();
            if (currentSection === 'dashboard') loadDashboard();
        }
    });
}

// ============================================================
// INVOICES
// ============================================================

async function loadInvoices() {
    const status = document.getElementById('filterInvoiceStatus')?.value || '';
    let path = '/invoices?per_page=50';
    if (status) path += `&status=${status}`;

    const data = await apiGet(path);
    if (!data) return;

    const tbody = document.getElementById('invoicesBody');
    if (!data.invoices.length) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#999;">No invoices found</td></tr>';
        return;
    }

    tbody.innerHTML = data.invoices.map(i => `
        <tr>
            <td>${i.invoice_number}</td>
            <td>${i.student_name || 'Unknown'}</td>
            <td>${formatCurrency(i.amount)}</td>
            <td>${formatCurrency(i.balance)}</td>
            <td>${formatDate(i.due_date)}</td>
            <td><span class="status-badge ${i.status}">${i.status}</span></td>
            <td>
                <button class="btn-action" onclick="printInvoice(${i.id})" title="Print"><i class="icon-printer"></i></button>
            </td>
        </tr>
    `).join('');
}

function showInvoiceModal() {
    showInvoiceModalFor(null);
}

function showInvoiceModalFor(studentId) {
    const html = `
        <form id="invoiceForm">
            <div class="form-group">
                <label>Student</label>
                <select id="invStudentId" class="form-input" required>
                    <option value="">Select student...</option>
                </select>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Amount (KES)</label>
                    <input type="number" id="invAmount" class="form-input" required min="1">
                </div>
                <div class="form-group">
                    <label>Due Date</label>
                    <input type="date" id="invDueDate" class="form-input">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Academic Year</label>
                    <input type="text" id="invYear" class="form-input" placeholder="2025/2026">
                </div>
                <div class="form-group">
                    <label>Term</label>
                    <select id="invTerm" class="form-input">
                        <option value="">Select Term</option>
                        <option value="Term 1">Term 1</option>
                        <option value="Term 2">Term 2</option>
                        <option value="Term 3">Term 3</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label>Description</label>
                <input type="text" id="invDesc" class="form-input" placeholder="Fee invoice" required>
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%;margin-top:8px;">Create Invoice</button>
        </form>
    `;
    openModal('Create Invoice', html);
    loadStudentsForSelect('invStudentId', studentId);

    document.getElementById('invoiceForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            student_id: parseInt(document.getElementById('invStudentId').value),
            amount: parseFloat(document.getElementById('invAmount').value),
            due_date: document.getElementById('invDueDate').value || null,
            academic_year: document.getElementById('invYear').value || null,
            term: document.getElementById('invTerm').value || null,
            description: document.getElementById('invDesc').value
        };
        await apiPost('/invoices', payload);
        closeModal();
        if (currentSection === 'invoices') loadInvoices();
    });
}

function showBulkInvoiceModal() {
    const html = `
        <form id="bulkInvoiceForm">
            <div class="form-group">
                <label>Class</label>
                <select id="bulkClass" class="form-input" required>
                    <option value="">Select class...</option>
                </select>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Amount (KES)</label>
                    <input type="number" id="bulkAmount" class="form-input" required min="1">
                </div>
                <div class="form-group">
                    <label>Due Date</label>
                    <input type="date" id="bulkDueDate" class="form-input">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Academic Year</label>
                    <input type="text" id="bulkYear" class="form-input" placeholder="2025/2026">
                </div>
                <div class="form-group">
                    <label>Term</label>
                    <select id="bulkTerm" class="form-input">
                        <option value="Term 1">Term 1</option>
                        <option value="Term 2">Term 2</option>
                        <option value="Term 3">Term 3</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label>Description</label>
                <input type="text" id="bulkDesc" class="form-input" placeholder="Term fees" required>
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%;margin-top:8px;">Create Invoices for Class</button>
        </form>
    `;
    openModal('Bulk Invoice - Entire Class', html);
    loadClassesForSelect('bulkClass');

    document.getElementById('bulkInvoiceForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            class_id: parseInt(document.getElementById('bulkClass').value),
            amount: parseFloat(document.getElementById('bulkAmount').value),
            due_date: document.getElementById('bulkDueDate').value || null,
            academic_year: document.getElementById('bulkYear').value || null,
            term: document.getElementById('bulkTerm').value || null,
            description: document.getElementById('bulkDesc').value
        };
        const result = await apiPost('/invoices/bulk', payload);
        closeModal();
        if (result) alert(`${result.count} invoices created successfully`);
        loadInvoices();
    });
}

// ============================================================
// RECEIPTS
// ============================================================

async function loadReceipts() {
    const data = await apiGet('/receipts?per_page=50');
    if (!data) return;

    const tbody = document.getElementById('receiptsBody');
    if (!data.receipts.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#999;">No receipts found</td></tr>';
        return;
    }

    tbody.innerHTML = data.receipts.map(r => `
        <tr>
            <td>${r.receipt_number}</td>
            <td>${r.student_name || 'Unknown'}</td>
            <td><strong>${formatCurrency(r.amount)}</strong></td>
            <td>${r.payment_method}</td>
            <td>${formatDate(r.created_at)}</td>
            <td>
                <button class="btn-action" onclick="printReceipt(${r.id})" title="Print"><i class="icon-printer"></i></button>
            </td>
        </tr>
    `).join('');
}

async function printReceipt(receiptId) {
    const data = await apiGet(`/receipts/${receiptId}`);
    if (!data) return;
    showPrintableReceipt(data.receipt, data.school);
}

async function printInvoice(invoiceId) {
    const data = await apiGet(`/invoices/${invoiceId}`);
    if (!data) return;
    showPrintableInvoice(data.invoice, data.school);
}

function showPrintableReceipt(receipt, school) {
    if (!school) {
        fetch('/api/settings/school', { headers: { 'Authorization': `Bearer ${token}` } })
            .then(r => r.json())
            .then(d => showPrintableReceiptHTML(receipt, d.school || {}));
    } else {
        showPrintableReceiptHTML(receipt, school);
    }
}

function showPrintableReceiptHTML(receipt, school) {
    const html = buildReceiptHTML(receipt, school);
    const frame = document.getElementById('printFrame');
    frame.srcdoc = html;
    setTimeout(() => frame.contentWindow.print(), 500);
}

function showPrintableInvoice(invoice, school) {
    if (!school) {
        fetch('/api/settings/school', { headers: { 'Authorization': `Bearer ${token}` } })
            .then(r => r.json())
            .then(d => showPrintableInvoiceHTML(invoice, d.school || {}));
    } else {
        showPrintableInvoiceHTML(invoice, school);
    }
}

function showPrintableInvoiceHTML(invoice, school) {
    const html = buildInvoiceHTML(invoice, school);
    const frame = document.getElementById('printFrame');
    frame.srcdoc = html;
    setTimeout(() => frame.contentWindow.print(), 500);
}

function buildReceiptHTML(receipt, school) {
    return `<!DOCTYPE html>
<html><head><style>
    @page { size: A5; margin: 15mm; }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; color: #333; padding: 20px; }
    .header { text-align: center; border-bottom: 2px solid #E63946; padding-bottom: 12px; margin-bottom: 16px; }
    .school-name { font-size: 18px; font-weight: 700; color: #E63946; }
    .school-motto { font-size: 10px; font-style: italic; color: #666; margin-top: 2px; }
    .school-info { font-size: 9px; color: #888; margin-top: 4px; }
    .doc-title { font-size: 14px; font-weight: 700; text-align: center; margin: 12px 0; text-transform: uppercase; letter-spacing: 1px; }
    .receipt-no { text-align: center; font-size: 12px; font-weight: 600; color: #E63946; margin-bottom: 16px; }
    .details-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 16px; }
    .detail-item { }
    .detail-label { font-size: 9px; color: #888; text-transform: uppercase; }
    .detail-value { font-size: 11px; font-weight: 600; }
    .amount-box { text-align: center; background: #f9f9f9; border: 1px solid #eee; border-radius: 6px; padding: 12px; margin: 16px 0; }
    .amount-label { font-size: 10px; color: #666; }
    .amount-value { font-size: 22px; font-weight: 700; color: #E63946; }
    .footer { margin-top: 24px; border-top: 1px solid #eee; padding-top: 12px; }
    .signatures { display: flex; justify-content: space-between; margin-top: 30px; }
    .sig-line { width: 120px; border-top: 1px solid #999; text-align: center; font-size: 9px; padding-top: 4px; }
    .qr-placeholder { text-align: center; margin-top: 12px; font-size: 9px; color: #999; border: 1px dashed #ddd; padding: 8px; border-radius: 4px; }
</style></head><body>
    <div class="header">
        <div class="school-name">${school.school_name || 'CLASSMATE ACADEMY'}</div>
        <div class="school-motto">${school.motto || ''}</div>
        <div class="school-info">${school.address || ''} | ${school.email || ''} | ${school.phone || ''}</div>
    </div>
    <div class="doc-title">Official Payment Receipt</div>
    <div class="receipt-no">${receipt.receipt_number}</div>
    <div class="details-grid">
        <div class="detail-item"><div class="detail-label">Student Name</div><div class="detail-value">${receipt.student_name || '-'}</div></div>
        <div class="detail-item"><div class="detail-label">Date</div><div class="detail-value">${formatDate(receipt.created_at)}</div></div>
        <div class="detail-item"><div class="detail-label">Payment Method</div><div class="detail-value">${receipt.payment_method}</div></div>
        <div class="detail-item"><div class="detail-label">Description</div><div class="detail-value">${receipt.description || 'Fee payment'}</div></div>
    </div>
    <div class="amount-box">
        <div class="amount-label">Amount Received</div>
        <div class="amount-value">${formatCurrency(receipt.amount)}</div>
    </div>
    <div class="qr-placeholder">QR: ${receipt.receipt_number} | Verified Digital Receipt</div>
    <div class="footer">
        <div class="signatures">
            <div class="sig-line">Finance Officer</div>
            <div class="sig-line">Principal</div>
        </div>
    </div>
</body></html>`;
}

function buildInvoiceHTML(invoice, school) {
    return `<!DOCTYPE html>
<html><head><style>
    @page { size: A5; margin: 15mm; }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; color: #333; padding: 20px; }
    .header { text-align: center; border-bottom: 2px solid #E63946; padding-bottom: 12px; margin-bottom: 16px; }
    .school-name { font-size: 18px; font-weight: 700; color: #E63946; }
    .school-motto { font-size: 10px; font-style: italic; color: #666; margin-top: 2px; }
    .school-info { font-size: 9px; color: #888; margin-top: 4px; }
    .doc-title { font-size: 14px; font-weight: 700; text-align: center; margin: 12px 0; text-transform: uppercase; letter-spacing: 1px; }
    .invoice-no { text-align: center; font-size: 12px; font-weight: 600; color: #E63946; margin-bottom: 16px; }
    .details-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 16px; }
    .detail-item { }
    .detail-label { font-size: 9px; color: #888; text-transform: uppercase; }
    .detail-value { font-size: 11px; font-weight: 600; }
    .amount-box { background: #f9f9f9; border: 1px solid #eee; border-radius: 6px; padding: 12px; margin: 16px 0; }
    .amount-row { display: flex; justify-content: space-between; padding: 4px 0; }
    .amount-row.total { border-top: 1px solid #ddd; padding-top: 8px; margin-top: 4px; font-weight: 700; font-size: 14px; }
    .status-tag { display: inline-block; padding: 3px 10px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; }
    .status-unpaid { background: #fce4ec; color: #c62828; }
    .status-partial { background: #fff3e0; color: #e65100; }
    .status-paid { background: #e8f5e9; color: #2e7d32; }
    .footer { margin-top: 24px; border-top: 1px solid #eee; padding-top: 12px; font-size: 9px; color: #888; }
    .signatures { display: flex; justify-content: space-between; margin-top: 30px; }
    .sig-line { width: 120px; border-top: 1px solid #999; text-align: center; font-size: 9px; padding-top: 4px; }
    .qr-placeholder { text-align: center; margin-top: 12px; font-size: 9px; color: #999; border: 1px dashed #ddd; padding: 8px; border-radius: 4px; }
</style></head><body>
    <div class="header">
        <div class="school-name">${school.school_name || 'CLASSMATE ACADEMY'}</div>
        <div class="school-motto">${school.motto || ''}</div>
        <div class="school-info">${school.address || ''} | ${school.email || ''} | ${school.phone || ''}</div>
    </div>
    <div class="doc-title">Fee Invoice</div>
    <div class="invoice-no">${invoice.invoice_number}</div>
    <div class="details-grid">
        <div class="detail-item"><div class="detail-label">Student Name</div><div class="detail-value">${invoice.student_name || '-'}</div></div>
        <div class="detail-item"><div class="detail-label">Due Date</div><div class="detail-value">${formatDate(invoice.due_date)}</div></div>
        <div class="detail-item"><div class="detail-label">Term</div><div class="detail-value">${invoice.term || '-'}</div></div>
        <div class="detail-item"><div class="detail-label">Academic Year</div><div class="detail-value">${invoice.academic_year || '-'}</div></div>
    </div>
    <div class="amount-box">
        <div class="amount-row"><span>Description</span><span>${invoice.description || 'Fee invoice'}</span></div>
        <div class="amount-row"><span>Total Amount</span><span>${formatCurrency(invoice.amount)}</span></div>
        <div class="amount-row"><span>Amount Paid</span><span>${formatCurrency(invoice.amount - invoice.balance)}</span></div>
        <div class="amount-row total"><span>Balance Due</span><span>${formatCurrency(invoice.balance)}</span></div>
    </div>
    <p style="text-align:center;">Status: <span class="status-tag status-${invoice.status}">${invoice.status}</span></p>
    <div class="qr-placeholder">QR: ${invoice.invoice_number} | Verified Digital Invoice</div>
    <div class="footer">
        <div class="signatures">
            <div class="sig-line">Finance Officer</div>
            <div class="sig-line">Principal</div>
        </div>
    </div>
</body></html>`;
}

// ============================================================
// EXPENSES
// ============================================================

async function loadExpenses() {
    const data = await apiGet('/expenses');
    if (!data) return;

    const tbody = document.getElementById('expensesBody');
    if (!data.expenses.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#999;">No expenses recorded</td></tr>';
        return;
    }

    tbody.innerHTML = data.expenses.map(e => `
        <tr>
            <td>${formatDate(e.expense_date)}</td>
            <td>${e.category_name || '-'}</td>
            <td>${e.description}</td>
            <td>${e.vendor || '-'}</td>
            <td><strong>${formatCurrency(e.amount)}</strong></td>
            <td>${e.payment_method || '-'}</td>
        </tr>
    `).join('');
}

function showExpenseModal() {
    const html = `
        <form id="expenseForm">
            <div class="form-group">
                <label>Category</label>
                <select id="expCategory" class="form-input" required>
                    <option value="">Select category...</option>
                </select>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Amount (KES)</label>
                    <input type="number" id="expAmount" class="form-input" required min="1">
                </div>
                <div class="form-group">
                    <label>Date</label>
                    <input type="date" id="expDate" class="form-input" value="${new Date().toISOString().split('T')[0]}">
                </div>
            </div>
            <div class="form-group">
                <label>Description</label>
                <input type="text" id="expDesc" class="form-input" required placeholder="What was this expense for?">
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Vendor</label>
                    <input type="text" id="expVendor" class="form-input" placeholder="Vendor name">
                </div>
                <div class="form-group">
                    <label>Payment Method</label>
                    <select id="expMethod" class="form-input">
                        <option value="cash">Cash</option>
                        <option value="bank_transfer">Bank Transfer</option>
                        <option value="cheque">Cheque</option>
                        <option value="mobile_money">Mobile Money</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label>Reference Number</label>
                <input type="text" id="expRef" class="form-input" placeholder="Optional reference">
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%;margin-top:8px;">Record Expense</button>
        </form>
    `;
    openModal('Record Expense', html);
    loadExpenseCategories();

    document.getElementById('expenseForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            category_id: parseInt(document.getElementById('expCategory').value),
            amount: parseFloat(document.getElementById('expAmount').value),
            expense_date: document.getElementById('expDate').value,
            description: document.getElementById('expDesc').value,
            vendor: document.getElementById('expVendor').value || null,
            payment_method: document.getElementById('expMethod').value,
            reference_number: document.getElementById('expRef').value || null
        };
        await apiPost('/expenses', payload);
        closeModal();
        loadExpenses();
    });
}

async function loadExpenseCategories() {
    const data = await apiGet('/expense-categories');
    if (!data) return;
    const select = document.getElementById('expCategory');
    data.categories.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.name;
        select.appendChild(opt);
    });
}

// ============================================================
// REPORTS
// ============================================================

async function loadReport(type) {
    const output = document.getElementById('reportOutput');
    const content = document.getElementById('reportContent');
    output.style.display = 'block';

    if (type === 'collection') {
        document.getElementById('reportTitle').textContent = 'Collection Report';
        const data = await apiGet('/reports/collection?period=monthly');
        if (!data) return;

        let html = `
            <div class="profile-stats">
                <div class="profile-stat-card"><div class="profile-stat-label">Period</div><div class="profile-stat-value">${data.period}</div></div>
                <div class="profile-stat-card"><div class="profile-stat-label">Total Collected</div><div class="profile-stat-value">${formatCurrency(data.total_collected)}</div></div>
                <div class="profile-stat-card"><div class="profile-stat-label">Paying Students</div><div class="profile-stat-value">${data.paying_students}</div></div>
            </div>
            <h4 style="margin:16px 0 8px;font-size:13px;">By Class</h4>
            <table class="mini-table"><thead><tr><th>Class</th><th>Collected</th><th>Expected</th><th>Rate</th></tr></thead><tbody>
        `;
        html += data.class_breakdown.map(c => `
            <tr><td>${c.class_name}</td><td>${formatCurrency(c.collected)}</td><td>${formatCurrency(c.expected)}</td><td>${c.rate}%</td></tr>
        `).join('');
        html += '</tbody></table>';
        content.innerHTML = html;

    } else if (type === 'arrears') {
        document.getElementById('reportTitle').textContent = 'Arrears Report';
        const data = await apiGet('/reports/arrears');
        if (!data) return;

        let html = `
            <div class="profile-stats">
                <div class="profile-stat-card"><div class="profile-stat-label">Students in Arrears</div><div class="profile-stat-value">${data.student_count}</div></div>
                <div class="profile-stat-card"><div class="profile-stat-label">Total Outstanding</div><div class="profile-stat-value" style="color:#E63946;">${formatCurrency(data.total_outstanding)}</div></div>
            </div>
            <table class="mini-table"><thead><tr><th>Student</th><th>Admission No</th><th>Class</th><th>Outstanding</th></tr></thead><tbody>
        `;
        html += data.arrears.map(a => `
            <tr><td>${a.student_name}</td><td>${a.admission_number}</td><td>${a.class_name}</td><td style="color:#E63946;font-weight:600;">${formatCurrency(a.outstanding)}</td></tr>
        `).join('');
        html += '</tbody></table>';
        content.innerHTML = html;

    } else if (type === 'fully-paid') {
        document.getElementById('reportTitle').textContent = 'Fully Paid Students';
        const data = await apiGet('/reports/fully-paid');
        if (!data) return;

        let html = `
            <div class="profile-stats">
                <div class="profile-stat-card"><div class="profile-stat-label">Fully Paid</div><div class="profile-stat-value" style="color:#2ecc71;">${data.count}</div></div>
            </div>
            <table class="mini-table"><thead><tr><th>Student</th><th>Admission No</th><th>Class</th><th>Total Paid</th></tr></thead><tbody>
        `;
        html += data.students.map(s => `
            <tr><td>${s.student_name}</td><td>${s.admission_number}</td><td>${s.class_name}</td><td>${formatCurrency(s.total_paid)}</td></tr>
        `).join('');
        html += '</tbody></table>';
        content.innerHTML = html;

    } else if (type === 'statement') {
        document.getElementById('reportTitle').textContent = 'Student Statement';
        content.innerHTML = `
            <div class="form-group">
                <label>Select Student</label>
                <select id="reportStudentSelect" class="form-input" onchange="generateStatement(this.value)">
                    <option value="">Choose a student...</option>
                </select>
            </div>
            <div id="statementContent"></div>
        `;
        loadStudentsForSelect('reportStudentSelect');
    }
}

async function generateStatement(studentId) {
    if (!studentId) return;
    const data = await apiGet(`/student-statement/${studentId}`);
    if (!data) return;

    const { student, entries, summary } = data;
    let html = `
        <div class="profile-stats" style="margin-top:16px;">
            <div class="profile-stat-card"><div class="profile-stat-label">Total Debits</div><div class="profile-stat-value">${formatCurrency(summary.total_debits)}</div></div>
            <div class="profile-stat-card"><div class="profile-stat-label">Total Credits</div><div class="profile-stat-value" style="color:#2ecc71;">${formatCurrency(summary.total_credits)}</div></div>
            <div class="profile-stat-card"><div class="profile-stat-label">Balance</div><div class="profile-stat-value" style="color:#E63946;">${formatCurrency(summary.closing_balance)}</div></div>
        </div>
        <table class="mini-table"><thead><tr><th>Date</th><th>Description</th><th>Debit</th><th>Credit</th><th>Balance</th></tr></thead><tbody>
    `;
    html += entries.map(e => `
        <tr>
            <td>${formatDate(e.date)}</td>
            <td>${e.description}</td>
            <td>${e.debit ? formatCurrency(e.debit) : '-'}</td>
            <td>${e.credit ? formatCurrency(e.credit) : '-'}</td>
            <td><strong>${formatCurrency(e.balance)}</strong></td>
        </tr>
    `).join('');
    html += '</tbody></table>';
    document.getElementById('statementContent').innerHTML = html;
}

// ============================================================
// NOTIFICATIONS
// ============================================================

async function loadNotifications() {
    const data = await apiGet('/notifications');
    if (!data) return;

    const tbody = document.getElementById('notificationsBody');
    if (!data.notifications.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#999;">No notifications</td></tr>';
        return;
    }

    tbody.innerHTML = data.notifications.map(n => `
        <tr>
            <td>${formatDate(n.sent_at || n.created_at)}</td>
            <td>${n.student_name || '-'}</td>
            <td>${n.notification_type}</td>
            <td>${n.subject || '-'}</td>
            <td>${n.channel}</td>
            <td><span class="status-badge ${n.status === 'sent' ? 'paid' : 'unpaid'}">${n.status}</span></td>
        </tr>
    `).join('');
}

function showReminderModal() {
    const html = `
        <form id="reminderForm">
            <div class="form-group">
                <label>Send reminders to students with outstanding balances</label>
                <p style="font-size:12px;color:#888;margin-top:4px;">This will send a system notification to all students who have unpaid invoices.</p>
            </div>
            <div class="form-group">
                <label>Message</label>
                <textarea id="reminderMsg" class="form-input" rows="3">This is a reminder about your outstanding fee balance. Please make payment at your earliest convenience.</textarea>
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%;margin-top:8px;">Send Reminders</button>
        </form>
    `;
    openModal('Send Fee Reminders', html);

    document.getElementById('reminderForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        // Get all students with arrears
        const arrearsData = await apiGet('/reports/arrears');
        if (!arrearsData || !arrearsData.arrears.length) {
            alert('No students with outstanding balances found.');
            closeModal();
            return;
        }
        const studentIds = arrearsData.arrears.map(a => a.student_id);
        const message = document.getElementById('reminderMsg').value;

        const result = await apiPost('/notifications/send-reminder', { student_ids: studentIds, message });
        closeModal();
        if (result) alert(`${result.count} reminders sent successfully`);
        loadNotifications();
    });
}

// ============================================================
// SETTINGS
// ============================================================

async function loadSettings() {
    const data = await apiGet('/settings');
    if (!data) return;

    const s = data.settings;
    document.getElementById('settCurrency').value = s.currency || 'KES';
    document.getElementById('settCurrencySymbol').value = s.currency_symbol || 'KES';
    document.getElementById('settReceiptPrefix').value = s.receipt_prefix || 'RCP';
    document.getElementById('settInvoicePrefix').value = s.invoice_prefix || 'INV';
    document.getElementById('settPenaltyRate').value = s.late_penalty_rate || 0;
    document.getElementById('settGracePeriod').value = s.grace_period_days || 14;
    document.getElementById('settAutoReminder').checked = s.auto_reminder || false;
    document.getElementById('settReminderDays').value = s.reminder_days_before || 7;
    document.getElementById('settReceiptFooter').value = s.receipt_footer_text || '';
    document.getElementById('settInvoiceFooter').value = s.invoice_footer_text || '';

    // Fee categories
    const catData = await apiGet('/fee-categories');
    const catList = document.getElementById('feeCategoriesList');
    if (catData && catData.categories.length) {
        catList.innerHTML = catData.categories.map(c => `
            <div class="category-item">
                <div><span class="category-name">${c.name}</span><br><span class="category-code">${c.code}</span></div>
                <span class="status-badge ${c.is_mandatory ? 'paid' : 'partial'}">${c.is_mandatory ? 'Mandatory' : 'Optional'}</span>
            </div>
        `).join('');
    } else {
        catList.innerHTML = '<p style="color:#999;font-size:12px;">No categories defined</p>';
    }

    // Bank accounts
    const bankList = document.getElementById('bankAccountsList');
    if (data.bank_accounts && data.bank_accounts.length) {
        bankList.innerHTML = data.bank_accounts.map(b => `
            <div class="bank-item">
                <div><span class="bank-name">${b.bank_name} - ${b.account_name}</span><br><span class="bank-number">${b.account_number}</span></div>
                ${b.is_primary ? '<span class="status-badge paid">Primary</span>' : ''}
            </div>
        `).join('');
    } else {
        bankList.innerHTML = '<p style="color:#999;font-size:12px;">No bank accounts configured</p>';
    }
}

async function saveFinanceSettings(e) {
    e.preventDefault();
    const payload = {
        currency: document.getElementById('settCurrency').value,
        currency_symbol: document.getElementById('settCurrencySymbol').value,
        receipt_prefix: document.getElementById('settReceiptPrefix').value,
        invoice_prefix: document.getElementById('settInvoicePrefix').value,
        late_penalty_rate: parseFloat(document.getElementById('settPenaltyRate').value) || 0,
        grace_period_days: parseInt(document.getElementById('settGracePeriod').value) || 14,
        auto_reminder: document.getElementById('settAutoReminder').checked,
        reminder_days_before: parseInt(document.getElementById('settReminderDays').value) || 7,
        receipt_footer_text: document.getElementById('settReceiptFooter').value,
        invoice_footer_text: document.getElementById('settInvoiceFooter').value
    };
    await apiPut('/settings', payload);
    alert('Settings saved successfully');
}

function showCategoryModal() {
    const html = `
        <form id="categoryForm">
            <div class="form-row">
                <div class="form-group">
                    <label>Category Name</label>
                    <input type="text" id="catName" class="form-input" required placeholder="e.g. Tuition">
                </div>
                <div class="form-group">
                    <label>Code</label>
                    <input type="text" id="catCode" class="form-input" required placeholder="e.g. TUI">
                </div>
            </div>
            <div class="form-group">
                <label>Description</label>
                <input type="text" id="catDesc" class="form-input" placeholder="Optional description">
            </div>
            <div class="form-group">
                <label><input type="checkbox" id="catMandatory" checked> Mandatory</label>
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%;margin-top:8px;">Add Category</button>
        </form>
    `;
    openModal('Add Fee Category', html);

    document.getElementById('categoryForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await apiPost('/fee-categories', {
            name: document.getElementById('catName').value,
            code: document.getElementById('catCode').value,
            description: document.getElementById('catDesc').value || null,
            is_mandatory: document.getElementById('catMandatory').checked
        });
        closeModal();
        loadSettings();
    });
}

function showBankAccountModal() {
    const html = `
        <form id="bankForm">
            <div class="form-row">
                <div class="form-group">
                    <label>Bank Name</label>
                    <input type="text" id="bankName" class="form-input" required>
                </div>
                <div class="form-group">
                    <label>Account Name</label>
                    <input type="text" id="bankAccName" class="form-input" required>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Account Number</label>
                    <input type="text" id="bankAccNum" class="form-input" required>
                </div>
                <div class="form-group">
                    <label>Branch</label>
                    <input type="text" id="bankBranch" class="form-input">
                </div>
            </div>
            <div class="form-group">
                <label><input type="checkbox" id="bankPrimary"> Primary Account</label>
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%;margin-top:8px;">Add Account</button>
        </form>
    `;
    openModal('Add Bank Account', html);

    document.getElementById('bankForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await apiPost('/bank-accounts', {
            bank_name: document.getElementById('bankName').value,
            account_name: document.getElementById('bankAccName').value,
            account_number: document.getElementById('bankAccNum').value,
            branch: document.getElementById('bankBranch').value || null,
            is_primary: document.getElementById('bankPrimary').checked
        });
        closeModal();
        loadSettings();
    });
}

// ============================================================
// HELPERS
// ============================================================

async function loadStudentsForSelect(selectId, preselectedId) {
    const res = await fetch('/api/students', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const select = document.getElementById(selectId);
    if (!select) return;

    (data.students || []).forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id;
        opt.textContent = `${s.first_name} ${s.last_name} (${s.admission_number || 'N/A'})`;
        if (preselectedId && s.id === preselectedId) opt.selected = true;
        select.appendChild(opt);
    });
}

async function loadClassesForSelect(selectId) {
    const res = await fetch('/api/academics/classes', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const select = document.getElementById(selectId);
    if (!select) return;

    (data.classes || []).forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.name;
        select.appendChild(opt);
    });
}

// Make functions globally accessible
window.viewStudentProfile = viewStudentProfile;
window.viewStatement = viewStatement;
window.showPaymentModalFor = showPaymentModalFor;
window.showInvoiceModalFor = showInvoiceModalFor;
window.editFeeStructure = showFeeStructureModal;
window.deleteFeeStructure = deleteFeeStructure;
window.printReceipt = printReceipt;
window.printInvoice = printInvoice;
window.generateStatement = generateStatement;
