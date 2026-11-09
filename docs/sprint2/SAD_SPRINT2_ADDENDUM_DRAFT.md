# SCMS SAD v1.0 - Sprint 2 proposed architecture/API addendum (DRAFT)

**Issue:** #30 (T-04) | **Status:** provisional, pending merge and review

## Reference

Supplements the submitted SAD v1.0 **Section 3.4** (components), **Section 4.3** (API design), and **Section 4.5** (UX design). Implementations reuse Flask blueprints, SQLAlchemy models, JWT role checks, HTML templates, and static JavaScript. No schema migration was added for F024, F041 or F042.

## Components and user flows

- **F024 / ComplaintModule:** `app/complaints/routes.py` implements Citizen reopening; `StatusHistory` records the reason and status; existing audit and notification services are called; `app/static/js/my_complaints.js` and `app/templates/my_complaints.html` expose the action.
- **F024 / NotificationModule:** `app/notifications/routes.py` adds staff notifications; `app/templates/staff_notifications.html`, `app/static/js/staff_notifications.js` provide the staff inbox.
- **F041 / FeedbackModule:** `app/feedback/routes.py` uses existing `Feedback` and `Complaint` models; `feedback.html` and `admin_feedback.html` plus corresponding JS support citizen submission and Admin review.
- **F042 / ReportingModule:** `app/reporting/routes.py` aggregates complaints; `reports.html` and `reports.js` show filtering, counts, turnaround, and CSV export.

## Proposed endpoint inventory

| Requirement | Method and endpoint | Access | Purpose / main constraint |
|---|---|---|---|
| F024 | `POST /api/v1/complaints/<public_id>/reopen` | Complainant owner | Reason required; current status Resolved/Closed; writes history/audit; notifies staff |
| F024 | `GET /api/v1/notifications/staff` | Admin or Officer | Return signed-in staff member's in-app notifications |
| F024 | `PATCH /api/v1/notifications/staff/<notification_id>/read` | Admin or Officer; notification owner | Mark own staff notification as read |
| F041 | `POST /api/v1/complaints/<public_id>/feedback` | Complainant owner | Integer rating 1-5, optional comment, one per complaint, status Resolved |
| F041 | `GET /api/v1/admin/feedback` | Admin only | Paginated feedback view, no citizen contact details |
| F042 | `GET /api/v1/reports/summary` | Admin only | Summary counts and turnaround; optional `start_date` / `end_date` |
| F042 | `GET /api/v1/reports/summary.csv` | Admin only | CSV of same filtered summary |

Webpage routes (HTML): `/feedback`, `/admin/feedback`, `/admin/reports`, `/staff-notifications` (the pages render templates; the APIs enforce data access).

## Data and integrity

- Existing `Complaint`: `public_id`, `user_id`, `category`, `department`, `status`, `created_at`, `resolved_at`, `resolution_remarks`, `assigned_to_id`.
- Existing `StatusHistory`: status, remarks, changed-by, timestamp.
- Existing `Feedback`: complaint FK unique, citizen FK, rating with DB check 1-5, comment, created timestamp.
- Reopening uses a conditional status update to prevent duplicate concurrent reopen transitions; after success it creates timeline and audit records.
- Feedback uses both an application pre-check and a unique database constraint; duplicates are rejected.
- Reports read aggregate dimensions and timestamps, not identifiable citizen fields. CSV output guards against spreadsheet formula interpretation for group names.

## Reporting metric definition

The **date range filters submission timestamps** (`Complaint.created_at`). The turnaround numerator uses `(resolved_at - created_at)` for currently `Resolved`/`Closed` complaints with nonnegative durations; the denominator is the count of those valid samples, **not** every complaint in the filter. When denominator is zero, JSON provides a null average; the UI presents `N/A`.

## Integration/architecture limitations

At draft time #97, #98 and #99 are independent, unmerged PRs and their route changes have not been tested together on `main`. Routes and shared navigation touched by multiple PRs require conflict review. Staff notifications use existing delivery integrations when configured; do not claim external email/SMS delivery was demonstrated. Deployment TLS, load targets, and QA sign-off are outside this feature-branch evidence.
