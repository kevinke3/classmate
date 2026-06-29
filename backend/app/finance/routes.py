from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract, and_, or_
import uuid

from backend.app import db
from backend.app.models import (
    FeeStructure, FeeRecord, Student, Invoice, Receipt, SchoolSettings, SchoolClass
)
from backend.app.finance.models import (
    FeeCategory, FeeComponent, Bursary, Penalty, Installment,
    ExpenseCategory, Expense, Income, FinanceNotification,
    BankAccount, FinanceSettings
)

finance_bp = Blueprint('finance', __name__)


def require_finance_access():
    claims = get_jwt()
    role = claims.get('role')
    if role not in ('admin', 'finance'):
        return False
    return True


# ============================================================
# DASHBOARD & ANALYTICS
# ============================================================

@finance_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Comprehensive finance dashboard with KPIs and analytics."""
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    # Approximate term/year start
    year_start = today.replace(month=1, day=1)

    # Collection KPIs
    collected_today = db.session.query(
        func.coalesce(func.sum(FeeRecord.amount_paid), 0)
    ).filter(
        FeeRecord.status == 'completed',
        func.date(FeeRecord.payment_date) == today
    ).scalar()

    collected_week = db.session.query(
        func.coalesce(func.sum(FeeRecord.amount_paid), 0)
    ).filter(
        FeeRecord.status == 'completed',
        func.date(FeeRecord.payment_date) >= week_start
    ).scalar()

    collected_month = db.session.query(
        func.coalesce(func.sum(FeeRecord.amount_paid), 0)
    ).filter(
        FeeRecord.status == 'completed',
        func.date(FeeRecord.payment_date) >= month_start
    ).scalar()

    collected_year = db.session.query(
        func.coalesce(func.sum(FeeRecord.amount_paid), 0)
    ).filter(
        FeeRecord.status == 'completed',
        func.date(FeeRecord.payment_date) >= year_start
    ).scalar()

    total_outstanding = db.session.query(
        func.coalesce(func.sum(Invoice.balance), 0)
    ).filter(Invoice.status != 'paid').scalar()

    total_expected = db.session.query(
        func.coalesce(func.sum(Invoice.amount), 0)
    ).scalar()

    total_collected = db.session.query(
        func.coalesce(func.sum(FeeRecord.amount_paid), 0)
    ).filter_by(status='completed').scalar()

    collection_rate = (float(total_collected) / float(total_expected) * 100) if total_expected > 0 else 0

    # Pending items
    pending_invoices = Invoice.query.filter(Invoice.status.in_(['unpaid', 'partial'])).count()
    overdue_invoices = Invoice.query.filter(
        Invoice.status != 'paid',
        Invoice.due_date < today
    ).count()

    total_payments = FeeRecord.query.filter_by(status='completed').count()
    total_invoices = Invoice.query.count()

    # Expenses total
    total_expenses = db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter_by(status='recorded').scalar()

    # Other income
    other_income = db.session.query(
        func.coalesce(func.sum(Income.amount), 0)
    ).scalar()

    # Recent transactions (last 10)
    recent_payments = FeeRecord.query.filter_by(status='completed').order_by(
        FeeRecord.payment_date.desc()
    ).limit(10).all()

    recent_transactions = []
    for p in recent_payments:
        student = Student.query.get(p.student_id)
        recent_transactions.append({
            'id': p.id,
            'student_name': student.full_name if student else 'Unknown',
            'admission_number': student.admission_number if student else '',
            'amount': p.amount_paid,
            'method': p.payment_method,
            'date': p.payment_date.isoformat() if p.payment_date else None,
            'reference': p.transaction_id
        })

    # Monthly revenue trend (last 6 months)
    monthly_revenue = []
    for i in range(5, -1, -1):
        m = today.replace(day=1) - timedelta(days=i * 30)
        month_total = db.session.query(
            func.coalesce(func.sum(FeeRecord.amount_paid), 0)
        ).filter(
            FeeRecord.status == 'completed',
            extract('month', FeeRecord.payment_date) == m.month,
            extract('year', FeeRecord.payment_date) == m.year
        ).scalar()
        monthly_revenue.append({
            'month': m.strftime('%b %Y'),
            'amount': float(month_total)
        })

    # Outstanding by class
    outstanding_by_class = []
    classes = SchoolClass.query.filter_by(is_active=True).all()
    for cls in classes:
        class_outstanding = db.session.query(
            func.coalesce(func.sum(Invoice.balance), 0)
        ).join(Student, Invoice.student_id == Student.id).filter(
            Student.class_id == cls.id,
            Invoice.status != 'paid'
        ).scalar()
        if class_outstanding > 0:
            outstanding_by_class.append({
                'class_name': cls.name,
                'amount': float(class_outstanding)
            })

    # Payment method distribution
    method_dist = db.session.query(
        FeeRecord.payment_method,
        func.sum(FeeRecord.amount_paid)
    ).filter_by(status='completed').group_by(FeeRecord.payment_method).all()

    payment_methods = [{'method': m[0] or 'Other', 'amount': float(m[1])} for m in method_dist]

    return jsonify({
        'kpis': {
            'collected_today': float(collected_today),
            'collected_week': float(collected_week),
            'collected_month': float(collected_month),
            'collected_year': float(collected_year),
            'total_outstanding': float(total_outstanding),
            'total_expected': float(total_expected),
            'total_collected': float(total_collected),
            'collection_rate': round(collection_rate, 1),
            'total_payments': total_payments,
            'total_invoices': total_invoices,
            'pending_invoices': pending_invoices,
            'overdue_invoices': overdue_invoices,
            'total_expenses': float(total_expenses),
            'other_income': float(other_income),
            'net_income': float(total_collected) + float(other_income) - float(total_expenses)
        },
        'recent_transactions': recent_transactions,
        'monthly_revenue': monthly_revenue,
        'outstanding_by_class': outstanding_by_class,
        'payment_methods': payment_methods
    }), 200


@finance_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_finance_stats():
    """Legacy stats endpoint for backward compatibility."""
    total_collected = db.session.query(
        func.coalesce(func.sum(FeeRecord.amount_paid), 0)
    ).filter_by(status='completed').scalar()
    total_payments = FeeRecord.query.filter_by(status='completed').count()
    total_outstanding = db.session.query(
        func.coalesce(func.sum(Invoice.balance), 0)
    ).filter(Invoice.status != 'paid').scalar()
    total_invoices = Invoice.query.count()

    return jsonify({
        'total_collected': float(total_collected),
        'total_payments': total_payments,
        'total_outstanding': float(total_outstanding),
        'total_invoices': total_invoices
    }), 200


# ============================================================
# FEE STRUCTURE MANAGEMENT
# ============================================================

@finance_bp.route('/fee-structures', methods=['GET'])
@jwt_required()
def get_fee_structures():
    structures = FeeStructure.query.order_by(FeeStructure.created_at.desc()).all()
    result = []
    for s in structures:
        data = s.to_dict()
        components = FeeComponent.query.filter_by(fee_structure_id=s.id).all()
        data['components'] = [c.to_dict() for c in components]
        data['total_amount'] = sum(c.amount for c in components) if components else s.amount
        result.append(data)
    return jsonify({'fee_structures': result}), 200


@finance_bp.route('/fee-structures', methods=['POST'])
@jwt_required()
def create_fee_structure():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    data = request.get_json()
    structure = FeeStructure(
        name=data['name'],
        class_id=data.get('class_id'),
        academic_year=data.get('academic_year'),
        term=data.get('term'),
        amount=data.get('amount', 0),
        description=data.get('description'),
        due_date=data.get('due_date')
    )
    db.session.add(structure)
    db.session.flush()

    # Add components if provided
    components = data.get('components', [])
    total = 0
    for comp in components:
        fc = FeeComponent(
            fee_structure_id=structure.id,
            category_id=comp['category_id'],
            amount=comp['amount'],
            is_optional=comp.get('is_optional', False),
            description=comp.get('description')
        )
        db.session.add(fc)
        total += comp['amount']

    if total > 0:
        structure.amount = total

    db.session.commit()

    result = structure.to_dict()
    result['components'] = [c.to_dict() for c in FeeComponent.query.filter_by(fee_structure_id=structure.id).all()]
    return jsonify({'fee_structure': result}), 201


@finance_bp.route('/fee-structures/<int:structure_id>', methods=['PUT'])
@jwt_required()
def update_fee_structure(structure_id):
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    structure = FeeStructure.query.get_or_404(structure_id)
    data = request.get_json()

    structure.name = data.get('name', structure.name)
    structure.class_id = data.get('class_id', structure.class_id)
    structure.academic_year = data.get('academic_year', structure.academic_year)
    structure.term = data.get('term', structure.term)
    structure.description = data.get('description', structure.description)
    structure.due_date = data.get('due_date', structure.due_date)

    # Replace components if provided
    if 'components' in data:
        FeeComponent.query.filter_by(fee_structure_id=structure.id).delete()
        total = 0
        for comp in data['components']:
            fc = FeeComponent(
                fee_structure_id=structure.id,
                category_id=comp['category_id'],
                amount=comp['amount'],
                is_optional=comp.get('is_optional', False),
                description=comp.get('description')
            )
            db.session.add(fc)
            total += comp['amount']
        structure.amount = total if total > 0 else data.get('amount', structure.amount)
    else:
        structure.amount = data.get('amount', structure.amount)

    db.session.commit()
    result = structure.to_dict()
    result['components'] = [c.to_dict() for c in FeeComponent.query.filter_by(fee_structure_id=structure.id).all()]
    return jsonify({'fee_structure': result}), 200


@finance_bp.route('/fee-structures/<int:structure_id>', methods=['DELETE'])
@jwt_required()
def delete_fee_structure(structure_id):
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    structure = FeeStructure.query.get_or_404(structure_id)
    FeeComponent.query.filter_by(fee_structure_id=structure.id).delete()
    db.session.delete(structure)
    db.session.commit()
    return jsonify({'message': 'Fee structure deleted'}), 200


# ============================================================
# FEE CATEGORIES
# ============================================================

@finance_bp.route('/fee-categories', methods=['GET'])
@jwt_required()
def get_fee_categories():
    categories = FeeCategory.query.filter_by(is_active=True).order_by(FeeCategory.sort_order).all()
    return jsonify({'categories': [c.to_dict() for c in categories]}), 200


@finance_bp.route('/fee-categories', methods=['POST'])
@jwt_required()
def create_fee_category():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    data = request.get_json()
    category = FeeCategory(
        name=data['name'],
        code=data['code'],
        description=data.get('description'),
        is_mandatory=data.get('is_mandatory', True),
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(category)
    db.session.commit()
    return jsonify({'category': category.to_dict()}), 201


# ============================================================
# PAYMENTS
# ============================================================

@finance_bp.route('/payments', methods=['GET'])
@jwt_required()
def get_payments():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    student_id = request.args.get('student_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    method = request.args.get('method')

    query = FeeRecord.query.filter_by(status='completed')

    if student_id:
        query = query.filter_by(student_id=student_id)
    if method:
        query = query.filter_by(payment_method=method)
    if date_from:
        query = query.filter(func.date(FeeRecord.payment_date) >= date_from)
    if date_to:
        query = query.filter(func.date(FeeRecord.payment_date) <= date_to)

    pagination = query.order_by(FeeRecord.payment_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    payments = []
    for p in pagination.items:
        payment_data = p.to_dict()
        student = Student.query.get(p.student_id)
        if student:
            payment_data['student_name'] = student.full_name
            payment_data['admission_number'] = student.admission_number
        payments.append(payment_data)

    return jsonify({
        'payments': payments,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@finance_bp.route('/payments', methods=['POST'])
@jwt_required()
def record_payment():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    payment = FeeRecord(
        student_id=data['student_id'],
        fee_structure_id=data.get('fee_structure_id'),
        amount_paid=data['amount_paid'],
        payment_method=data.get('payment_method', 'cash'),
        transaction_id=data.get('transaction_id') or f'TXN-{uuid.uuid4().hex[:8].upper()}',
        status='completed'
    )
    db.session.add(payment)
    db.session.flush()

    # Generate receipt
    settings = FinanceSettings.query.first()
    prefix = settings.receipt_prefix if settings else 'RCP'
    receipt_num = f'{prefix}-{datetime.utcnow().strftime("%Y%m%d")}-{payment.id:04d}'
    receipt = Receipt(
        receipt_number=receipt_num,
        payment_id=payment.id,
        student_id=data['student_id'],
        amount=data['amount_paid'],
        payment_method=data.get('payment_method', 'cash'),
        description=data.get('description', 'Fee payment'),
        generated_by=current_user_id
    )
    db.session.add(receipt)

    # Auto-apply to oldest unpaid invoices
    invoices = Invoice.query.filter_by(
        student_id=data['student_id'], status='unpaid'
    ).order_by(Invoice.created_at.asc()).all()

    partial_invoices = Invoice.query.filter_by(
        student_id=data['student_id'], status='partial'
    ).order_by(Invoice.created_at.asc()).all()

    all_invoices = partial_invoices + invoices
    remaining = data['amount_paid']
    for inv in all_invoices:
        if remaining <= 0:
            break
        if inv.balance <= remaining:
            remaining -= inv.balance
            inv.balance = 0
            inv.status = 'paid'
        else:
            inv.balance -= remaining
            inv.status = 'partial'
            remaining = 0

    # Create notification
    student = Student.query.get(data['student_id'])
    notif = FinanceNotification(
        student_id=data['student_id'],
        notification_type='payment_confirm',
        channel='system',
        subject=f'Payment of KES {data["amount_paid"]:,.0f} received',
        message=f'Payment received for {student.full_name if student else "student"}. Receipt: {receipt_num}',
        status='sent'
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({
        'payment': payment.to_dict(),
        'receipt': receipt.to_dict()
    }), 201


# ============================================================
# INVOICES
# ============================================================

@finance_bp.route('/invoices', methods=['GET'])
@jwt_required()
def get_invoices():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    student_id = request.args.get('student_id', type=int)
    status = request.args.get('status')
    class_id = request.args.get('class_id', type=int)

    query = Invoice.query
    if student_id:
        query = query.filter_by(student_id=student_id)
    if status:
        query = query.filter_by(status=status)
    if class_id:
        query = query.join(Student, Invoice.student_id == Student.id).filter(Student.class_id == class_id)

    pagination = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'invoices': [inv.to_dict() for inv in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@finance_bp.route('/invoices', methods=['POST'])
@jwt_required()
def create_invoice():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    settings = FinanceSettings.query.first()
    prefix = settings.invoice_prefix if settings else 'INV'
    inv_num = f'{prefix}-{datetime.utcnow().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}'

    due_date_val = None
    if data.get('due_date'):
        due_date_val = date.fromisoformat(data['due_date'])

    invoice = Invoice(
        invoice_number=inv_num,
        student_id=data['student_id'],
        fee_structure_id=data.get('fee_structure_id'),
        amount=data['amount'],
        balance=data['amount'],
        description=data.get('description', 'Fee invoice'),
        term=data.get('term'),
        academic_year=data.get('academic_year'),
        due_date=due_date_val,
        status='unpaid',
        created_by=current_user_id
    )
    db.session.add(invoice)
    db.session.commit()

    return jsonify({'invoice': invoice.to_dict()}), 201


@finance_bp.route('/invoices/bulk', methods=['POST'])
@jwt_required()
def create_bulk_invoices():
    """Create invoices for an entire class or custom group."""
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    data = request.get_json()
    current_user_id = int(get_jwt_identity())
    class_id = data.get('class_id')
    student_ids = data.get('student_ids', [])

    if class_id:
        students = Student.query.filter_by(class_id=class_id, status='active').all()
        student_ids = [s.id for s in students]

    settings = FinanceSettings.query.first()
    prefix = settings.invoice_prefix if settings else 'INV'
    due_date_val = date.fromisoformat(data['due_date']) if data.get('due_date') else None

    created = []
    for sid in student_ids:
        inv_num = f'{prefix}-{datetime.utcnow().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}'
        invoice = Invoice(
            invoice_number=inv_num,
            student_id=sid,
            fee_structure_id=data.get('fee_structure_id'),
            amount=data['amount'],
            balance=data['amount'],
            description=data.get('description', 'Fee invoice'),
            term=data.get('term'),
            academic_year=data.get('academic_year'),
            due_date=due_date_val,
            status='unpaid',
            created_by=current_user_id
        )
        db.session.add(invoice)
        created.append(invoice)

    db.session.commit()
    return jsonify({
        'message': f'{len(created)} invoices created',
        'count': len(created)
    }), 201


@finance_bp.route('/invoices/<int:invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    school = SchoolSettings.query.first()
    return jsonify({
        'invoice': invoice.to_dict(),
        'school': school.to_dict() if school else None
    }), 200


# ============================================================
# RECEIPTS
# ============================================================

@finance_bp.route('/receipts', methods=['GET'])
@jwt_required()
def get_receipts():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    student_id = request.args.get('student_id', type=int)

    query = Receipt.query
    if student_id:
        query = query.filter_by(student_id=student_id)

    pagination = query.order_by(Receipt.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'receipts': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages
    }), 200


@finance_bp.route('/receipts/<int:receipt_id>', methods=['GET'])
@jwt_required()
def get_receipt(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)
    school = SchoolSettings.query.first()
    return jsonify({
        'receipt': receipt.to_dict(),
        'school': school.to_dict() if school else None
    }), 200


# ============================================================
# STUDENT FINANCIAL PROFILES
# ============================================================

@finance_bp.route('/student-balance/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_balance(student_id):
    student = Student.query.get_or_404(student_id)

    total_invoiced = db.session.query(
        func.coalesce(func.sum(Invoice.amount), 0)
    ).filter_by(student_id=student_id).scalar()

    total_paid = db.session.query(
        func.coalesce(func.sum(FeeRecord.amount_paid), 0)
    ).filter_by(student_id=student_id, status='completed').scalar()

    outstanding = db.session.query(
        func.coalesce(func.sum(Invoice.balance), 0)
    ).filter(Invoice.student_id == student_id, Invoice.status != 'paid').scalar()

    # Bursaries/discounts
    total_bursary = db.session.query(
        func.coalesce(func.sum(Bursary.amount), 0)
    ).filter_by(student_id=student_id, status='active').scalar()

    # Penalties
    total_penalties = db.session.query(
        func.coalesce(func.sum(Penalty.amount), 0)
    ).filter_by(student_id=student_id, is_waived=False).scalar()

    return jsonify({
        'student_id': student_id,
        'student_name': student.full_name,
        'admission_number': student.admission_number,
        'class_name': student.school_class.name if student.school_class else None,
        'total_invoiced': float(total_invoiced),
        'total_paid': float(total_paid),
        'outstanding_balance': float(outstanding),
        'total_bursary': float(total_bursary),
        'total_penalties': float(total_penalties),
        'net_balance': float(outstanding) + float(total_penalties) - float(total_bursary)
    }), 200


@finance_bp.route('/student-profile/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_financial_profile(student_id):
    """Full financial profile for a student."""
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    student = Student.query.get_or_404(student_id)

    # Balance info
    total_invoiced = db.session.query(
        func.coalesce(func.sum(Invoice.amount), 0)
    ).filter_by(student_id=student_id).scalar()

    total_paid = db.session.query(
        func.coalesce(func.sum(FeeRecord.amount_paid), 0)
    ).filter_by(student_id=student_id, status='completed').scalar()

    outstanding = db.session.query(
        func.coalesce(func.sum(Invoice.balance), 0)
    ).filter(Invoice.student_id == student_id, Invoice.status != 'paid').scalar()

    # Payment history
    payments = FeeRecord.query.filter_by(
        student_id=student_id, status='completed'
    ).order_by(FeeRecord.payment_date.desc()).limit(50).all()

    # Invoices
    invoices = Invoice.query.filter_by(student_id=student_id).order_by(Invoice.created_at.desc()).limit(50).all()

    # Receipts
    receipts = Receipt.query.filter_by(student_id=student_id).order_by(Receipt.created_at.desc()).limit(50).all()

    # Bursaries
    bursaries = Bursary.query.filter_by(student_id=student_id).all()

    # Penalties
    penalties = Penalty.query.filter_by(student_id=student_id).all()

    # Installments
    installments = Installment.query.filter_by(student_id=student_id).all()

    return jsonify({
        'student': {
            'id': student.id,
            'full_name': student.full_name,
            'admission_number': student.admission_number,
            'class_name': student.school_class.name if student.school_class else None
        },
        'balance': {
            'total_invoiced': float(total_invoiced),
            'total_paid': float(total_paid),
            'outstanding': float(outstanding)
        },
        'payments': [p.to_dict() for p in payments],
        'invoices': [i.to_dict() for i in invoices],
        'receipts': [r.to_dict() for r in receipts],
        'bursaries': [b.to_dict() for b in bursaries],
        'penalties': [p.to_dict() for p in penalties],
        'installments': [i.to_dict() for i in installments]
    }), 200


@finance_bp.route('/student-statement/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_statement(student_id):
    """Generate financial statement for a student."""
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    student = Student.query.get_or_404(student_id)
    academic_year = request.args.get('academic_year')
    term = request.args.get('term')

    # Get all transactions
    inv_query = Invoice.query.filter_by(student_id=student_id)
    pay_query = FeeRecord.query.filter_by(student_id=student_id, status='completed')

    if academic_year:
        inv_query = inv_query.filter_by(academic_year=academic_year)
    if term:
        inv_query = inv_query.filter_by(term=term)

    invoices = inv_query.order_by(Invoice.created_at.asc()).all()
    payments = pay_query.order_by(FeeRecord.payment_date.asc()).all()

    # Build statement entries
    entries = []
    running_balance = 0
    for inv in invoices:
        running_balance += inv.amount
        entries.append({
            'date': inv.created_at.isoformat() if inv.created_at else None,
            'type': 'invoice',
            'description': inv.description or f'Invoice {inv.invoice_number}',
            'debit': inv.amount,
            'credit': 0,
            'balance': running_balance,
            'reference': inv.invoice_number
        })

    for pay in payments:
        running_balance -= pay.amount_paid
        entries.append({
            'date': pay.payment_date.isoformat() if pay.payment_date else None,
            'type': 'payment',
            'description': f'Payment - {pay.payment_method}',
            'debit': 0,
            'credit': pay.amount_paid,
            'balance': running_balance,
            'reference': pay.transaction_id
        })

    # Sort by date
    entries.sort(key=lambda x: x['date'] or '')

    # Recalculate running balance in order
    balance = 0
    for e in entries:
        balance += e['debit'] - e['credit']
        e['balance'] = balance

    school = SchoolSettings.query.first()

    return jsonify({
        'student': {
            'id': student.id,
            'full_name': student.full_name,
            'admission_number': student.admission_number,
            'class_name': student.school_class.name if student.school_class else None
        },
        'school': school.to_dict() if school else None,
        'entries': entries,
        'summary': {
            'total_debits': sum(e['debit'] for e in entries),
            'total_credits': sum(e['credit'] for e in entries),
            'closing_balance': balance
        },
        'filters': {
            'academic_year': academic_year,
            'term': term
        }
    }), 200


# ============================================================
# REPORTS
# ============================================================

@finance_bp.route('/reports/collection', methods=['GET'])
@jwt_required()
def collection_report():
    """Collection report by period."""
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    period = request.args.get('period', 'daily')  # daily, weekly, monthly, termly, annual
    class_id = request.args.get('class_id', type=int)
    today = date.today()

    if period == 'daily':
        start = today
    elif period == 'weekly':
        start = today - timedelta(days=today.weekday())
    elif period == 'monthly':
        start = today.replace(day=1)
    elif period == 'termly':
        start = today.replace(day=1) - timedelta(days=90)
    else:
        start = today.replace(month=1, day=1)

    query = db.session.query(
        FeeRecord.student_id,
        func.sum(FeeRecord.amount_paid).label('total_paid')
    ).filter(
        FeeRecord.status == 'completed',
        func.date(FeeRecord.payment_date) >= start
    )

    if class_id:
        query = query.join(Student, FeeRecord.student_id == Student.id).filter(Student.class_id == class_id)

    results = query.group_by(FeeRecord.student_id).all()

    total_collected = sum(r.total_paid for r in results)
    student_count = len(results)

    # Per-class breakdown
    class_breakdown = []
    classes = SchoolClass.query.filter_by(is_active=True).all()
    for cls in classes:
        cls_total = db.session.query(
            func.coalesce(func.sum(FeeRecord.amount_paid), 0)
        ).join(Student, FeeRecord.student_id == Student.id).filter(
            Student.class_id == cls.id,
            FeeRecord.status == 'completed',
            func.date(FeeRecord.payment_date) >= start
        ).scalar()

        cls_expected = db.session.query(
            func.coalesce(func.sum(Invoice.amount), 0)
        ).join(Student, Invoice.student_id == Student.id).filter(
            Student.class_id == cls.id
        ).scalar()

        class_breakdown.append({
            'class_name': cls.name,
            'collected': float(cls_total),
            'expected': float(cls_expected),
            'rate': round(float(cls_total) / float(cls_expected) * 100, 1) if cls_expected > 0 else 0
        })

    return jsonify({
        'period': period,
        'start_date': start.isoformat(),
        'total_collected': float(total_collected),
        'paying_students': student_count,
        'class_breakdown': class_breakdown
    }), 200


@finance_bp.route('/reports/arrears', methods=['GET'])
@jwt_required()
def arrears_report():
    """Students with outstanding balances."""
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    class_id = request.args.get('class_id', type=int)
    min_amount = request.args.get('min_amount', 0, type=float)

    query = db.session.query(
        Student.id,
        Student.first_name,
        Student.last_name,
        Student.admission_number,
        Student.class_id,
        func.coalesce(func.sum(Invoice.balance), 0).label('outstanding')
    ).join(Invoice, Invoice.student_id == Student.id).filter(
        Invoice.status != 'paid'
    ).group_by(Student.id).having(
        func.sum(Invoice.balance) > min_amount
    ).order_by(func.sum(Invoice.balance).desc())

    if class_id:
        query = query.filter(Student.class_id == class_id)

    results = query.all()

    arrears = []
    for r in results:
        cls = SchoolClass.query.get(r.class_id) if r.class_id else None
        arrears.append({
            'student_id': r.id,
            'student_name': f'{r.first_name} {r.last_name}'.strip(),
            'admission_number': r.admission_number,
            'class_name': cls.name if cls else 'N/A',
            'outstanding': float(r.outstanding)
        })

    return jsonify({
        'arrears': arrears,
        'total_outstanding': sum(a['outstanding'] for a in arrears),
        'student_count': len(arrears)
    }), 200


@finance_bp.route('/reports/fully-paid', methods=['GET'])
@jwt_required()
def fully_paid_report():
    """Students who have fully paid their fees."""
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    class_id = request.args.get('class_id', type=int)

    # Students with no outstanding invoices
    subq = db.session.query(Invoice.student_id).filter(Invoice.status != 'paid').subquery()

    query = Student.query.filter(
        Student.status == 'active',
        ~Student.id.in_(db.session.query(subq.c.student_id))
    )

    if class_id:
        query = query.filter_by(class_id=class_id)

    students = query.all()
    result = []
    for s in students:
        total_paid = db.session.query(
            func.coalesce(func.sum(FeeRecord.amount_paid), 0)
        ).filter_by(student_id=s.id, status='completed').scalar()
        result.append({
            'student_id': s.id,
            'student_name': s.full_name,
            'admission_number': s.admission_number,
            'class_name': s.school_class.name if s.school_class else 'N/A',
            'total_paid': float(total_paid)
        })

    return jsonify({'students': result, 'count': len(result)}), 200


# ============================================================
# EXPENSES & INCOME
# ============================================================

@finance_bp.route('/expenses', methods=['GET'])
@jwt_required()
def get_expenses():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = Expense.query.order_by(Expense.expense_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'expenses': [e.to_dict() for e in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages
    }), 200


@finance_bp.route('/expenses', methods=['POST'])
@jwt_required()
def record_expense():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    expense = Expense(
        category_id=data['category_id'],
        amount=data['amount'],
        description=data['description'],
        reference_number=data.get('reference_number'),
        vendor=data.get('vendor'),
        payment_method=data.get('payment_method', 'cash'),
        expense_date=date.fromisoformat(data['expense_date']) if data.get('expense_date') else date.today(),
        academic_year=data.get('academic_year'),
        term=data.get('term'),
        recorded_by=current_user_id,
        status='recorded'
    )
    db.session.add(expense)
    db.session.commit()
    return jsonify({'expense': expense.to_dict()}), 201


@finance_bp.route('/expense-categories', methods=['GET'])
@jwt_required()
def get_expense_categories():
    categories = ExpenseCategory.query.filter_by(is_active=True).all()
    return jsonify({'categories': [c.to_dict() for c in categories]}), 200


@finance_bp.route('/expense-categories', methods=['POST'])
@jwt_required()
def create_expense_category():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    data = request.get_json()
    cat = ExpenseCategory(
        name=data['name'],
        code=data['code'],
        description=data.get('description'),
        budget_limit=data.get('budget_limit')
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify({'category': cat.to_dict()}), 201


@finance_bp.route('/income', methods=['GET'])
@jwt_required()
def get_income():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = Income.query.order_by(Income.income_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'income': [i.to_dict() for i in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages
    }), 200


@finance_bp.route('/income', methods=['POST'])
@jwt_required()
def record_income():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    income = Income(
        source=data['source'],
        amount=data['amount'],
        description=data.get('description'),
        income_type=data.get('income_type', 'other'),
        reference_number=data.get('reference_number'),
        income_date=date.fromisoformat(data['income_date']) if data.get('income_date') else date.today(),
        academic_year=data.get('academic_year'),
        term=data.get('term'),
        recorded_by=current_user_id
    )
    db.session.add(income)
    db.session.commit()
    return jsonify({'income': income.to_dict()}), 201


# ============================================================
# BURSARIES & SCHOLARSHIPS
# ============================================================

@finance_bp.route('/bursaries', methods=['GET'])
@jwt_required()
def get_bursaries():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    student_id = request.args.get('student_id', type=int)
    query = Bursary.query
    if student_id:
        query = query.filter_by(student_id=student_id)

    bursaries = query.order_by(Bursary.created_at.desc()).all()
    return jsonify({'bursaries': [b.to_dict() for b in bursaries]}), 200


@finance_bp.route('/bursaries', methods=['POST'])
@jwt_required()
def create_bursary():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    bursary = Bursary(
        student_id=data['student_id'],
        name=data['name'],
        bursary_type=data.get('bursary_type', 'bursary'),
        amount=data['amount'],
        percentage=data.get('percentage'),
        academic_year=data.get('academic_year'),
        term=data.get('term'),
        reason=data.get('reason'),
        approved_by=current_user_id,
        status='active',
        start_date=date.fromisoformat(data['start_date']) if data.get('start_date') else date.today(),
        end_date=date.fromisoformat(data['end_date']) if data.get('end_date') else None
    )
    db.session.add(bursary)
    db.session.commit()
    return jsonify({'bursary': bursary.to_dict()}), 201


# ============================================================
# NOTIFICATIONS
# ============================================================

@finance_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_finance_notifications():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = FinanceNotification.query.order_by(
        FinanceNotification.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'notifications': [n.to_dict() for n in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages
    }), 200


@finance_bp.route('/notifications/send-reminder', methods=['POST'])
@jwt_required()
def send_fee_reminder():
    """Send fee reminder to students with outstanding balances."""
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    data = request.get_json()
    student_ids = data.get('student_ids', [])
    message = data.get('message', 'This is a reminder about your outstanding fee balance. Please make payment at your earliest convenience.')

    sent = 0
    for sid in student_ids:
        student = Student.query.get(sid)
        if not student:
            continue

        outstanding = db.session.query(
            func.coalesce(func.sum(Invoice.balance), 0)
        ).filter(Invoice.student_id == sid, Invoice.status != 'paid').scalar()

        notif = FinanceNotification(
            student_id=sid,
            notification_type='reminder',
            channel='system',
            subject=f'Fee Reminder - Outstanding Balance: KES {float(outstanding):,.0f}',
            message=message,
            status='sent'
        )
        db.session.add(notif)
        sent += 1

    db.session.commit()
    return jsonify({'message': f'{sent} reminders sent', 'count': sent}), 200


# ============================================================
# FINANCE SETTINGS
# ============================================================

@finance_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_finance_settings():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    settings = FinanceSettings.query.first()
    if not settings:
        settings = FinanceSettings()
        db.session.add(settings)
        db.session.commit()

    bank_accounts = BankAccount.query.filter_by(is_active=True).all()

    return jsonify({
        'settings': settings.to_dict(),
        'bank_accounts': [b.to_dict() for b in bank_accounts]
    }), 200


@finance_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_finance_settings():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    settings = FinanceSettings.query.first()
    if not settings:
        settings = FinanceSettings()
        db.session.add(settings)

    data = request.get_json()
    for field in ['currency', 'currency_symbol', 'tax_rate', 'late_penalty_rate',
                  'late_penalty_type', 'grace_period_days', 'auto_penalty',
                  'auto_reminder', 'reminder_days_before', 'receipt_prefix',
                  'invoice_prefix', 'receipt_footer_text', 'invoice_footer_text']:
        if field in data:
            setattr(settings, field, data[field])

    if 'payment_methods' in data:
        if isinstance(data['payment_methods'], list):
            settings.payment_methods = ','.join(data['payment_methods'])
        else:
            settings.payment_methods = data['payment_methods']

    db.session.commit()
    return jsonify({'settings': settings.to_dict()}), 200


@finance_bp.route('/bank-accounts', methods=['GET'])
@jwt_required()
def get_bank_accounts():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403
    accounts = BankAccount.query.filter_by(is_active=True).all()
    return jsonify({'accounts': [a.to_dict() for a in accounts]}), 200


@finance_bp.route('/bank-accounts', methods=['POST'])
@jwt_required()
def create_bank_account():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    data = request.get_json()
    account = BankAccount(
        bank_name=data['bank_name'],
        account_name=data['account_name'],
        account_number=data['account_number'],
        branch=data.get('branch'),
        swift_code=data.get('swift_code'),
        is_primary=data.get('is_primary', False)
    )
    db.session.add(account)
    db.session.commit()
    return jsonify({'account': account.to_dict()}), 201
