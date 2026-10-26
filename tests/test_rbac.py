from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import User

URL = "/api/v1/auth"


def header_for(role, email):
    u = User(name="T", email=email, role=role, is_verified=True)
    u.set_password("Secret123!")
    db.session.add(u)
    db.session.commit()
    token = create_access_token(identity=str(u.id))
    return {"Authorization": f"Bearer {token}"}


def test_no_token_is_401(client):
    assert client.get(f"{URL}/admin-check").status_code == 401


def test_complainant_forbidden_on_admin_route(client):
    h = header_for("Complainant", "c@x.com")
    assert client.get(f"{URL}/admin-check", headers=h).status_code == 403


def test_officer_forbidden_on_admin_route(client):
    h = header_for("Officer", "o@x.com")
    assert client.get(f"{URL}/admin-check", headers=h).status_code == 403


def test_admin_allowed_on_admin_route(client):
    h = header_for("Admin", "a@x.com")
    assert client.get(f"{URL}/admin-check", headers=h).status_code == 200


def test_officer_and_admin_allowed_on_staff_route(client):
    for role, email in (("Officer", "o@x.com"), ("Admin", "a@x.com")):
        h = header_for(role, email)
        assert client.get(f"{URL}/staff-check", headers=h).status_code == 200


def test_complainant_forbidden_on_staff_route(client):
    h = header_for("Complainant", "c@x.com")
    assert client.get(f"{URL}/staff-check", headers=h).status_code == 403


def test_register_cannot_choose_role(client):
    r = client.post(f"{URL}/register", json={
        "name": "X", "email": "x@x.com", "password": "Secret123!", "role": "Admin"})
    assert r.status_code == 201
    assert User.query.filter_by(email="x@x.com").first().role == "Complainant"