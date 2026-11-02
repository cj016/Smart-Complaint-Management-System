from unittest.mock import patch

from app.extensions import db


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["database"] == "up"


def test_health_reports_db_down(client):
    with patch.object(db.session, "execute", side_effect=Exception("db down")):
        r = client.get("/health")
    assert r.status_code == 503
    assert r.get_json()["status"] == "degraded"