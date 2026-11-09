"""Task 1 regression: login responses and server-side staff access rules."""
from datetime import timedelta
from pathlib import Path

import pytest

from app.extensions import db
from app.models import Role, User
from app.utils import utcnow

LOGIN = "/api/v1/auth/login"


def create_person(role, verified=True):
    user = User(name="Demo", email=f"{role.lower()}@example.com", role=role,
                is_verified=verified)
    user.set_password("TestPassword123!")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.mark.parametrize("role", [Role.COMPLAINANT, Role.OFFICER, Role.ADMIN])
def test_login_returns_correct_role_and_staff_permissions(client, role):
    user = create_person(role)
    response = client.post(LOGIN, json={"email": user.email,
                                        "password": "TestPassword123!"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["role"] == role
    headers = {"Authorization": "Bearer " + body["access_token"]}

    dashboard = client.get("/api/v1/admin/complaints", headers=headers)
    expected = 403 if role == Role.COMPLAINANT else 200
    assert dashboard.status_code == expected
    admin_only = client.get("/api/v1/auth/admin-check", headers=headers)
    assert admin_only.status_code == (200 if role == Role.ADMIN else 403)


def test_register_cannot_create_admin_or_officer(client):
    for role in (Role.ADMIN, Role.OFFICER):
        response = client.post("/api/v1/auth/register", json={
            "name": "Demo", "email": f"new-{role.lower()}@example.com",
            "password": "TestPassword123!", "role": role,
        })
        assert response.status_code == 201
        user = User.query.filter_by(email=f"new-{role.lower()}@example.com").one()
        assert user.role == Role.COMPLAINANT


@pytest.mark.parametrize("role", [Role.OFFICER, Role.ADMIN])
def test_locked_staff_token_cannot_access_dashboard_or_profile(client, role):
    user = create_person(role)
    response = client.post(LOGIN, json={"email": user.email,
                                        "password": "TestPassword123!"})
    token = response.get_json()["access_token"]
    user.locked_until = utcnow() + timedelta(minutes=15)
    db.session.commit()
    headers = {"Authorization": "Bearer " + token}
    assert client.get("/api/v1/admin/complaints", headers=headers).status_code == 423
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 423


def test_unverified_staff_token_cannot_access_dashboard(client):
    user = create_person(Role.ADMIN)
    response = client.post(LOGIN, json={"email": user.email,
                                        "password": "TestPassword123!"})
    token = response.get_json()["access_token"]
    user.is_verified = False
    db.session.commit()
    headers = {"Authorization": "Bearer " + token}
    assert client.get("/api/v1/admin/complaints", headers=headers).status_code == 403
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 403


def test_client_side_role_routes_are_kept_in_sync():
    root = Path(__file__).resolve().parents[1]
    login_js = (root / "app/static/js/login.js").read_text()
    dashboard_js = (root / "app/static/js/admin_dashboard.js").read_text()
    auth_js = (root / "app/static/js/auth.js").read_text()
    assert 'Officer: "/admin"' in login_js
    assert 'Admin: "/admin"' in login_js
    assert 'Complainant: "/my-complaints"' in login_js
    assert dashboard_js.count('var isAdmin =') == 1
    assert "SCMS.authFetch(API + path" in dashboard_js
    assert 'function logout() {' in auth_js
    assert 'window.location.href = "/login"' in auth_js
