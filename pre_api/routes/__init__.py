from .admin_routes import admin_bp
from .auth_routes import auth_bp
from .student_routes import student_bp
from .tutors_routes import tutors_bp
from .chatbot import chatbot_bp

__all__ = ["admin_bp", "auth_bp", "student_bp", "tutors_bp", "chatbot_bp"]
