"""Seed one fixed-email Admin for LOCAL demo; password comes from an environment secret."""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv  # noqa: E402
load_dotenv()
from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Role, User  # noqa: E402

EMAIL = "admin@scms.test"  # Fixed demo username, not an authentication bypass.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset-existing", action="store_true",
                        help="Explicitly update password for the existing demo Admin")
    args = parser.parse_args()
    if os.getenv("APP_ENV", "development") != "development":
        raise SystemExit("Demo seed cannot run outside development.")
    password = os.getenv("SCMS_DEMO_ADMIN_PASSWORD", "")
    if len(password) < 12:
        raise SystemExit("Set a local SCMS_DEMO_ADMIN_PASSWORD (12+ chars). Never commit it.")
    app = create_app("development")
    with app.app_context():
        user = User.query.filter_by(email=EMAIL).first()
        if user and user.role != Role.ADMIN:
            raise SystemExit("That email belongs to a non-Admin. Refusing privilege escalation.")
        if user is None:
            user = User(name="Demo Admin", email=EMAIL, role=Role.ADMIN, is_verified=True)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print("Created local Admin:", EMAIL)
        elif args.reset_existing:
            user.set_password(password)
            user.is_verified = True
            db.session.commit()
            print("Updated password for existing local demo Admin:", EMAIL)
        else:
            print("Admin exists; password unchanged. Use --reset-existing if needed:", EMAIL)
    print("Sign in at /login with the password set locally. Do not share it.")


if __name__ == "__main__":
    main()
