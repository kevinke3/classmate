document.addEventListener('DOMContentLoaded', () => {
    if (!auth.requireAuth()) return;

    const user = auth.getUser();
    if (user && user.role !== 'finance' && user.role !== 'admin') {
        window.location.href = '/login';
        return;
    }

    initTabs();
    loadStats();
    loadPayments();
    loadInvoices();
    loadReceipts();

    document.getElementById('recordPaymentBtn').addEventListener('click', showRecordPaymentModal);
    document.getElementById('createInvoiceBtn').addEventListener('click', showCreateInvoiceModal);
    document.getElementById('closePrintBtn').addEventListener('click', closePrintModal);
    document.getElementById('printBtn').addEventListener('click', () => window.print());
    document.getElementById('invoiceFilter').addEventListener('change', loadInvoices);

    const balanceSearch = document.getElementById('balanceSearch');
    let debounce;
    balanceSearch.addEventListener('input', () => {
        clearTimeout(debounce);
        debounce = setTimeout(() => searchStudentBalances(balanceSearch.value), 300);
    });
});

function initTabs() {
    const tabs = document.querySelectorAll('.finance-tab');
    const panels = document.querySelectorAll('.finance-panel');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(`panel-${tab.dataset.tab}`).classList.add('active');
        });
    });
}

async function loadStats() {
    try {
        const data = await api.get('/finance/stats');
        document.getElementById('totalCollected').textContent = formatKES(data.total_collected);
        document.getElementById('totalOutstanding').textContent = formatKES(data.total_outstanding);
        document.getElementById('totalPayments').textContent = data.total_payments;
        document.getElementById('totalInvoices').textContent = data.total_invoices;
    } catch (err) {
        console.error('Failed to load finance stats:', err);
    }
}

