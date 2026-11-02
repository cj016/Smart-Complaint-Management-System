"""F024: owner-only reopening, timeline, staff notifications and audit."""
import re
from datetime import timedelta

from flask import Blueprint, jsonify, render_template, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from .admin.services import sla_hours
from .audit.services import record_audit
from .errors import error_response
from .extensions import db
from .models import Complaint, Role, StatusHistory, User
from .notifications.services import create_notification
from .notifications.status_events import notify_status_change
from .sanitize import clean_text
from .tracking.routes import serialize_complaint
from .utils import utcnow

bp = Blueprint("reopening", __name__)
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


@bp.post("/api/v1/tracking/by-id/<complaint_id>/reopen")
@jwt_required()
def reopen(complaint_id):
    complaint, error = owned_complaint(complaint_id)
    if error is not None:
        return error
    data = json_body()
    reason = data.get("reason") if data is not None else None
    if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 2000:
        return error_response("VALIDATION_ERROR", "Reason must be 1-2000 characters.",
                              status=422)
    reason = clean_text(reason)
    if not reason:
        return error_response("VALIDATION_ERROR", "Reason cannot be empty.", status=422)
    now = utcnow()
    # Conditional update also prevents duplicate reopening on SQLite.
    result = db.session.execute(db.update(Complaint).where(
        Complaint.id == complaint.id, Complaint.status.in_(TERMINAL)
    ).values(status="Reopened", resolved_at=None, updated_at=now,
             sla_due_at=now + timedelta(hours=sla_hours(complaint.priority))))
    if result.rowcount != 1:
        db.session.rollback()
        return error_response("CONFLICT", "Only resolved or closed complaints can reopen.",
                              status=409)
    db.session.add(StatusHistory(complaint_id=complaint.id, status="Reopened",
                                 remarks=reason, changed_by_id=complaint.user_id,
                                 changed_at=now))
    record_audit(complaint.user_id, "COMPLAINT_REOPENED", "Complaint",
                 complaint.public_id, "Reopened by the owning citizen")
    db.session.commit()
    notify_status_change(complaint)
    # Reuse the shared delivery service; assigned staff and admins need to act.
    staff_ids = set(db.session.scalars(
        db.select(User.id).where(User.role == Role.ADMIN)).all())
    if complaint.assigned_to_id is not None:
        staff_ids.add(complaint.assigned_to_id)
    staff_ids.discard(complaint.user_id)
    for staff_id in sorted(staff_ids):
        create_notification(staff_id,
                            f"Complaint {complaint.public_id} was reopened: {reason}",
                            complaint_id=complaint.id)
    return jsonify(serialize_complaint(complaint))


@bp.get("/resolution-actions")
def resolution_actions_page():
    return render_template("track.html", resolution_actions=True)
