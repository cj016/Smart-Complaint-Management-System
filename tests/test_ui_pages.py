import pytest


@pytest.mark.parametrize("path", ["/", "/ui-kit", "/my-complaints"])
def test_pages_render_with_viewport_meta(client, path):
    resp = client.get(path)
    assert resp.status_code == 200
    assert b'name="viewport"' in resp.data  # required for SCMS-NF-004
