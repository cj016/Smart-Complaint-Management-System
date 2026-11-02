"""UI-03: My Complaints session integration checks."""

from pathlib import Path


JS_PATH = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "static"
    / "js"
    / "my_complaints.js"
)


def test_my_complaints_page_loads(client):
    response = client.get("/my-complaints")

    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert 'id="login-warning"' in html
    assert 'id="complaints-section"' in html
    assert "js/my_complaints.js" in html


def test_my_complaints_uses_shared_auth_helper():
    js = JS_PATH.read_text(encoding="utf-8")

    assert "SCMS.getToken()" in js
    assert "SCMS.clear()" in js
    assert "localStorage.removeItem" not in js


def test_expired_session_hides_complaints():
    js = JS_PATH.read_text(encoding="utf-8")

    assert "response.status === 401" in js
    assert "handleExpiredSession()" in js
    assert "section.hidden = true" in js
    assert "warning.hidden = false" in js
    assert "tbody.replaceChildren()" in js


def test_error_handling_is_present():
    js = JS_PATH.read_text(encoding="utf-8")

    assert "response.ok" in js
    assert "SCMS.errorText(" in js
    assert "Could not load complaints" in js


def test_filter_and_pagination_preserved():
    js = JS_PATH.read_text(encoding="utf-8")

    assert "status-filter" in js
    assert "prev-btn" in js
    assert "next-btn" in js
    assert "encodeURIComponent(filter.value)" in js
