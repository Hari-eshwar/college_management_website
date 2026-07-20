from flask import Blueprint

auth_bp = Blueprint('auth', __name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')
student_bp = Blueprint('student', __name__, url_prefix='/student')
api_bp = Blueprint('api', __name__, url_prefix='/api')

from . import auth_routes, admin_routes, faculty_routes, student_routes, api_routes
