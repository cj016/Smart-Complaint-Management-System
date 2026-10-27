"""Test case TC-Track-03 (SCMS-F-022): view the complaint status timeline."""
import pytest
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import Complaint, Role, StatusHistory, User

CID = "SCMS-2026-00042"
URL = f"/api/v1/tracking/by-id/{CID}/timeline"


def make_user(email, role=Role.COMPLAINANT):
    user = User(name=email.split("@")[0], email=email, password_hash="x", role=role,
                is_verified=True)
    db.session.add(user)
    db.session.commit()
    return user


def auth(user):
    return {"Authorization": f"Bearer {create_access_token(identity=str(user.id))}"}


def make_complaint(owner, steps=()):
    c = Complaint(public_id=CID, user_id=owner.id, category="Sanitation",
                  description="Overflowing bin", location="5th Cross Road",
                  status=steps[-1][0] if steps else "Submitted")
    for status, remarks in steps:
        c.history.append(StatusHistory(status=status, remarks=remarks))
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture()
def citizens(app):
    return make_user("a@example.com"), make_user("b@example.com")


def test_requires_login(client):
    resp = client.get(URL)
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_owner_sees_steps_oldest_first(client, citizens):
    a, _ = citizens
    make_complaint(a, [("Submitted", None), ("In Review", "Looking into it"),
                       ("Resolved", "Cleaned up")])
    resp = client.get(URL, headers=auth(a))
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["complaintId"] == CID
    assert body["currentStatus"] == "Resolved"
    assert [s["status"] for s in body["steps"]] == ["Submitted", "In Review", "Resolved"]
    assert body["steps"][1]["remarks"] == "Looking into it"
    assert body["steps"][0]["changedAt"].endswith("Z")


def test_id_is_case_insensitive(client, citizens):
    a, _ = citizens
    make_complaint(a, [("Submitted", None)])
    resp = client.get(URL.lower(), headers=auth(a))
    assert resp.status_code == 200


def test_other_citizen_gets_404(client, citizens):
    a, b = citizens
    make_complaint(a, [("Submitted", None)])
    assert client.get(URL, headers=auth(b)).status_code == 404


@pytest.mark.parametrize("role", [Role.OFFICER, Role.ADMIN])
def test_staff_can_see_any_timeline(client, citizens, role):
    make_complaint(citizens[0], [("Submitted", None)])
    staff = make_user("staff@example.com", role)
    assert client.get(URL, headers=auth(staff)).status_code == 200


def test_unknown_id_is_404(client, citizens):
    resp = client.get("/api/v1/tracking/by-id/SCMS-2026-99999/timeline",
                      headers=auth(citizens[0]))
    assert resp.status_code == 404


@pytest.mark.parametrize("bad", ["12345", "SCMS-26-1", "DROP-TABLE"])
def test_bad_format_is_422(client, citizens, bad):
    resp = client.get(f"/api/v1/tracking/by-id/{bad}/timeline", headers=auth(citizens[0]))
    assert resp.status_code == 422


def test_complaint_without_history_still_shows_current_status(client, citizens):
    a, _ = citizens
    make_complaint(a)  # no history rows, e.g. created by scripts/seed_demo.py
    body = client.get(URL, headers=auth(a)).get_json()
    assert [s["status"] for s in body["steps"]] == ["Submitted"]


def test_timeline_grows_when_admin_updates_status(client, citizens):
    a, _ = citizens
    make_complaint(a, [("Submitted", None)])
    admin = make_user("admin@example.com", Role.ADMIN)
    resp = client.post(f"/api/v1/admin/complaints/{CID}/status",
                       json={"status": "In Review", "remarks": "On it"}, headers=auth(admin))
    assert resp.status_code == 200
    steps = client.get(URL, headers=auth(a)).get_json()["steps"]
    assert [s["status"] for s in steps] == ["Submitted", "In Review"]
    assert steps[-1]["remarks"] == "On it"


def test_track_page_has_timeline_list(client):
    resp = client.get("/track")
    assert b'id="timeline"' in resp.data
