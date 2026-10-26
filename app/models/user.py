from ..extensions import db
from ..utils import utcnow


class Role:
    COMPLAINANT = "Complainant"
    OFFICER = "Officer"
    ADMIN = "Admin"


class User(db.Model):
    """Citizens, officers and admins (SRS 2.3). Auth fields support F-001..F-004."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    mobile = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.String(255), nullable=False)  # never plaintext (F-003)
    role = db.Column(db.String(20), nullable=False, default=Role.COMPLAINANT)
    department = db.Column(db.String(100))
    is_verified = db.Column(db.Boolean, nullable=False, default=False)  # OTP done (F-001)
    failed_login_count = db.Column(db.Integer, nullable=False, default=0)  # F-004
    locked_until = db.Column(db.DateTime)  # F-004
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    complaints = db.relationship(
        "Complaint", foreign_keys="Complaint.user_id", back_populates="complainant")
    assigned_complaints = db.relationship(
        "Complaint", foreign_keys="Complaint.assigned_to_id", back_populates="assignee")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class OtpCode(db.Model):
    """One-time codes for email/mobile verification (SCMS-F-001)."""
    __tablename__ = "otp_codes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    code_hash = db.Column(db.String(255), nullable=False)
    purpose = db.Column(db.String(30), nullable=False, default="registration")
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
