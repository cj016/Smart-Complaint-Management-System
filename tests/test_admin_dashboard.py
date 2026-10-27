"""SCMS-F-031 (dashboard lists all complaints) and SCMS-F-032 (filter / sort)."""
import pytest

from app.models import Role
from tests.admin_helpers import auth, make_complaint, make_user

URL = "/api/v1/admin/complaints"


@pytest.fixture()
def people(app):
    return {
        "admin": make_user("admin@example.com", Role.ADMIN),
        "officer": make_user("officer@example.com", Role.OFFICER),
        "a": make_user("a@example.com", name="Asha"),
        "b": make_user("b@example.com", name="Bala"),
    }


@pytest.fixture()
def seeded(people):
    a, b = people["a"], people["b"]
    make_complaint(a, 1, status="Submitted", priority="Low", category="Roads")
    make_complaint(b, 2, status="In Progress", priority="Critical", category="Sanitation")
    make_complaint(a, 3, status="Resolved", priority="High", category="Roads")
    make_complaint(b, 4, status="Submitted", priority="Medium", category="Noise")
    return people


def ids(resp):
    return [item["complaintId"] for item in resp.get_json()["items"]]


# ---- F-031: view all complaints ----------------------------------------------------

def test_requires_login(client):
    resp = client.get(URL)
    assert resp.status_code == 401


def test_complainant_is_forbidden(client, seeded):
    assert client.get(URL, headers=auth(seeded["a"])).status_code == 403


@pytest.mark.parametrize("who", ["admin", "officer"])
def test_staff_see_complaints_of_all_citizens(client, seeded, who):
    resp = client.get(URL, headers=auth(seeded[who]))
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 4
    assert {i["complainant"] for i in body["items"]} == {"Asha", "Bala"}


def test_default_order_is_newest_first(client, seeded):
    resp = client.get(URL, headers=auth(seeded["admin"]))
    assert ids(resp) == ["SCMS-2026-00004", "SCMS-2026-00003", "SCMS-2026-00002",
                         "SCMS-2026-00001"]


def test_row_has_expected_fields(client, seeded):
    item = client.get(URL, headers=auth(seeded["admin"])).get_json()["items"][0]
    assert set(item) == {"complaintId", "category", "location", "status", "priority",
                         "department", "complainant", "assignedTo", "nextStatuses",
                         "createdAt", "updatedAt"}
    assert item["assignedTo"] is None


def test_pagination(client, seeded):
    resp = client.get(f"{URL}?per_page=3&page=2", headers=auth(seeded["admin"]))
    body = resp.get_json()
    assert body["total"] == 4 and body["pages"] == 2 and len(body["items"]) == 1


@pytest.mark.parametrize("query", ["page=0", "per_page=0", "page=x"])
def test_bad_paging_is_422(client, seeded, query):
    resp = client.get(f"{URL}?{query}", headers=auth(seeded["admin"]))
    assert resp.status_code == 422


# ---- F-032: filter ------------------------------------------------------------------

def test_filter_by_category(client, seeded):
    resp = client.get(f"{URL}?category=Roads", headers=auth(seeded["admin"]))
    assert sorted(ids(resp)) == ["SCMS-2026-00001", "SCMS-2026-00003"]


def test_filter_by_priority(client, seeded):
    resp = client.get(f"{URL}?priority=Critical", headers=auth(seeded["admin"]))
    assert ids(resp) == ["SCMS-2026-00002"]


def test_filter_by_status(client, seeded):
    resp = client.get(f"{URL}?status=Submitted", headers=auth(seeded["admin"]))
    assert sorted(ids(resp)) == ["SCMS-2026-00001", "SCMS-2026-00004"]


def test_filters_combine(client, seeded):
    resp = client.get(f"{URL}?category=Roads&status=Submitted",
                      headers=auth(seeded["admin"]))
    assert ids(resp) == ["SCMS-2026-00001"]


def test_filter_with_no_match_is_empty_not_an_error(client, seeded):
    resp = client.get(f"{URL}?category=Roads&priority=Critical",
                      headers=auth(seeded["admin"]))
    assert resp.status_code == 200
    assert resp.get_json()["items"] == []


@pytest.mark.parametrize("query", ["status=Nope", "priority=Urgent"])
def test_unknown_filter_value_is_422(client, seeded, query):
    resp = client.get(f"{URL}?{query}", headers=auth(seeded["admin"]))
    assert resp.status_code == 422
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


# ---- F-032: sort --------------------------------------------------------------------

def test_sort_by_priority_uses_severity_not_alphabet(client, seeded):
    resp = client.get(f"{URL}?sort=priority&order=desc", headers=auth(seeded["admin"]))
    priorities = [i["priority"] for i in resp.get_json()["items"]]
    assert priorities == ["Critical", "High", "Medium", "Low"]


def test_sort_by_priority_ascending(client, seeded):
    resp = client.get(f"{URL}?sort=priority&order=asc", headers=auth(seeded["admin"]))
    priorities = [i["priority"] for i in resp.get_json()["items"]]
    assert priorities == ["Low", "Medium", "High", "Critical"]


def test_sort_by_status_follows_lifecycle_order(client, seeded):
    resp = client.get(f"{URL}?sort=status&order=asc", headers=auth(seeded["admin"]))
    statuses = [i["status"] for i in resp.get_json()["items"]]
    assert statuses == ["Submitted", "Submitted", "In Progress", "Resolved"]


def test_sort_by_category(client, seeded):
    resp = client.get(f"{URL}?sort=category&order=asc", headers=auth(seeded["admin"]))
    categories = [i["category"] for i in resp.get_json()["items"]]
    assert categories == sorted(categories)


def test_sort_by_oldest_first(client, seeded):
    resp = client.get(f"{URL}?sort=created_at&order=asc", headers=auth(seeded["admin"]))
    assert ids(resp)[0] == "SCMS-2026-00001"


@pytest.mark.parametrize("query", ["sort=password", "sort=id;DROP", "order=sideways"])
def test_bad_sort_is_422(client, seeded, query):
    resp = client.get(f"{URL}?{query}", headers=auth(seeded["admin"]))
    assert resp.status_code == 422


def test_filter_and_sort_together(client, seeded):
    resp = client.get(f"{URL}?category=Roads&sort=priority&order=desc",
                      headers=auth(seeded["admin"]))
    assert ids(resp) == ["SCMS-2026-00003", "SCMS-2026-00001"]  # High before Low


# ---- officers list + page -----------------------------------------------------------

def test_officer_list_contains_only_officers(client, seeded):
    resp = client.get("/api/v1/admin/officers", headers=auth(seeded["admin"]))
    assert resp.status_code == 200
    assert [o["name"] for o in resp.get_json()["items"]] == ["officer"]


def test_officer_list_forbidden_for_citizen(client, seeded):
    resp = client.get("/api/v1/admin/officers", headers=auth(seeded["a"]))
    assert resp.status_code == 403


def test_dashboard_page_renders(client):
    resp = client.get("/admin")
    assert resp.status_code == 200
    assert b'name="viewport"' in resp.data
