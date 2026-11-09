"""Sprint 3 regression tests for malformed login/registration JSON and role security."""
import pytest
from app.models import User


@pytest.mark.parametrize("route", ["register", "verify-otp", "resend-otp", "login"])
@pytest.mark.parametrize("body", [[], [1], "hello", 123, True])
def test_auth_routes_reject_non_object_json(client, route, body):
    response = client.post("/api/v1/auth/" + route, json=body)
    assert response.status_code == 400


@pytest.mark.parametrize("field,value", [
    ("email", 123), ("email", ["a@example.org"]),
    ("mobile", 123), ("mobile", ["1234567890"]),
    ("password", ["not-a-password"]),
])
def test_register_bad_input_does_not_crash(client, field, value):
    body = {"name": "Test", "email": "new@example.org", "password": "Example12345!"}
    body[field] = value
    response = client.post("/api/v1/auth/register", json=body)
    assert response.status_code == 400
    assert User.query.filter_by(email="new@example.org").first() is None


def test_login_bad_email_type_not_500(client):
    response = client.post("/api/v1/auth/login", json={"email": ["wrong"], "password": "x"})
    assert response.status_code == 401
