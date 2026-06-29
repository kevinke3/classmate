from datetime import datetime, date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app import db
from backend.app.models import (
    User, Teacher, Student, SchoolClass, Attendance, Grade, Assignment,
    Message, Parent, ParentStudent, Invoice, Notification
)
from backend.app.class_teacher.models import BehaviorRecord, CounselingNote, HomeworkRecord
from backend.app.deputy.models import DisciplineRecord

ct_bp = Blueprint('class_teacher', __name__)


def get_class_teacher_info():
    uid = get_jwt_identity()
    user = User.query.get(uid)
    if not user:
        return None, None, jsonify({'error': 'Unauthorized'}), 401
    if user.role == 'admin':
        return user, None, None, None
    if user.role != 'teacher':
        return None, None, jsonify({'error': 'Teacher access required'}), 403
    teacher = Teacher.query.filter_by(user_id=user.id).first()
    if not teacher:
        return None, None, jsonify({'error': 'Teacher profile not found'}), 404
    return user, teacher, None, None


def get_teacher_class_ids(teacher):
    if not teacher:
        return [c.id for c in SchoolClass.query.filter_by(is_active=True).all()]
    from backend.app.deputy.models import ClassTeacherAllocation
    allocs = ClassTeacherAllocation.query.filter_by(
        teacher_id=teacher.id, is_active=True).all()
    if allocs:
        return [a.class_id for a in allocs]
    from backend.app.models import ClassTeacher
    ct_records = ClassTeacher.query.filter_by(
        teacher_id=teacher.id, is_class_teacher=True).all()
    return [ct.class_id for ct in ct_records]


@ct_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    user, teacher, err, code = get_class_teacher_info()
    if err:
        return err, code

    class_ids = get_teacher_class_ids(teacher)
    student_count = Student.query.filter(
        Student.class_id.in_(class_ids), Student.status == 'active'
    ).count() if class_ids else 0

    today = date.today()
    today_att = Attendance.query.filter(
        Attendance.class_id.in_(class_ids), Attendance.date == today
    ).count() if class_ids else 0
    today_present = Attendance.query.filter(
        Attendance.class_id.in_(class_ids), Attendance.date == today,
        Attendance.status == 'present'
    ).count() if class_ids else 0
    att_rate = round(today_present / today_att * 100, 1) if today_att > 0 else 0

    student_ids = [s.id for s in Student.query.filter(
        Student.class_id.in_(class_ids), Student.status == 'active').all()] if class_ids else []

    grades = Grade.query.filter(Grade.student_id.in_(student_ids)).all() if student_ids else []
    avg_score = round(sum(g.marks or 0 for g in grades) / len(grades), 1) if grades else 0

    discipline_count = DisciplineRecord.query.filter(
        DisciplineRecord.student_id.in_(student_ids), DisciplineRecord.status == 'open'
    ).count() if student_ids else 0

    homework_pending = HomeworkRecord.query.filter(
        HomeworkRecord.student_id.in_(student_ids), HomeworkRecord.status == 'pending'
    ).count() if student_ids else 0

    unpaid = Invoice.query.filter(
        Invoice.student_id.in_(student_ids), Invoice.status.in_(['unpaid', 'partial'])
    ).count() if student_ids else 0

    recent_behavior = [b.to_dict() for b in BehaviorRecord.query.filter(
        BehaviorRecord.student_id.in_(student_ids)
    ).order_by(BehaviorRecord.created_at.desc()).limit(5).all()] if student_ids else []

    class_names = [c.name for c in SchoolClass.query.filter(
        SchoolClass.id.in_(class_ids)).all()] if class_ids else []

    return jsonify({
        'class_names': class_names,
        'student_count': student_count,
        'attendance_rate': att_rate,
        'today_present': today_present,
        'today_total': today_att,
        'avg_score': avg_score,
        'open_discipline': discipline_count,
        'homework_pending': homework_pending,
        'unpaid_invoices': unpaid,
        'recent_behavior': recent_behavior,
    })


# ── Students ──────────────────────────────────────────────────────────
@ct_bp.route('/students', methods=['GET'])
@jwt_required()
def get_students():
    user, teacher, err, code = get_class_teacher_info()
    if err:
        return err, code
    class_ids = get_teacher_class_ids(teacher)
    students = Student.query.filter(
        Student.class_id.in_(class_ids), Student.status == 'active'
    ).order_by(Student.first_name).all() if class_ids else []
    return jsonify([s.to_dict() for s in students])


