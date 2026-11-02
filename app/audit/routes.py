"""SCMS-SR004: Admin-only audit log endpoints."""

from flask import Blueprint, jsonify

from ..auth.decorators import roles_required
from ..extensions import db
from ..models import AuditLog, Role
from .services import verify_audit_chain

bp = Blueprint("audit", __name__)


@bp.get("/verify")
@roles_required(Role.ADMIN)
def verify():
    """Check whether the stored audit hash chain is intact."""
    return jsonify(verify_audit_chain())


@bp.get("/entries")
@roles_required(Role.ADMIN)
def entries():
    """Show the latest 50 audit records, newest first."""
    rows = db.session.execute(
        db.select(AuditLog)
        .order_by(AuditLog.id.desc())
        .limit(50)
    ).scalars().all()

    return jsonify({
        "items": [
            {
                "id": item.id,
                "actorId": item.actor_id,
                "action": item.action,
                "entityType": item.entity_type,
                "entityId": item.entity_id,
                "details": item.details,
                "createdAt": item.created_at.isoformat() + "Z",
                "entryHash": item.entry_hash,
                "previousHash": item.prev_hash,
            }
            for item in rows
        ]
    })
