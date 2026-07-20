from flask import request, jsonify, send_file
from flask_login import login_required, current_user
from database.models import db, Attendance, Student, Faculty, LeaveRequest, Alert, Timetable, Subject
from . import api_bp
from datetime import date, datetime, timedelta
from utils.report_generator import ReportGenerator
import os
import numpy as np
import json

report_gen = ReportGenerator()

@api_bp.route('/attendance/start', methods=['POST'])
@login_required
def api_start_attendance():
    from routes.faculty_routes import start_attendance
    return start_attendance()

@api_bp.route('/attendance/mark', methods=['POST'])
@login_required
def api_mark_attendance():
    from routes.faculty_routes import mark_attendance
    return mark_attendance()

@api_bp.route('/recognize', methods=['POST'])
@login_required
def api_recognize():
    return jsonify({'status': 'error', 'message': 'Face recognition is disabled (AI features unavailable)'}), 503

@api_bp.route('/anti-spoof', methods=['POST'])
@login_required
def api_anti_spoof():
    return jsonify({'status': 'error', 'message': 'Anti-spoof is disabled (AI features unavailable)'}), 503

@api_bp.route('/report/generate', methods=['POST'])
@login_required
def api_generate_report():
    data = request.get_json() or request.form
    faculty_id = data.get('faculty_id', '')
    subject = data.get('subject_name', '')
    from_date_str = data.get('from_date', '')
    to_date_str = data.get('to_date', '')
    format_type = data.get('format', 'pdf')
    query = Attendance.query
    if faculty_id:
        query = query.filter_by(faculty_id=faculty_id)
    if subject:
        query = query.filter_by(subject_name=subject)
    if from_date_str:
        query = query.filter(Attendance.date >= datetime.strptime(from_date_str, '%Y-%m-%d').date())
    if to_date_str:
        query = query.filter(Attendance.date <= datetime.strptime(to_date_str, '%Y-%m-%d').date())
    records = query.order_by(Attendance.date.desc()).all()
    attendance_data = [{
        'student_id': r.student_id,
        'subject': r.subject_name,
        'date': r.date.isoformat() if r.date else '',
        'status': r.status,
    } for r in records]
    os.makedirs('reports', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if format_type == 'excel':
        path = f'reports/attendance_report_{timestamp}.xlsx'
        report_gen.generate_attendance_excel(attendance_data, path)
        return send_file(path, as_attachment=True, download_name=f'attendance_{timestamp}.xlsx')
    elif format_type == 'csv':
        path = f'reports/attendance_report_{timestamp}.csv'
        report_gen.generate_attendance_csv(attendance_data, path)
        return send_file(path, as_attachment=True, download_name=f'attendance_{timestamp}.csv')
    else:
        path = f'reports/attendance_report_{timestamp}.pdf'
        report_gen.generate_attendance_pdf(attendance_data, path)
        return send_file(path, as_attachment=True, download_name=f'attendance_{timestamp}.pdf')

@api_bp.route('/report/comprehensive', methods=['POST'])
@login_required
def api_comprehensive_report():
    data = request.get_json() or request.form
    faculty_id = data.get('faculty_id', '')
    subject = data.get('subject_name', '')
    from_date_str = data.get('from_date', '')
    to_date_str = data.get('to_date', '')
    query = Attendance.query
    if faculty_id:
        query = query.filter_by(faculty_id=faculty_id)
    if subject:
        query = query.filter_by(subject_name=subject)
    if from_date_str:
        query = query.filter(Attendance.date >= datetime.strptime(from_date_str, '%Y-%m-%d').date())
    if to_date_str:
        query = query.filter(Attendance.date <= datetime.strptime(to_date_str, '%Y-%m-%d').date())
    records = query.order_by(Attendance.date.desc()).all()
    attendance_data = [{'student_id': r.student_id, 'name': Student.query.get(r.student_id).name if Student.query.get(r.student_id) else '', 'date': r.date.isoformat() if r.date else '', 'status': r.status} for r in records]
    os.makedirs('reports', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = f'reports/comprehensive_report_{timestamp}.txt'
    report_gen.generate_comprehensive_report(attendance_data, path)
    return send_file(path, as_attachment=True, download_name=f'report_{timestamp}.txt')

@api_bp.route('/admin/leave/approve', methods=['POST'])
@login_required
def api_approve_leave():
    from routes.admin_routes import approve_leave
    data = request.get_json() or request.form
    leave_id = data.get('leave_id')
    if leave_id:
        from database.models import LeaveRequest
        leave = LeaveRequest.query.get(int(leave_id))
        if leave:
            from routes.admin_routes import approve_leave
            return approve_leave(leave.leave_id)
    return jsonify({'status': 'error', 'message': 'Leave not found'}), 404

@api_bp.route('/admin/leave/reject', methods=['POST'])
@login_required
def api_reject_leave():
    from routes.admin_routes import reject_leave
    data = request.get_json() or request.form
    leave_id = data.get('leave_id')
    if leave_id:
        from database.models import LeaveRequest
        leave = LeaveRequest.query.get(int(leave_id))
        if leave:
            return reject_leave(leave.leave_id)
    return jsonify({'status': 'error', 'message': 'Leave not found'}), 404

@api_bp.route('/register', methods=['POST'])
def api_register():
    from werkzeug.security import generate_password_hash
    from database.models import db, User
    data = request.get_json() or request.form
    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = data.get('email', '').strip()
    role = data.get('role', 'student')
    if User.query.filter_by(username=username).first():
        return jsonify({'status': 'error', 'message': 'User exists'}), 400
    user = User(username=username, password=generate_password_hash(password), email=email, role=role)
    db.session.add(user)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'User registered'})

@api_bp.route('/generate-embeddings', methods=['POST'])
@login_required
def api_generate_embeddings():
    return jsonify({'status': 'error', 'message': 'Embeddings generation is disabled (AI features unavailable)'}), 503

@api_bp.route('/attendance/summary', methods=['GET'])
@login_required
def api_attendance_summary():
    days = int(request.args.get('days', 30))
    since = date.today() - timedelta(days=days)
    records = Attendance.query.filter(Attendance.date >= since).all()
    total = len(records)
    present = sum(1 for r in records if r.status == 'Present')
    absent = sum(1 for r in records if r.status == 'Absent')
    late = sum(1 for r in records if r.status == 'Late')
    return jsonify({
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'attendance_rate': round(present / total * 100, 1) if total else 0
    })

@api_bp.route('/dashboard/stats', methods=['GET'])
@login_required
def api_dashboard_stats():
    today = date.today()
    total_students = Student.query.count()
    total_faculty = Faculty.query.count()
    today_attendance = Attendance.query.filter_by(date=today).count()
    active_sessions = __import__('database.models', fromlist=['AttendanceSession']).AttendanceSession.query.filter_by(status='active').count()
    pending_leaves = LeaveRequest.query.filter_by(status='Pending').count()
    return jsonify({
        'total_students': total_students,
        'total_faculty': total_faculty,
        'today_attendance': today_attendance,
        'active_sessions': active_sessions,
        'pending_leaves': pending_leaves
    })
