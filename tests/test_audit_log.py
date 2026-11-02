"""Tests for SCMS-SR004 audit hash chaining."""

from app.audit.services import record_audit, verify_audit_chain
from app.extensions import db
from app.models import AuditLog


def test_empty_audit_log_is_valid(app):
    with app.app_context():
        assert verify_audit_chain()["valid"] is True


def test_record_creates_hash_linked_entries(app):
    with app.app_context():
        first = record_audit(
            1, "STATUS_CHANGED", "Complaint",
            "SCMS-2026-00001", "Submitted -> In Review"
        )
        db.session.commit()

        second = record_audit(
            1, "STATUS_CHANGED", "Complaint",
            "SCMS-2026-00001", "In Review -> Assigned"
        )
        db.session.commit()

        assert first.entry_hash is not None
        assert second.prev_hash == first.entry_hash
        assert verify_audit_chain()["valid"] is True
        assert verify_audit_chain()["checked"] == 2


def test_modified_entry_is_detected(app):
    with app.app_context():
        entry = record_audit(
            1, "STATUS_CHANGED", "Complaint",
            "SCMS-2026-00001", "Submitted -> In Review"
        )
        db.session.commit()

        # Simulates tampering directly in the database.
        entry.details = "Changed without permission"
        db.session.commit()

        result = verify_audit_chain()

        assert result["valid"] is False
        assert result["brokenAt"] == entry.id


def test_broken_previous_hash_is_detected(app):
    with app.app_context():
        record_audit(
            1, "ASSIGNED", "Complaint",
            "SCMS-2026-00001", "Assigned to officer"
        )
        db.session.commit()

        entry = db.session.scalar(db.select(AuditLog))
        entry.prev_hash = "fake"
        db.session.commit()

        assert verify_audit_chain()["valid"] is False
