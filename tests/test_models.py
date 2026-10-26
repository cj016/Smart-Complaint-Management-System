import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Complaint, ComplaintPhoto, Feedback, StatusHistory, User


def make_user(email="citizen@example.com"):
    user = User(name="Test Citizen", email=email, password_hash="x")
    db.session.add(user)
    db.session.commit()
    return user


def make_complaint(user, public_id="SCMS-2026-00001"):
    c = Complaint(public_id=public_id, user_id=user.id, category="Sanitation",
                  description="Overflowing bin", location="5th Cross Road")
    db.session.add(c)
    db.session.commit()
    return c


def test_user_defaults(app):
    user = make_user()
    assert user.role == "Complainant"
    assert user.is_verified is False
    assert user.failed_login_count == 0


def test_complaint_defaults_and_relations(app):
    user = make_user()
    c = make_complaint(user)
    assert c.status == "Submitted"
    assert c.priority == "Medium"
    assert c.complainant.email == "citizen@example.com"
    db.session.add_all([
        ComplaintPhoto(complaint_id=c.id, filename="a.jpg", size_bytes=100),
        StatusHistory(complaint_id=c.id, status="Submitted", changed_by_id=user.id),
    ])
    db.session.commit()
    assert len(c.photos) == 1
    assert c.history[0].status == "Submitted"


def test_public_id_must_be_unique(app):
    user = make_user()
    make_complaint(user, "SCMS-2026-00001")
    with pytest.raises(IntegrityError):
        make_complaint(user, "SCMS-2026-00001")


def test_feedback_rating_constraint(app):
    user = make_user()
    c = make_complaint(user)
    db.session.add(Feedback(complaint_id=c.id, user_id=user.id, rating=9))
    with pytest.raises(IntegrityError):
        db.session.commit()
