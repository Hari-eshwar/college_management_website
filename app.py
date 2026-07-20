import os
import sys
import logging
from flask import Flask, render_template, redirect, url_for, jsonify
from flask_login import LoginManager
from flask_cors import CORS
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash
from database.models import db, User, Student, Faculty
from firebase import firebase_service
from routes import auth_bp, admin_bp, faculty_bp, student_bp, api_bp
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'smart-attendance-secret-key-change-in-production')
db_url = os.getenv('DATABASE_URL', 'sqlite:///smart_attendance.db')
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
if 'postgresql' in db_url and 'sslmode' not in db_url:
    db_url += '?sslmode=require' if '?' not in db_url else '&sslmode=require'
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 5,
    'max_overflow': 2,
}
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['SNAPSHOT_FOLDER'] = os.path.join('static', 'snapshots')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

app.config['MAIL_SERVER'] = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('SMTP_PORT', '587'))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('SMTP_EMAIL', '')
app.config['MAIL_PASSWORD'] = os.getenv('SMTP_PASSWORD', '')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SNAPSHOT_FOLDER'], exist_ok=True)
os.makedirs('dataset', exist_ok=True)
os.makedirs('models', exist_ok=True)
os.makedirs('reports', exist_ok=True)

db.init_app(app)
CORS(app)
csrf = CSRFProtect(app)
csrf.exempt(api_bp)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(faculty_bp)
app.register_blueprint(student_bp)
app.register_blueprint(api_bp)

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now(timezone.utc).isoformat()})

def seed_admin():
    with app.app_context():
        db.create_all()
        import sqlalchemy as sa
        try:
            insp = sa.inspect(db.engine)
            cols = [c['name'] for c in insp.get_columns('students')]
            if 'backlog_subjects' not in cols:
                db.session.execute(db.text("ALTER TABLE students ADD COLUMN backlog_subjects TEXT DEFAULT ''"))
                db.session.commit()
        except Exception as e:
            logger.warning('Migration backlog_subjects skipped: %s', e)
        try:
            insp = sa.inspect(db.engine)
            cols = [c['name'] for c in insp.get_columns('attendance')]
            for col in ['emotion', 'emotion_probability', 'focus_score', 'confidence_score']:
                if col in cols:
                    db.session.execute(db.text(f'ALTER TABLE attendance DROP COLUMN {col}'))
            if any(c in cols for c in ['emotion', 'emotion_probability', 'focus_score', 'confidence_score']):
                db.session.commit()
        except Exception:
            pass
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password=generate_password_hash('admin123'),
                         role='admin', email='admin@smartattendance.com')
            db.session.add(admin)
            db.session.commit()
            logger.info('Admin user created (admin/admin123)')
        if not Faculty.query.filter_by(faculty_id='FAC001').first():
            demo = Faculty(faculty_id='FAC001', name='Dr. Demo Faculty',
                           email='faculty@smartattendance.com', phone='9876543210',
                           department='Computer Science')
            db.session.add(demo)
            if not User.query.filter_by(username='faculty').first():
                u = User(username='faculty', password=generate_password_hash('faculty123'),
                         role='faculty', email='faculty@smartattendance.com')
                db.session.add(u)
            db.session.commit()
            logger.info('Demo faculty created (faculty/faculty123)')
        if not Student.query.filter_by(student_id='STU001').first():
            s = Student(student_id='STU001', usn='1BM21CS001', name='Demo Student',
                        department='Computer Science', semester='5', section='A',
                        email='student@smartattendance.com', phone='9876543211')
            db.session.add(s)
            if not User.query.filter_by(username='student').first():
                u = User(username='student', password=generate_password_hash('student123'),
                         role='student', email='student@smartattendance.com')
                db.session.add(u)
            db.session.commit()
            logger.info('Demo student created (student/student123)')

initialize_firebase = firebase_service.initialize()
if initialize_firebase:
    logger.info('Firebase initialized successfully')
else:
    logger.info('Firebase not configured - running without Firebase')

with app.app_context():
    seed_admin()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
