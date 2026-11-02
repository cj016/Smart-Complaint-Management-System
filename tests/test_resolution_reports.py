"""TC-Report-01: reports enforce roles and count current states without double-counting."""
import csv
import io

import pytest
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import Complaint, Role, User


@pytest.fixture()
def admin(app):
    user = User(name="Admin", email="admin@example.com", password_hash="x", role=Role.ADMIN)
    db.session.add(user)
    db.session.commit()
    return user


def auth(user):
    return {"Authorization": "Bearer " + create_access_token(identity=str(user.id))}


@pytest.mark.parametrize("fmt", ["json", "csv"])
def test_report_roles(client, admin, fmt):
    url = "/api/v1/reports?format=" + fmt
    assert client.get(url).status_code == 401
    for role in (Role.COMPLAINANT, Role.OFFICER):
        admin.role = role
        db.session.commit()
        assert client.get(url, headers=auth(admin)).status_code == 403


def test_empty_report(client, admin):
    response = client.get("/api/v1/reports", headers=auth(admin))
    assert response.json == {"groupBy": "category", "items": [], "totalComplaints": 0}
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize("group", ["category", "department"])
def test_group_counts(client, admin, group):
    for i, status in enumerate(["Resolved", "Closed", "Reopened", "Submitted"]):
        db.session.add(Complaint(public_id=f"SCMS-2026-{i:05}", user_id=admin.id,
                                 category="Roads", department=None, status=status,
                                 description="Issue", location="Road"))
    db.session.commit()
    response = client.get("/api/v1/reports?group_by=" + group, headers=auth(admin))
    assert response.json["items"] == [{"group": "Roads" if group == "category" else "Unassigned",
                                       "total": 4, "resolved": 1, "closed": 1,
                                       "reopened": 1, "completed": 2, "open": 2,
                                       "resolutionRate": 50.0, "averageTurnaroundHours": None,
                                       "turnaroundSamples": 0}]
    assert response.json["totalComplaints"] == 4


def test_multiple_groups_and_csv_safety(client, admin):
    for i, category in enumerate(["Roads", "Roads", "=HYPERLINK(1)", "Drain, water"]):
        db.session.add(Complaint(public_id=f"SCMS-2026-{i:05}", user_id=admin.id,
                                 category=category, description="Private text", location="Private"))
    db.session.commit()
    response = client.get("/api/v1/reports?format=csv", headers=auth(admin))
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert sum(int(row["total"]) for row in rows) == 4
    assert "'=HYPERLINK(1)" in [row["group"] for row in rows]
    assert "Drain, water" in [row["group"] for row in rows]
    assert "Private" not in response.text
    assert "attachment" in response.headers["Content-Disposition"]


@pytest.mark.parametrize("query", ["group_by=bad", "format=pdf", "group_by=__dict__"])
def test_invalid_query(client, admin, query):
    assert client.get("/api/v1/reports?" + query, headers=auth(admin)).status_code == 422


def test_report_page(client):
    assert client.get("/reports").status_code == 200


@pytest.mark.parametrize("group", ["category", "department"])
def test_turnaround_and_inclusive_date_filter(client, admin, group):
    from datetime import datetime

    rows = [
        ("Resolved", datetime(2026, 10, 1, 0, 0), datetime(2026, 10, 1, 2, 0)),
        ("Closed", datetime(2026, 10, 1, 23, 59, 59), datetime(2026, 10, 2, 5, 59, 59)),
        ("Reopened", datetime(2026, 10, 1, 12, 0), datetime(2026, 10, 2, 12, 0)),
        ("Resolved", datetime(2026, 10, 1, 12, 0), None),
        ("Resolved", datetime(2026, 9, 30, 23, 59, 59), datetime(2026, 10, 1, 9, 0)),
        ("Resolved", datetime(2026, 10, 2, 0, 0), datetime(2026, 10, 2, 9, 0)),
    ]
    for i, (status, created, resolved) in enumerate(rows):
        db.session.add(Complaint(public_id=f"SCMS-2026-{i:05}", user_id=admin.id,
                                 category="Roads", department="Works", status=status,
                                 description="Issue", location="Road", created_at=created,
                                 resolved_at=resolved))
    db.session.commit()
    query = f"?group_by={group}&start_date=2026-10-01&end_date=2026-10-01"
    report = client.get("/api/v1/reports" + query, headers=auth(admin))
    item = report.json["items"][0]
    assert item["total"] == 4 and item["completed"] == 3 and item["open"] == 1
    assert item["averageTurnaroundHours"] == 4.0 and item["turnaroundSamples"] == 2
    csv_response = client.get("/api/v1/reports" + query + "&format=csv", headers=auth(admin))
    exported = list(csv.DictReader(io.StringIO(csv_response.text)))
    assert exported[0]["total"] == "4" and exported[0]["averageTurnaroundHours"] == "4.0"


@pytest.mark.parametrize("query", [
    "start_date=bad", "end_date=2026-02-30", "start_date=2026-1-1", "start_date=2026-W01-1",
    "start_date=2026-11-02&end_date=2026-11-01",
])
@pytest.mark.parametrize("endpoint", ["/api/v1/reports"])
def test_invalid_date_ranges(client, admin, query, endpoint):
    assert client.get(endpoint + "?" + query, headers=auth(admin)).status_code == 422
