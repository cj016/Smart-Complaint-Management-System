"""SCMS-F-022 (TC-Track-03): view the status timeline of a complaint."""
from datetime import timedelta

import pytest

from app.models import Role, StatusHistory
from app.extensions import db
from app.utils import utcnow
from tests.admin_helpers import auth, make_complaint, make_user


@pytest.fixture()
def people(app):
    return {
        "a": make_user("a@example.com"),
        "b": make_user("b@example.com"),
        "officer": make_user("officer@example.com", Role.OFFICER, name="Ravi"),
        "admin": make_user("admin@example.com", Role.ADMIN),
    }


def timeline(client, who, public_id="SCMS-2026-00042"):
    return client.get(f"/api/v1/tracking/by-id/{public_id}/timeline", headers=auth(who))


@pytest.fixture()
def complaint(people):
    c = make_complaint(people["a"], 42, status="Resolved")
    base = c.created_at
    # added out of order on purpose: the API must sort them by time
    for minutes, status, remarks in ((30, "Resolved", "Fixed"), (10, "In Review", None),
                                     (20, "Assigned", "Assigned to Ravi")):
        db.session.add(StatusHistory(complaint_id=c.id, status=status, remarks=remarks,
                                     changed_by_id=people["officer"].id,
                                     changed_at=base + timedelta(minutes=minutes)))
    db.session.commit()
    return c


def test_requires_login(client):
    resp = client.get("/api/v1/tracking/by-id/SCMS-2026-00042/timeline")
    assert resp.status_code == 401


def test_owner_sees_steps_oldest_first(client, people, complaint):
    resp = timeline(client, people["a"])
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["complaintId"] == "SCMS-2026-00042"
    assert body["currentStatus"] == "Resolved"
    assert [s["status"] for s in body["steps"]] == [
        "Submitted", "In Review", "Assigned", "Resolved"]
    assert body["steps"][2]["remarks"] == "Assigned to Ravi"
    assert body["steps"][3]["remarks"] == "Fixed"


def test_steps_show_role_not_staff_name(client, people, complaint):
    steps = timeline(client, people["a"]).get_json()["steps"]
    assert steps[0]["changedByRole"] == "Complainant"
    assert steps[1]["changedByRole"] == "Officer"
    assert "Ravi" not in str(steps[1]) and "changedBy" not in steps[1]


def test_step_has_expected_fields(client, people, complaint):
    step = timeline(client, people["a"]).get_json()["steps"][0]
    assert set(step) == {"status", "remarks", "changedAt", "changedByRole"}
    assert step["changedAt"].endswith("Z")


def test_other_citizen_gets_404(client, people, complaint):
    assert timeline(client, people["b"]).status_code == 404


@pytest.mark.parametrize("who", ["officer", "admin"])
def test_staff_can_view_any_timeline(client, people, complaint, who):
    assert timeline(client, people[who]).status_code == 200


def test_id_is_case_insensitive(client, people, complaint):
    assert timeline(client, people["a"], "scms-2026-00042").status_code == 200


def test_unknown_id_is_404(client, people):
    resp = timeline(client, people["a"], "SCMS-2026-09999")
    assert resp.status_code == 404
    assert resp.get_json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.parametrize("bad", ["12345", "SCMS-26-1", "DROP-TABLE"])
def test_bad_format_is_422(client, people, bad):
    assert timeline(client, people["a"], bad).status_code == 422


def test_entry_without_actor_is_labelled_system(client, people):
    c = make_complaint(people["a"], 42)
    db.session.add(StatusHistory(complaint_id=c.id, status="In Review",
                                 changed_at=utcnow() + timedelta(hours=1)))
    db.session.commit()
    steps = timeline(client, people["a"]).get_json()["steps"]
    assert steps[-1]["changedByRole"] == "System"


def test_track_page_has_timeline_list(client):
    html = client.get("/track").get_data(as_text=True)
    assert 'id="timeline"' in html
