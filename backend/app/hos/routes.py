from datetime import datetime, date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app import db
from backend.app.models import (
    User, Teacher, Student, SchoolClass, Subject, Examination, Grade, Attendance
)
from backend.app.hos.models import AcademicTarget, AcademicIntervention, GradeAnalysis
from backend.app.senior_teacher.models import SyllabusCoverage

hos_bp = Blueprint('hos', __name__)


def require_hos_or_above():
    uid = get_jwt_identity()
    user = User.query.get(uid)
    if not user:
        return None, jsonify({'error': 'Unauthorized'}), 401
    if user.role == 'admin':
        return user, None, None
    if user.role == 'teacher':
        teacher = Teacher.query.filter_by(user_id=user.id).first()
        if teacher and teacher.teacher_role in ('head_of_studies', 'deputy'):
            return user, None, None
    return None, jsonify({'error': 'Head of Studies or admin access required'}), 403


@hos_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    user, err, code = require_hos_or_above()
    if err:
        return err, code

    total_students = Student.query.filter_by(status='active').count()
    total_exams = Examination.query.count()
    total_subjects = Subject.query.count()

    avg_score = db.session.query(db.func.avg(Grade.marks)).scalar() or 0
    pass_count = Grade.query.filter(Grade.marks >= 50).count()
    total_grades = Grade.query.count()
    pass_rate = round(pass_count / total_grades * 100, 1) if total_grades > 0 else 0

    active_interventions = AcademicIntervention.query.filter_by(status='active').count()
    avg_coverage = db.session.query(db.func.avg(SyllabusCoverage.percentage)).scalar() or 0

    class_performance = []
    for cls in SchoolClass.query.filter_by(is_active=True).all():
        cls_grades = Grade.query.join(Student).filter(Student.class_id == cls.id).all()
        if cls_grades:
            cls_avg = sum(g.marks or 0 for g in cls_grades) / len(cls_grades)
        else:
            cls_avg = 0
        class_performance.append({'class_name': cls.name, 'mean_score': round(cls_avg, 1)})

    subject_performance = []
    for subj in Subject.query.all():
        subj_grades = Grade.query.filter_by(subject_id=subj.id).all()
        if subj_grades:
            subj_avg = sum(g.marks or 0 for g in subj_grades) / len(subj_grades)
        else:
            subj_avg = 0
        subject_performance.append({'subject_name': subj.name, 'mean_score': round(subj_avg, 1)})

    grade_distribution = db.session.query(
        Grade.grade, db.func.count(Grade.id)
    ).group_by(Grade.grade).all()

    return jsonify({
        'total_students': total_students,
        'total_exams': total_exams,
        'total_subjects': total_subjects,
        'overall_mean': round(float(avg_score), 1),
        'pass_rate': pass_rate,
        'active_interventions': active_interventions,
        'avg_syllabus_coverage': round(float(avg_coverage), 1),
        'class_performance': class_performance,
        'subject_performance': subject_performance,
        'grade_distribution': [{'grade': g or 'N/A', 'count': c} for g, c in grade_distribution],
    })


# ── Examinations ───────────────────────────────────────────────────────
@hos_bp.route('/examinations', methods=['GET'])
@jwt_required()
def get_examinations():
    user, err, code = require_hos_or_above()
    if err:
        return err, code
    return jsonify([e.to_dict() for e in Examination.query.order_by(
        Examination.start_date.desc()).all()])


@hos_bp.route('/examinations', methods=['POST'])
@jwt_required()
def create_examination():
    user, err, code = require_hos_or_above()
    if err:
        return err, code
    data = request.get_json()
    exam = Examination(
        name=data['name'],
        exam_type=data['exam_type'],
        academic_year=data.get('academic_year', str(date.today().year)),
        term=data.get('term'),
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None,
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None,
        status=data.get('status', 'scheduled'),
        created_by=user.id,
    )
    db.session.add(exam)
    db.session.commit()
    return jsonify(exam.to_dict()), 201


@hos_bp.route('/examinations/<int:eid>/results', methods=['GET'])
@jwt_required()
def exam_results(eid):
    user, err, code = require_hos_or_above()
    if err:
        return err, code
    exam = Examination.query.get_or_404(eid)
    grades = Grade.query.filter_by(examination_id=eid).all()

    students = {}
    for g in grades:
        sid = g.student_id
        if sid not in students:
            students[sid] = {
                'student_id': sid,
                'student_name': g.student.full_name if g.student else None,
                'admission_number': g.student.admission_number if g.student else None,
                'subjects': [],
                'total': 0,
                'count': 0,
            }
        students[sid]['subjects'].append({
            'subject': g.subject.name if g.subject else None,
            'marks': g.marks,
            'grade': g.grade,
        })
        students[sid]['total'] += g.marks or 0
        students[sid]['count'] += 1

    results = []
    for s in students.values():
        s['mean'] = round(s['total'] / s['count'], 1) if s['count'] > 0 else 0
        results.append(s)
    results.sort(key=lambda x: x['total'], reverse=True)

    for rank, r in enumerate(results, 1):
        r['rank'] = rank

    return jsonify({
        'exam': exam.to_dict(),
        'results': results,
        'total_students': len(results),
    })


