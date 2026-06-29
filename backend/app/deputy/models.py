from datetime import datetime
from backend.app import db


class DisciplineRecord(db.Model):
    __tablename__ = 'discipline_records'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    incident_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    category = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), default='minor')
    description = db.Column(db.Text, nullable=False)
    action_taken = db.Column(db.Text)
    status = db.Column(db.String(20), default='open')
    parent_notified = db.Column(db.Boolean, default=False)
    parent_meeting_date = db.Column(db.DateTime)
    counseling_referred = db.Column(db.Boolean, default=False)
    suspension_days = db.Column(db.Integer, default=0)
    resolution_notes = db.Column(db.Text)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='discipline_records')
    reporter = db.relationship('User', foreign_keys=[reported_by])
    resolver = db.relationship('User', foreign_keys=[resolved_by])

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'admission_number': self.student.admission_number if self.student else None,
            'reported_by': self.reported_by,
            'reporter_name': self.reporter.full_name if self.reporter else None,
            'incident_date': self.incident_date.isoformat() if self.incident_date else None,
            'category': self.category,
            'severity': self.severity,
            'description': self.description,
            'action_taken': self.action_taken,
            'status': self.status,
            'parent_notified': self.parent_notified,
            'parent_meeting_date': self.parent_meeting_date.isoformat() if self.parent_meeting_date else None,
            'counseling_referred': self.counseling_referred,
            'suspension_days': self.suspension_days,
            'resolution_notes': self.resolution_notes,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    leave_type = db.Column(db.String(30), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship('Teacher', backref='leave_requests')
    approver = db.relationship('User', foreign_keys=[approved_by])

    def to_dict(self):
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.user.full_name if self.teacher and self.teacher.user else None,
            'employee_id': self.teacher.employee_id if self.teacher else None,
            'leave_type': self.leave_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'reason': self.reason,
            'status': self.status,
            'approved_by_name': self.approver.full_name if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejection_reason': self.rejection_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ClassTeacherAllocation(db.Model):
    __tablename__ = 'class_teacher_allocations'

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    stream_id = db.Column(db.Integer, db.ForeignKey('streams.id'))
    academic_year = db.Column(db.String(20), nullable=False)
    term = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    allocated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    allocated_at = db.Column(db.DateTime, default=datetime.utcnow)
    deallocated_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    teacher = db.relationship('Teacher', backref='ct_allocations')
    school_class = db.relationship('SchoolClass', backref='ct_allocations')
    stream = db.relationship('Stream', backref='ct_allocations')
    allocator = db.relationship('User', foreign_keys=[allocated_by])

    def to_dict(self):
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.user.full_name if self.teacher and self.teacher.user else None,
            'employee_id': self.teacher.employee_id if self.teacher else None,
            'class_id': self.class_id,
            'class_name': self.school_class.name if self.school_class else None,
            'stream_id': self.stream_id,
            'stream_name': self.stream.name if self.stream else None,
            'academic_year': self.academic_year,
            'term': self.term,
            'is_active': self.is_active,
            'allocated_by_name': self.allocator.full_name if self.allocator else None,
            'allocated_at': self.allocated_at.isoformat() if self.allocated_at else None,
            'deallocated_at': self.deallocated_at.isoformat() if self.deallocated_at else None,
            'notes': self.notes,
        }


class DutyRoster(db.Model):
    __tablename__ = 'duty_rosters'

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    duty_type = db.Column(db.String(50), nullable=False)
    day_of_week = db.Column(db.Integer)
    duty_date = db.Column(db.Date)
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    location = db.Column(db.String(100))
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='assigned')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship('Teacher', backref='duty_rosters')
    creator = db.relationship('User', foreign_keys=[created_by])

    def to_dict(self):
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.user.full_name if self.teacher and self.teacher.user else None,
            'duty_type': self.duty_type,
            'day_of_week': self.day_of_week,
            'duty_date': self.duty_date.isoformat() if self.duty_date else None,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'location': self.location,
            'notes': self.notes,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class TeacherAttendance(db.Model):
    __tablename__ = 'teacher_attendances'

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='present')
    check_in = db.Column(db.Time)
    check_out = db.Column(db.Time)
    remarks = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship('Teacher', backref='attendances')
    recorder = db.relationship('User', foreign_keys=[recorded_by])

    def to_dict(self):
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.user.full_name if self.teacher and self.teacher.user else None,
            'employee_id': self.teacher.employee_id if self.teacher else None,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status,
            'check_in': str(self.check_in) if self.check_in else None,
            'check_out': str(self.check_out) if self.check_out else None,
            'remarks': self.remarks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class WelfareRecord(db.Model):
    __tablename__ = 'welfare_records'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    action_taken = db.Column(db.Text)
    status = db.Column(db.String(20), default='open')
    priority = db.Column(db.String(20), default='medium')
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='welfare_records')
    reporter = db.relationship('User', foreign_keys=[reported_by])

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'category': self.category,
            'description': self.description,
            'action_taken': self.action_taken,
            'status': self.status,
            'priority': self.priority,
            'reporter_name': self.reporter.full_name if self.reporter else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
