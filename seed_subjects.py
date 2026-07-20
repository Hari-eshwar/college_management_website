import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ['SECRET_KEY'] = 'seed'
os.environ['DATABASE_URL'] = 'sqlite:///smart_attendance.db'

from app import app, db
from database.models import Subject, Department

with app.app_context():
    dept_map = {d.name: d.code.upper() for d in Department.query.all()}

# Dept → (theory list, lab list, max_sem)
SUBJECTS = {
    "Computer Science": (
        ["Programming in C", "Data Structures", "Database Systems", "Operating Systems", "Computer Networks"],
        ["C Programming Lab", "Data Structures Lab", "Web Development Lab"],
        6,
    ),
    "Business Administration": (
        ["Principles of Management", "Marketing Management", "Financial Accounting", "Business Economics", "Organizational Behavior"],
        ["Computer Applications Lab", "Business Analytics Lab", "Communication Lab"],
        6,
    ),
    "COmmerce": (
        ["Financial Accounting", "Cost Accounting", "Business Statistics", "Income Tax", "Auditing"],
        ["Tally Lab", "Accounting Software Lab", "Business Research Lab"],
        6,
    ),
    "Engineering": (
        ["Engineering Mathematics", "Engineering Physics", "Engineering Mechanics", "Basic Electronics", "Programming for Engineers"],
        ["Physics Lab", "Electronics Lab", "Engineering Drawing Lab"],
        8,
    ),
    "Technology and Science": (
        ["Discrete Mathematics", "Data Structures & Algorithms", "Database Management Systems", "Operating Systems", "Computer Networks"],
        ["Programming Lab", "Database Lab", "Networking Lab"],
        8,
    ),
}

with app.app_context():
    db.session.execute(db.text('DELETE FROM timetable'))
    Subject.query.delete()
    db.session.commit()
    print("Cleared old subjects + timetable")

    for dept_name, (theory, lab, max_sem) in SUBJECTS.items():
        code = dept_map.get(dept_name, dept_name[:3].upper())
        for sem in range(1, max_sem + 1):
            for i, t in enumerate(theory):
                sid = f"{code}{sem:02d}{i+1:02d}"
                s = Subject(subject_id=sid, subject_name=t,
                            department=dept_name, semester=str(sem),
                            section='A', is_lab=False,
                            hours_per_week=4, credits=4)
                db.session.add(s)
            for i, lb in enumerate(lab):
                lid = f"{code}{sem:02d}L{i+1:02d}"
                ls = Subject(subject_id=lid, subject_name=lb,
                             department=dept_name, semester=str(sem),
                             section='A', is_lab=True,
                             hours_per_week=3, credits=2)
                db.session.add(ls)
    db.session.commit()

    print("\nSubjects per department:")
    for dept_name in SUBJECTS:
        names = sorted(set(s.subject_name for s in Subject.query.filter_by(department=dept_name).all()))
        count = Subject.query.filter_by(department=dept_name).count()
        print(f"  {dept_name}: {', '.join(names)} ({count} total)")
    print(f"\nGrand total: {Subject.query.count()} subjects")
