from ..extensions import db
from ..utils import utcnow


class AuditLog(db.Model):
    """Append-only, tamper-evident log (SCMS-SR-004).
    entry_hash = hash(prev_hash + this row's content).
    The hash chain is implemented in app/audit/services.py.
    """
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(60), nullable=False)
    entity_type = db.Column(db.String(40))
    entity_id = db.Column(db.String(40))
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    prev_hash = db.Column(db.String(128))
    entry_hash = db.Column(db.String(128))
