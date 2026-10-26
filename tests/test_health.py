def test_health_ok(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_every_module_stub_is_wired(client):
    for prefix in ["auth", "complaints", "tracking", "admin", "notifications", "reports"]:
        resp = client.get(f"/api/v1/{prefix}/ping")
        assert resp.status_code == 200, prefix


def test_unknown_api_route_uses_standard_error_format(client):
    resp = client.get("/api/v1/does-not-exist")
    assert resp.status_code == 404
    err = resp.get_json()["error"]
    assert set(err) == {"code", "message", "details"}
    assert err["code"] == "NOT_FOUND"
