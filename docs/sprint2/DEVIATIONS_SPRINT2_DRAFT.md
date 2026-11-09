# Sprint 2 implementation refinements and deviations - DRAFT

**Issue:** #30 (T-04) | **Status:** provisional. Review with `docs/DEVIATIONS.md` after merging.

The original SRS/SAD describe high-level features. The following details are implementation refinements, **not necessarily contradictions** of the original specification. Keep the existing repository deviations; append/reconcile these only after confirming integrated `main`.

| Original reference | Implemented detail / extension | Why it was chosen | Issue / PR |
|---|---|---|---|
| SRS 4.3 (F-024); SAD 3.4, 4.3 | Reopening requires a nonblank reason (max 2,000 chars), only owner, from Resolved/Closed; creates `Reopened` timeline/audit, clears old resolution metadata | Explicit authorization and consistent new workflow cycle | #27 / #97 |
| SRS 4.3 (F-024, notifications); SAD NotificationModule | Staff in-app inbox for assigned Officer and Admins, rather than relying only on Citizen inbox; external email/SMS depends on configuration | Staff must be able to see reopening events | #27 / #97 |
| SRS 4.5 (F-041); SAD Citizen UI | Feedback requires owner and current Resolved status, integer 1-5, optional comment up to 1,000 chars, one row per complaint | Enforce single submission and consistent validation | #28 / #98 |
| SRS 4.5 (F-042); SAD ReportingModule | Date range filters complaint **submission date**, missing department shown as `Unassigned`, mean turnaround only from eligible Resolved/Closed records; null -> N/A | Avoid misleading turnaround metrics and ambiguous date scope | #29 / #99 |
| SRS 4.5 (F-042); SAD API examples | Added CSV export of filtered aggregate reports with guarded spreadsheet content | Allow simple faculty demo/report download without disclosing citizen data | #29 / #99 |
| SRS Section 8 (RTM); existing `docs/RTM.md` | New feature tests exist on unmerged PR branches, while the generator still lists F024/F041/F042 as `N` | Update generator mapping and recompute status after integrated merge; do not claim QA sign-off early | #30 / pending |

## Existing deviations to preserve

Do **not** overwrite `docs/DEVIATIONS.md`, which already documents local SQLite vs planned database, GitHub Projects vs Jira, three-role RBAC, local HTTP vs deployment TLS, and other earlier decisions. Review stale descriptions (for example, early demo login scripts) against the final integrated application instead of copying them as if still current.
