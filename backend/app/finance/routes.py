from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import requests
import base64
from datetime import datetime

from backend.app import db
from backend.app.models import FeeStructure, FeeRecord, Student

finance_bp = Blueprint('finance', __name__)


@finance_bp.route('/fee-structures', methods=['GET'])
@jwt_required()
def get_fee_structures():
    structures = FeeStructure.query.all()
    return jsonify({'fee_structures': [f.to_dict() for f in structures]}), 200


@finance_bp.route('/fee-structures', methods=['POST'])
@jwt_required()
def create_fee_structure():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

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
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    student_id = request.args.get('student_id', type=int)

    query = FeeRecord.query

    if student_id:
        query = query.filter_by(student_id=student_id)

    pagination = query.order_by(FeeRecord.payment_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'payments': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages
    }), 200


@finance_bp.route('/payments', methods=['POST'])
@jwt_required()
def record_payment():
    data = request.get_json()

    payment = FeeRecord(
        student_id=data['student_id'],
        fee_structure_id=data.get('fee_structure_id'),
        amount_paid=data['amount_paid'],
        payment_method=data.get('payment_method', 'cash'),
        transaction_id=data.get('transaction_id'),
        mpesa_receipt=data.get('mpesa_receipt')
    )
    db.session.add(payment)
    db.session.commit()

    return jsonify({'payment': payment.to_dict()}), 201


@finance_bp.route('/mpesa/stk-push', methods=['POST'])
@jwt_required()
def mpesa_stk_push():
    from flask import current_app

    data = request.get_json()
    phone = data.get('phone')
    amount = data.get('amount')
    student_id = data.get('student_id')

    consumer_key = current_app.config.get('MPESA_CONSUMER_KEY')
    consumer_secret = current_app.config.get('MPESA_CONSUMER_SECRET')

    if not consumer_key or not consumer_secret:
        return jsonify({'error': 'M-Pesa not configured'}), 503

    auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    auth_response = requests.get(auth_url, auth=(consumer_key, consumer_secret))

    if auth_response.status_code != 200:
        return jsonify({'error': 'Failed to authenticate with M-Pesa'}), 503

    access_token = auth_response.json().get('access_token')
    shortcode = current_app.config.get('MPESA_SHORTCODE')
    passkey = current_app.config.get('MPESA_PASSKEY')
    callback_url = current_app.config.get('MPESA_CALLBACK_URL')

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(
        f'{shortcode}{passkey}{timestamp}'.encode()
    ).decode()

    payload = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(amount),
        'PartyA': phone,
        'PartyB': shortcode,
        'PhoneNumber': phone,
        'CallBackURL': callback_url,
        'AccountReference': f'ClassMate-{student_id}',
        'TransactionDesc': 'Fee Payment'
    }

    stk_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.post(stk_url, json=payload, headers=headers)

    return jsonify(response.json()), response.status_code


@finance_bp.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json()

    result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
    if result_code == 0:
        metadata = data['Body']['stkCallback']['CallbackMetadata']['Item']
        amount = next(i['Value'] for i in metadata if i['Name'] == 'Amount')
        receipt = next(i['Value'] for i in metadata if i['Name'] == 'MpesaReceiptNumber')
        phone = next(i['Value'] for i in metadata if i['Name'] == 'PhoneNumber')

        payment = FeeRecord(
            amount_paid=amount,
            payment_method='mpesa',
            mpesa_receipt=receipt,
            transaction_id=receipt,
            status='completed'
        )
        db.session.add(payment)
        db.session.commit()

    return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200


@finance_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_finance_stats():
    total_collected = db.session.query(
        db.func.sum(FeeRecord.amount_paid)
    ).filter_by(status='completed').scalar() or 0

    total_payments = FeeRecord.query.filter_by(status='completed').count()

    return jsonify({
        'total_collected': float(total_collected),
        'total_payments': total_payments
    }), 200
