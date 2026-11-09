# SCMS SRS v1.0 - Sprint 2 proposed addendum (DRAFT)

**Issue:** #30 (T-04) | **Status:** provisional, pending merge and QA review

## Purpose and cross-reference

This addendum expands the existing requirements in the submitted SRS v1.0, **Section 4.3** (Complaint Tracking & Status Updates), **Section 4.5** (Notifications, Feedback & Reporting), and **Section 8** (RTM). It does **not** change the original submitted PDF. The SRS already lists the status `Reopened` and requirement IDs SCMS-F-024, SCMS-F-041 and SCMS-F-042; the following records the implemented details subject to integration verification.

## SCMS-F-024 - Reopen resolved/closed complaints (Issue #27, PR #97)

**Actor:** authenticated Complainant (Citizen).

- Citizen can request reopening only for a complaint they own and whose current status is `Resolved` or `Closed`.
- Reopening reason is mandatory (nonblank), at most 2,000 characters in this implementation.
- On success the current status becomes `Reopened`; a timestamped `StatusHistory` entry with the reason and actor is created, and an audit action is recorded.
- The previously recorded resolution timestamp and remarks are cleared for the new work cycle.
- An in-app notification is generated for the assigned Officer (if any) and Admin account(s). Staff can view their in-app notifications in a staff inbox.
- Repeated reopening and reopening from any other status are rejected. Requests for complaints not owned by the citizen are not disclosed (404 response).
- The Citizen's My Complaints page offers the reopening action when eligible; tracking timeline shows the new status event.

**Acceptance evidence:** `tests/test_f024_reopen.py` on the F024 branch; nine browser checks manually reported passed. Not yet integrated/approved.

## SCMS-F-041 - Rate resolution and give feedback (Issue #28, PR #98)

**Actor:** authenticated Complainant (Citizen); read access for Admin.

- A citizen can rate **their own complaint in `Resolved` status** using an integer rating from 1 through 5.
- Comment is optional; implementation limit is 1,000 characters.
- Only one feedback record is allowed per complaint, enforced by permission checks and a database uniqueness constraint.
- Duplicate, invalid or out-of-status submissions are rejected; other citizens' complaints are not disclosed.
- Admins can view submitted ratings/comments via a protected API and Admin feedback webpage; Officer/Citizen accounts cannot retrieve the Admin feedback API.

**Acceptance evidence:** `tests/test_f041_feedback.py` on the F041 branch; seven browser checks manually reported passed. Not yet integrated/approved.

## SCMS-F-042 - Category/department reports (Issue #29, PR #99)

**Actor:** authenticated Admin only.

- Reports include total complaints and complaint counts by category, department and current status.
- Date filtering uses **complaint submission (`created_at`) date**, inclusive of the start and end dates; invalid date formats/ranges are rejected.
- Missing/blank departments are grouped as `Unassigned`.
- Average turnaround is the mean elapsed time in hours from complaint creation to recorded resolution, considering **currently `Resolved` or `Closed` complaints with valid resolution timestamps** only. Report the sample count; show `N/A` when no eligible records exist.
- Admin can export the selected summary as CSV. Reports do not need to expose citizen names, contact details, locations or complaint descriptions.
- Citizens and Officers cannot access the protected report endpoints.

**Acceptance evidence:** `tests/test_f042_reports.py` on the F042 branch; eight browser checks manually reported passed. Not yet integrated/approved.

## Outstanding approval

All three requirements remain **feature-branch verified, not integrated or QA approved** at the time of this draft. The authoritative acceptance result must be updated after feature PRs merge and the combined system is retested.