@ct_bp.route('/students/<int:sid>/profile', methods=['GET'])
@jwt_required()
def student_profile(sid):
    user, teacher, err, code = get_class_teacher_info()
    if err:
        return err, code
    student = Student.query.get_or_404(sid)
    grades = [g.to_dict() for g in Grade.query.filter_by(student_id=sid).order_by(Grade.created_at.desc()).all()]
    attendance = Attendance.query.filter_by(student_id=sid).all()
    total_att = len(attendance)
    present_att = sum(1 for a in attendance if a.status == 'present')
    att_rate = round(present_att / total_att * 100, 1) if total_att > 0 else 0

    behaviors = [b.to_dict() for b in BehaviorRecord.query.filter_by(student_id=sid).order_by(
        BehaviorRecord.date.desc()).limit(10).all()]
    discipline = [d.to_dict() for d in DisciplineRecord.query.filter_by(student_id=sid).order_by(
        DisciplineRecord.created_at.desc()).limit(10).all()]
    counseling = [c.to_dict() for c in CounselingNote.query.filter_by(student_id=sid).order_by(
        CounselingNote.session_date.desc()).limit(10).all()]

    invoices = Invoice.query.filter_by(student_id=sid).all()
    total_fees = sum(i.amount for i in invoices)
    total_paid = sum(i.amount - i.balance for i in invoices)
    outstanding = sum(i.balance for i in invoices)
    fee_cleared = outstanding <= 0

    return jsonify({
        'student': student.to_dict(),
        'grades': grades,
        'attendance_rate': att_rate,
        'total_attendance': total_att,
        'present_count': present_att,
        'behaviors': behaviors,
        'discipline': discipline,
        'counseling': counseling,
        'total_fees': total_fees,
        'total_paid': total_paid,
        'outstanding': outstanding,
        'fee_cleared': fee_cleared,
    })


# ── Attendance ────────────────────────────────────────────────────────
@ct_bp.route('/attendance', methods=['GET'])
@jwt_required()
def get_attendance():
    user, teacher, err, code = get_class_teacher_info()
    if err:
        return err, code
    class_ids = get_teacher_class_ids(teacher)
    att_date = request.args.get('date', date.today().isoformat())
    records = Attendance.query.filter(
        Attendance.class_id.in_(class_ids),
        Attendance.date == datetime.strptime(att_date, '%Y-%m-%d').date()
    ).all() if class_ids else []
    return jsonify([r.to_dict() for r in records])


@ct_bp.route('/attendance', methods=['POST'])
@jwt_required()
def mark_attendance():
    user, teacher, err, code = get_class_teacher_info()
    if err:
        return err, code
    data = request.get_json()
    records = data.get('records', [])
    att_date = datetime.strptime(data.get('date', date.today().isoformat()), '%Y-%m-%d').date()

    for rec in records:
        existing = Attendance.query.filter_by(
            student_id=rec['student_id'], date=att_date
        ).first()
        if existing:
            existing.status = rec['status']
            existing.remarks = rec.get('remarks')
        else:
            att = Attendance(
                student_id=rec['student_id'],
                class_id=rec.get('class_id', 0),
                date=att_date,
                status=rec['status'],
                remarks=rec.get('remarks'),
                marked_by=user.id,
            )
            db.session.add(att)
    db.session.commit()
    return jsonify({'message': f'{len(records)} attendance records saved'})


# ── Behavior ──────────────────────────────────────────────────────────
@ct_bp.route('/behavior', methods=['GET'])
@jwt_required()
def get_behavior():
    user, teacher, err, code = get_class_teacher_info()
    if err:
        return err, code
    class_ids = get_teacher_class_ids(teacher)
    student_ids = [s.id for s in Student.query.filter(
        Student.class_id.in_(class_ids), Student.status == 'active').all()] if class_ids else []
    records = BehaviorRecord.query.filter(
        BehaviorRecord.student_id.in_(student_ids)
    ).order_by(BehaviorRecord.date.desc()).all() if student_ids else []
    return jsonify([r.to_dict() for r in records])


@ct_bp.route('/behavior', methods=['POST'])
@jwt_required()
def create_behavior():
    user, teacher, err, code = get_class_teacher_info()
    if err:
        return err, code
    data = request.get_json()
    record = BehaviorRecord(
        student_id=data['student_id'],
        recorded_by=user.id,
        behavior_type=data['behavior_type'],
        category=data['category'],
        description=data['description'],
        action_taken=data.get('action_taken'),
        points=data.get('points', 0),
        date=datetime.strptime(data.get('date', date.today().isoformat()), '%Y-%m-%d').date(),
    )
    db.session.add(record)
    db.session.commit()
    return jsonify(record.to_dict()), 201


