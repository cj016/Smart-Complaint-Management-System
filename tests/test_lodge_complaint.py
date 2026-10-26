"""Test case TC-Lodge-01 (SCMS-F-010): lodge a new complaint."""
import re

import pytest
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import Complaint, StatusHistory, User

VALID = {"category": "Sanitation", "description": "Overflowing garbage bin",
         "location": "5th Cross Road, Sector 4"}


@pytest.fixture()
def citizen(app):
    user = User(name="Asha", email="asha@example.com", password_hash="x")
    db.session.add(user)
    db.session.commit()
    return user


def auth(user):
    return {"Authorization": f"Bearer {create_access_token(identity=str(user.id))}"}


def post(client, user, data):
    return client.post("/api/v1/complaints", data=data, headers=auth(user))  # multipart


def test_requires_login(client):
    resp = client.post("/api/v1/complaints", data=VALID)
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_lodge_returns_201_with_id_and_status(client, citizen):
    resp = post(client, citizen, VALID)
    assert resp.status_code == 201
    body = resp.get_json()
    assert re.match(r"^SCMS-\d{4}-\d{5}$", body["complaintId"])
    assert body["status"] == "Submitted"
    assert body["createdAt"].endswith("Z")


def test_complaint_is_saved_for_the_logged_in_user(client, citizen):
    post(client, citizen, VALID)
    c = db.session.execute(db.select(Complaint)).scalar_one()
    assert c.user_id == citizen.id
    assert c.status == "Submitted"
    assert (c.category, c.location) == (VALID["category"], VALID["location"])


def test_first_status_history_row_is_created(client, citizen):
    post(client, citizen, VALID)
    row = db.session.execute(db.select(StatusHistory)).scalar_one()
    assert row.status == "Submitted"
    assert row.changed_by_id == citizen.id


def test_json_body_is_also_accepted(client, citizen):
    resp = client.post("/api/v1/complaints", json=VALID, headers=auth(citizen))
    assert resp.status_code == 201


def test_ids_are_unique_and_increasing(client, citizen):
    first = post(client, citizen, VALID).get_json()["complaintId"]
    second = post(client, citizen, VALID).get_json()["complaintId"]
    assert first != second
    assert int(second[-5:]) == int(first[-5:]) + 1


@pytest.mark.parametrize("missing", ["category", "description", "location"])
def test_missing_field_returns_422_and_saves_nothing(client, citizen, missing):
    data = {k: v for k, v in VALID.items() if k != missing}
    resp = post(client, citizen, data)
    assert resp.status_code == 422
    body = resp.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert missing in body["error"]["details"]["fields"]
    assert db.session.execute(db.select(Complaint)).first() is None


def test_text_is_trimmed_before_saving(client, citizen):
    post(client, citizen, {**VALID, "location": "  Main Street  "})
    assert db.session.execute(db.select(Complaint)).scalar_one().location == "Main Street"


def test_token_for_deleted_user_is_rejected(client, app):
    token = create_access_token(identity="9999")
    resp = client.post("/api/v1/complaints", data=VALID,
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_lodge_page_renders(client):
    resp = client.get("/lodge")
    assert resp.status_code == 200
    assert b'name="viewport"' in resp.data
    assert b'id="lodge-form"' in resp.data
