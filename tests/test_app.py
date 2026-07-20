import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from app import app, db, User
from database.models import Student, Faculty, Attendance, Timetable, LeaveRequest
from werkzeug.security import generate_password_hash
from datetime import date, datetime

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-key'
    WTF_CSRF_ENABLED = False
    DEBUG = False

class SmartAttendanceTestCase(unittest.TestCase):
    def setUp(self):
        app.config.from_object(TestConfig)
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_1_health_endpoint(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')

    def test_2_landing_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Smart Attendance', response.data)

    def test_3_login_page(self):
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_4_admin_login(self):
        with app.app_context():
            admin = User(username='admin', password=generate_password_hash('admin123'), role='admin')
            db.session.add(admin)
            db.session.commit()
        response = self.app.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_5_invalid_login(self):
        response = self.app.post('/login', data={
            'username': 'wrong',
            'password': 'wrong'
        }, follow_redirects=True)
        self.assertIn(b'Invalid', response.data)

    def test_6_api_login(self):
        with app.app_context():
            admin = User(username='admin', password=generate_password_hash('admin123'), role='admin')
            db.session.add(admin)
            db.session.commit()
        response = self.app.post('/api/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')

    def test_7_database_models(self):
        with app.app_context():
            student = Student(
                student_id='STU001',
                usn='1BM21CS001',
                name='Test Student',
                department='CS',
                semester='5',
                section='A',
                email='test@test.com',
                parent_phone='9999999999'
            )
            db.session.add(student)
            faculty = Faculty(
                faculty_id='FAC001',
                name='Test Faculty',
                email='faculty@test.com',
                department='CS'
            )
            db.session.add(faculty)
            db.session.commit()
            self.assertEqual(Student.query.count(), 1)
            self.assertEqual(Faculty.query.count(), 1)

    def test_8_attendance_model(self):
        with app.app_context():
            student = Student(student_id='STU001', usn='USN001', name='S1', department='CS', semester='5', section='A')
            faculty = Faculty(faculty_id='FAC001', name='F1', email='f1@t.com', department='CS')
            db.session.add_all([student, faculty])
            db.session.commit()
            attendance = Attendance(
                student_id='STU001', faculty_id='FAC001',
                subject_name='AI', status='Present',

            )
            db.session.add(attendance)
            db.session.commit()
            self.assertEqual(Attendance.query.count(), 1)
            self.assertEqual(attendance.status, 'Present')

    def test_9_leave_request_model(self):
        with app.app_context():
            faculty = Faculty(faculty_id='FAC001', name='F1', email='f1@t.com', department='CS')
            db.session.add(faculty)
            db.session.commit()
            leave = LeaveRequest(
                faculty_id='FAC001', leave_type='Sick',
                from_date=date.today(), to_date=date.today(),
                reason='Not feeling well'
            )
            db.session.add(leave)
            db.session.commit()
            self.assertEqual(LeaveRequest.query.count(), 1)
            self.assertEqual(leave.status, 'Pending')

    def test_10_api_endpoints(self):
        with app.app_context():
            admin = User(username='admin', password=generate_password_hash('admin123'), role='admin')
            db.session.add(admin)
            faculty_user = User(username='faculty', password=generate_password_hash('faculty123'), role='faculty', email='f@t.com')
            db.session.add(faculty_user)
            faculty = Faculty(faculty_id='FAC001', name='F1', email='f@t.com', department='CS')
            db.session.add(faculty)
            student = Student(student_id='STU001', usn='USN001', name='S1', department='CS', semester='5', section='A')
            db.session.add(student)
            db.session.commit()
        self.app.post('/login', data={'username': 'faculty', 'password': 'faculty123'})
        response = self.app.post('/api/attendance/start',
            json={'subject_name': 'AI', 'department': 'CS', 'semester': '5', 'section': 'A'})
        self.assertEqual(response.status_code, 200)
        self.app.post('/login', data={'username': 'admin', 'password': 'admin123'})
        response = self.app.post('/api/generate-embeddings')
        self.assertEqual(response.status_code, 200)
        response = self.app.get('/api/attendance/summary?days=7')
        self.assertEqual(response.status_code, 200)
        response = self.app.get('/api/dashboard/stats')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
