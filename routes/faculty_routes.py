from flask import render_template, request, redirect, url_for, jsonify, flash, Response, session, send_file
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from database.models import db, Faculty, Timetable, Attendance, AttendanceSession, LeaveRequest, Alert, Notification, Student, User, TestResult
from . import faculty_bp
from datetime import datetime, date, timezone
from utils.report_generator import ReportGenerator
from utils.notifications import NotificationService
import logging
import os
import uuid
logger = logging.getLogger(__name__)

notification_service = NotificationService()

def faculty_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'faculty':
            flash('Access denied', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def get_faculty():
    return Faculty.query.filter_by(email=current_user.email).first()

@faculty_bp.route('/dashboard')
@login_required
@faculty_required
def dashboard():
    faculty = get_faculty()
    if not faculty:
        flash('Faculty profile not found', 'danger')
        return redirect(url_for('auth.login'))
    today_name = datetime.now().strftime('%A')
    today_classes = Timetable.query.filter_by(faculty_id=faculty.faculty_id, day=today_name).all()
    today_attendance = Attendance.query.filter_by(faculty_id=faculty.faculty_id, date=date.today()).all()
    leaves = LeaveRequest.query.filter_by(faculty_id=faculty.faculty_id).order_by(LeaveRequest.created_at.desc()).limit(10).all()
    active_session = AttendanceSession.query.filter_by(faculty_id=faculty.faculty_id, status='active').first()
    alerts = Alert.query.filter_by(faculty_id=faculty.faculty_id, is_read=False).order_by(Alert.created_at.desc()).all()
    stats = {
        'total_classes': len(today_classes),
        'today_attendance': len(today_attendance),
        'present_count': sum(1 for a in today_attendance if a.status == 'Present'),
        'pending_leaves': LeaveRequest.query.filter_by(faculty_id=faculty.faculty_id, status='Pending').count(),
    }
    return render_template('faculty_dashboard.html', faculty=faculty, classes=today_classes,
                          today_attendance=today_attendance, leaves=leaves,
                          active_session=active_session, alerts=alerts, stats=stats)

@faculty_bp.route('/attendance')
@login_required
@faculty_required
def attendance():
    faculty = get_faculty()
    today_name = datetime.now().strftime('%A')
    today_classes = Timetable.query.filter_by(faculty_id=faculty.faculty_id, day=today_name).all()
    active_session = AttendanceSession.query.filter_by(faculty_id=faculty.faculty_id, status='active').first()
    return render_template('faculty_attendance.html', faculty=faculty,
                          classes=today_classes, active_session=active_session)

@faculty_bp.route('/attendance/start', methods=['POST'])
@login_required
@faculty_required
def start_attendance():
    faculty = get_faculty()
    data = request.get_json() or request.form
    subject = data.get('subject_name', '')
    department = data.get('department', '')
    semester = data.get('semester', '')
    section = data.get('section', '')
    active = AttendanceSession.query.filter_by(faculty_id=faculty.faculty_id, status='active').first()
    if active:
        return jsonify({'status': 'error', 'message': 'An attendance session is already active'})
    students = Student.query.filter_by(department=department, semester=semester, section=section).all()
    session_rec = AttendanceSession(
        faculty_id=faculty.faculty_id,
        subject_name=subject,
        department=department,
        semester=semester,
        section=section,
        status='active',
        total_students=len(students)
    )
    db.session.add(session_rec)
    db.session.commit()
    return jsonify({'status': 'success', 'session_id': session_rec.session_id, 'total_students': len(students)})

@faculty_bp.route('/attendance/pause', methods=['POST'])
@login_required
@faculty_required
def pause_attendance():
    faculty = get_faculty()
    active = AttendanceSession.query.filter_by(faculty_id=faculty.faculty_id, status='active').first()
    if active:
        active.status = 'paused'
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Attendance session paused'})
    return jsonify({'status': 'error', 'message': 'No active session'}), 400

@faculty_bp.route('/attendance/resume', methods=['POST'])
@login_required
@faculty_required
def resume_attendance():
    faculty = get_faculty()
    paused = AttendanceSession.query.filter_by(faculty_id=faculty.faculty_id, status='paused').first()
    if paused:
        paused.status = 'active'
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Attendance session resumed'})
    return jsonify({'status': 'error', 'message': 'No paused session'}), 400

@faculty_bp.route('/attendance/stop', methods=['POST'])
@login_required
@faculty_required
def stop_attendance():
    faculty = get_faculty()
    active = AttendanceSession.query.filter_by(faculty_id=faculty.faculty_id, status='active').first() or \
             AttendanceSession.query.filter_by(faculty_id=faculty.faculty_id, status='paused').first()
    if active:
        active.status = 'completed'
        active.ended_at = datetime.now(timezone.utc)
        present = Attendance.query.filter_by(
            faculty_id=faculty.faculty_id, date=date.today(),
            subject_name=active.subject_name, status='Present'
        ).count()
        late = Attendance.query.filter_by(
            faculty_id=faculty.faculty_id, date=date.today(),
            subject_name=active.subject_name, status='Late'
        ).count()
        active.present_count = present
        active.late_count = late
        db.session.commit()
    return jsonify({'status': 'success', 'message': 'Attendance session ended'})

@faculty_bp.route('/attendance/students')
@login_required
@faculty_required
def get_students():
    faculty = get_faculty()
    semester = request.args.get('semester')
    section = request.args.get('section')
    subject = request.args.get('subject', '')
    query = Student.query.filter_by(is_active=True)
    if faculty.department:
        query = query.filter_by(department=faculty.department)
    if semester:
        query = query.filter_by(semester=semester)
    if section:
        query = query.filter_by(section=section)
    students = query.order_by(Student.name).all()
    return jsonify({
        'students': [{'student_id': s.student_id, 'usn': s.usn, 'name': s.name} for s in students]
    })

@faculty_bp.route('/attendance/mark', methods=['POST'])
@login_required
@faculty_required
def mark_attendance():
    faculty = get_faculty()
    data = request.get_json()
    if not data or not data.get('students'):
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    subject = data.get('subject_name', '')
    marked = 0
    errors = []
    for entry in data['students']:
        student_id = entry.get('student_id')
        status = entry.get('status', 'Present')
        if not student_id:
            continue
        existing = Attendance.query.filter_by(
            student_id=student_id, faculty_id=faculty.faculty_id,
            date=date.today(), subject_name=subject
        ).first()
        if existing:
            existing.status = status
        else:
            record = Attendance(
                student_id=student_id, faculty_id=faculty.faculty_id,
                subject_name=subject, status=status
            )
            db.session.add(record)
        marked += 1
    db.session.commit()
    return jsonify({'status': 'success', 'marked': marked})

@faculty_bp.route('/attendance/edit/<int:attendance_id>', methods=['POST'])
@login_required
@faculty_required
def edit_attendance(attendance_id):
    faculty = get_faculty()
    record = Attendance.query.get_or_404(attendance_id)
    if record.faculty_id != faculty.faculty_id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    record.status = request.form.get('status', record.status)
    db.session.commit()
    flash('Attendance record updated', 'success')
    return redirect(url_for('faculty.attendance_history'))

@faculty_bp.route('/attendance/verify/<int:attendance_id>', methods=['POST'])
@login_required
@faculty_required
def verify_attendance(attendance_id):
    faculty = get_faculty()
    record = Attendance.query.get_or_404(attendance_id)
    if record.faculty_id != faculty.faculty_id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    record.is_live_verified = True
    if record.status == 'Unknown':
        record.status = request.form.get('status', 'Present')
    db.session.commit()
    flash('Attendance verified', 'success')
    return redirect(url_for('faculty.attendance_history'))

@faculty_bp.route('/attendance/session-status')
@login_required
@faculty_required
def session_status():
    faculty = get_faculty()
    active = AttendanceSession.query.filter_by(
        faculty_id=faculty.faculty_id
    ).filter(
        AttendanceSession.status.in_(['active', 'paused'])
    ).first()
    if not active:
        return jsonify({'active': False})
    today_atd = Attendance.query.filter_by(
        faculty_id=faculty.faculty_id, date=date.today(), subject_name=active.subject_name
    ).all()
    return jsonify({
        'active': True,
        'paused': active.status == 'paused',
        'session_id': active.session_id,
        'subject': active.subject_name,
        'total': active.total_students,
        'present': sum(1 for a in today_atd if a.status == 'Present'),
        'late': sum(1 for a in today_atd if a.status == 'Late'),
        'marked': len(today_atd)
    })

@faculty_bp.route('/timetable')
@login_required
@faculty_required
def timetable():
    faculty = get_faculty()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    week_timetable = {}
    for day in days:
        week_timetable[day] = Timetable.query.filter_by(
            faculty_id=faculty.faculty_id, day=day
        ).order_by(Timetable.start_time).all()
    return render_template('faculty_timetable.html', faculty=faculty, week_timetable=week_timetable, days=days)

@faculty_bp.route('/leaves')
@login_required
@faculty_required
def leaves():
    faculty = get_faculty()
    leaves = LeaveRequest.query.filter_by(faculty_id=faculty.faculty_id).order_by(LeaveRequest.created_at.desc()).all()
    return render_template('faculty_leaves.html', faculty=faculty, leaves=leaves)

@faculty_bp.route('/leave/request', methods=['POST'])
@login_required
@faculty_required
def request_leave():
    faculty = get_faculty()
    data = request.form
    leave = LeaveRequest(
        faculty_id=faculty.faculty_id,
        faculty_name=faculty.name,
        department=faculty.department,
        leave_type=data.get('leave_type', ''),
        from_date=datetime.strptime(data.get('from_date', ''), '%Y-%m-%d').date(),
        to_date=datetime.strptime(data.get('to_date', ''), '%Y-%m-%d').date(),
        reason=data.get('reason', '')
    )
    att = request.files.get('attachment')
    if att and att.filename:
        filename = f'leave_{faculty.faculty_id}_{uuid.uuid4().hex[:8]}_{att.filename}'
        path = os.path.join('static', 'uploads', filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        att.save(path)
        leave.attachment = path
    db.session.add(leave)
    db.session.commit()
    notif = Notification(
        recipient_type='admin',
        recipient_id='admin',
        title='New Leave Request',
        message=f'{faculty.name} requested {leave.leave_type} leave'
    )
    db.session.add(notif)
    db.session.commit()
    flash('Leave request submitted', 'success')
    return redirect(url_for('faculty.leaves'))

@faculty_bp.route('/notifications')
@login_required
@faculty_required
def notifications():
    faculty = get_faculty()
    notifs = Notification.query.filter_by(
        recipient_type='faculty', recipient_id=faculty.faculty_id
    ).order_by(Notification.created_at.desc()).all()
    return jsonify([{
        'id': n.notification_id,
        'title': n.title,
        'message': n.message,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat() if n.created_at else ''
    } for n in notifs])

@faculty_bp.route('/attendance/history')
@login_required
@faculty_required
def attendance_history():
    faculty = get_faculty()
    if not faculty:
        flash('Faculty profile not found', 'danger')
        return redirect(url_for('auth.login'))
    page = request.args.get('page', 1, type=int)
    per_page = 15
    subject_filter = request.args.get('subject', '')
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')
    query = AttendanceSession.query.filter_by(faculty_id=faculty.faculty_id)
    if subject_filter:
        query = query.filter(AttendanceSession.subject_name.ilike(f'%{subject_filter}%'))
    if date_from:
        query = query.filter(AttendanceSession.started_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(AttendanceSession.started_at <= datetime.strptime(date_to, '%Y-%m-%d'))
    total = query.count()
    sessions = query.order_by(AttendanceSession.started_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    subjects = db.session.query(AttendanceSession.subject_name).filter_by(faculty_id=faculty.faculty_id).distinct().all()
    subject_list = [s[0] for s in subjects]
    return render_template('faculty_attendance_history.html', faculty=faculty,
                          sessions=sessions, page=page,
                          total_pages=(total + per_page - 1) // per_page,
                          subject_list=subject_list,
                          subject_filter=subject_filter,
                          date_from=date_from, date_to=date_to)

@faculty_bp.route('/attendance/report')
@login_required
@faculty_required
def attendance_report():
    faculty = get_faculty()
    if not faculty:
        flash('Faculty profile not found', 'danger')
        return redirect(url_for('auth.login'))
    format_type = request.args.get('format', 'pdf')
    subject = request.args.get('subject', '')
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')
    query = Attendance.query.filter_by(faculty_id=faculty.faculty_id)
    if subject:
        query = query.filter_by(subject_name=subject)
    if date_from:
        query = query.filter(Attendance.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(Attendance.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    records = query.order_by(Attendance.date.desc()).all()
    attendance_data = []
    for r in records:
        student = Student.query.get(r.student_id)
        attendance_data.append({
            'student_id': r.student_id,
            'name': student.name if student else r.student_id,
            'subject': r.subject_name,
            'date': r.date.isoformat() if r.date else '',
            'status': r.status,
        })
    os.makedirs('reports', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_gen = ReportGenerator()
    if format_type == 'excel':
        path = f'reports/faculty_report_{faculty.faculty_id}_{timestamp}.xlsx'
        report_gen.generate_attendance_excel(attendance_data, path)
        return send_file(path, as_attachment=True, download_name=f'attendance_{timestamp}.xlsx')
    elif format_type == 'csv':
        path = f'reports/faculty_report_{faculty.faculty_id}_{timestamp}.csv'
        report_gen.generate_attendance_csv(attendance_data, path)
        return send_file(path, as_attachment=True, download_name=f'attendance_{timestamp}.csv')
    else:
        path = f'reports/faculty_report_{faculty.faculty_id}_{timestamp}.txt'
        report_gen.generate_comprehensive_report(attendance_data, path)
        return send_file(path, as_attachment=True, download_name=f'attendance_{timestamp}.txt')

@faculty_bp.route('/profile')
@login_required
@faculty_required
def profile():
    faculty = get_faculty()
    if not faculty:
        flash('Faculty profile not found', 'danger')
        return redirect(url_for('auth.login'))
    session_count = AttendanceSession.query.filter_by(faculty_id=faculty.faculty_id).count()
    total_classes = Attendance.query.filter_by(faculty_id=faculty.faculty_id).count()
    return render_template('faculty_profile.html', faculty=faculty,
                          session_count=session_count, total_classes=total_classes)

@faculty_bp.route('/profile', methods=['POST'])
@login_required
@faculty_required
def update_profile():
    faculty = get_faculty()
    if not faculty:
        flash('Faculty profile not found', 'danger')
        return redirect(url_for('auth.login'))
    faculty.name = request.form.get('name', faculty.name)
    faculty.email = request.form.get('email', faculty.email)
    faculty.phone = request.form.get('phone', faculty.phone)
    faculty.department = request.form.get('department', faculty.department)
    db.session.commit()
    flash('Profile updated successfully', 'success')
    return redirect(url_for('faculty.profile'))

@faculty_bp.route('/students')
@login_required
@faculty_required
def students():
    faculty = get_faculty()
    if not faculty:
        flash('Faculty profile not found', 'danger')
        return redirect(url_for('auth.login'))
    semester_filter = request.args.get('semester', '')
    section_filter = request.args.get('section', '')
    search = request.args.get('search', '')
    query = Student.query.filter_by(is_active=True)
    if faculty.department:
        query = query.filter_by(department=faculty.department)
    if semester_filter:
        query = query.filter_by(semester=semester_filter)
    if section_filter:
        query = query.filter_by(section=section_filter)
    if search:
        query = query.filter(
            db.or_(
                Student.name.ilike(f'%{search}%'),
                Student.usn.ilike(f'%{search}%'),
                Student.student_id.ilike(f'%{search}%')
            )
        )
    student_list = query.order_by(Student.name).all()
    student_stats = []
    for s in student_list:
        atd_count = Attendance.query.filter_by(student_id=s.student_id, faculty_id=faculty.faculty_id).count()
        present_count = Attendance.query.filter_by(student_id=s.student_id, faculty_id=faculty.faculty_id, status='Present').count()
        pct = round(present_count / atd_count * 100, 1) if atd_count > 0 else 0
        student_stats.append({'student': s, 'total': atd_count, 'present': present_count, 'percentage': pct})
    semesters = db.session.query(Student.semester).filter_by(department=faculty.department).distinct().all()
    sections = db.session.query(Student.section).filter_by(department=faculty.department).distinct().all()
    return render_template('faculty_students.html', faculty=faculty,
                          student_stats=student_stats,
                          semester_list=[s[0] for s in semesters],
                          section_list=[s[0] for s in sections],
                          semester_filter=semester_filter,
                          section_filter=section_filter, search=search)

@faculty_bp.route('/students/add', methods=['POST'])
@login_required
@faculty_required
def add_student():
    faculty = get_faculty()
    if not faculty:
        flash('Faculty profile not found', 'danger')
        return redirect(url_for('auth.login'))
    student_id = request.form.get('student_id', '').strip()
    if Student.query.filter_by(student_id=student_id).first():
        flash('Student ID already exists', 'danger')
        return redirect(url_for('faculty.students'))
    if Student.query.filter_by(usn=request.form.get('usn', '')).first():
        flash('USN already exists', 'danger')
        return redirect(url_for('faculty.students'))
    student = Student(
        student_id=student_id,
        usn=request.form.get('usn', ''),
        name=request.form.get('name', ''),
        department=faculty.department,
        semester=request.form.get('semester', ''),
        section=request.form.get('section', ''),
        email=request.form.get('email', ''),
        phone=request.form.get('phone', '')
    )
    face_file = request.files.get('face_image')
    if face_file and face_file.filename:
        from werkzeug.utils import secure_filename
        import uuid
        ext = face_file.filename.rsplit('.', 1)[-1].lower() if '.' in face_file.filename else 'jpg'
        filename = f'{student_id}_{uuid.uuid4().hex[:8]}.{ext}'
        path = os.path.join('dataset', student_id, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        face_file.save(path)
        student.profile_image = path
    if not User.query.filter_by(username=student_id).first():
        user = User(
            username=student_id,
            password=generate_password_hash(student_id + '@123'),
            role='student',
            email=request.form.get('email', '')
        )
        db.session.add(user)
    db.session.add(student)
    db.session.commit()
    flash(f'Student {student.name} added successfully (login: {student_id} / {student_id}@123)', 'success')
    return redirect(url_for('faculty.students'))

@faculty_bp.route('/notifications/read/<int:nid>', methods=['POST'])
@login_required
@faculty_required
def mark_notification_read(nid):
    notif = Notification.query.get_or_404(nid)
    notif.is_read = True
    db.session.commit()
    return jsonify({'status': 'success'})

@faculty_bp.route('/alerts/read/<int:aid>', methods=['POST'])
@login_required
@faculty_required
def mark_alert_read(aid):
    alert = Alert.query.get_or_404(aid)
    alert.is_read = True
    db.session.commit()
    return jsonify({'status': 'success'})

@faculty_bp.route('/results')
@login_required
@faculty_required
def test_results():
    faculty = get_faculty()
    results = TestResult.query.order_by(TestResult.created_at.desc()).all()
    subjects = db.session.query(TestResult.subject_name).distinct().all()
    all_fac = {f.faculty_id: f.name for f in Faculty.query.all()}
    return render_template('faculty_results.html', faculty=faculty, results=results,
                          subject_list=[s[0] for s in subjects], faculty_names=all_fac)

@faculty_bp.route('/results/add', methods=['GET', 'POST'])
@login_required
@faculty_required
def add_test_result():
    faculty = get_faculty()
    if request.method == 'POST':
        subject = request.form.get('subject_name', '')
        semester = request.form.get('semester', '')
        section = request.form.get('section', '')
        test_type = request.form.get('test_type', '')
        total_marks = float(request.form.get('total_marks', 100))
        students = Student.query.filter_by(
            department=faculty.department, semester=semester, section=section, is_active=True
        ).all()
        for student in students:
            marks_str = request.form.get(f'marks_{student.student_id}')
            if marks_str and marks_str.strip():
                marks = float(marks_str)
                pct = (marks / total_marks) * 100
                if pct >= 90:
                    grade = 'A'
                elif pct >= 75:
                    grade = 'B'
                elif pct >= 60:
                    grade = 'C'
                elif pct >= 50:
                    grade = 'D'
                else:
                    grade = 'F'
                result = TestResult(
                    student_id=student.student_id,
                    faculty_id=faculty.faculty_id,
                    subject_name=subject,
                    department=faculty.department,
                    semester=semester,
                    section=section,
                    test_type=test_type,
                    marks=marks,
                    total_marks=total_marks,
                    grade=grade
                )
                db.session.add(result)
        db.session.commit()
        flash('Test results published successfully', 'success')
        return redirect(url_for('faculty.test_results'))
    semesters = db.session.query(Student.semester).filter_by(department=faculty.department).distinct().all()
    sections = db.session.query(Student.section).filter_by(department=faculty.department).distinct().all()
    subjects = db.session.query(Timetable.subject_name).filter_by(faculty_id=faculty.faculty_id).distinct().all()
    return render_template('faculty_add_result.html', faculty=faculty,
                          semester_list=[s[0] for s in semesters],
                          section_list=[s[0] for s in sections],
                          subject_list=[s[0] for s in subjects])

@faculty_bp.route('/results/students')
@login_required
@faculty_required
def results_students():
    faculty = get_faculty()
    semester = request.args.get('semester')
    section = request.args.get('section')
    students = Student.query.filter_by(
        department=faculty.department, semester=semester, section=section, is_active=True
    ).order_by(Student.name).all()
    return jsonify({
        'students': [{'student_id': s.student_id, 'usn': s.usn, 'name': s.name} for s in students]
    })


@faculty_bp.route('/results/edit/<int:result_id>', methods=['GET', 'POST'])
@login_required
@faculty_required
def edit_test_result(result_id):
    result = TestResult.query.get_or_404(result_id)
    faculty = get_faculty()
    if request.method == 'POST':
        marks = float(request.form.get('marks', 0))
        total_marks = float(request.form.get('total_marks', result.total_marks))
        pct = (marks / total_marks) * 100
        if pct >= 90:       grade = 'A'
        elif pct >= 75:     grade = 'B'
        elif pct >= 60:     grade = 'C'
        elif pct >= 50:     grade = 'D'
        else:               grade = 'F'
        result.marks = marks
        result.total_marks = total_marks
        result.grade = grade
        db.session.commit()
        flash('Result updated', 'success')
        return redirect(url_for('faculty.test_results'))
    return render_template('faculty_edit_result.html', faculty=faculty, result=result)
