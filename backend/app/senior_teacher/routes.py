from datetime import datetime, date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app import db
from backend.app.models import User, Teacher, SchoolClass, Subject
from backend.app.senior_teacher.models import (
    LessonPlan, SchemeOfWork, ClassroomObservation, SyllabusCoverage
)

senior_teacher_bp = Blueprint('senior_teacher', __name__)


def require_senior_or_above():
    uid = get_jwt_identity()
    user = User.query.get(uid)
    if not user:
        return None, jsonify({'error': 'Unauthorized'}), 401
    if user.role == 'admin':
        return user, None, None
    if user.role == 'teacher':
        teacher = Teacher.query.filter_by(user_id=user.id).first()
        if teacher and teacher.teacher_role in ('senior_teacher', 'deputy'):
            return user, None, None
    return None, jsonify({'error': 'Senior teacher or admin access required'}), 403


@senior_teacher_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    user, err, code = require_senior_or_above()
    if err:
        return err, code

    total_teachers = Teacher.query.filter_by(status='active').count()
    total_lessons = LessonPlan.query.count()
    completed_lessons = LessonPlan.query.filter_by(status='completed').count()
    pending_observations = ClassroomObservation.query.filter_by(status='scheduled').count()
    total_schemes = SchemeOfWork.query.count()

    lesson_rate = round(completed_lessons / total_lessons * 100, 1) if total_lessons > 0 else 0

    coverage = db.session.query(db.func.avg(SyllabusCoverage.percentage)).scalar() or 0

    recent_observations = [o.to_dict() for o in ClassroomObservation.query.order_by(
        ClassroomObservation.created_at.desc()).limit(5).all()]

    lessons_by_status = db.session.query(
        LessonPlan.status, db.func.count(LessonPlan.id)
    ).group_by(LessonPlan.status).all()

    return jsonify({
        'total_teachers': total_teachers,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'lesson_completion_rate': lesson_rate,
        'pending_observations': pending_observations,
        'total_schemes': total_schemes,
        'avg_syllabus_coverage': round(float(coverage), 1),
        'recent_observations': recent_observations,
        'lessons_by_status': [{'status': s, 'count': c} for s, c in lessons_by_status],
    })


# ── Lesson Plans ───────────────────────────────────────────────────────
@senior_teacher_bp.route('/lesson-plans', methods=['GET'])
@jwt_required()
def get_lesson_plans():
    user, err, code = require_senior_or_above()
    if err:
        return err, code
    teacher_id = request.args.get('teacher_id')
    q = LessonPlan.query.order_by(LessonPlan.lesson_date.desc())
    if teacher_id:
        q = q.filter_by(teacher_id=teacher_id)
    return jsonify([lp.to_dict() for lp in q.all()])


@senior_teacher_bp.route('/lesson-plans/<int:lpid>/review', methods=['POST'])
@jwt_required()
def review_lesson_plan(lpid):
    user, err, code = require_senior_or_above()
    if err:
        return err, code
    lp = LessonPlan.query.get_or_404(lpid)
    data = request.get_json()
    lp.status = data.get('status', 'reviewed')
    lp.reviewed_by = user.id
    lp.reviewed_at = datetime.utcnow()
    lp.completion_notes = data.get('notes', '')
    db.session.commit()
    return jsonify(lp.to_dict())


# ── Schemes of Work ───────────────────────────────────────────────────
@senior_teacher_bp.route('/schemes', methods=['GET'])
@jwt_required()
def get_schemes():
    user, err, code = require_senior_or_above()
    if err:
        return err, code
    return jsonify([s.to_dict() for s in SchemeOfWork.query.order_by(
        SchemeOfWork.created_at.desc()).all()])


# ── Classroom Observations ─────────────────────────────────────────────
@senior_teacher_bp.route('/observations', methods=['GET'])
@jwt_required()
def get_observations():
    user, err, code = require_senior_or_above()
    if err:
        return err, code
    return jsonify([o.to_dict() for o in ClassroomObservation.query.order_by(
        ClassroomObservation.observation_date.desc()).all()])


@senior_teacher_bp.route('/observations', methods=['POST'])
@jwt_required()
def create_observation():
    user, err, code = require_senior_or_above()
    if err:
        return err, code
    data = request.get_json()
    obs = ClassroomObservation(
        teacher_id=data['teacher_id'],
        observer_id=user.id,
        class_id=data.get('class_id'),
        subject_id=data.get('subject_id'),
        observation_date=datetime.strptime(data['observation_date'], '%Y-%m-%d').date(),
        lesson_delivery=data.get('lesson_delivery'),
        student_engagement=data.get('student_engagement'),
        classroom_management=data.get('classroom_management'),
        content_knowledge=data.get('content_knowledge'),
        use_of_resources=data.get('use_of_resources'),
        overall_rating=data.get('overall_rating'),
        strengths=data.get('strengths'),
        areas_for_improvement=data.get('areas_for_improvement'),
        recommendations=data.get('recommendations'),
    )
    db.session.add(obs)
    db.session.commit()
    return jsonify(obs.to_dict()), 201


# ── Syllabus Coverage ──────────────────────────────────────────────────
@senior_teacher_bp.route('/syllabus', methods=['GET'])
@jwt_required()
def get_syllabus():
    user, err, code = require_senior_or_above()
    if err:
        return err, code
    return jsonify([s.to_dict() for s in SyllabusCoverage.query.all()])


# ── Reports ────────────────────────────────────────────────────────────
@senior_teacher_bp.route('/reports/teacher-performance', methods=['GET'])
@jwt_required()
def teacher_performance_report():
    user, err, code = require_senior_or_above()
    if err:
        return err, code

    teachers = Teacher.query.filter_by(status='active').all()
    results = []
    for t in teachers:
        total_lp = LessonPlan.query.filter_by(teacher_id=t.id).count()
        completed_lp = LessonPlan.query.filter_by(teacher_id=t.id, status='completed').count()
        obs = ClassroomObservation.query.filter_by(teacher_id=t.id).all()
        avg_rating = sum(o.overall_rating or 0 for o in obs) / len(obs) if obs else 0
        syl = SyllabusCoverage.query.filter_by(teacher_id=t.id).all()
        avg_coverage = sum(s.percentage for s in syl) / len(syl) if syl else 0

        results.append({
            'teacher_id': t.id,
            'teacher_name': t.user.full_name if t.user else None,
            'employee_id': t.employee_id,
            'department': t.department,
            'total_lessons': total_lp,
            'completed_lessons': completed_lp,
            'lesson_rate': round(completed_lp / total_lp * 100, 1) if total_lp > 0 else 0,
            'avg_observation_rating': round(avg_rating, 1),
            'avg_syllabus_coverage': round(avg_coverage, 1),
        })

    return jsonify(results)
