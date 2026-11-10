# Code Coverage Report

## 1. Project details

- Project: Smart Complaint Management System (Team 9)
- Test date: 10 November 2026
- Commit tested: `eb5f17e`
- Python version: 3.13.7
- Framework: pytest with pytest-cov / coverage.py
- Automated tests passed: 437
- Warnings reported: 271
- Scope: Python backend under `app/`

## 2. Objective

To measure how much of the SCMS Python backend
was executed by the automated test suite.

## 3. Method

Coverage was collected using pytest-cov with
`--cov=app --cov-branch`.

Line coverage = executed statements / total statements x 100.

## 4. Results

| Metric | Result |
|---|---:|
| Total statements | 1367 |
| Covered statements | 1276 |
| Uncovered statements | 91 |
| Line coverage | 93.34% |

## 5. Coverage by Python file

| File | Covered | Total | Line coverage |
|---|---:|---:|---:|
| `app/__init__.py` | 47 | 53 | 88.68% |
| `app/admin/routes.py` | 169 | 173 | 97.69% |
| `app/admin/services.py` | 48 | 48 | 100.00% |
| `app/audit/routes.py` | 15 | 15 | 100.00% |
| `app/audit/services.py` | 26 | 26 | 100.00% |
| `app/auth/decorators.py` | 21 | 21 | 100.00% |
| `app/auth/routes.py` | 130 | 141 | 92.20% |
| `app/complaints/photos.py` | 64 | 75 | 85.33% |
| `app/complaints/routes.py` | 135 | 151 | 89.40% |
| `app/complaints/services.py` | 11 | 11 | 100.00% |
| `app/complaints/validation.py` | 19 | 19 | 100.00% |
| `app/config.py` | 31 | 31 | 100.00% |
| `app/crypto.py` | 26 | 28 | 92.86% |
| `app/errors.py` | 18 | 21 | 85.71% |
| `app/extensions.py` | 8 | 8 | 100.00% |
| `app/feedback/routes.py` | 60 | 63 | 95.24% |
| `app/health.py` | 13 | 13 | 100.00% |
| `app/models/__init__.py` | 5 | 5 | 100.00% |
| `app/models/audit.py` | 13 | 13 | 100.00% |
| `app/models/complaint.py` | 54 | 54 | 100.00% |
| `app/models/notification.py` | 12 | 12 | 100.00% |
| `app/models/user.py` | 41 | 42 | 97.62% |
| `app/notifications/routes.py` | 61 | 63 | 96.83% |
| `app/notifications/services.py` | 38 | 66 | 57.58% |
| `app/notifications/status_events.py` | 4 | 4 | 100.00% |
| `app/reporting/routes.py` | 90 | 91 | 98.90% |
| `app/sanitize.py` | 7 | 8 | 87.50% |
| `app/tls.py` | 6 | 6 | 100.00% |
| `app/tracking/routes.py` | 66 | 68 | 97.06% |
| `app/utils.py` | 3 | 3 | 100.00% |
| `app/web/routes.py` | 35 | 35 | 100.00% |

## 6. Main areas for improvement

| File | Uncovered statements |
|---|---:|
| `app/notifications/services.py` | 28 |
| `app/complaints/routes.py` | 16 |
| `app/auth/routes.py` | 11 |
| `app/complaints/photos.py` | 11 |
| `app/__init__.py` | 6 |
| `app/admin/routes.py` | 4 |
| `app/errors.py` | 3 |
| `app/feedback/routes.py` | 3 |

## 7. Observations

- The backend achieved 93.34% line coverage.
- 91 statements were not executed.
- All 437 automated tests passed.
- The run reported 271 warnings.
- Many warnings concern unclosed SQLite connections.
- Database connection cleanup should be reviewed separately.
- This report does not measure JavaScript or browser code coverage.

## 8. Evidence

- `evidence/coverage.json`
- `evidence/coverage.xml`
- `evidence/coverage-output.txt`
- `evidence/htmlcov/index.html` (local HTML report)

## 9. Conclusion

SCMS achieved 93.34% Python backend line coverage.
Uncovered code is identified above for future improvement.