async function loadPayments() {
    try {
        const data = await api.get('/finance/payments?per_page=50');
        const tbody = document.getElementById('paymentsTableBody');
        if (!data.payments || data.payments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No payments recorded yet</td></tr>';
            return;
        }
        tbody.innerHTML = data.payments.map(p => `
            <tr>
                <td>
                    <div class="user-cell">
                        <div class="user-cell-avatar">${getInitials(p.student_name || 'N/A')}</div>
                        <div class="user-cell-info">
                            <span class="user-cell-name">${p.student_name || 'Unknown'}</span>
                            <span class="user-cell-email">${p.admission_number || ''}</span>
                        </div>
                    </div>
                </td>
                <td><strong>${formatKES(p.amount_paid)}</strong></td>
                <td><span class="badge badge-${getBadgeClass(p.payment_method)}">${p.payment_method || 'N/A'}</span></td>
                <td>${p.transaction_id || 'N/A'}</td>
                <td>${formatDate(p.payment_date)}</td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick="viewPaymentReceipt(${p.id})">
                        <i class="icon-receipt"></i> Receipt
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load payments:', err);
    }
}

async function loadInvoices() {
    try {
        const filter = document.getElementById('invoiceFilter').value;
        const url = filter ? `/finance/invoices?per_page=50&status=${filter}` : '/finance/invoices?per_page=50';
        const data = await api.get(url);
        const tbody = document.getElementById('invoicesTableBody');
        if (!data.invoices || data.invoices.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No invoices found</td></tr>';
            return;
        }
        tbody.innerHTML = data.invoices.map(inv => `
            <tr>
                <td><strong>${inv.invoice_number}</strong></td>
                <td>
                    <div class="user-cell">
                        <div class="user-cell-avatar">${getInitials(inv.student_name || 'N/A')}</div>
                        <div class="user-cell-info">
                            <span class="user-cell-name">${inv.student_name || 'Unknown'}</span>
                            <span class="user-cell-email">${inv.admission_number || ''}</span>
                        </div>
                    </div>
                </td>
                <td>${formatKES(inv.amount)}</td>
                <td><strong>${formatKES(inv.balance)}</strong></td>
                <td>${inv.due_date ? formatDate(inv.due_date) : 'N/A'}</td>
                <td><span class="badge badge-${getStatusBadge(inv.status)}">${inv.status}</span></td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick="viewInvoice(${inv.id})">
                        <i class="icon-printer"></i> Print
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load invoices:', err);
    }
}

async function loadReceipts() {
    try {
        const data = await api.get('/finance/receipts?per_page=50');
        const tbody = document.getElementById('receiptsTableBody');
        if (!data.receipts || data.receipts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No receipts generated yet</td></tr>';
            return;
        }
        tbody.innerHTML = data.receipts.map(r => `
            <tr>
                <td><strong>${r.receipt_number}</strong></td>
                <td>
                    <div class="user-cell">
                        <div class="user-cell-avatar">${getInitials(r.student_name || 'N/A')}</div>
                        <div class="user-cell-info">
                            <span class="user-cell-name">${r.student_name || 'Unknown'}</span>
                            <span class="user-cell-email">${r.admission_number || ''}</span>
                        </div>
                    </div>
                </td>
                <td><strong>${formatKES(r.amount)}</strong></td>
                <td>${r.payment_method || 'N/A'}</td>
                <td>${formatDate(r.created_at)}</td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick="viewReceipt(${r.id})">
                        <i class="icon-printer"></i> Print
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load receipts:', err);
    }
}

async function searchStudentBalances(query) {
    const container = document.getElementById('balanceCards');
    if (!query || query.length < 2) {
        container.innerHTML = '<div class="empty-state">Type at least 2 characters to search</div>';
        return;
    }

    try {
        const data = await api.get(`/students/?search=${encodeURIComponent(query)}&per_page=20`);
        const students = data.students || data;
        if (!students || students.length === 0) {
            container.innerHTML = '<div class="empty-state">No students found</div>';
            return;
        }

        container.innerHTML = '';
        for (const s of students) {
            try {
                const balance = await api.get(`/finance/student-balance/${s.id}`);
                container.innerHTML += `
                    <div class="balance-card">
                        <div class="balance-card-header">
                            <div class="balance-card-avatar">${getInitials(s.full_name || 'N/A')}</div>
                            <div>
                                <div class="balance-card-name">${s.full_name || 'Unknown'}</div>
                                <div class="balance-card-id">${s.admission_number}</div>
                            </div>
                        </div>
                        <div class="balance-card-stats">
                            <div class="balance-stat">
                                <div class="balance-stat-value">${formatKES(balance.total_invoiced)}</div>
                                <div class="balance-stat-label">Invoiced</div>
                            </div>
                            <div class="balance-stat paid">
                                <div class="balance-stat-value">${formatKES(balance.total_paid)}</div>
                                <div class="balance-stat-label">Paid</div>
                            </div>
                            <div class="balance-stat outstanding" style="grid-column: span 2;">
                                <div class="balance-stat-value">${formatKES(balance.outstanding_balance)}</div>
                                <div class="balance-stat-label">Outstanding Balance</div>
                            </div>
                        </div>
                    </div>
                `;
            } catch (e) {
                console.error('Balance fetch failed for student', s.id, e);
            }
        }
    } catch (err) {
        console.error('Student search failed:', err);
        container.innerHTML = '<div class="empty-state">Search failed</div>';
    }
}

async function viewInvoice(invoiceId) {
    try {
        const data = await api.get(`/finance/invoices/${invoiceId}`);
        const inv = data.invoice;
        const school = data.school || {};
        showPrintDocument('Invoice', buildInvoiceHTML(inv, school));
    } catch (err) {
        console.error('Failed to load invoice:', err);
    }
}

async function viewReceipt(receiptId) {
    try {
        const data = await api.get(`/finance/receipts/${receiptId}`);
        const receipt = data.receipt;
        const school = data.school || {};
        showPrintDocument('Receipt', buildReceiptHTML(receipt, school));
    } catch (err) {
        console.error('Failed to load receipt:', err);
    }
}

async function viewPaymentReceipt(paymentId) {
    try {
        const data = await api.get('/finance/receipts?per_page=100');
        const receipt = data.receipts.find(r => r.payment_id === paymentId);
        if (receipt) {
            viewReceipt(receipt.id);
        } else {
            alert('No receipt found for this payment');
        }
    } catch (err) {
        console.error('Failed to find receipt:', err);
    }
}

function buildInvoiceHTML(inv, school) {
    return `
        <div class="print-document">
            <div class="print-header">
                ${school.logo_url ? `<img src="${school.logo_url}" alt="Logo" style="height: 60px; margin-bottom: 8px;">` : ''}
                <div class="print-school-name">${school.school_name || 'ClassMate Academy'}</div>
                <div class="print-school-motto">${school.motto || ''}</div>
                <div class="print-school-contact">
                    ${school.address || ''} | ${school.email || ''} | ${school.phone || ''}
                </div>
            </div>
            <div class="print-doc-title">Fee Invoice</div>
            <div class="print-info-grid">
                <div class="print-info-row">
                    <span class="print-info-label">Invoice No:</span>
                    <span>${inv.invoice_number}</span>
                </div>
                <div class="print-info-row">
                    <span class="print-info-label">Date:</span>
                    <span>${formatDate(inv.created_at)}</span>
                </div>
                <div class="print-info-row">
                    <span class="print-info-label">Student Name:</span>
                    <span>${inv.student_name || 'N/A'}</span>
                </div>
                <div class="print-info-row">
                    <span class="print-info-label">Adm. Number:</span>
                    <span>${inv.admission_number || 'N/A'}</span>
                </div>
                <div class="print-info-row">
                    <span class="print-info-label">Term:</span>
                    <span>${inv.term || 'N/A'}</span>
                </div>
                <div class="print-info-row">
                    <span class="print-info-label">Academic Year:</span>
                    <span>${inv.academic_year || 'N/A'}</span>
                </div>
            </div>
            <table class="print-table">
                <thead>
                    <tr>
                        <th>Description</th>
                        <th style="text-align: right;">Amount (KES)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>${inv.description || 'Fee invoice'}</td>
                        <td style="text-align: right;">${formatAmount(inv.amount)}</td>
                    </tr>
                </tbody>
            </table>
            <div class="print-total">
                Total: KES ${formatAmount(inv.amount)}
            </div>
            <div style="font-size: 13px; margin-bottom: 8px;">
                <strong>Balance Due: KES ${formatAmount(inv.balance)}</strong>
            </div>
            ${inv.due_date ? `<div style="font-size: 13px;">Due Date: ${formatDate(inv.due_date)}</div>` : ''}
            <div class="print-footer">
                <div class="print-signature">
                    <div class="print-signature-line"></div>
                    Finance Officer
                </div>
                <div class="print-signature">
                    <div class="print-signature-line"></div>
                    Principal
                </div>
            </div>
        </div>
    `;
}

function buildReceiptHTML(receipt, school) {
    return `
        <div class="print-document">
            <div class="print-header">
                ${school.logo_url ? `<img src="${school.logo_url}" alt="Logo" style="height: 60px; margin-bottom: 8px;">` : ''}
                <div class="print-school-name">${school.school_name || 'ClassMate Academy'}</div>
                <div class="print-school-motto">${school.motto || ''}</div>
                <div class="print-school-contact">
                    ${school.address || ''} | ${school.email || ''} | ${school.phone || ''}
                </div>
            </div>
            <div class="print-doc-title">Official Receipt</div>
            <div class="print-info-grid">
                <div class="print-info-row">
                    <span class="print-info-label">Receipt No:</span>
                    <span>${receipt.receipt_number}</span>
                </div>
                <div class="print-info-row">
                    <span class="print-info-label">Date:</span>
                    <span>${formatDate(receipt.created_at)}</span>
                </div>
                <div class="print-info-row">
                    <span class="print-info-label">Student Name:</span>
                    <span>${receipt.student_name || 'N/A'}</span>
                </div>
                <div class="print-info-row">
                    <span class="print-info-label">Adm. Number:</span>
                    <span>${receipt.admission_number || 'N/A'}</span>
                </div>
                <div class="print-info-row">
                    <span class="print-info-label">Payment Method:</span>
                    <span>${receipt.payment_method || 'N/A'}</span>
                </div>
                <div class="print-info-row">
                    <span class="print-info-label">Issued By:</span>
                    <span>${receipt.generated_by_name || 'N/A'}</span>
                </div>
            </div>
            <table class="print-table">
                <thead>
                    <tr>
                        <th>Description</th>
                        <th style="text-align: right;">Amount (KES)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>${receipt.description || 'Fee payment'}</td>
                        <td style="text-align: right;">${formatAmount(receipt.amount)}</td>
                    </tr>
                </tbody>
            </table>
            <div class="print-total">
                Amount Received: KES ${formatAmount(receipt.amount)}
            </div>
            <div class="print-footer">
                <div class="print-signature">
                    <div class="print-signature-line"></div>
                    Finance Officer
                </div>
                <div class="print-signature">
                    <div class="print-signature-line"></div>
                    Principal
                </div>
            </div>
        </div>
    `;
}

function showPrintDocument(title, html) {
    document.getElementById('printTitle').textContent = title;
    document.getElementById('printContent').innerHTML = html;
    document.getElementById('printOverlay').classList.add('active');
}

function closePrintModal() {
    document.getElementById('printOverlay').classList.remove('active');
}

async function showRecordPaymentModal() {
    let students = [];
    try {
        const data = await api.get('/students/?per_page=100');
        students = data.students || data || [];
    } catch (e) {
        console.error(e);
    }

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay active';
    overlay.innerHTML = `
        <div class="modal" style="max-width: 500px;">
            <div class="modal-header">
                <h3 class="modal-title">Record Payment</h3>
                <button class="btn btn-outline btn-sm close-modal"><i class="icon-x"></i></button>
            </div>
            <div class="modal-body">
                <form id="paymentForm">
                    <div class="form-group">
                        <label class="form-label">Student</label>
                        <select id="payStudentId" required style="width:100%;height:40px;border:1px solid var(--color-border);border-radius:var(--radius-md);padding:0 12px;font-family:var(--font-family);font-size:var(--font-size-sm);">
                            <option value="">Select student...</option>
                            ${students.map(s => `<option value="${s.id}">${s.full_name} (${s.admission_number})</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Amount (KES)</label>
                        <input type="number" id="payAmount" min="1" required style="width:100%;height:40px;border:1px solid var(--color-border);border-radius:var(--radius-md);padding:0 12px;font-family:var(--font-family);">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Payment Method</label>
                        <select id="payMethod" style="width:100%;height:40px;border:1px solid var(--color-border);border-radius:var(--radius-md);padding:0 12px;font-family:var(--font-family);font-size:var(--font-size-sm);">
                            <option value="cash">Cash</option>
                            <option value="bank_transfer">Bank Transfer</option>
                            <option value="cheque">Cheque</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Description</label>
                        <input type="text" id="payDescription" value="Fee payment" style="width:100%;height:40px;border:1px solid var(--color-border);border-radius:var(--radius-md);padding:0 12px;font-family:var(--font-family);">
                    </div>
                    <div style="display:flex;gap:12px;margin-top:20px;">
                        <button type="submit" class="btn btn-primary">Record Payment</button>
                        <button type="button" class="btn btn-outline close-modal">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    overlay.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', () => overlay.remove());
    });

    document.getElementById('paymentForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = e.target.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';

        try {
            await api.post('/finance/payments', {
                student_id: parseInt(document.getElementById('payStudentId').value),
                amount_paid: parseFloat(document.getElementById('payAmount').value),
                payment_method: document.getElementById('payMethod').value,
                description: document.getElementById('payDescription').value
            });
            overlay.remove();
            loadStats();
            loadPayments();
            loadReceipts();
        } catch (err) {
            console.error(err);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Record Payment';
        }
    });
}

async function showCreateInvoiceModal() {
    let students = [];
    try {
        const data = await api.get('/students/?per_page=100');
        students = data.students || data || [];
    } catch (e) {
        console.error(e);
    }

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay active';
    overlay.innerHTML = `
        <div class="modal" style="max-width: 500px;">
            <div class="modal-header">
                <h3 class="modal-title">Create Invoice</h3>
                <button class="btn btn-outline btn-sm close-modal"><i class="icon-x"></i></button>
            </div>
            <div class="modal-body">
                <form id="invoiceForm">
                    <div class="form-group">
                        <label class="form-label">Student</label>
                        <select id="invStudentId" required style="width:100%;height:40px;border:1px solid var(--color-border);border-radius:var(--radius-md);padding:0 12px;font-family:var(--font-family);font-size:var(--font-size-sm);">
                            <option value="">Select student...</option>
                            ${students.map(s => `<option value="${s.id}">${s.full_name} (${s.admission_number})</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Amount (KES)</label>
                        <input type="number" id="invAmount" min="1" required style="width:100%;height:40px;border:1px solid var(--color-border);border-radius:var(--radius-md);padding:0 12px;font-family:var(--font-family);">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Description</label>
                        <input type="text" id="invDescription" value="Tuition Fee" style="width:100%;height:40px;border:1px solid var(--color-border);border-radius:var(--radius-md);padding:0 12px;font-family:var(--font-family);">
                    </div>
                    <div class="form-row" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                        <div class="form-group">
                            <label class="form-label">Term</label>
                            <select id="invTerm" style="width:100%;height:40px;border:1px solid var(--color-border);border-radius:var(--radius-md);padding:0 12px;font-family:var(--font-family);font-size:var(--font-size-sm);">
                                <option value="Term 1">Term 1</option>
                                <option value="Term 2">Term 2</option>
                                <option value="Term 3">Term 3</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Academic Year</label>
                            <input type="text" id="invYear" value="2025" style="width:100%;height:40px;border:1px solid var(--color-border);border-radius:var(--radius-md);padding:0 12px;font-family:var(--font-family);">
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Due Date</label>
                        <input type="date" id="invDueDate" style="width:100%;height:40px;border:1px solid var(--color-border);border-radius:var(--radius-md);padding:0 12px;font-family:var(--font-family);">
                    </div>
                    <div style="display:flex;gap:12px;margin-top:20px;">
                        <button type="submit" class="btn btn-primary">Create Invoice</button>
                        <button type="button" class="btn btn-outline close-modal">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    overlay.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', () => overlay.remove());
    });

    document.getElementById('invoiceForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = e.target.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating...';

        try {
            await api.post('/finance/invoices', {
                student_id: parseInt(document.getElementById('invStudentId').value),
                amount: parseFloat(document.getElementById('invAmount').value),
                description: document.getElementById('invDescription').value,
                term: document.getElementById('invTerm').value,
                academic_year: document.getElementById('invYear').value,
                due_date: document.getElementById('invDueDate').value || null
            });
            overlay.remove();
            loadStats();
            loadInvoices();
        } catch (err) {
            console.error(err);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Invoice';
        }
    });
}

function formatKES(amount) {
    if (amount === null || amount === undefined) return 'KES 0';
    const num = Number(amount);
    if (num >= 1000000) {
        return `KES ${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
        return `KES ${num.toLocaleString()}`;
    }
    return `KES ${num}`;
}

function formatAmount(amount) {
    return Number(amount).toLocaleString('en-KE', { minimumFractionDigits: 0 });
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

function getInitials(name) {
    if (!name || name === 'N/A') return '?';
    return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

function getBadgeClass(method) {
    const map = { cash: 'warning', bank_transfer: 'info', cheque: 'info', mpesa: 'success' };
    return map[method] || 'info';
}

function getStatusBadge(status) {
    const map = { paid: 'success', unpaid: 'warning', partial: 'info', overdue: 'error' };
    return map[status] || 'info';
}
