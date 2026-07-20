from flask import render_template, request, redirect, url_for, jsonify, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from database.models import db, User
from . import auth_bp
from datetime import datetime, timezone

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'faculty':
                return redirect(url_for('faculty.dashboard'))
            else:
                return redirect(url_for('student.portal'))
        flash('Invalid username or password', 'danger')
        return render_template('login.html')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or request.form
    username = data.get('username', '').strip()
    password = data.get('password', '')
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        login_user(user)
        return jsonify({'status': 'success', 'role': user.role, 'user_id': user.id})
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
