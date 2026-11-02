from app.sanitize import clean_text
from app.models.user import User

XSS = "<script>alert(1)</script>Asha"
SQLI = "' OR 1=1--"


def test_clean_text_strips_tags():
    assert "<" not in clean_text(XSS)
    assert clean_text(XSS) == "alert(1)Asha"
    assert clean_text("x" * 500, 120) == "x" * 120


def test_register_strips_html_from_name(client):
    r = client.post("/api/v1/auth/register", json={
        "name": XSS, "email": "xss@x.com", "password": "Passw0rd!x"})
    assert r.status_code == 201
    assert "<" not in User.query.filter_by(email="xss@x.com").first().name


def test_sqli_login_rejected(client):
    r = client.post("/api/v1/auth/login",
                    json={"email": SQLI, "password": SQLI})
    assert r.status_code == 401


def test_security_headers_present(client):
    r = client.get("/api/v1/auth/ping")
    assert "default-src 'self'" in r.headers["Content-Security-Policy"]
    assert r.headers["X-Content-Type-Options"] == "nosniff"