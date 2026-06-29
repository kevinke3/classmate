from datetime import datetime
from backend.app import db


class LessonPlan(db.Model):
    __tablename__ = 'lesson_plans'

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    objectives = db.Column(db.Text)
    activities = db.Column(db.Text)
    resources = db.Column(db.Text)
    lesson_date = db.Column(db.Date)
    duration_minutes = db.Column(db.Integer, default=40)
    status = db.Column(db.String(20), default='planned')
    completion_notes = db.Column(db.Text)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship('Teacher', backref='lesson_plans')
    subject = db.relationship('Subject', backref='lesson_plans')
    school_class = db.relationship('SchoolClass', backref='lesson_plans')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])

    def to_dict(self):
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.user.full_name if self.teacher and self.teacher.user else None,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'class_id': self.class_id,
            'class_name': self.school_class.name if self.school_class else None,
            'topic': self.topic,
            'objectives': self.objectives,
            'activities': self.activities,
            'resources': self.resources,
            'lesson_date': self.lesson_date.isoformat() if self.lesson_date else None,
            'duration_minutes': self.duration_minutes,
            'status': self.status,
            'completion_notes': self.completion_notes,
            'reviewed_by_name': self.reviewer.full_name if self.reviewer else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class SchemeOfWork(db.Model):
    __tablename__ = 'schemes_of_work'

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    term = db.Column(db.String(20), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)
    week_number = db.Column(db.Integer)
    topic = db.Column(db.String(200), nullable=False)
    subtopics = db.Column(db.Text)
    objectives = db.Column(db.Text)
    teaching_methods = db.Column(db.Text)
    resources = db.Column(db.Text)
    assessment = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship('Teacher', backref='schemes_of_work')
    subject = db.relationship('Subject', backref='schemes_of_work')
    school_class = db.relationship('SchoolClass', backref='schemes_of_work')

    def to_dict(self):
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.user.full_name if self.teacher and self.teacher.user else None,
            'subject_name': self.subject.name if self.subject else None,
            'class_name': self.school_class.name if self.school_class else None,
            'term': self.term,
            'academic_year': self.academic_year,
            'week_number': self.week_number,
            'topic': self.topic,
            'subtopics': self.subtopics,
            'objectives': self.objectives,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ClassroomObservation(db.Model):
    __tablename__ = 'classroom_observations'

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    observer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    observation_date = db.Column(db.Date, nullable=False)
    lesson_delivery = db.Column(db.Integer)
    student_engagement = db.Column(db.Integer)
    classroom_management = db.Column(db.Integer)
    content_knowledge = db.Column(db.Integer)
    use_of_resources = db.Column(db.Integer)
    overall_rating = db.Column(db.Integer)
    strengths = db.Column(db.Text)
    areas_for_improvement = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    teacher_response = db.Column(db.Text)
    status = db.Column(db.String(20), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship('Teacher', backref='observations')
    observer = db.relationship('User', foreign_keys=[observer_id])
    school_class = db.relationship('SchoolClass')
    subject = db.relationship('Subject')

    def to_dict(self):
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.user.full_name if self.teacher and self.teacher.user else None,
            'observer_name': self.observer.full_name if self.observer else None,
            'class_name': self.school_class.name if self.school_class else None,
            'subject_name': self.subject.name if self.subject else None,
            'observation_date': self.observation_date.isoformat() if self.observation_date else None,
            'lesson_delivery': self.lesson_delivery,
            'student_engagement': self.student_engagement,
            'classroom_management': self.classroom_management,
            'content_knowledge': self.content_knowledge,
            'use_of_resources': self.use_of_resources,
            'overall_rating': self.overall_rating,
            'strengths': self.strengths,
            'areas_for_improvement': self.areas_for_improvement,
            'recommendations': self.recommendations,
            'teacher_response': self.teacher_response,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class SyllabusCoverage(db.Model):
    __tablename__ = 'syllabus_coverage'

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    term = db.Column(db.String(20), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)
    total_topics = db.Column(db.Integer, default=0)
    covered_topics = db.Column(db.Integer, default=0)
    percentage = db.Column(db.Float, default=0)
    remarks = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship('Teacher', backref='syllabus_records')
    subject = db.relationship('Subject')
    school_class = db.relationship('SchoolClass')

    def to_dict(self):
        return {
            'id': self.id,
            'teacher_name': self.teacher.user.full_name if self.teacher and self.teacher.user else None,
            'subject_name': self.subject.name if self.subject else None,
            'class_name': self.school_class.name if self.school_class else None,
            'term': self.term,
            'academic_year': self.academic_year,
            'total_topics': self.total_topics,
            'covered_topics': self.covered_topics,
            'percentage': self.percentage,
            'remarks': self.remarks,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
