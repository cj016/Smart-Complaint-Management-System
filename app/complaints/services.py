"""Business logic for the complaints module (kept out of routes.py)."""
from sqlalchemy import func

from ..extensions import db
from ..models import Complaint
from ..utils import utcnow

# Sequence numbers from this value up are reserved for demo data
# (scripts/seed_demo.py uses SCMS-YYYY-9NNNN) and never used for real complaints.
DEMO_RANGE_START = 90000


def generate_complaint_id(year=None):
    """Return the next unique Complaint ID, format SCMS-YYYY-NNNNN (SCMS-F-011).

    Example: SCMS-2026-00042. The counter restarts at 00001 every year.
    The database also enforces uniqueness (complaints.public_id is UNIQUE), so
    if two requests ever collide, the second insert fails instead of duplicating.
    """
    year = year or utcnow().year
    prefix = f"SCMS-{year}-"

    # Largest existing number for this year, ignoring the demo range.
    seq = db.func.cast(func.substr(Complaint.public_id, len(prefix) + 1), db.Integer)
    highest = db.session.execute(
        db.select(func.max(seq)).where(
            Complaint.public_id.like(f"{prefix}%"),
            seq < DEMO_RANGE_START,
        )
    ).scalar()

    return f"{prefix}{(highest or 0) + 1:05d}"
