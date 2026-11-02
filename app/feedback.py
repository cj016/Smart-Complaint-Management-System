"""F041: owner-only resolution feedback and protected Admin feedback view."""
from datetime import date, datetime, time
import re

from flask import Blueprint, jsonify, render_template, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from .audit.services import record_audit
from .auth.decorators import roles_required
from .errors import error_response
from .extensions import db
from .models import Complaint, Feedback, Role, User
from .sanitize import clean_text

bp = Blueprint("feedback", __name__)
TERMINAL = ("Resolved", "Closed")


def owned_complaint(public_id):
    public_id = public_id.strip().upper()
    if not re.fullmatch(r"SCMS-\d{4}-\d{5}", public_id):
        return None, error_response("VALIDATION_ERROR", "Invalid Complaint ID.", status=422)
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None or user.role != Role.COMPLAINANT:
        return None, error_response("FORBIDDEN", "Citizen account required.", status=403)
    complaint = db.session.execute(db.select(Complaint).where(
        Complaint.public_id == public_id, Complaint.user_id == user.id
    ).with_for_update()).scalar_one_or_none()
    if complaint is None:
        return None, error_response("NOT_FOUND", "Complaint not found.", status=404)
    return complaint, None


def json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def feedback_json(feedback):
    return {"rating": feedback.rating, "comment": feedback.comment,
            "createdAt": feedback.created_at.isoformat() + "Z"}


@bp.route("/api/v1/tracking/by-id/<complaint_id>/feedback", methods=["GET", "POST"])
@jwt_required()
def feedback(complaint_id):
    complaint, error = owned_complaint(complaint_id)
    if error is not None:
        return error
    existing = db.session.execute(db.select(Feedback).where(
        Feedback.complaint_id == complaint.id)).scalar_one_or_none()
    if request.method == "GET":
        return jsonify({"feedback": feedback_json(existing) if existing else None})
    if complaint.status not in TERMINAL:
        return error_response("CONFLICT", "Feedback requires a resolved or closed complaint.",
                              status=409)
    if existing is not None:
        return error_response("CONFLICT", "Feedback has already been submitted.", status=409)
    data = json_body()
    rating = data.get("rating") if data is not None else None
    comment = data.get("comment", "") if data is not None else ""
    if type(rating) is not int or not 1 <= rating <= 5:
        return error_response("VALIDATION_ERROR", "Rating must be an integer from 1 to 5.",
                              status=422)
    if not isinstance(comment, str) or len(comment) > 2000:
        return error_response("VALIDATION_ERROR", "Comment must be at most 2000 characters.",
                              status=422)
    entry = Feedback(complaint_id=complaint.id, user_id=complaint.user_id,
                     rating=rating, comment=clean_text(comment))
    db.session.add(entry)
    try:
        record_audit(complaint.user_id, "FEEDBACK_SUBMITTED", "Complaint",
                     complaint.public_id, f"Resolution rating: {rating}/5")
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response("CONFLICT", "Feedback has already been submitted.", status=409)
    return jsonify({"feedback": feedback_json(entry)}), 201


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


@bp.get("/api/v1/feedback/admin")
@roles_required(Role.ADMIN)
def feedback_report():
    start, end, error = date_range()
    if error is not None:
        return error
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 25))
    except ValueError:
        return error_response("VALIDATION_ERROR", "Invalid pagination.", status=422)
    if page < 1 or not 1 <= per_page <= 100:
        return error_response("VALIDATION_ERROR", "Invalid pagination.", status=422)
    stmt = db.select(Feedback).join(Complaint, Feedback.complaint_id == Complaint.id)
    stmt = dated(stmt, start, end).order_by(Feedback.created_at.desc(), Feedback.id.desc())
    result = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
    items = [{"complaintId": entry.complaint.public_id, "rating": entry.rating,
              "comment": entry.comment, "createdAt": entry.created_at.isoformat() + "Z"}
             for entry in result.items]
    return no_store(jsonify({"items": items, "total": result.total, "page": result.page,
                             "pages": result.pages, "perPage": result.per_page}))


@bp.get("/feedback")
def feedback_page():
    return render_template("feedback.html")
