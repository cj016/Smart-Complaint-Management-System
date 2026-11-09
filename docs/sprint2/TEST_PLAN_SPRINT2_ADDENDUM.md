# SCMS Software Test Plan v1.0 - Sprint 2 test evidence addendum

**Issue:** #30 (T-04) | **Status:** integrated automated testing passed; manual acceptance and QA sign-off pending

## Basis

Supplements original Test Plan v1.0 Sections **3** (features), **5** (approach), **13** (traceability), **14** (metrics). The original plan names `TC-Track-05`, `TC-Feedback-01`, `TC-Report-01` through the SRS RTM. Work was carried out on separate Git feature branches using Zorin OS, Python virtual environment, pytest, Flake8, and manual browser checks.

## Recorded branch-level results (developer-provided terminal output)

| Requirement | Branch / PR | Automated feature tests | Entire suite on that branch | Lint and diff | Browser evidence | Final PR status |
|---|---|---|---|---|---|---|
| SCMS-F-024 / TC-Track-05 | `feature/F024-reopen-complaint`, PR #97 | 21 passed (`tests/test_f024_reopen.py`) | 309 passed | Flake8 clean; `git diff --check` clean | 9 of 9 checks reported passed | Merged |
| SCMS-F-041 / TC-Feedback-01 | `feature/F041-resolution-feedback`, PR #98 | 40 passed (`tests/test_f041_feedback.py`) | 328 passed | Flake8 clean; `git diff --check` clean | 7 of 7 checks reported passed | Merged |
| SCMS-F-042 / TC-Report-01 | `feature/F042-resolution-reports`, PR #99 | 28 passed (`tests/test_f042_reports.py`) | 316 passed | Flake8 clean; `git diff --check` clean | 8 of 8 checks reported passed | Merged |

All three corresponding GitHub CI `CI/test (pull_request)` checks were reported successful in the developer's terminal output. **The full-suite totals differ because each branch was based on `main` and did not contain the unmerged features from other PRs. Do not add the totals together.** The developer manually reported the browser checks; screenshots and an independently signed UAT log are not included here.

## Integrated automated verification (9 November 2026)

- PRs #97, #98 and #99 were merged into `main`; the documentation branch incorporated `origin/main` at `a11db3a`.
- `python -m pytest -q`: **411 passed in 23.24s**.
- `python -m flake8 .`: passed with no reported issues.
- `python scripts/generate_rtm.py`: **23 P, 0 F, 10 N**, full suite **411 passed in 21.82s**.
- Requirements SCMS-F-024, SCMS-F-041 and SCMS-F-042 are **P**, not QA-approved **A**.
- See `INTEGRATION_TEST_RESULTS.md` and `../RTM.md`.

## Manual acceptance scenarios to retain

- **F024:** Citizen lodges; Admin assigns; Officer resolves; original Citizen reopens with a reason; timeline shows `Reopened`; Admin/Officer see the staff notification; ineligible complaints cannot be reopened.
- **F041:** Citizen rates an owned Resolved complaint 1-5 with optional comment; duplicate/other-owner/unresolved attempts rejected; Admin sees feedback; Officer denied access to Admin API.
- **F042:** Admin sees counts by category/department/status; filters include/exclude expected submission dates; `Unassigned` department and missing turnaround handled; CSV downloads; non-Admin users are denied reporting data.

## Repeatable commands (from project root, right branch)

```bash
python -m pytest -q tests/test_f024_reopen.py
python -m pytest -q tests/test_f041_feedback.py
python -m pytest -q tests/test_f042_reports.py
python -m pytest -q
python -m flake8 .
git diff --check
```

## Integration exit criteria and remaining checks

- **Completed:** PRs #97, #98 and #99 merged; 411 automated tests and Flake8 passed on the integrated documentation branch; RTM regenerated.
- **Pending manual evidence:** Repeat the Citizen, Officer and Admin browser scenarios against the combined application and record any results.
- **Pending sign-off:** Obtain QA Lead approval before changing any RTM status to `A` (Approved).
- **Deployment evidence:** Production TLS, uptime and concurrent-load targets are not established by these local automated tests.
- **Document preservation:** The original submitted PDFs remain unchanged; deviations are recorded separately.

**Evidence limitation:** Prior feature-branch browser checks were developer-reported, not a signed combined UAT record.
