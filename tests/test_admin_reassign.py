"""SCMS-F-035 (TC-Admin-06): an admin reassigns a complaint to a different officer/dept."""
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


def reassign(client, who, officer_id, public_id="SCMS-2026-00001", **extra):
    return client.post(f"/api/v1/admin/complaints/{public_id}/reassign", headers=auth(who),
                       json={"officerId": officer_id, **extra})


def assigned_complaint(people, status="Assigned", n=1):
    return make_complaint(people["citizen"], n, status=status,
                          assignee=people["officer"], department="Roads Dept")


def test_requires_login(client):
    resp = client.post("/api/v1/admin/complaints/SCMS-2026-00001/reassign", json={})
    assert resp.status_code == 401


def test_only_admin_can_reassign(client, people):
    assigned_complaint(people)
    for who in ("officer", "citizen"):
        resp = reassign(client, people[who], people["other_officer"].id, remarks="x")
        assert resp.status_code == 403


def test_admin_reassigns_to_another_officer(client, people):
    assigned_complaint(people, status="In Progress")
    resp = reassign(client, people["admin"], people["other_officer"].id,
                    remarks="Wrong department")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["assignedTo"] == {"id": people["other_officer"].id, "name": "Meena"}
    assert body["department"] == "Sanitation Dept"
    assert body["status"] == "In Progress"  # status does not change

    c = reload("SCMS-2026-00001")
    assert c.assigned_to_id == people["other_officer"].id
    assert c.history[-1].remarks == "Reassigned: Wrong department"
    assert c.history[-1].changed_by_id == people["admin"].id


def test_department_can_be_overridden(client, people):
    assigned_complaint(people)
    resp = reassign(client, people["admin"], people["other_officer"].id,
                    department="Water Dept", remarks="Needs water team")
    assert resp.get_json()["department"] == "Water Dept"


def test_same_officer_with_new_department_is_allowed(client, people):
    assigned_complaint(people)
    resp = reassign(client, people["admin"], people["officer"].id,
                    department="Water Dept", remarks="Moved department")
    assert resp.status_code == 200
    assert resp.get_json()["department"] == "Water Dept"


def test_same_officer_and_department_is_rejected(client, people):
    assigned_complaint(people)
    resp = reassign(client, people["admin"], people["officer"].id, remarks="No change")
    assert resp.status_code == 409


def test_reason_is_required(client, people):
    assigned_complaint(people)
    for extra in ({}, {"remarks": "   "}, {"remarks": 5}):
        resp = reassign(client, people["admin"], people["other_officer"].id, **extra)
        assert resp.status_code == 422
        assert "remarks" in resp.get_json()["error"]["details"]["fields"]


def test_officer_id_must_be_an_existing_officer(client, people):
    assigned_complaint(people)
    for bad in (None, "abc", True, 9999, people["citizen"].id):
        resp = client.post("/api/v1/admin/complaints/SCMS-2026-00001/reassign",
                           headers=auth(people["admin"]),
                           json={"officerId": bad, "remarks": "x"})
        assert resp.status_code == 422


def test_unassigned_complaint_cannot_be_reassigned(client, people):
    make_complaint(people["citizen"], 1)
    resp = reassign(client, people["admin"], people["officer"].id, remarks="x")
    assert resp.status_code == 409


@pytest.mark.parametrize("status", ["Resolved", "Closed"])
def test_finished_complaints_cannot_be_reassigned(client, people, status):
    assigned_complaint(people, status=status)
    resp = reassign(client, people["admin"], people["other_officer"].id, remarks="x")
    assert resp.status_code == 409


def test_unknown_complaint_is_404(client, people):
    resp = reassign(client, people["admin"], people["officer"].id,
                    public_id="SCMS-2026-09999", remarks="x")
    assert resp.status_code == 404
