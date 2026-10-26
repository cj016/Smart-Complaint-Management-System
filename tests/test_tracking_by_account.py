"""Test case TC-Track-02 (SCMS-F-021): track complaint status by account."""
from datetime import timedelta

import pytest
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import Complaint, User
from app.utils import utcnow


def make_user(email):
    user = User(name=email.split("@")[0], email=email, password_hash="x")
    db.session.add(user)
    db.session.commit()
    return user


def make_complaint(user, n, status="Submitted"):
    c = Complaint(public_id=f"SCMS-2026-{n:05d}", user_id=user.id, category="Roads",
                  description="Pothole", location="Main St", status=status,
                  created_at=utcnow() + timedelta(minutes=n))
    db.session.add(c)
    db.session.commit()
    return c


def auth(user):
    token = create_access_token(identity=str(user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def two_users(app):
    return make_user("a@example.com"), make_user("b@example.com")


def test_requires_login(client):
    resp = client.get("/api/v1/tracking/my-complaints")
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_returns_only_own_complaints_newest_first(client, two_users):
    a, b = two_users
    make_complaint(a, 1)
    make_complaint(a, 2, "In Progress")
    make_complaint(b, 3)
    resp = client.get("/api/v1/tracking/my-complaints", headers=auth(a))
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 2
    assert [i["complaintId"] for i in body["items"]] == ["SCMS-2026-00002", "SCMS-2026-00001"]
    assert set(body["items"][0]) == {"complaintId", "category", "location", "status",
                                     "priority", "createdAt", "updatedAt"}


def test_user_with_no_complaints_gets_empty_list(client, two_users):
    resp = client.get("/api/v1/tracking/my-complaints", headers=auth(two_users[1]))
    assert resp.status_code == 200
    assert resp.get_json()["items"] == []
    assert resp.get_json()["total"] == 0


def test_status_filter(client, two_users):
    a, _ = two_users
    make_complaint(a, 1, "Submitted")
    make_complaint(a, 2, "Resolved")
    resp = client.get("/api/v1/tracking/my-complaints?status=Resolved", headers=auth(a))
    items = resp.get_json()["items"]
    assert [i["status"] for i in items] == ["Resolved"]


def test_invalid_status_filter_rejected(client, two_users):
    resp = client.get("/api/v1/tracking/my-complaints?status=Nope", headers=auth(two_users[0]))
    assert resp.status_code == 422
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_pagination(client, two_users):
    a, _ = two_users
    for n in range(1, 6):
        make_complaint(a, n)
    resp = client.get("/api/v1/tracking/my-complaints?page=2&per_page=2", headers=auth(a))
    body = resp.get_json()
    assert body["total"] == 5 and body["pages"] == 3 and body["page"] == 2
    assert len(body["items"]) == 2


def test_bad_page_value_rejected(client, two_users):
    resp = client.get("/api/v1/tracking/my-complaints?page=abc", headers=auth(two_users[0]))
    assert resp.status_code == 422
