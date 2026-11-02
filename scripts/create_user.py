import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.user import User  # noqa: E402


def main(name, email, password, role):
    app = create_app()
    with app.app_context():
        if User.query.filter_by(email=email).first():
            print("User already exists")
            return
        user = User(name=name, email=email, role=role, is_verified=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Created {email} as {role}")


if __name__ == "__main__":
    main(*sys.argv[1:5])