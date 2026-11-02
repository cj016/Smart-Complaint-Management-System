from flask import Blueprint, jsonify
from sqlalchemy import text

from .extensions import db
from .utils import utcnow

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    """Liveness + database check, used by uptime monitors (SCMS-NF-002)."""
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        db.session.rollback()
        return jsonify(status="degraded", database="down"), 503
    return jsonify(status="ok", database="up", time=utcnow().isoformat()), 200