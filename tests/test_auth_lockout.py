from datetime import timedelta

from app.extensions import db
from app.models import User
from app.utils import utcnow

URL = "/api/v1/auth/login"
GOOD = {"email": "t@x.com", "password": "Secret123!"}
BAD = {"email": "t@x.com", "password": "wrong"}


def make_user():
    u = User(name="T", email="t@x.com", role="Complainant", is_verified=True)
    u.set_password("Secret123!")
    db.session.add(u)
    db.session.commit()
    return u


def test_locks_after_five_failures(client):
    make_user()
    for _ in range(5):
        assert client.post(URL, json=BAD).status_code == 401
    assert client.post(URL, json=GOOD).status_code == 423


def test_four_failures_do_not_lock(client):
    make_user()
    for _ in range(4):
        client.post(URL, json=BAD)
    assert client.post(URL, json=GOOD).status_code == 200


def test_success_resets_counter(client):
    user = make_user()
    for _ in range(4):
        client.post(URL, json=BAD)
    client.post(URL, json=GOOD)
    db.session.refresh(user)
    assert user.failed_login_count == 0


def test_login_works_after_lock_expires(client):
    user = make_user()
    for _ in range(5):
        client.post(URL, json=BAD)
    user.locked_until = utcnow() - timedelta(minutes=1)
    db.session.commit()
    assert client.post(URL, json=GOOD).status_code == 200