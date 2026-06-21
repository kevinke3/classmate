from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from backend.app import db
from backend.app.models import Teacher, User

teachers_bp = Blueprint('teachers', __name__)


@teachers_bp.route('/', methods=['GET'])
@jwt_required()
def get_teachers():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    department = request.args.get('department')
    search = request.args.get('search')

    query = Teacher.query.join(User)

    if department:
        query = query.filter(Teacher.department == department)
    if search:
        query = query.filter(
            db.or_(
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                Teacher.employee_id.ilike(f'%{search}%')
            )
        )

    pagination = query.order_by(Teacher.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'teachers': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@teachers_bp.route('/<int:teacher_id>', methods=['GET'])
@jwt_required()
def get_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    return jsonify({'teacher': teacher.to_dict()}), 200


@teachers_bp.route('/', methods=['POST'])
@jwt_required()
def create_teacher():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()

    user = User(
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        role='teacher',
        phone=data.get('phone')
    )
    user.set_password(data.get('password', 'changeme123'))

    db.session.add(user)
    db.session.flush()

    teacher = Teacher(
        user_id=user.id,
        employee_id=data['employee_id'],
        department=data.get('department'),
        specialization=data.get('specialization'),
        qualification=data.get('qualification')
    )

    db.session.add(teacher)
    db.session.commit()

    return jsonify({'teacher': teacher.to_dict()}), 201


@teachers_bp.route('/<int:teacher_id>', methods=['PUT'])
@jwt_required()
def update_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    data = request.get_json()

    if 'department' in data:
        teacher.department = data['department']
    if 'specialization' in data:
        teacher.specialization = data['specialization']
    if 'qualification' in data:
        teacher.qualification = data['qualification']
    if 'status' in data:
        teacher.status = data['status']

    if 'first_name' in data:
        teacher.user.first_name = data['first_name']
    if 'last_name' in data:
        teacher.user.last_name = data['last_name']

    db.session.commit()

    return jsonify({'teacher': teacher.to_dict()}), 200
