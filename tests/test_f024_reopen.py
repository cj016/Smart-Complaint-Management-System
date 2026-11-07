"""SCMS-F024: ownership, status transition, history, staff notification and UI."""
import pytest

from app.audit.services import verify_audit_chain
from app.extensions import db
from app.models import AuditLog, Notification, Role
from tests.admin_helpers import auth, make_complaint, make_user, reload

URL = "/api/v1/complaints/SCMS-2026-00001/reopen"


@pytest.fixture()
def people(app):
    return {
        "citizen": make_user("f024-citizen@example.com"),
        "stranger": make_user("f024-stranger@example.com"),
        "officer": make_user("f024-officer@example.com", Role.OFFICER),
        "admin": make_user("f024-admin@example.com", Role.ADMIN),
    }


def reopen(client, actor, reason="Still broken", url=URL):
    return client.post(url, headers=auth(actor), json={"reason": reason})


@pytest.mark.parametrize("original", ["Resolved", "Closed"])
def test_owner_reopens_and_notifies_staff(client, app, people, original):
    with app.app_context():
        complaint = make_complaint(
            people["citizen"], status=original, assignee=people["officer"]
        )
        response = reopen(client, people["citizen"], "  The issue remains  ")
        assert response.status_code == 200
        assert response.get_json()["status"] == "Reopened"
        updated = reload(complaint.public_id)
        assert updated.status == "Reopened"
        assert updated.history[-1].status == "Reopened"
        assert updated.history[-1].remarks == "The issue remains"
        assert updated.history[-1].changed_by_id == people["citizen"].id

        notifications = db.session.scalars(
            db.select(Notification).where(Notification.complaint_id == complaint.id,
                                          Notification.channel == "in_app")
        ).all()
        assert {n.user_id for n in notifications} == {
            people["officer"].id, people["admin"].id
        }
        assert all("reopened" in n.message.lower() for n in notifications)
        entry = db.session.scalar(db.select(AuditLog))
        assert entry.action == "COMPLAINT_REOPENED"
        assert entry.actor_id == people["citizen"].id
        assert verify_audit_chain()["valid"] is True

        timeline = client.get(
            "/api/v1/tracking/by-id/" + complaint.public_id + "/timeline",
            headers=auth(people["citizen"]),
        )
        assert timeline.status_code == 200
        assert timeline.get_json()["steps"][-1]["remarks"] == "The issue remains"


def test_unassigned_complaint_notifies_admin(client, app, people):
    with app.app_context():
        complaint = make_complaint(people["citizen"], status="Closed")
        assert reopen(client, people["citizen"]).status_code == 200
        notified = db.session.scalars(db.select(Notification).where(
            Notification.complaint_id == complaint.id,
            Notification.channel == "in_app",
        )).all()
        assert [n.user_id for n in notified] == [people["admin"].id]


def test_requires_login(client):
    assert client.post(URL, json={"reason": "Not fixed"}).status_code == 401


@pytest.mark.parametrize("role", ["officer", "admin"])
def test_staff_cannot_reopen(client, app, people, role):
    with app.app_context():
        make_complaint(people["citizen"], status="Resolved")
        assert reopen(client, people[role]).status_code == 403


def test_other_citizen_gets_404(client, app, people):
    with app.app_context():
        make_complaint(people["citizen"], status="Resolved")
        assert reopen(client, people["stranger"]).status_code == 404
        assert reopen(client, people["citizen"], url=(
            "/api/v1/complaints/SCMS-2026-09999/reopen"
        )).status_code == 404


@pytest.mark.parametrize("state", ["Submitted", "Assigned", "In Progress", "Reopened"])
def test_wrong_status_rejected(client, app, people, state):
    with app.app_context():
        make_complaint(people["citizen"], status=state)
        resp = reopen(client, people["citizen"])
        assert resp.status_code == 409
        assert reload("SCMS-2026-00001").status == state
        assert db.session.scalar(db.select(db.func.count(AuditLog.id))) == 0


def test_duplicate_attempt_rejected(client, app, people):
    with app.app_context():
        complaint = make_complaint(people["citizen"], status="Resolved")
        assert reopen(client, people["citizen"]).status_code == 200
        assert reopen(client, people["citizen"]).status_code == 409
        assert len(reload(complaint.public_id).history) == 2
        assert db.session.scalar(db.select(db.func.count(AuditLog.id))) == 1


@pytest.mark.parametrize("reason", ["", "  ", None, 123, [], "x" * 2001])
def test_invalid_reason_rejected(client, app, people, reason):
    with app.app_context():
        make_complaint(people["citizen"], status="Resolved")
        response = reopen(client, people["citizen"], reason)
        assert response.status_code == 422
        assert reload("SCMS-2026-00001").status == "Resolved"


def test_non_object_json_rejected(client, app, people):
    with app.app_context():
        make_complaint(people["citizen"], status="Resolved")
        resp = client.post(URL, headers=auth(people["citizen"]), json=["reason"])
        assert resp.status_code == 422


def test_staff_notifications_are_private(client, app, people):
    with app.app_context():
        make_complaint(people["citizen"], status="Resolved",
                       assignee=people["officer"])
        assert reopen(client, people["citizen"]).status_code == 200
        assert client.get("/api/v1/notifications/staff",
                          headers=auth(people["citizen"])).status_code == 403
        officer_inbox = client.get(
            "/api/v1/notifications/staff",
            headers=auth(people["officer"]),
        )
        assert officer_inbox.status_code == 200
        item = officer_inbox.get_json()["items"][0]
        assert officer_inbox.get_json()["unreadCount"] == 1
        assert client.patch("/api/v1/notifications/staff/" + str(item["id"]) + "/read",
                            headers=auth(people["admin"])).status_code == 404
        assert client.patch("/api/v1/notifications/staff/" + str(item["id"]) + "/read",
                            headers=auth(people["officer"])).status_code == 200
        assert client.get("/api/v1/notifications/staff",
                          headers=auth(people["officer"])).get_json()["unreadCount"] == 0


def test_reopen_ui_is_served(client):
    page = client.get("/my-complaints")
    assert page.status_code == 200
    assert b'id="reopen-panel"' in page.data
    staff_page = client.get("/staff-notifications")
    assert staff_page.status_code == 200
    assert b'id="staff-notifications-list"' in staff_page.data
