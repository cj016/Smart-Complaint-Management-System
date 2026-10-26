"""Test case TC-Lodge-04 (SCMS-F-013): attach up to 3 images, max 5 MB each."""
from io import BytesIO

import pytest
from flask_jwt_extended import create_access_token
from PIL import Image

from app.extensions import db
from app.models import Complaint, ComplaintPhoto, Role, User

MB = 1024 * 1024


def make_user(email, role=Role.COMPLAINANT):
    user = User(name=email.split("@")[0], email=email, password_hash="x", role=role)
    db.session.add(user)
    db.session.commit()
    return user


def make_complaint(user, n=1):
    c = Complaint(public_id=f"SCMS-2026-{n:05d}", user_id=user.id, category="Roads",
                  description="Pothole", location="Main St")
    db.session.add(c)
    db.session.commit()
    return c


def auth(user):
    return {"Authorization": f"Bearer {create_access_token(identity=str(user.id))}"}


def image_bytes(fmt="PNG"):
    buf = BytesIO()
    Image.new("RGB", (8, 8), "red").save(buf, fmt)
    return buf.getvalue()


def files(*items):
    """items: (file name, bytes) pairs -> multipart form body with the 'photos' field."""
    return {"photos": [(BytesIO(data), name) for name, data in items]}


@pytest.fixture()
def upload_dir(app, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    return tmp_path


@pytest.fixture()
def owner(app):
    return make_user("owner@example.com")


@pytest.fixture()
def complaint(owner):
    return make_complaint(owner)


def post(client, user, public_id, body):
    return client.post(f"/api/v1/complaints/{public_id}/photos", data=body,
                       headers=auth(user), content_type="multipart/form-data")


def stored_files(upload_dir):
    return [p for p in upload_dir.rglob("*") if p.is_file()]


# ---- happy path ---------------------------------------------------------------------

def test_requires_login(client, complaint):
    resp = client.post(f"/api/v1/complaints/{complaint.public_id}/photos",
                       data=files(("a.png", image_bytes())),
                       content_type="multipart/form-data")
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_attach_one_photo(client, owner, complaint, upload_dir):
    data = image_bytes()
    resp = post(client, owner, complaint.public_id, files(("evidence.png", data)))
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["complaintId"] == complaint.public_id
    assert body["remaining"] == 2 and body["maxPhotos"] == 3
    photo = body["photos"][0]
    assert photo["originalName"] == "evidence.png" and photo["sizeBytes"] == len(data)

    assert db.session.query(ComplaintPhoto).count() == 1
    saved = stored_files(upload_dir)
    assert len(saved) == 1 and saved[0].read_bytes() == data


def test_attach_three_photos_at_once(client, owner, complaint, upload_dir):
    body = files(("1.png", image_bytes()), ("2.jpg", image_bytes("JPEG")),
                 ("3.webp", image_bytes("WEBP")))
    resp = post(client, owner, complaint.public_id, body)
    assert resp.status_code == 201
    assert len(resp.get_json()["photos"]) == 3
    assert resp.get_json()["remaining"] == 0
    assert len(stored_files(upload_dir)) == 3


def test_photos_can_be_added_in_separate_requests(client, owner, complaint, upload_dir):
    post(client, owner, complaint.public_id, files(("1.png", image_bytes())))
    resp = post(client, owner, complaint.public_id,
                files(("2.png", image_bytes()), ("3.png", image_bytes())))
    assert resp.status_code == 201
    assert resp.get_json()["remaining"] == 0


# ---- limits -------------------------------------------------------------------------

def test_fourth_photo_rejected(client, owner, complaint, upload_dir):
    post(client, owner, complaint.public_id,
         files(("1.png", image_bytes()), ("2.png", image_bytes()), ("3.png", image_bytes())))
    resp = post(client, owner, complaint.public_id, files(("4.png", image_bytes())))
    assert resp.status_code == 413
    assert resp.get_json()["error"]["code"] == "TOO_MANY_PHOTOS"
    assert db.session.query(ComplaintPhoto).count() == 3
    assert len(stored_files(upload_dir)) == 3


def test_four_photos_in_one_request_rejected_and_nothing_saved(client, owner, complaint,
                                                               upload_dir):
    body = files(*[(f"{i}.png", image_bytes()) for i in range(4)])
    resp = post(client, owner, complaint.public_id, body)
    assert resp.status_code == 413
    assert resp.get_json()["error"]["code"] == "TOO_MANY_PHOTOS"
    assert db.session.query(ComplaintPhoto).count() == 0
    assert stored_files(upload_dir) == []


def test_photo_over_5mb_rejected(client, owner, complaint, upload_dir):
    too_big = image_bytes() + b"\0" * (5 * MB)  # valid PNG header, but > 5 MB in total
    resp = post(client, owner, complaint.public_id, files(("big.png", too_big)))
    assert resp.status_code == 413
    err = resp.get_json()["error"]
    assert err["code"] == "PHOTO_TOO_LARGE" and "5 MB" in err["message"]
    assert db.session.query(ComplaintPhoto).count() == 0
    assert stored_files(upload_dir) == []


def test_size_limit_boundary(app, client, owner, complaint, upload_dir):
    data = image_bytes()
    app.config["MAX_PHOTO_BYTES"] = len(data)  # exactly at the limit: accepted
    ok = post(client, owner, complaint.public_id, files(("ok.png", data)))
    assert ok.status_code == 201

    app.config["MAX_PHOTO_BYTES"] = len(data) - 1  # one byte over: rejected
    over = post(client, owner, complaint.public_id, files(("over.png", data)))
    assert over.status_code == 413


# ---- bad files ----------------------------------------------------------------------

def test_text_file_renamed_to_jpg_rejected(client, owner, complaint, upload_dir):
    resp = post(client, owner, complaint.public_id,
                files(("fake.jpg", b"this is not an image")))
    assert resp.status_code == 422
    assert resp.get_json()["error"]["code"] == "INVALID_PHOTO"
    assert stored_files(upload_dir) == []


def test_gif_rejected(client, owner, complaint, upload_dir):
    resp = post(client, owner, complaint.public_id, files(("a.gif", image_bytes("GIF"))))
    assert resp.status_code == 422
    assert "JPEG, PNG or WebP" in resp.get_json()["error"]["message"]


def test_empty_file_rejected(client, owner, complaint, upload_dir):
    resp = post(client, owner, complaint.public_id, files(("empty.png", b"")))
    assert resp.status_code == 422


def test_no_file_sent_rejected(client, owner, complaint, upload_dir):
    resp = client.post(f"/api/v1/complaints/{complaint.public_id}/photos",
                       headers=auth(owner), data={}, content_type="multipart/form-data")
    assert resp.status_code == 422
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_one_bad_file_rejects_the_whole_request(client, owner, complaint, upload_dir):
    body = files(("good.png", image_bytes()), ("bad.png", b"nope"))
    resp = post(client, owner, complaint.public_id, body)
    assert resp.status_code == 422
    assert db.session.query(ComplaintPhoto).count() == 0
    assert stored_files(upload_dir) == []


def test_user_supplied_file_name_never_used_on_disk(client, owner, complaint, upload_dir):
    resp = post(client, owner, complaint.public_id,
                files(("../../evil.png", image_bytes())))
    assert resp.status_code == 201
    assert resp.get_json()["photos"][0]["originalName"] == "evil.png"
    saved = stored_files(upload_dir)
    assert len(saved) == 1
    assert upload_dir in saved[0].parents and saved[0].name != "evil.png"


# ---- access control -----------------------------------------------------------------

def test_cannot_attach_to_someone_elses_complaint(client, complaint, upload_dir):
    stranger = make_user("stranger@example.com")
    resp = post(client, stranger, complaint.public_id, files(("a.png", image_bytes())))
    assert resp.status_code == 404
    assert stored_files(upload_dir) == []


def test_unknown_complaint_id(client, owner, upload_dir):
    resp = post(client, owner, "SCMS-2026-99999", files(("a.png", image_bytes())))
    assert resp.status_code == 404
    assert resp.get_json()["error"]["code"] == "NOT_FOUND"


def test_owner_can_list_and_download(client, owner, complaint, upload_dir):
    data = image_bytes()
    post(client, owner, complaint.public_id, files(("a.png", data)))

    listing = client.get(f"/api/v1/complaints/{complaint.public_id}/photos",
                         headers=auth(owner))
    assert listing.status_code == 200
    photo = listing.get_json()["photos"][0]

    download = client.get(photo["url"], headers=auth(owner))
    assert download.status_code == 200
    assert download.mimetype == "image/png"
    assert download.data == data


def test_other_citizen_cannot_view_photos(client, owner, complaint, upload_dir):
    post(client, owner, complaint.public_id, files(("a.png", image_bytes())))
    stranger = make_user("stranger@example.com")
    url = client.get(f"/api/v1/complaints/{complaint.public_id}/photos",
                     headers=auth(owner)).get_json()["photos"][0]["url"]
    assert client.get(url, headers=auth(stranger)).status_code == 404
    listing = client.get(f"/api/v1/complaints/{complaint.public_id}/photos",
                         headers=auth(stranger))
    assert listing.status_code == 404


def test_officer_can_view_photos(client, owner, complaint, upload_dir):
    post(client, owner, complaint.public_id, files(("a.png", image_bytes())))
    officer = make_user("officer@example.com", role=Role.OFFICER)
    url = client.get(f"/api/v1/complaints/{complaint.public_id}/photos",
                     headers=auth(officer)).get_json()["photos"][0]["url"]
    assert client.get(url, headers=auth(officer)).status_code == 200
