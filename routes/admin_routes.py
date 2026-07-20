from flask import render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from database.models import db, User, Student, Faculty, Subject, Timetable, LeaveRequest, Attendance, AttendanceSession, Alert, Notification, Department, DepartmentSection
from . import admin_bp
from datetime import datetime, date, timezone
from utils.notifications import NotificationService
import os
import uuid
import csv
import io
import logging

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def validate_image(file):
    if not file or not file.filename:
        return False
    if not allowed_file(file.filename):
        return False
    if file.content_length and file.content_length > 5 * 1024 * 1024:
        return False
    return True

notification_service = NotificationService()
logger = logging.getLogger(__name__)

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    students = Student.query.all()
    faculty = Faculty.query.all()
    subjects = Subject.query.all()
    today = date.today()
    today_attendance = Attendance.query.filter_by(date=today).all()
    leaves = LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).all()
    sessions = AttendanceSession.query.order_by(AttendanceSession.started_at.desc()).limit(5).all()
    alerts = Alert.query.order_by(Alert.created_at.desc()).limit(10).all()
    stats = {
        'total_students': len(students),
        'total_faculty': len(faculty),
        'total_subjects': len(subjects),
        'today_attendance': len(today_attendance),
        'pending_leaves': LeaveRequest.query.filter_by(status='Pending').count(),
        'active_sessions': AttendanceSession.query.filter_by(status='active').count()
    }
    return render_template('admin_dashboard.html', students=students, faculty=faculty,
                          subjects=subjects, leaves=leaves, sessions=sessions,
                          alerts=alerts, stats=stats)

@admin_bp.route('/students')
@login_required
@admin_required
def students():
    dept_filter = request.args.get('department', '')
    sem_filter = request.args.get('semester', '')
    sec_filter = request.args.get('section', '')
    search = request.args.get('search', '')
    query = Student.query
    if dept_filter:
        query = query.filter_by(department=dept_filter)
    if sem_filter:
        query = query.filter_by(semester=sem_filter)
    if sec_filter:
        query = query.filter_by(section=sec_filter)
    if search:
        query = query.filter(
            db.or_(
                Student.name.ilike(f'%{search}%'),
                Student.usn.ilike(f'%{search}%'),
                Student.student_id.ilike(f'%{search}%')
            )
        )
    students = query.order_by(Student.name).all()
    departments = Department.query.order_by(Department.name).all()
    semesters = db.session.query(Student.semester).distinct().order_by(Student.semester).all()
    sections = db.session.query(Student.section).distinct().order_by(Student.section).all()
    return render_template('admin_students.html', students=students, departments=departments,
                          semester_list=[s[0] for s in semesters],
                          section_list=[s[0] for s in sections],
                          dept_filter=dept_filter, sem_filter=sem_filter,
                          sec_filter=sec_filter, search=search)

