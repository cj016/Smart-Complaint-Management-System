from app.extensions import db
from app.models.user import User

MOBILE = "9876543210"


def _register(client, email="p@x.com", mobile=MOBILE):
    return client.post("/api/v1/auth/register", json={
        "name": "P", "email": email, "mobile": mobile, "password": "Passw0rd!x"})


def test_mobile_encrypted_in_database(client):
    assert _register(client).status_code == 201
    raw = db.session.execute(
        db.text("SELECT mobile FROM users WHERE email = :e"), {"e": "p@x.com"}
    ).scalar()
    assert raw is not None and MOBILE not in raw


def test_mobile_decrypts_through_orm(client):
    _register(client)
    assert User.query.filter_by(email="p@x.com").first().mobile == MOBILE


def test_duplicate_mobile_rejected(client):
    assert _register(client).status_code == 201
    assert _register(client, email="q@x.com").status_code == 409