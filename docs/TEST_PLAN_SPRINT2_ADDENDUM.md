# Test Plan update: TC-Track-05, TC-Feedback-01 and TC-Report-01

Date: 2026-11-02. Supplements Test_Plan_Team9.pdf; T-04 documentation deliverable.

| Case | Automated coverage | Evidence |
|---|---|---|
| TC-Track-05 / F024 | Owner-only reopen, Resolved/Closed success, wrong states, invalid reason, duplicate conflicts, timeline, SLA restart | tests/test_citizen_actions.py |
| TC-Feedback-01 / F041 | Owner-only access, valid integer ratings, invalid types/ranges/comments, terminal states, duplicates, persistence across reopening | tests/test_citizen_actions.py |
| TC-Report-01 / F042 | Admin-only JSON/CSV, empty dataset, category/department totals, Reopened counted as open, invalid parameters, CSV escaping | tests/test_resolution_reports.py |

## Run from the project root with its virtual environment active

```bash
python -m pytest -q tests/test_citizen_actions.py tests/test_resolution_reports.py
python -m flake8 .
python -m pytest -q
python scripts/generate_rtm.py
```

Tests use create_app("testing") with an in-memory SQLite database. Do not point test
fixtures at the development or production database. The RTM generator repeats the full
suite and writes docs/RTM.md; it does not approve requirements on behalf of QA.

## Disposable feature demo

Run `python scripts/demo_harsh_tasks.py` from the project root. Open
http://127.0.0.1:5001/login. This uses in-memory SQLite, not the normal app database.
Stop/restart the script to reset the sample data. Password for all demo accounts:
`SCMS-Demo-2026!` (sample-only).

| Account | Email | Purpose |
|---|---|---|
| Citizen | citizen@scms.example | Reopen and submit feedback |
| Other citizen | other@scms.example | Ownership isolation |
| Admin | admin@scms.example | Report totals and CSV |

| Complaint ID | Initial status | Owner |
|---|---|---|
| SCMS-2026-00001 | Resolved | Citizen |
| SCMS-2026-00002 | Closed | Citizen |
| SCMS-2026-00003 | In Progress | Citizen |
| SCMS-2026-00004 | Resolved | Other citizen |

Before any changes, the report has four complaints: Roads total 2/completed 1/open 1;
Water Supply total 1/completed 1/open 0; Sanitation total 1/completed 1/open 0.
Reopening 00001 changes Roads to total 2/completed 0/open 2. Logging in as Citizen
and searching for 00004 returns not found. No resolution forms appear for 00003.

The additional tests/test_harsh_demo.py smoke test verifies actual login, feedback,
reopening, timeline, report permissions/totals, CSV, and page rendering end to end
through Flask's test client. It does not automate a real browser.

## Manual acceptance on the user's PC (pending)

1. Start the disposable demo above (or your normally configured app). Sign in as Citizen.
   Open Reopen & Feedback from the navigation; use the sample IDs above for the demo.
2. Track an existing Resolved or Closed complaint. Submit feedback; verify it persists
   after reload and cannot be submitted twice.
3. Supply a reopen reason; verify Reopened appears in the timeline and the same ID,
   ownership, attachments and prior resolution history remain intact.
4. Confirm another citizen cannot act on that complaint, and open complaints show no
   resolution-action forms. Backend tests enforce these permissions independently.
5. Sign in as Admin. Open Reports, compare category and department totals with known
   demo complaints, and open the downloaded CSV. Test an empty dataset separately.
6. Check Track and Reports at phone/tablet/desktop widths; keyboard-operate both forms.
7. Review the documentation addenda/deviations and obtain team review before merging.

Automated checks do not substitute for visual acceptance, load testing, live email/SMS
integration or PostgreSQL concurrent-request tests. No fabricated screenshots or sign-off
are included.

## Integration with current main

Reopening also verifies one in-app status notification and a valid audit entry; feedback
verifies an audit entry. Repeated rejected requests must not create duplicate entries.
These use the existing shared notification and audit services from current main.


## Additional acceptance checks from GitHub issues #27-#29

- F024: verify assigned officer and Admin receive the reopen notification, and the
  audit chain verifies. Rejected repeated reopening creates no additional notifications.
- F041: after submitting a rating as Citizen, sign in as Admin and confirm the rating
  and comment appear under Citizen resolution feedback on Reports.
- F042: change From/To dates and reload; JSON, displayed rows and CSV must use the
  same inclusive UTC complaint-submission window. Invalid/reversed dates show an error.
- F042: verify Average turnaround (hours) and Timed completions. For two completed
  complaints with durations 2 and 6 hours, average is 4 hours with 2 samples. Missing
  timestamps and currently Reopened complaints are excluded.

These additions are covered by tests/test_resolution_reports.py and
 tests/test_citizen_actions.py. Local browser rechecks of these added acceptance details
remain pending; screenshots supplied earlier show page loading, not these outcomes.
