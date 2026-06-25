from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from backend.app import db
from backend.app.models import (
    Teacher, User, Student, Parent, ParentStudent,
    ClassTeacher, SchoolClass, Message,
    Announcement, Event, Examination, Grade,
    Assignment, Subject, Timetable
)

teachers_bp = Blueprint('teachers', __name__)


# ---- Core teacher CRUD (admin) ----

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

    teacher_role = data.get('teacher_role', 'class_teacher')
    if teacher_role not in Teacher.VALID_ROLES:
        teacher_role = 'class_teacher'

    teacher = Teacher(
        user_id=user.id,
        employee_id=data['employee_id'],
        department=data.get('department'),
        specialization=data.get('specialization'),
        qualification=data.get('qualification'),
        teacher_role=teacher_role
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
    if 'teacher_role' in data:
        if data['teacher_role'] in Teacher.VALID_ROLES:
            teacher.teacher_role = data['teacher_role']

    if 'first_name' in data:
        teacher.user.first_name = data['first_name']
    if 'last_name' in data:
        teacher.user.last_name = data['last_name']

    db.session.commit()

    return jsonify({'teacher': teacher.to_dict()}), 200


# ---- Teacher portal: current teacher profile ----

@teachers_bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_profile():
    claims = get_jwt()
    if claims.get('role') != 'teacher':
        return jsonify({'error': 'Teacher access required'}), 403

    user_id = int(get_jwt_identity())
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher:
        return jsonify({'error': 'Teacher profile not found'}), 404

    my_classes = []
    for ct in teacher.classes.all():
        sc = SchoolClass.query.get(ct.class_id)
        if sc:
            my_classes.append({
                'id': sc.id,
                'name': sc.name,
                'is_class_teacher': ct.is_class_teacher,
                'student_count': sc.students.count()
            })

    return jsonify({
        'teacher': teacher.to_dict(),
        'classes': my_classes
    }), 200


# ---- Class Teacher: message parents of their class ----

@teachers_bp.route('/my-class-parents', methods=['GET'])
@jwt_required()
def get_my_class_parents():
    claims = get_jwt()
    if claims.get('role') != 'teacher':
        return jsonify({'error': 'Teacher access required'}), 403

    user_id = int(get_jwt_identity())
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher or not teacher.can_message_parents:
        return jsonify({'error': 'Only Class Teachers and Deputies can message parents'}), 403

    class_assignments = ClassTeacher.query.filter_by(
        teacher_id=teacher.id, is_class_teacher=True
    ).all()
    class_ids = [ca.class_id for ca in class_assignments]

    if not class_ids:
        return jsonify({'parents': [], 'message': 'No classes assigned'}), 200

    students_in_classes = Student.query.filter(
        Student.class_id.in_(class_ids)
    ).all()
    student_ids = [s.id for s in students_in_classes]

    parent_links = ParentStudent.query.filter(
        ParentStudent.student_id.in_(student_ids)
    ).all()
    parent_ids = list({pl.parent_id for pl in parent_links})

    parents = Parent.query.filter(Parent.id.in_(parent_ids)).all()

    result = []
    for parent in parents:
        children = []
        for pl in parent.children.all():
            if pl.student_id in student_ids:
                student = Student.query.get(pl.student_id)
                if student:
                    children.append({
                        'id': student.id,
                        'name': student.full_name,
                        'class_id': student.class_id
                    })
        result.append({
            'parent': parent.to_dict(),
            'children': children
        })

    return jsonify({'parents': result}), 200


@teachers_bp.route('/message-parent', methods=['POST'])
@jwt_required()
def message_parent():
    claims = get_jwt()
    if claims.get('role') != 'teacher':
        return jsonify({'error': 'Teacher access required'}), 403

    user_id = int(get_jwt_identity())
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher or not teacher.can_message_parents:
        return jsonify({'error': 'Only Class Teachers and Deputies can message parents'}), 403

    data = request.get_json()
    parent_user_id = data.get('parent_user_id')
    subject = data.get('subject', '')
    body = data.get('body', '')

    if not parent_user_id or not body:
        return jsonify({'error': 'parent_user_id and body are required'}), 400

    parent_user = User.query.get(parent_user_id)
    if not parent_user or parent_user.role != 'parent':
        return jsonify({'error': 'Invalid parent'}), 404

    message = Message(
        sender_id=user_id,
        recipient_id=parent_user_id,
        subject=subject,
        body=body,
        message_type='direct'
    )
    db.session.add(message)
    db.session.commit()

    return jsonify({'message': message.to_dict()}), 201


# ---- Head of Studies: academic management ----

@teachers_bp.route('/academics/overview', methods=['GET'])
@jwt_required()
def academics_overview():
    claims = get_jwt()
    if claims.get('role') != 'teacher':
        return jsonify({'error': 'Teacher access required'}), 403

    user_id = int(get_jwt_identity())
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher or not teacher.can_manage_academics:
        return jsonify({'error': 'Only Head of Studies and Deputies can manage academics'}), 403

    classes = SchoolClass.query.filter_by(is_active=True).all()
    subjects = Subject.query.all()
    exams = Examination.query.order_by(Examination.created_at.desc()).limit(10).all()
    assignments = Assignment.query.order_by(Assignment.created_at.desc()).limit(10).all()

    return jsonify({
        'classes': [c.to_dict() for c in classes],
        'subjects': [s.to_dict() for s in subjects],
        'recent_exams': [e.to_dict() for e in exams],
        'recent_assignments': [a.to_dict() for a in assignments],
        'total_classes': len(classes),
        'total_subjects': len(subjects),
        'total_exams': Examination.query.count(),
        'total_assignments': Assignment.query.count()
    }), 200


@teachers_bp.route('/academics/grades', methods=['POST'])
@jwt_required()
def manage_grades():
    claims = get_jwt()
    if claims.get('role') != 'teacher':
        return jsonify({'error': 'Teacher access required'}), 403

    user_id = int(get_jwt_identity())
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher or not teacher.can_manage_academics:
        return jsonify({'error': 'Only Head of Studies and Deputies can manage grades'}), 403

    data = request.get_json()
    grade = Grade(
        student_id=data['student_id'],
        examination_id=data['examination_id'],
        subject_id=data['subject_id'],
        marks=data.get('marks'),
        grade=data.get('grade'),
        remarks=data.get('remarks'),
        graded_by=user_id
    )
    db.session.add(grade)
    db.session.commit()

    return jsonify({'grade': grade.to_dict()}), 201


@teachers_bp.route('/academics/exams', methods=['POST'])
@jwt_required()
def create_exam():
    claims = get_jwt()
    if claims.get('role') != 'teacher':
        return jsonify({'error': 'Teacher access required'}), 403

    user_id = int(get_jwt_identity())
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher or not teacher.can_manage_academics:
        return jsonify({'error': 'Only Head of Studies and Deputies can create exams'}), 403

    data = request.get_json()
    exam = Examination(
        name=data['name'],
        exam_type=data.get('exam_type', 'term'),
        academic_year=data.get('academic_year'),
        term=data.get('term'),
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        created_by=user_id
    )
    db.session.add(exam)
    db.session.commit()

    return jsonify({'exam': exam.to_dict()}), 201


@teachers_bp.route('/academics/assignments', methods=['POST'])
@jwt_required()
def create_teacher_assignment():
    claims = get_jwt()
    if claims.get('role') != 'teacher':
        return jsonify({'error': 'Teacher access required'}), 403

    user_id = int(get_jwt_identity())
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher or not teacher.can_manage_academics:
        return jsonify({'error': 'Only Head of Studies and Deputies can create assignments'}), 403

    data = request.get_json()
    assignment = Assignment(
        title=data['title'],
        description=data.get('description'),
        subject_id=data['subject_id'],
        class_id=data['class_id'],
        teacher_id=teacher.id,
        due_date=data.get('due_date'),
        max_marks=data.get('max_marks')
    )
    db.session.add(assignment)
    db.session.commit()

    return jsonify({'assignment': assignment.to_dict()}), 201


# ---- Senior Teacher: announcements + events ----

@teachers_bp.route('/announcements', methods=['GET'])
@jwt_required()
def get_announcements():
    claims = get_jwt()
    if claims.get('role') != 'teacher':
        return jsonify({'error': 'Teacher access required'}), 403

    announcements = Announcement.query.order_by(
        Announcement.created_at.desc()
    ).limit(20).all()

    return jsonify({
        'announcements': [a.to_dict() for a in announcements]
    }), 200


@teachers_bp.route('/announcements', methods=['POST'])
@jwt_required()
def create_announcement():
    claims = get_jwt()
    if claims.get('role') != 'teacher':
        return jsonify({'error': 'Teacher access required'}), 403

    user_id = int(get_jwt_identity())
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher or not teacher.can_manage_announcements:
        return jsonify({'error': 'Only Senior Teachers and Deputies can post announcements'}), 403

    data = request.get_json()
    announcement = Announcement(
        title=data['title'],
        body=data['body'],
        target_role=data.get('target_role', 'teacher'),
        priority=data.get('priority', 'normal'),
        created_by=user_id
    )
    db.session.add(announcement)
    db.session.commit()

    return jsonify({'announcement': announcement.to_dict()}), 201


@teachers_bp.route('/events', methods=['GET'])
@jwt_required()
def get_events():
    claims = get_jwt()
    if claims.get('role') != 'teacher':
        return jsonify({'error': 'Teacher access required'}), 403

    events = Event.query.order_by(Event.event_date.desc()).limit(20).all()

    return jsonify({
        'events': [e.to_dict() for e in events]
    }), 200


@teachers_bp.route('/events', methods=['POST'])
@jwt_required()
def create_event():
    claims = get_jwt()
    if claims.get('role') != 'teacher':
        return jsonify({'error': 'Teacher access required'}), 403

    user_id = int(get_jwt_identity())
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher or not teacher.can_manage_events:
        return jsonify({'error': 'Only Senior Teachers and Deputies can manage events'}), 403

    data = request.get_json()
    event = Event(
        title=data['title'],
        description=data.get('description'),
        event_date=data['event_date'],
        end_date=data.get('end_date'),
        location=data.get('location'),
        event_type=data.get('event_type', 'general'),
        created_by=user_id
    )
    db.session.add(event)
    db.session.commit()

    return jsonify({'event': event.to_dict()}), 201
