# Smart Complaint Management System (SCMS) - Team 9

Web app for citizens to lodge/track civic complaints and for officers to triage, assign and
resolve them. Built from `SRS_Team9.pdf`, `SAD_Team9 .pdf` and `Test_Plan_Team9.pdf`.

**Stack:** Python 3.12, Flask, SQLAlchemy (ORM), Flask-Migrate, Flask-JWT-Extended,
SQLite for local dev / PostgreSQL target, plain HTML/CSS/JS frontend.

## Assigned Sprint 2 features and documentation

Four separate PRs cover F024, F041, F042 and T-04; merge this documentation PR last.

- F024: Track by ID lets the owner reopen a Resolved/Closed complaint with a reason,
  updating timeline/SLA, notifying assigned staff/Admins and recording an audit entry.
- F041: Feedback (/feedback) lets citizens submit one 1-5 rating/comment. Admins use
  the same Feedback page to view ratings with pagination and date filtering.
- F042: Admin Reports (/reports) shows category/department resolution counts, average
  turnaround, inclusive UTC date filters and matching CSV.

Updates supplement original PDFs:

- [SRS update](docs/SRS_SPRINT2_ADDENDUM.md)
- [SAD / API update](docs/SAD_SPRINT2_ADDENDUM.md)
- [Test Plan / browser checklist](docs/TEST_PLAN_SPRINT2_ADDENDUM.md)
- [Deviations](docs/DEVIATIONS.md)

Run `python -m flake8 .`, `python -m pytest -q`, then `python scripts/generate_rtm.py`.
The RTM leaves requirements N while separate feature tests are absent and marks P only
once tests exist and pass. QA approval is separate. After all features merge,
`python scripts/demo_harsh_tasks.py` starts a disposable in-memory demo at
http://127.0.0.1:5001/login. No migration or normal-database change is needed for the demo.
