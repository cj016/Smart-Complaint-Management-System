from app.extensions import db
from app.models import User

URL = "/api/v1/auth"


def make_user(verified=True):
    u = User(name="T", email="t@x.com", role="Complainant", is_verified=verified)
    u.set_password("Secret123!")
    db.session.add(u)
    db.session.commit()
    return u


def test_login_success_returns_token(client):
    make_user()
    r = client.post(f"{URL}/login", json={"email": "t@x.com", "password": "Secret123!"})
    assert r.status_code == 200
    assert "access_token" in r.get_json()


def test_login_wrong_password(client):
    make_user()
    r = client.post(f"{URL}/login", json={"email": "t@x.com", "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_email_same_error(client):
    make_user()
    wrong_pw = client.post(f"{URL}/login", json={"email": "t@x.com", "password": "wrong"})
    no_user = client.post(f"{URL}/login", json={"email": "no@x.com", "password": "x"})
    assert wrong_pw.get_json() == no_user.get_json()


def test_login_unverified_user_blocked(client):
    make_user(verified=False)
    r = client.post(f"{URL}/login", json={"email": "t@x.com", "password": "Secret123!"})
    assert r.status_code == 403