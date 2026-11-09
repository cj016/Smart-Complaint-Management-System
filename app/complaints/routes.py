"""Complaint endpoints.

SCMS-F-010: POST /api/v1/complaints  - a logged-in citizen lodges a new complaint
            (multipart/form-data or JSON; optional "photos" files, see SCMS-F-013).
SCMS-F-013: POST/GET /api/v1/complaints/<id>/photos[/<photo_id>] - photo evidence.
All endpoints require: Authorization: Bearer <JWT>
"""
from datetime import timedelta

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from ..admin.services import sla_hours
from ..audit.services import record_audit
from ..auth.decorators import roles_required
from ..errors import error_response
from ..extensions import db
from ..models import Complaint, Role, StatusHistory, User
from ..notifications.services import create_notification
from ..utils import utcnow
from .photos import MIME_TYPES, PhotoError, attach_photos, photo_path, remove_files
from .services import generate_complaint_id
from .validation import validate_complaint_fields, validation_error_response

bp = Blueprint("complaints", __name__)

ID_RETRIES = 3  # if two citizens submit at the same instant, try the next free ID


@bp.get("/ping")
def ping():
    return jsonify({"module": "complaints", "status": "ok"})


@bp.errorhandler(PhotoError)
def handle_photo_error(exc):
    return error_response(exc.code, exc.message, exc.details, exc.status)


# ---- SCMS-F010: lodge a complaint ----------------------------------------------------

@bp.post("")
@roles_required(Role.COMPLAINANT)
def lodge_complaint():
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        return error_response("UNAUTHORIZED", "Account not found. Please log in again.",
                              status=401)

    data = request.get_json(silent=True) if request.is_json else request.form
    clean, errors = validate_complaint_fields(data)
    if errors:
        return validation_error_response(errors)
    files = [f for f in request.files.getlist("photos") if f and f.filename]

    for attempt in range(ID_RETRIES):
        complaint = Complaint(public_id=generate_complaint_id(), user_id=user.id,
                              status="Submitted", **clean)
        complaint.history.append(StatusHistory(status="Submitted", changed_by_id=user.id))
        db.session.add(complaint)
        try:
            db.session.flush()  # reserves the ID; fails if another request just took it
            break
        except IntegrityError:
            db.session.rollback()
            if attempt == ID_RETRIES - 1:
                return error_response("CONFLICT", "Could not create the complaint. "
                                      "Please try again.", status=409)

    rows = []
    try:
        if files:  # all-or-nothing: a bad photo means the complaint is not saved either
            rows = attach_photos(complaint, files)
        db.session.commit()
    except PhotoError:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        remove_files(rows)
        raise

    return jsonify({
        "complaintId": complaint.public_id,
        "status": complaint.status,
        "createdAt": complaint.created_at.isoformat() + "Z",
        "photos": len(rows),
    }), 201


# ---- SCMS-F024: a citizen reopens a resolved / closed complaint -------------------

MAX_REOPEN_REASON = 2000


