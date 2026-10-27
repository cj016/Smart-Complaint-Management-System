"""Admin module.

SCMS-F-031: GET   /api/v1/admin/complaints               dashboard: all complaints
SCMS-F-032: same endpoint with ?category=&priority=&status=&sort=&order=
SCMS-F-030: POST  /api/v1/admin/complaints/<id>/assign   assign to an officer (Admin only)
SCMS-F-033: PATCH /api/v1/admin/complaints/<id>/status   update status + resolution remarks
Helper:     GET   /api/v1/admin/officers                 officers for the assign drop-down

All endpoints need: Authorization: Bearer <JWT> with role Officer/Admin (SCMS-SR-002).
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.orm import selectinload

from ..auth.decorators import roles_required
from ..errors import error_response
from ..extensions import db
from ..models import (PRIORITIES, STATUSES, Complaint, Role, User)
from .services import (SORT_COLUMNS, TRANSITIONS, build_dashboard_query)

bp = Blueprint("admin", __name__)

STAFF = (Role.OFFICER, Role.ADMIN)


def _iso(dt):
    return dt.isoformat() + "Z" if dt else None


def serialize_row(c):
    return {
        "complaintId": c.public_id,
        "category": c.category,
        "location": c.location,
        "status": c.status,
        "priority": c.priority,
        "department": c.department,
        "complainant": c.complainant.name if c.complainant else None,
        "assignedTo": ({"id": c.assignee.id, "name": c.assignee.name}
                       if c.assignee else None),
        "nextStatuses": TRANSITIONS.get(c.status, []),
        "createdAt": _iso(c.created_at),
        "updatedAt": _iso(c.updated_at),
    }


def _current_user():
    return db.session.get(User, int(get_jwt_identity()))


def _find_complaint(public_id):
    return db.session.execute(
        db.select(Complaint).where(Complaint.public_id == public_id.strip().upper())
    ).scalar_one_or_none()


def _not_found():
    return error_response("NOT_FOUND", "No complaint found with that ID.", status=404)


@bp.get("/ping")
def ping():
    return jsonify({"module": "admin", "status": "ok"})


# ---- SCMS-F031 + F032: dashboard with filter / sort --------------------------------

@bp.get("/complaints")
@roles_required(*STAFF)
def list_complaints():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        return error_response("VALIDATION_ERROR", "page and per_page must be integers.",
                              status=422)
    if page < 1 or per_page < 1:
        return error_response("VALIDATION_ERROR", "page and per_page must be >= 1.",
                              status=422)
    per_page = min(per_page, 50)

    category = (request.args.get("category") or "").strip() or None
    priority = request.args.get("priority") or None
    status = request.args.get("status") or None
    sort = request.args.get("sort") or "created_at"
    order = (request.args.get("order") or "desc").lower()

    if priority and priority not in PRIORITIES:
        return error_response("VALIDATION_ERROR", "Unknown priority filter.",
                              {"field": "priority", "allowed": PRIORITIES}, 422)
    if status and status not in STATUSES:
        return error_response("VALIDATION_ERROR", "Unknown status filter.",
                              {"field": "status", "allowed": STATUSES}, 422)
    if sort not in SORT_COLUMNS:
        return error_response("VALIDATION_ERROR", "Unknown sort field.",
                              {"field": "sort", "allowed": sorted(SORT_COLUMNS)}, 422)
    if order not in ("asc", "desc"):
        return error_response("VALIDATION_ERROR", "order must be asc or desc.",
                              {"field": "order"}, 422)

    stmt = build_dashboard_query(category, priority, status, sort, order).options(
        selectinload(Complaint.complainant), selectinload(Complaint.assignee))
    result = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [serialize_row(c) for c in result.items],
        "page": result.page,
        "perPage": result.per_page,
        "total": result.total,
        "pages": result.pages,
    })


@bp.get("/officers")
@roles_required(*STAFF)
def list_officers():
    officers = db.session.execute(
        db.select(User).where(User.role == Role.OFFICER).order_by(User.name)).scalars()
    return jsonify({"items": [
        {"id": o.id, "name": o.name, "department": o.department} for o in officers]})
