"""Create a demo admin, two officers, a citizen and sample complaints for the admin dashboard.

Run from the repo root with the venv active:   python scripts/seed_admin_demo.py
Safe to run more than once: users and complaints are only created if missing.
Prints admin and officer tokens (JWT) to paste into the browser, because the login page
(SCMS-F-002) is another teammate's item.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from flask_jwt_extended import create_access_token  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Complaint, Role, StatusHistory, User  # noqa: E402
from app.utils import utcnow  # noqa: E402

PASSWORD = "Demo@12345"

USERS = [
    ("admin@scms.test", "Demo Admin", Role.ADMIN, None),
    ("officer1@scms.test", "Ravi Officer", Role.OFFICER, "Sanitation Dept"),
    ("officer2@scms.test", "Meena Officer", Role.OFFICER, "Roads Dept"),
    ("citizen@scms.test", "Demo Citizen", Role.COMPLAINANT, None),
]

LIFECYCLE = ["Submitted", "In Review", "Assigned", "In Progress", "Resolved", "Closed"]

# (category, priority, status, officer email or None, location)
COMPLAINTS = [
    ("Sanitation", "High", "Submitted", None, "5th Cross Road"),
    ("Roads", "Critical", "Submitted", None, "MG Road Junction"),
    ("Water Supply", "Medium", "In Review", None, "Lake View Colony"),
    ("Street Lighting", "Low", "Assigned", "officer1@scms.test", "Park Avenue"),
    ("Roads", "High", "In Progress", "officer2@scms.test", "Ring Road, Sector 4"),
    ("Noise", "Medium", "Resolved", "officer1@scms.test", "Market Street"),
    ("Sanitation", "Critical", "Assigned", "officer1@scms.test", "Station Road"),
    ("Other", "Low", "Closed", "officer2@scms.test", "Old Town Square"),
]

app = create_app()
with app.app_context():
    people = {}
    for email, name, role, department in USERS:
        user = User.query.filter_by(email=email).first()
        if user is None:
            user = User(name=name, email=email, role=role, department=department,
                        is_verified=True)
            user.set_password(PASSWORD)
            db.session.add(user)
            db.session.commit()
        people[email] = user

    citizen = people["citizen@scms.test"]
    year = utcnow().year
    # 95NNN stays inside the demo ID range (never used for real complaints)
    for n, (category, priority, status, officer_email, location) in enumerate(COMPLAINTS, 1):
        public_id = f"SCMS-{year}-95{n:03d}"
        if Complaint.query.filter_by(public_id=public_id).first():
            continue
        officer = people.get(officer_email)
        complaint = Complaint(
            public_id=public_id, user_id=citizen.id, category=category, priority=priority,
            status=status, location=location, description=f"Demo {category} complaint",
            assigned_to_id=officer.id if officer else None,
            department=officer.department if officer else None)
        # one timeline entry per lifecycle step up to the current status (F-022 demo)
        for step in LIFECYCLE[:LIFECYCLE.index(status) + 1]:
            actor = citizen if step == "Submitted" else people["admin@scms.test"]
            complaint.history.append(StatusHistory(
                status=step, changed_by_id=actor.id,
                remarks="Fixed and verified on site." if step == "Resolved" else None))
        if status in ("Resolved", "Closed"):
            complaint.resolution_remarks = "Fixed and verified on site."
            complaint.resolved_at = utcnow()
        db.session.add(complaint)
    db.session.commit()

    def token_for(email):
        user = people[email]
        return create_access_token(identity=str(user.id),
                                   additional_claims={"role": user.role})

    print("\nDemo data ready. All demo accounts use password:", PASSWORD)
    print("Open http://127.0.0.1:5000/admin, press F12 (or Option+Cmd+I), and in the Console")
    print("run ONE of these, then reload the page. Tokens are valid for 1 hour.\n")
    print("ADMIN (can assign):")
    print(f'localStorage.setItem("scms_token", "{token_for("admin@scms.test")}")\n')
    print("OFFICER (cannot assign, can update own complaints):")
    print(f'localStorage.setItem("scms_token", "{token_for("officer1@scms.test")}")\n')
    print("CITIZEN (for the timeline on /track):")
    print(f'localStorage.setItem("scms_token", "{token_for("citizen@scms.test")}")\n')