@bp.post("/<public_id>/reopen")
@roles_required(Role.COMPLAINANT)
def reopen_complaint(public_id):
    """Only the owner may reopen a Resolved/Closed complaint, with a reason."""
    complaint = _find_complaint(public_id.strip().upper(), owner_only=True)
    if complaint is None:
        return _not_found()  # do not reveal someone else's complaint

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("VALIDATION_ERROR", "A JSON object is required.",
                              {"field": "reason"}, 422)
    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        return error_response("VALIDATION_ERROR", "Reopening reason is required.",
                              {"field": "reason"}, 422)
    reason = reason.strip()
    if len(reason) > MAX_REOPEN_REASON:
        return error_response("VALIDATION_ERROR", "Reason must be at most 2000 characters.",
                              {"field": "reason"}, 422)

    # Reopening starts a fresh SLA clock, without changing the original complaint ID.
    now = utcnow()
    new_sla_due = now + timedelta(hours=sla_hours(complaint.priority))
    # A conditional UPDATE also prevents two near-simultaneous requests reopening
    # the same resolved/closed state twice.
    changed = db.session.execute(
        db.update(Complaint)
        .where(Complaint.id == complaint.id,
               Complaint.status.in_(("Resolved", "Closed")))
        .values(status="Reopened", resolved_at=None, sla_due_at=new_sla_due)
    )
    if changed.rowcount != 1:
        db.session.rollback()
        return error_response("CONFLICT", "Only Resolved or Closed complaints can be reopened.",
                              {"status": complaint.status}, 409)

    db.session.add(StatusHistory(
        complaint_id=complaint.id,
        status="Reopened",
        remarks=reason,
        changed_by_id=int(get_jwt_identity()),
    ))
    record_audit(int(get_jwt_identity()), "COMPLAINT_REOPENED",
                 "Complaint", complaint.public_id, "Citizen reopened the complaint")
    db.session.commit()

    # Existing notification service creates in-app records (and configured
    # email/SMS). Notify the assigned officer and all administrators, once each.
    recipient_ids = set(db.session.scalars(
        db.select(User.id).where(User.role == Role.ADMIN)
    ).all())
    if complaint.assigned_to_id is not None:
        recipient_ids.add(complaint.assigned_to_id)
    for recipient_id in sorted(recipient_ids):
        try:
            create_notification(
                recipient_id,
                f"Complaint {complaint.public_id} was reopened by its citizen.",
                complaint.id,
            )
        except Exception:
            # Reopen and audit were already committed. Avoid reporting a false
            # failure/encouraging a duplicate retry because notification failed.
            db.session.rollback()
            current_app.logger.exception("Reopen staff notification failed")

    return jsonify({"complaintId": complaint.public_id, "status": "Reopened",
                    "message": "Complaint reopened successfully."})


# ---- SCMS-F013: photo evidence -------------------------------------------------------

def _iso(dt):
    return dt.isoformat() + "Z" if dt else None


def serialize_photo(complaint, photo):
    return {
        "id": photo.id,
        "originalName": photo.original_name,
        "sizeBytes": photo.size_bytes,
        "uploadedAt": _iso(photo.uploaded_at),
        "url": f"/api/v1/complaints/{complaint.public_id}/photos/{photo.id}",
    }


def _find_complaint(public_id, owner_only):
    """The complaint if the caller may see it, else None (callers answer 404 either way,
    so a stranger cannot tell whether a Complaint ID exists)."""
    user_id = int(get_jwt_identity())
    complaint = db.session.execute(
        db.select(Complaint).where(Complaint.public_id == public_id)).scalar_one_or_none()
    if complaint is None:
        return None
    if complaint.user_id == user_id:
        return complaint
    if not owner_only:
        user = db.session.get(User, user_id)
        if user is not None and user.role in (Role.OFFICER, Role.ADMIN):
            return complaint
    return None


def _not_found():
    return error_response("NOT_FOUND", "Complaint not found.", status=404)


def _photos_body(complaint):
    limit = current_app.config["MAX_PHOTOS"]
    return {
        "complaintId": complaint.public_id,
        "photos": [serialize_photo(complaint, p) for p in complaint.photos],
        "maxPhotos": limit,
        "remaining": max(limit - len(complaint.photos), 0),
    }


@bp.post("/<public_id>/photos")
@jwt_required()
def upload_photos(public_id):
    """Attach 1-3 images (multipart field "photos", 5 MB each) to the caller's complaint."""
    complaint = _find_complaint(public_id, owner_only=True)
    if complaint is None:
        return _not_found()

    rows = attach_photos(complaint, request.files.getlist("photos"))
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        remove_files(rows)
        raise
    return jsonify(_photos_body(complaint)), 201


@bp.get("/<public_id>/photos")
@jwt_required()
def list_photos(public_id):
    complaint = _find_complaint(public_id, owner_only=False)
    if complaint is None:
        return _not_found()
    return jsonify(_photos_body(complaint))


@bp.get("/<public_id>/photos/<int:photo_id>")
@jwt_required()
def get_photo(public_id, photo_id):
    """Photos are private (SAD 6): only the owner or an officer/admin can download them."""
    complaint = _find_complaint(public_id, owner_only=False)
    if complaint is None:
        return _not_found()
    photo = next((p for p in complaint.photos if p.id == photo_id), None)
    if photo is None:
        return error_response("NOT_FOUND", "Photo not found.", status=404)

    path = photo_path(photo)
    if not path.is_file():
        return error_response("NOT_FOUND", "Photo file is missing.", status=404)
    response = send_file(path, mimetype=MIME_TYPES.get(path.suffix, "application/octet-stream"))
    response.headers["Cache-Control"] = "private, max-age=0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
