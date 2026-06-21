from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from datetime import date, timedelta

from backend.app import db
from backend.app.models import (
    Student, Teacher, User, Attendance, FeeRecord,
    Grade, SchoolClass, Examination
)

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    total_students = Student.query.filter_by(status='active').count()
    total_teachers = Teacher.query.filter_by(status='active').count()
    total_classes = SchoolClass.query.filter_by(is_active=True).count()

    total_revenue = db.session.query(
        db.func.sum(FeeRecord.amount_paid)
    ).filter_by(status='completed').scalar() or 0

    today = date.today()
    today_attendance = Attendance.query.filter_by(date=today).all()
    present_today = sum(1 for a in today_attendance if a.status == 'present')
    attendance_rate = round(
        (present_today / len(today_attendance) * 100), 1
    ) if today_attendance else 0

    return jsonify({
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'total_revenue': float(total_revenue),
        'attendance_rate': attendance_rate,
        'present_today': present_today
    }), 200


@analytics_bp.route('/attendance-trends', methods=['GET'])
@jwt_required()
def get_attendance_trends():
    today = date.today()
    trends = []

    for i in range(30):
        d = today - timedelta(days=i)
        records = Attendance.query.filter_by(date=d).all()
        present = sum(1 for r in records if r.status == 'present')
        total = len(records)
        trends.append({
            'date': d.isoformat(),
            'present': present,
            'total': total,
            'rate': round((present / total * 100), 1) if total > 0 else 0
        })

    trends.reverse()
    return jsonify({'trends': trends}), 200


@analytics_bp.route('/revenue-trends', methods=['GET'])
@jwt_required()
def get_revenue_trends():
    today = date.today()
    trends = []

    for i in range(12):
        month_start = today.replace(day=1) - timedelta(days=30 * i)
        month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        revenue = db.session.query(
            db.func.sum(FeeRecord.amount_paid)
        ).filter(
            FeeRecord.payment_date >= month_start,
            FeeRecord.payment_date <= month_end,
            FeeRecord.status == 'completed'
        ).scalar() or 0

        trends.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': float(revenue)
        })

    trends.reverse()
    return jsonify({'trends': trends}), 200


@analytics_bp.route('/performance', methods=['GET'])
@jwt_required()
def get_performance_analytics():
    exams = Examination.query.order_by(Examination.created_at.desc()).limit(5).all()

    performance = []
    for exam in exams:
        grades = Grade.query.filter_by(examination_id=exam.id).all()
        if grades:
            avg = sum(g.marks for g in grades if g.marks) / len(grades)
            performance.append({
                'exam_name': exam.name,
                'average_marks': round(avg, 1),
                'total_students': len(grades)
            })

    return jsonify({'performance': performance}), 200
