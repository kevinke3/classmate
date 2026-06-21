from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from backend.app import db
from backend.app.models import Examination, Grade, Student, Subject

examinations_bp = Blueprint('examinations', __name__)


@examinations_bp.route('/', methods=['GET'])
@jwt_required()
def get_examinations():
    exams = Examination.query.order_by(Examination.created_at.desc()).all()
    return jsonify({'examinations': [e.to_dict() for e in exams]}), 200


@examinations_bp.route('/', methods=['POST'])
@jwt_required()
def create_examination():
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'teacher']:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    exam = Examination(
        name=data['name'],
        exam_type=data['exam_type'],
        academic_year=data.get('academic_year'),
        term=data.get('term'),
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        created_by=current_user_id
    )
    db.session.add(exam)
    db.session.commit()

    return jsonify({'examination': exam.to_dict()}), 201


@examinations_bp.route('/<int:exam_id>/grades', methods=['GET'])
@jwt_required()
def get_exam_grades(exam_id):
    class_id = request.args.get('class_id', type=int)
    subject_id = request.args.get('subject_id', type=int)

    query = Grade.query.filter_by(examination_id=exam_id)

    if subject_id:
        query = query.filter_by(subject_id=subject_id)

    grades = query.all()

    return jsonify({'grades': [g.to_dict() for g in grades]}), 200


@examinations_bp.route('/<int:exam_id>/grades', methods=['POST'])
@jwt_required()
def submit_grades(exam_id):
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'teacher']:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    current_user_id = int(get_jwt_identity())
    grades_data = data.get('grades', [])

    for grade_data in grades_data:
        existing = Grade.query.filter_by(
            student_id=grade_data['student_id'],
            examination_id=exam_id,
            subject_id=grade_data['subject_id']
        ).first()

        if existing:
            existing.marks = grade_data['marks']
            existing.grade = grade_data.get('grade')
            existing.remarks = grade_data.get('remarks')
        else:
            grade = Grade(
                student_id=grade_data['student_id'],
                examination_id=exam_id,
                subject_id=grade_data['subject_id'],
                marks=grade_data['marks'],
                grade=grade_data.get('grade'),
                remarks=grade_data.get('remarks'),
                graded_by=current_user_id
            )
            db.session.add(grade)

    db.session.commit()

    return jsonify({'message': f'Grades submitted for {len(grades_data)} students'}), 201


@examinations_bp.route('/student/<int:student_id>/report', methods=['GET'])
@jwt_required()
def get_student_report(student_id):
    exam_id = request.args.get('exam_id', type=int)

    query = Grade.query.filter_by(student_id=student_id)
    if exam_id:
        query = query.filter_by(examination_id=exam_id)

    grades = query.all()

    total_marks = sum(g.marks for g in grades if g.marks)
    total_subjects = len(grades)
    average = round(total_marks / total_subjects, 1) if total_subjects > 0 else 0

    return jsonify({
        'grades': [g.to_dict() for g in grades],
        'summary': {
            'total_marks': total_marks,
            'total_subjects': total_subjects,
            'average': average
        }
    }), 200
