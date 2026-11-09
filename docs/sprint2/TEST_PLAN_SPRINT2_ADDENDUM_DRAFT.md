# SCMS Software Test Plan v1.0 - Sprint 2 test evidence addendum (DRAFT)

**Issue:** #30 (T-04) | **Status:** branch-level evidence, NOT final integrated acceptance

## Basis

Supplements original Test Plan v1.0 Sections **3** (features), **5** (approach), **13** (traceability), **14** (metrics). The original plan names `TC-Track-05`, `TC-Feedback-01`, `TC-Report-01` through the SRS RTM. Work was carried out on separate Git feature branches using Zorin OS, Python virtual environment, pytest, Flake8, and manual browser checks.

## Recorded branch-level results (developer-provided terminal output)

| Requirement | Branch / PR | Automated feature tests | Entire suite on that branch | Lint and diff | Browser evidence | Review status at draft |
|---|---|---|---|---|---|---|
| SCMS-F-024 / TC-Track-05 | `feature/F024-reopen-complaint`, PR #97 | 21 passed (`tests/test_f024_reopen.py`) | 309 passed | Flake8 clean; `git diff --check` clean | 9 of 9 checks reported passed | Open, pending |
| SCMS-F-041 / TC-Feedback-01 | `feature/F041-resolution-feedback`, PR #98 | 40 passed (`tests/test_f041_feedback.py`) | 328 passed | Flake8 clean; `git diff --check` clean | 7 of 7 checks reported passed | Open, pending |
| SCMS-F-042 / TC-Report-01 | `feature/F042-resolution-reports`, PR #99 | 28 passed (`tests/test_f042_reports.py`) | 316 passed | Flake8 clean; `git diff --check` clean | 8 of 8 checks reported passed | Open, pending |

All three corresponding GitHub CI `CI/test (pull_request)` checks were reported successful in the developer's terminal output. **The full-suite totals differ because each branch was based on `main` and did not contain the unmerged features from other PRs. Do not add the totals together.** The developer manually reported the browser checks; screenshots and an independently signed UAT log are not included here.

## Manual acceptance scenarios to retain

- **F024:** Citizen lodges; Admin assigns; Officer resolves; original Citizen reopens with a reason; timeline shows `Reopened`; Admin/Officer see the staff notification; ineligible complaints cannot be reopened.
- **F041:** Citizen rates an owned Resolved complaint 1-5 with optional comment; duplicate/other-owner/unresolved attempts rejected; Admin sees feedback; Officer denied access to Admin API.
- **F042:** Admin sees counts by category/department/status; filters include/exclude expected submission dates; `Unassigned` department and missing turnaround handled; CSV downloads; non-Admin users are denied reporting data.

## Repeatable commands (from project root, right branch)

```bash
python -m pytest -q tests/test_f024_reopen.py  # after F024 merged
python -m pytest -q tests/test_f041_feedback.py  # after F041 merged
python -m pytest -q tests/test_f042_reports.py  # after F042 merged
python -m pytest -q
python -m flake8 .
git diff --check
```

## Required integrated-system exit criteria

- PR #97, #98 and #99 must be merged and their final implementations present on `main`.
- Record `git rev-parse HEAD` and a dated integrated `pytest`/Flake8 log; rerun manual workflows on the combined database/application.
- Verify permission checks and shared route/navigation compatibility after integration.
- Update the RTM using the real test runs, and seek QA Lead approval before changing any status to `A` (Approved).
- Preserve all original submitted PDFs and list deviations without removing old results.

**Open evidence:** No combined integrated test result, final UAT sign-off, deployed uptime/load test, or final QA acceptance has been provided as of this draft.
