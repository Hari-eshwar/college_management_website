# AI-Powered Smart Attendance System

A production-ready BCA final year project that uses AI and Deep Learning to automate attendance and provide comprehensive analytics.

## Features

### Core AI Features
- **Face Recognition**: Automated attendance using FaceNet/DeepFace with high accuracy
- **Anti-Spoof Detection**: Liveness verification through blink detection and head movement analysis

### Management Features
- **Admin Panel**: Complete CRUD for students, faculty, subjects, timetable
- **Faculty Dashboard**: Live attendance sessions, timetable view, leave management
- **Student Portal**: Attendance history, personal analytics
- **Leave Workflow**: Request/approve/reject with status tracking
- **Timetable Management**: Weekly schedule with classroom assignments
- **Real-time Monitoring**: Live camera feed with face detection overlay

### Communication
- **Parent Notifications**: Email alerts for absences (SMTP)
- **Firebase Integration**: Optional cloud sync, push notifications, authentication
- **Socket.IO**: Real-time updates for live attendance sessions

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask, Flask-SocketIO |
| AI/ML | OpenCV, TensorFlow, Keras, MediaPipe, DeepFace, FaceNet |
| Database | SQLAlchemy (SQLite/MySQL/PostgreSQL) |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js |
| Real-time | Socket.IO, WebSockets |
| Cloud | Firebase (optional), SMTP Email, Twilio SMS (optional) |
| Deployment | Docker, Gunicorn + Eventlet |

## Project Structure

```
smart_attendance/
├── app.py                    # Main Flask application with blueprint registration
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker container configuration
├── docker-compose.yml        # Multi-service orchestration
├── .env.example              # Environment variable template
│
├── database/
│   └── models.py             # SQLAlchemy models (User, Student, Faculty, Attendance, etc.)
│
├── routes/
│   ├── auth_routes.py        # Login, logout, register
│   ├── admin_routes.py       # Admin: students, faculty, timetable, leaves, subjects
│   ├── faculty_routes.py     # Faculty: dashboard, attendance, timetable, leaves
│   ├── student_routes.py     # Student: portal, attendance history, analytics
│   └── api_routes.py         # REST API endpoints
│
├── utils/
│   ├── report_generator.py   # PDF/Excel/CSV report generation
│   └── notifications.py     # Email notification service
│
├── firebase/
│   ├── __init__.py
│   └── config.py             # Firebase auth, database, storage, messaging
│
│
├── templates/                # Jinja2 HTML templates (10+ pages)
│   ├── base.html             # Layout with sidebar, dark mode, glassmorphism
│   ├── landing.html          # Landing page
│   ├── login.html            # Login page
│   ├── admin_dashboard.html  # Admin control panel
│   ├── admin_students.html   # Student CRUD
│   ├── admin_faculty.html    # Faculty management
│   ├── admin_timetable.html  # Timetable management
│   ├── admin_leaves.html     # Leave approval
│   ├── admin_subjects.html   # Subject management
│   ├── faculty_dashboard.html# Faculty home
│   ├── faculty_attendance.html# Live attendance with camera
│   ├── faculty_timetable.html# Weekly timetable view
│   ├── faculty_leaves.html   # Leave request form
│   ├── student_portal.html   # Student dashboard
│   ├── student_attendance_list.html
│   └── analytics.html        # Analytics & reports
│
├── static/
│   ├── css/style.css         # Complete glassmorphism UI with dark mode
│   └── js/
│       ├── main.js           # Theme, sidebar, notifications, toasts
│       └── analytics.js      # Charts and analytics
│
├── tests/
│   ├── __init__.py
│   └── test_app.py           # Unit tests (models, auth, API endpoints)
│
├── dataset/                  # Student face images (created at runtime)
├── models/                   # Trained AI models (created at runtime)
├── reports/                  # Generated reports (created at runtime)
└── static/
    ├── snapshots/            # Captured snapshots
    └── uploads/              # File uploads
```

## Installation

### Prerequisites
- Python 3.10+
- Webcam (for live attendance)
- pip (Python package manager)

### Quick Start

```bash
# 1. Clone and enter directory
git clone <repo-url>
cd smart_attendance

# 2. Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

### Docker Deployment

```bash
docker-compose up --build
```

### Environment Variables
Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your configuration
```

## Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Faculty | faculty | faculty123 |
| Student | student | student123 |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/login` | POST | User authentication |
| `/api/register` | POST | User registration |
| `/api/attendance/start` | POST | Start attendance session |
| `/api/attendance/mark` | POST | Mark individual attendance |

| `/api/report/generate` | POST | Generate PDF/Excel/CSV report |
| `/api/report/comprehensive` | POST | Generate AI comprehensive report |
| `/api/faculty/leave/request` | POST | Submit leave request |
| `/api/admin/leave/approve` | POST | Approve leave request |
| `/api/admin/leave/reject` | POST | Reject leave request |
| `/api/attendance/summary` | GET | Attendance summary statistics |
| `/api/dashboard/stats` | GET | Dashboard statistics |
| `/api/generate-embeddings` | POST | Generate face embeddings from dataset |

## Testing

```bash
python -m pytest tests/ -v
```

## Security Features

- Role-based access control (Admin, Faculty, Student)
- Password hashing with Werkzeug
- SQL injection prevention via SQLAlchemy ORM
- Session management with Flask-Login

- File upload validation
- CSRF-ready architecture

## Deployment

### Production Checklist
1. Set a strong `SECRET_KEY` in environment variables
2. Use MySQL/PostgreSQL instead of SQLite
3. Configure SMTP for email notifications
4. Enable HTTPS (reverse proxy with Nginx)
5. Set up Firebase service account (optional)
6. Run behind Gunicorn with eventlet workers
7. Use Docker for containerized deployment

### Platforms
- **Backend**: Render, Railway, AWS EC2, DigitalOcean
- **Frontend**: Included in Flask templates (no separate deployment needed)
- **Database**: SQLite (dev), MySQL/PostgreSQL (prod)
- **Container**: Docker + Docker Compose

## License

MIT License - For educational purposes
