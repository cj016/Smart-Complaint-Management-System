# System Validation Report

## Project details

- Project: Smart Complaint Management System
- Team: Team 9
- Date: 10 November 2026
- Commit tested: `eb5f17e`
- Testing: Playwright browser tests and manual checks

## Objective

To verify the main Citizen, Admin and Officer workflows
and check that the application works correctly in a browser.

## Automated browser testing

- Total checks passed: 12
- Browser failures logged: 0
- Skipped groups logged: 0

| ID | Test scenario | Result |
|---|---|---|
| BV-01 | guest root redirects to shared login | Pass |
| BV-02 | Admin login/dashboard/reports/feedback | Pass |
| BV-03 | Citizen registration/OTP/login | Pass |
| BV-04 | Citizen lodge/My Complaints/track | Pass |
| BV-05 | Admin assigns complaint | Pass |
| BV-06 | Officer can update only assigned complaint | Pass |
| BV-07 | Citizen feedback/reopen/timeline | Pass |
| BV-08 | Admin report CSV export | Pass |

The browser test also checked the login page at
360px, 768px, 1280px and 1920px.

## Manual validation

- Passed: 8
- Failed: 0
- Not tested: 0

| ID | Test scenario | Result | Notes |
|---|---|---|---|
| MV-01 | Invalid login password shows an error | Pass | - |
| MV-02 | Citizen cannot use Admin-only actions | Pass | - |
| MV-03 | Complaint status filter works | Pass | - |
| MV-04 | Invalid complaint ID shows an error | Pass | - |
| MV-05 | Citizen notifications appear after a status change | Pass | - |
| MV-06 | Staff notifications are shown for reopened complaints | Pass | - |
| MV-07 | Registration and complaint pages work on mobile | Pass | - |
| MV-08 | Logout clears the session | Pass | - |

## Evidence

- `evidence/system-browser-smoke.txt`
- `TEST_CASE_EXECUTION.md`
- Browser screenshots found locally: 10
- Screenshot folder: `docs/screenshots/sprint3-browser/`

## Limitations

- Tests were performed in a local development environment.
- Production uptime and concurrent load were not verified by these browser checks.
- Deployment TLS and any remaining Test Plan cases need separate verification.

## Conclusion

The browser test recorded 12 successful checks.
Manual testing recorded 8 passes, 0 failures
and 0 not-tested cases.
