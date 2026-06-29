"""Enhanced finance models for comprehensive school financial management."""
from datetime import datetime
from backend.app import db


class FeeCategory(db.Model):
    """Fee categories like Tuition, Boarding, Transport, etc."""
    __tablename__ = 'fee_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_mandatory = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'is_mandatory': self.is_mandatory,
            'is_active': self.is_active,
            'sort_order': self.sort_order
        }


class FeeComponent(db.Model):
    """Individual fee components within a fee structure."""
    __tablename__ = 'fee_components'

    id = db.Column(db.Integer, primary_key=True)
    fee_structure_id = db.Column(db.Integer, db.ForeignKey('fee_structures.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('fee_categories.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    is_optional = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)

    category = db.relationship('FeeCategory', backref='components')

    def to_dict(self):
        return {
            'id': self.id,
            'fee_structure_id': self.fee_structure_id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'category_code': self.category.code if self.category else None,
            'amount': self.amount,
            'is_optional': self.is_optional,
            'description': self.description
        }


class Bursary(db.Model):
    """Bursary/scholarship/discount applied to a student."""
    __tablename__ = 'bursaries'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    bursary_type = db.Column(db.String(30), default='bursary')  # bursary, scholarship, discount
    amount = db.Column(db.Float, nullable=False)
    percentage = db.Column(db.Float)  # alternative to fixed amount
    academic_year = db.Column(db.String(20))
    term = db.Column(db.String(20))
    reason = db.Column(db.Text)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='active')  # active, expired, revoked
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='bursaries')
    approver = db.relationship('User', backref='approved_bursaries')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'name': self.name,
            'bursary_type': self.bursary_type,
            'amount': self.amount,
            'percentage': self.percentage,
            'academic_year': self.academic_year,
            'term': self.term,
            'reason': self.reason,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Penalty(db.Model):
    """Late payment penalties or fines."""
    __tablename__ = 'penalties'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    is_waived = db.Column(db.Boolean, default=False)
    waived_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    waived_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='penalties')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'amount': self.amount,
            'reason': self.reason,
            'is_waived': self.is_waived,
            'waived_reason': self.waived_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Installment(db.Model):
    """Fee installment plan for a student."""
    __tablename__ = 'installments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    total_amount = db.Column(db.Float, nullable=False)
    num_installments = db.Column(db.Integer, nullable=False)
    amount_per_installment = db.Column(db.Float, nullable=False)
    paid_installments = db.Column(db.Integer, default=0)
    next_due_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active, completed, defaulted
    academic_year = db.Column(db.String(20))
    term = db.Column(db.String(20))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='installments')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'total_amount': self.total_amount,
            'num_installments': self.num_installments,
            'amount_per_installment': self.amount_per_installment,
            'paid_installments': self.paid_installments,
            'next_due_date': self.next_due_date.isoformat() if self.next_due_date else None,
            'status': self.status,
            'academic_year': self.academic_year,
            'term': self.term,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ExpenseCategory(db.Model):
    """Categories for school expenses."""
    __tablename__ = 'expense_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    budget_limit = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'budget_limit': self.budget_limit,
            'is_active': self.is_active
        }


