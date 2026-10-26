from flask import Blueprint, jsonify

bp = Blueprint("admin", __name__)


@bp.get("/ping")
def ping():
    return jsonify({"module": "admin", "status": "stub - not implemented yet"})
