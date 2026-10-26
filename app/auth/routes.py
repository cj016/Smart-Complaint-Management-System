import secrets
from datetime import timedelta

from .decorators import roles_required

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models.user import OtpCode, Role, User
from ..utils import utcnow

bp = Blueprint("auth", __name__)

OTP_MINUTES = 10
MAX_ATTEMPTS = 5
LOCK_MINUTES = 15  # use the SRS value


@bp.get("/ping")
def ping():
    return jsonify({"module": "auth", "status": "stub - not implemented yet"})


def _send_otp(user, code):
    # Dev stub: prints the OTP in the terminal. Swap for real email/SMS later.
    print(f"[DEV] OTP for {user.email}: {code}")


def _issue_otp(user):
    code = f"{secrets.randbelow(900000) + 100000}"  # 6 digits
    db.session.add(OtpCode(
        user_id=user.id,
        code_hash=generate_password_hash(code),
        purpose="registration",
        expires_at=utcnow() + timedelta(minutes=OTP_MINUTES),
    ))
    db.session.commit()
    _send_otp(user, code)


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    mobile = (data.get("mobile") or "").strip() or None
    password = data.get("password") or ""

    if not name or "@" not in email or len(password) < 8:
        return jsonify(error="Name, valid email and password (min 8 chars) required"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(error="Email already registered"), 409
    if mobile and User.query.filter_by(mobile=mobile).first():
        return jsonify(error="Mobile already registered"), 409

    # role is never taken from the request
    user = User(name=name, email=email, mobile=mobile, role=Role.COMPLAINANT)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    _issue_otp(user)
    return jsonify(message="Registered. Enter the OTP sent to you."), 201


@bp.post("/verify-otp")
def verify_otp():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    user = User.query.filter_by(email=email).first()
    otp = (
        OtpCode.query.filter_by(user_id=user.id, used=False)
        .order_by(OtpCode.id.desc()).first()
        if user else None
    )
    if (not otp or otp.expires_at < utcnow()
            or not check_password_hash(otp.code_hash, str(data.get("otp", "")))):
        return jsonify(error="Invalid or expired OTP"), 400

    otp.used = True
    user.is_verified = True
    db.session.commit()
    return jsonify(message="Account verified"), 200


@bp.post("/resend-otp")
def resend_otp():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if user and not user.is_verified:
        _issue_otp(user)
    return jsonify(message="If the account exists, a new OTP was sent."), 200


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    user = User.query.filter_by(email=email).first()

    if user and user.locked_until and user.locked_until > utcnow():
        return jsonify(error="Account locked. Try again later."), 423

    if not user or not user.check_password(data.get("password") or ""):
        if user:
            user.failed_login_count += 1
            if user.failed_login_count >= MAX_ATTEMPTS:
                user.locked_until = utcnow() + timedelta(minutes=LOCK_MINUTES)
                user.failed_login_count = 0
            db.session.commit()
        return jsonify(error="Invalid email or password"), 401

    user.failed_login_count = 0
    user.locked_until = None
    db.session.commit()

    if not user.is_verified:
        return jsonify(error="Please verify your account first"), 403

    token = create_access_token(
        identity=str(user.id), additional_claims={"role": user.role})
    return jsonify(access_token=token, role=user.role), 200


@bp.get("/admin-check")
@roles_required(Role.ADMIN)
def admin_check():
    return jsonify(message="admin ok")


@bp.get("/staff-check")
@roles_required(Role.OFFICER, Role.ADMIN)
def staff_check():
    return jsonify(message="staff ok")