class Expense(db.Model):
    """School expenses tracking."""
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    reference_number = db.Column(db.String(50))
    vendor = db.Column(db.String(200))
    payment_method = db.Column(db.String(50))
    receipt_url = db.Column(db.String(500))
    expense_date = db.Column(db.Date, default=datetime.utcnow)
    academic_year = db.Column(db.String(20))
    term = db.Column(db.String(20))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='recorded')  # recorded, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship('ExpenseCategory', backref='expenses')
    recorder = db.relationship('User', foreign_keys=[recorded_by], backref='recorded_expenses')

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'amount': self.amount,
            'description': self.description,
            'reference_number': self.reference_number,
            'vendor': self.vendor,
            'payment_method': self.payment_method,
            'expense_date': self.expense_date.isoformat() if self.expense_date else None,
            'academic_year': self.academic_year,
            'term': self.term,
            'status': self.status,
            'recorded_by_name': self.recorder.full_name if self.recorder else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Income(db.Model):
    """Non-fee income (donations, grants, etc.)."""
    __tablename__ = 'incomes'

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    income_type = db.Column(db.String(50))  # donation, grant, rental, other
    reference_number = db.Column(db.String(50))
    income_date = db.Column(db.Date, default=datetime.utcnow)
    academic_year = db.Column(db.String(20))
    term = db.Column(db.String(20))
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recorder = db.relationship('User', backref='recorded_incomes')

    def to_dict(self):
        return {
            'id': self.id,
            'source': self.source,
            'amount': self.amount,
            'description': self.description,
            'income_type': self.income_type,
            'reference_number': self.reference_number,
            'income_date': self.income_date.isoformat() if self.income_date else None,
            'academic_year': self.academic_year,
            'term': self.term,
            'recorded_by_name': self.recorder.full_name if self.recorder else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class FinanceNotification(db.Model):
    """Finance-specific notification logs."""
    __tablename__ = 'finance_notifications'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.id'))
    notification_type = db.Column(db.String(50), nullable=False)  # payment_confirm, receipt, overdue, reminder
    channel = db.Column(db.String(20), default='system')  # sms, email, system
    subject = db.Column(db.String(200))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='sent')  # pending, sent, failed, read
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='finance_notifications')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'notification_type': self.notification_type,
            'channel': self.channel,
            'subject': self.subject,
            'message': self.message,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class BankAccount(db.Model):
    """School bank accounts for payment processing."""
    __tablename__ = 'bank_accounts'

    id = db.Column(db.Integer, primary_key=True)
    bank_name = db.Column(db.String(100), nullable=False)
    account_name = db.Column(db.String(200), nullable=False)
    account_number = db.Column(db.String(50), nullable=False)
    branch = db.Column(db.String(100))
    swift_code = db.Column(db.String(20))
    is_primary = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'bank_name': self.bank_name,
            'account_name': self.account_name,
            'account_number': self.account_number,
            'branch': self.branch,
            'swift_code': self.swift_code,
            'is_primary': self.is_primary,
            'is_active': self.is_active
        }


class FinanceSettings(db.Model):
    """Finance module configuration."""
    __tablename__ = 'finance_settings'

    id = db.Column(db.Integer, primary_key=True)
    currency = db.Column(db.String(10), default='KES')
    currency_symbol = db.Column(db.String(5), default='KES')
    tax_rate = db.Column(db.Float, default=0)
    late_penalty_rate = db.Column(db.Float, default=0)
    late_penalty_type = db.Column(db.String(20), default='fixed')  # fixed, percentage
    grace_period_days = db.Column(db.Integer, default=14)
    auto_penalty = db.Column(db.Boolean, default=False)
    auto_reminder = db.Column(db.Boolean, default=True)
    reminder_days_before = db.Column(db.Integer, default=7)
    receipt_prefix = db.Column(db.String(10), default='RCP')
    invoice_prefix = db.Column(db.String(10), default='INV')
    receipt_footer_text = db.Column(db.Text)
    invoice_footer_text = db.Column(db.Text)
    payment_methods = db.Column(db.Text, default='cash,bank_transfer,cheque,mobile_money')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'currency': self.currency,
            'currency_symbol': self.currency_symbol,
            'tax_rate': self.tax_rate,
            'late_penalty_rate': self.late_penalty_rate,
            'late_penalty_type': self.late_penalty_type,
            'grace_period_days': self.grace_period_days,
            'auto_penalty': self.auto_penalty,
            'auto_reminder': self.auto_reminder,
            'reminder_days_before': self.reminder_days_before,
            'receipt_prefix': self.receipt_prefix,
            'invoice_prefix': self.invoice_prefix,
            'receipt_footer_text': self.receipt_footer_text,
            'invoice_footer_text': self.invoice_footer_text,
            'payment_methods': self.payment_methods.split(',') if self.payment_methods else [],
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
