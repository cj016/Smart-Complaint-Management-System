# Sprint 2 implementation refinements and deviations

**Sprint 3 reconciliation (2026-11-11):** A correction to the reopening behavior below reflects merged PR #102: prior resolution remarks are preserved and the SLA deadline restarts. See [SPRINT3_COMPLETION_UPDATE.md](SPRINT3_COMPLETION_UPDATE.md).

**Issue:** #30 (T-04) | **Status:** merged and automated integration-tested; QA review pending.

The original SRS/SAD describe high-level features. The following details are implementation refinements, **not necessarily contradictions** of the original specification. The historical repository deviations remain in `docs/DEVIATIONS.md`; this supplement records the Sprint 2 refinements after integration.

| Original reference | Implemented detail / extension | Why it was chosen | Issue / PR |
|---|---|---|---|
| SRS 4.3 (F-024); SAD 3.4, 4.3 | Reopening requires a nonblank reason (max 2,000 chars), only owner, from Resolved/Closed; creates `Reopened` timeline/audit, clears the old resolution timestamp, preserves the prior resolution remarks, and starts a new priority-based SLA deadline | Explicit authorization and consistent new workflow cycle | #27 / #97 |
| SRS 4.3 (F-024, notifications); SAD NotificationModule | Staff in-app inbox for assigned Officer and Admins, rather than relying only on Citizen inbox; external email/SMS depends on configuration | Staff must be able to see reopening events | #27 / #97 |
| SRS 4.5 (F-041); SAD Citizen UI | Feedback requires owner and current Resolved status, integer 1-5, optional comment up to 1,000 chars, one row per complaint | Enforce single submission and consistent validation | #28 / #98 |
| SRS 4.5 (F-042); SAD ReportingModule | Date range filters complaint **submission date**, missing department shown as `Unassigned`, mean turnaround only from eligible Resolved/Closed records; null -> N/A | Avoid misleading turnaround metrics and ambiguous date scope | #29 / #99 |
| SRS 4.5 (F-042); SAD API examples | Added CSV export of filtered aggregate reports with guarded spreadsheet content | Allow simple faculty demo/report download without disclosing citizen data | #29 / #99 |
| SRS Section 8 (RTM); existing `docs/RTM.md` | Merged feature tests are mapped in `scripts/generate_rtm.py`, and the generated RTM marks F024/F041/F042 as `P` | Keep automated evidence repeatable without treating `P` as independent QA sign-off | #30 |

## Existing deviations to preserve

Do **not** overwrite `docs/DEVIATIONS.md`, which already documents local SQLite vs planned database, GitHub Projects vs Jira, three-role RBAC, local HTTP vs deployment TLS, and other earlier decisions. Review stale descriptions (for example, early demo login scripts) against the final integrated application instead of copying them as if still current.


## Sprint 3 refinements after PR #102

- **F010 — Citizen-only lodging:** The API explicitly forbids authenticated
  Admin/Officer submission (HTTP 403), rather than depending solely on
  role-specific navigation. Verified in automated regression tests.
- **F024 — Resolution history and SLA:** Reopening clears only the prior
  resolution timestamp, retains previous resolution remarks for reference,
  and assigns a new SLA due time based on complaint priority. The reopening
  reason remains in the status history.
- **F024 — Notification failure:** A committed reopening remains successful
  if a later staff notification attempt fails; the failure is logged.
- **Citizen sessions:** Lodge and Track pages clear session storage and
  redirect to Login when receiving HTTP 401.

These are implementation refinements to the earlier feature detail, not
newly claimed QA approvals. The existing `docs/DEVIATIONS.md` remains
unchanged; historical rows there should be reviewed separately for staleness.
