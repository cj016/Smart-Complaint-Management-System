"""SCMS-F-010: a logged-in citizen lodges a new complaint.

POST /api/v1/complaints   (multipart/form-data or JSON)
Fields: category, description, location (mandatory); photos are added in SCMS-F-013.
Requires: Authorization: Bearer <JWT>
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from ..errors import error_response
from ..extensions import db
from ..models import Complaint, StatusHistory, User
from .services import generate_complaint_id
from .validation import validate_complaint_fields, validation_error_response

bp = Blueprint("complaints", __name__)

ID_RETRIES = 3  # if two citizens submit at the same instant, try the next free ID


@bp.get("/ping")
def ping():
    return jsonify({"module": "complaints", "status": "ok"})


@bp.post("")
@jwt_required()
def lodge_complaint():
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        return error_response("UNAUTHORIZED", "Account not found. Please log in again.",
                              status=401)

    data = request.get_json(silent=True) if request.is_json else request.form
    clean, errors = validate_complaint_fields(data)
    if errors:
        return validation_error_response(errors)

    for attempt in range(ID_RETRIES):
        complaint = Complaint(public_id=generate_complaint_id(), user_id=user.id,
                              status="Submitted", **clean)
        complaint.history.append(StatusHistory(status="Submitted", changed_by_id=user.id))
        db.session.add(complaint)
        try:
            db.session.commit()
            break
        except IntegrityError:
            db.session.rollback()
            if attempt == ID_RETRIES - 1:
                return error_response("CONFLICT", "Could not create the complaint. "
                                      "Please try again.", status=409)

    return jsonify({
        "complaintId": complaint.public_id,
        "status": complaint.status,
        "createdAt": complaint.created_at.isoformat() + "Z",
    }), 201
