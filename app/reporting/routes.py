from flask import Blueprint, jsonify

bp = Blueprint("reporting", __name__)


@bp.get("/ping")
def ping():
    return jsonify({"module": "reporting", "status": "stub - not implemented yet"})
