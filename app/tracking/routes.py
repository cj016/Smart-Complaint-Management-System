"""SCMS-F-021: a logged-in citizen can track the status of all their own complaints.

GET /api/v1/tracking/my-complaints?status=&page=&per_page=
Requires: Authorization: Bearer <JWT>  (identity = str(user.id), see docs/CONVENTIONS.md)

SCMS-F-020: track one complaint by its Complaint ID.
GET /api/v1/tracking/by-id/<complaint_id>
"""
import re

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..errors import error_response
from ..extensions import db
from ..models import STATUSES, Complaint, Role, User

bp = Blueprint("tracking", __name__)

COMPLAINT_ID_FORMAT = re.compile(r"^SCMS-\d{4}-\d{5}$")


def _iso(dt):
    return dt.isoformat() + "Z" if dt else None


def serialize_complaint(c):
    return {
        "complaintId": c.public_id,
        "category": c.category,
        "location": c.location,
        "status": c.status,
        "priority": c.priority,
        "createdAt": _iso(c.created_at),
        "updatedAt": _iso(c.updated_at),
    }


@bp.get("/ping")
def ping():
    return jsonify({"module": "tracking", "status": "ok"})


@bp.get("/by-id/<complaint_id>")
@jwt_required()
def track_by_id(complaint_id):
    """SCMS-F-020: look up one complaint by its Complaint ID (e.g. SCMS-2026-00042).

    Citizens can only see their own complaints; officers and admins can see any.
    Someone else's complaint gets the same 404 as a missing one, so Complaint IDs
    cannot be probed to find out which ones exist.
    """
    complaint_id = complaint_id.strip().upper()
    if not COMPLAINT_ID_FORMAT.match(complaint_id):
        return error_response("VALIDATION_ERROR",
                              "Complaint ID must look like SCMS-2026-00042.",
                              {"field": "complaintId"}, 422)

    user = db.session.get(User, int(get_jwt_identity()))
    complaint = db.session.execute(
        db.select(Complaint).where(Complaint.public_id == complaint_id)).scalar_one_or_none()

    is_staff = user is not None and user.role in (Role.OFFICER, Role.ADMIN)
    if complaint is None or user is None or not (is_staff or complaint.user_id == user.id):
        return error_response("NOT_FOUND", "No complaint found with that ID.", status=404)

    data = serialize_complaint(complaint)
    data["description"] = complaint.description
    data["department"] = complaint.department
    return jsonify(data)


@bp.get("/my-complaints")
@jwt_required()
def my_complaints():
    user_id = int(get_jwt_identity())

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

    status = request.args.get("status")
    if status and status not in STATUSES:
        return error_response("VALIDATION_ERROR", "Unknown status filter.",
                              {"allowed": STATUSES}, 422)

    stmt = db.select(Complaint).where(Complaint.user_id == user_id)
    if status:
        stmt = stmt.where(Complaint.status == status)
    stmt = stmt.order_by(Complaint.created_at.desc(), Complaint.id.desc())

    result = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [serialize_complaint(c) for c in result.items],
        "page": result.page,
        "perPage": result.per_page,
        "total": result.total,
        "pages": result.pages,
    })
