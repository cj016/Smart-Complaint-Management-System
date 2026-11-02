"""SCMS-F040: Automatic complaint status notifications."""

from app.extensions import db
from app.models import Notification, Role
from tests.admin_helpers import auth, make_complaint, make_user


def test_status_update_notifies_citizen(client, app):
    with app.app_context():
        admin = make_user("f040-admin@example.com", Role.ADMIN)
        citizen = make_user("f040-citizen@example.com")
        complaint = make_complaint(citizen, 1)

        response = client.patch(
            f"/api/v1/admin/complaints/{complaint.public_id}/status",
            headers=auth(admin),
            json={"status": "In Review", "remarks": "Checking"},
        )

        assert response.status_code == 200

        notifications = db.session.execute(
            db.select(Notification).where(
                Notification.user_id == citizen.id,
                Notification.channel == "in_app",
            )
        ).scalars().all()

        assert len(notifications) == 1
        assert complaint.public_id in notifications[0].message
        assert "In Review" in notifications[0].message
        assert notifications[0].complaint_id == complaint.id


def test_invalid_status_creates_no_notification(client, app):
    with app.app_context():
        admin = make_user("invalid-admin@example.com", Role.ADMIN)
        citizen = make_user("invalid-citizen@example.com")
        complaint = make_complaint(citizen, 1)

        response = client.patch(
            f"/api/v1/admin/complaints/{complaint.public_id}/status",
            headers=auth(admin),
            json={"status": "Resolved", "remarks": "Attempted resolution"},
        )

        assert response.status_code == 409
        assert db.session.scalar(
            db.select(db.func.count(Notification.id))
        ) == 0


def test_citizen_cannot_trigger_status_notification(client, app):
    with app.app_context():
        citizen = make_user("blocked-citizen@example.com")
        complaint = make_complaint(citizen, 1)

        response = client.patch(
            f"/api/v1/admin/complaints/{complaint.public_id}/status",
            headers=auth(citizen),
            json={"status": "In Review"},
        )

        assert response.status_code == 403
        assert db.session.scalar(
            db.select(db.func.count(Notification.id))
        ) == 0


def test_assignment_notifies_citizen(client, app):
    with app.app_context():
        admin = make_user("assign-admin@example.com", Role.ADMIN)
        officer = make_user("assign-officer@example.com", Role.OFFICER)
        citizen = make_user("assign-citizen@example.com")
        complaint = make_complaint(citizen, 1)

        response = client.post(
            f"/api/v1/admin/complaints/{complaint.public_id}/assign",
            headers=auth(admin),
            json={"officerId": officer.id},
        )

        assert response.status_code == 200

        notifications = db.session.execute(
            db.select(Notification).where(
                Notification.user_id == citizen.id,
                Notification.channel == "in_app",
            )
        ).scalars().all()

        assert len(notifications) == 1
        assert "Assigned" in notifications[0].message
