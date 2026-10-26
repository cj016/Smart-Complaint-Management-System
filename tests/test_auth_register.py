from datetime import timedelta

from app.extensions import db
from app.models import User
from app.models.user import OtpCode
from app.utils import utcnow

URL = "/api/v1/auth"
NEW_USER = {"name": "Test", "email": "t@x.com", "password": "Secret123!"}


def test_register_success(client):
    r = client.post(f"{URL}/register", json=NEW_USER)
    assert r.status_code == 201
    assert User.query.filter_by(email="t@x.com").first().is_verified is False


def test_register_duplicate_email(client):
    client.post(f"{URL}/register", json=NEW_USER)
    r = client.post(f"{URL}/register", json=NEW_USER)
    assert r.status_code == 409


def test_register_rejects_short_password(client):
    r = client.post(f"{URL}/register", json={**NEW_USER, "password": "short"})
    assert r.status_code == 400


def test_register_ignores_role_in_request(client):
    client.post(f"{URL}/register", json={**NEW_USER, "role": "Admin"})
    assert User.query.filter_by(email="t@x.com").first().role == "Complainant"


def test_verify_wrong_otp(client):
    client.post(f"{URL}/register", json=NEW_USER)
    r = client.post(f"{URL}/verify-otp", json={"email": "t@x.com", "otp": "000000"})
    assert r.status_code == 400


def test_verify_expired_otp(client):
    client.post(f"{URL}/register", json=NEW_USER)
    otp = OtpCode.query.first()
    otp.expires_at = utcnow() - timedelta(minutes=1)
    db.session.commit()
    r = client.post(f"{URL}/verify-otp", json={"email": "t@x.com", "otp": "123456"})
    assert r.status_code == 400