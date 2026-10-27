"""Business rules for the admin module (SCMS-F-030 .. F-033), kept out of routes.py."""
from sqlalchemy import case

from ..extensions import db
from ..models import PRIORITIES, STATUSES, Complaint

# Which status an officer/admin may move a complaint to next (SRS 4.3 timeline).
# "Assigned" is reached through the assign endpoint (F-030) and "Reopened" through the
# citizen's reopen action (F-024), so neither appears as a target here.
TRANSITIONS = {
    "Submitted": ["In Review"],
    "In Review": [],
    "Assigned": ["In Progress"],
    "In Progress": ["Resolved"],
    "Resolved": ["Closed"],
    "Closed": [],
    "Reopened": ["In Review"],
}

# Complaints in these states can still be (re)assigned.
ASSIGNABLE_STATUSES = ["Submitted", "In Review", "Assigned", "In Progress", "Reopened"]
# Assigning moves a complaint to "Assigned" only from these states.
AUTO_ASSIGN_FROM = ["Submitted", "In Review", "Reopened"]

MAX_REMARKS = 2000

# Sort by severity / lifecycle order, not alphabetically.
_priority_rank = case({p: i for i, p in enumerate(PRIORITIES)},
                      value=Complaint.priority, else_=-1)
_status_rank = case({s: i for i, s in enumerate(STATUSES)},
                    value=Complaint.status, else_=-1)

SORT_COLUMNS = {
    "created_at": Complaint.created_at,
    "updated_at": Complaint.updated_at,
    "category": Complaint.category,
    "priority": _priority_rank,
    "status": _status_rank,
}


def build_dashboard_query(category=None, priority=None, status=None,
                          sort="created_at", order="desc"):
    """SELECT for the admin dashboard with optional filters and a safe sort.

    sort/order must already be validated by the caller (only keys of SORT_COLUMNS).
    """
    stmt = db.select(Complaint)
    if category:
        stmt = stmt.where(Complaint.category == category)
    if priority:
        stmt = stmt.where(Complaint.priority == priority)
    if status:
        stmt = stmt.where(Complaint.status == status)

    column = SORT_COLUMNS[sort]
    primary = column.asc() if order == "asc" else column.desc()
    # Complaint.id as tie-breaker keeps paging stable.
    return stmt.order_by(primary, Complaint.id.desc())

