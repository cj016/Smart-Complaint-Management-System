"""Test case TC-Lodge-02 (SCMS-F-011): auto-generate a unique Complaint ID."""
import re

from app.complaints.services import generate_complaint_id
from app.extensions import db
from app.models import Complaint, User

ID_FORMAT = re.compile(r"^SCMS-\d{4}-\d{5}$")


def make_user():
    user = User(name="Test", email="t@example.com", password_hash="x")
    db.session.add(user)
    db.session.commit()
    return user


def add_complaint(user, public_id):
    db.session.add(Complaint(public_id=public_id, user_id=user.id, category="Roads",
                             description="Pothole", location="Main St"))
    db.session.commit()


def test_first_id_of_the_year_is_00001(app):
    assert generate_complaint_id(2026) == "SCMS-2026-00001"


def test_id_matches_required_format(app):
    assert ID_FORMAT.match(generate_complaint_id())


def test_ids_increase_and_are_unique(app):
    user = make_user()
    seen = set()
    for _ in range(5):
        new_id = generate_complaint_id(2026)
        assert new_id not in seen
        seen.add(new_id)
        add_complaint(user, new_id)
    assert sorted(seen) == [f"SCMS-2026-{n:05d}" for n in range(1, 6)]


def test_counter_restarts_each_year(app):
    user = make_user()
    add_complaint(user, "SCMS-2026-00007")
    assert generate_complaint_id(2026) == "SCMS-2026-00008"
    assert generate_complaint_id(2027) == "SCMS-2027-00001"


def test_demo_seed_ids_are_ignored(app):
    user = make_user()
    add_complaint(user, "SCMS-2026-00003")
    add_complaint(user, "SCMS-2026-90001")  # created by scripts/seed_demo.py
    assert generate_complaint_id(2026) == "SCMS-2026-00004"
