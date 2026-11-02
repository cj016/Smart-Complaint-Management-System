"""Tests for the SCMS-F023 delivery service."""

from unittest.mock import patch

from app.extensions import db
from app.models import Notification, Role, User
from app.notifications.services import create_notification


def make_user(email="citizen@example.com", mobile=None):
    user = User(
        name="Test Citizen",
        email=email,
        password_hash="test-hash",
        role=Role.COMPLAINANT,
    )
    if mobile:
        user.set_mobile(mobile)
    db.session.add(user)
    db.session.commit()
    return user


def test_creates_in_app_notification(app):
    with app.app_context():
        user = make_user()

        records = create_notification(
            user.id, "Your complaint is in progress."
        )

        assert len(records) == 1
        assert records[0].channel == "in_app"
        assert records[0].delivery_status == "delivered"

        stored = db.session.get(Notification, records[0].id)
        assert stored.message == "Your complaint is in progress."


def test_email_not_sent_without_configuration(app):
    with app.app_context():
        user = make_user()

        with patch(
            "app.notifications.services._send_email"
        ) as send_email:
            records = create_notification(user.id, "Status updated")

        assert len(records) == 1
        send_email.assert_not_called()


def test_configured_email_delivery(app):
    with app.app_context():
        user = make_user()
        app.config["SMTP_HOST"] = "smtp.example.com"

        with patch(
            "app.notifications.services._send_email",
            return_value=True,
        ) as send_email:
            records = create_notification(user.id, "Status updated")

        assert len(records) == 2
        assert records[1].channel == "email"
        assert records[1].delivery_status == "delivered"
        send_email.assert_called_once_with(
            user.email, "Status updated"
        )


def test_failed_email_preserves_in_app_notification(app):
    with app.app_context():
        user = make_user()
        app.config["SMTP_HOST"] = "smtp.example.com"

        with patch(
            "app.notifications.services._send_email",
            side_effect=OSError("SMTP unavailable"),
        ):
            records = create_notification(user.id, "Status updated")

        assert records[0].delivery_status == "delivered"
        assert records[1].delivery_status == "failed"


def test_configured_sms_sender(app):
    with app.app_context():
        user = make_user(mobile="9876543210")
        calls = []

        def send_sms(mobile, message):
            calls.append((mobile, message))
            return True

        app.config["SMS_SENDER"] = send_sms
        records = create_notification(user.id, "Status updated")

        assert len(records) == 2
        assert records[1].channel == "sms"
        assert records[1].delivery_status == "delivered"
        assert calls == [("9876543210", "Status updated")]
