# System Test Case Execution Log

Project: Smart Complaint Management System (Team 9)
Date: 10 November 2026
Commit tested: `eb5f17e`

## Automated browser validation

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

Browser test summary: 12 checks passed.
This total includes the responsive viewport checks.

Evidence: `evidence/system-browser-smoke.txt`

## Additional manual validation

Fill in Pass, Fail or Not tested after checking each case.

| ID | Test scenario | Result | Notes |
|---|---|---|---|
| MV-01 | Invalid login password shows an error | PASS | - |
| MV-02 | Citizen cannot use Admin-only actions | PASS | - |
| MV-03 | Complaint status filter works | PASS | - |
| MV-04 | Invalid complaint ID shows an error | PASS | - |
| MV-05 | Citizen notifications appear after a status change | PASS | - |
| MV-06 | Staff notifications are shown for reopened complaints | PASS | - |
| MV-07 | Registration and complaint pages work on mobile | PASS | - |
| MV-08 | Logout clears the session | PASS | - |
