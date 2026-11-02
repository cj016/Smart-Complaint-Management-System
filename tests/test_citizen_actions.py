"""TC-Track-05 / TC-Feedback-01: authorization, validation and state changes."""
from datetime import timedelta

import pytest
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import AuditLog, Complaint, Feedback, Notification, Role, StatusHistory, User
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


@pytest.mark.parametrize("action,payload", [
    ("reopen", {"reason": "Still broken"}), ("feedback", {"rating": 4})])
def test_owner_only(client, records, action, payload):
    users, _ = records
    assert client.post(endpoint(action), json=payload).status_code == 401
    for index, status in [(1, 404), (2, 403), (3, 403)]:
        assert client.post(endpoint(action), json=payload,
                           headers=headers(users[index])).status_code == status


@pytest.mark.parametrize("status", ["Resolved", "Closed"])
def test_reopen_and_timeline(client, records, status):
    users, complaint = records
    complaint.status = status
    db.session.commit()
    response = client.post(endpoint("reopen"), json={"reason": "<b>Still broken</b>"},
                           headers=headers(users[0]))
    assert response.status_code == 200
    assert response.json["status"] == "Reopened"
    db.session.refresh(complaint)
    assert complaint.resolved_at is None
    assert complaint.sla_due_at > utcnow()
    assert complaint.resolution_remarks == "Fixed"  # preserve previous resolution
    history = db.session.execute(db.select(StatusHistory)).scalars().all()
    assert len(history) == 1
    assert history[0].remarks == "Still broken"
    assert history[0].changed_by_id == users[0].id
    assert client.post(endpoint("reopen"), json={"reason": "Again"},
                       headers=headers(users[0])).status_code == 409
    assert db.session.scalar(db.select(db.func.count(StatusHistory.id))) == 1
    timeline = client.get(endpoint("timeline"), headers=headers(users[0]))
    assert timeline.json["steps"][-1]["status"] == "Reopened"


@pytest.mark.parametrize("status", [
    "Submitted", "In Review", "Assigned", "In Progress", "Reopened"])
@pytest.mark.parametrize("action,payload", [
    ("reopen", {"reason": "Unresolved"}), ("feedback", {"rating": 3})])
def test_wrong_state(client, records, status, action, payload):
    users, complaint = records
    complaint.status = status
    db.session.commit()
    assert client.post(endpoint(action), json=payload,
                       headers=headers(users[0])).status_code == 409
    assert db.session.scalar(db.select(db.func.count(Feedback.id))) == 0
    assert db.session.scalar(db.select(db.func.count(StatusHistory.id))) == 0


@pytest.mark.parametrize("payload", [{}, [], None, {"reason": 7}, {"reason": " "},
                                     {"reason": "x" * 2001}, {"reason": "<b></b>"}])
def test_bad_reason(client, records, payload):
    users, _ = records
    assert client.post(endpoint("reopen"), json=payload,
                       headers=headers(users[0])).status_code == 422


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


@pytest.mark.parametrize("action", ["reopen", "feedback"])
def test_invalid_and_missing_id(client, records, action):
    users, _ = records
    for public_id, status in [("bad", 422), ("SCMS-2026-99999", 404)]:
        response = client.post(f"/api/v1/tracking/by-id/{public_id}/{action}",
                               json={"reason": "Unresolved", "rating": 4},
                               headers=headers(users[0]))
        assert response.status_code == status


def test_owner_feedback_hidden_from_others(client, records):
    users, _ = records
    assert client.get(endpoint("feedback"), headers=headers(users[1])).status_code == 404


def test_feedback_preserved_after_reopen(client, records):
    users, _ = records
    client.post(endpoint("feedback"), json={"rating": 2}, headers=headers(users[0]))
    client.post(endpoint("reopen"), json={"reason": "Still broken"}, headers=headers(users[0]))
    saved = client.get(endpoint("feedback"), headers=headers(users[0])).json
    assert saved["feedback"]["rating"] == 2


def test_reopen_audit_and_notification_once(client, records):
    from app.audit.services import verify_audit_chain

    users, complaint = records
    complaint.assigned_to_id = users[3].id
    db.session.commit()
    for expected in (200, 409):
        response = client.post(endpoint("reopen"), json={"reason": "Still unresolved"},
                               headers=headers(users[0]))
        assert response.status_code == expected
    entries = db.session.execute(db.select(AuditLog)).scalars().all()
    assert len(entries) == 1
    assert entries[0].action == "COMPLAINT_REOPENED"
    assert entries[0].actor_id == users[0].id
    assert verify_audit_chain()["valid"] is True
    notifications = db.session.execute(db.select(Notification)).scalars().all()
    assert len(notifications) == 3
    assert {n.user_id for n in notifications} == {users[0].id, users[2].id, users[3].id}
    assert all(n.complaint_id == complaint.id for n in notifications)
    assert all("reopened" in n.message.lower() for n in notifications)


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
