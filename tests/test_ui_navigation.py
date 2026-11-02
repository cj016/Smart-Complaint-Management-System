"""UI-02: Navigation integration tests."""

import pytest


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/login",
        "/register",
        "/lodge",
        "/my-complaints",
        "/track",
        "/admin",
    ],
)
def test_pages_render(client, path):
    response = client.get(path)
    assert response.status_code == 200


def test_only_one_main_navigation(client):
    html = client.get("/").get_data(as_text=True)

    assert html.count("<nav") == 1
    assert 'aria-label="Main navigation"' in html


def test_navigation_contains_required_links(client):
    html = client.get("/").get_data(as_text=True)

    for path in [
        "/login",
        "/register",
        "/lodge",
        "/my-complaints",
        "/track",
        "/admin",
    ]:
        assert f'href="{path}"' in html


def test_navigation_has_correct_roles(client):
    html = client.get("/").get_data(as_text=True)

    assert 'data-roles="Complainant"' in html
    assert 'data-roles="Admin,Officer"' in html
    assert 'data-auth="out"' in html
    assert 'data-auth="in"' in html


def test_no_broken_officer_link(client):
    html = client.get("/").get_data(as_text=True)

    assert 'href="/officer"' not in html


def test_authentication_script_loaded(client):
    html = client.get("/").get_data(as_text=True)

    assert "js/auth.js" in html
    assert 'id="logout-btn"' in html


def test_hidden_navigation_css(client):
    response = client.get("/static/css/style.css")
    assert response.status_code == 200

    css = response.get_data(as_text=True)

    assert "[hidden]" in css
    assert "display: none !important" in css
    assert "@media (max-width: 599px)" in css
