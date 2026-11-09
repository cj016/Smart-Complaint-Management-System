from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from ..extensions import db
from ..models.user import User
from ..utils import utcnow


def roles_required(*roles):
    """Allow the request only if the logged-in user has one of `roles`."""
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()  # 401 if the token is missing or invalid
            user = db.session.get(User, int(get_jwt_identity()))
            if user is None:
                return jsonify(error="Account not found"), 401
            if not user.is_verified or user.role not in roles:
                return jsonify(error="Forbidden"), 403
            if user.locked_until and user.locked_until > utcnow():
                return jsonify(error="Account locked"), 423
            return fn(*args, **kwargs)
        return decorated
    return wrapper