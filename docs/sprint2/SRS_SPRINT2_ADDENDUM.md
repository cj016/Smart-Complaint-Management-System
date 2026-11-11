# SCMS SRS v1.0 - Sprint 2 implemented addendum

**Post-Sprint 3 update (2026-11-11):** PR #102 is merged; SCMS-F-010 is Citizen-only and SCMS-F-024 now retains prior resolution remarks and resets SLA on reopening. Latest integrated suite: **437 passed**. See [SPRINT3_COMPLETION_UPDATE.md](SPRINT3_COMPLETION_UPDATE.md); QA approval is separate.

**Issue:** #30 (T-04) | **Status:** merged and integration-tested; QA approval pending

## Purpose and cross-reference

This addendum expands the existing requirements in the submitted SRS v1.0, **Section 4.3** (Complaint Tracking & Status Updates), **Section 4.5** (Notifications, Feedback & Reporting), and **Section 8** (RTM). It does **not** change the original submitted PDF. The SRS already lists the status `Reopened` and requirement IDs SCMS-F-024, SCMS-F-041 and SCMS-F-042; the following records the implemented details verified by the integrated automated suite on 9 November 2026.

## SCMS-F-024 - Reopen resolved/closed complaints (Issue #27, PR #97)

**Actor:** authenticated Complainant (Citizen).

- Citizen can request reopening only for a complaint they own and whose current status is `Resolved` or `Closed`.
- Reopening reason is mandatory (nonblank), at most 2,000 characters in this implementation.
- On success the current status becomes `Reopened`; a timestamped `StatusHistory` entry with the reason and actor is created, and an audit action is recorded.
- Reopening clears the previous resolution timestamp (`resolved_at`), but preserves the prior `resolution_remarks` until a new resolution replaces them. A fresh priority-based SLA deadline (`sla_due_at`) is set for the new work cycle.
- An in-app notification is generated for the assigned Officer (if any) and Admin account(s). Staff can view their in-app notifications in a staff inbox.
- Repeated reopening and reopening from any other status are rejected. Requests for complaints not owned by the citizen are not disclosed (404 response).
- The Citizen's My Complaints page offers the reopening action when eligible; tracking timeline shows the new status event.

**Acceptance evidence:** `tests/test_f024_reopen.py` on the F024 branch; nine browser checks manually reported passed. Integrated automated tests passed; QA approval remains pending.

## SCMS-F-041 - Rate resolution and give feedback (Issue #28, PR #98)

**Actor:** authenticated Complainant (Citizen); read access for Admin.

- A citizen can rate **their own complaint in `Resolved` status** using an integer rating from 1 through 5.
- Comment is optional; implementation limit is 1,000 characters.
- Only one feedback record is allowed per complaint, enforced by permission checks and a database uniqueness constraint.
- Duplicate, invalid or out-of-status submissions are rejected; other citizens' complaints are not disclosed.
- Admins can view submitted ratings/comments via a protected API and Admin feedback webpage; Officer/Citizen accounts cannot retrieve the Admin feedback API.

**Acceptance evidence:** `tests/test_f041_feedback.py` on the F041 branch; seven browser checks manually reported passed. Integrated automated tests passed; QA approval remains pending.

## SCMS-F-042 - Category/department reports (Issue #29, PR #99)

**Actor:** authenticated Admin only.

- Reports include total complaints and complaint counts by category, department and current status.
- Date filtering uses **complaint submission (`created_at`) date**, inclusive of the start and end dates; invalid date formats/ranges are rejected.
- Missing/blank departments are grouped as `Unassigned`.
- Average turnaround is the mean elapsed time in hours from complaint creation to recorded resolution, considering **currently `Resolved` or `Closed` complaints with valid resolution timestamps** only. Report the sample count; show `N/A` when no eligible records exist.
- Admin can export the selected summary as CSV. Reports do not need to expose citizen names, contact details, locations or complaint descriptions.
- Citizens and Officers cannot access the protected report endpoints.

**Acceptance evidence:** `tests/test_f042_reports.py` on the F042 branch; eight browser checks manually reported passed. Integrated automated tests passed; QA approval remains pending.

## Integrated verification and outstanding approval

PRs #97, #98 and #99 are merged. On 9 November 2026, the combined automated suite reported **411 passed**, Flake8 passed, and all three mapped RTM requirements were marked **P**. See `INTEGRATION_TEST_RESULTS.md` and `../RTM.md`. These are automated results, not a signed combined browser UAT or QA Lead approval.
