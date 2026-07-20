import numpy as np
from flask import render_template, request, redirect, url_for, jsonify, flash, send_file
from flask_login import login_required, current_user
from database.models import db, Student, Attendance, Notification, Timetable, TestResult
from . import student_bp
from datetime import date, datetime, timedelta
from utils.report_generator import ReportGenerator
import os

def student_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Access denied', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def get_student():
    return Student.query.filter_by(email=current_user.email).first()

@student_bp.route('/portal')
@login_required
@student_required
def portal():
    student = get_student()
    if not student:
        flash('Student profile not found', 'danger')
        return redirect(url_for('auth.login'))
    attendance = Attendance.query.filter_by(student_id=student.student_id).order_by(Attendance.date.desc()).all()
    stats = {
        'total': len(attendance),
        'present': sum(1 for a in attendance if a.status == 'Present'),
        'absent': sum(1 for a in attendance if a.status == 'Absent'),
        'late': sum(1 for a in attendance if a.status == 'Late'),
    }
    if stats['total'] > 0:
        stats['attendance_pct'] = round(stats['present'] / stats['total'] * 100, 1)
    else:
        stats['attendance_pct'] = 0.0
    recent = attendance[:10]
    return render_template('student_portal.html', student=student,
                          attendance=recent, stats=stats, all_count=len(attendance))

@student_bp.route('/attendance')
@login_required
@student_required
def attendance():
    student = get_student()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    records = Attendance.query.filter_by(student_id=student.student_id).order_by(
        Attendance.date.desc()
    ).offset((page - 1) * per_page).limit(per_page).all()
    total = Attendance.query.filter_by(student_id=student.student_id).count()
    return render_template('student_attendance_list.html', student=student,
                          records=records, page=page, total_pages=(total + per_page - 1) // per_page)

@student_bp.route('/results')
@login_required
@student_required
def test_results():
    student = get_student()
    if not student:
        flash('Student profile not found', 'danger')
        return redirect(url_for('auth.login'))
    results = TestResult.query.filter_by(student_id=student.student_id).order_by(TestResult.created_at.desc()).all()
    return render_template('student_results.html', student=student, results=results)

@student_bp.route('/timetable')
@login_required
@student_required
def timetable():
    student = get_student()
    if not student:
        flash('Student profile not found', 'danger')
        return redirect(url_for('auth.login'))
    from database.models import Faculty
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    week_timetable = {}
    for day in days:
        week_timetable[day] = Timetable.query.filter_by(
            department=student.department, semester=student.semester,
            section=student.section, day=day
        ).order_by(Timetable.start_time).all()
    faculty_names = {f.faculty_id: f.name for f in Faculty.query.all()}
    return render_template('student_timetable.html', student=student, week_timetable=week_timetable, days=days, faculty_names=faculty_names)

@student_bp.route('/analytics')
@login_required
@student_required
def analytics():
    student = get_student()
    records = Attendance.query.filter_by(student_id=student.student_id).order_by(Attendance.date).all()
    return jsonify({
        'total_records': len(records)
    })

@student_bp.route('/analytics/page')
@login_required
@student_required
def analytics_page():
    student = get_student()
    if not student:
        flash('Student profile not found', 'danger')
        return redirect(url_for('auth.login'))
    records = Attendance.query.filter_by(student_id=student.student_id).order_by(Attendance.date).all()
    stats = {
        'total_records': len(records),
        'present': sum(1 for r in records if r.status == 'Present'),
        'absent': sum(1 for r in records if r.status == 'Absent'),
        'late': sum(1 for r in records if r.status == 'Late'),
        'subjects': list(set(r.subject_name for r in records if r.subject_name))
    }
    return render_template('student_analytics.html', student=student, stats=stats, records=records)

@student_bp.route('/notifications')
@login_required
@student_required
def notifications():
    student = get_student()
    notifs = Notification.query.filter_by(
        recipient_type='student', recipient_id=student.student_id
    ).order_by(Notification.created_at.desc()).all()
    return jsonify([{
        'id': n.notification_id,
        'title': n.title,
        'message': n.message,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat() if n.created_at else ''
    } for n in notifs])

@student_bp.route('/notifications/read/<int:nid>', methods=['POST'])
@login_required
@student_required
def mark_notification_read(nid):
    notif = Notification.query.get_or_404(nid)
    notif.is_read = True
    db.session.commit()
    return jsonify({'status': 'success'})

@student_bp.route('/profile')
@login_required
@student_required
def profile():
    student = get_student()
    if not student:
        flash('Student profile not found', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('student_profile.html', student=student)

@student_bp.route('/profile', methods=['POST'])
@login_required
@student_required
def update_profile():
    student = get_student()
    if not student:
        flash('Student profile not found', 'danger')
        return redirect(url_for('auth.login'))
    student.name = request.form.get('name', student.name)
    student.email = request.form.get('email', student.email)
    student.phone = request.form.get('phone', student.phone)
    student.parent_phone = request.form.get('parent_phone', student.parent_phone)
    student.parent_email = request.form.get('parent_email', student.parent_email)
    db.session.commit()
    flash('Profile updated successfully', 'success')
    return redirect(url_for('student.profile'))

@student_bp.route('/report')
@login_required
@student_required
def download_report():
    student = get_student()
    if not student:
        flash('Student profile not found', 'danger')
        return redirect(url_for('auth.login'))
    format_type = request.args.get('format', 'pdf')
    records = Attendance.query.filter_by(student_id=student.student_id).order_by(Attendance.date.desc()).all()
    attendance_data = [{
        'date': r.date.isoformat() if r.date else '',
        'subject': r.subject_name,
        'status': r.status,
        'time': str(r.time) if r.time else ''
    } for r in records]
    os.makedirs('reports', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_gen = ReportGenerator()
    if format_type == 'excel':
        path = f'reports/student_report_{student.student_id}_{timestamp}.xlsx'
        report_gen.generate_attendance_excel(attendance_data, path)
        return send_file(path, as_attachment=True, download_name=f'{student.usn}_report_{timestamp}.xlsx')
    elif format_type == 'csv':
        path = f'reports/student_report_{student.student_id}_{timestamp}.csv'
        report_gen.generate_attendance_csv(attendance_data, path)
        return send_file(path, as_attachment=True, download_name=f'{student.usn}_report_{timestamp}.csv')
    else:
        path = f'reports/student_report_{student.student_id}_{timestamp}.txt'
        report_gen.generate_comprehensive_report(attendance_data, path)
        return send_file(path, as_attachment=True, download_name=f'{student.usn}_report_{timestamp}.txt')
