"""Test cases TC-Admin-02 (SCMS-F-031 view all complaints) and TC-Admin-03 (SCMS-F-032
filter / sort by category, priority, status)."""
import pytest
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import Complaint, Role, User

URL = "/api/v1/admin/complaints"


def make_user(email, role):
    user = User(name=email.split("@")[0], email=email, password_hash="x", role=role,
                is_verified=True)
    db.session.add(user)
    db.session.commit()
    return user


def auth(user):
    return {"Authorization": f"Bearer {create_access_token(identity=str(user.id))}"}


def make_complaint(owner, n, category="Sanitation", priority="Medium", status="Submitted",
                   location="5th Cross Road", description="Overflowing bin"):
    c = Complaint(public_id=f"SCMS-2026-{n:05d}", user_id=owner.id, category=category,
                  description=description, location=location, status=status,
                  priority=priority)
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture()
def people(app):
    return {
        "citizen": make_user("citizen@example.com", Role.COMPLAINANT),
        "officer": make_user("officer@example.com", Role.OFFICER),
        "admin": make_user("admin@example.com", Role.ADMIN),
    }


def ids(resp):
    return [item["complaintId"] for item in resp.get_json()["items"]]


# ---- F-031: access control -------------------------------------------------------------

def test_requires_login(client):
    resp = client.get(URL)
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_citizen_is_forbidden(client, people):
    assert client.get(URL, headers=auth(people["citizen"])).status_code == 403


@pytest.mark.parametrize("who", ["officer", "admin"])
def test_staff_can_open_dashboard(client, people, who):
    assert client.get(URL, headers=auth(people[who])).status_code == 200


# ---- F-031: list everything ------------------------------------------------------------

def test_lists_complaints_from_all_citizens(client, people):
    other = make_user("other@example.com", Role.COMPLAINANT)
    make_complaint(people["citizen"], 1)
    make_complaint(other, 2)
    resp = client.get(URL, headers=auth(people["admin"]))
    body = resp.get_json()
    assert body["total"] == 2
    assert set(ids(resp)) == {"SCMS-2026-00001", "SCMS-2026-00002"}
    row = body["items"][0]
    for key in ("complaintId", "category", "location", "status", "priority", "assignedTo",
                "createdAt"):
        assert key in row


def test_newest_first_by_default(client, people):
    for n in (1, 2, 3):
        make_complaint(people["citizen"], n)
    resp = client.get(URL, headers=auth(people["admin"]))
    assert ids(resp) == ["SCMS-2026-00003", "SCMS-2026-00002", "SCMS-2026-00001"]


def test_pagination(client, people):
    for n in range(1, 4):
        make_complaint(people["citizen"], n)
    resp = client.get(f"{URL}?per_page=2&page=2", headers=auth(people["admin"]))
    body = resp.get_json()
    assert body["total"] == 3 and body["pages"] == 2 and body["page"] == 2
    assert len(body["items"]) == 1


def test_bad_page_is_422(client, people):
    resp = client.get(f"{URL}?page=abc", headers=auth(people["admin"]))
    assert resp.status_code == 422
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


# ---- F-032: filters ----------------------------------------------------------------------

def test_filter_by_status(client, people):
    make_complaint(people["citizen"], 1, status="Submitted")
    make_complaint(people["citizen"], 2, status="Resolved")
    resp = client.get(f"{URL}?status=Resolved", headers=auth(people["admin"]))
    assert ids(resp) == ["SCMS-2026-00002"]


def test_filter_by_category(client, people):
    make_complaint(people["citizen"], 1, category="Roads")
    make_complaint(people["citizen"], 2, category="Sanitation")
    resp = client.get(f"{URL}?category=Roads", headers=auth(people["admin"]))
    assert ids(resp) == ["SCMS-2026-00001"]


def test_filter_by_priority(client, people):
    make_complaint(people["citizen"], 1, priority="Low")
    make_complaint(people["citizen"], 2, priority="Critical")
    resp = client.get(f"{URL}?priority=Critical", headers=auth(people["admin"]))
    assert ids(resp) == ["SCMS-2026-00002"]


