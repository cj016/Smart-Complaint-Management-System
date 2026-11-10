"""Run the existing overdue-escalation service as a scheduled background job."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv  # noqa: E402
load_dotenv()
from app import create_app  # noqa: E402
from app.admin.services import escalate_overdue  # noqa: E402


def main():
    app = create_app()
    with app.app_context():
        rows = escalate_overdue(actor_id=None)
        print(f"SLA job completed: escalated {len(rows)} complaint(s).")


if __name__ == "__main__":
    main()
