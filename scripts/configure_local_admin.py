"""Prompt for a fixed demo Admin password and store its hash in the local database.

Password is intentionally NOT hard-coded in the Git repository or bypassed in routes.
"""
from getpass import getpass
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
if os.environ.get("APP_ENV", "development") != "development":
    raise SystemExit("Use APP_ENV=development for this demo-only setup.")
secret = getpass("Choose fixed local Admin password (12+ characters): ")
confirm = getpass("Confirm password: ")
if len(secret) < 12 or secret != confirm:
    raise SystemExit("Passwords must match and contain at least 12 characters.")
os.environ["SCMS_DEMO_ADMIN_PASSWORD"] = secret
subprocess.run([sys.executable, str(ROOT / "scripts/seed_fixed_admin.py"),
                "--reset-existing"], check=True)
print("Admin email: admin@scms.test. Keep your chosen demo password privately.")
print("No plaintext password or JWT was written to the project files.")
