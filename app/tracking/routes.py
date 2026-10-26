from flask import Blueprint, jsonify

bp = Blueprint("tracking", __name__)


@bp.get("/ping")
def ping():
    return jsonify({"module": "tracking", "status": "stub - not implemented yet"})
