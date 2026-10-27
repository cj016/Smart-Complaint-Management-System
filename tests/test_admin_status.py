"""SCMS-F-033: update status with resolution remarks."""
import pytest

from app.models import Role
from tests.admin_helpers import auth, make_complaint, make_user, reload


@pytest.fixture()
def people(app):
    return {
        "admin": make_user("admin@example.com", Role.ADMIN),
        "officer": make_user("officer@example.com", Role.OFFICER, name="Ravi"),
        "other_officer": make_user("o2@example.com", Role.OFFICER, name="Meena"),
        "citizen": make_user("citizen@example.com"),
    }


def update(client, who, status, remarks=None, public_id="SCMS-2026-00001"):
    body = {"status": status}
    if remarks is not None:
        body["remarks"] = remarks
    return client.patch(f"/api/v1/admin/complaints/{public_id}/status",
                        headers=auth(who), json=body)


def test_requires_login(client):
    resp = client.patch("/api/v1/admin/complaints/SCMS-2026-00001/status",
                        json={"status": "In Review"})
    assert resp.status_code == 401


def test_citizen_is_forbidden(client, people):
    make_complaint(people["citizen"], 1)
    assert update(client, people["citizen"], "In Review").status_code == 403


def test_admin_moves_submitted_to_in_review(client, people):
    make_complaint(people["citizen"], 1)
    resp = update(client, people["admin"], "In Review", "Looking into it")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "In Review"
    c = reload("SCMS-2026-00001")
    assert [h.status for h in c.history] == ["Submitted", "In Review"]
    assert c.history[-1].remarks == "Looking into it"
    assert c.history[-1].changed_by_id == people["admin"].id


def test_assigned_officer_can_start_work(client, people):
    make_complaint(people["citizen"], 1, status="Assigned", assignee=people["officer"])
    resp = update(client, people["officer"], "In Progress")
    assert resp.status_code == 200
    assert resp.get_json()["nextStatuses"] == ["Resolved"]


def test_officer_cannot_touch_someone_elses_complaint(client, people):
    make_complaint(people["citizen"], 1, status="Assigned", assignee=people["officer"])
    resp = update(client, people["other_officer"], "In Progress")
    assert resp.status_code == 403
    assert reload("SCMS-2026-00001").status == "Assigned"


def test_resolve_needs_remarks(client, people):
    make_complaint(people["citizen"], 1, status="In Progress", assignee=people["officer"])
    for remarks in (None, "", "   "):
        resp = update(client, people["officer"], "Resolved", remarks)
        assert resp.status_code == 422
        assert resp.get_json()["error"]["details"]["field"] == "remarks"
    assert reload("SCMS-2026-00001").status == "In Progress"


def test_resolve_saves_remarks_and_time(client, people):
    make_complaint(people["citizen"], 1, status="In Progress", assignee=people["officer"])
    resp = update(client, people["officer"], "Resolved", "  Pothole filled  ")
    assert resp.status_code == 200
    c = reload("SCMS-2026-00001")
    assert c.status == "Resolved"
    assert c.resolution_remarks == "Pothole filled"
    assert c.resolved_at is not None
    assert c.history[-1].remarks == "Pothole filled"


def test_resolved_can_be_closed(client, people):
    make_complaint(people["citizen"], 1, status="Resolved", assignee=people["officer"])
    assert update(client, people["admin"], "Closed").status_code == 200
    assert reload("SCMS-2026-00001").status == "Closed"


@pytest.mark.parametrize("current,target", [
    ("Submitted", "Resolved"),     # cannot skip steps
    ("In Progress", "Submitted"),  # cannot go backwards
    ("Closed", "In Progress"),     # closed is final
    ("Submitted", "Assigned"),     # Assigned comes from the assign endpoint
    ("In Progress", "Reopened"),   # Reopened is the citizen's action (F-024)
])
def test_invalid_transition_is_409(client, people, current, target):
    make_complaint(people["citizen"], 1, status=current, assignee=people["officer"])
    resp = update(client, people["admin"], target, "note")
    assert resp.status_code == 409
    assert resp.get_json()["error"]["code"] == "CONFLICT"
    assert reload("SCMS-2026-00001").status == current


def test_unknown_status_is_422(client, people):
    make_complaint(people["citizen"], 1)
    assert update(client, people["admin"], "Flying").status_code == 422


def test_remarks_too_long_is_422(client, people):
    make_complaint(people["citizen"], 1)
    assert update(client, people["admin"], "In Review", "x" * 2001).status_code == 422


def test_remarks_must_be_text(client, people):
    make_complaint(people["citizen"], 1)
    resp = client.patch("/api/v1/admin/complaints/SCMS-2026-00001/status",
                        headers=auth(people["admin"]),
                        json={"status": "In Review", "remarks": 123})
    assert resp.status_code == 422


def test_unknown_complaint_is_404(client, people):
    assert update(client, people["admin"], "In Review",
                  public_id="SCMS-2026-09999").status_code == 404
