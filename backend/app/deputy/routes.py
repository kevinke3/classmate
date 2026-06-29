from datetime import datetime, date, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app import db
from backend.app.models import (
    User, Student, Teacher, SchoolClass, Stream, Attendance, Notification
)
from backend.app.deputy.models import (
    DisciplineRecord, LeaveRequest, ClassTeacherAllocation,
    DutyRoster, TeacherAttendance, WelfareRecord
)

deputy_bp = Blueprint('deputy', __name__)


def require_deputy_or_admin():
    uid = get_jwt_identity()
    user = User.query.get(uid)
    if not user:
        return None, jsonify({'error': 'Unauthorized'}), 401
    if user.role == 'admin':
        return user, None, None
    if user.role == 'teacher':
        teacher = Teacher.query.filter_by(user_id=user.id).first()
        if teacher and teacher.teacher_role == 'deputy':
            return user, None, None
    return None, jsonify({'error': 'Deputy or admin access required'}), 403


# ── Dashboard ──────────────────────────────────────────────────────────
@deputy_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code

    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    total_students = Student.query.filter_by(status='active').count()
    total_teachers = Teacher.query.filter_by(status='active').count()
    total_classes = SchoolClass.query.filter_by(is_active=True).count()

    open_discipline = DisciplineRecord.query.filter_by(status='open').count()
    pending_leaves = LeaveRequest.query.filter_by(status='pending').count()
    open_welfare = WelfareRecord.query.filter_by(status='open').count()

    today_student_att = Attendance.query.filter_by(date=today).count()
    today_student_present = Attendance.query.filter_by(date=today, status='present').count()
    student_att_rate = round((today_student_present / today_student_att * 100), 1) if today_student_att > 0 else 0

    today_teacher_att = TeacherAttendance.query.filter_by(date=today).count()
    today_teacher_present = TeacherAttendance.query.filter_by(date=today, status='present').count()
    teacher_att_rate = round((today_teacher_present / today_teacher_att * 100), 1) if today_teacher_att > 0 else 0

    recent_discipline = [d.to_dict() for d in DisciplineRecord.query.order_by(
        DisciplineRecord.created_at.desc()).limit(5).all()]
    recent_leaves = [l.to_dict() for l in LeaveRequest.query.order_by(
        LeaveRequest.created_at.desc()).limit(5).all()]

    discipline_by_category = db.session.query(
        DisciplineRecord.category, db.func.count(DisciplineRecord.id)
    ).group_by(DisciplineRecord.category).all()

    students_by_class = db.session.query(
        SchoolClass.name, db.func.count(Student.id)
    ).join(Student, Student.class_id == SchoolClass.id
    ).filter(Student.status == 'active'
    ).group_by(SchoolClass.name).all()

    return jsonify({
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'open_discipline': open_discipline,
        'pending_leaves': pending_leaves,
        'open_welfare': open_welfare,
        'student_attendance_rate': student_att_rate,
        'teacher_attendance_rate': teacher_att_rate,
        'today_student_present': today_student_present,
        'today_teacher_present': today_teacher_present,
        'recent_discipline': recent_discipline,
        'recent_leaves': recent_leaves,
        'discipline_by_category': [{'category': c, 'count': n} for c, n in discipline_by_category],
        'students_by_class': [{'class_name': c, 'count': n} for c, n in students_by_class],
    })


# ── Discipline ─────────────────────────────────────────────────────────
@deputy_bp.route('/discipline', methods=['GET'])
@jwt_required()
def get_discipline():
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code
    status_filter = request.args.get('status')
    q = DisciplineRecord.query.order_by(DisciplineRecord.created_at.desc())
    if status_filter:
        q = q.filter_by(status=status_filter)
    return jsonify([d.to_dict() for d in q.all()])


@deputy_bp.route('/discipline', methods=['POST'])
@jwt_required()
def create_discipline():
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code
    data = request.get_json()
    record = DisciplineRecord(
        student_id=data['student_id'],
        reported_by=user.id,
        incident_date=datetime.strptime(data.get('incident_date', date.today().isoformat()), '%Y-%m-%d').date(),
        category=data['category'],
        severity=data.get('severity', 'minor'),
        description=data['description'],
        action_taken=data.get('action_taken'),
        counseling_referred=data.get('counseling_referred', False),
        suspension_days=data.get('suspension_days', 0),
    )
    db.session.add(record)
    db.session.commit()
    return jsonify(record.to_dict()), 201


@deputy_bp.route('/discipline/<int:rid>', methods=['PUT'])
@jwt_required()
def update_discipline(rid):
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code
    record = DisciplineRecord.query.get_or_404(rid)
    data = request.get_json()
    for field in ['category', 'severity', 'description', 'action_taken',
                  'parent_notified', 'counseling_referred', 'suspension_days',
                  'resolution_notes', 'status']:
        if field in data:
            setattr(record, field, data[field])
    if data.get('status') == 'resolved':
        record.resolved_by = user.id
        record.resolved_at = datetime.utcnow()
    db.session.commit()
    return jsonify(record.to_dict())


