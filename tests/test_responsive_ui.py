"""TC-UX-01 (automated part) - the manual part is checking 360px..1920px in DevTools."""
BADGES = ["submitted", "in-review", "assigned", "in-progress", "resolved", "closed",
          "reopened"]


def test_ui_kit_has_all_seven_status_badges(client):
    html = client.get("/ui-kit").get_data(as_text=True)
    for slug in BADGES:
        assert f"badge-{slug}" in html


def test_stylesheet_defines_badges_and_breakpoints(client):
    css = client.get("/static/css/style.css").get_data(as_text=True)
    for slug in BADGES:
        assert f".badge-{slug}" in css
    assert "@media (min-width: 768px)" in css
    assert "overflow-x: auto" in css
