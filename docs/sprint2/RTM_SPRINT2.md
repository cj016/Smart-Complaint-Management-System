# Sprint 2 Requirements Traceability Supplement

**Important:** This is a supplement to SRS Section 8 and the repository's `docs/RTM.md`, **not** an overwrite of its generated statuses.

| Requirement | Original SRS test ID | Implementation / PR | Automated test mapping | Historical feature-branch evidence | Integrated automated status | QA approval |
|---|---|---|---|---|---|---|
| SCMS-F-024: Reopen | TC-Track-05 | `app/complaints/routes.py`, notification routes, Citizen page; #97 | `tests/test_f024_reopen.py` | 21 feature tests, 309 full-suite; manual 9/9 | P (9 November 2026) | Pending |
| SCMS-F-041: Feedback | TC-Feedback-01 | `app/feedback/routes.py`, Feedback model, Citizen/Admin pages; #98 | `tests/test_f041_feedback.py` | 40 feature tests, 328 full-suite; manual 7/7 | P (9 November 2026) | Pending |
| SCMS-F-042: Reports | TC-Report-01 | `app/reporting/routes.py`, Admin reports page; #99 | `tests/test_f042_reports.py` | 28 feature tests, 316 full-suite; manual 8/8 | P (9 November 2026) | Pending |

## Generated RTM verification

`scripts/generate_rtm.py` now maps SCMS-F-024, SCMS-F-041 and SCMS-F-042 to `test_f024_reopen.py`, `test_f041_feedback.py` and `test_f042_reports.py`. On 9 November 2026, `docs/RTM.md` was regenerated: **23 P, 0 F, 10 N**, with **411 passed** in the full suite. `P` means automated tests passed; no independent QA approval (`A`) is claimed.

## Related but separate work

Issue #95 / PR #96: Admin/Officer/Citizen login navigation fix; 296 tests passed on its branch, with manually verified registration/login. Do not conflate Issue #95 with the Sprint 2 functional IDs above.
