import sys
import os
import io
import csv
import unittest
from unittest.mock import MagicMock

# Mock heavy ML dependencies BEFORE importing the app
sys.modules['cv2'] = MagicMock()
sys.modules['deepface'] = MagicMock()
sys.modules['deepface.DeepFace'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['mediapipe.solutions'] = MagicMock()
sys.modules['mediapipe.solutions.face_detection'] = MagicMock()
sys.modules['mediapipe.solutions.face_mesh'] = MagicMock()
sys.modules['mediapipe.solutions.drawing_utils'] = MagicMock()
sys.modules['fpdf'] = MagicMock()
sys.modules['fpdf.FPDF'] = MagicMock()
sys.modules['openpyxl'] = MagicMock()
sys.modules['pandas'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['scipy'] = MagicMock()
sys.modules['scipy.spatial'] = MagicMock()
sys.modules['scipy.spatial.distance'] = MagicMock()
sys.modules['firebase_admin'] = MagicMock()
sys.modules['firebase_admin.credentials'] = MagicMock()
sys.modules['firebase_admin.auth'] = MagicMock()
sys.modules['firebase_admin.db'] = MagicMock()
sys.modules['firebase_admin.storage'] = MagicMock()
sys.modules['firebase_admin.messaging'] = MagicMock()
sys.modules['twilio'] = MagicMock()
sys.modules['twilio.rest'] = MagicMock()
sys.modules['apscheduler'] = MagicMock()
sys.modules['apscheduler.schedulers'] = MagicMock()
sys.modules['apscheduler.schedulers.background'] = MagicMock()
sys.modules['eventlet'] = MagicMock()
sys.modules['flask_socketio'] = MagicMock()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, User
from database.models import Student, Faculty, Subject, Timetable, Attendance
from werkzeug.security import generate_password_hash
from datetime import date


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-key'
    WTF_CSRF_ENABLED = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class AdminEndpointsTestCase(unittest.TestCase):
    def setUp(self):
        app.config.from_object(TestConfig)
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            admin = User(username='admin', password=generate_password_hash('admin123'), role='admin', email='admin@test.com')
            db.session.add(admin)
            db.session.commit()
        self.app.post('/login', data={'username': 'admin', 'password': 'admin123'})

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # ──────────── Helpers ────────────
    def _add_faculty(self, fid='FAC001', name='Dr. Test', email='f@test.com', dept='CS'):
        with app.app_context():
            f = Faculty(faculty_id=fid, name=name, email=email, department=dept)
            db.session.add(f)
            if not User.query.filter_by(username=fid).first():
                user = User(username=fid, password=generate_password_hash(fid + '@123'), role='faculty', email=email)
                db.session.add(user)
            db.session.commit()

    def _add_subject(self, sid='SUB001', name='AI', dept='CS', sem='5'):
        with app.app_context():
            sub = Subject(subject_id=sid, subject_name=name, department=dept, semester=sem)
            db.session.add(sub)
            db.session.commit()

    def _add_timetable(self, fac_id='FAC001', subj='AI', dept='CS', sem='5', sec='A', day='Monday', start='09:00', end='10:00', room='101'):
        with app.app_context():
            tt = Timetable(faculty_id=fac_id, subject_name=subj, department=dept, semester=sem, section=sec, day=day, start_time=start, end_time=end, room_number=room)
            db.session.add(tt)
            db.session.commit()

    # ──────────── Faculty Edit ────────────
    def test_faculty_edit_updates_fields(self):
        self._add_faculty()
        response = self.app.post('/admin/faculty/edit/FAC001', data={
            'name': 'Dr. Updated', 'email': 'updated@test.com',
            'phone': '1234567890', 'department': 'Math'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            f = Faculty.query.get('FAC001')
            self.assertEqual(f.name, 'Dr. Updated')
            self.assertEqual(f.email, 'updated@test.com')
            self.assertEqual(f.department, 'Math')

    def test_faculty_edit_404(self):
        response = self.app.post('/admin/faculty/edit/NONEXISTENT', data={'name': 'X'})
        self.assertEqual(response.status_code, 404)

    # ──────────── Subject CRUD ────────────
    def test_subject_add(self):
        response = self.app.post('/admin/subjects/add', data={
            'subject_id': 'SUB001', 'subject_name': 'AI',
            'department': 'CS', 'semester': '5'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            self.assertEqual(Subject.query.count(), 1)
            self.assertEqual(Subject.query.get('SUB001').subject_name, 'AI')

    def test_subject_edit(self):
        self._add_subject()
        response = self.app.post('/admin/subjects/edit/SUB001', data={
            'subject_name': 'Machine Learning', 'department': 'Math', 'semester': '6'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            sub = Subject.query.get('SUB001')
            self.assertEqual(sub.subject_name, 'Machine Learning')
            self.assertEqual(sub.department, 'Math')

    def test_subject_edit_404(self):
        response = self.app.post('/admin/subjects/edit/NONEXISTENT', data={'subject_name': 'X'})
        self.assertEqual(response.status_code, 404)

    def test_subject_delete(self):
        self._add_subject()
        response = self.app.post('/admin/subjects/delete/SUB001', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            self.assertEqual(Subject.query.count(), 0)

    def test_subject_delete_404(self):
        response = self.app.post('/admin/subjects/delete/NONEXISTENT')
        self.assertEqual(response.status_code, 404)

    # ──────────── Timetable Edit ────────────
    def test_timetable_edit(self):
        self._add_faculty()
        self._add_timetable()
        with app.app_context():
            tt_id = Timetable.query.first().timetable_id
        response = self.app.post(f'/admin/timetable/edit/{tt_id}', data={
            'faculty_id': 'FAC001', 'subject_name': 'ML', 'department': 'CS',
            'semester': '6', 'section': 'B', 'day': 'Tuesday',
            'start_time': '10:00', 'end_time': '11:00', 'room_number': '202'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            tt = Timetable.query.get(tt_id)
            self.assertEqual(tt.subject_name, 'ML')
            self.assertEqual(tt.day, 'Tuesday')
            self.assertEqual(tt.room_number, '202')

    def test_timetable_edit_404(self):
        response = self.app.post('/admin/timetable/edit/99999', data={'day': 'Friday'})
        self.assertEqual(response.status_code, 404)

    def test_timetable_delete(self):
        self._add_faculty()
        self._add_timetable()
        with app.app_context():
            tt_id = Timetable.query.first().timetable_id
        response = self.app.post(f'/admin/timetable/delete/{tt_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            self.assertEqual(Timetable.query.count(), 0)

    # ──────────── Bulk Student Import ────────────
    def test_bulk_import_valid_csv(self):
        csv_content = b'student_id,usn,name,department,semester,section,email,phone\nSTU100,USN100,Bulk Student,CS,5,A,bulk@test.com,1234567890\nSTU101,USN101,Bulk Student 2,CS,5,B,bulk2@test.com,0987654321\n'
        data = {'csv_file': (io.BytesIO(csv_content), 'students.csv')}
        response = self.app.post('/admin/students/bulk-add', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            self.assertEqual(Student.query.count(), 2)
            self.assertEqual(User.query.filter_by(role='student').count(), 2)

    def test_bulk_import_skips_duplicates(self):
        with app.app_context():
            s = Student(student_id='STU001', usn='USN001', name='Existing', department='CS', semester='5', section='A')
            db.session.add(s)
            u = User(username='STU001', password=generate_password_hash('x@123'), role='student', email='e@t.com')
            db.session.add(u)
            db.session.commit()
        csv_content = b'student_id,usn,name,department,semester,section,email,phone\nSTU001,USN001,Duplicate,CS,5,A,dup@test.com,123\nSTU100,USN100,New Student,CS,5,B,new@test.com,456\n'
        data = {'csv_file': (io.BytesIO(csv_content), 'students.csv')}
        response = self.app.post('/admin/students/bulk-add', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            self.assertEqual(Student.query.count(), 2)

    def test_bulk_import_no_file(self):
        response = self.app.post('/admin/students/bulk-add', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_bulk_import_non_csv(self):
        data = {'csv_file': (io.BytesIO(b'not csv'), 'file.txt')}
        response = self.app.post('/admin/students/bulk-add', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            self.assertEqual(Student.query.count(), 0)

    def test_bulk_import_creates_user_accounts(self):
        csv_content = b'student_id,usn,name,department,semester,section,email,phone\nSTU200,USN200,User Test,CS,5,A,user@test.com,123\n'
        data = {'csv_file': (io.BytesIO(csv_content), 'students.csv')}
        response = self.app.post('/admin/students/bulk-add', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            user = User.query.filter_by(username='STU200').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.role, 'student')

    # ──────────── Access Control ────────────
    def test_unauthenticated_redirected(self):
        self.app.get('/logout')
        response = self.app.get('/admin/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_non_admin_redirected(self):
        self.app.get('/logout')
        with app.app_context():
            u = User(username='student', password=generate_password_hash('student123'), role='student', email='s@test.com')
            db.session.add(u)
            db.session.commit()
        self.app.post('/login', data={'username': 'student', 'password': 'student123'})
        response = self.app.get('/admin/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
