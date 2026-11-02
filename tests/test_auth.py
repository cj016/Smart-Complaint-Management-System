"""F001 / F002 / SR002 tests. If your conftest.py already has `client`, delete the fixtures here.
Check the config name below matches app/config.py (config_by_name keys)."""
import pytest

from app import create_app
from app.extensions import db
from app.models.user import Role, User


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def make_user(email, role, password="Passw0rd!x"):
    u = User(name="T", email=email, role=role, is_verified=True)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()


def login(client, email, password="Passw0rd!x"):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return r, {"Authorization": f"Bearer {r.get_json().get('access_token', '')}"}


def test_register_verify_login_flow(client):
    r = client.post("/api/v1/auth/register", json={
        "name": "Asha", "email": "a@x.com", "password": "Passw0rd!x"})
    assert r.status_code == 201
    code = r.get_json()["dev_otp"]
    assert login(client, "a@x.com")[0].status_code == 403          # not verified yet
    assert client.post("/api/v1/auth/verify-otp",
                       json={"email": "a@x.com", "otp": code}).status_code == 200
    r, h = login(client, "a@x.com")
    assert r.status_code == 200 and r.get_json()["role"] == Role.COMPLAINANT
    assert client.get("/api/v1/auth/me", headers=h).get_json()["email"] == "a@x.com"
    assert client.post("/api/v1/auth/logout", headers=h).status_code == 200


def test_register_rejects_bad_input_and_duplicates(client):
    bad = {"name": "A", "email": "nope", "password": "short"}
    assert client.post("/api/v1/auth/register", json=bad).status_code == 400
    ok = {"name": "A", "email": "d@x.com", "password": "Passw0rd!x"}
    assert client.post("/api/v1/auth/register", json=ok).status_code == 201
    assert client.post("/api/v1/auth/register", json=ok).status_code == 409


def test_role_cannot_be_self_assigned(client):
    client.post("/api/v1/auth/register", json={
        "name": "A", "email": "r@x.com", "password": "Passw0rd!x", "role": "Admin"})
    assert User.query.filter_by(email="r@x.com").first().role == Role.COMPLAINANT


def test_lockout_after_5_failures(client):
    make_user("l@x.com", Role.COMPLAINANT)
    for _ in range(5):
        client.post("/api/v1/auth/login", json={"email": "l@x.com", "password": "wrong"})
    assert login(client, "l@x.com")[0].status_code == 423


@pytest.mark.parametrize("role,admin_code,staff_code", [
    (Role.COMPLAINANT, 403, 403),
    (Role.OFFICER, 403, 200),
    (Role.ADMIN, 200, 200),
])
def test_role_matrix(client, role, admin_code, staff_code):
    make_user("m@x.com", role)
    _, h = login(client, "m@x.com")
    assert client.get("/api/v1/auth/admin-check", headers=h).status_code == admin_code
    assert client.get("/api/v1/auth/staff-check", headers=h).status_code == staff_code


def test_protected_routes_need_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/admin-check").status_code == 401
