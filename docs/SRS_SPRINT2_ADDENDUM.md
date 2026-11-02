# SRS update: F024, F041 and F042

Date: 2026-11-02. Supplements SRS_Team9.pdf sections 4.3, 4.5 and 8.
Scope: issues #27, #28 and #29; implementation prepared for harsh-157-ctrl.
This addendum is for team review; it does not assert QA approval.

## F024: reopen a complaint

An authenticated Complainant may reopen only their own Resolved or Closed complaint.
A nonempty plain-text reason of at most 2000 characters is required. The same complaint
ID is retained. Status becomes Reopened and exactly one timeline entry records the
reason, actor and time. The existing status notification service notifies the citizen;
the assigned staff member and all Admins also receive a reopen notification. The resolution timestamp is cleared and the SLA restarts using
the current priority. Previous resolution remarks, assignee, department, photos and
feedback remain available. A repeated request conflicts rather than duplicating history.
No arbitrary reopening deadline is introduced because the supplied SRS specifies none.

## F041: rate resolution

The owner may submit an integer rating from 1 through 5 with an optional comment of at
most 2000 characters on a Resolved or Closed complaint. One feedback record is allowed
per complaint, matching the existing database constraint. No editing or deletion endpoint
is added. Earlier feedback remains after reopening; a later resolution does not allow a
second rating. A new feedback-per-resolution policy would require team agreement and a
schema migration. Comments and reasons have HTML tags/control characters removed and
are escaped when displayed. Admins can view ratings and comments in the Feedback page
through an Admin-only paginated endpoint.

## F042: resolution reports

Only Admin users may obtain category-wise or department-wise aggregates as JSON or CSV.
Each group includes total, Resolved, Closed, Reopened, completed, open and resolution
percentage. Completed = currently Resolved + Closed; open = total - completed.
Resolution percentage = completed / total * 100, rounded to two decimals. Reopened
complaints count as open. Null/blank departments appear under Unassigned. Empty datasets
return an empty list and total zero. Reports contain aggregate data, not citizen details.

Optional start_date and end_date use inclusive YYYY-MM-DD UTC complaint-submission
dates and apply equally to JSON, CSV and the feedback list. Reversed/invalid dates
return 422. Average turnaround is the average hours from original submission to latest
resolution for currently Resolved/Closed complaints with valid resolved_at timestamps.
Missing or negative durations are excluded, with turnaroundSamples reporting the
number used. No available durations produces null (shown as a dash), never a fabricated
zero. Reopened complaints are excluded until resolved again. The existing schema does
not track a separate clock for each resolution cycle, so the original submission is
the defined start. Admin feedback results omit citizen identity/contact details.
CSV text beginning with a formula marker is prefixed with an apostrophe.

## Acceptance and traceability

See TEST_PLAN_SPRINT2_ADDENDUM.md. docs/RTM.md is generated from tests; P indicates an
automated pass, while A remains reserved for the QA Lead. UI acceptance, review and
merging are separate steps and must be performed on the user's current branch.


Merge this documentation PR after F024, F041 and F042. Reopening is on Track by ID
(also /resolution-actions); citizens/Admins use Feedback (/feedback); Admins use Reports
(/reports). Feature tests: test_reopening.py, test_feedback.py, test_resolution_reports.py.
