# Branch Coverage Report

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

To check how many Python decision paths were
executed by the automated tests.

## 3. Method

Coverage was measured using the `--cov-branch` option.
This checks branches in conditions and other control flow.

Branch coverage = covered branches / total branches x 100.

## 4. Results

| Metric | Result |
|---|---:|
| Total branches | 304 |
| Covered branches | 259 |
| Missing branches | 45 |
| Branch coverage | 85.20% |

## 5. Branch coverage by Python file

| File | Covered | Total | Branch coverage |
|---|---:|---:|---:|
| `app/__init__.py` | 2 | 6 | 33.33% |
| `app/admin/routes.py` | 63 | 66 | 95.45% |
| `app/admin/services.py` | 12 | 12 | 100.00% |
| `app/audit/services.py` | 6 | 6 | 100.00% |
| `app/auth/decorators.py` | 6 | 6 | 100.00% |
| `app/auth/routes.py` | 35 | 42 | 83.33% |
| `app/complaints/photos.py` | 14 | 20 | 70.00% |
| `app/complaints/routes.py` | 36 | 42 | 85.71% |
| `app/complaints/validation.py` | 8 | 8 | 100.00% |
| `app/crypto.py` | 2 | 4 | 50.00% |
| `app/errors.py` | 1 | 2 | 50.00% |
| `app/feedback/routes.py` | 16 | 16 | 100.00% |
| `app/notifications/routes.py` | 7 | 10 | 70.00% |
| `app/notifications/services.py` | 6 | 16 | 37.50% |
| `app/reporting/routes.py` | 29 | 30 | 96.67% |
| `app/sanitize.py` | 1 | 2 | 50.00% |
| `app/tracking/routes.py` | 15 | 16 | 93.75% |

## 6. Main areas for improvement

| File | Missing branches |
|---|---:|
| `app/notifications/services.py` | 10 |
| `app/auth/routes.py` | 7 |
| `app/complaints/photos.py` | 6 |
| `app/complaints/routes.py` | 6 |
| `app/__init__.py` | 4 |
| `app/admin/routes.py` | 3 |
| `app/notifications/routes.py` | 3 |
| `app/crypto.py` | 2 |

## 7. Observations

- Branch coverage was 85.20%.
- 45 branches were not exercised.
- Some conditions and error-handling paths need more tests.
- High test pass rates do not guarantee complete branch coverage.
- All 437 automated tests passed during measurement.

## 8. Evidence

- `evidence/coverage.json`
- `evidence/coverage.xml`
- `evidence/coverage-output.txt`
- `evidence/htmlcov/index.html` (local HTML report)

## 9. Conclusion

SCMS achieved 85.20% Python backend branch coverage.
Additional tests can target the missing decision paths.
