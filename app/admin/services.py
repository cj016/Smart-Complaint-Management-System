"""Business rules for the admin module (SCMS-F-030 .. F-035), kept out of routes.py."""
from datetime import timedelta

from flask import current_app
from sqlalchemy import case

from ..extensions import db
from ..models import PRIORITIES, STATUSES, Complaint, StatusHistory
from ..utils import utcnow

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
                          sort="created_at", order="desc", assignee_id=None):
    """SELECT for the admin dashboard with optional filters and a safe sort.

    sort/order must already be validated by the caller (only keys of SORT_COLUMNS).
    assignee_id limits the result to complaints assigned to that user (used for officers).
    """
    stmt = db.select(Complaint)
    if assignee_id is not None:
        stmt = stmt.where(Complaint.assigned_to_id == assignee_id)
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


# ---- SCMS-F034: SLA auto-escalation --------------------------------------------------

# A complaint in one of these states has not been resolved yet, so the SLA still runs.
OPEN_STATUSES = [s for s in STATUSES if s not in ("Resolved", "Closed")]


def sla_hours(priority):
    hours = current_app.config["SLA_HOURS"]
    return hours.get(priority, hours["Medium"])


def sla_due(complaint):
    """When the complaint must be resolved by (sla_due_at, or created_at + SLA hours)."""
    return complaint.sla_due_at or (
        complaint.created_at + timedelta(hours=sla_hours(complaint.priority)))


def escalate_overdue(actor_id=None, now=None):
    """Raise the priority of every open complaint past its SLA by one level.

    The SLA clock restarts for the new priority, so one run never escalates the
    same complaint twice. Returns a list of what was escalated.
    """
    now = now or utcnow()
    open_complaints = db.session.execute(
        db.select(Complaint).where(Complaint.status.in_(OPEN_STATUSES))
    ).scalars().all()

    escalated = []
    for c in open_complaints:
        if sla_due(c) > now:
            continue
        old = c.priority
        index = PRIORITIES.index(old) if old in PRIORITIES else 1
        new = PRIORITIES[min(index + 1, len(PRIORITIES) - 1)]  # stops at Critical
        c.priority = new
        c.sla_due_at = now + timedelta(hours=sla_hours(new))
        c.history.append(StatusHistory(
            status=c.status, changed_by_id=actor_id,
            remarks=f"Escalated: SLA breached (priority {old} to {new})"))
        escalated.append({"complaintId": c.public_id, "from": old, "to": new})
    db.session.commit()
    return escalated
