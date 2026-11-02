"""Smoke test the disposable demonstration through real login and API requests."""
from scripts.demo_harsh_tasks import DEMO_PASSWORD, build_demo


def test_demo_login_actions_and_reports():
    app = build_demo()
    client = app.test_client()
    citizen = client.post("/api/v1/auth/login", json={
        "email": "citizen@scms.example", "password": DEMO_PASSWORD})
    assert citizen.status_code == 200
    headers = {"Authorization": "Bearer " + citizen.json["access_token"]}
    base = "/api/v1/tracking/by-id/SCMS-2026-00001"
    assert client.post(base + "/feedback", headers=headers,
                       json={"rating": 4, "comment": "Demo check"}).status_code == 201
    assert client.post(base + "/reopen", headers=headers,
                       json={"reason": "Issue persists"}).status_code == 200
    assert client.get(base + "/timeline", headers=headers).json["currentStatus"] == "Reopened"
    assert client.get("/api/v1/tracking/by-id/SCMS-2026-00004",
                      headers=headers).status_code == 404
    assert client.get("/api/v1/reports", headers=headers).status_code == 403
    admin = client.post("/api/v1/auth/login", json={
        "email": "admin@scms.example", "password": DEMO_PASSWORD})
    headers = {"Authorization": "Bearer " + admin.json["access_token"]}
    response = client.get("/api/v1/reports", headers=headers)
    assert response.status_code == 200 and response.json["totalComplaints"] == 4
    roads = next(item for item in response.json["items"] if item["group"] == "Roads")
    assert roads["open"] == 2 and roads["resolutionRate"] == 0
    assert client.get("/api/v1/reports?format=csv", headers=headers).status_code == 200
    for path in ("/", "/track", "/resolution-actions", "/reports"):
        assert client.get(path).status_code == 200
