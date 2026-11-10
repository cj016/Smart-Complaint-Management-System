# Smart Complaint Management System (SCMS)

Software Engineering project - Team 9.

SCMS is a web application where citizens can register, lodge complaints and track their status. Admins can assign complaints to officers, and officers can update their assigned complaints.

## Technologies used

- Python, Flask and SQLAlchemy
- HTML, CSS and JavaScript
- SQLite for local development
- GitHub for version control and project tracking

## Main features

- Citizen registration and login
- Complaint submission with photos
- Complaint tracking and status timeline
- Admin and Officer dashboard
- Complaint assignment, reassignment and SLA escalation
- Notifications, feedback and reports

## How to run

1. Clone the repository and open it in VS Code.
2. Create a Python virtual environment.
3. Install dependencies:

    pip install -r requirements.txt

4. Copy `.env.example` to `.env` if `.env` does not exist.
5. Set the secret keys and a valid Fernet encryption key in `.env`.
6. Run the database migrations:

    python -m flask --app run.py db upgrade

7. Start the application:

    python run.py

Open http://127.0.0.1:5000 in your browser.

For a local demo Admin account, run:

    python scripts/configure_local_admin.py

The Admin email is `admin@scms.test`. The password is chosen locally and is not included in the repository.

## Testing

Run all automated tests:

    python -m pytest -q

Check code formatting:

    python -m flake8 .

The project also has browser smoke tests in `scripts/sprint3_browser_smoke.py`. These need a running local server, Playwright and demo accounts.

## Project files

- `app/` - Backend, templates and static files
- `tests/` - Automated tests
- `scripts/` - Setup and utility scripts
- `migrations/` - Database migrations
- `docs/` - Project documentation and evidence

The original SRS, SAD and Test Plan PDFs are available in the repository.
