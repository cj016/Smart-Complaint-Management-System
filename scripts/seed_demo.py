"""Create a demo citizen + sample complaints and print a login token (JWT).

Lets you try the My Complaints page and record the demo before the login page exists.
Run from the repo root with the venv active:   python scripts/seed_demo.py
Safe to run more than once (it adds 5 more complaints each time).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from flask_jwt_extended import create_access_token  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Complaint, User  # noqa: E402

CATEGORIES = ["Sanitation", "Roads", "Water Supply", "Street Lighting", "Noise"]
STATUSES = ["Submitted", "In Review", "Assigned", "In Progress", "Resolved"]

app = create_app()
with app.app_context():
    user = User.query.filter_by(email="demo@example.com").first()
    if user is None:
        user = User(name="Demo Citizen", email="demo@example.com", is_verified=True,
                    password_hash="demo-not-a-real-hash")
        db.session.add(user)
        db.session.commit()

    start = Complaint.query.filter(Complaint.public_id.like("SCMS-2026-9%")).count() + 1
    for offset in range(5):
        n = start + offset
        db.session.add(Complaint(
            public_id=f"SCMS-2026-9{n:04d}", user_id=user.id,
            category=CATEGORIES[offset], status=STATUSES[offset],
            description="Demo complaint", location=f"Demo Street {n}"))
    db.session.commit()

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    print("\nDemo complaints added for demo@example.com.")
    print("Open http://127.0.0.1:5000/my-complaints, press F12, and in the Console run:\n")
    print(f'localStorage.setItem("scms_token", "{token}")\n')
    print("Then reload the page. (The token is valid for 1 hour.)")
