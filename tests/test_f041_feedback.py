"""SCMS-F041: citizen feedback and admin visibility regressions."""
import pytest

from app.extensions import db
from app.models import Feedback, Role
from tests.admin_helpers import auth, make_complaint, make_user

API = "/api/v1/complaints/SCMS-2026-00001/feedback"
ADMIN_API = "/api/v1/admin/feedback"


@pytest.fixture()
def people(app):
    return {
        "owner": make_user("owner-f041@example.com"),
        "stranger": make_user("stranger-f041@example.com"),
        "officer": make_user("officer-f041@example.com", Role.OFFICER),
        "admin": make_user("admin-f041@example.com", Role.ADMIN),
    }


def send(client, who, data=None, url=API):
    return client.post(url, headers=auth(who),
                       json={"rating": 5, "comment": "Good work"}
                       if data is None else data)


def test_citizen_rates_own_resolved_complaint(client, people):
    c = make_complaint(people["owner"], status="Resolved")
    result = send(client, people["owner"], {"rating": 4, "comment": "  Fixed quickly  "})
    assert result.status_code == 201
    body = result.get_json()
    assert body["complaintId"] == c.public_id
    assert body["rating"] == 4
    assert body["comment"] == "Fixed quickly"
    assert body["createdAt"]
    db.session.expire_all()
    saved = db.session.execute(db.select(Feedback)).scalar_one()
    assert saved.user_id == people["owner"].id
    assert saved.complaint_id == c.id
    assert saved.complaint.status == "Resolved"


@pytest.mark.parametrize("payload", [
    {"rating": 1},
    {"rating": 5, "comment": ""},
    {"rating": 3, "comment": "   "},
])
def test_rating_one_to_five_and_optional_comment(client, people, payload):
    make_complaint(people["owner"], status="Resolved")
    response = send(client, people["owner"], payload)
    assert response.status_code == 201
    assert response.get_json()["comment"] is None


@pytest.mark.parametrize(
    "rating",
    [None, 0, 6, True, False, 1.5, "5", "invalid", [], {}],
)
def test_rejects_invalid_ratings(client, people, rating):
    make_complaint(people["owner"], status="Resolved")
    response = send(client, people["owner"], {"rating": rating})
    assert response.status_code == 422
    assert response.get_json()["error"]["details"]["field"] == "rating"
    assert db.session.execute(db.select(Feedback)).scalars().all() == []


@pytest.mark.parametrize("comment", [10, [], {}, "x" * 1001])
def test_rejects_invalid_comments(client, people, comment):
    make_complaint(people["owner"], status="Resolved")
    response = send(client, people["owner"], {"rating": 4, "comment": comment})
    assert response.status_code == 422
    assert db.session.execute(db.select(Feedback)).scalars().all() == []


def test_duplicate_feedback_is_rejected_and_original_preserved(client, people):
    make_complaint(people["owner"], status="Resolved")
    assert send(client, people["owner"], {"rating": 5}).status_code == 201
    duplicate = send(client, people["owner"], {"rating": 1})
    assert duplicate.status_code == 409
    existing = db.session.execute(db.select(Feedback)).scalar_one()
    assert existing.rating == 5


@pytest.mark.parametrize("status", ["Submitted", "In Review", "Assigned",
                                    "In Progress", "Closed", "Reopened"])
def test_only_resolved_complaints_can_be_rated(client, people, status):
    make_complaint(people["owner"], status=status)
    response = send(client, people["owner"])
    assert response.status_code == 409


def test_cannot_rate_someone_elses_complaint(client, people):
    make_complaint(people["owner"], status="Resolved")
    assert send(client, people["stranger"]).status_code == 404


def test_missing_complaint_is_not_found(client, people):
    assert send(client, people["owner"]).status_code == 404


def test_unauthed_submission_is_rejected(client):
    assert client.post(API, json={"rating": 5}).status_code == 401


@pytest.mark.parametrize("role", ["officer", "admin"])
def test_staff_cannot_submit_feedback(client, people, role):
    make_complaint(people["owner"], status="Resolved")
    assert send(client, people[role]).status_code == 403


def test_request_requires_json_object(client, people):
    make_complaint(people["owner"], status="Resolved")
    assert client.post(API, headers=auth(people["owner"]),
                       data="not json").status_code == 422
    assert send(client, people["owner"], [1, 2]).status_code == 422


def test_admin_views_submitted_ratings(client, people):
    make_complaint(people["owner"], status="Resolved")
    assert send(client, people["owner"]).status_code == 201
    response = client.get(ADMIN_API, headers=auth(people["admin"]))
    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["complaintId"] == "SCMS-2026-00001"
    assert body["items"][0]["rating"] == 5
    assert body["items"][0]["comment"] == "Good work"
    assert "email" not in body["items"][0]
    assert "password_hash" not in body["items"][0]


@pytest.mark.parametrize("role", ["owner", "officer"])
def test_non_admins_cannot_read_ratings(client, people, role):
    assert client.get(ADMIN_API, headers=auth(people[role])).status_code == 403


def test_anonymous_cannot_read_ratings(client):
    assert client.get(ADMIN_API).status_code == 401


def test_admin_feedback_pagination(client, people):
    make_complaint(people["owner"], n=1, status="Resolved")
    make_complaint(people["owner"], n=2, status="Resolved")
    assert send(client, people["owner"]).status_code == 201
    assert send(client, people["owner"], url=API.replace("00001", "00002")).status_code == 201
    response = client.get(ADMIN_API + "?page=1&per_page=1",
                          headers=auth(people["admin"]))
    assert response.status_code == 200
    assert response.get_json()["total"] == 2
    assert len(response.get_json()["items"]) == 1
    assert response.get_json()["pages"] == 2


@pytest.mark.parametrize("query", ["page=abc", "per_page=-1", "page=0"])
def test_invalid_admin_pagination(client, people, query):
    assert client.get(ADMIN_API + "?" + query,
                      headers=auth(people["admin"])).status_code == 422


def test_feedback_pages_render(client):
    citizen = client.get("/feedback")
    admin = client.get("/admin/feedback")
    assert citizen.status_code == admin.status_code == 200
    assert b"feedback.js" in citizen.data
    assert b"admin_feedback.js" in admin.data
    assert b"feedback-cta" in client.get("/track").data
    assert b"Rate a resolution" in client.get("/").data
