"""Create demo admin + officers + sample complaints and print login tokens (JWT).

Lets you try the admin dashboard and record the demo before the login page exists.
Run from the repo root with the venv active:   python scripts/seed_staff.py
Safe to run more than once (staff accounts are reused; it adds 8 more complaints each time).
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

PASSWORD = "Staff@12345"
STAFF = [
    ("Admin User", "admin@example.com", Role.ADMIN, "Administration"),
    ("Ravi Officer", "officer1@example.com", Role.OFFICER, "Roads"),
    ("Sneha Officer", "officer2@example.com", Role.OFFICER, "Sanitation"),
]
SAMPLES = [
    ("Sanitation", "High", "Overflowing garbage bin on 5th Cross Road"),
    ("Roads", "Critical", "Large pothole near the bus stand"),
    ("Water Supply", "Medium", "No water supply since morning"),
    ("Street Lighting", "Low", "Street light flickering on 2nd Main"),
    ("Noise", "Low", "Loud music late at night"),
    ("Roads", "Medium", "Broken footpath outside the school"),
    ("Sanitation", "Critical", "Open drain overflowing onto the road"),
    ("Water Supply", "High", "Pipe leak flooding the lane"),
]


def get_or_create(name, email, role, department):
    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(name=name, email=email, role=role, department=department,
                    is_verified=True)
        user.set_password(PASSWORD)
        db.session.add(user)
        db.session.commit()
    return user


def token_for(user):
    return create_access_token(identity=str(user.id), additional_claims={"role": user.role})


app = create_app()
with app.app_context():
    users = {email: get_or_create(name, email, role, dept) for name, email, role, dept in STAFF}
    citizen = User.query.filter_by(email="demo@example.com").first()
    if citizen is None:
        citizen = User(name="Demo Citizen", email="demo@example.com", is_verified=True,
                       password_hash="demo-not-a-real-hash")
        db.session.add(citizen)
        db.session.commit()

    year = utcnow().year
    start = Complaint.query.filter(Complaint.public_id.like(f"SCMS-{year}-9%")).count() + 1
    for offset, (category, priority, description) in enumerate(SAMPLES):
        n = start + offset
        complaint = Complaint(
            public_id=f"SCMS-{year}-9{n:04d}", user_id=citizen.id, category=category,
            priority=priority, description=description, location=f"Demo Street {n}",
            status="Submitted")
        complaint.history.append(StatusHistory(status="Submitted", changed_by_id=citizen.id))
        db.session.add(complaint)
    db.session.commit()

    print(f"\nStaff accounts (password for all: {PASSWORD}):")
    for _, email, role, _ in STAFF:
        print(f"  {role:8s} {email}")
    print("\nOpen http://127.0.0.1:5000/admin, press Option+Cmd+J (Chrome) and paste ONE line.")
    print("\nAs ADMIN (can assign + update status):\n")
    print(f'localStorage.setItem("scms_token", "{token_for(users["admin@example.com"])}")\n')
    print("As OFFICER (can only update complaints assigned to them):\n")
    print(f'localStorage.setItem("scms_token", "{token_for(users["officer1@example.com"])}")\n')
    print("As the demo CITIZEN (for the status timeline on /track):\n")
    print(f'localStorage.setItem("scms_token", "{token_for(citizen)}")\n')
    print("Then reload the page. (Tokens are valid for 1 hour.)")
