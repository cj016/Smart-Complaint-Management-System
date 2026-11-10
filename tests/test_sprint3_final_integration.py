"""Final Sprint 3 site-shell smoke and permission regression tests.

These are Flask test-client checks; a real browser test is separately required.
"""

from pathlib import Path
import pytest
from app.extensions import db
from app.models import Role, User


@pytest.mark.parametrize("url", [
    "/", "/login", "/register", "/my-complaints", "/lodge",
    "/track", "/admin", "/notifications", "/staff-notifications",
    "/feedback", "/admin/feedback", "/admin/reports",
])
def test_all_site_pages_render(client, url):
    response = client.get(url)
    assert response.status_code == 200
    assert b'name="viewport"' in response.data


def test_unified_login_preserves_original_contract(client):
    html = client.get("/login").get_data(as_text=True)
    for item in (
        'id="login-form"', 'name="email"', 'name="password"',
        'id="message"', 'id="login-citizen"', 'id="login-staff"',
        'js/login.js', 'js/login_mode.js', 'href="/register"',
    ):
        assert item in html
    assert "admin@scms.test" not in html  # do not expose credentials in markup


def test_root_entry_script_is_present(client):
    html = client.get("/").get_data(as_text=True)
    assert 'js/entry.js' in html
    entry = client.get("/static/js/entry.js").get_data(as_text=True)
    assert 'window.location.replace("/login")' in entry
    assert 'window.location.replace("/my-complaints")' in entry
    assert 'window.location.replace("/admin")' in entry


def test_fixed_admin_is_not_a_backdoor(client):
    # A fixed email must still authenticate with a real password hash.
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@scms.test", "password": "incorrect",
    })
    assert response.status_code in (401, 423)  # lockout may affect a seeded account


def test_citizens_cannot_become_admins_on_registration(client):
    response = client.post("/api/v1/auth/register", json={
        "name": "New Citizen", "email": "fresh-citizen@integration.test",
        "password": "Example12345!", "role": Role.ADMIN,
    })
    assert response.status_code == 201
    person = db.session.scalar(db.select(User).where(
        User.email == "fresh-citizen@integration.test"))
    assert person.role == Role.COMPLAINANT


def test_status_actions_have_valid_user_journey(client):
    html = client.get("/my-complaints").get_data(as_text=True)
    assert 'id="reopen-form"' in html
    html = client.get("/admin").get_data(as_text=True)
    for value in ('id="assign-form"', 'id="reassign-form"',
                  'id="status-form"', 'id="escalate-btn"'):
        assert value in html
    script = client.get("/static/js/my_complaints.js").get_data(as_text=True)
    assert '"/track?complaintId="' in script
    assert '"/feedback?complaintId="' in script


def test_admin_and_reports_require_staff_token(client):
    assert client.get("/api/v1/admin/complaints").status_code == 401
    assert client.get("/api/v1/reports/summary").status_code == 401


def test_final_alignment_and_assets(client):
    citizen = client.get("/my-complaints").get_data(as_text=True)
    admin = client.get("/admin").get_data(as_text=True)
    tracking = client.get("/track").get_data(as_text=True)
    login = client.get("/login").get_data(as_text=True)

    assert 'class="scms-pagination"' in citizen
    assert 'class="scms-pagination"' in admin
    assert 'id="timeline"' in tracking
    assert "js/login_mode.js" in login

    source = Path("app/static/js/login_mode.js").read_text(
        encoding="utf-8"
    )
    assert "Admin: use the fixed demo account." not in source

    base = Path("app/templates/base.html").read_text(
        encoding="utf-8"
    )
    if "ui_enhancements.js" in base:
        assert client.get(
            "/static/js/ui_enhancements.js"
        ).status_code == 200
