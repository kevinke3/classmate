from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from backend.app import db
from backend.app.models import Student, User, SchoolClass

students_bp = Blueprint('students', __name__)


@students_bp.route('/', methods=['GET'])
@jwt_required()
def get_students():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    class_id = request.args.get('class_id', type=int)
    search = request.args.get('search')
    status = request.args.get('status', 'active')

    query = Student.query.join(User)

    if class_id:
        query = query.filter(Student.class_id == class_id)
    if status:
        query = query.filter(Student.status == status)
    if search:
        query = query.filter(
            db.or_(
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                Student.admission_number.ilike(f'%{search}%')
            )
        )

    pagination = query.order_by(Student.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'students': [s.to_dict() for s in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@students_bp.route('/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student(student_id):
    student = Student.query.get_or_404(student_id)
    return jsonify({'student': student.to_dict()}), 200


@students_bp.route('/', methods=['POST'])
@jwt_required()
def create_student():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()

    user = User(
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        role='student',
        phone=data.get('phone')
    )
    user.set_password(data.get('password', 'changeme123'))

    db.session.add(user)
    db.session.flush()

    student = Student(
        user_id=user.id,
        admission_number=data['admission_number'],
        class_id=data.get('class_id'),
        stream_id=data.get('stream_id'),
        date_of_birth=data.get('date_of_birth'),
        gender=data.get('gender'),
        address=data.get('address'),
        guardian_name=data.get('guardian_name'),
        guardian_phone=data.get('guardian_phone'),
        guardian_email=data.get('guardian_email')
    )

    db.session.add(student)
    db.session.commit()

    return jsonify({'student': student.to_dict()}), 201


@students_bp.route('/<int:student_id>', methods=['PUT'])
@jwt_required()
def update_student(student_id):
    student = Student.query.get_or_404(student_id)
    data = request.get_json()

    if 'class_id' in data:
        student.class_id = data['class_id']
    if 'stream_id' in data:
        student.stream_id = data['stream_id']
    if 'status' in data:
        student.status = data['status']
    if 'address' in data:
        student.address = data['address']
    if 'guardian_name' in data:
        student.guardian_name = data['guardian_name']
    if 'guardian_phone' in data:
        student.guardian_phone = data['guardian_phone']

    if 'first_name' in data:
        student.user.first_name = data['first_name']
    if 'last_name' in data:
        student.user.last_name = data['last_name']

    db.session.commit()

    return jsonify({'student': student.to_dict()}), 200


@students_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_student_stats():
    total = Student.query.filter_by(status='active').count()
    by_class = db.session.query(
        SchoolClass.name, db.func.count(Student.id)
    ).join(Student).filter(Student.status == 'active').group_by(SchoolClass.name).all()

    return jsonify({
        'total_students': total,
        'by_class': [{'class_name': c[0], 'count': c[1]} for c in by_class]
    }), 200
