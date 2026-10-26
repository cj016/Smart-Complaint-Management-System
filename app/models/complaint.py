from ..extensions import db
from ..utils import utcnow

# Status timeline from SRS 4.3 / SAD 4.5
STATUSES = ["Submitted", "In Review", "Assigned", "In Progress",
            "Resolved", "Closed", "Reopened"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]


class Complaint(db.Model):
    """public_id is the citizen-facing Complaint ID, format SCMS-YYYY-NNNNN (F-011)."""
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Submitted", index=True)
    priority = db.Column(db.String(10), nullable=False, default="Medium")
    department = db.Column(db.String(100))
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    resolution_remarks = db.Column(db.Text)
    sla_due_at = db.Column(db.DateTime)  # F-034 auto-escalation
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    resolved_at = db.Column(db.DateTime)

    complainant = db.relationship(
        "User", foreign_keys=[user_id], back_populates="complaints")
    assignee = db.relationship(
        "User", foreign_keys=[assigned_to_id], back_populates="assigned_complaints")
    photos = db.relationship(
        "ComplaintPhoto", back_populates="complaint", cascade="all, delete-orphan")
    history = db.relationship(
        "StatusHistory", back_populates="complaint", cascade="all, delete-orphan",
        order_by="StatusHistory.changed_at")
    feedback = db.relationship(
        "Feedback", back_populates="complaint", uselist=False, cascade="all, delete-orphan")


class ComplaintPhoto(db.Model):
    __tablename__ = "complaint_photos"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id"), nullable=False,
                             index=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255))
    size_bytes = db.Column(db.Integer)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    complaint = db.relationship("Complaint", back_populates="photos")


class StatusHistory(db.Model):
    """One row per status change - powers the timeline (F-022)."""
    __tablename__ = "status_history"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id"), nullable=False,
                             index=True)
    status = db.Column(db.String(20), nullable=False)
    remarks = db.Column(db.Text)
    changed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    changed_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    complaint = db.relationship("Complaint", back_populates="history")


class Feedback(db.Model):
    __tablename__ = "feedback"
    __table_args__ = (db.CheckConstraint("rating >= 1 AND rating <= 5",
                                         name="ck_feedback_rating"),)

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id"), unique=True,
                             nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    complaint = db.relationship("Complaint", back_populates="feedback")
