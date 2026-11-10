"""Sprint 3 regression: citizen-only submission, reopening history and failure isolation."""
from datetime import timedelta
from unittest.mock import patch

import pytest
from app.extensions import db
from app.models import Complaint, Role
from app.utils import utcnow
from tests.admin_helpers import auth, make_complaint, make_user, reload

URL = "/api/v1/complaints"


@pytest.mark.parametrize("role", [Role.ADMIN, Role.OFFICER])
def test_staff_cannot_lodge_citizen_complaint(client, app, role):
    staff = make_user(role.lower() + "-lodge@example.org", role)
    response = client.post(URL, headers=auth(staff), json={
        "category": "Roads", "location": "Main street", "description": "Unsafe road"
    })
    assert response.status_code == 403
    assert db.session.scalar(db.select(db.func.count(Complaint.id))) == 0


def test_citizen_can_still_submit(client, app):
    citizen = make_user("sprint3-citizen@example.org")
    response = client.post(URL, headers=auth(citizen), json={
        "category": "Roads", "location": "Main street", "description": "Unsafe road"
    })
    assert response.status_code == 201


def test_reopen_resets_sla_and_preserves_previous_remarks(client, app):
    citizen = make_user("sprint3-reopen@example.org")
    complaint = make_complaint(citizen, status="Resolved", priority="High")
    complaint.resolution_remarks = "Original fix did not work"
    complaint.resolved_at = utcnow() - timedelta(days=2)
    complaint.sla_due_at = utcnow() - timedelta(days=3)
    db.session.commit()
    before = utcnow()
    response = client.post(URL + "/" + complaint.public_id + "/reopen",
                           headers=auth(citizen), json={"reason": "Problem still exists"})
    assert response.status_code == 200
    saved = reload(complaint.public_id)
    assert saved.status == "Reopened"
    assert saved.resolved_at is None
    assert saved.resolution_remarks == "Original fix did not work"
    assert before + timedelta(hours=47) <= saved.sla_due_at
    assert saved.sla_due_at <= utcnow() + timedelta(hours=49)
    assert saved.history[-1].remarks == "Problem still exists"


def test_notification_failure_does_not_revert_successful_reopen(client, app):
    citizen = make_user("sprint3-failure@example.org")
    make_user("sprint3-admin@example.org", Role.ADMIN)
    complaint = make_complaint(citizen, status="Resolved")
    with patch(
        'app.complaints.routes.create_notification',
        side_effect=RuntimeError('test outage'),
    ):
        response = client.post(URL + "/" + complaint.public_id + "/reopen",
                               headers=auth(citizen), json={"reason": "Still broken"})
    assert response.status_code == 200
    assert reload(complaint.public_id).status == "Reopened"
