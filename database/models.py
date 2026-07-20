from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date, time, timezone

db = SQLAlchemy()

def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True)
    is_verified = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=_utcnow)

class Student(db.Model):
    __tablename__ = 'students'
    student_id = db.Column(db.String(20), primary_key=True)
    usn = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.String(10), nullable=False)
    section = db.Column(db.String(5), nullable=False)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(15))
    parent_phone = db.Column(db.String(15))
    parent_email = db.Column(db.String(100))
    face_embedding_path = db.Column(db.String(200))
    profile_image = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    backlog_subjects = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=_utcnow)

    attendances = db.relationship('Attendance', backref='student', lazy=True)

class Faculty(db.Model):
    __tablename__ = 'faculty'
    faculty_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15))
    department = db.Column(db.String(50), nullable=False)
    semesters_handled = db.Column(db.Text, default='')  # comma-separated, e.g. "1,2,3"
    profile_image = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=_utcnow)

    attendances = db.relationship('Attendance', backref='faculty', lazy=True)
    timetables = db.relationship('Timetable', backref='faculty', lazy=True)
    leaves = db.relationship('LeaveRequest', backref='faculty', lazy=True)

class Subject(db.Model):
    __tablename__ = 'subjects'
    subject_id = db.Column(db.String(20), primary_key=True)
    subject_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.String(10), nullable=False)
    section = db.Column(db.String(5), default='A')
    is_lab = db.Column(db.Boolean, default=False)
    hours_per_week = db.Column(db.Integer, default=4)
    credits = db.Column(db.Integer, default=4)
    created_at = db.Column(db.DateTime, default=_utcnow)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    attendance_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('students.student_id'), nullable=False)
    faculty_id = db.Column(db.String(20), db.ForeignKey('faculty.faculty_id'), nullable=False)
    subject_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, default=lambda: date.today(), nullable=False)
    time = db.Column(db.Time, default=lambda: datetime.now().time())

    status = db.Column(db.String(20), default='Present')
    is_live_verified = db.Column(db.Boolean, default=False)
    is_late = db.Column(db.Boolean, default=False)
    snapshot_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=_utcnow)

class Timetable(db.Model):
    __tablename__ = 'timetable'
    timetable_id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.String(20), db.ForeignKey('faculty.faculty_id'), nullable=False)
    subject_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.String(10), nullable=False)
    section = db.Column(db.String(5), nullable=False)
    day = db.Column(db.String(15), nullable=False)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)
    room_number = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)

class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    leave_id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.String(20), db.ForeignKey('faculty.faculty_id'), nullable=False)
    faculty_name = db.Column(db.String(100))
    department = db.Column(db.String(50))
    leave_type = db.Column(db.String(50), nullable=False)
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    attachment = db.Column(db.String(200))
    status = db.Column(db.String(20), default='Pending')
    admin_remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, onupdate=_utcnow)

class Alert(db.Model):
    __tablename__ = 'alerts'
    alert_id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.String(20), db.ForeignKey('faculty.faculty_id'))
    alert_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    snapshot_path = db.Column(db.String(200))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    notification_id = db.Column(db.Integer, primary_key=True)
    recipient_type = db.Column(db.String(20), nullable=False)
    recipient_id = db.Column(db.String(20))
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

class AttendanceSession(db.Model):
    __tablename__ = 'attendance_sessions'
    session_id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.String(20), db.ForeignKey('faculty.faculty_id'), nullable=False)
    subject_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50))
    semester = db.Column(db.String(10))
    section = db.Column(db.String(5))
    status = db.Column(db.String(20), default='active')
    started_at = db.Column(db.DateTime, default=_utcnow)
    ended_at = db.Column(db.DateTime)
    total_students = db.Column(db.Integer, default=0)
    present_count = db.Column(db.Integer, default=0)
    late_count = db.Column(db.Integer, default=0)

class TestResult(db.Model):
    __tablename__ = 'test_results'
    result_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('students.student_id'), nullable=False)
    faculty_id = db.Column(db.String(20), db.ForeignKey('faculty.faculty_id'), nullable=False)
    subject_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.String(10), nullable=False)
    section = db.Column(db.String(5), nullable=False)
    test_type = db.Column(db.String(50), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    total_marks = db.Column(db.Float, default=100)
    grade = db.Column(db.String(5))
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=_utcnow)

    student = db.relationship('Student', backref='test_results')

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

    def __repr__(self):
        return f'<Department {self.name}>'

class DepartmentSection(db.Model):
    __tablename__ = 'department_sections'
    id = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(10), nullable=False)
    section = db.Column(db.String(5), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)
