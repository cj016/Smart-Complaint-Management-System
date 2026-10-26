from flask import Blueprint, jsonify
from sqlalchemy import text

from .extensions import db

bp = Blueprint("health", __name__)


@bp.get("/api/v1/health")
def health():
    db.session.execute(text("SELECT 1"))
    return jsonify({"status": "ok", "service": "SCMS"})