def test_filters_combine(client, people):
    make_complaint(people["citizen"], 1, category="Roads", priority="High")
    make_complaint(people["citizen"], 2, category="Roads", priority="Low")
    make_complaint(people["citizen"], 3, category="Noise", priority="High")
    resp = client.get(f"{URL}?category=Roads&priority=High", headers=auth(people["admin"]))
    assert ids(resp) == ["SCMS-2026-00001"]


def test_search_by_location_or_id(client, people):
    make_complaint(people["citizen"], 1, location="Gandhi Nagar")
    make_complaint(people["citizen"], 2, location="MG Road")
    admin = auth(people["admin"])
    assert ids(client.get(f"{URL}?q=gandhi", headers=admin)) == ["SCMS-2026-00001"]
    assert ids(client.get(f"{URL}?q=00002", headers=admin)) == ["SCMS-2026-00002"]


def test_search_treats_percent_as_text(client, people):
    make_complaint(people["citizen"], 1)
    resp = client.get(f"{URL}?q=%25", headers=auth(people["admin"]))
    assert resp.get_json()["total"] == 0


@pytest.mark.parametrize("query", ["status=Nope", "priority=Urgent", "sort=password",
                                   "order=sideways"])
def test_bad_filter_values_are_422(client, people, query):
    resp = client.get(f"{URL}?{query}", headers=auth(people["admin"]))
    assert resp.status_code == 422
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


# ---- F-032: sorting ----------------------------------------------------------------------

def test_sort_by_priority_uses_severity_not_alphabet(client, people):
    make_complaint(people["citizen"], 1, priority="Low")
    make_complaint(people["citizen"], 2, priority="Critical")
    make_complaint(people["citizen"], 3, priority="Medium")
    make_complaint(people["citizen"], 4, priority="High")
    admin = auth(people["admin"])
    desc = client.get(f"{URL}?sort=priority&order=desc", headers=admin)
    assert ids(desc) == ["SCMS-2026-00002", "SCMS-2026-00004", "SCMS-2026-00003",
                         "SCMS-2026-00001"]
    asc = client.get(f"{URL}?sort=priority&order=asc", headers=admin)
    assert ids(asc)[0] == "SCMS-2026-00001"


def test_sort_by_status_follows_the_workflow(client, people):
    make_complaint(people["citizen"], 1, status="Resolved")
    make_complaint(people["citizen"], 2, status="Submitted")
    make_complaint(people["citizen"], 3, status="In Progress")
    resp = client.get(f"{URL}?sort=status&order=asc", headers=auth(people["admin"]))
    assert ids(resp) == ["SCMS-2026-00002", "SCMS-2026-00003", "SCMS-2026-00001"]


def test_sort_by_category(client, people):
    make_complaint(people["citizen"], 1, category="Roads")
    make_complaint(people["citizen"], 2, category="Noise")
    resp = client.get(f"{URL}?sort=category&order=asc", headers=auth(people["admin"]))
    assert ids(resp) == ["SCMS-2026-00002", "SCMS-2026-00001"]


# ---- helpers used by the page ------------------------------------------------------------

def test_filter_options(client, people):
    make_complaint(people["citizen"], 1, category="Roads")
    make_complaint(people["citizen"], 2, category="Noise")
    body = client.get("/api/v1/admin/filter-options", headers=auth(people["admin"])).get_json()
    assert body["categories"] == ["Noise", "Roads"]
    assert "Critical" in body["priorities"] and "Reopened" in body["statuses"]


def test_filter_options_forbidden_for_citizen(client, people):
    resp = client.get("/api/v1/admin/filter-options", headers=auth(people["citizen"]))
    assert resp.status_code == 403


def test_detail_includes_description(client, people):
    make_complaint(people["citizen"], 1, description="Pipe leak")
    resp = client.get(f"{URL}/SCMS-2026-00001", headers=auth(people["officer"]))
    assert resp.status_code == 200
    assert resp.get_json()["description"] == "Pipe leak"
    assert client.get(f"{URL}/SCMS-2026-99999", headers=auth(people["officer"])
                      ).status_code == 404


def test_dashboard_page_renders(client):
    resp = client.get("/admin")
    assert resp.status_code == 200
    assert b'name="viewport"' in resp.data
