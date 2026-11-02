"""Controller: HTTP endpoint for the sample module."""

from flask import Blueprint, jsonify, request

from .services import prepare_feedback

bp = Blueprint("sample_feedback", __name__)


@bp.post("/")
def submit_feedback():
    data = request.get_json(silent=True) or {}

    try:
        feedback = prepare_feedback(data.get("message"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422

    return jsonify({
        "message": feedback.message,
        "status": "accepted",
    }), 201
