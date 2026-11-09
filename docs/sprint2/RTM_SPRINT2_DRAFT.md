# Provisional Sprint 2 Requirements Traceability Matrix (DRAFT)

**Important:** This is a supplement to SRS Section 8 and the repository's `docs/RTM.md`, **not** an overwrite of its generated statuses.

| Requirement | Original SRS test ID | Implementation / PR | Automated test mapping | Evidence on separate feature branch | Final main status | QA approval |
|---|---|---|---|---|---|---|
| SCMS-F-024: Reopen | TC-Track-05 | `app/complaints/routes.py`, notification routes, Citizen page; #97 | `tests/test_f024_reopen.py` | 21 feature tests, 309 full-suite; manual 9/9 | Pending merge and integrated run | Pending |
| SCMS-F-041: Feedback | TC-Feedback-01 | `app/feedback/routes.py`, Feedback model, Citizen/Admin pages; #98 | `tests/test_f041_feedback.py` | 40 feature tests, 328 full-suite; manual 7/7 | Pending merge and integrated run | Pending |
| SCMS-F-042: Reports | TC-Report-01 | `app/reporting/routes.py`, Admin reports page; #99 | `tests/test_f042_reports.py` | 28 feature tests, 316 full-suite; manual 8/8 | Pending merge and integrated run | Pending |

## Repo RTM generator correction after merging

In `scripts/generate_rtm.py`, the existing requirements SCMS-F-024, SCMS-F-041 and SCMS-F-042 currently map to an **empty test-file list**. That is why the existing generated `docs/RTM.md` marks them `N` (not automated). **Only after their test files are present on merged `main`**, update those mappings to `test_f024_reopen.py`, `test_f041_feedback.py`, `test_f042_reports.py` respectively, and regenerate `docs/RTM.md`. The generator's `P` means tests passed, not independent QA approval (`A`).

## Related but separate work

Issue #95 / PR #96: Admin/Officer/Citizen login navigation fix; 296 tests passed on its branch, with manually verified registration/login. Do not conflate Issue #95 with the Sprint 2 functional IDs above.
