# Unit Test Report

## 1. Project details

- Project: Smart Complaint Management System (SCMS)
- Team: Team 9
- Test date: 10 November 2026
- Git commit: `eb5f17e`
- Python version: 3.13.7
- Testing framework: pytest

## 2. Objective

To check that the implemented features work correctly
and that existing functionality is not broken.

## 3. Testing method

Automated tests were executed using pytest.
The suite includes unit, API, integration, security,
UI structure and performance-related tests.
The complete results were saved as JUnit XML.

## 4. Test results

| Metric | Result |
|---|---|
| Tests collected | 437 |
| Passed | 437 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |
| Pass percentage (executed tests) | 100.00% |
| Execution time | 20.19 seconds |

## 5. Results by test file

| Test file | Total | Passed | Failed/Errors | Skipped |
|---|---:|---:|---:|---:|
| `tests/test_admin_assign.py` | 17 | 17 | 0 | 0 |
| `tests/test_admin_dashboard.py` | 30 | 30 | 0 | 0 |
| `tests/test_admin_escalation.py` | 9 | 9 | 0 | 0 |
| `tests/test_admin_reassign.py` | 12 | 12 | 0 | 0 |
| `tests/test_admin_status.py` | 17 | 17 | 0 | 0 |
| `tests/test_audit_api.py` | 5 | 5 | 0 | 0 |
| `tests/test_audit_integration.py` | 4 | 4 | 0 | 0 |
| `tests/test_audit_log.py` | 4 | 4 | 0 | 0 |
| `tests/test_auth.py` | 8 | 8 | 0 | 0 |
| `tests/test_auth_lockout.py` | 4 | 4 | 0 | 0 |
| `tests/test_auth_login.py` | 4 | 4 | 0 | 0 |
| `tests/test_auth_register.py` | 6 | 6 | 0 | 0 |
| `tests/test_complaint_id.py` | 5 | 5 | 0 | 0 |
| `tests/test_complaint_validation.py` | 14 | 14 | 0 | 0 |
| `tests/test_csrf.py` | 5 | 5 | 0 | 0 |
| `tests/test_dashboard_performance.py` | 4 | 4 | 0 | 0 |
| `tests/test_f024_reopen.py` | 21 | 21 | 0 | 0 |
| `tests/test_f040_notifications.py` | 4 | 4 | 0 | 0 |
| `tests/test_f041_feedback.py` | 40 | 40 | 0 | 0 |
| `tests/test_f042_reports.py` | 28 | 28 | 0 | 0 |
| `tests/test_health.py` | 2 | 2 | 0 | 0 |
| `tests/test_lodge_complaint.py` | 12 | 12 | 0 | 0 |
| `tests/test_lodge_with_photos.py` | 5 | 5 | 0 | 0 |
| `tests/test_models.py` | 4 | 4 | 0 | 0 |
| `tests/test_modular_mvc.py` | 5 | 5 | 0 | 0 |
| `tests/test_notification_delivery.py` | 5 | 5 | 0 | 0 |
| `tests/test_notifications.py` | 8 | 8 | 0 | 0 |
| `tests/test_password.py` | 3 | 3 | 0 | 0 |
| `tests/test_photo_attachments.py` | 19 | 19 | 0 | 0 |
| `tests/test_pii_encryption.py` | 3 | 3 | 0 | 0 |
| `tests/test_rbac.py` | 7 | 7 | 0 | 0 |
| `tests/test_responsive_ui.py` | 2 | 2 | 0 | 0 |
| `tests/test_role_login_navigation.py` | 8 | 8 | 0 | 0 |
| `tests/test_sanitization.py` | 4 | 4 | 0 | 0 |
| `tests/test_scalability.py` | 2 | 2 | 0 | 0 |
| `tests/test_sprint3_admin_browser_shell.py` | 2 | 2 | 0 | 0 |
| `tests/test_sprint3_auth_validation.py` | 26 | 26 | 0 | 0 |
| `tests/test_sprint3_citizen.py` | 5 | 5 | 0 | 0 |
| `tests/test_sprint3_final_integration.py` | 19 | 19 | 0 | 0 |
| `tests/test_tls.py` | 1 | 1 | 0 | 0 |
| `tests/test_tracking_by_account.py` | 7 | 7 | 0 | 0 |
| `tests/test_tracking_by_id.py` | 12 | 12 | 0 | 0 |
| `tests/test_tracking_timeline.py` | 14 | 14 | 0 | 0 |
| `tests/test_ui03_session.py` | 5 | 5 | 0 | 0 |
| `tests/test_ui_navigation.py` | 13 | 13 | 0 | 0 |
| `tests/test_ui_pages.py` | 3 | 3 | 0 | 0 |

## 6. Observations

- 437 automated tests passed.
- 0 tests failed or had errors.
- The results show that the tested functionality
  passed the automated checks on this revision.
- The tests do not replace complete manual system testing.

## 7. Evidence

- `evidence/pytest-results.xml`
- `evidence/pytest-output.txt`
- `evidence/test-inventory.txt`

## 8. Conclusion

The automated test execution was successful.
