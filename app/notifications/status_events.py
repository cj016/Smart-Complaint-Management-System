"""SCMS-F040: Notify the citizen after a complaint status change."""

from .services import create_notification


def notify_status_change(complaint):
    """Create the citizen notification for an updated complaint."""
    message = (
        f"Your complaint {complaint.public_id} "
        f"is now {complaint.status}."
    )
    return create_notification(
        user_id=complaint.user_id,
        message=message,
        complaint_id=complaint.id,
    )
