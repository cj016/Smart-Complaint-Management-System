"""SCMS-NF-001 (TC-Perf-01): the admin dashboard answers within 3 s for 90% of requests."""
import math
import time
from datetime import timedelta

import pytest

from app.extensions import db
from app.models import PRIORITIES, STATUSES, Complaint, Role
from app.utils import utcnow
from tests.admin_helpers import auth, make_user

TOTAL_COMPLAINTS = 500   # a realistic data set for the dashboard
REQUESTS = 60            # requests per URL
LIMIT_SECONDS = 3.0      # SRS 5, SCMS-NF-001
CATEGORIES = ["Roads", "Water", "Sanitation", "Electricity"]

URLS = {
    "dashboard": "/api/v1/admin/complaints",
    "filter_and_sort": ("/api/v1/admin/complaints"
                        "?category=Roads&priority=High&sort=priority&order=desc"),
    "last_page": "/api/v1/admin/complaints?page=10&per_page=50",
}


@pytest.fixture()
def admin_headers(app):
    admin = make_user("admin@example.com", Role.ADMIN)
    citizen = make_user("citizen@example.com")
    now = utcnow()
    db.session.add_all([
        Complaint(public_id=f"SCMS-2026-{i:05d}", user_id=citizen.id,
                  category=CATEGORIES[i % len(CATEGORIES)], description="Test complaint",
                  location="Main St", status=STATUSES[i % len(STATUSES)],
                  priority=PRIORITIES[i % len(PRIORITIES)],
                  created_at=now - timedelta(minutes=i))
        for i in range(1, TOTAL_COMPLAINTS + 1)
    ])
    db.session.commit()
    return auth(admin)


def percentile_90(samples):
    ordered = sorted(samples)
    return ordered[math.ceil(0.9 * len(ordered)) - 1]


def test_seed_data_is_in_the_dashboard(client, admin_headers):
    resp = client.get(URLS["dashboard"], headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()["total"] == TOTAL_COMPLAINTS


@pytest.mark.parametrize("url", list(URLS.values()), ids=list(URLS))
def test_90_percent_of_requests_finish_within_3_seconds(client, admin_headers, url):
    timings = []
    for _ in range(REQUESTS):
        start = time.perf_counter()
        resp = client.get(url, headers=admin_headers)
        timings.append(time.perf_counter() - start)
        assert resp.status_code == 200
    assert percentile_90(timings) <= LIMIT_SECONDS
