"""Sprint 3 browser-shell coverage of Admin-only reassign and SLA actions."""
from pathlib import Path


def test_admin_dashboard_has_reassignment_and_escalation_form(client):
    response = client.get("/admin")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for item in ('id="reassign-form"', 'id="reassign-officer-select"',
                 'id="reassign-reason"', 'id="escalate-btn"',
                 'data-roles="Admin"'):
        assert item in html


def test_admin_script_binds_existing_api_actions():
    root = Path(__file__).resolve().parents[1]
    script = (root / "app/static/js/admin_dashboard.js").read_text()
    assert '/reassign' in script
    assert '/escalate-overdue' in script
    assert 'if (!isAdmin)' in script
