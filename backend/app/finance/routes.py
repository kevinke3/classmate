from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, date
import uuid

from backend.app import db
from backend.app.models import (
    FeeStructure, FeeRecord, Student, Invoice, Receipt, SchoolSettings
)

finance_bp = Blueprint('finance', __name__)


def require_finance_access():
    claims = get_jwt()
    role = claims.get('role')
    if role not in ('admin', 'finance'):
        return False
    return True


@finance_bp.route('/fee-structures', methods=['GET'])
@jwt_required()
def get_fee_structures():
    structures = FeeStructure.query.all()
    return jsonify({'fee_structures': [f.to_dict() for f in structures]}), 200


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
        amount=data['amount'],
        description=data.get('description'),
        due_date=data.get('due_date')
    )
    db.session.add(structure)
    db.session.commit()

    return jsonify({'fee_structure': structure.to_dict()}), 201


@finance_bp.route('/payments', methods=['GET'])
@jwt_required()
def get_payments():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    student_id = request.args.get('student_id', type=int)

    query = FeeRecord.query

    if student_id:
        query = query.filter_by(student_id=student_id)

    pagination = query.order_by(FeeRecord.payment_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    payments = []
    for p in pagination.items:
        payment_data = p.to_dict()
        if p.student_id:
            student = Student.query.get(p.student_id)
            if student and student.user:
                payment_data['student_name'] = student.user.full_name
                payment_data['admission_number'] = student.admission_number
        payments.append(payment_data)

    return jsonify({
        'payments': payments,
        'total': pagination.total,
        'pages': pagination.pages
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

    receipt_num = f'RCP-{datetime.utcnow().strftime("%Y%m%d")}-{payment.id:04d}'
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

    invoices = Invoice.query.filter_by(
        student_id=data['student_id'], status='unpaid'
    ).order_by(Invoice.created_at.asc()).all()
    remaining = data['amount_paid']
    for inv in invoices:
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

    db.session.commit()

    return jsonify({
        'payment': payment.to_dict(),
        'receipt': receipt.to_dict()
    }), 201


@finance_bp.route('/invoices', methods=['GET'])
@jwt_required()
def get_invoices():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    student_id = request.args.get('student_id', type=int)
    status = request.args.get('status')

    query = Invoice.query
    if student_id:
        query = query.filter_by(student_id=student_id)
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'invoices': [inv.to_dict() for inv in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages
    }), 200


@finance_bp.route('/invoices', methods=['POST'])
@jwt_required()
def create_invoice():
    if not require_finance_access():
        return jsonify({'error': 'Finance access required'}), 403

    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    inv_num = f'INV-{datetime.utcnow().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}'

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


@finance_bp.route('/invoices/<int:invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    school = SchoolSettings.query.first()
    return jsonify({
        'invoice': invoice.to_dict(),
        'school': school.to_dict() if school else None
    }), 200


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


@finance_bp.route('/student-balance/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_balance(student_id):
    student = Student.query.get_or_404(student_id)

    total_invoiced = db.session.query(
        db.func.coalesce(db.func.sum(Invoice.amount), 0)
    ).filter_by(student_id=student_id).scalar()

    total_paid = db.session.query(
        db.func.coalesce(db.func.sum(FeeRecord.amount_paid), 0)
    ).filter_by(student_id=student_id, status='completed').scalar()

    outstanding = db.session.query(
        db.func.coalesce(db.func.sum(Invoice.balance), 0)
    ).filter(Invoice.student_id == student_id, Invoice.status != 'paid').scalar()

    return jsonify({
        'student_id': student_id,
        'student_name': student.user.full_name if student.user else None,
        'total_invoiced': float(total_invoiced),
        'total_paid': float(total_paid),
        'outstanding_balance': float(outstanding)
    }), 200


@finance_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_finance_stats():
    total_collected = db.session.query(
        db.func.coalesce(db.func.sum(FeeRecord.amount_paid), 0)
    ).filter_by(status='completed').scalar()

    total_payments = FeeRecord.query.filter_by(status='completed').count()

    total_outstanding = db.session.query(
        db.func.coalesce(db.func.sum(Invoice.balance), 0)
    ).filter(Invoice.status != 'paid').scalar()

    total_invoices = Invoice.query.count()

    return jsonify({
        'total_collected': float(total_collected),
        'total_payments': total_payments,
        'total_outstanding': float(total_outstanding),
        'total_invoices': total_invoices
    }), 200
