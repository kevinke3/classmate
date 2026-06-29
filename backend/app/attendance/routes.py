from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import date, datetime, timedelta

from backend.app import db
from backend.app.models import Attendance, Student, User

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/mark', methods=['POST'])
@jwt_required()
def mark_attendance():
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'teacher']:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    records = data.get('records', [])
    attendance_date = data.get('date', date.today().isoformat())
    class_id = data.get('class_id')

    created = []
    for record in records:
        existing = Attendance.query.filter_by(
            student_id=record['student_id'],
            date=attendance_date
        ).first()

        if existing:
            existing.status = record['status']
            existing.remarks = record.get('remarks')
        else:
            attendance = Attendance(
                student_id=record['student_id'],
                class_id=class_id,
                date=attendance_date,
                status=record['status'],
                remarks=record.get('remarks'),
                marked_by=current_user_id
            )
            db.session.add(attendance)
            created.append(attendance)

    db.session.commit()

    return jsonify({
        'message': f'Attendance marked for {len(records)} students',
        'date': attendance_date
    }), 201


@attendance_bp.route('/class/<int:class_id>', methods=['GET'])
@jwt_required()
def get_class_attendance(class_id):
    attendance_date = request.args.get('date', date.today().isoformat())

    records = Attendance.query.filter_by(
        class_id=class_id,
        date=attendance_date
    ).all()

    return jsonify({
        'attendance': [r.to_dict() for r in records],
        'date': attendance_date
    }), 200


@attendance_bp.route('/student/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_attendance(student_id):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Attendance.query.filter_by(student_id=student_id)

    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)

    records = query.order_by(Attendance.date.desc()).all()

    total = len(records)
    present = sum(1 for r in records if r.status == 'present')
    absent = sum(1 for r in records if r.status == 'absent')
    late = sum(1 for r in records if r.status == 'late')

    return jsonify({
        'attendance': [r.to_dict() for r in records],
        'summary': {
            'total_days': total,
            'present': present,
            'absent': absent,
            'late': late,
            'percentage': round((present / total * 100), 1) if total > 0 else 0
        }
    }), 200


@attendance_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_attendance_stats():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    today_records = Attendance.query.filter_by(date=today).all()
    today_present = sum(1 for r in today_records if r.status == 'present')
    today_total = len(today_records)

    return jsonify({
        'today': {
            'total': today_total,
            'present': today_present,
            'absent': today_total - today_present,
            'percentage': round((today_present / today_total * 100), 1) if today_total > 0 else 0
        }
    }), 200
