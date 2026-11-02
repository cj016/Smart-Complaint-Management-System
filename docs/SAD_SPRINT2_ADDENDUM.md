# SAD update: citizen actions and reports

Date: 2026-11-02. Supplements SAD_Team9 .pdf API/module design.

| Method | URL | Access | Body / result |
|---|---|---|---|
| POST | /api/v1/tracking/by-id/{id}/reopen | Owning Complainant | {"reason":"Still unresolved"}; complaint JSON, 200 |
| GET | /api/v1/tracking/by-id/{id}/feedback | Owning Complainant | {"feedback":null} or saved feedback, 200 |
| POST | /api/v1/tracking/by-id/{id}/feedback | Owning Complainant | {"rating":4,"comment":"Good"}; feedback JSON, 201 |
| GET | /api/v1/reports?group_by=category&format=json | Admin | groupBy, items, totalComplaints |
| GET | /api/v1/reports?group_by=department&format=csv | Admin | CSV attachment |
| GET | /resolution-actions | Public HTML shell | Citizen Reopen & Feedback page |
| GET | /api/v1/feedback/admin?page=1&per_page=25 | Admin | complaintId, rating, comment, createdAt; paginated |
| GET | /reports | Public HTML shell | Admin data fetched via protected API |

JWT Bearer authentication uses the existing login/session convention. Missing tokens
return 401, wrong roles 403, missing or another citizen's complaint 404, invalid input
422 and state/duplicate conflicts 409. Error responses use the existing error envelope.

app/reopening.py and app/feedback.py owns the new citizen endpoints. Existing tracking GET handlers
remain unchanged. app/reporting/routes.py aggregates in SQL rather than loading every
complaint. Track HTML loads an additional script for reopen/feedback forms; /reports
loads reports.js and the navigation link is visible to Admin accounts only. UI role
checks are cosmetic; the server is authoritative.

Existing Complaint, StatusHistory and Feedback tables are reused. No migration, database
recreation, credential change or production seed is required. Reopen uses a conditional
status UPDATE plus a timeline INSERT in one transaction. Feedback uses a complaint row
lock on databases that support it and the existing unique complaint constraint for
duplicate protection; integrity conflicts roll back. Tests cover sequential duplicate
submissions. PostgreSQL concurrency and production-load testing are not claimed.

Report responses are marked no-store. DOM rendering uses textContent. Reopening reuses the existing notify_status_change service after the business transaction
commits. Reopening and feedback append entries through record_audit in the same
transaction as the corresponding action. No notification or audit implementation is
changed. Configured channel delivery behavior remains owned by the existing services;
no external delivery credentials are introduced. General CSRF work is outside this patch.


## Date range, turnaround and staff notifications

Report and feedback GET endpoints accept start_date/end_date, interpreted as inclusive
UTC complaint-submission dates. Groups additionally return averageTurnaroundHours and
turnaroundSamples; CSV includes both fields. Duration calculation streams only timestamps
and group labels, avoiding backend-specific date functions and citizen details.
Feedback pagination accepts per_page 1-100 (default 25) and page >= 1.

Reopening uses create_notification for the assigned staff member and all Admins,
deduplicating recipient IDs. No staff notification appears on a rejected duplicate reopen.
Feedback ratings/comments are visible to Admins through the Feedback page and protected
feedback endpoint. Date filters use the complaint creation date, not feedback creation.


Merge this documentation PR after F024, F041 and F042. Reopening is on Track by ID
(also /resolution-actions); citizens/Admins use Feedback (/feedback); Admins use Reports
(/reports). Feature tests: test_reopening.py, test_feedback.py, test_resolution_reports.py.
