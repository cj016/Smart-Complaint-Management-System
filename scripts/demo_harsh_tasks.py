"""Run ONLY harsh-157-ctrl's feature demo with disposable in-memory data.

Run from the project root: python scripts/demo_harsh_tasks.py
This does not read .env or access your normal database. Stop with Ctrl+C.
"""
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Local-only demo process, never deployment configuration.
os.environ["FORCE_HTTPS"] = "false"

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Complaint, Role, StatusHistory, User  # noqa: E402
from app.utils import utcnow  # noqa: E402

DEMO_PASSWORD = "SCMS-Demo-2026!"


def build_demo():
    app = create_app("testing")
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"
    app.config.update(TESTING=False, DEBUG=False)
    with app.app_context():
        db.create_all()
        people = {}
        for name, email, role in [
            ("Harsh Demo Citizen", "citizen@scms.example", Role.COMPLAINANT),
            ("Second Demo Citizen", "other@scms.example", Role.COMPLAINANT),
            ("Demo Admin", "admin@scms.example", Role.ADMIN),
        ]:
            user = User(name=name, email=email, role=role, is_verified=True)
            user.set_password(DEMO_PASSWORD)
            db.session.add(user)
            people[email] = user
        db.session.flush()
        for public_id, status, category, department, email in [
            ("SCMS-2026-00001", "Resolved", "Roads", "Public Works", "citizen@scms.example"),
            ("SCMS-2026-00002", "Closed", "Water Supply", "Utilities", "citizen@scms.example"),
            ("SCMS-2026-00003", "In Progress", "Roads", "Public Works", "citizen@scms.example"),
            ("SCMS-2026-00004", "Resolved", "Sanitation", None, "other@scms.example"),
        ]:
            complaint = Complaint(
                public_id=public_id, user_id=people[email].id, status=status,
                category=category, department=department, location="Demo Street",
                description="Disposable feature demonstration complaint",
                resolved_at=utcnow() if status in ("Resolved", "Closed") else None)
            complaint.history.append(StatusHistory(status="Submitted", remarks="Demo created"))
            if status != "Submitted":
                complaint.history.append(StatusHistory(status=status, remarks="Demo status"))
            db.session.add(complaint)
        db.session.commit()
    return app


if __name__ == "__main__":
    demo = build_demo()
    print("\nDEMO ONLY: http://127.0.0.1:5001/login")
    print("Citizen: citizen@scms.example")
    print("Other citizen: other@scms.example")
    print("Admin: admin@scms.example")
    print("All demo passwords: " + DEMO_PASSWORD)
    print("Resolved: SCMS-2026-00001; Closed: SCMS-2026-00002")
    print("In Progress: SCMS-2026-00003; belongs to other citizen: SCMS-2026-00004")
    print("In-memory data disappears on exit. Your normal database is untouched.\n")
    demo.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)