@admin_bp.route('/students/add', methods=['POST'])
@login_required
@admin_required
def add_student():
    data = request.form
    student_id = data.get('student_id', '').strip()
    if Student.query.filter_by(student_id=student_id).first():
        flash('Student ID already exists', 'danger')
        return redirect(url_for('admin.students'))
    if Student.query.filter_by(usn=data.get('usn', '')).first():
        flash('USN already exists', 'danger')
        return redirect(url_for('admin.students'))
    student = Student(
        student_id=student_id,
        usn=data.get('usn', ''),
        name=data.get('name', ''),
        department=data.get('department', ''),
        semester=data.get('semester', ''),
        section=data.get('section', ''),
        email=data.get('email', ''),
        phone=data.get('phone', ''),
        parent_phone=data.get('parent_phone', ''),
        parent_email=data.get('parent_email', '')
    )
    face_file = request.files.get('face_image')
    if face_file and face_file.filename and validate_image(face_file):
        ext = face_file.filename.rsplit('.', 1)[-1].lower()
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
            email=data.get('email', '')
        )
        db.session.add(user)
    db.session.add(student)
    db.session.commit()
    flash('Student added successfully', 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/students/edit/<student_id>', methods=['POST'])
@login_required
@admin_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.name = request.form.get('name', student.name)
    student.department = request.form.get('department', student.department)
    student.semester = request.form.get('semester', student.semester)
    student.section = request.form.get('section', student.section)
    student.email = request.form.get('email', student.email)
    student.phone = request.form.get('phone', student.phone)
    student.parent_phone = request.form.get('parent_phone', student.parent_phone)
    student.parent_email = request.form.get('parent_email', student.parent_email)
    face_file = request.files.get('face_image')
    if face_file and face_file.filename and validate_image(face_file):
        ext = face_file.filename.rsplit('.', 1)[-1].lower()
        filename = f'{student_id}_{uuid.uuid4().hex[:8]}.{ext}'
        path = os.path.join('dataset', student_id, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        face_file.save(path)
        student.profile_image = path
    db.session.commit()
    flash('Student updated successfully', 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/students/delete/<student_id>', methods=['POST'])
@login_required
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    Attendance.query.filter_by(student_id=student_id).delete()
    User.query.filter_by(username=student_id).delete()
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted successfully', 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/faculty')
@login_required
@admin_required
def faculty():
    faculty_list = Faculty.query.all()
    departments = Department.query.order_by(Department.name).all()
    return render_template('admin_faculty.html', faculty=faculty_list, departments=departments)

@admin_bp.route('/faculty/add', methods=['POST'])
@login_required
@admin_required
def add_faculty():
    data = request.form
    faculty_id = data.get('faculty_id', '').strip()
    if Faculty.query.filter_by(faculty_id=faculty_id).first():
        flash('Faculty ID already exists', 'danger')
        return redirect(url_for('admin.faculty'))
    faculty = Faculty(
        faculty_id=faculty_id,
        name=data.get('name', ''),
        email=data.get('email', ''),
        phone=data.get('phone', ''),
        department=data.get('department', ''),
        semesters_handled=','.join(request.form.getlist('semesters'))
    )
    if not User.query.filter_by(username=faculty_id).first():
        user = User(
            username=faculty_id,
            password=generate_password_hash(faculty_id + '@123'),
            role='faculty',
            email=data.get('email', '')
        )
        db.session.add(user)
    db.session.add(faculty)
    db.session.commit()
    flash('Faculty added successfully', 'success')
    return redirect(url_for('admin.faculty'))

@admin_bp.route('/faculty/edit/<faculty_id>', methods=['POST'])
@login_required
@admin_required
def edit_faculty(faculty_id):
    faculty = Faculty.query.get_or_404(faculty_id)
    faculty.name = request.form.get('name', faculty.name)
    faculty.email = request.form.get('email', faculty.email)
    faculty.phone = request.form.get('phone', faculty.phone)
    faculty.department = request.form.get('department', faculty.department)
    faculty.semesters_handled = ','.join(request.form.getlist('semesters'))
    db.session.commit()
    flash('Faculty updated successfully', 'success')
    return redirect(url_for('admin.faculty'))

@admin_bp.route('/faculty/delete/<faculty_id>', methods=['POST'])
@login_required
@admin_required
def delete_faculty(faculty_id):
    faculty = Faculty.query.get_or_404(faculty_id)
    Timetable.query.filter_by(faculty_id=faculty_id).delete()
    Attendance.query.filter_by(faculty_id=faculty_id).delete()
    LeaveRequest.query.filter_by(faculty_id=faculty_id).delete()
    User.query.filter_by(username=faculty_id).delete()
    db.session.delete(faculty)
    db.session.commit()
    flash('Faculty deleted successfully', 'success')
    return redirect(url_for('admin.faculty'))


@admin_bp.route('/leaves')
@login_required
@admin_required
def leaves():
    leaves = LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).all()
    return render_template('admin_leaves.html', leaves=leaves)

@admin_bp.route('/leaves/approve/<int:leave_id>', methods=['POST'])
@login_required
@admin_required
def approve_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    leave.status = 'Approved'
    leave.admin_remarks = request.form.get('remarks', 'Approved')
    leave.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    notif = Notification(
        recipient_type='faculty',
        recipient_id=leave.faculty_id,
        title='Leave Approved',
        message=f'Your {leave.leave_type} leave has been approved.'
    )
    db.session.add(notif)
    db.session.commit()
    try:
        faculty = Faculty.query.get(leave.faculty_id)
        if faculty and faculty.email:
            notification_service.send_leave_status_notification(
                faculty.email, faculty.name, 'Approved', leave.admin_remarks or ''
            )
    except Exception as e:
        logger.warning(f'Leave approval email failed for {leave.faculty_id}: {e}')
    flash('Leave approved', 'success')
    return redirect(url_for('admin.leaves'))

@admin_bp.route('/leaves/reject/<int:leave_id>', methods=['POST'])
@login_required
@admin_required
def reject_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    leave.status = 'Rejected'
    leave.admin_remarks = request.form.get('remarks', 'Rejected')
    leave.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    notif = Notification(
        recipient_type='faculty',
        recipient_id=leave.faculty_id,
        title='Leave Rejected',
        message=f'Your {leave.leave_type} leave has been rejected. Remarks: {leave.admin_remarks}'
    )
    db.session.add(notif)
    db.session.commit()
    # Send email notification to faculty
    try:
        faculty = Faculty.query.get(leave.faculty_id)
        if faculty and faculty.email:
            notification_service.send_leave_status_notification(
                faculty.email, faculty.name, 'Rejected', leave.admin_remarks or ''
            )
    except Exception as e:
        logger.warning(f'Leave rejection email failed for {leave.faculty_id}: {e}')
    flash('Leave rejected', 'warning')
    return redirect(url_for('admin.leaves'))

@admin_bp.route('/students/bulk-add', methods=['POST'])
@login_required
@admin_required
def bulk_add_students():
    file = request.files.get('csv_file')
    if not file or not file.filename:
        flash('No file uploaded', 'danger')
        return redirect(url_for('admin.students'))
    if not file.filename.endswith('.csv'):
        flash('Please upload a CSV file', 'danger')
        return redirect(url_for('admin.students'))
    try:
        stream = io.StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        added = 0
        skipped = 0
        for row in reader:
            student_id = row.get('student_id', '').strip()
            usn = row.get('usn', '').strip()
            name = row.get('name', '').strip()
            if not student_id or not usn or not name:
                skipped += 1
                continue
            if Student.query.filter_by(student_id=student_id).first():
                skipped += 1
                continue
            if Student.query.filter_by(usn=usn).first():
                skipped += 1
                continue
            student = Student(
                student_id=student_id,
                usn=usn,
                name=name,
                department=row.get('department', '').strip(),
                semester=row.get('semester', '1').strip(),
                section=row.get('section', 'A').strip(),
                email=row.get('email', '').strip(),
                phone=row.get('phone', '').strip(),
                parent_phone=row.get('parent_phone', '').strip(),
                parent_email=row.get('parent_email', '').strip()
            )
            if not User.query.filter_by(username=student_id).first():
                user = User(
                    username=student_id,
                    password=generate_password_hash(student_id + '@123'),
                    role='student',
                    email=row.get('email', '').strip()
                )
                db.session.add(user)
            db.session.add(student)
            added += 1
        db.session.commit()
        flash(f'Bulk import complete: {added} added, {skipped} skipped', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error importing CSV: {str(e)}', 'danger')
    return redirect(url_for('admin.students'))

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    total_students = Student.query.count()
    total_faculty = Faculty.query.count()
    total_attendance = Attendance.query.count()
    today = date.today()
    today_count = Attendance.query.filter_by(date=today).count()
    present_today = Attendance.query.filter_by(date=today, status='Present').count()
    weekly_present = []
    weekly_absent = []
    from datetime import timedelta
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        day_records = Attendance.query.filter_by(date=d).all()
        p = sum(1 for r in day_records if r.status == 'Present')
        a = sum(1 for r in day_records if r.status in ('Absent', 'Late'))
        weekly_present.append(p)
        weekly_absent.append(a)
    return jsonify({
        'total_students': total_students,
        'total_faculty': total_faculty,
        'total_attendance': total_attendance,
        'today_attendance': today_count,
        'present_today': present_today,
        'weekly_present': weekly_present,
        'weekly_absent': weekly_absent
    })

@admin_bp.route('/ranking')
@login_required
@admin_required
def student_ranking():
    students = Student.query.all()
    ranking = []
    for s in students:
        total = Attendance.query.filter_by(student_id=s.student_id).count()
        if total == 0:
            continue
        present = Attendance.query.filter_by(student_id=s.student_id, status='Present').count()
        pct = round(present / total * 100, 1)
        ranking.append({'student_id': s.student_id, 'name': s.name, 'total': total, 'present': present, 'pct': pct})
    ranking.sort(key=lambda x: x['pct'], reverse=True)
    return jsonify({'ranking': ranking[:20]})

@admin_bp.route('/analytics/monthly')
@login_required
@admin_required
def monthly_analytics():
    from datetime import timedelta
    months = []
    today = date.today()
    for i in range(5, -1, -1):
        month_start = today.replace(day=1) - timedelta(days=i*30)
        month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        records = Attendance.query.filter(Attendance.date >= month_start, Attendance.date <= month_end).all()
        total = len(records)
        present = sum(1 for r in records if r.status == 'Present')
        months.append({
            'month': month_start.strftime('%b %Y'),
            'total': total,
            'present': present,
            'absent': total - present,
            'pct': round(present / total * 100, 1) if total else 0
        })
    return jsonify({'months': months})

@admin_bp.route('/analytics/heatmap')
@login_required
@admin_required
def analytics_heatmap():
    from datetime import timedelta
    today = date.today()
    days = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    weeks = []
    for w in range(4):
        week_data = []
        for d in range(7):
            dt = today - timedelta(days=(3-w)*7 + (6-d))
            records = Attendance.query.filter_by(date=dt).all()
            total = len(records)
            present = sum(1 for r in records if r.status == 'Present')
            pct = round(present / total * 100, 1) if total else 0
            week_data.append({'x': d, 'y': w, 'v': pct})
        weeks.extend(week_data)
    return jsonify({'data': weeks, 'labels': days})

@admin_bp.route('/analytics/page')
@login_required
@admin_required
def analytics_page():
    return render_template('analytics.html')

@admin_bp.route('/notifications')
@login_required
@admin_required
def notifications():
    notifs = Notification.query.filter_by(
        recipient_type='admin'
    ).order_by(Notification.created_at.desc()).all()
    return render_template('admin_notifications.html', notifications=notifs)

@admin_bp.route('/notifications/read/<int:nid>', methods=['POST'])
@login_required
@admin_required
def mark_notification_read(nid):
    notif = Notification.query.get_or_404(nid)
    notif.is_read = True
    db.session.commit()
    return jsonify({'status': 'success'})

@admin_bp.route('/notifications/read-all', methods=['POST'])
@login_required
@admin_required
def mark_all_notifications_read():
    Notification.query.filter_by(recipient_type='admin', is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'status': 'success'})

@admin_bp.route('/departments')
@login_required
@admin_required
def departments():
    depts = Department.query.order_by(Department.name).all()
    return render_template('admin_departments.html', departments=depts)

@admin_bp.route('/departments/add', methods=['POST'])
@login_required
@admin_required
def add_department():
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip()
    if not name or not code:
        flash('Name and code are required', 'danger')
        return redirect(url_for('admin.departments'))
    if Department.query.filter((Department.name == name) | (Department.code == code)).first():
        flash('Department name or code already exists', 'danger')
        return redirect(url_for('admin.departments'))
    dept = Department(name=name, code=code)
    db.session.add(dept)
    db.session.commit()
    flash(f'Department {name} ({code}) created', 'success')
    return redirect(url_for('admin.departments'))

@admin_bp.route('/departments/edit/<int:dept_id>', methods=['POST'])
@login_required
@admin_required
def edit_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip()
    if not name or not code:
        flash('Name and code are required', 'danger')
        return redirect(url_for('admin.departments'))
    existing = Department.query.filter(
        db.or_(Department.name == name, Department.code == code),
        Department.id != dept_id
    ).first()
    if existing:
        flash('Another department already uses that name or code', 'danger')
        return redirect(url_for('admin.departments'))
    dept.name = name
    dept.code = code
    db.session.commit()
    flash('Department updated', 'success')
    return redirect(url_for('admin.departments'))

@admin_bp.route('/departments/delete/<int:dept_id>', methods=['POST'])
@login_required
@admin_required
def delete_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    db.session.delete(dept)
    db.session.commit()
    flash('Department deleted', 'success')
    return redirect(url_for('admin.departments'))

@admin_bp.route('/api/departments')
@login_required
def api_departments():
    depts = Department.query.order_by(Department.name).all()
    return jsonify([{'id': d.id, 'name': d.name, 'code': d.code} for d in depts])

# ── Department Detail: Subjects + Timetable ──

@admin_bp.route('/departments/<int:dept_id>')
@login_required
@admin_required
def department_detail(dept_id):
    dept = Department.query.get_or_404(dept_id)
    subjects = Subject.query.filter_by(department=dept.name).order_by(Subject.semester, Subject.subject_name).all()
    faculty_list = Faculty.query.filter_by(department=dept.name, is_active=True).all()
    sections = DepartmentSection.query.filter_by(department_name=dept.name).order_by(DepartmentSection.semester, DepartmentSection.section).all()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    week_timetable = {}
    for day in days:
        week_timetable[day] = Timetable.query.filter_by(department=dept.name).filter(
            Timetable.day == day
        ).order_by(Timetable.start_time).all()
    return render_template('admin_department_detail.html', dept=dept, subjects=subjects,
                          faculty=faculty_list, sections=sections,
                          week_timetable=week_timetable, days=days,
                          faculty_names={f.faculty_id: f.name for f in Faculty.query.all()})

@admin_bp.route('/departments/<int:dept_id>/subjects/add', methods=['POST'])
@login_required
@admin_required
def add_department_subject(dept_id):
    dept = Department.query.get_or_404(dept_id)
    sub_id = request.form.get('subject_id', '').strip()
    if Subject.query.filter_by(subject_id=sub_id).first():
        flash('Subject ID already exists', 'danger')
        return redirect(url_for('admin.department_detail', dept_id=dept_id))
    subject = Subject(
        subject_id=sub_id,
        subject_name=request.form.get('subject_name', '').strip(),
        department=dept.name,
        semester=request.form.get('semester', ''),
        section=request.form.get('section', 'A'),
        is_lab=request.form.get('is_lab') == 'on',
        hours_per_week=int(request.form.get('hours_per_week', 4)),
        credits=int(request.form.get('credits', 4))
    )
    db.session.add(subject)
    db.session.commit()
    flash(f'Subject {subject.subject_name} added', 'success')
    return redirect(url_for('admin.department_detail', dept_id=dept_id))

@admin_bp.route('/departments/<int:dept_id>/subjects/<sub_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_department_subject(dept_id, sub_id):
    subject = Subject.query.get_or_404(sub_id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted', 'success')
    return redirect(url_for('admin.department_detail', dept_id=dept_id))

@admin_bp.route('/departments/<int:dept_id>/sections/add', methods=['POST'])
@login_required
@admin_required
def add_department_section(dept_id):
    dept = Department.query.get_or_404(dept_id)
    semester = request.form.get('semester', '').strip()
    section = request.form.get('section', '').strip()
    if not semester or not section:
        flash('Semester and section required', 'danger')
        return redirect(url_for('admin.department_detail', dept_id=dept_id))
    if DepartmentSection.query.filter_by(department_name=dept.name, semester=semester, section=section).first():
        flash(f'Section {section} already exists for semester {semester}', 'danger')
        return redirect(url_for('admin.department_detail', dept_id=dept_id))
    ds = DepartmentSection(department_name=dept.name, semester=semester, section=section)
    db.session.add(ds)
    db.session.commit()
    flash(f'Section {section} added for semester {semester}', 'success')
    return redirect(url_for('admin.department_detail', dept_id=dept_id))

@admin_bp.route('/departments/<int:dept_id>/sections/<int:sec_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_department_section(dept_id, sec_id):
    ds = DepartmentSection.query.get_or_404(sec_id)
    db.session.delete(ds)
    db.session.commit()
    flash('Section deleted', 'success')
    return redirect(url_for('admin.department_detail', dept_id=dept_id))

@admin_bp.route('/departments/<int:dept_id>/timetable/generate', methods=['POST'])
@login_required
@admin_required
def generate_timetable(dept_id):
    semester = request.form.get('semester', '')
    if dept_id == 0:
        dept_name = request.form.get('department', '')
        dept = Department.query.filter_by(name=dept_name).first()
        # Auto-select first section after generation
        first_sec = DepartmentSection.query.filter_by(department_name=dept_name, semester=semester).first()
        sec_param = first_sec.section if first_sec else ''
        redirect_url = url_for('admin.timetable_view', department=dept_name,
                                semester=semester, section=sec_param)
    else:
        dept = Department.query.get_or_404(dept_id)
        redirect_url = url_for('admin.department_detail', dept_id=dept_id)
    if not dept:
        flash('Department not found', 'danger')
        return redirect(url_for('admin.departments'))
    if not semester:
        flash('Select semester', 'danger')
        return redirect(redirect_url)

    sections = DepartmentSection.query.filter_by(department_name=dept.name, semester=semester).all()
    if not sections:
        flash('No sections defined for this semester. Create sections first.', 'danger')
        return redirect(redirect_url)

    subjects = Subject.query.filter_by(department=dept.name, semester=semester).all()
    if not subjects:
        flash('No subjects found for this semester', 'danger')
        return redirect(redirect_url)

    all_fac = Faculty.query.filter_by(department=dept.name, is_active=True).all()
    faculty_list = [f for f in all_fac if semester in (f.semesters_handled or '').split(',')]
    if not faculty_list:
        flash(f'No faculty assigned to semester {semester} in this department. Set semesters in Faculty settings.', 'danger')
        return redirect(redirect_url)

    # Clear existing timetable for this dept/semester (all sections)
    Timetable.query.filter_by(department=dept.name, semester=semester).delete()
    db.session.commit()

    SLOTS = [
        ('A', '08:00', '09:00'),
        ('B', '09:00', '10:00'),
        ('C', '10:15', '11:15'),
        ('D', '11:15', '12:15'),
        ('E', '12:30', '13:30'),
        ('F', '13:30', '14:30'),
    ]
    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    busy = set()  # global: (faculty_id, day, slot_label)
    entries = []

    for sec in sections:
        sec_busy = set()  # per-section: (day, slot_label)
        for sub in subjects:
            fac = faculty_list[hash(sub.subject_id + sec.section) % len(faculty_list)]
            needed_h = sub.hours_per_week or (3 if sub.is_lab else 4)
            assigned = 0
            day_idx = hash(sub.subject_id + sec.section) % len(DAYS)

            while assigned < needed_h:
                found = False
                for di in range(len(DAYS)):
                    day = DAYS[(day_idx + di) % len(DAYS)]
                    for s_label, start, end in SLOTS:
                        if ((fac.faculty_id, day, s_label) not in busy and
                            (day, s_label) not in sec_busy):
                            busy.add((fac.faculty_id, day, s_label))
                            sec_busy.add((day, s_label))
                            entries.append((day, start, end, sec.section, sub, fac))
                            assigned += 1
                            found = True
                            break
                    if found:
                        break
                if not found:
                    day_idx += 1
                    if day_idx > 100:
                        break
                day_idx += 1

    # ── Persist all entries ──
    for day, start, end, sec_name, sub, fac in entries:
        tt = Timetable(
            faculty_id=fac.faculty_id,
            subject_name=sub.subject_name,
            department=dept.name,
            semester=semester,
            section=sec_name,
            day=day,
            start_time=start,
            end_time=end
        )
        db.session.add(tt)
    db.session.commit()
    total_slots = len(entries)
    total_sections = len(sections)
    flash(f'Timetable generated: {total_slots} slots across {total_sections} section(s) without clashes', 'success')
    return redirect(redirect_url)

@admin_bp.route('/departments/<int:dept_id>/timetable/clear', methods=['POST'])
@login_required
@admin_required
def clear_timetable(dept_id):
    dept = Department.query.get_or_404(dept_id)
    semester = request.form.get('semester', '')
    section = request.form.get('section', '')
    q = Timetable.query.filter_by(department=dept.name)
    if semester:
        q = q.filter_by(semester=semester)
    if section:
        q = q.filter_by(section=section)
    count = q.delete()
    db.session.commit()
    flash(f'Cleared {count} timetable entries', 'success')
    return redirect(url_for('admin.department_detail', dept_id=dept_id))

@admin_bp.route('/api/departments/<int:dept_id>/subjects')
@login_required
def api_dept_subjects(dept_id):
    dept = Department.query.get_or_404(dept_id)
    subjects = Subject.query.filter_by(department=dept.name).all()
    return jsonify([{
        'id': s.subject_id, 'name': s.subject_name,
        'semester': s.semester, 'section': s.section,
        'is_lab': s.is_lab, 'hours_per_week': s.hours_per_week
    } for s in subjects])

@admin_bp.route('/api/departments/<int:dept_id>/faculty')
@login_required
def api_dept_faculty(dept_id):
    dept = Department.query.get_or_404(dept_id)
    faculty = Faculty.query.filter_by(department=dept.name, is_active=True).all()
    return jsonify([{'id': f.faculty_id, 'name': f.name} for f in faculty])

# ── Dedicated Timetable View (hour-wise) ──

@admin_bp.route('/timetable-view')
@login_required
@admin_required
def timetable_view():
    dept_filter = request.args.get('department', '')
    sem_filter = request.args.get('semester', '')
    sec_filter = request.args.get('section', '')
    departments = Department.query.order_by(Department.name).all()
    sections = []
    week_timetable = {}
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    hour_rows = []

    if dept_filter and sem_filter and sec_filter:
        sections = DepartmentSection.query.filter_by(department_name=dept_filter, semester=sem_filter).all()
        for day in days:
            week_timetable[day] = Timetable.query.filter_by(
                department=dept_filter, semester=sem_filter, section=sec_filter, day=day
            ).order_by(Timetable.start_time).all()

        time_slot_defs = [
            ('08:00', '09:00', False),
            ('09:00', '10:00', False),
            ('10:00', '10:15', True),
            ('10:15', '11:15', False),
            ('11:15', '12:15', False),
            ('12:15', '12:30', True),
            ('12:30', '13:30', False),
            ('13:30', '14:30', False),
        ]
        for s_start, s_end, is_break in time_slot_defs:
            if is_break:
                hour_rows.append({'time': f'{s_start}-{s_end}', 'is_break': True, 'cells': {}})
            else:
                row = {'time': f'{s_start}-{s_end}', 'is_break': False, 'cells': {}}
                for day in days:
                    row['cells'][day] = None
                    for tt in week_timetable[day]:
                        if tt.start_time == s_start:
                            row['cells'][day] = tt
                hour_rows.append(row)
    elif dept_filter and sem_filter:
        sections = DepartmentSection.query.filter_by(department_name=dept_filter, semester=sem_filter).all()

    semesters = []
    if dept_filter:
        semesters = db.session.query(DepartmentSection.semester).filter_by(department_name=dept_filter).distinct().order_by(DepartmentSection.semester).all()
        semesters = [s[0] for s in semesters]

    faculty_list = Faculty.query.all()
    faculty_names = {f.faculty_id: f.name for f in faculty_list}

    return render_template('admin_timetable_view.html', departments=departments,
                          dept_filter=dept_filter, sem_filter=sem_filter, sec_filter=sec_filter,
                          semester_list=semesters, sections=sections, days=days, hour_rows=hour_rows,
                           faculty_names=faculty_names)


@admin_bp.route('/promote', methods=['GET', 'POST'])
@login_required
@admin_required
def promote_students():
    departments = Department.query.order_by(Department.name).all()

    if request.method == 'POST':
        dept_name = request.form.get('department', '')
        semester = request.form.get('semester', '')
        promoted_ids = request.form.getlist('promoted')
        failed_ids = request.form.getlist('failed')

        if not dept_name or not semester:
            flash('Select department and semester', 'danger')
            return redirect(url_for('admin.promote_students'))

        max_sem = 8 if dept_name.upper() in ('BE', 'BTECH', 'ENGINEERING', 'TECHNOLOGY AND SCIENCE') else 6

        for sid in promoted_ids:
            s = Student.query.get(sid)
            if s:
                new_sem = int(s.semester) + 1
                if new_sem <= max_sem:
                    s.semester = str(new_sem)
                    s.backlog_subjects = ''

        for sid in failed_ids:
            s = Student.query.get(sid)
            if s:
                new_sem = int(s.semester) + 1
                if new_sem <= max_sem:
                    s.semester = str(new_sem)
                subjects = Subject.query.filter_by(department=dept_name, semester=semester).all()
                backlog_names = ', '.join(set(sub.subject_name for sub in subjects))
                existing = [b.strip() for b in (s.backlog_subjects or '').split(',') if b.strip()]
                for bn in backlog_names.split(', '):
                    if bn not in existing:
                        existing.append(bn)
                s.backlog_subjects = ', '.join(existing)

        db.session.commit()
        flash(f'Promoted {len(promoted_ids)} student(s), marked {len(failed_ids)} student(s) with backlogs', 'success')
        return redirect(url_for('admin.promote_students', department=dept_name, semester=semester))

    dept_filter = request.args.get('department', '')
    sem_filter = request.args.get('semester', '')
    students = []
    if dept_filter and sem_filter:
        students = Student.query.filter_by(department=dept_filter, semester=sem_filter).order_by(Student.name).all()

    semesters = []
    if dept_filter:
        semesters = [s[0] for s in
                     db.session.query(Student.semester).filter_by(department=dept_filter).distinct().order_by(Student.semester).all()]

    return render_template('admin_promote.html', departments=departments,
                           dept_filter=dept_filter, sem_filter=sem_filter,
                           semester_list=semesters, students=students)


@admin_bp.route('/clear-all-data', methods=['POST'])
@login_required
@admin_required
def clear_all_data():
    for tbl in [Timetable, Attendance, AttendanceSession, TestResult,
                LeaveRequest, Alert, Notification, Subject,
                DepartmentSection, Department, Student, Faculty]:
        tbl.query.delete()
    # Delete all non-admin users
    User.query.filter(User.role != 'admin').delete()
    db.session.commit()
    flash('All data cleared. Admin account preserved.', 'warning')
    return redirect(url_for('admin.dashboard'))
