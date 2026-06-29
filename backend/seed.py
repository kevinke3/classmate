"""Seed the database with sample data for development."""
from datetime import date, datetime, timedelta
from backend.app import create_app, db
from backend.app.models import (
    User, Student, Teacher, Parent, ParentStudent, SchoolClass, Stream,
    Subject, Attendance, FeeStructure, FeeRecord, Examination,
    Grade, Announcement, Event, Notification, SchoolSettings,
    Invoice, Receipt, ClassTeacher
)
from backend.app.finance.models import (
    FeeCategory, FeeComponent, ExpenseCategory, Expense,
    Income, FinanceSettings, BankAccount, FinanceNotification
)
from backend.app.deputy.models import (
    DisciplineRecord, LeaveRequest, ClassTeacherAllocation,
    DutyRoster, TeacherAttendance, WelfareRecord
)
from backend.app.senior_teacher.models import (
    LessonPlan, SchemeOfWork, ClassroomObservation, SyllabusCoverage
)
from backend.app.hos.models import AcademicTarget, AcademicIntervention
from backend.app.class_teacher.models import BehaviorRecord, CounselingNote


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

        # Teacher users with sub-roles
        # (first, last, email, dept, spec, emp_id, teacher_role)
        teachers_data = [
            ('Mary', 'Kariuki', 'mary@classmate.io', 'Sciences', 'Biology', 'EMP/001', 'class_teacher'),
            ('Peter', 'Oloo', 'peter@classmate.io', 'Mathematics', 'Mathematics', 'EMP/002', 'head_of_studies'),
            ('Agnes', 'Njeri', 'agnes@classmate.io', 'Languages', 'English', 'EMP/003', 'senior_teacher'),
            ('John', 'Waweru', 'john@classmate.io', 'Sciences', 'Chemistry', 'EMP/004', 'deputy'),
            ('Sarah', 'Otieno', 'sarah@classmate.io', 'Humanities', 'History', 'EMP/005', 'class_teacher'),
        ]

        teachers = []
        for first, last, email, dept, spec, emp_id, t_role in teachers_data:
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
                qualification='Masters',
                teacher_role=t_role
            )
            db.session.add(teacher)
            teachers.append((user, teacher))

        # Unpack teacher references for portal seed data
        mary_user, mary_teacher = teachers[0]
        peter_user, peter_teacher = teachers[1]
        agnes_user, agnes_teacher = teachers[2]
        john_user, john_teacher = teachers[3]
        sarah_user, sarah_teacher = teachers[4]

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

        # Link parent to first student
        parent_student = ParentStudent(
            parent_id=parent.id,
            student_id=students[0].id,
            relationship='parent'
        )
        db.session.add(parent_student)

        # Assign class teachers to classes
        db.session.flush()
        # Mary (class_teacher) -> Form 1, Sarah (class_teacher) -> Form 2
        ct1 = ClassTeacher(teacher_id=mary_teacher.id, class_id=classes[0].id, is_class_teacher=True)
        ct2 = ClassTeacher(teacher_id=sarah_teacher.id, class_id=classes[1].id, is_class_teacher=True)
        # Deputy John also assigned to Form 3 as class teacher
        ct3 = ClassTeacher(teacher_id=john_teacher.id, class_id=classes[2].id, is_class_teacher=True)
        db.session.add_all([ct1, ct2, ct3])

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

        # Finance Settings
        fin_settings = FinanceSettings(
            currency='KES',
            currency_symbol='KES',
            receipt_prefix='RCP',
            invoice_prefix='INV',
            grace_period_days=14,
            auto_reminder=True,
            reminder_days_before=7,
            payment_methods='cash,bank_transfer,cheque,mobile_money',
            receipt_footer_text='Thank you for your payment. This is an official receipt.',
            invoice_footer_text='Please make payment before the due date to avoid penalties.'
        )
        db.session.add(fin_settings)

        # Fee Categories
        categories_data = [
            ('Tuition', 'TUI', 'Term tuition fees', True),
            ('Boarding', 'BRD', 'Boarding fees for residential students', False),
            ('Transport', 'TRN', 'School transport fees', False),
            ('Examination', 'EXM', 'Exam registration and processing fees', True),
            ('Activity', 'ACT', 'Co-curricular and club activities', False),
            ('Meals', 'MEL', 'Lunch and meals program', False),
            ('Uniform', 'UNI', 'School uniform fees', False),
            ('Development', 'DEV', 'School development levy', True),
            ('Library', 'LIB', 'Library and resource fees', True),
            ('ICT', 'ICT', 'Computer and technology fees', True),
        ]
        for i, (name, code, desc, mandatory) in enumerate(categories_data):
            cat = FeeCategory(name=name, code=code, description=desc, is_mandatory=mandatory, sort_order=i)
            db.session.add(cat)

        # Expense Categories
        exp_categories = [
            ('Salaries', 'SAL', 'Staff salaries and wages'),
            ('Utilities', 'UTL', 'Electricity, water, internet'),
            ('Maintenance', 'MNT', 'Building and equipment maintenance'),
            ('Supplies', 'SUP', 'Teaching and office supplies'),
            ('Transport', 'EXP-TRN', 'Vehicle fuel and maintenance'),
            ('Food', 'FD', 'Kitchen and catering expenses'),
            ('Equipment', 'EQP', 'Furniture and equipment purchases'),
        ]
        for name, code, desc in exp_categories:
            db.session.add(ExpenseCategory(name=name, code=code, description=desc))
        db.session.flush()

        # Bank Account
        bank = BankAccount(
            bank_name='Kenya Commercial Bank',
            account_name='ClassMate Academy',
            account_number='1234567890',
            branch='Main Branch',
            is_primary=True
        )
        db.session.add(bank)

        # Sample expenses
        expense_items = [
            (1, 50000, 'Monthly electricity bill', 'Kenya Power', 'bank_transfer'),
            (2, 25000, 'Water supply', 'Nairobi Water', 'bank_transfer'),
            (3, 15000, 'Classroom repairs', 'ABC Contractors', 'cheque'),
            (4, 8000, 'Exam papers printing', 'PrintExpress', 'cash'),
        ]
        for cat_id, amount, desc, vendor, method in expense_items:
            exp = Expense(
                category_id=cat_id,
                amount=amount,
                description=desc,
                vendor=vendor,
                payment_method=method,
                expense_date=date.today() - timedelta(days=cat_id * 3),
                recorded_by=finance_user.id,
                status='recorded'
            )
            db.session.add(exp)

        # Sample income
        inc = Income(
            source='Government Grant',
            amount=200000,
            description='Capitation grant for Term 1',
            income_type='grant',
            income_date=date.today() - timedelta(days=30),
            recorded_by=finance_user.id
        )
        db.session.add(inc)

        # Deputy Portal: Discipline records
        students_all = Student.query.all()
        for i, (cat, sev, desc) in enumerate([
            ('Misconduct', 'minor', 'Talking during assembly'),
            ('Truancy', 'major', 'Absent from afternoon classes without permission'),
            ('Fighting', 'critical', 'Physical altercation in the dining hall'),
            ('Insubordination', 'minor', 'Refused to follow teacher instructions'),
        ]):
            dr = DisciplineRecord(
                student_id=students_all[i % len(students_all)].id,
                reported_by=john_user.id,
                incident_date=date.today() - timedelta(days=i * 3),
                category=cat, severity=sev, description=desc,
                status='open' if i < 3 else 'resolved',
                action_taken='Verbal warning' if sev == 'minor' else 'Written warning',
            )
            db.session.add(dr)

        # Deputy: Leave requests
        for t, lt in [(mary_teacher, 'Sick Leave'), (peter_teacher, 'Personal Leave')]:
            lr = LeaveRequest(
                teacher_id=t.id,
                leave_type=lt,
                start_date=date.today() + timedelta(days=5),
                end_date=date.today() + timedelta(days=7),
                reason=f'{lt} due to personal reasons',
                status='pending',
            )
            db.session.add(lr)

        # Deputy: Class Teacher Allocations
        for t, cls in [(mary_teacher, classes[0]), (sarah_teacher, classes[1])]:
            cta = ClassTeacherAllocation(
                teacher_id=t.id,
                class_id=cls.id,
                academic_year=str(date.today().year),
                allocated_by=john_user.id,
                is_active=True,
            )
            db.session.add(cta)

        # Deputy: Teacher Attendance
        for t in [mary_teacher, peter_teacher, agnes_teacher, sarah_teacher]:
            ta = TeacherAttendance(
                teacher_id=t.id,
                date=date.today(),
                status='present',
                recorded_by=john_user.id,
            )
            db.session.add(ta)

        # Deputy: Welfare records
        wr = WelfareRecord(
            student_id=students_all[0].id,
            reported_by=mary_user.id,
            category='Health',
            description='Student has recurring headaches, needs medical check.',
            priority='medium',
            status='open',
        )
        db.session.add(wr)

        # Deputy: Duty Roster
        duty = DutyRoster(
            teacher_id=agnes_teacher.id,
            duty_type='Morning Assembly',
            duty_date=date.today(),
            start_time='07:00',
            end_time='07:30',
            location='Assembly Ground',
            created_by=john_user.id,
        )
        db.session.add(duty)

        # Senior Teacher: Lesson Plans
        subjects_all = Subject.query.all()
        for i, topic in enumerate(['Introduction to Algebra', 'The Water Cycle', 'Parts of Speech']):
            lp = LessonPlan(
                teacher_id=[mary_teacher, peter_teacher, agnes_teacher][i % 3].id,
                subject_id=subjects_all[i % len(subjects_all)].id,
                class_id=classes[0].id,
                topic=topic,
                objectives='Students will understand ' + topic.lower(),
                lesson_date=date.today() - timedelta(days=i),
                status='completed' if i == 0 else 'planned',
            )
            db.session.add(lp)

        # Senior Teacher: Schemes of Work
        sw = SchemeOfWork(
            teacher_id=mary_teacher.id,
            subject_id=subjects_all[0].id,
            class_id=classes[0].id,
            term='Term 1',
            academic_year=str(date.today().year),
            week_number=1,
            topic='Number Systems',
            objectives='Understand real numbers',
            status='completed',
        )
        db.session.add(sw)

        # Senior Teacher: Observations
        obs = ClassroomObservation(
            teacher_id=mary_teacher.id,
            observer_id=agnes_user.id,
            observation_date=date.today() - timedelta(days=2),
            lesson_delivery=4,
            student_engagement=5,
            classroom_management=4,
            content_knowledge=5,
            overall_rating=4,
            strengths='Excellent student engagement, clear explanations',
            areas_for_improvement='More group activities',
        )
        db.session.add(obs)

        # Senior Teacher: Syllabus Coverage
        for i, (t, s, pct) in enumerate([
            (mary_teacher, subjects_all[0], 72),
            (peter_teacher, subjects_all[1] if len(subjects_all) > 1 else subjects_all[0], 55),
        ]):
            sc = SyllabusCoverage(
                teacher_id=t.id,
                subject_id=s.id,
                class_id=classes[0].id,
                total_topics=20,
                covered_topics=int(20 * pct / 100),
                percentage=pct,
                term='Term 1',
                academic_year=str(date.today().year),
            )
            db.session.add(sc)

        # HoS: Academic Targets
        at = AcademicTarget(
            class_id=classes[0].id,
            academic_year=str(date.today().year),
            term='Term 1',
            target_mean=65.0,
            target_pass_rate=80.0,
            set_by=peter_user.id,
        )
        db.session.add(at)

        # HoS: Interventions
        ai = AcademicIntervention(
            student_id=students_all[0].id,
            subject_id=subjects_all[0].id if subjects_all else None,
            intervention_type='Remedial Classes',
            description='Weekly remedial sessions for Mathematics improvement',
            current_score=35.0,
            target_score=50.0,
            created_by=peter_user.id,
            status='active',
        )
        db.session.add(ai)

        # Class Teacher: Behavior Records
        for bt, cat, desc, pts in [
            ('positive', 'Leadership', 'Led class discussion effectively', 5),
            ('negative', 'Conduct', 'Disrupted class during lesson', -3),
        ]:
            br = BehaviorRecord(
                student_id=students_all[0].id,
                recorded_by=mary_user.id,
                behavior_type=bt,
                category=cat,
                description=desc,
                points=pts,
                date=date.today() - timedelta(days=1),
            )
            db.session.add(br)

        # Class Teacher: Counseling Notes
        cn = CounselingNote(
            student_id=students_all[0].id,
            counselor_id=mary_user.id,
            session_date=date.today() - timedelta(days=3),
            category='Academic',
            summary='Discussion about improving study habits.',
            recommendations='Create a study schedule, reduce screen time.',
            follow_up_date=date.today() + timedelta(days=14),
            status='active',
        )
        db.session.add(cn)

        db.session.commit()
        print('Database seeded successfully!')
        print('Login credentials:')
        print('  Admin: admin@classmate.io / admin123')
        print('  Finance: finance@classmate.io / finance123')
        print('  Teacher (Class Teacher): mary@classmate.io / teacher123')
        print('  Teacher (Head of Studies): peter@classmate.io / teacher123')
        print('  Teacher (Senior Teacher): agnes@classmate.io / teacher123')
        print('  Teacher (Deputy): john@classmate.io / teacher123')
        print('  Parent: parent@classmate.io / parent123')


if __name__ == '__main__':
    seed()
