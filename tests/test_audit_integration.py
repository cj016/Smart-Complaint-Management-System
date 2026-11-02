"""SCMS-SR004: Admin actions generate audit entries."""

from app.audit.services import verify_audit_chain
from app.extensions import db
from app.models import AuditLog, Role
from tests.admin_helpers import auth, make_complaint, make_user


def test_status_change_is_audited(client, app):
    with app.app_context():
        admin = make_user("audit-admin@example.com", Role.ADMIN)
        citizen = make_user("audit-citizen@example.com")
        complaint = make_complaint(citizen)

        response = client.patch(
            f"/api/v1/admin/complaints/{complaint.public_id}/status",
            headers=auth(admin),
            json={"status": "In Review"},
        )

        assert response.status_code == 200

        entry = db.session.scalar(db.select(AuditLog))
        assert entry.actor_id == admin.id
        assert entry.action == "COMPLAINT_STATUS_CHANGED"
        assert entry.entity_id == complaint.public_id
        assert verify_audit_chain()["valid"] is True


def test_assignment_is_audited(client, app):
    with app.app_context():
        admin = make_user("audit-admin@example.com", Role.ADMIN)
        officer = make_user("audit-officer@example.com", Role.OFFICER)
        citizen = make_user("audit-citizen@example.com")
        complaint = make_complaint(citizen)

        response = client.post(
            f"/api/v1/admin/complaints/{complaint.public_id}/assign",
            headers=auth(admin),
            json={"officerId": officer.id},
        )

        assert response.status_code == 200
        entry = db.session.scalar(db.select(AuditLog))
        assert entry.action == "COMPLAINT_ASSIGNED"
        assert entry.actor_id == admin.id
        assert verify_audit_chain()["valid"] is True


def test_failed_action_creates_no_audit_entry(client, app):
    with app.app_context():
        admin = make_user("audit-admin@example.com", Role.ADMIN)
        citizen = make_user("audit-citizen@example.com")
        complaint = make_complaint(citizen)

        response = client.patch(
            f"/api/v1/admin/complaints/{complaint.public_id}/status",
            headers=auth(admin),
            json={"status": "Closed"},
        )

        assert response.status_code == 409
        assert db.session.scalar(
            db.select(db.func.count(AuditLog.id))
        ) == 0


def test_reassignment_is_audited(client, app):
    with app.app_context():
        admin = make_user("audit-admin@example.com", Role.ADMIN)
        first = make_user("first-officer@example.com", Role.OFFICER)
        second = make_user("second-officer@example.com", Role.OFFICER)
        citizen = make_user("audit-citizen@example.com")
        complaint = make_complaint(
            citizen, status="Assigned", assignee=first
        )

        response = client.post(
            f"/api/v1/admin/complaints/{complaint.public_id}/reassign",
            headers=auth(admin),
            json={"officerId": second.id, "remarks": "Workload"},
        )

        assert response.status_code == 200
        entry = db.session.scalar(db.select(AuditLog))
        assert entry.action == "COMPLAINT_REASSIGNED"
        assert entry.actor_id == admin.id
        assert verify_audit_chain()["valid"] is True
