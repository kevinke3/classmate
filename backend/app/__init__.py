from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_mail import Mail
from flask_cors import CORS

from backend.config import config

db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO()
mail = Mail()


def create_app(config_name='default'):
    app = Flask(
        __name__,
        static_folder='../../frontend/static',
        template_folder='../../frontend/templates'
    )
    app.config.from_object(config[config_name])

    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    mail.init_app(app)
    CORS(app)

    from backend.app.auth.routes import auth_bp
    from backend.app.users.routes import users_bp
    from backend.app.students.routes import students_bp
    from backend.app.teachers.routes import teachers_bp
    from backend.app.academics.routes import academics_bp
    from backend.app.attendance.routes import attendance_bp
    from backend.app.finance.routes import finance_bp
    import backend.app.finance.models  # noqa: F401 - register finance models
    from backend.app.examinations.routes import examinations_bp
    from backend.app.messaging.routes import messaging_bp
    from backend.app.notifications.routes import notifications_bp
    from backend.app.analytics.routes import analytics_bp
    from backend.app.settings.routes import settings_bp
    from backend.app.documents.routes import documents_bp
    from backend.app.deputy.routes import deputy_bp
    import backend.app.deputy.models  # noqa: F401
    from backend.app.senior_teacher.routes import senior_teacher_bp
    import backend.app.senior_teacher.models  # noqa: F401
    from backend.app.hos.routes import hos_bp
    import backend.app.hos.models  # noqa: F401
    from backend.app.class_teacher.routes import ct_bp
    import backend.app.class_teacher.models  # noqa: F401
    from backend.app.main import main_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(students_bp, url_prefix='/api/students')
    app.register_blueprint(teachers_bp, url_prefix='/api/teachers')
    app.register_blueprint(academics_bp, url_prefix='/api/academics')
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    app.register_blueprint(finance_bp, url_prefix='/api/finance')
    app.register_blueprint(examinations_bp, url_prefix='/api/examinations')
    app.register_blueprint(messaging_bp, url_prefix='/api/messaging')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    app.register_blueprint(deputy_bp, url_prefix='/api/deputy')
    app.register_blueprint(senior_teacher_bp, url_prefix='/api/senior-teacher')
    app.register_blueprint(hos_bp, url_prefix='/api/hos')
    app.register_blueprint(ct_bp, url_prefix='/api/class-teacher')
    app.register_blueprint(main_bp)

    return app
