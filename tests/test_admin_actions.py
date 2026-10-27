"""Test cases TC-Admin-01 (SCMS-F-030 assign complaint to officer) and TC-Admin-04
(SCMS-F-033 update status with resolution remarks)."""
import pytest
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import Complaint, Role, StatusHistory, User

BASE = "/api/v1/admin/complaints"
CID = "SCMS-2026-00042"


def make_user(email, role, department=None):
    user = User(name=email.split("@")[0], email=email, password_hash="x", role=role,
                is_verified=True, department=department)
    db.session.add(user)
    db.session.commit()
    return user


def auth(user):
    return {"Authorization": f"Bearer {create_access_token(identity=str(user.id))}"}


def make_complaint(owner, status="Submitted", assigned_to=None):
    c = Complaint(public_id=CID, user_id=owner.id, category="Sanitation",
                  description="Overflowing bin", location="5th Cross Road", status=status,
                  assigned_to_id=assigned_to.id if assigned_to else None)
    db.session.add(c)
    db.session.commit()
    return c


def reload_complaint():
    db.session.expire_all()
    return db.session.execute(
        db.select(Complaint).where(Complaint.public_id == CID)).scalar_one()


def history_of(complaint):
    db.session.expire_all()
    return db.session.execute(
        db.select(StatusHistory).where(StatusHistory.complaint_id == complaint.id)
        .order_by(StatusHistory.id)).scalars().all()


@pytest.fixture()
def people(app):
    return {
        "citizen": make_user("citizen@example.com", Role.COMPLAINANT),
        "officer": make_user("officer@example.com", Role.OFFICER, "Sanitation"),
        "officer2": make_user("officer2@example.com", Role.OFFICER, "Roads"),
        "admin": make_user("admin@example.com", Role.ADMIN),
    }


def assign(client, user, body, cid=CID):
    return client.post(f"{BASE}/{cid}/assign", json=body, headers=auth(user))


def set_status(client, user, body, cid=CID):
    return client.post(f"{BASE}/{cid}/status", json=body, headers=auth(user))


# ---- F-030: assign ---------------------------------------------------------------------

def test_assign_requires_login(client, people):
    make_complaint(people["citizen"])
    assert client.post(f"{BASE}/{CID}/assign", json={"officerId": 1}).status_code == 401


@pytest.mark.parametrize("who", ["citizen", "officer"])
def test_only_admin_can_assign(client, people, who):
    make_complaint(people["citizen"])
    resp = assign(client, people[who], {"officerId": people["officer"].id})
    assert resp.status_code == 403


def test_admin_assigns_officer(client, people):
    make_complaint(people["citizen"])
    resp = assign(client, people["admin"], {"officerId": people["officer"].id})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "Assigned"
    assert body["assignedTo"]["id"] == people["officer"].id
    assert body["department"] == "Sanitation"  # defaults to the officer's department

    c = reload_complaint()
    assert c.assigned_to_id == people["officer"].id
    rows = history_of(c)
    assert rows[-1].status == "Assigned"
    assert rows[-1].changed_by_id == people["admin"].id


def test_admin_can_override_department(client, people):
    make_complaint(people["citizen"])
    resp = assign(client, people["admin"],
                  {"officerId": people["officer"].id, "department": "Waste Mgmt"})
    assert resp.get_json()["department"] == "Waste Mgmt"


def test_assign_keeps_status_when_work_already_started(client, people):
    make_complaint(people["citizen"], status="In Progress")
    resp = assign(client, people["admin"], {"officerId": people["officer"].id})
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "In Progress"


@pytest.mark.parametrize("body", [{}, {"officerId": "abc"}, {"officerId": True},
                                  {"officerId": 9999}])
def test_assign_bad_officer_is_422(client, people, body):
    make_complaint(people["citizen"])
    resp = assign(client, people["admin"], body)
    assert resp.status_code == 422
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_cannot_assign_to_a_citizen_or_admin(client, people):
    make_complaint(people["citizen"])
    for target in ("citizen", "admin"):
        resp = assign(client, people["admin"], {"officerId": people[target].id})
        assert resp.status_code == 422


def test_assign_unknown_complaint_is_404(client, people):
    resp = assign(client, people["admin"], {"officerId": people["officer"].id},
                  cid="SCMS-2026-99999")
    assert resp.status_code == 404


