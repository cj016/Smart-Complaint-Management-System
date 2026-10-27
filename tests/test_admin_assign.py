"""SCMS-F-030 (TC-Admin-01): an admin assigns a complaint to an officer."""
import pytest

from app.models import Role
from tests.admin_helpers import auth, make_complaint, make_user, reload


@pytest.fixture()
def people(app):
    return {
        "admin": make_user("admin@example.com", Role.ADMIN),
        "officer": make_user("officer@example.com", Role.OFFICER, name="Ravi",
                             department="Roads Dept"),
        "other_officer": make_user("o2@example.com", Role.OFFICER, name="Meena",
                                   department="Sanitation Dept"),
        "citizen": make_user("citizen@example.com"),
    }


def assign(client, who, officer_id, public_id="SCMS-2026-00001", **extra):
    return client.post(f"/api/v1/admin/complaints/{public_id}/assign", headers=auth(who),
                       json={"officerId": officer_id, **extra})


def test_requires_login(client):
    resp = client.post("/api/v1/admin/complaints/SCMS-2026-00001/assign", json={})
    assert resp.status_code == 401


def test_admin_assigns_and_status_becomes_assigned(client, people):
    make_complaint(people["citizen"], 1)
    resp = assign(client, people["admin"], people["officer"].id)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "Assigned"
    assert body["assignedTo"] == {"id": people["officer"].id, "name": "Ravi"}
    assert body["department"] == "Roads Dept"  # taken from the officer

    c = reload("SCMS-2026-00001")
    assert c.assigned_to_id == people["officer"].id
    assert [h.status for h in c.history] == ["Submitted", "Assigned"]
    assert c.history[-1].changed_by_id == people["admin"].id


def test_assign_from_in_review(client, people):
    make_complaint(people["citizen"], 1, status="In Review")
    assert assign(client, people["admin"], people["officer"].id).get_json()["status"] == \
        "Assigned"


def test_department_can_be_overridden(client, people):
    make_complaint(people["citizen"], 1)
    resp = assign(client, people["admin"], people["officer"].id, department="Drainage")
    assert resp.get_json()["department"] == "Drainage"


def test_reassign_keeps_status_and_changes_officer(client, people):
    make_complaint(people["citizen"], 1, status="In Progress",
                   assignee=people["officer"])
    resp = assign(client, people["admin"], people["other_officer"].id)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "In Progress"
    assert body["assignedTo"]["name"] == "Meena"


def test_officer_cannot_assign(client, people):
    make_complaint(people["citizen"], 1)
    assert assign(client, people["officer"], people["officer"].id).status_code == 403


def test_citizen_cannot_assign(client, people):
    make_complaint(people["citizen"], 1)
    assert assign(client, people["citizen"], people["officer"].id).status_code == 403
    assert reload("SCMS-2026-00001").assigned_to_id is None


def test_unknown_complaint_is_404(client, people):
    resp = assign(client, people["admin"], people["officer"].id, "SCMS-2026-09999")
    assert resp.status_code == 404
    assert resp.get_json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.parametrize("bad", [None, "abc", True, 99999, 1.5])
def test_bad_officer_id_is_422(client, people, bad):
    make_complaint(people["citizen"], 1)
    resp = assign(client, people["admin"], bad)
    assert resp.status_code == 422
    assert "officerId" in resp.get_json()["error"]["details"]["fields"]


def test_cannot_assign_to_a_citizen_or_admin(client, people):
    make_complaint(people["citizen"], 1)
    for target in (people["citizen"], people["admin"]):
        assert assign(client, people["admin"], target.id).status_code == 422


@pytest.mark.parametrize("status", ["Resolved", "Closed"])
def test_finished_complaint_cannot_be_assigned(client, people, status):
    make_complaint(people["citizen"], 1, status=status)
    resp = assign(client, people["admin"], people["officer"].id)
    assert resp.status_code == 409
    assert resp.get_json()["error"]["code"] == "CONFLICT"


def test_empty_body_is_422(client, people):
    make_complaint(people["citizen"], 1)
    resp = client.post("/api/v1/admin/complaints/SCMS-2026-00001/assign",
                       headers=auth(people["admin"]))
    assert resp.status_code == 422
