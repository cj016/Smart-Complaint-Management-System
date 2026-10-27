"""Admin / officer endpoints (AdminModule, SAD 3.4).

SCMS-F031  GET  /api/v1/admin/complaints                  dashboard: all complaints (Officer, Admin)
SCMS-F032  same endpoint, query params: status, category, priority, q, sort, order, page, per_page
SCMS-F030  POST /api/v1/admin/complaints/<id>/assign      assign to an officer (Admin only)
SCMS-F033  POST /api/v1/admin/complaints/<id>/status      update status + remarks (Officer, Admin)
Helpers    GET  /api/v1/admin/complaints/<id>, /officers, /filter-options

All endpoints need: Authorization: Bearer <JWT>
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import case, or_

from ..auth.decorators import roles_required
from ..errors import error_response
from ..extensions import db
from ..models import PRIORITIES, STATUSES, Complaint, Role, StatusHistory, User
from ..utils import utcnow

bp = Blueprint("admin", __name__)

STAFF = (Role.OFFICER, Role.ADMIN)
MAX_PER_PAGE = 50
MAX_REMARKS = 2000
SORT_FIELDS = ("created_at", "updated_at", "category", "priority", "status")

# Which status a staff member may move a complaint to (SRS 4.3 lists the statuses but not the
# rules). "Assigned" is set by the assign endpoint and "Reopened" by the citizen (F-024).
ALLOWED_TRANSITIONS = {
    "Submitted": ["In Review"],
    "In Review": ["In Progress"],
    "Assigned": ["In Progress"],
    "In Progress": ["Resolved"],
    "Resolved": ["Closed"],
    "Reopened": ["In Review", "In Progress"],
}


@bp.get("/ping")
def ping():
    return jsonify({"module": "admin", "status": "ok"})


# ---- helpers -------------------------------------------------------------------------

def _iso(dt):
    return dt.isoformat() + "Z" if dt else None


def _current_user():
    return db.session.get(User, int(get_jwt_identity()))


def _get_complaint(public_id):
    return db.session.execute(
        db.select(Complaint).where(Complaint.public_id == public_id.strip().upper())
    ).scalar_one_or_none()


def _not_found():
    return error_response("NOT_FOUND", "Complaint not found.", status=404)


def _invalid(message, field=None, status=422):
    return error_response("VALIDATION_ERROR", message, {"field": field} if field else None,
                          status)


def _rank(column, ordered_values):
    """Sort by position in a list (Low < Medium < High < Critical), not alphabetically."""
    return case({v: i for i, v in enumerate(ordered_values)}, value=column,
                else_=len(ordered_values))


def serialize_row(c):
    return {
        "complaintId": c.public_id,
        "category": c.category,
        "location": c.location,
        "status": c.status,
        "priority": c.priority,
        "department": c.department,
        "assignedTo": {"id": c.assignee.id, "name": c.assignee.name} if c.assignee else None,
        "createdAt": _iso(c.created_at),
        "updatedAt": _iso(c.updated_at),
    }


def serialize_detail(c):
    data = serialize_row(c)
    data["description"] = c.description
    data["resolutionRemarks"] = c.resolution_remarks
    data["resolvedAt"] = _iso(c.resolved_at)
    data["allowedStatuses"] = ALLOWED_TRANSITIONS.get(c.status, [])
    return data


# ---- SCMS-F031 / F032: dashboard list ------------------------------------------------

@bp.get("/complaints")
@roles_required(*STAFF)
def list_complaints():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        return _invalid("page and per_page must be integers.")
    if page < 1 or per_page < 1:
        return _invalid("page and per_page must be >= 1.")
    per_page = min(per_page, MAX_PER_PAGE)

    status = request.args.get("status", "").strip()
    priority = request.args.get("priority", "").strip()
    category = request.args.get("category", "").strip()
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "created_at").strip()
    order = request.args.get("order", "desc").strip().lower()

    if status and status not in STATUSES:
        return error_response("VALIDATION_ERROR", "Unknown status filter.",
                              {"field": "status", "allowed": STATUSES}, 422)
    if priority and priority not in PRIORITIES:
        return error_response("VALIDATION_ERROR", "Unknown priority filter.",
                              {"field": "priority", "allowed": PRIORITIES}, 422)
    if sort not in SORT_FIELDS:
        return error_response("VALIDATION_ERROR", "Unknown sort field.",
                              {"field": "sort", "allowed": list(SORT_FIELDS)}, 422)
    if order not in ("asc", "desc"):
        return error_response("VALIDATION_ERROR", "order must be asc or desc.",
                              {"field": "order"}, 422)

    stmt = db.select(Complaint)
    if status:
        stmt = stmt.where(Complaint.status == status)
    if priority:
        stmt = stmt.where(Complaint.priority == priority)
    if category:
        stmt = stmt.where(Complaint.category == category)
    if q:
        escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{escaped}%"
        stmt = stmt.where(or_(
            Complaint.public_id.ilike(like, escape="\\"),
            Complaint.location.ilike(like, escape="\\"),
            Complaint.description.ilike(like, escape="\\"),
        ))

    if sort == "priority":
        key = _rank(Complaint.priority, PRIORITIES)
    elif sort == "status":
        key = _rank(Complaint.status, STATUSES)
    else:
        key = getattr(Complaint, sort)
    key = key.asc() if order == "asc" else key.desc()
    stmt = stmt.order_by(key, Complaint.id.desc())

    result = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [serialize_row(c) for c in result.items],
        "page": result.page,
        "perPage": result.per_page,
        "total": result.total,
        "pages": result.pages,
        "sort": sort,
        "order": order,
    })


@bp.get("/filter-options")
@roles_required(*STAFF)
def filter_options():
    categories = db.session.execute(
        db.select(Complaint.category).distinct().order_by(Complaint.category)
    ).scalars().all()
    return jsonify({"statuses": STATUSES, "priorities": PRIORITIES, "categories": categories})


@bp.get("/complaints/<public_id>")
@roles_required(*STAFF)
def complaint_detail(public_id):
    complaint = _get_complaint(public_id)
    if complaint is None:
        return _not_found()
    return jsonify(serialize_detail(complaint))


# ---- SCMS-F030: assign to an officer -------------------------------------------------

@bp.get("/officers")
@roles_required(Role.ADMIN)
def list_officers():
    officers = db.session.execute(
        db.select(User).where(User.role == Role.OFFICER).order_by(User.name)
    ).scalars().all()
    return jsonify({"items": [
        {"id": o.id, "name": o.name, "department": o.department} for o in officers]})


@bp.post("/complaints/<public_id>/assign")
@roles_required(Role.ADMIN)
def assign_complaint(public_id):
    admin = _current_user()
    complaint = _get_complaint(public_id)
    if complaint is None:
        return _not_found()

    data = request.get_json(silent=True) or {}
    officer_id = data.get("officerId")
    if isinstance(officer_id, bool) or not isinstance(officer_id, int):
        return _invalid("officerId is required and must be a number.", "officerId")
    officer = db.session.get(User, officer_id)
    if officer is None or officer.role != Role.OFFICER:
        return _invalid("officerId must be the id of an officer.", "officerId")

    department = data.get("department")
    if department is not None and not isinstance(department, str):
        return _invalid("department must be text.", "department")
    department = (department or "").strip() or officer.department
    if department and len(department) > 100:
        return _invalid("department must be at most 100 characters.", "department")

    if complaint.status in ("Resolved", "Closed"):
        return error_response("CONFLICT", "A resolved or closed complaint cannot be assigned. "
                              "It must be reopened first.", status=409)

    complaint.assigned_to_id = officer.id
    complaint.department = department
    if complaint.status in ("Submitted", "In Review"):
        complaint.status = "Assigned"
        note = f"Assigned to {officer.name}" + (f" ({department})" if department else "")
        complaint.history.append(
            StatusHistory(status="Assigned", remarks=note, changed_by_id=admin.id))
    db.session.commit()
    return jsonify(serialize_detail(complaint))


# ---- SCMS-F033: update status with resolution remarks --------------------------------

@bp.post("/complaints/<public_id>/status")
@roles_required(*STAFF)
def update_status(public_id):
    user = _current_user()
    complaint = _get_complaint(public_id)
    if complaint is None:
        return _not_found()
    if user.role == Role.OFFICER and complaint.assigned_to_id != user.id:
        return error_response("FORBIDDEN", "You can only update complaints assigned to you.",
                              status=403)

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    remarks = data.get("remarks")
    if not isinstance(new_status, str) or new_status not in STATUSES:
        return error_response("VALIDATION_ERROR", "Unknown status.",
                              {"field": "status", "allowed": STATUSES}, 422)
    if remarks is not None and not isinstance(remarks, str):
        return _invalid("remarks must be text.", "remarks")
    remarks = (remarks or "").strip()
    if len(remarks) > MAX_REMARKS:
        return _invalid(f"remarks must be at most {MAX_REMARKS} characters.", "remarks")

    allowed = ALLOWED_TRANSITIONS.get(complaint.status, [])
    if new_status not in allowed:
        return error_response(
            "CONFLICT", f"A complaint that is '{complaint.status}' cannot move to "
            f"'{new_status}'.", {"current": complaint.status, "allowed": allowed}, 409)
    if new_status == "Resolved" and not remarks:
        return _invalid("Resolution remarks are required when resolving a complaint.",
                        "remarks")

    complaint.status = new_status
    if new_status == "Resolved":
        complaint.resolution_remarks = remarks
        complaint.resolved_at = utcnow()
    complaint.history.append(
        StatusHistory(status=new_status, remarks=remarks or None, changed_by_id=user.id))
    db.session.commit()
    return jsonify(serialize_detail(complaint))
