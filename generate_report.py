"""Generate project report PDF"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from fpdf import FPDF

class Report(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 8)
            self.cell(0, 8, 'Smart Attendance System - Project Report', align='L')
            self.cell(0, 8, f'Page {self.page_no()}', align='R', new_x='LMARGIN', new_y='NEXT')
            self.line(10, 14, 200, 14)
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(25, 55, 109)
        self.cell(0, 12, title, new_x='LMARGIN', new_y='NEXT')
        self.set_draw_color(25, 55, 109)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(60, 60, 60)
        self.cell(0, 10, title, new_x='LMARGIN', new_y='NEXT')
        self.ln(2)

    def body_text(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.5, text)
        self.ln(3)

    def bullet(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(30, 30, 30)
        self.cell(5, 5.5, '-')
        self.multi_cell(0, 5.5, text, new_x='LMARGIN', new_y='NEXT')

    def entity(self, name, fields):
        self.set_font('Courier', 'B', 9)
        self.set_text_color(25, 55, 109)
        self.cell(80, 5, f'[{name}]')
        self.ln(4)
        self.set_font('Courier', '', 8.5)
        self.set_text_color(40, 40, 40)
        for f in fields:
            pk = 'PK' if f.startswith('*') else ''
            display = f.lstrip('*')
            self.cell(80, 4.5, f'  {display:25s} {pk}')
            self.ln(4)
        self.ln(3)


pdf = Report()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)

# ── Title Page ──
pdf.add_page()
pdf.ln(50)
pdf.set_font('Helvetica', 'B', 28)
pdf.set_text_color(25, 55, 109)
pdf.cell(0, 15, 'Smart Attendance System', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.ln(5)
pdf.set_font('Helvetica', '', 16)
pdf.set_text_color(80, 80, 80)
pdf.cell(0, 10, 'Project Report', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.ln(10)
pdf.set_font('Helvetica', '', 12)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 8, 'An AI-Powered Web Application for Educational Institution', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.cell(0, 8, 'Attendance Management', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.ln(30)
pdf.set_text_color(60, 60, 60)
pdf.cell(0, 7, 'Technology Stack: Python, Flask, PostgreSQL, Bootstrap 5', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.cell(0, 7, 'Deployment: Render + Neon PostgreSQL', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.cell(0, 7, 'Year: 2026', align='C', new_x='LMARGIN', new_y='NEXT')

# ── Table of Contents ──
pdf.add_page()
pdf.chapter_title('Table of Contents')
pdf.set_font('Helvetica', '', 12)
toc = [
    '1. Project Overview',
    '2. Technology Stack',
    '3. System Architecture & ER Diagram',
    '4. Codebase Structure',
    '5. Module Workflows',
    '   5.1 Admin Module',
    '   5.2 Faculty Module',
    '   5.3 Student Module',
    '6. Key Features',
    '7. Deployment & Hosting',
]
for item in toc:
    indent = 10 if item.startswith('   ') else 0
    pdf.set_x(15 + indent)
    pdf.cell(0, 8, item.strip(), new_x='LMARGIN', new_y='NEXT')

# ── 1. Project Overview ──
pdf.add_page()
pdf.chapter_title('1. Project Overview')
pdf.body_text(
    'The Smart Attendance System is a web-based application designed to digitize and automate '
    'the attendance management process in educational institutions. The system replaces traditional '
    'paper-based attendance registers with a digital platform that allows faculty to mark attendance, '
    'generate timetables, record test results, and provides administrators with complete control over '
    'departments, subjects, faculty assignments, and student data.'
)
pdf.body_text(
    'The system follows a three-role architecture: Administrator, Faculty, and Student. Each role has '
    'a dedicated portal with role-specific functionality. Administrators manage the entire system '
    'hierarchy including departments, semesters, sections, subjects, faculty assignments, and timetable '
    'generation. Faculty members mark student attendance, manage test results, view their schedules, '
    'and handle leave requests. Students can view their attendance records, download reports, and '
    'check their weekly timetable.'
)
pdf.body_text(
    'Key capabilities include automatic timetable generation with clash detection across multiple '
    'sections, semester-wise faculty assignment, department and section management, self-service student '
    'promotion with backlog tracking, and comprehensive analytics dashboards.'
)

# ── 2. Technology Stack ──
pdf.add_page()
pdf.chapter_title('2. Technology Stack')

pdf.section_title('Backend')
pdf.bullet('Language: Python 3.13')
pdf.bullet('Web Framework: Flask 3.x (lightweight, modular, WSGI-compliant)')
pdf.bullet('ORM: SQLAlchemy 2.x with Flask-SQLAlchemy')
pdf.bullet('Authentication: Flask-Login with role-based access control')
pdf.bullet('Form Protection: Flask-WTF with CSRF protection')
pdf.bullet('API Framework: RESTful JSON endpoints for AJAX interactions')

pdf.section_title('Frontend')
pdf.bullet('HTML Templating: Jinja2 (server-side rendering with inheritance)')
pdf.bullet('CSS Framework: Bootstrap 5.3 with dark/light theme support')
pdf.bullet('Icons: Font Awesome 6')
pdf.bullet('Charts: Chart.js (bar charts, attendance trends)')
pdf.bullet('AJAX: Native Fetch API for dynamic data loading')

pdf.section_title('Database')
pdf.bullet('Development: SQLite 3')
pdf.bullet('Production: PostgreSQL 16 (via Neon cloud)')
pdf.bullet('ORM Migrations: SQLAlchemy create_all() with auto-migration scripts')

pdf.section_title('Deployment & Infrastructure')
pdf.bullet('Hosting: Render.com (Free Tier Web Service)')
pdf.bullet('Database Hosting: Neon (Free Tier PostgreSQL)')
pdf.bullet('WSGI Server: Gunicorn (multi-worker)')
pdf.bullet('Uptime Monitoring: cron-job.org (10-min ping)')

pdf.section_title('Additional Services')
pdf.bullet('Email Notifications: Flask-Mail with SMTP')
pdf.bullet('SMS Notifications: Twilio API')
pdf.bullet('Push Notifications: Firebase Cloud Messaging')
pdf.bullet('Report Generation: fpdf2 (PDF), openpyxl (Excel)')
pdf.bullet('Data Analysis: Pandas, NumPy')

# ── 3. ER Diagram ──
pdf.add_page()
pdf.chapter_title('3. Entity Relationship Diagram')
pdf.body_text(
    'The database consists of 12 tables. Below is the entity relationship diagram showing all '
    'tables, their attributes, primary keys, and foreign key relationships.'
)

pdf.section_title('Entities and Attributes')

tables = [
    ('users', ['*id (PK)', 'username (UNIQUE)', 'password', 'role (admin/faculty/student)', 'email', 'is_verified', 'last_login', 'created_at']),
    ('students', ['*student_id (PK)', 'usn (UNIQUE)', 'name', 'department', 'semester', 'section', 'email', 'phone', 'parent_phone', 'parent_email', 'is_active', 'backlog_subjects', 'created_at']),
    ('faculty', ['*faculty_id (PK)', 'name', 'email (UNIQUE)', 'phone', 'department', 'semesters_handled', 'is_active', 'created_at']),
    ('departments', ['*id (PK)', 'name (UNIQUE)', 'code (UNIQUE)', 'created_at']),
    ('department_sections', ['*id (PK)', 'department_name', 'semester', 'section', 'created_at']),
    ('subjects', ['*subject_id (PK)', 'subject_name', 'department', 'semester', 'section', 'is_lab', 'hours_per_week', 'credits', 'created_at']),
    ('attendance', ['*attendance_id (PK)', 'student_id (FK)', 'faculty_id (FK)', 'subject_name', 'date', 'time', 'status', 'is_late', 'snapshot_path', 'created_at']),
    ('timetable', ['*timetable_id (PK)', 'faculty_id (FK)', 'subject_name', 'department', 'semester', 'section', 'day', 'start_time', 'end_time', 'room_number']),
    ('test_results', ['*result_id (PK)', 'student_id (FK)', 'faculty_id (FK)', 'subject_name', 'department', 'semester', 'section', 'test_type', 'marks', 'total_marks', 'grade', 'remarks', 'created_at']),
    ('leave_requests', ['*leave_id (PK)', 'faculty_id (FK)', 'faculty_name', 'department', 'leave_type', 'from_date', 'to_date', 'reason', 'status', 'admin_remarks', 'created_at']),
    ('alerts', ['*alert_id (PK)', 'faculty_id (FK)', 'alert_type', 'message', 'is_read', 'created_at']),
    ('notifications', ['*notification_id (PK)', 'recipient_type', 'recipient_id', 'title', 'message', 'is_read', 'created_at']),
    ('attendance_sessions', ['*session_id (PK)', 'faculty_id (FK)', 'subject_name', 'department', 'semester', 'section', 'status', 'started_at', 'ended_at', 'total_students']),
]

for name, fields in tables:
    pdf.entity(name, fields)

pdf.add_page()
pdf.section_title('Relationships')
pdf.set_font('Helvetica', '', 10)
rels = [
    'students.student_id ---< attendance.student_id (One student has many attendance records)',
    'faculty.faculty_id ---< attendance.faculty_id (One faculty marks many attendances)',
    'faculty.faculty_id ---< timetable.faculty_id (One faculty has many timetable slots)',
    'faculty.faculty_id ---< leave_requests.faculty_id (One faculty has many leave requests)',
    'faculty.faculty_id ---< test_results.faculty_id (One faculty publishes many results)',
    'students.student_id ---< test_results.student_id (One student has many test results)',
    'faculty.faculty_id ---< alerts.faculty_id (One faculty receives many alerts)',
    'faculty.faculty_id ---< attendance_sessions.faculty_id (One faculty creates many sessions)',
    'departments.name = students.department (Department name links to students)',
    'departments.name = subjects.department (Department name links to subjects)',
    'departments.name = faculty.department (Department name links to faculty)',
    'departments.name + semester = department_sections (Composite context for sections)',
]
for r in rels:
    pdf.bullet(r)
    pdf.ln(2)

pdf.ln(5)
pdf.body_text(
    'Key Design Notes:\n'
    '- Departments are identified by name, not ID, for readability across all related tables.\n'
    '- Sections are managed separately through department_sections table, not embedded in subjects.\n'
    '- Subjects are created per-semester and apply to all sections within that semester.\n'
    '- Faculty have a semesters_handled (comma-separated) field for flexible semester assignment.\n'
    '- Timetable generation uses a global clash detector that prevents the same faculty from being '
    'assigned to two sections at the same time slot.\n'
    '- The backlog_subjects field on students tracks subjects failed for retake in the next cycle.'
)

# ── 4. Codebase Structure ──
pdf.add_page()
pdf.chapter_title('4. Codebase Structure')
pdf.body_text('The project follows a modular Flask blueprint architecture:')

structure = """
smart_attendance/
+-- app.py                    # Application factory, config, seed_admin()
+-- requirements.txt          # Python dependencies
+-- .env                      # Environment variables (not committed)
+-- database/
|   +-- models.py            # All 13 SQLAlchemy ORM models
+-- routes/
|   +-- __init__.py           # Blueprint registration
|   +-- auth_routes.py        # Login/logout, authentication
|   +-- admin_routes.py       # Admin panel (departments, sections, subjects,
|   |                           faculty, timetable gen, promote, clear-all)
|   +-- faculty_routes.py     # Faculty dashboard, attendance, results, leaves
|   +-- student_routes.py     # Student portal, attendance, results, timetable
|   +-- api_routes.py         # REST API endpoints for external consumption
+-- templates/
|   +-- base.html             # Master layout with sidebar, theme toggle
|   +-- login.html            # Login page
|   +-- landing.html          # Public landing page
|   +-- admin_*.html          # 12 admin templates
|   +-- faculty_*.html        # 8 faculty templates  
|   +-- student_*.html        # 5 student templates
|   +-- analytics.html        # Shared analytics view
+-- static/
|   +-- css/style.css         # Custom CSS with glassmorphism design
|   +-- js/analytics.js       # Analytics chart rendering
|   +-- uploads/              # Profile image uploads
|   +-- snapshots/            # Attendance snapshots
+-- utils/
|   +-- notifications.py      # Email, SMS, Firebase notification service
|   +-- report_generator.py   # PDF/Excel report generation
+-- firebase/
|   +-- config.py             # Firebase initialization
|   +-- setup.py              # Firebase setup utilities
|   +-- serviceAccountKey.json (not committed)
+-- training/                 # ML training scripts (deprecated)
+-- reports/                  # Generated report output directory
+-- models/                   # ML model storage
+-- dataset/                  # Training dataset storage
"""

pdf.set_font('Courier', '', 7.5)
pdf.set_text_color(30, 30, 30)
pdf.multi_cell(0, 3.5, structure)
pdf.ln(5)

# ── 5. Module Workflows ──
pdf.add_page()
pdf.chapter_title('5. Module Workflows')

pdf.section_title('5.1 Admin Module')
pdf.body_text(
    'The Admin module is the central management hub. The workflow is as follows:'
)
pdf.set_font('Helvetica', '', 10)
steps = [
    '1. Department Management: Admin creates departments (e.g., Computer Science, Engineering) '
    'with unique codes. Each department serves as the top-level organizational unit.',
    '2. Section Definition: Within each department, admin defines sections (A, B) for every '
    'semester. These sections are used for timetable generation and student grouping.',
    '3. Subject Creation: Admin adds subjects per semester per department. Subjects are marked '
    'as theory or lab with configurable hours per week and credits.',
    '4. Faculty Management: Admin adds faculty members, assigns them to a department, and '
    'specifies which semesters they handle (e.g., "1,3,5,7" for odd semesters). Each faculty '
    'member gets an auto-generated user account.',
    '5. Timetable Generation: Admin selects a semester and clicks Generate. The system:',
    '   a. Fetches all subjects for the semester',
    '   b. Fetches faculty assigned to that semester',
    '   c. For each section, builds a unique weekly schedule',
    '   d. Distributes subjects across 1-hour slots (08:00-14:30) with breaks',
    '   e. Uses a global clash detector to prevent faculty double-booking',
    '6. Student Management: Admin can add, edit, delete students, view attendance, and search/'
    'filter by department, semester, and section.',
    '7. Student Promotion: At end of semester, admin selects students for promotion. Passed '
    'students move to next semester. Failed students also move forward but carry backlog subjects '
    'for retake in the next corresponding academic cycle.',
    '8. Leave Management: Admin reviews and approves/rejects faculty leave requests.',
    '9. Analytics Dashboard: View attendance trends, top students by attendance percentage, '
    'recent sessions, and alerts.',
    '10. Data Reset: A danger-zone option clears all data while preserving the admin account.',
]
for s in steps:
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(30, 30, 30)
    x = pdf.get_x()
    pdf.multi_cell(0, 5.5, s)
    pdf.ln(2)

pdf.add_page()
pdf.section_title('5.2 Faculty Module')
pdf.body_text('The Faculty module handles daily classroom operations:')

steps2 = [
    '1. Dashboard: Faculty sees today\'s class schedule, a quick attendance summary (total, present, '
    'absent, late for current day), and recent attendance sessions.',
    '2. Mark Attendance: Faculty selects semester, section, and subject from dropdowns, then clicks '
    '"Load Students". The system displays all enrolled students with radio buttons for Present/Absent/'
    'Late. Faculty submits the batch and attendance is recorded.',
    '3. Attendance History: Faculty can view past attendance records, filter by subject, date range, '
    'or student. Records show status, date, and time of marking.',
    '4. Timetable View: Faculty sees their personal weekly timetable showing all assigned classes '
    'across sections, with subject names, times, rooms, and sections.',
    '5. Test Results: Faculty can:',
    '   a. View all published test results from all faculty members (with "Published By" column)',
    '   b. Add new test results by selecting semester, section, subject, test type, and entering '
    'marks per student. Grade is auto-calculated (A: 90%+, B: 75%+, C: 60%+, D: 50%+, F: below)',
    '   c. Edit existing test results to update marks/total and auto-recalculate grade.',
    '6. Student Management: Faculty can add new students to their department via a modal form, '
    'which auto-creates the student record and user account with a default password.',
    '7. Leave Requests: Faculty can submit leave requests with type, dates, reason, and optional '
    'attachments. Admin approval status is displayed.',
]
for s in steps2:
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 5.5, s)
    pdf.ln(2)

pdf.section_title('5.3 Student Module')
pdf.body_text('The Student module provides self-service access:')

steps3 = [
    '1. My Portal: The student dashboard displays personal information (name, USN, department, '
    'semester, section) and attendance statistics as percentage cards (attendance %, present count, '
    'late count, absent count). A chart shows attendance trends over recent days.',
    '2. Attendance History: Students can view their complete attendance record with subject, date, '
    'time, and status columns. A "View All" link shows the full history.',
    '3. Test Results: Students can see all their test results including subject name, test type, '
    'marks obtained, total marks, grade, and a grade badge (color-coded).',
    '4. Weekly Timetable: Students can view their own weekly timetable filtered automatically by '
    'their department, semester, and section. The timetable shows all 1-hour slots from 08:00 to '
    '14:30 with subject names and faculty names.',
    '5. Download Reports: Students can download their attendance report in PDF, Excel, or CSV formats.',
    '6. Profile Management: Students can edit their profile information (name, email, phone, parent '
    'contact details).',
]
for s in steps3:
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 5.5, s)
    pdf.ln(2)

# ── 6. Key Features ──
pdf.add_page()
pdf.chapter_title('6. Key Features')
features = [
    'Three-Role Architecture: Separate portals for Admin, Faculty, and Students with role-based access control.',
    'Department Management: Create and manage departments with unique codes, nested subject and section management.',
    'Auto Timetable Generator: Generates clash-free weekly timetables for all sections simultaneously. Supports '
    '1-hour teaching slots with breaks, assigns faculty per semester, and distributes subjects intelligently.',
    'Manual Attendance Marking: Faculty selects semester/section/subject and marks attendance via radio buttons '
    '(Present/Absent/Late) in a batch operation. No camera or facial recognition needed.',
    'Test Results Management: Faculty can publish, view all, and edit test results. Auto-calculated grades. '
    'All faculty can see results published by any faculty member.',
    'Student Promotion: Admin promotes students to the next semester. Failed students carry backlog subjects '
    'for retake in the next academic cycle.',
    'Faculty Semester Assignment: Faculty are assigned to specific semesters (e.g., odd/even). Timetable '
    'generator filters faculty by semester assignment.',
    'Leave Management: Faculty submit leave requests; admin approves or rejects them.',
    'Notifications: Multi-channel notification delivery via email (SMTP), SMS (Twilio), and push (Firebase).',
    'Report Generation: Downloadable PDF, Excel, and CSV attendance reports with comprehensive formatting.',
    'Analytics Dashboard: Admin sees weekly attendance trends, student rankings, and session history.',
    'Dark/Light Theme: Toggleable theme with persistent preference using CSS custom properties and Bootstrap data attributes.',
    'Responsive Design: Mobile-friendly layout using Bootstrap 5 grid system.',
    'CSRF Protection: All POST forms and AJAX requests include CSRF tokens via Flask-WTF.',
    'Backlog Tracking: Students with failed subjects carry forward backlog information visible in the promotion page.',
]
for f in features:
    pdf.bullet(f)
    pdf.ln(2)

# ── 7. Deployment ──
pdf.add_page()
pdf.chapter_title('7. Deployment & Hosting')
pdf.body_text(
    'The application is deployed on Render.com (Free Tier) with Neon PostgreSQL as the production '
    'database. The deployment process is as follows:'
)
deploy = [
    'Source Code: Hosted on GitHub for version control and continuous deployment.',
    'Build: Render automatically detects the Python environment, installs dependencies from '
    'requirements.txt, and starts the application using Gunicorn WSGI server.',
    'Database: Neon provides a fully managed PostgreSQL 16 database on the free tier. The connection '
    'string is passed to the application via the DATABASE_URL environment variable.',
    'Uptime: Render\'s free web service sleeps after 15 minutes of inactivity. A cron-job.org service '
    'pings the /health endpoint every 10 minutes to keep the application warm.',
    'Environment Variables: SECRET_KEY (session encryption), DATABASE_URL (Neon connection string), '
    'SMTP credentials (email notifications), Twilio credentials (SMS), Firebase config (push notifications).',
    'Scaling: The application uses Gunicorn with 4 workers for concurrent request handling. PostgreSQL '
    'handles connection pooling automatically.',
]
for d in deploy:
    pdf.bullet(d)
    pdf.ln(2)

# Save
output_path = os.path.join(os.path.dirname(__file__), 'reports', 'Smart_Attendance_Project_Report.pdf')
os.makedirs(os.path.dirname(output_path), exist_ok=True)
pdf.output(output_path)
print(f'Report generated: {output_path}')
