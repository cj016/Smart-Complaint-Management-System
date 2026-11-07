"""SCMS-F023: Citizen notification inbox API."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from ..auth.decorators import roles_required
from ..errors import error_response
from ..extensions import db
from ..models import Notification, Role

bp = Blueprint("notifications", __name__)


def _serialize(notification):
    return {
        "id": notification.id,
        "complaintId": notification.complaint_id,
        "channel": notification.channel,
        "message": notification.message,
        "deliveryStatus": notification.delivery_status,
        "isRead": notification.is_read,
        "createdAt": (
            notification.created_at.isoformat() + "Z"
            if notification.created_at else None
        ),
    }


@bp.get("/staff")
@roles_required(Role.ADMIN, Role.OFFICER)
def staff_notifications():
    """The signed-in staff member's own in-app notifications (latest 30)."""
    user_id = int(get_jwt_identity())
    rows = db.session.scalars(
        db.select(Notification)
        .where(Notification.user_id == user_id, Notification.channel == "in_app")
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(30)
    ).all()
    unread = db.session.scalar(
        db.select(db.func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.channel == "in_app",
            Notification.is_read.is_(False),
        )
    )
    return jsonify({"items": [_serialize(item) for item in rows],
                    "unreadCount": unread or 0})


@bp.patch("/staff/<int:notification_id>/read")
@roles_required(Role.ADMIN, Role.OFFICER)
def staff_mark_read(notification_id):
    """Mark only this staff user's own in-app notification as read."""
    user_id = int(get_jwt_identity())
    notification = db.session.scalar(
        db.select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
            Notification.channel == "in_app",
        )
    )
    if notification is None:
        return error_response("NOT_FOUND", "Notification not found.", status=404)
    if not notification.is_read:
        notification.is_read = True
        db.session.commit()
    return jsonify(_serialize(notification))


@bp.get("/ping")
def ping():
    return jsonify({
        "module": "notifications",
        "status": "ok",
    })


@bp.get("")
@bp.get("/")
@roles_required(Role.COMPLAINANT)
def list_notifications():
    """List the signed-in citizen's notifications."""
    user_id = int(get_jwt_identity())

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        return error_response(
            "VALIDATION_ERROR",
            "page and per_page must be integers.",
            status=422,
        )

    if page < 1 or per_page < 1:
        return error_response(
            "VALIDATION_ERROR",
            "page and per_page must be positive.",
            status=422,
        )

    per_page = min(per_page, 50)

    stmt = (
        db.select(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.channel == "in_app",
        )
        .order_by(
            Notification.created_at.desc(),
            Notification.id.desc(),
        )
    )

    result = db.paginate(
        stmt,
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return jsonify({
        "items": [_serialize(item) for item in result.items],
        "page": result.page,
        "perPage": result.per_page,
        "pages": result.pages,
        "total": result.total,
    })


@bp.get("/unread-count")
@roles_required(Role.COMPLAINANT)
def unread_count():
    """Count unread in-app notifications for the current citizen."""
    user_id = int(get_jwt_identity())

    count = db.session.scalar(
        db.select(db.func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.channel == "in_app",
            Notification.is_read.is_(False),
        )
    )

    return jsonify({"unreadCount": count or 0})


@bp.patch("/<int:notification_id>/read")
@roles_required(Role.COMPLAINANT)
def mark_read(notification_id):
    """Mark an owned notification as read."""
    user_id = int(get_jwt_identity())

    notification = db.session.execute(
        db.select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    ).scalar_one_or_none()

    if notification is None:
        return error_response(
            "NOT_FOUND",
            "Notification not found.",
            status=404,
        )

    if not notification.is_read:
        notification.is_read = True
        db.session.commit()

    return jsonify(_serialize(notification))
