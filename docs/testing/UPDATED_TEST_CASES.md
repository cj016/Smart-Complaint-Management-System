# Updated Test Case Document

## Project details

- Project: Smart Complaint Management System
- Team: Team 9
- Date: 10 November 2026
- Tested commit: `eb5f17e`

## 1. Objective

To update the earlier test case mappings after the
Sprint 2 and Sprint 3 implementation changes.

This document is based on the existing RTM and
the recorded pytest execution results.

An automated pass confirms the mapped tests passed.
It does not automatically mean that every aspect
of a requirement has been fully validated.

## 2. Updated requirement test cases

| Requirement | Test case | Test scenario | Evidence | Result |
|---|---|---|---|---|
| SCMS-F-001 | TC-Reg-01 | Citizen registration with OTP | `tests/test_auth_register.py` | Mapped automated tests passed |
| SCMS-F-002 | TC-Auth-01 | Authenticate registered user | `tests/test_auth_login.py` | Mapped automated tests passed |
| SCMS-F-003 | TC-Sec-01 | Hash and salt stored passwords | `tests/test_password.py` | Mapped automated tests passed |
| SCMS-F-004 | TC-Auth-02 | Lock account after failed logins | `tests/test_auth_lockout.py` | Mapped automated tests passed |
| SCMS-F-010 | TC-Lodge-01 | Lodge new complaint | `tests/test_lodge_complaint.py` | Mapped automated tests passed |
| SCMS-F-011 | TC-Lodge-02 | Auto-generate Complaint ID | `tests/test_complaint_id.py` | Mapped automated tests passed |
| SCMS-F-012 | TC-Lodge-03 | Validate mandatory complaint fields | `tests/test_complaint_validation.py` | Mapped automated tests passed |
| SCMS-F-013 | TC-Lodge-04 | Attach photo evidence to complaint | `tests/test_photo_attachments.py`, `tests/test_lodge_with_photos.py` | Mapped automated tests passed |
| SCMS-F-020 | TC-Track-01 | Track complaint status by ID | `tests/test_tracking_by_id.py` | Mapped automated tests passed |
| SCMS-F-021 | TC-Track-02 | Track complaint status by account | `tests/test_tracking_by_account.py` | Mapped automated tests passed |
| SCMS-F-022 | TC-Track-03 | View complaint status timeline | `tests/test_tracking_timeline.py` | Mapped automated tests passed |
| SCMS-F-023 | TC-Track-04 | In-app / email-SMS status notifications | `tests/test_notifications.py`, `tests/test_notification_delivery.py` | Partial: External email/SMS delivery not fully verified |
| SCMS-F-024 | TC-Track-05 | Reopen resolved or closed complaint | `tests/test_f024_reopen.py` | Mapped automated tests passed |
| SCMS-F-030 | TC-Admin-01 | Assign complaint to officer | `tests/test_admin_assign.py` | Mapped automated tests passed |
| SCMS-F-031 | TC-Admin-02 | View all complaints in admin dashboard | `tests/test_admin_dashboard.py` | Mapped automated tests passed |
| SCMS-F-032 | TC-Admin-03 | Filter/sort complaints by category, priority, status | `tests/test_admin_dashboard.py` | Mapped automated tests passed |
| SCMS-F-033 | TC-Admin-04 | Update status with resolution remarks | `tests/test_admin_status.py` | Mapped automated tests passed |
| SCMS-F-034 | TC-Admin-05 | Auto-escalate overdue complaints (SLA) | `tests/test_admin_escalation.py` | Mapped automated tests passed |
| SCMS-F-035 | TC-Admin-06 | Reassign complaint to different officer/dept. | `tests/test_admin_reassign.py` | Mapped automated tests passed |
| SCMS-F-040 | TC-Notify-01 | Send status-change notification | `tests/test_f040_notifications.py` | Mapped automated tests passed |
| SCMS-F-041 | TC-Feedback-01 | Rate resolution and give feedback | `tests/test_f041_feedback.py` | Mapped automated tests passed |
| SCMS-F-042 | TC-Report-01 | Generate category/department-wise reports | `tests/test_f042_reports.py` | Mapped automated tests passed |
| SCMS-NF-001 | TC-Perf-01 | Dashboard response time target | `tests/test_dashboard_performance.py` | Partial: Measured in local test environment |
| SCMS-NF-002 | Ops reports | 99.5% monthly uptime | No automated test mapped | Not verified |
| SCMS-NF-003 | TC-Sec-02 | Encryption of PII | `tests/test_pii_encryption.py` | Mapped automated tests passed |
| SCMS-NF-004 | TC-UX-01 | Responsive UI (360px-1920px) | `tests/test_responsive_ui.py` | Partial: Not all devices and pages verified |
| SCMS-NF-005 | TC-Scale-01 | Horizontal scalability (1k-50k users) | `tests/test_scalability.py` | Partial: Production-scale load testing not performed |
| SCMS-NF-006 | TC-Maint-01 | Modular MVC codebase | `tests/test_modular_mvc.py` | Partial: Full manual code review not recorded |
| SCMS-SR-001 | TC-Sec-03 | TLS 1.2+ mandatory on all connections | `tests/test_tls.py` | Partial: Production TLS deployment not verified |
| SCMS-SR-002 | TC-Sec-04 | Role-based access control | `tests/test_rbac.py` | Mapped automated tests passed |
| SCMS-SR-003 | TC-Sec-05 | Input sanitization (SQLi / XSS) | `tests/test_sanitization.py` | Partial: Independent security scan not performed |
| SCMS-SR-004 | TC-Sec-06 | Tamper-evident audit log | `tests/test_audit_log.py`, `tests/test_audit_integration.py` | Mapped automated tests passed |
| SCMS-SR-005 | TC-Sec-07 | CSRF protection on state-changing requests | `tests/test_csrf.py` | Mapped automated tests passed |

## 3. Additional Sprint 3 test cases

| Test ID | Test scenario | Expected result | Evidence |
|---|---|---|---|
| TC-S3-01 | Citizen interface | Citizen pages and actions work | `tests/test_sprint3_citizen.py` (Passed) |
| TC-S3-02 | Authentication validation | Invalid inputs are rejected | `tests/test_sprint3_auth_validation.py` (Passed) |
| TC-S3-03 | Admin browser interface | Admin interface components work | `tests/test_sprint3_admin_browser_shell.py` (Passed) |
| TC-S3-04 | Final integration | Implemented features work together | `tests/test_sprint3_final_integration.py` (Passed) |
| TC-S3-05 | Role-based navigation | Users see the correct navigation | `tests/test_role_login_navigation.py` (Passed) |

## 4. Manual system validation

Manual test cases MV-01 through MV-08 and their
recorded results are maintained in:

- `TEST_CASE_EXECUTION.md`

## 5. Testing evidence

- `evidence/pytest-results.xml`
- `evidence/test-inventory.txt`
- `TEST_CASE_EXECUTION.md`
- `UNIT_TEST_REPORT.md`
- `SYSTEM_VALIDATION_REPORT.md`
- `CODE_COVERAGE_REPORT.md`
- `BRANCH_COVERAGE_REPORT.md`

## 6. Remaining validation

Test cases should be compared with the original
`Test_Plan_Team9.pdf` before final submission.

Production uptime, deployment security and
large-scale performance claims require separate evidence.

## 7. Conclusion

The earlier test case mappings have been updated
with the automated tests added during later sprints.
Partial and unverified areas are identified above.
