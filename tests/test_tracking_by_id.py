"""Test case TC-Track-01 (SCMS-F-020): track complaint status by Complaint ID."""
import pytest
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import Complaint, Role, User


def make_user(email, role=Role.COMPLAINANT):
    user = User(name=email.split("@")[0], email=email, password_hash="x", role=role)
    db.session.add(user)
    db.session.commit()
    return user


def make_complaint(user, public_id="SCMS-2026-00042", status="In Progress"):
    c = Complaint(public_id=public_id, user_id=user.id, category="Sanitation",
                  description="Overflowing bin", location="5th Cross Road",
                  status=status, department="Sanitation Dept")
    db.session.add(c)
    db.session.commit()
    return c


def auth(user):
    return {"Authorization": f"Bearer {create_access_token(identity=str(user.id))}"}


def get(client, complaint_id, user):
    return client.get(f"/api/v1/tracking/by-id/{complaint_id}", headers=auth(user))


@pytest.fixture()
def citizens(app):
    return make_user("a@example.com"), make_user("b@example.com")


def test_requires_login(client):
    resp = client.get("/api/v1/tracking/by-id/SCMS-2026-00042")
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_owner_sees_status_and_details(client, citizens):
    a, _ = citizens
    make_complaint(a)
    resp = get(client, "SCMS-2026-00042", a)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["complaintId"] == "SCMS-2026-00042"
    assert body["status"] == "In Progress"
    assert body["description"] == "Overflowing bin"
    assert body["department"] == "Sanitation Dept"


def test_id_is_case_and_space_insensitive(client, citizens):
    a, _ = citizens
    make_complaint(a)
    assert get(client, "scms-2026-00042", a).status_code == 200


def test_unknown_id_returns_404(client, citizens):
    resp = get(client, "SCMS-2026-99999", citizens[0])
    assert resp.status_code == 404
    assert resp.get_json()["error"]["code"] == "NOT_FOUND"


def test_other_citizens_complaint_looks_like_404(client, citizens):
    a, b = citizens
    make_complaint(a)
    resp = get(client, "SCMS-2026-00042", b)
    assert resp.status_code == 404  # same as unknown, so IDs cannot be probed


@pytest.mark.parametrize("role", [Role.OFFICER, Role.ADMIN])
def test_staff_can_see_any_complaint(client, citizens, role):
    make_complaint(citizens[0])
    staff = make_user("staff@example.com", role)
    assert get(client, "SCMS-2026-00042", staff).status_code == 200


@pytest.mark.parametrize("bad", ["12345", "SCMS-26-1", "SCMS-2026-ABCDE", "DROP-TABLE"])
def test_bad_format_is_422(client, citizens, bad):
    resp = get(client, bad, citizens[0])
    assert resp.status_code == 422
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_track_page_renders(client):
    resp = client.get("/track")
    assert resp.status_code == 200
    assert b'name="viewport"' in resp.data
