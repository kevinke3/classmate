from datetime import datetime
from backend.app import db


class AcademicTarget(db.Model):
    __tablename__ = 'academic_targets'

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    academic_year = db.Column(db.String(20), nullable=False)
    term = db.Column(db.String(20), nullable=False)
    target_mean = db.Column(db.Float)
    target_pass_rate = db.Column(db.Float)
    actual_mean = db.Column(db.Float)
    actual_pass_rate = db.Column(db.Float)
    remarks = db.Column(db.Text)
    set_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    school_class = db.relationship('SchoolClass', backref='academic_targets')
    subject = db.relationship('Subject', backref='academic_targets')
    setter = db.relationship('User', foreign_keys=[set_by])

    def to_dict(self):
        return {
            'id': self.id,
            'class_name': self.school_class.name if self.school_class else 'All',
            'subject_name': self.subject.name if self.subject else 'Overall',
            'academic_year': self.academic_year,
            'term': self.term,
            'target_mean': self.target_mean,
            'target_pass_rate': self.target_pass_rate,
            'actual_mean': self.actual_mean,
            'actual_pass_rate': self.actual_pass_rate,
            'remarks': self.remarks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class AcademicIntervention(db.Model):
    __tablename__ = 'academic_interventions'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    intervention_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    target_score = db.Column(db.Float)
    current_score = db.Column(db.Float)
    status = db.Column(db.String(20), default='active')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='interventions')
    subject = db.relationship('Subject')
    creator = db.relationship('User', foreign_keys=[created_by])

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'admission_number': self.student.admission_number if self.student else None,
            'subject_name': self.subject.name if self.subject else None,
            'intervention_type': self.intervention_type,
            'description': self.description,
            'target_score': self.target_score,
            'current_score': self.current_score,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class GradeAnalysis(db.Model):
    __tablename__ = 'grade_analyses'

    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    mean_score = db.Column(db.Float)
    highest_score = db.Column(db.Float)
    lowest_score = db.Column(db.Float)
    pass_count = db.Column(db.Integer, default=0)
    fail_count = db.Column(db.Integer, default=0)
    grade_a = db.Column(db.Integer, default=0)
    grade_b = db.Column(db.Integer, default=0)
    grade_c = db.Column(db.Integer, default=0)
    grade_d = db.Column(db.Integer, default=0)
    grade_e = db.Column(db.Integer, default=0)
    total_students = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    examination = db.relationship('Examination', backref='analyses')
    school_class = db.relationship('SchoolClass')
    subject = db.relationship('Subject')

    def to_dict(self):
        return {
            'id': self.id,
            'exam_name': self.examination.name if self.examination else None,
            'class_name': self.school_class.name if self.school_class else 'All',
            'subject_name': self.subject.name if self.subject else 'Overall',
            'mean_score': self.mean_score,
            'highest_score': self.highest_score,
            'lowest_score': self.lowest_score,
            'pass_count': self.pass_count,
            'fail_count': self.fail_count,
            'grade_a': self.grade_a,
            'grade_b': self.grade_b,
            'grade_c': self.grade_c,
            'grade_d': self.grade_d,
            'grade_e': self.grade_e,
            'total_students': self.total_students,
            'pass_rate': round(self.pass_count / self.total_students * 100, 1) if self.total_students > 0 else 0,
        }
