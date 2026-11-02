"""SCMS-SR004: Simple append-only, hash-linked audit log."""

import hashlib
import json

from ..extensions import db
from ..models import AuditLog
from ..utils import utcnow

GENESIS_HASH = "0" * 64


def _entry_hash(entry):
    """Calculate the hash of all fields that must not change."""
    payload = {
        "actor_id": entry.actor_id,
        "action": entry.action,
        "entity_type": entry.entity_type,
        "entity_id": entry.entity_id,
        "details": entry.details,
        "created_at": entry.created_at.isoformat(),
        "prev_hash": entry.prev_hash,
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def record_audit(actor_id, action, entity_type, entity_id, details=None):
    """Append an audit entry to the current database transaction.

    The caller commits the transaction alongside its business action.
    """
    previous = db.session.execute(
        db.select(AuditLog).order_by(AuditLog.id.desc()).limit(1)
    ).scalar_one_or_none()

    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        details=details,
        created_at=utcnow(),
        prev_hash=previous.entry_hash if previous else GENESIS_HASH,
    )
    entry.entry_hash = _entry_hash(entry)
    db.session.add(entry)
    return entry


def verify_audit_chain():
    """Check the complete chain for altered fields or broken links."""
    entries = db.session.execute(
        db.select(AuditLog).order_by(AuditLog.id.asc())
    ).scalars().all()

    expected_previous = GENESIS_HASH

    for entry in entries:
        if entry.prev_hash != expected_previous:
            return {
                "valid": False,
                "checked": len(entries),
                "brokenAt": entry.id,
            }

        if entry.entry_hash != _entry_hash(entry):
            return {
                "valid": False,
                "checked": len(entries),
                "brokenAt": entry.id,
            }

        expected_previous = entry.entry_hash

    return {
        "valid": True,
        "checked": len(entries),
        "brokenAt": None,
    }
