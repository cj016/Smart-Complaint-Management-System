"""SCMS-SR004: Audit API access and verification tests."""

from app.audit.services import record_audit
from app.extensions import db
from app.models import Role
from tests.admin_helpers import auth, make_user


def test_audit_api_requires_login(client):
    assert client.get("/api/v1/audit/verify").status_code == 401
    assert client.get("/api/v1/audit/entries").status_code == 401


def test_citizen_cannot_view_audit(client, app):
    with app.app_context():
        citizen = make_user("audit-view-citizen@example.com")
        headers = auth(citizen)

        assert client.get(
            "/api/v1/audit/verify", headers=headers
        ).status_code == 403

        assert client.get(
            "/api/v1/audit/entries", headers=headers
        ).status_code == 403


def test_officer_cannot_view_audit(client, app):
    with app.app_context():
        officer = make_user(
            "audit-view-officer@example.com", Role.OFFICER
        )
        headers = auth(officer)

        assert client.get(
            "/api/v1/audit/verify", headers=headers
        ).status_code == 403


def test_admin_can_view_and_verify_audit(client, app):
    with app.app_context():
        admin = make_user(
            "audit-view-admin@example.com", Role.ADMIN
        )
        record_audit(
            admin.id, "COMPLAINT_ASSIGNED", "Complaint",
            "SCMS-2026-00001", "Assigned to officer"
        )
        db.session.commit()

        headers = auth(admin)

        verify = client.get(
            "/api/v1/audit/verify", headers=headers
        )
        assert verify.status_code == 200
        assert verify.get_json()["valid"] is True
        assert verify.get_json()["checked"] == 1

        entries = client.get(
            "/api/v1/audit/entries", headers=headers
        )
        assert entries.status_code == 200

        items = entries.get_json()["items"]
        assert len(items) == 1
        assert items[0]["action"] == "COMPLAINT_ASSIGNED"
        assert items[0]["actorId"] == admin.id


def test_audit_api_has_no_modify_routes(client, app):
    with app.app_context():
        admin = make_user(
            "audit-no-edit-admin@example.com", Role.ADMIN
        )
        headers = auth(admin)

        assert client.patch(
            "/api/v1/audit/entries/1",
            headers=headers,
            json={"details": "Changed"},
        ).status_code == 404

        assert client.delete(
            "/api/v1/audit/entries/1",
            headers=headers,
        ).status_code == 404
