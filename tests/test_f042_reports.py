"""SCMS-F042: Admin-only reports by category, department, status and date."""
import csv
from datetime import datetime
from io import StringIO

import pytest

from app.extensions import db
from app.models import Role
from tests.admin_helpers import auth, make_complaint, make_user

URL = "/api/v1/reports/summary"
CSV_URL = "/api/v1/reports/summary.csv"


@pytest.fixture()
def users(app):
    return {
        "admin": make_user("reports-admin@example.com", Role.ADMIN),
        "officer": make_user("reports-officer@example.com", Role.OFFICER),
        "citizen": make_user("reports-citizen@example.com"),
    }


def seed(people):
    user = people["citizen"]
    road = make_complaint(
        user, 1, category="Roads", status="Resolved", department="Public Works"
    )
    water = make_complaint(
        user, 2, category="Water", status="Closed", department="Public Works"
    )
    light = make_complaint(
        user, 3, category="Roads", status="In Progress", department=None
    )
    reopened = make_complaint(
        user, 4, category="Roads", status="Reopened", department="Electricity"
    )
    with db.session.no_autoflush:
        road.created_at = datetime(2026, 5, 10, 8)
        road.resolved_at = datetime(2026, 5, 11, 8)  # 24 hours
        water.created_at = datetime(2026, 5, 10, 23, 59, 59)
        water.resolved_at = datetime(2026, 5, 12, 23, 59, 59)  # 48 hours
        light.created_at = datetime(2026, 5, 11, 0)
        reopened.created_at = datetime(2026, 5, 12, 0)
        reopened.resolved_at = datetime(2026, 5, 13, 0)  # exclude reopened
    db.session.commit()
    return road, water, light, reopened


def get(client, users, url=URL):
    return client.get(url, headers=auth(users["admin"]))


@pytest.mark.parametrize("endpoint", [URL, CSV_URL])
def test_requires_login(client, endpoint):
    assert client.get(endpoint).status_code == 401


@pytest.mark.parametrize("role", ["citizen", "officer"])
@pytest.mark.parametrize("endpoint", [URL, CSV_URL])
def test_non_admin_forbidden(client, users, role, endpoint):
    assert client.get(endpoint, headers=auth(users[role])).status_code == 403


def test_empty_report(client, users):
    data = get(client, users).get_json()
    assert data["totalComplaints"] == 0
    assert data["byCategory"] == []
    assert data["byDepartment"] == []
    assert data["averageTurnaroundHours"] is None
    assert data["turnaroundSampleCount"] == 0
    assert sum(item["count"] for item in data["byStatus"]) == 0


def test_counts_by_category_department_and_status(client, users):
    seed(users)
    data = get(client, users).get_json()
    assert data["totalComplaints"] == 4
    assert {row["name"]: row["count"] for row in data["byCategory"]} == {
        "Roads": 3, "Water": 1}
    assert {row["name"]: row["count"] for row in data["byDepartment"]} == {
        "Public Works": 2, "Electricity": 1, "Unassigned": 1}
    counts = {row["name"]: row["count"] for row in data["byStatus"]}
    assert counts["Resolved"] == 1 and counts["Closed"] == 1
    assert counts["In Progress"] == 1 and counts["Reopened"] == 1


def test_average_turnaround_excludes_reopened(client, users):
    seed(users)
    data = get(client, users).get_json()
    assert data["averageTurnaroundHours"] == 36.0
    assert data["turnaroundSampleCount"] == 2


def test_excludes_missing_or_negative_resolution_timestamps(client, users):
    road, water, _, _ = seed(users)
    road.resolved_at = None
    water.resolved_at = datetime(2026, 5, 9)
    db.session.commit()
    data = get(client, users).get_json()
    assert data["averageTurnaroundHours"] is None
    assert data["turnaroundSampleCount"] == 0


@pytest.mark.parametrize("url,total", [
    (URL + "?start_date=2026-05-10&end_date=2026-05-10", 2),
    (URL + "?start_date=2026-05-11", 2),
    (URL + "?end_date=2026-05-10", 2),
    (URL + "?start_date=2026-05-12&end_date=2026-05-12", 1),
    (URL + "?start_date=2026-01-01&end_date=2026-01-02", 0),
])
def test_submission_date_filters(client, users, url, total):
    seed(users)
    result = get(client, users, url)
    assert result.status_code == 200
    assert result.get_json()["totalComplaints"] == total


def test_filter_date_semantics_visible(client, users):
    data = get(client, users, URL + "?start_date=2026-05-01").get_json()
    assert data["filters"] == {
        "startDate": "2026-05-01", "endDate": None, "dateField": "created_at"}


@pytest.mark.parametrize("query", [
    "start_date=tomorrow", "end_date=2026-02-30", "start_date=20260510",
    "start_date=2026-6-01", "start_date=2026-05-11&end_date=2026-05-10",
    "end_date=9999-12-31",
])
def test_bad_date_filters(client, users, query):
    response = get(client, users, URL + "?" + query)
    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_csv_includes_metrics_and_groups(client, users):
    seed(users)
    response = get(client, users, CSV_URL + "?start_date=2026-05-10")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "attachment" in response.headers["Content-Disposition"]
    rows = list(csv.reader(StringIO(response.get_data(as_text=True))))
    assert ["Total complaints", "4"] in rows
    assert ["Average turnaround (hours)", "36.0"] in rows
    assert ["Roads", "3"] in rows
    assert ["Public Works", "2"] in rows
    assert ["Reopened", "1"] in rows


def test_csv_export_uses_identical_filters(client, users):
    seed(users)
    response = get(client, users, CSV_URL + "?end_date=2026-05-10")
    rows = list(csv.reader(StringIO(response.get_data(as_text=True))))
    assert ["Total complaints", "2"] in rows


def test_csv_rejects_invalid_filters(client, users):
    assert get(client, users, CSV_URL + "?end_date=bad").status_code == 422


def test_csv_escapes_formula_like_categories(client, users):
    make_complaint(users["citizen"], 9, category="=2+2")
    response = get(client, users, CSV_URL)
    rows = list(csv.reader(StringIO(response.get_data(as_text=True))))
    assert ["'=2+2", "1"] in rows


def test_page_renders_report_shell(client):
    response = client.get("/admin/reports")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="report-content" hidden' in html
    assert 'js/reports.js' in html
    assert 'id="category-table"' in html


def test_dashboard_has_admin_only_link(client):
    html = client.get("/admin").get_data(as_text=True)
    assert 'href="/admin/reports"' in html
    assert 'data-roles="Admin" hidden' in html