def test_cannot_assign_resolved_complaint(client, people):
    make_complaint(people["citizen"], status="Resolved")
    resp = assign(client, people["admin"], {"officerId": people["officer"].id})
    assert resp.status_code == 409


def test_officer_list_is_admin_only(client, people):
    resp = client.get("/api/v1/admin/officers", headers=auth(people["admin"]))
    names = [o["name"] for o in resp.get_json()["items"]]
    assert names == ["officer", "officer2"]
    assert client.get("/api/v1/admin/officers", headers=auth(people["officer"])
                      ).status_code == 403


# ---- F-033: update status with remarks -------------------------------------------------

def test_status_requires_login(client, people):
    make_complaint(people["citizen"])
    assert client.post(f"{BASE}/{CID}/status", json={"status": "In Review"}
                       ).status_code == 401


def test_citizen_cannot_update_status(client, people):
    make_complaint(people["citizen"])
    assert set_status(client, people["citizen"], {"status": "In Review"}).status_code == 403


def test_admin_moves_submitted_to_in_review(client, people):
    c = make_complaint(people["citizen"])
    resp = set_status(client, people["admin"], {"status": "In Review", "remarks": "Checking"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "In Review"
    last = history_of(c)[-1]
    assert (last.status, last.remarks, last.changed_by_id) == (
        "In Review", "Checking", people["admin"].id)


def test_resolving_needs_remarks(client, people):
    make_complaint(people["citizen"], status="In Progress")
    for body in ({"status": "Resolved"}, {"status": "Resolved", "remarks": "   "}):
        resp = set_status(client, people["admin"], body)
        assert resp.status_code == 422
        assert resp.get_json()["error"]["details"]["field"] == "remarks"
    assert reload_complaint().status == "In Progress"


def test_resolving_saves_remarks_and_time(client, people):
    c = make_complaint(people["citizen"], status="In Progress")
    resp = set_status(client, people["admin"],
                      {"status": "Resolved", "remarks": "Bin emptied and cleaned"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "Resolved"
    assert body["resolutionRemarks"] == "Bin emptied and cleaned"
    assert body["resolvedAt"] is not None
    assert history_of(c)[-1].remarks == "Bin emptied and cleaned"
    assert body["allowedStatuses"] == ["Closed"]


def test_unknown_status_is_422(client, people):
    make_complaint(people["citizen"])
    resp = set_status(client, people["admin"], {"status": "Banana"})
    assert resp.status_code == 422


@pytest.mark.parametrize("current,target", [("Submitted", "Resolved"),
                                            ("Closed", "Reopened"),
                                            ("Submitted", "Assigned"),
                                            ("Resolved", "In Progress")])
def test_invalid_transition_is_409(client, people, current, target):
    make_complaint(people["citizen"], status=current)
    resp = set_status(client, people["admin"], {"status": target, "remarks": "x"})
    assert resp.status_code == 409
    assert resp.get_json()["error"]["code"] == "CONFLICT"
    assert reload_complaint().status == current


def test_officer_can_update_own_complaint(client, people):
    make_complaint(people["citizen"], status="Assigned", assigned_to=people["officer"])
    resp = set_status(client, people["officer"], {"status": "In Progress"})
    assert resp.status_code == 200


def test_officer_cannot_update_someone_elses_complaint(client, people):
    make_complaint(people["citizen"], status="Assigned", assigned_to=people["officer2"])
    resp = set_status(client, people["officer"], {"status": "In Progress"})
    assert resp.status_code == 403
    assert reload_complaint().status == "Assigned"


def test_full_workflow(client, people):
    c = make_complaint(people["citizen"])
    admin = people["admin"]
    assert set_status(client, admin, {"status": "In Review"}).status_code == 200
    assert assign(client, admin, {"officerId": people["officer"].id}).status_code == 200
    assert set_status(client, people["officer"], {"status": "In Progress"}).status_code == 200
    assert set_status(client, people["officer"],
                      {"status": "Resolved", "remarks": "Fixed"}).status_code == 200
    assert set_status(client, admin, {"status": "Closed"}).status_code == 200
    assert [h.status for h in history_of(c)] == [
        "In Review", "Assigned", "In Progress", "Resolved", "Closed"]
