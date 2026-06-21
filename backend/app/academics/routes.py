from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from backend.app import db
from backend.app.models import (
    SchoolClass, Stream, Subject, ClassSubject, SubjectTeacher,
    Timetable, Assignment
)

academics_bp = Blueprint('academics', __name__)


@academics_bp.route('/classes', methods=['GET'])
@jwt_required()
def get_classes():
    classes = SchoolClass.query.filter_by(is_active=True).all()
    return jsonify({'classes': [c.to_dict() for c in classes]}), 200


@academics_bp.route('/classes', methods=['POST'])
@jwt_required()
def create_class():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    school_class = SchoolClass(
        name=data['name'],
        level=data.get('level'),
        academic_year=data.get('academic_year'),
        capacity=data.get('capacity', 40)
    )
    db.session.add(school_class)
    db.session.commit()

    return jsonify({'class': school_class.to_dict()}), 201


@academics_bp.route('/subjects', methods=['GET'])
@jwt_required()
def get_subjects():
    subjects = Subject.query.all()
    return jsonify({'subjects': [s.to_dict() for s in subjects]}), 200


@academics_bp.route('/subjects', methods=['POST'])
@jwt_required()
def create_subject():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    subject = Subject(
        name=data['name'],
        code=data['code'],
        description=data.get('description'),
        is_compulsory=data.get('is_compulsory', False)
    )
    db.session.add(subject)
    db.session.commit()

    return jsonify({'subject': subject.to_dict()}), 201


@academics_bp.route('/timetable/<int:class_id>', methods=['GET'])
@jwt_required()
def get_timetable(class_id):
    entries = Timetable.query.filter_by(class_id=class_id).order_by(
        Timetable.day_of_week, Timetable.start_time
    ).all()

    timetable = []
    for entry in entries:
        timetable.append({
            'id': entry.id,
            'subject': entry.subject.name if entry.subject else None,
            'teacher': entry.teacher.user.full_name if entry.teacher else None,
            'day_of_week': entry.day_of_week,
            'start_time': entry.start_time.strftime('%H:%M'),
            'end_time': entry.end_time.strftime('%H:%M'),
            'room': entry.room
        })

    return jsonify({'timetable': timetable}), 200


@academics_bp.route('/assignments', methods=['GET'])
@jwt_required()
def get_assignments():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    class_id = request.args.get('class_id', type=int)
    subject_id = request.args.get('subject_id', type=int)

    query = Assignment.query

    if class_id:
        query = query.filter_by(class_id=class_id)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)

    pagination = query.order_by(Assignment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'assignments': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages
    }), 200


@academics_bp.route('/assignments', methods=['POST'])
@jwt_required()
def create_assignment():
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'teacher']:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    assignment = Assignment(
        title=data['title'],
        description=data.get('description'),
        subject_id=data['subject_id'],
        class_id=data['class_id'],
        teacher_id=data['teacher_id'],
        due_date=data.get('due_date'),
        max_marks=data.get('max_marks')
    )
    db.session.add(assignment)
    db.session.commit()

    return jsonify({'assignment': assignment.to_dict()}), 201
