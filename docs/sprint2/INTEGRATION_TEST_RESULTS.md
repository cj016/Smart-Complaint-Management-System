# Sprint 2 Integrated Test Results

**LATEST post-Sprint 3 verification (2026-11-11):** On the documentation branch after integrating `origin/main` (`c9c83de`, merge HEAD `e01e25c`): `python -m pytest -q` **437 passed in 19.21s**; `python -m flake8 .` passed; `python scripts/generate_rtm.py` **23 P / 0 F / 10 N**, full suite **437 passed in 18.29s**. The older 411-test results below remain historical Sprint 2 evidence. Manual UAT and QA sign-off are not established by these commands.

## Verification date and revision

- Date: 9 November 2026
- Merged feature PRs: #97 (F024), #98 (F041), #99 (F042)
- Integrated base: `origin/main` at `a11db3a`
- Documentation branch merge commit: `d9cca57`

## Automated verification

| Command | Observed result |
|---|---|
| `python -m pytest -q` | **411 passed in 23.24s** |
| `python -m flake8 .` | **Passed** (no output) |
| `python scripts/generate_rtm.py` | **23 P, 0 F, 10 N**; full suite 411 passed in 21.82s |
| `git diff --check` | **Passed** (no output) |

## Sprint 2 requirement coverage

| Requirement | Automated test | RTM status |
|---|---|---|
| SCMS-F-024 | `tests/test_f024_reopen.py` | P |
| SCMS-F-041 | `tests/test_f041_feedback.py` | P |
| SCMS-F-042 | `tests/test_f042_reports.py` | P |

The authoritative generated matrix is `docs/RTM.md` (relative to the repository root).
`P` means mapped automated tests passed, not independent QA approval.
The ten `N` requirements have no mapped passing automated coverage in the RTM;
these are not reported as test failures.

## Limitations and remaining review

The integration results above are from developer-provided terminal output.
Prior feature-branch browser checks were reported separately; a new combined
manual browser UAT record and QA Lead sign-off have not been supplied.
Local automated tests do not establish production TLS, uptime or load targets.