# ── Leave Requests ─────────────────────────────────────────────────────
@deputy_bp.route('/leaves', methods=['GET'])
@jwt_required()
def get_leaves():
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code
    status_filter = request.args.get('status')
    q = LeaveRequest.query.order_by(LeaveRequest.created_at.desc())
    if status_filter:
        q = q.filter_by(status=status_filter)
    return jsonify([l.to_dict() for l in q.all()])


@deputy_bp.route('/leaves/<int:lid>/approve', methods=['POST'])
@jwt_required()
def approve_leave(lid):
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code
    leave = LeaveRequest.query.get_or_404(lid)
    leave.status = 'approved'
    leave.approved_by = user.id
    leave.approved_at = datetime.utcnow()
    db.session.commit()

    notif = Notification(
        user_id=leave.teacher.user_id,
        title='Leave Approved',
        body=f'Your {leave.leave_type} leave from {leave.start_date} to {leave.end_date} has been approved.',
        notification_type='leave'
    )
    db.session.add(notif)
    db.session.commit()
    return jsonify(leave.to_dict())


@deputy_bp.route('/leaves/<int:lid>/reject', methods=['POST'])
@jwt_required()
def reject_leave(lid):
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code
    data = request.get_json()
    leave = LeaveRequest.query.get_or_404(lid)
    leave.status = 'rejected'
    leave.approved_by = user.id
    leave.approved_at = datetime.utcnow()
    leave.rejection_reason = data.get('reason', '')
    db.session.commit()
    return jsonify(leave.to_dict())


# ── Class Teacher Allocation ──────────────────────────────────────────
@deputy_bp.route('/allocations', methods=['GET'])
@jwt_required()
def get_allocations():
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code
    year = request.args.get('year', str(date.today().year))
    q = ClassTeacherAllocation.query.filter_by(academic_year=year).order_by(
        ClassTeacherAllocation.allocated_at.desc())
    return jsonify([a.to_dict() for a in q.all()])


@deputy_bp.route('/allocations', methods=['POST'])
@jwt_required()
def create_allocation():
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code
    data = request.get_json()
    teacher_id = data['teacher_id']
    class_id = data['class_id']
    year = data.get('academic_year', str(date.today().year))

    existing = ClassTeacherAllocation.query.filter_by(
        class_id=class_id, academic_year=year, is_active=True,
        stream_id=data.get('stream_id')
    ).first()
    if existing:
        return jsonify({'error': 'This class/stream already has an active allocation for this year'}), 409

    alloc = ClassTeacherAllocation(
        teacher_id=teacher_id,
        class_id=class_id,
        stream_id=data.get('stream_id'),
        academic_year=year,
        term=data.get('term'),
        allocated_by=user.id,
        notes=data.get('notes'),
    )
    db.session.add(alloc)
    db.session.commit()

    teacher = Teacher.query.get(teacher_id)
    if teacher:
        notif = Notification(
            user_id=teacher.user_id,
            title='Class Teacher Assignment',
            body=f'You have been assigned as class teacher for {alloc.school_class.name}.',
            notification_type='allocation'
        )
        db.session.add(notif)
        db.session.commit()
    return jsonify(alloc.to_dict()), 201


@deputy_bp.route('/allocations/<int:aid>', methods=['DELETE'])
@jwt_required()
def remove_allocation(aid):
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code
    alloc = ClassTeacherAllocation.query.get_or_404(aid)
    alloc.is_active = False
    alloc.deallocated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Allocation removed'})


# ── Duty Roster ────────────────────────────────────────────────────────
@deputy_bp.route('/duties', methods=['GET'])
@jwt_required()
def get_duties():
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code
    return jsonify([d.to_dict() for d in DutyRoster.query.order_by(
        DutyRoster.duty_date.desc()).all()])


@deputy_bp.route('/duties', methods=['POST'])
@jwt_required()
def create_duty():
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code
    data = request.get_json()
    duty = DutyRoster(
        teacher_id=data['teacher_id'],
        duty_type=data['duty_type'],
        duty_date=datetime.strptime(data['duty_date'], '%Y-%m-%d').date() if data.get('duty_date') else None,
        day_of_week=data.get('day_of_week'),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        location=data.get('location'),
        notes=data.get('notes'),
        created_by=user.id,
    )
    db.session.add(duty)
    db.session.commit()
    return jsonify(duty.to_dict()), 201


