"""SCMS-F-021: a logged-in citizen can track the status of all their own complaints.

GET /api/v1/tracking/my-complaints?status=&page=&per_page=
Requires: Authorization: Bearer <JWT>  (identity = str(user.id), see docs/CONVENTIONS.md)
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..errors import error_response
from ..extensions import db
from ..models import STATUSES, Complaint

bp = Blueprint("tracking", __name__)


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
