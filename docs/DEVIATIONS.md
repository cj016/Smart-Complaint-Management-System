# Deviations from the submitted SRS / SAD / Test Plan
(To be explained during the final demo - see Deliverables Part-2, item 2i.)
Add a row in the SAME pull request that causes a deviation.

| # | Document / section | Document says | What we actually did | Reason | Task |
|---|---|---|---|---|---|
| 1 | SRS 2.5; SAD 3.1, 3.6, 5.3 | Requirements and tasks tracked on Jira | Backlog, story points and sprints tracked in a GitHub Project linked to this repo | Deliverables Part-2 asks for the backlog in GitHub | T-01 |
| 2 | SRS 2.4, 3.3; SAD 3.6; Test Plan 6 | PostgreSQL or MySQL, including the test database | SQLite for local development and automated tests (in-memory in CI). PostgreSQL stays the deployment target: psycopg2 is in requirements.txt and only DATABASE_URL changes | Zero setup for the team and fast CI; the ORM keeps the code identical | T-01, T-02 |
| 3 | SRS 2.3, SR-002; SAD 3.9 | Two roles: Complainant and Admin/Officer | Three roles in the data model: Complainant, Officer, Admin (app.models.Role) | Lets RBAC tell officers from admins later without a schema change; Admin/Officer routes stay behind the same checks | T-01 |
| 4 | SRS 3.4, SR-001; SAD 3.6 | TLS 1.2+ on all connections | Local development, CI and the Sprint 1 demo run over plain HTTP on 127.0.0.1. HTTPS/TLS is planned at deployment behind Nginx | No certificates on student laptops; TLS is a deployment setting | T-01 |
| 5 | Test Plan 6 (Selenium); TC-UX-01; SRS NF-004 | Responsive layout verified with Selenium UI automation | Checked manually in browser DevTools at 360, 768, 1280 and 1920px (screenshots in docs/screenshots), plus pytest checks for the viewport tag, status badges and breakpoints | Selenium setup is outside Sprint 1 scope | NF004 |
| 6 | SRS 4.3, SCMS-F-021 | Citizen tracks complaints after logging in (F-002) | The page and API work. Until the login page (F-002) is merged, the demo uses scripts/seed_demo.py, which creates a demo citizen and prints a JWT to store in localStorage under scms_token | Login is another teammate's Sprint 1 item | F021 |

<!-- Add a new row whenever the code differs from the documents. -->