# ── Academic Targets ──────────────────────────────────────────────────
@hos_bp.route('/targets', methods=['GET'])
@jwt_required()
def get_targets():
    user, err, code = require_hos_or_above()
    if err:
        return err, code
    return jsonify([t.to_dict() for t in AcademicTarget.query.order_by(
        AcademicTarget.created_at.desc()).all()])


@hos_bp.route('/targets', methods=['POST'])
@jwt_required()
def create_target():
    user, err, code = require_hos_or_above()
    if err:
        return err, code
    data = request.get_json()
    target = AcademicTarget(
        class_id=data.get('class_id'),
        subject_id=data.get('subject_id'),
        academic_year=data.get('academic_year', str(date.today().year)),
        term=data.get('term', 'Term 1'),
        target_mean=data.get('target_mean'),
        target_pass_rate=data.get('target_pass_rate'),
        set_by=user.id,
    )
    db.session.add(target)
    db.session.commit()
    return jsonify(target.to_dict()), 201


# ── Interventions ─────────────────────────────────────────────────────
@hos_bp.route('/interventions', methods=['GET'])
@jwt_required()
def get_interventions():
    user, err, code = require_hos_or_above()
    if err:
        return err, code
    return jsonify([i.to_dict() for i in AcademicIntervention.query.order_by(
        AcademicIntervention.created_at.desc()).all()])


@hos_bp.route('/interventions', methods=['POST'])
@jwt_required()
def create_intervention():
    user, err, code = require_hos_or_above()
    if err:
        return err, code
    data = request.get_json()
    intervention = AcademicIntervention(
        student_id=data['student_id'],
        subject_id=data.get('subject_id'),
        intervention_type=data['intervention_type'],
        description=data['description'],
        target_score=data.get('target_score'),
        current_score=data.get('current_score'),
        created_by=user.id,
    )
    db.session.add(intervention)
    db.session.commit()
    return jsonify(intervention.to_dict()), 201


# ── Reports ────────────────────────────────────────────────────────────
@hos_bp.route('/reports/class-performance', methods=['GET'])
@jwt_required()
def class_performance_report():
    user, err, code = require_hos_or_above()
    if err:
        return err, code

    results = []
    for cls in SchoolClass.query.filter_by(is_active=True).all():
        student_ids = [s.id for s in cls.students.filter_by(status='active').all()]
        if not student_ids:
            results.append({
                'class_name': cls.name, 'student_count': 0,
                'mean_score': 0, 'pass_rate': 0, 'highest': 0, 'lowest': 0
            })
            continue
        grades = Grade.query.filter(Grade.student_id.in_(student_ids)).all()
        if not grades:
            results.append({
                'class_name': cls.name, 'student_count': len(student_ids),
                'mean_score': 0, 'pass_rate': 0, 'highest': 0, 'lowest': 0
            })
            continue
        marks = [g.marks for g in grades if g.marks is not None]
        mean = sum(marks) / len(marks) if marks else 0
        passed = sum(1 for m in marks if m >= 50)
        results.append({
            'class_name': cls.name,
            'student_count': len(student_ids),
            'mean_score': round(mean, 1),
            'pass_rate': round(passed / len(marks) * 100, 1) if marks else 0,
            'highest': max(marks) if marks else 0,
            'lowest': min(marks) if marks else 0,
        })

    return jsonify(results)


@hos_bp.route('/reports/subject-analysis', methods=['GET'])
@jwt_required()
def subject_analysis_report():
    user, err, code = require_hos_or_above()
    if err:
        return err, code

    results = []
    for subj in Subject.query.all():
        grades = Grade.query.filter_by(subject_id=subj.id).all()
        marks = [g.marks for g in grades if g.marks is not None]
        if not marks:
            results.append({
                'subject_name': subj.name, 'total_students': 0,
                'mean_score': 0, 'pass_rate': 0, 'highest': 0, 'lowest': 0
            })
            continue
        passed = sum(1 for m in marks if m >= 50)
        results.append({
            'subject_name': subj.name,
            'total_students': len(marks),
            'mean_score': round(sum(marks) / len(marks), 1),
            'pass_rate': round(passed / len(marks) * 100, 1),
            'highest': max(marks),
            'lowest': min(marks),
        })

    return jsonify(results)
