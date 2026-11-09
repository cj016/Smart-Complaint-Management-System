"""SCMS-F042: Admin-only reports; filter by complaint submission date."""
import csv
from datetime import date, datetime, time, timedelta
from io import StringIO

from flask import Blueprint, Response, jsonify, request

from ..auth.decorators import roles_required
from ..errors import error_response
from ..extensions import db
from ..models import Complaint, Role, STATUSES

bp = Blueprint("reporting", __name__)


def _parse_date(value):
    """Require the exact YYYY-MM-DD format; do not silently accept timestamps."""
    if not value:
        return None
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if parsed.isoformat() != value:
        return None
    return parsed


def _report_filters():
    start_text = request.args.get("start_date", "")
    end_text = request.args.get("end_date", "")
    start = _parse_date(start_text) if start_text else None
    end = _parse_date(end_text) if end_text else None
    if (start_text and start is None) or (end_text and end is None):
        return None, error_response(
            "VALIDATION_ERROR", "Dates must use YYYY-MM-DD.", status=422)
    if start is not None and end is not None and start > end:
        return None, error_response(
            "VALIDATION_ERROR", "start_date must be on or before end_date.", status=422)
    if end == date.max:
        return None, error_response(
            "VALIDATION_ERROR", "end_date is out of supported range.", status=422)
    return (start, end), None


def _report_data(start, end):
    # Select only necessary columns: no names, emails, locations or descriptions.
    stmt = db.select(
        Complaint.category, Complaint.department, Complaint.status,
        Complaint.created_at, Complaint.resolved_at,
    )
    if start is not None:
        stmt = stmt.where(Complaint.created_at >= datetime.combine(start, time.min))
    if end is not None:
        # Exclusive next midnight makes the user-selected final day inclusive.
        stmt = stmt.where(
            Complaint.created_at < datetime.combine(end + timedelta(days=1), time.min)
        )

    rows = db.session.execute(stmt).all()
    categories = {}
    departments = {}
    statuses = {status: 0 for status in STATUSES}
    durations = []
    for category, department, status, created_at, resolved_at in rows:
        categories[category] = categories.get(category, 0) + 1
        department_name = (department or "").strip() or "Unassigned"
        departments[department_name] = departments.get(department_name, 0) + 1
        statuses[status] = statuses.get(status, 0) + 1

        # A reopened complaint's old resolved_at must not count as currently resolved.
        if status in ("Resolved", "Closed") and resolved_at is not None:
            elapsed_hours = (resolved_at - created_at).total_seconds() / 3600
            if elapsed_hours >= 0:
                durations.append(elapsed_hours)

    def sorted_counts(counts):
        ordered = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
        return [{"name": name, "count": count} for name, count in ordered]

    return {
        "filters": {
            "startDate": start.isoformat() if start else None,
            "endDate": end.isoformat() if end else None,
            "dateField": "created_at",
        },
        "totalComplaints": len(rows),
        "byCategory": sorted_counts(categories),
        "byDepartment": sorted_counts(departments),
        "byStatus": [{"name": status, "count": count} for status, count in statuses.items()],
        "averageTurnaroundHours": (
            round(sum(durations) / len(durations), 2) if durations else None
        ),
        "turnaroundSampleCount": len(durations),
    }


@bp.get("/summary")
@roles_required(Role.ADMIN)
def summary():
    filters, error = _report_filters()
    if error:
        return error
    return jsonify(_report_data(*filters))


def _safe_csv(value):
    """Prevent spreadsheet formulas from running in user-supplied group names."""
    value = str(value)
    if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")):
        return "'" + value
    return value


@bp.get("/summary.csv")
@roles_required(Role.ADMIN)
def summary_csv():
    filters, error = _report_filters()
    if error:
        return error
    report = _report_data(*filters)
    content = StringIO(newline="")
    writer = csv.writer(content)
    writer.writerow(["SCMS resolution report", "Value"])
    writer.writerow(["Submission start date", report["filters"]["startDate"] or "All"])
    writer.writerow(["Submission end date", report["filters"]["endDate"] or "All"])
    writer.writerow(["Total complaints", report["totalComplaints"]])
    writer.writerow(["Average turnaround (hours)",
                     report["averageTurnaroundHours"] if
                     report["averageTurnaroundHours"] is not None else "N/A"])
    writer.writerow(["Turnaround sample count", report["turnaroundSampleCount"]])
    for title, field in (("Category", "byCategory"),
                         ("Department", "byDepartment"),
                         ("Status", "byStatus")):
        writer.writerow([])
        writer.writerow([title, "Complaint count"])
        for item in report[field]:
            writer.writerow([_safe_csv(item["name"]), item["count"]])
    response = Response(content.getvalue(), content_type="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = 'attachment; filename="scms-reports.csv"'
    response.headers["Cache-Control"] = "no-store"
    return response
