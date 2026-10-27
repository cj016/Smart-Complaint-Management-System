"""Test case TC-Lodge-04 (SCMS-F-013), lodge form path: photos sent with the complaint."""
from io import BytesIO

import pytest
from flask_jwt_extended import create_access_token
from PIL import Image

from app.extensions import db
from app.models import Complaint, ComplaintPhoto, User

VALID = {"category": "Roads", "description": "Pothole", "location": "Main St"}


def png(name="a.png"):
    buf = BytesIO()
    Image.new("RGB", (8, 8), "blue").save(buf, "PNG")
    buf.seek(0)
    return buf, name


@pytest.fixture()
def citizen(app, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    user = User(name="Asha", email="asha@example.com", password_hash="x")
    db.session.add(user)
    db.session.commit()
    return user


def lodge(client, user, photos=()):
    headers = {"Authorization": f"Bearer {create_access_token(identity=str(user.id))}"}
    data = {**VALID, "photos": list(photos)}
    return client.post("/api/v1/complaints", data=data, headers=headers,
                       content_type="multipart/form-data")


def test_lodge_without_photos_still_works(client, citizen):
    resp = lodge(client, citizen)
    assert resp.status_code == 201
    assert resp.get_json()["photos"] == 0


def test_lodge_with_three_photos(client, citizen, tmp_path):
    resp = lodge(client, citizen, [png("1.png"), png("2.png"), png("3.png")])
    assert resp.status_code == 201
    assert resp.get_json()["photos"] == 3
    assert db.session.query(ComplaintPhoto).count() == 3
    assert len([p for p in tmp_path.rglob("*") if p.is_file()]) == 3


def test_four_photos_rejected_and_complaint_not_saved(client, citizen, tmp_path):
    resp = lodge(client, citizen, [png(f"{i}.png") for i in range(4)])
    assert resp.status_code == 413
    assert resp.get_json()["error"]["code"] == "TOO_MANY_PHOTOS"
    assert db.session.execute(db.select(Complaint)).first() is None
    assert not [p for p in tmp_path.rglob("*") if p.is_file()]


def test_bad_photo_rejects_whole_submission(client, citizen, tmp_path):
    bad = (BytesIO(b"not an image"), "fake.jpg")
    resp = lodge(client, citizen, [png(), bad])
    assert resp.status_code == 422
    assert resp.get_json()["error"]["code"] == "INVALID_PHOTO"
    assert db.session.execute(db.select(Complaint)).first() is None
    assert not [p for p in tmp_path.rglob("*") if p.is_file()]


def test_oversized_photo_rejected(app, client, citizen):
    app.config["MAX_PHOTO_BYTES"] = 10  # tiny limit so the test stays fast
    resp = lodge(client, citizen, [png()])
    assert resp.status_code == 413
    assert resp.get_json()["error"]["code"] == "PHOTO_TOO_LARGE"
    assert db.session.execute(db.select(Complaint)).first() is None
