from flask import Blueprint, jsonify

bp = Blueprint("notifications", __name__)


@bp.get("/ping")
def ping():
    return jsonify({"module": "notifications", "status": "stub - not implemented yet"})
