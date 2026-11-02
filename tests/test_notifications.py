"""SCMS-F023: Notification inbox tests."""

from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import Notification, Role, User


URL = "/api/v1/notifications/"


def make_user(email, role=Role.COMPLAINANT):
    user = User(
        name=email.split("@")[0],
        email=email,
        password_hash="test-hash",
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    return user


def headers(user):
    token = create_access_token(identity=str(user.id))
    return {"Authorization": "Bearer " + token}


def add_notification(user, message, read=False):
    item = Notification(
        user_id=user.id,
        channel="in_app",
        message=message,
        delivery_status="delivered",
        is_read=read,
    )
    db.session.add(item)
    db.session.commit()
    return item


def test_inbox_requires_login(client):
    response = client.get(URL)
    assert response.status_code == 401


def test_citizen_sees_only_own_notifications(client, app):
    with app.app_context():
        first = make_user("first@example.com")
        second = make_user("second@example.com")

        add_notification(first, "Your complaint was updated")
        add_notification(second, "Private notification")

        response = client.get(URL, headers=headers(first))

        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 1
        assert data["items"][0]["message"] == (
            "Your complaint was updated"
        )


def test_officer_cannot_use_citizen_inbox(client, app):
    with app.app_context():
        officer = make_user("officer@example.com", Role.OFFICER)

        response = client.get(URL, headers=headers(officer))
        assert response.status_code == 403


def test_unread_count(client, app):
    with app.app_context():
        user = make_user("citizen@example.com")

        add_notification(user, "Unread")
        add_notification(user, "Already read", read=True)

        response = client.get(
            URL + "unread-count",
            headers=headers(user),
        )

        assert response.status_code == 200
        assert response.get_json()["unreadCount"] == 1


def test_mark_own_notification_read(client, app):
    with app.app_context():
        user = make_user("owner@example.com")
        item = add_notification(user, "Status updated")

        response = client.patch(
            URL + str(item.id) + "/read",
            headers=headers(user),
        )

        assert response.status_code == 200
        assert response.get_json()["isRead"] is True


def test_cannot_mark_another_users_notification(client, app):
    with app.app_context():
        owner = make_user("owner@example.com")
        other = make_user("other@example.com")
        item = add_notification(owner, "Private notification")

        response = client.patch(
            URL + str(item.id) + "/read",
            headers=headers(other),
        )

        assert response.status_code == 404
        assert db.session.get(Notification, item.id).is_read is False


def test_invalid_pagination_is_rejected(client, app):
    with app.app_context():
        user = make_user("paging@example.com")

        response = client.get(
            URL + "?page=abc",
            headers=headers(user),
        )

        assert response.status_code == 422


def test_inbox_excludes_email_and_sms_records(client, app):
    with app.app_context():
        user = make_user("channels@example.com")

        add_notification(user, "In-app update")

        for channel in ("email", "sms"):
            db.session.add(Notification(
                user_id=user.id,
                channel=channel,
                message="External delivery record",
                delivery_status="delivered",
            ))
        db.session.commit()

        response = client.get(URL, headers=headers(user))

        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 1
        assert data["items"][0]["channel"] == "in_app"
