from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from ..extensions import db
from ..models.user import User


def roles_required(*roles):
    """Allow the request only if the logged-in user has one of `roles`."""
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()  # 401 if the token is missing or invalid
            user = db.session.get(User, int(get_jwt_identity()))
            if not user or user.role not in roles:
                return jsonify(error="Forbidden"), 403
            return fn(*args, **kwargs)
        return decorated
    return wrapper