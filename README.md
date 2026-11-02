# Smart Complaint Management System (SCMS) - Team 9

Web app for citizens to lodge/track civic complaints and for officers to triage, assign and
resolve them. Built from `SRS_Team9.pdf`, `SAD_Team9 .pdf` and `Test_Plan_Team9.pdf`.

**Stack:** Python 3.12, Flask, SQLAlchemy (ORM), Flask-Migrate, Flask-JWT-Extended,
SQLite for local dev / PostgreSQL target, plain HTML/CSS/JS frontend.

## Sprint 2: harsh-157-ctrl (#27, #28, #29, #30)

Citizens can use the Reopen & Feedback navigation link to reopen their own
resolved/closed complaints and submit one resolution rating. These actions also appear
on the Track by ID page after a resolved/closed complaint is found. Admin users can open Reports and export category- or
department-wise resolution summaries. Existing tables are reused; no migration is needed.

The documentation updates supplement the original submitted PDFs:

- [SRS update](docs/SRS_SPRINT2_ADDENDUM.md)
- [SAD/API update](docs/SAD_SPRINT2_ADDENDUM.md)
- [Test Plan update and manual acceptance](docs/TEST_PLAN_SPRINT2_ADDENDUM.md)
- [Deviations](docs/DEVIATIONS.md)

Run `python -m flake8 .`, `python -m pytest -q`, then
`python scripts/generate_rtm.py` before requesting review. Manual acceptance and QA
approval remain separate. Existing login, notification and database setup are retained.

### Try only these features using disposable data

With the virtual environment active, run `python scripts/demo_harsh_tasks.py`.
Open http://127.0.0.1:5001/login. The script prints demo accounts and sample IDs.
It uses a fresh in-memory database; your normal database is not accessed. Stop with
Ctrl+C. See docs/TEST_PLAN_SPRINT2_ADDENDUM.md for the complete checklist.


The Reports page includes UTC complaint-submission date filters, average turnaround
hours with sample counts, and Admin-only citizen feedback. Reopening notifies the
assigned staff member and Admins using the existing notification service and records
the action through the existing audit service. See the Sprint 2 documentation addenda
for calculation rules and acceptance criteria from issues #27-#30.
