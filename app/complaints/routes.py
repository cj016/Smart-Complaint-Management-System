from flask import Blueprint, jsonify

bp = Blueprint("complaints", __name__)


@bp.get("/ping")
def ping():
    return jsonify({"module": "complaints", "status": "stub - not implemented yet"})
