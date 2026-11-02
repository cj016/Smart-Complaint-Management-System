# SCMS-NF005 — Scalability Verification

Requirement: SCMS-NF005
Test case: TC-Scale-01
Issue: #38

## Design review

- The application uses Flask's application factory (`create_app`).
- Login API authentication uses JWT bearer tokens in request headers.
- Application state is stored in a database rather than relying on a
  single Flask worker's in-memory login session.
- The database connection can be configured through `DATABASE_URL`.
- Multiple application instances behind a reverse proxy are a deployment
  architecture, not something verified by these local tests.

## 10x baseline test

Test file: `tests/test_scalability.py`

Method:
- Baseline: 50 complaint records.
- Larger dataset: 500 complaint records (10x).
- Send 20 sequential dashboard API requests for each dataset.
- Measure 90th-percentile application response time (p90).
- Check that the larger dataset responds within 3 seconds p90.
- Check degradation against a 10x ceiling, with a 5ms measurement
  floor to reduce sensitivity to very small timing values.

Run:

    python -m pytest tests/test_scalability.py -v -s

## Limitations

This is an in-process, single-worker test using SQLite and sequential
requests. It does not establish throughput, concurrent-user capacity,
horizontal scaling efficiency, or actual support for 1,000–50,000
active users.

A full deployment demonstration would require a shared production
database, multiple workers or app instances behind a reverse proxy,
and a separate concurrent HTTP load-testing tool.

## Evidence

Record the measured p90 timings and test results from the local or CI
run before marking this requirement verified.

## Local test results — November 2, 2026

- Baseline: 50 complaints, p90 = 0.0022 seconds
- Larger dataset: 500 complaints, p90 = 0.0017 seconds
- Reported degradation ratio: 0.34x (using 5 ms floor)
- Scalability tests: 2 passed
- Complete pytest suite: 283 passed
- Result: Passed this local 10x dataset test only