# ── Teacher Attendance ─────────────────────────────────────────────────
@deputy_bp.route('/teacher-attendance', methods=['GET'])
@jwt_required()
def get_teacher_attendance():
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code
    att_date = request.args.get('date', date.today().isoformat())
    records = TeacherAttendance.query.filter_by(
        date=datetime.strptime(att_date, '%Y-%m-%d').date()
    ).all()
    return jsonify([r.to_dict() for r in records])


@deputy_bp.route('/teacher-attendance', methods=['POST'])
@jwt_required()
def mark_teacher_attendance():
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code
    data = request.get_json()
    att_date = datetime.strptime(data.get('date', date.today().isoformat()), '%Y-%m-%d').date()

    existing = TeacherAttendance.query.filter_by(
        teacher_id=data['teacher_id'], date=att_date
    ).first()
    if existing:
        existing.status = data['status']
        existing.remarks = data.get('remarks')
        db.session.commit()
        return jsonify(existing.to_dict())

    record = TeacherAttendance(
        teacher_id=data['teacher_id'],
        date=att_date,
        status=data['status'],
        remarks=data.get('remarks'),
        recorded_by=user.id,
    )
    db.session.add(record)
    db.session.commit()
    return jsonify(record.to_dict()), 201


# ── Welfare ────────────────────────────────────────────────────────────
@deputy_bp.route('/welfare', methods=['GET'])
@jwt_required()
def get_welfare():
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code
    return jsonify([w.to_dict() for w in WelfareRecord.query.order_by(
        WelfareRecord.created_at.desc()).all()])


@deputy_bp.route('/welfare', methods=['POST'])
@jwt_required()
def create_welfare():
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code
    data = request.get_json()
    record = WelfareRecord(
        student_id=data['student_id'],
        category=data['category'],
        description=data['description'],
        action_taken=data.get('action_taken'),
        priority=data.get('priority', 'medium'),
        reported_by=user.id,
    )
    db.session.add(record)
    db.session.commit()
    return jsonify(record.to_dict()), 201


@deputy_bp.route('/welfare/<int:wid>', methods=['PUT'])
@jwt_required()
def update_welfare(wid):
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code
    record = WelfareRecord.query.get_or_404(wid)
    data = request.get_json()
    for field in ['category', 'description', 'action_taken', 'status', 'priority']:
        if field in data:
            setattr(record, field, data[field])
    db.session.commit()
    return jsonify(record.to_dict())


# ── Reports ────────────────────────────────────────────────────────────
@deputy_bp.route('/reports/discipline', methods=['GET'])
@jwt_required()
def discipline_report():
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code

    total = DisciplineRecord.query.count()
    open_count = DisciplineRecord.query.filter_by(status='open').count()
    resolved = DisciplineRecord.query.filter_by(status='resolved').count()
    suspensions = db.session.query(db.func.sum(DisciplineRecord.suspension_days)).scalar() or 0

    by_severity = db.session.query(
        DisciplineRecord.severity, db.func.count(DisciplineRecord.id)
    ).group_by(DisciplineRecord.severity).all()

    by_category = db.session.query(
        DisciplineRecord.category, db.func.count(DisciplineRecord.id)
    ).group_by(DisciplineRecord.category).all()

    return jsonify({
        'total': total,
        'open': open_count,
        'resolved': resolved,
        'total_suspension_days': suspensions,
        'by_severity': [{'severity': s, 'count': c} for s, c in by_severity],
        'by_category': [{'category': cat, 'count': c} for cat, c in by_category],
    })


@deputy_bp.route('/reports/attendance', methods=['GET'])
@jwt_required()
def attendance_report():
    user, err, code = require_deputy_or_admin()
    if err:
        return err, code

    period = request.args.get('period', 'today')
    if period == 'today':
        start = date.today()
        end = date.today()
    elif period == 'week':
        start = date.today() - timedelta(days=date.today().weekday())
        end = date.today()
    elif period == 'month':
        start = date.today().replace(day=1)
        end = date.today()
    else:
        start = date.today()
        end = date.today()

    student_total = Attendance.query.filter(Attendance.date.between(start, end)).count()
    student_present = Attendance.query.filter(
        Attendance.date.between(start, end), Attendance.status == 'present').count()

    teacher_total = TeacherAttendance.query.filter(TeacherAttendance.date.between(start, end)).count()
    teacher_present = TeacherAttendance.query.filter(
        TeacherAttendance.date.between(start, end), TeacherAttendance.status == 'present').count()

    return jsonify({
        'period': period,
        'student_total': student_total,
        'student_present': student_present,
        'student_rate': round(student_present / student_total * 100, 1) if student_total > 0 else 0,
        'teacher_total': teacher_total,
        'teacher_present': teacher_present,
        'teacher_rate': round(teacher_present / teacher_total * 100, 1) if teacher_total > 0 else 0,
    })
