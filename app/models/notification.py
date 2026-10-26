from ..extensions import db
from ..utils import utcnow


class Notification(db.Model):
    """In-app / email / SMS notifications (F-023, F-040)."""
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id"))
    channel = db.Column(db.String(10), nullable=False, default="in_app")  # in_app/email/sms
    message = db.Column(db.Text, nullable=False)
    delivery_status = db.Column(db.String(10), nullable=False, default="pending")
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
