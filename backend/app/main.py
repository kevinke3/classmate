from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('auth/login.html')


@main_bp.route('/login')
def login():
    return render_template('auth/login.html')


@main_bp.route('/register')
def register():
    return render_template('auth/register.html')


@main_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard/index.html')


@main_bp.route('/students')
def students():
    return render_template('students/index.html')


@main_bp.route('/teachers')
def teachers():
    return render_template('teachers/index.html')


@main_bp.route('/academics')
def academics():
    return render_template('academics/index.html')


@main_bp.route('/finance')
def finance():
    return render_template('finance/index.html')


@main_bp.route('/attendance')
def attendance():
    return render_template('attendance/index.html')


@main_bp.route('/messages')
def messages():
    return render_template('messages/index.html')


@main_bp.route('/settings')
def settings():
    return render_template('settings/index.html')


@main_bp.route('/admin')
def admin_portal():
    return render_template('admin/index.html')


@main_bp.route('/parent-portal')
def parent_portal():
    return render_template('parent/index.html')


@main_bp.route('/student-portal')
def student_portal():
    return render_template('student/index.html')


@main_bp.route('/teacher-portal')
def teacher_portal():
    return render_template('teacher/index.html')


@main_bp.route('/finance-portal')
def finance_portal():
    return render_template('finance/portal.html')
