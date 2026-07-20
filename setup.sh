#!/usr/bin/env bash
set -euo pipefail

echo "=== Smart Attendance System Setup ==="

# 1. Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "[OK] Virtual environment created"
fi

source venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
echo "[OK] Dependencies installed"

# 3. Copy .env if not exists
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[WARN] .env created from .env.example — edit it with your real credentials"
else
    echo "[OK] .env already exists"
fi

# 4. Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('[OK] Database initialized')"

# 5. Seed default admin
python -c "
from app import app, db
from database.models import User
from werkzeug.security import generate_password_hash
app.app_context().push()
if not User.query.filter_by(username='admin').first():
    admin = User(username='admin', password=generate_password_hash('admin@123'), role='admin', email='admin@example.com')
    db.session.add(admin)
    db.session.commit()
    print('[OK] Default admin created (admin / admin@123)')
else:
    print('[OK] Admin already exists')
"

echo ""
echo "=== Setup complete! ==="
echo "Run: source venv/bin/activate && flask run"
