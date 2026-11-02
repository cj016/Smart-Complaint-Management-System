"""SCMS-F-034 (TC-Admin-05): complaints past their SLA are escalated automatically."""
from datetime import timedelta

import pytest

from app.admin.services import escalate_overdue
from app.models import Role
from app.utils import utcnow
from tests.admin_helpers import auth, make_complaint, make_user, reload


@pytest.fixture()
def people(app):
    return {
        "admin": make_user("admin@example.com", Role.ADMIN),
        "officer": make_user("officer@example.com", Role.OFFICER),
        "citizen": make_user("citizen@example.com"),
    }


def overdue():
    return utcnow() - timedelta(hours=1)


def test_overdue_complaint_priority_goes_up_and_is_logged(app, people):
    make_complaint(people["citizen"], 1, priority="Medium", sla_due_at=overdue())
    result = escalate_overdue()
    assert result == [{"complaintId": "SCMS-2026-00001", "from": "Medium", "to": "High"}]
    c = reload("SCMS-2026-00001")
    assert c.priority == "High"
    assert c.sla_due_at > utcnow()  # SLA clock restarted
    assert "Escalated" in c.history[-1].remarks


def test_complaint_not_yet_due_is_untouched(app, people):
    make_complaint(people["citizen"], 1, sla_due_at=utcnow() + timedelta(hours=5))
    assert escalate_overdue() == []
    assert reload("SCMS-2026-00001").priority == "Medium"


def test_resolved_and_closed_complaints_are_ignored(app, people):
    make_complaint(people["citizen"], 1, status="Resolved", sla_due_at=overdue())
    make_complaint(people["citizen"], 2, status="Closed", sla_due_at=overdue())
    assert escalate_overdue() == []


def test_same_complaint_is_not_escalated_twice_in_a_row(app, people):
    make_complaint(people["citizen"], 1, sla_due_at=overdue())
    assert len(escalate_overdue()) == 1
    assert escalate_overdue() == []
    assert reload("SCMS-2026-00001").priority == "High"


def test_priority_stops_at_critical(app, people):
    make_complaint(people["citizen"], 1, priority="Critical", sla_due_at=overdue())
    escalate_overdue()
    assert reload("SCMS-2026-00001").priority == "Critical"


def test_without_sla_due_at_the_priority_sla_hours_are_used(app, people):
    make_complaint(people["citizen"], 1, priority="Low")
    assert escalate_overdue() == []  # just created
    result = escalate_overdue(now=utcnow() + timedelta(hours=121))  # Low SLA is 120 h
    assert result[0]["to"] == "Medium"


def post(client, who=None):
    headers = auth(who) if who else {}
    return client.post("/api/v1/admin/escalate-overdue", headers=headers)


def test_endpoint_requires_login(client):
    assert post(client).status_code == 401


def test_endpoint_is_admin_only(client, people):
    assert post(client, people["citizen"]).status_code == 403
    assert post(client, people["officer"]).status_code == 403


def test_admin_runs_escalation_through_the_api(client, people):
    make_complaint(people["citizen"], 1, sla_due_at=overdue())
    resp = post(client, people["admin"])
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["escalatedCount"] == 1
    assert body["items"][0]["to"] == "High"
