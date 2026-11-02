"""SCMS-F041/F042: admin-only feedback and dated resolution reports."""
import csv
from datetime import date, datetime, time
import io

from flask import Blueprint, Response, jsonify, request
from sqlalchemy import case, func

from ..auth.decorators import roles_required
from ..errors import error_response
from ..extensions import db
from ..models import Complaint, Role

bp = Blueprint("reporting", __name__)


@bp.get("/ping")
def ping():
    return jsonify({"module": "reporting", "status": "ok"})


def csv_safe(value):
    text = "" if value is None else str(value)
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text


def date_range():
    """Inclusive UTC complaint-submission dates, with strict ISO input."""
    values = []
    for key in ("start_date", "end_date"):
        raw = request.args.get(key, "")
        if not raw:
            values.append(None)
            continue
        try:
            if len(raw) != 10:
                raise ValueError()
            parsed = date.fromisoformat(raw)
            if parsed.isoformat() != raw:
                raise ValueError()
            values.append(parsed)
        except ValueError:
            return None, None, error_response(
                "VALIDATION_ERROR", "Dates must use YYYY-MM-DD.", status=422)
    start, end = values
    if start and end and start > end:
        return None, None, error_response(
            "VALIDATION_ERROR", "Start date must not follow end date.", status=422)
    return start, end, None


def dated(stmt, start, end):
    if start:
        stmt = stmt.where(Complaint.created_at >= datetime.combine(start, time.min))
    if end:
        stmt = stmt.where(Complaint.created_at <= datetime.combine(end, time.max))
    return stmt


def no_store(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("")
@bp.get("/")
@roles_required(Role.ADMIN)
def reports():
    group_by = request.args.get("group_by", "category")
    output = request.args.get("format", "json")
    if group_by not in ("category", "department") or output not in ("json", "csv"):
        return error_response("VALIDATION_ERROR", "Use category/department and json/csv.",
                              status=422)
    start, end, error = date_range()
    if error is not None:
        return error
    column = getattr(Complaint, group_by)
    label = func.coalesce(func.nullif(column, ""), "Unassigned")
    completed = Complaint.status.in_(("Resolved", "Closed"))
    stmt = db.select(
        label.label("group_name"), func.count(Complaint.id),
        func.sum(case((Complaint.status == "Resolved", 1), else_=0)),
        func.sum(case((Complaint.status == "Closed", 1), else_=0)),
        func.sum(case((Complaint.status == "Reopened", 1), else_=0)),
        func.sum(case((completed, 1), else_=0)),
    ).group_by(label).order_by(label)
    # Stream timestamps only, avoiding database-specific date arithmetic and PII.
    duration_query = dated(db.select(label, Complaint.created_at, Complaint.resolved_at).where(
        completed, Complaint.resolved_at.is_not(None)), start, end)
    durations = {}
    for name, created, resolved in db.session.execute(duration_query).yield_per(1000):
        hours = (resolved - created).total_seconds() / 3600
        if hours >= 0:
            total_hours, samples = durations.get(name, (0, 0))
            durations[name] = (total_hours + hours, samples + 1)
    items = []
    for row in db.session.execute(dated(stmt, start, end)):
        name, total, resolved, closed, reopened, done = row
        total_hours, samples = durations.get(name, (0, 0))
        items.append({"group": name, "total": total, "resolved": resolved,
                      "closed": closed, "reopened": reopened, "completed": done,
                      "open": total - done, "resolutionRate": round(100 * done / total, 2),
                      "averageTurnaroundHours": (round(total_hours / samples, 2)
                                                 if samples else None),
                      "turnaroundSamples": samples})
    if output == "csv":
        stream = io.StringIO(newline="")
        fields = ["group", "total", "resolved", "closed", "reopened", "completed", "open",
                  "resolutionRate", "averageTurnaroundHours", "turnaroundSamples"]
        writer = csv.writer(stream)
        writer.writerow(fields)
        for item in items:
            writer.writerow([csv_safe(item[key]) for key in fields])
        response = Response(stream.getvalue(), mimetype="text/csv")
        response.headers["Content-Disposition"] = (
            f'attachment; filename="scms-{group_by}-report.csv"')
    else:
        response = jsonify({"groupBy": group_by, "items": items,
                            "totalComplaints": sum(item["total"] for item in items)})
    return no_store(response)
