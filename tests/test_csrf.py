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


def _login(client):
    u = User(name="T", email="c@x.com", role=Role.COMPLAINANT, is_verified=True)
    u.set_password("Passw0rd!x")
    db.session.add(u)
    db.session.commit()
    r = client.post("/api/v1/auth/login",
                    json={"email": "c@x.com", "password": "Passw0rd!x"})
    return r, r.get_json()["access_token"]


def test_login_sets_no_cookies(client):
    r, _ = _login(client)
    assert "Set-Cookie" not in r.headers


def test_cookie_token_is_not_accepted(client):
    _, token = _login(client)
    client.set_cookie("access_token_cookie", token)
    assert client.post("/api/v1/auth/logout").status_code == 401


def test_state_change_needs_bearer_header(client):
    assert client.post("/api/v1/auth/logout").status_code == 401


def test_cors_blocks_foreign_origin(client):
    r = client.get("/api/v1/auth/ping", headers={"Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in r.headers


def test_cors_allows_own_origin(client):
    r = client.get("/api/v1/auth/ping", headers={"Origin": "http://localhost:5000"})
    assert r.headers.get("Access-Control-Allow-Origin") == "http://localhost:5000"