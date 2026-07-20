"""Run this AFTER creating departments in the UI, then:
   python3 seed_data.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ['SECRET_KEY'] = 'seed'
os.environ['DATABASE_URL'] = 'sqlite:///smart_attendance.db'

from app import app, db
from database.models import Department, Faculty, Student, User, Subject, DepartmentSection
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    depts = Department.query.all()
    if not depts:
        print("No departments found. Create them in the UI first, then re-run.")
        sys.exit(1)

    # ── Faculty ──
    fac_data = [
        ("FAC001", "Dr. Arun Kumar", "arun@college.edu", "CS", "1,3,5,7"),
        ("FAC002", "Dr. Bhavana Rao", "bhavana@college.edu", "CS", "2,4,6,8"),
        ("FAC003", "Prof. Chetan Shetty", "chetan@college.edu", "IS", "1,3,5,7"),
        ("FAC004", "Dr. Divya Nair", "divya@college.edu", "IS", "2,4,6,8"),
        ("FAC005", "Prof. Eshwar Patil", "eshwar@college.edu", "ECE", "1,3,5,7"),
        ("FAC006", "Dr. Fathima Begum", "fathima@college.edu", "ECE", "2,4,6,8"),
        ("FAC007", "Prof. Ganesh Iyer", "ganesh@college.edu", "ME", "1,3,5"),
        ("FAC008", "Dr. Harini Krishnan", "harini@college.edu", "ME", "2,4,6"),
        ("FAC009", "Prof. Imran Khan", "imran@college.edu", "CV", "1,3,5"),
        ("FAC010", "Dr. Jyothi Sharma", "jyothi@college.edu", "CV", "2,4,6"),
    ]
    for fid, name, email, dept, sems in fac_data:
        if not Faculty.query.filter_by(faculty_id=fid).first():
            f = Faculty(faculty_id=fid, name=name, email=email,
                        department=dept, semesters_handled=sems, is_active=True)
            db.session.add(f)
        if not User.query.filter_by(username=fid).first():
            u = User(username=fid, password=generate_password_hash(fid + '@123'),
                     role='faculty', email=email)
            db.session.add(u)
    db.session.commit()
    print("✓ 10 faculty created")

    # ── Subjects ──
    theory_8sem = [
        "Mathematics", "Programming Fundamentals", "Data Structures",
        "Database Systems", "Operating Systems"
    ]
    lab_8sem = ["Programming Lab", "Database Lab", "Networking Lab"]
    theory_6sem = [
        "Mathematics", "Programming Fundamentals",
        "Database Systems", "Operating Systems", "Web Technologies"
    ]
    lab_6sem = ["Programming Lab", "Database Lab", "Web Lab"]

    for d in depts:
        is_8sem = d.name.upper() in ("BE", "BTECH")
        theory_list = theory_8sem if is_8sem else theory_6sem
        lab_list = lab_8sem if is_8sem else lab_6sem
        max_sem = 8 if is_8sem else 6

        for sem in range(1, max_sem + 1):
            for i, t in enumerate(theory_list):
                sid = f"{d.code.upper()}{sem:02d}{i+1:02d}"
                if not Subject.query.filter_by(subject_id=sid).first():
                    s = Subject(subject_id=sid, subject_name=t,
                                department=d.name, semester=str(sem),
                                section='A', is_lab=False,
                                hours_per_week=4, credits=4)
                    db.session.add(s)
            for i, lb in enumerate(lab_list):
                lid = f"{d.code.upper()}{sem:02d}L{i+1:02d}"
                if not Subject.query.filter_by(subject_id=lid).first():
                    ls = Subject(subject_id=lid, subject_name=lb,
                                 department=d.name, semester=str(sem),
                                 section='A', is_lab=True,
                                 hours_per_week=3, credits=2)
                    db.session.add(ls)
    db.session.commit()
    print(f"✓ Subjects created for {len(depts)} departments")

    # ── Sections (A, B) for odd semesters of each dept ──
    for d in depts:
        max_sem = 8 if d.name.upper() in ("BE", "BTECH") else 6
        for sem in range(1, max_sem + 1):
            for sec in ("A", "B"):
                if not DepartmentSection.query.filter_by(
                    department_name=d.name, semester=str(sem), section=sec).first():
                    ds = DepartmentSection(department_name=d.name,
                                           semester=str(sem), section=sec)
                    db.session.add(ds)
    db.session.commit()
    print("✓ Sections A, B created for all semesters")

    # ── Students (15 per dept, spread across semesters 1,3,5 for odd-start) ──
    count = 0
    for d in depts:
        max_sem = 8 if d.name.upper() in ("BE", "BTECH") else 6
        start_sems = [s for s in range(1, max_sem + 1) if s % 2 == 1]
        students_per_dept = 15
        sem_cycle = start_sems * (students_per_dept // len(start_sems) + 1)
        for idx in range(students_per_dept):
            sem = str(sem_cycle[idx])
            sec = "A" if idx % 2 == 0 else "B"
            sid = f"{d.code.upper()}{idx+1:03d}"
            usn = f"{d.code.upper()}{sem}{idx+1:03d}"
            name = f"Student {d.code} {idx+1}"
            if not Student.query.filter_by(student_id=sid).first():
                st = Student(student_id=sid, usn=usn, name=name,
                             department=d.name, semester=sem, section=sec,
                             email=f"{sid.lower()}@college.edu",
                             phone=f"987654{idx+1:04d}", is_active=True)
                db.session.add(st)
                count += 1
            if not User.query.filter_by(username=sid).first():
                u = User(username=sid,
                         password=generate_password_hash(sid + '@123'),
                         role='student', email=f"{sid.lower()}@college.edu")
                db.session.add(u)
    db.session.commit()
    print(f"✓ {count} students created across {len(depts)} departments")
    print("\nDone! Login credentials: username / username@123")
