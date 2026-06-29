from datetime import datetime
from backend.app import db


class BehaviorRecord(db.Model):
    __tablename__ = 'behavior_records'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    behavior_type = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    action_taken = db.Column(db.Text)
    points = db.Column(db.Integer, default=0)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='behavior_records')
    recorder = db.relationship('User', foreign_keys=[recorded_by])

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'admission_number': self.student.admission_number if self.student else None,
            'recorded_by_name': self.recorder.full_name if self.recorder else None,
            'behavior_type': self.behavior_type,
            'category': self.category,
            'description': self.description,
            'action_taken': self.action_taken,
            'points': self.points,
            'date': self.date.isoformat() if self.date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class CounselingNote(db.Model):
    __tablename__ = 'counseling_notes'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    counselor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    category = db.Column(db.String(50), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    recommendations = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')
    is_confidential = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='counseling_notes')
    counselor = db.relationship('User', foreign_keys=[counselor_id])

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'counselor_name': self.counselor.full_name if self.counselor else None,
            'session_date': self.session_date.isoformat() if self.session_date else None,
            'category': self.category,
            'summary': self.summary,
            'recommendations': self.recommendations,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'status': self.status,
            'is_confidential': self.is_confidential,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class HomeworkRecord(db.Model):
    __tablename__ = 'homework_records'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    submitted_at = db.Column(db.DateTime)
    marks = db.Column(db.Float)
    remarks = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='homework_records')
    assignment = db.relationship('Assignment', backref='submissions')
    recorder = db.relationship('User', foreign_keys=[recorded_by])

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'assignment_id': self.assignment_id,
            'assignment_title': self.assignment.title if self.assignment else None,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'marks': self.marks,
            'remarks': self.remarks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
