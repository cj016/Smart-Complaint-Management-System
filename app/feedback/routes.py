"""SCMS-F041: one citizen rating per resolved complaint; admin-only review."""
from flask import Blueprint, jsonify, render_template, request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from ..auth.decorators import roles_required
from ..errors import error_response
from ..extensions import db
from ..models import Complaint, Feedback, Role, User

bp = Blueprint("feedback", __name__)
MAX_COMMENT = 1000


def _iso(value):
    return value.isoformat() + "Z" if value else None


@bp.get("/feedback")
def citizen_page():
    return render_template("feedback.html")


@bp.get("/admin/feedback")
def admin_page():
    return render_template("admin_feedback.html")


@bp.post("/api/v1/complaints/<public_id>/feedback")
@roles_required(Role.COMPLAINANT)
def submit_feedback(public_id):
    """Only the owner may rate a complaint currently in Resolved status."""
    actor = db.session.get(User, int(get_jwt_identity()))
    complaint = db.session.execute(
        db.select(Complaint).where(Complaint.public_id == public_id.strip().upper())
    ).scalar_one_or_none()

    # Using 404 for foreign complaints avoids revealing their existence.
    if complaint is None or complaint.user_id != actor.id:
        return error_response("NOT_FOUND", "Complaint not found.", status=404)

    if complaint.status != "Resolved":
        return error_response("CONFLICT",
                              "Only resolved complaints can be rated.", status=409)

    if complaint.feedback is not None:
        return error_response("CONFLICT",
                              "Feedback was already submitted for this complaint.",
                              status=409)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("VALIDATION_ERROR", "A JSON object is required.",
                              status=422)

    rating = data.get("rating")
    if type(rating) is not int or not 1 <= rating <= 5:
        return error_response("VALIDATION_ERROR",
                              "Rating must be a whole number from 1 to 5.",
                              {"field": "rating"}, 422)

    comment = data.get("comment")
    if comment is not None and not isinstance(comment, str):
        return error_response("VALIDATION_ERROR", "Comment must be text.",
                              {"field": "comment"}, 422)
    comment = comment.strip() if comment is not None else ""
    if len(comment) > MAX_COMMENT:
        return error_response("VALIDATION_ERROR",
                              f"Comment must be at most {MAX_COMMENT} characters.",
                              {"field": "comment"}, 422)

    feedback = Feedback(
        complaint_id=complaint.id, user_id=actor.id,
        rating=rating, comment=comment or None,
    )
    db.session.add(feedback)
    try:
        db.session.commit()
    except IntegrityError:
        # The model's unique complaint_id also prevents simultaneous submissions.
        db.session.rollback()
        return error_response("CONFLICT",
                              "Feedback was already submitted for this complaint.",
                              status=409)

    return jsonify({
        "complaintId": complaint.public_id,
        "rating": feedback.rating,
        "comment": feedback.comment,
        "createdAt": _iso(feedback.created_at),
    }), 201


@bp.get("/api/v1/admin/feedback")
@roles_required(Role.ADMIN)
def list_feedback():
    """Admin-only paginated list; never reveals citizen contact details."""
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
    except (ValueError, TypeError):
        return error_response("VALIDATION_ERROR",
                              "page and per_page must be integers.", status=422)
    if page < 1 or per_page < 1:
        return error_response("VALIDATION_ERROR",
                              "page and per_page must be positive.", status=422)
    per_page = min(per_page, 50)

    stmt = (db.select(Feedback)
            .options(selectinload(Feedback.complaint))
            .order_by(Feedback.created_at.desc(), Feedback.id.desc()))
    result = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [{
            "complaintId": item.complaint.public_id,
            "category": item.complaint.category,
            "status": item.complaint.status,
            "rating": item.rating,
            "comment": item.comment,
            "createdAt": _iso(item.created_at),
        } for item in result.items],
        "page": result.page,
        "perPage": result.per_page,
        "total": result.total,
        "pages": result.pages,
    })
