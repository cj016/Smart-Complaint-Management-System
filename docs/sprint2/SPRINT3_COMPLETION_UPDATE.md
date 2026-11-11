# Sprint 3 Completion Update for Issue #30

**Verified date:** 2026-11-11  
**Documentation PR:** #101  
**Merged functional correction:** PR #102  
**Integrated main base:** `c9c83de`  
**Documentation branch HEAD at verification:** `e01e25c`

## Scope of the correction

SCMS-F-010 now requires the `Complainant` role at the complaint submission API.
Authenticated Admin and Officer requests are rejected with HTTP 403.

SCMS-F-024 now retains `Complaint.resolution_remarks` from the previous
resolution for context when a Citizen reopens an owned Resolved/Closed
complaint. The previous `resolved_at` is cleared, and `sla_due_at` is reset
from the reopening time according to the configured SLA for the complaint's
priority. The reopening reason is recorded separately in status history.
This supersedes the earlier Sprint 2 wording that both timestamp and
resolution remarks are cleared.

Staff notification creation is performed after the successful reopening
transaction; a notification exception is logged without turning that
committed operation into a failed response. Citizen Lodge and Track pages
clear stored session state and redirect to Login on unauthorized responses.

## Latest integrated automated verification

| Check | Developer-observed result |
|---|---|
| `python -m pytest -q` | 437 passed in 19.21s |
| `python -m flake8 .` | No errors reported |
| `python scripts/generate_rtm.py` | 23 P, 0 F, 10 N; full suite 437 passed in 18.29s |
| SCMS-F-024 / F-041 / F-042 | Each mapped requirement status `P` |

The old 411-test figure recorded in the November 9 Sprint 2 evidence is
retained elsewhere as a **historical baseline**, not a current result.
`docs/RTM.md` is the generated source of truth for RTM statuses, and the
repo's `docs/testing/` and `docs/screenshots/sprint3-browser/` folders
contain separately maintained verification artifacts.

## Manual verification and limitations

The developer reported successful local-browser checks for Citizen lodging,
Admin/Officer submission denial (HTTP 403), reopening, duplicate reopening
denial (HTTP 409), staff notifications, tracking after reopening, and
Lodge/Track expired-session redirects. These reports are not equivalent to
an independent signed user-acceptance test. Photo edge cases and 360px
mobile verification should not be claimed from the available evidence unless
separately checked and recorded. No production TLS, load-capacity, external
SMS/email delivery or QA Lead acceptance is inferred from pytest passing.

## Documentation relationship

This update supplements the original submitted SRS, SAD and Test Plan PDFs,
which remain untouched. See the Sprint 2 SRS/SAD/Test Plan addenda, the
Sprint 2 deviations supplement, `docs/DEVIATIONS.md`, and `docs/RTM.md`.
