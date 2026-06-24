"""Seed the database with sample data for development."""
from datetime import date, datetime, timedelta
from backend.app import create_app, db
from backend.app.models import (
    User, Student, Teacher, Parent, SchoolClass, Stream,
    Subject, Attendance, FeeStructure, FeeRecord, Examination,
    Grade, Announcement, Event, Notification, SchoolSettings,
    Invoice, Receipt
)


def seed():
    app = create_app('development')

    with app.app_context():
        db.create_all()

        if User.query.first():
            print('Database already seeded.')
            return

        # Admin user
        admin = User(
            email='admin@classmate.io',
            first_name='Admin',
            last_name='User',
            role='admin',
            phone='+254700000001',
            is_verified=True
        )
        admin.set_password('admin123')
        db.session.add(admin)

        # Teacher users
        teachers_data = [
            ('Mary', 'Kariuki', 'mary@classmate.io', 'Sciences', 'Biology', 'EMP/001'),
            ('Peter', 'Oloo', 'peter@classmate.io', 'Mathematics', 'Mathematics', 'EMP/002'),
            ('Agnes', 'Njeri', 'agnes@classmate.io', 'Languages', 'English', 'EMP/003'),
            ('John', 'Waweru', 'john@classmate.io', 'Sciences', 'Chemistry', 'EMP/004'),
            ('Sarah', 'Otieno', 'sarah@classmate.io', 'Humanities', 'History', 'EMP/005'),
        ]

        teachers = []
        for first, last, email, dept, spec, emp_id in teachers_data:
            user = User(
                email=email, first_name=first, last_name=last,
                role='teacher', is_verified=True
            )
            user.set_password('teacher123')
            db.session.add(user)
            db.session.flush()

            teacher = Teacher(
                user_id=user.id, employee_id=emp_id,
                department=dept, specialization=spec,
                qualification='Masters'
            )
            db.session.add(teacher)
            teachers.append(teacher)

        # Classes
        classes = []
        for level in range(1, 5):
            school_class = SchoolClass(
                name=f'Form {level}',
                level=level,
                academic_year='2025',
                capacity=200
            )
            db.session.add(school_class)
            db.session.flush()
            classes.append(school_class)

            for stream_name in ['East', 'West', 'North', 'South']:
                stream = Stream(name=stream_name, class_id=school_class.id)
                db.session.add(stream)

        db.session.flush()

        # Subjects
        subjects_data = [
            ('Mathematics', 'MATH', True),
            ('English', 'ENG', True),
            ('Kiswahili', 'KIS', True),
            ('Biology', 'BIO', False),
            ('Chemistry', 'CHEM', False),
            ('Physics', 'PHY', False),
            ('History', 'HIST', False),
            ('Geography', 'GEO', False),
        ]

        subjects = []
        for name, code, compulsory in subjects_data:
            subject = Subject(name=name, code=code, is_compulsory=compulsory)
            db.session.add(subject)
            subjects.append(subject)

        # Students (records only, no login accounts -- parents access via Parent Portal)
        students_data = [
            ('Grace', 'Wanjiku', 'ADM/2024/001', 'F'),
            ('James', 'Ochieng', 'ADM/2024/002', 'M'),
            ('Faith', 'Kamau', 'ADM/2024/003', 'F'),
            ('David', 'Mwangi', 'ADM/2024/004', 'M'),
            ('Lucy', 'Akinyi', 'ADM/2024/005', 'F'),
            ('Brian', 'Kiprop', 'ADM/2024/006', 'M'),
            ('Anne', 'Wambui', 'ADM/2024/007', 'F'),
            ('Kevin', 'Mutua', 'ADM/2024/008', 'M'),
        ]

        students = []
        for i, (first, last, adm_no, gender) in enumerate(students_data):
            student = Student(
                first_name=first,
                last_name=last,
                admission_number=adm_no,
                class_id=classes[i % 4].id,
                gender=gender,
                date_of_birth=date(2007, 1, 1) + timedelta(days=i * 45),
                guardian_name=f'Parent of {first}',
                guardian_phone=f'+25470000{1000 + i}'
            )
            db.session.add(student)
            students.append(student)

        # Finance officer user
        finance_user = User(
            email='finance@classmate.io',
            first_name='Susan',
            last_name='Muthoni',
            role='finance',
            phone='+254700000020',
            is_verified=True
        )
        finance_user.set_password('finance123')
        db.session.add(finance_user)
        db.session.flush()

        # Parent user
        parent_user = User(
            email='parent@classmate.io',
            first_name='Joseph',
            last_name='Wanjiku',
            role='parent',
            is_verified=True
        )
        parent_user.set_password('parent123')
        db.session.add(parent_user)
        db.session.flush()

        parent = Parent(user_id=parent_user.id, occupation='Engineer')
        db.session.add(parent)

        db.session.flush()

        # Fee structures
        for cls in classes:
            fee = FeeStructure(
                name=f'Tuition Fee - {cls.name}',
                class_id=cls.id,
                academic_year='2025',
                term='Term 1',
                amount=45000,
                due_date=date(2025, 3, 15)
            )
            db.session.add(fee)

        # Fee payments
        for student in students[:4]:
            payment = FeeRecord(
                student_id=student.id,
                amount_paid=45000,
                payment_method='mpesa',
                mpesa_receipt=f'QKJ{student.id}HDBS7R',
                status='completed'
            )
            db.session.add(payment)

        # Announcements
        announcements = [
            ('End of Term Exams', 'Exams begin June 28. All students must report by 7:30 AM.', 'high'),
            ('Sports Day', 'Annual sports day scheduled for July 10. All students to participate.', 'normal'),
            ('Parent-Teacher Conference', 'Form 4 parents meeting on July 2 at the auditorium.', 'normal'),
        ]

        for title, body, priority in announcements:
            ann = Announcement(
                title=title, body=body, priority=priority,
                created_by=admin.id
            )
            db.session.add(ann)

        # Events
        events = [
            ('End of Term Exams', date(2025, 6, 28), 'Main Hall', 'academic'),
            ('Parent-Teacher Conference', date(2025, 7, 2), 'Auditorium', 'meeting'),
            ('Sports Day', date(2025, 7, 10), 'Sports Field', 'sports'),
            ('Term Closes', date(2025, 7, 15), 'School', 'administrative'),
        ]

        for title, event_date, location, event_type in events:
            event = Event(
                title=title,
                event_date=datetime.combine(event_date, datetime.min.time()),
                location=location,
                event_type=event_type,
                created_by=admin.id
            )
            db.session.add(event)

        # School settings
        school = SchoolSettings(
            school_name='ClassMate Academy',
            motto='Excellence in Education',
            email='info@classmate.io',
            phone='+254 700 000 000',
            address='P.O. Box 12345, Nairobi, Kenya',
            academic_year='2025',
            current_term='Term 1'
        )
        db.session.add(school)

        # Invoices for students
        for i, student in enumerate(students):
            inv = Invoice(
                invoice_number=f'INV-2025-{i+1:04d}',
                student_id=student.id,
                amount=45000,
                balance=45000 if i >= 4 else 0,
                description='Tuition Fee - Term 1',
                term='Term 1',
                academic_year='2025',
                due_date=date(2025, 3, 15),
                status='paid' if i < 4 else 'unpaid',
                created_by=finance_user.id
            )
            db.session.add(inv)

        db.session.flush()

        # Receipts for completed payments
        payments = FeeRecord.query.filter_by(status='completed').all()
        for pay in payments:
            receipt = Receipt(
                receipt_number=f'RCP-2025-{pay.id:04d}',
                payment_id=pay.id,
                student_id=pay.student_id,
                amount=pay.amount_paid,
                payment_method=pay.payment_method,
                description='Tuition Fee Payment',
                generated_by=finance_user.id
            )
            db.session.add(receipt)

        db.session.commit()
        print('Database seeded successfully!')
        print('Login credentials:')
        print('  Admin: admin@classmate.io / admin123')
        print('  Finance: finance@classmate.io / finance123')
        print('  Teacher: mary@classmate.io / teacher123')
        print('  Parent: parent@classmate.io / parent123')


if __name__ == '__main__':
    seed()
