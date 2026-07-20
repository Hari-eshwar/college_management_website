import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ['SECRET_KEY'] = 'seed'
os.environ['DATABASE_URL'] = 'sqlite:///smart_attendance.db'

from app import app, db
from database.models import Department, Faculty, User
from werkzeug.security import generate_password_hash

with app.app_context():
    depts = Department.query.all()
    print("Departments:", [(d.name, d.code) for d in depts])

    # Nuke old faculty & their user accounts via raw SQL to avoid ORM issues
    db.session.execute(db.text('DELETE FROM timetable'))
    for f in Faculty.query.all():
        db.session.execute(db.text('DELETE FROM "users" WHERE username = :uid'), {'uid': f.faculty_id})
        db.session.delete(f)
    db.session.commit()
    print("Cleared old faculty + users")

    fac_data = [
        # Odd-sem theory faculty
        ("FAC001", "Dr. Arun Kumar", "arun@college.edu", "Computer Science", "1,3,5"),
        ("FAC003", "Prof. Chetan Shetty", "chetan@college.edu", "Business Administration", "1,3,5"),
        ("FAC005", "Prof. Eshwar Patil", "eshwar@college.edu", "COmmerce", "1,3,5"),
        ("FAC007", "Prof. Ganesh Iyer", "ganesh@college.edu", "Engineering", "1,3,5,7"),
        ("FAC009", "Prof. Imran Khan", "imran@college.edu", "Technology and Science", "1,3,5,7"),
        # Even-sem theory faculty
        ("FAC002", "Dr. Bhavana Rao", "bhavana@college.edu", "Computer Science", "2,4,6"),
        ("FAC004", "Dr. Divya Nair", "divya@college.edu", "Business Administration", "2,4,6"),
        ("FAC006", "Dr. Fathima Begum", "fathima@college.edu", "COmmerce", "2,4,6"),
        ("FAC008", "Dr. Harini Krishnan", "harini@college.edu", "Engineering", "2,4,6,8"),
        ("FAC010", "Dr. Jyothi Sharma", "jyothi@college.edu", "Technology and Science", "2,4,6,8"),
        # Lab faculty — shared across all semesters
        ("FAC011", "Prof. Suresh Reddy", "suresh@college.edu", "Computer Science", "1,2,3,4,5,6"),
        ("FAC012", "Dr. Meena Iyer", "meena@college.edu", "Business Administration", "1,2,3,4,5,6"),
        ("FAC013", "Mr. Prakash Joshi", "prakash@college.edu", "COmmerce", "1,2,3,4,5,6"),
        ("FAC014", "Ms. Anita Desai", "anita@college.edu", "Engineering", "1,2,3,4,5,6,7,8"),
        ("FAC015", "Dr. Ravi Verma", "ravi@college.edu", "Technology and Science", "1,2,3,4,5,6,7,8"),
    ]
    for fid, name, email, dept, sems in fac_data:
        f = Faculty(faculty_id=fid, name=name, email=email,
                    department=dept, semesters_handled=sems, is_active=True)
        db.session.add(f)
        u = User(username=fid, password=generate_password_hash(fid + '@123'),
                 role='faculty', email=email)
        db.session.add(u)
    db.session.commit()
    print("✓ 10 faculty recreated with correct departments")

    print("\nFinal mapping:")
    for f in Faculty.query.order_by(Faculty.faculty_id).all():
        print(f"  {f.faculty_id} - {f.name:30s} Dept: {f.department:25s} Semesters: {f.semesters_handled}")
