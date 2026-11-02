"""SCMS-F023: Create and deliver citizen notifications."""

import smtplib
from email.message import EmailMessage

from flask import current_app

from ..extensions import db
from ..models import Notification, User


def _record(user_id, complaint_id, channel, message, status):
    notification = Notification(
        user_id=user_id,
        complaint_id=complaint_id,
        channel=channel,
        message=message,
        delivery_status=status,
    )
    db.session.add(notification)
    return notification


def _send_email(address, message):
    """Send email only when an SMTP server is configured."""
    host = current_app.config.get("SMTP_HOST")
    sender = current_app.config.get("SMTP_FROM")

    if not host or not sender:
        return False

    mail = EmailMessage()
    mail["Subject"] = "SCMS Complaint Update"
    mail["From"] = sender
    mail["To"] = address
    mail.set_content(message)

    port = int(current_app.config.get("SMTP_PORT", 587))
    username = current_app.config.get("SMTP_USERNAME")
    password = current_app.config.get("SMTP_PASSWORD")
    use_ssl = current_app.config.get("SMTP_USE_SSL", False)

    if use_ssl:
        server = smtplib.SMTP_SSL(host, port, timeout=10)
    else:
        server = smtplib.SMTP(host, port, timeout=10)

    with server:
        if not use_ssl:
            server.starttls()
        if username and password:
            server.login(username, password)
        server.send_message(mail)

    return True


def create_notification(user_id, message, complaint_id=None):
    """Create an in-app notification and attempt configured channels.

    Returns the persisted notification records. A failed external
    delivery does not remove the citizen's in-app notification.
    """
    user = db.session.get(User, user_id)
    if user is None:
        raise ValueError("Notification recipient does not exist.")

    if not isinstance(message, str) or not message.strip():
        raise ValueError("Notification message must not be empty.")

    message = message.strip()

    records = [
        _record(user.id, complaint_id, "in_app", message, "delivered")
    ]

    # Save the in-app notification before attempting external delivery.
    db.session.commit()

    if user.email and current_app.config.get("SMTP_HOST"):
        email_record = _record(
            user.id, complaint_id, "email", message, "pending"
        )
        db.session.commit()
        records.append(email_record)

        try:
            delivered = _send_email(user.email, message)
            email_record.delivery_status = (
                "delivered" if delivered else "failed"
            )
        except (OSError, smtplib.SMTPException, ValueError):
            current_app.logger.warning(
                "Notification email delivery failed."
            )
            email_record.delivery_status = "failed"

        db.session.commit()

    # SMS requires an actual gateway adapter configured by deployment.
    # Do not claim SMS delivery merely because a mobile number exists.
    sms_sender = current_app.config.get("SMS_SENDER")

    if user.mobile and callable(sms_sender):
        sms_record = _record(
            user.id, complaint_id, "sms", message, "pending"
        )
        db.session.commit()
        records.append(sms_record)

        try:
            result = sms_sender(user.mobile, message)
            sms_record.delivery_status = (
                "delivered" if result is True else "failed"
            )
        except Exception:
            current_app.logger.warning(
                "Notification SMS gateway delivery failed."
            )
            sms_record.delivery_status = "failed"

        db.session.commit()

    return records
