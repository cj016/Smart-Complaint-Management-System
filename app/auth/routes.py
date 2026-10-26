from flask import Blueprint, jsonify

bp = Blueprint("auth", __name__)


@bp.get("/ping")
def ping():
    return jsonify({"module": "auth", "status": "stub - not implemented yet"})
