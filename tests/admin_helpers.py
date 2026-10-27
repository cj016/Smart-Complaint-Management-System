"""Small helpers shared by the admin / timeline tests."""
from datetime import timedelta

from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import Complaint, Role, StatusHistory, User
from app.utils import utcnow


def make_user(email, role=Role.COMPLAINANT, name=None, department=None):
    user = User(name=name or email.split("@")[0], email=email, password_hash="x",
                role=role, department=department, is_verified=True)
    db.session.add(user)
    db.session.commit()
    return user


def make_complaint(owner, n=1, status="Submitted", priority="Medium", category="Roads",
                   assignee=None, **extra):
    """n makes the Complaint ID and the created_at time unique (higher n = newer)."""
    complaint = Complaint(
        public_id=f"SCMS-2026-{n:05d}", user_id=owner.id, category=category,
        description="Test complaint", location="Main St", status=status, priority=priority,
        assigned_to_id=assignee.id if assignee else None,
        created_at=utcnow() + timedelta(minutes=n), **extra)
    complaint.history.append(StatusHistory(
           status="Submitted", changed_by_id=owner.id,
           changed_at=utcnow() - timedelta(hours=1)))
    db.session.add(complaint)
    db.session.commit()
    return complaint


def auth(user):
    return {"Authorization": f"Bearer {create_access_token(identity=str(user.id))}"}


def reload(public_id):
    """Fresh copy from the database (the API call used a different session)."""
    db.session.expire_all()
    return db.session.execute(
        db.select(Complaint).where(Complaint.public_id == public_id)).scalar_one()