# ── Counseling ────────────────────────────────────────────────────────
@ct_bp.route('/counseling', methods=['GET'])
@jwt_required()
def get_counseling():
    user, teacher, err, code = get_class_teacher_info()
    if err:
        return err, code
    class_ids = get_teacher_class_ids(teacher)
    student_ids = [s.id for s in Student.query.filter(
        Student.class_id.in_(class_ids), Student.status == 'active').all()] if class_ids else []
    records = CounselingNote.query.filter(
        CounselingNote.student_id.in_(student_ids)
    ).order_by(CounselingNote.session_date.desc()).all() if student_ids else []
    return jsonify([r.to_dict() for r in records])


@ct_bp.route('/counseling', methods=['POST'])
@jwt_required()
def create_counseling():
    user, teacher, err, code = get_class_teacher_info()
    if err:
        return err, code
    data = request.get_json()
    note = CounselingNote(
        student_id=data['student_id'],
        counselor_id=user.id,
        session_date=datetime.strptime(data.get('session_date', date.today().isoformat()), '%Y-%m-%d').date(),
        category=data['category'],
        summary=data['summary'],
        recommendations=data.get('recommendations'),
        follow_up_date=datetime.strptime(data['follow_up_date'], '%Y-%m-%d').date() if data.get('follow_up_date') else None,
        is_confidential=data.get('is_confidential', True),
    )
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201


# ── Parent Messaging ─────────────────────────────────────────────────
@ct_bp.route('/parents', methods=['GET'])
@jwt_required()
def get_class_parents():
    user, teacher, err, code = get_class_teacher_info()
    if err:
        return err, code
    class_ids = get_teacher_class_ids(teacher)
    student_ids = [s.id for s in Student.query.filter(
        Student.class_id.in_(class_ids), Student.status == 'active').all()] if class_ids else []
    parent_links = ParentStudent.query.filter(
        ParentStudent.student_id.in_(student_ids)).all() if student_ids else []
    parents = []
    seen = set()
    for pl in parent_links:
        if pl.parent_id not in seen:
            seen.add(pl.parent_id)
            parent = Parent.query.get(pl.parent_id)
            if parent:
                parents.append({
                    **parent.to_dict(),
                    'student_name': Student.query.get(pl.student_id).full_name if pl.student_id else None,
                })
    return jsonify(parents)


@ct_bp.route('/message-parent', methods=['POST'])
@jwt_required()
def message_parent():
    user, teacher, err, code = get_class_teacher_info()
    if err:
        return err, code
    data = request.get_json()
    parent = Parent.query.get_or_404(data['parent_id'])
    msg = Message(
        sender_id=user.id,
        recipient_id=parent.user_id,
        subject=data.get('subject', 'Message from Class Teacher'),
        body=data['body'],
        message_type='direct',
    )
    db.session.add(msg)

    notif = Notification(
        user_id=parent.user_id,
        title='New Message from Class Teacher',
        body=f'{user.full_name} sent you a message.',
        notification_type='message',
    )
    db.session.add(notif)
    db.session.commit()
    return jsonify({'message': 'Message sent successfully'})


# ── Reports ──────────────────────────────────────────────────────────
@ct_bp.route('/reports/attendance', methods=['GET'])
@jwt_required()
def attendance_report():
    user, teacher, err, code = get_class_teacher_info()
    if err:
        return err, code
    class_ids = get_teacher_class_ids(teacher)
    students = Student.query.filter(
        Student.class_id.in_(class_ids), Student.status == 'active'
    ).all() if class_ids else []

    results = []
    for s in students:
        att = Attendance.query.filter_by(student_id=s.id).all()
        total = len(att)
        present = sum(1 for a in att if a.status == 'present')
        results.append({
            'student_name': s.full_name,
            'admission_number': s.admission_number,
            'total_days': total,
            'present': present,
            'absent': total - present,
            'rate': round(present / total * 100, 1) if total > 0 else 0,
        })
    return jsonify(results)


@ct_bp.route('/reports/performance', methods=['GET'])
@jwt_required()
def performance_report():
    user, teacher, err, code = get_class_teacher_info()
    if err:
        return err, code
    class_ids = get_teacher_class_ids(teacher)
    students = Student.query.filter(
        Student.class_id.in_(class_ids), Student.status == 'active'
    ).all() if class_ids else []

    results = []
    for s in students:
        grades = Grade.query.filter_by(student_id=s.id).all()
        marks = [g.marks for g in grades if g.marks is not None]
        avg = round(sum(marks) / len(marks), 1) if marks else 0
        results.append({
            'student_name': s.full_name,
            'admission_number': s.admission_number,
            'subjects_count': len(marks),
            'average': avg,
            'highest': max(marks) if marks else 0,
            'lowest': min(marks) if marks else 0,
        })
    results.sort(key=lambda x: x['average'], reverse=True)
    for rank, r in enumerate(results, 1):
        r['rank'] = rank
    return jsonify(results)
