"""Create a verified Admin or Officer locally, never through public registration.

Example: python scripts/create_user.py --name "Demo Admin" --email admin@scms.test --role Admin
Password is prompted securely, not passed on the shell command line.
"""
import argparse
from getpass import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.user import Role, User  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", required=True, choices=[Role.ADMIN, Role.OFFICER])
    parser.add_argument("--department", default=None)
    args = parser.parse_args()

    password = getpass("Enter new staff password (at least 8 characters): ")
    confirm = getpass("Confirm password: ")
    if len(password) < 8 or password != confirm:
        parser.error("Passwords must match and contain at least 8 characters")

    email = args.email.strip().lower()
    app = create_app()
    with app.app_context():
        if User.query.filter_by(email=email).first():
            parser.error("Email already exists (no account modified)")
        user = User(name=args.name.strip(), email=email, role=args.role,
                    department=args.department, is_verified=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Created {email} as {args.role}")


if __name__ == "__main__":
    main()
