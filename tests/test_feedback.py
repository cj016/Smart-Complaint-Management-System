"""Feature-specific owner, role, state and audit tests."""
from datetime import timedelta

import pytest
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import AuditLog, Complaint, Feedback, Role, StatusHistory, User
from app.utils import utcnow


@pytest.fixture()
def records(app):
    users = []
    for i, role in enumerate([Role.COMPLAINANT, Role.COMPLAINANT, Role.ADMIN, Role.OFFICER]):
        user = User(name="Tester", email=f"u{i}@example.com", password_hash="x", role=role)
        db.session.add(user)
        users.append(user)
    db.session.flush()
    complaint = Complaint(public_id="SCMS-2026-00001", user_id=users[0].id,
                          category="Roads", location="Road", description="Pothole",
                          status="Resolved", resolved_at=utcnow(), resolution_remarks="Fixed",
                          sla_due_at=utcnow() - timedelta(days=1))
    db.session.add(complaint)
    db.session.commit()
    return users, complaint


def headers(user):
    return {"Authorization": "Bearer " + create_access_token(identity=str(user.id))}


def endpoint(action):
    return "/api/v1/tracking/by-id/SCMS-2026-00001/" + action


@pytest.mark.parametrize("action,payload", [("feedback", {"rating": 4})])
def test_owner_only(client, records, action, payload):
    users, _ = records
    assert client.post(endpoint(action), json=payload).status_code == 401
    for index, status in [(1, 404), (2, 403), (3, 403)]:
        assert client.post(endpoint(action), json=payload,
                           headers=headers(users[index])).status_code == status


@pytest.mark.parametrize("status", [
    "Submitted", "In Review", "Assigned", "In Progress", "Reopened"])
@pytest.mark.parametrize("action,payload", [("feedback", {"rating": 4})])
def test_wrong_state(client, records, status, action, payload):
    users, complaint = records
    complaint.status = status
    db.session.commit()
    assert client.post(endpoint(action), json=payload,
                       headers=headers(users[0])).status_code == 409
    assert db.session.scalar(db.select(db.func.count(Feedback.id))) == 0
    assert db.session.scalar(db.select(db.func.count(StatusHistory.id))) == 0


@pytest.mark.parametrize("action", ["feedback"])
def test_invalid_and_missing_id(client, records, action):
    users, _ = records
    for public_id, status in [("bad", 422), ("SCMS-2026-99999", 404)]:
        response = client.post(f"/api/v1/tracking/by-id/{public_id}/{action}",
                               json={"reason": "Unresolved", "rating": 4},
                               headers=headers(users[0]))
        assert response.status_code == status


@pytest.mark.parametrize("rating", [True, False, 0, 6, 3.5, "4", None])
def test_bad_rating(client, records, rating):
    users, _ = records
    assert client.post(endpoint("feedback"), json={"rating": rating},
                       headers=headers(users[0])).status_code == 422


@pytest.mark.parametrize("status", ["Resolved", "Closed"])
def test_feedback_and_duplicate(client, records, status):
    users, complaint = records
    complaint.status = status
    db.session.commit()
    assert client.get(endpoint("feedback"), headers=headers(users[0])).json == {"feedback": None}
    response = client.post(endpoint("feedback"), json={"rating": 5, "comment": "<b>Good</b>"},
                           headers=headers(users[0]))
    assert response.status_code == 201
    assert response.json["feedback"]["comment"] == "Good"
    saved = client.get(endpoint("feedback"), headers=headers(users[0])).json
    assert saved["feedback"]["rating"] == 5
    assert client.post(endpoint("feedback"), json={"rating": 2},
                       headers=headers(users[0])).status_code == 409
    assert db.session.scalar(db.select(db.func.count(Feedback.id))) == 1
    assert complaint.status == status


@pytest.mark.parametrize("comment", [None, [], 3, "x" * 2001])
def test_bad_comment(client, records, comment):
    users, _ = records
    assert client.post(endpoint("feedback"), json={"rating": 3, "comment": comment},
                       headers=headers(users[0])).status_code == 422


def test_owner_feedback_hidden_from_others(client, records):
    users, _ = records
    assert client.get(endpoint("feedback"), headers=headers(users[1])).status_code == 404


def test_feedback_has_audit_entry(client, records):
    from app.audit.services import verify_audit_chain

    users, complaint = records
    for expected in (201, 409):
        response = client.post(endpoint("feedback"), json={"rating": 4},
                               headers=headers(users[0]))
        assert response.status_code == expected
    entries = db.session.execute(db.select(AuditLog)).scalars().all()
    assert len(entries) == 1
    assert entries[0].action == "FEEDBACK_SUBMITTED"
    assert entries[0].entity_id == complaint.public_id
    assert verify_audit_chain()["valid"] is True


@pytest.fixture()
def admin(app):
    user = User(name="Admin", email="admin@example.com", password_hash="x", role=Role.ADMIN)
    db.session.add(user)
    db.session.commit()
    return user


def auth(user):
    return {"Authorization": "Bearer " + create_access_token(identity=str(user.id))}


def test_admin_feedback_visibility_pagination_and_dates(client, admin):
    from datetime import datetime
    from app.models import Feedback

    for i in range(2):
        complaint = Complaint(public_id=f"SCMS-2026-{i:05}", user_id=admin.id,
                              category="Roads", description="Issue", location="Road",
                              created_at=datetime(2026, 10, i + 1), status="Resolved")
        db.session.add(complaint)
        db.session.flush()
        db.session.add(Feedback(complaint_id=complaint.id, user_id=admin.id, rating=i + 3,
                                comment="Citizen comment"))
    db.session.commit()
    response = client.get("/api/v1/feedback/admin?per_page=1", headers=auth(admin))
    assert response.status_code == 200 and response.json["total"] == 2
    assert len(response.json["items"]) == 1 and response.json["pages"] == 2
    second = client.get("/api/v1/feedback/admin?per_page=1&page=2", headers=auth(admin))
    assert second.json["items"][0]["rating"] != response.json["items"][0]["rating"]
    filtered = client.get("/api/v1/feedback/admin?start_date=2026-10-02",
                          headers=auth(admin))
    assert filtered.json["total"] == 1 and filtered.json["items"][0]["rating"] == 4
    assert "user_id" not in filtered.json["items"][0]
    assert filtered.headers["Cache-Control"] == "no-store"
    assert client.get("/api/v1/feedback/admin").status_code == 401
    admin.role = Role.COMPLAINANT
    db.session.commit()
    assert client.get("/api/v1/feedback/admin", headers=auth(admin)).status_code == 403


@pytest.mark.parametrize("query", ["page=0", "page=bad", "per_page=0", "per_page=101"])
def test_feedback_pagination_validation(client, admin, query):
    assert client.get("/api/v1/feedback/admin?" + query, headers=auth(admin)).status_code == 422


def test_feedback_page(client):
    assert client.get("/feedback").status_code == 200
