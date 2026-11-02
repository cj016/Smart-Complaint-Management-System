# Sprint 2 Test Plan update: F024, F041, F042

Merge this documentation PR after the three separate feature PRs. Original submitted
PDFs are preserved. QA approval and browser acceptance remain separate from test passes.

| Requirement | Automated evidence |
|---|---|
| F024 / TC-Track-05 | tests/test_reopening.py: ownership, reason, terminal states, timeline/SLA, staff/Admin notifications, audit, duplicate rejection |
| F041 / TC-Feedback-01 | tests/test_feedback.py: owner-only rating/comment, validation, one rating, Admin visibility/date filters/pagination, audit |
| F042 / TC-Report-01 | tests/test_resolution_reports.py: Admin-only groups/counts/states, average turnaround/samples, inclusive dates, validation and CSV |

Run `python -m flake8 .`, `python -m pytest -q`, then
`python scripts/generate_rtm.py`. The generator leaves these requirements N while
separate feature test files are absent; it marks P only when those tests exist and pass.
It never marks QA approval A. GitHub CI must validate each actual pushed branch.
Production concurrency, live external email/SMS and load testing are not claimed.

## Disposable manual demo (after the three code PRs merge)

Run `python scripts/demo_harsh_tasks.py`; open http://127.0.0.1:5001/login.
This uses in-memory data, not the normal database. Restart to reset. Password for all
samples: SCMS-Demo-2026!. Citizen: citizen@scms.example; Admin: admin@scms.example;
Other citizen: other@scms.example.

1. Citizen -> Feedback -> find SCMS-2026-00001 (Resolved); save a rating/comment.
   Search again and verify saved feedback and duplicate protection.
2. Admin -> Feedback -> verify rating/comment, pagination and submission-date filters.
3. Citizen -> Track by ID -> 00001 -> reopen with a reason. Verify Reopened and timeline;
   assigned staff/Admin receive notifications. Tests verify both recipient roles.
4. 00002 starts Closed and can reopen; 00003 is In Progress and cannot. Citizen cannot
   access 00004, which belongs to Other citizen.
5. Admin -> Reports -> compare groups and CSV. Before reopening, Roads total 2/completed
   1/open 1; after reopening 00001, completed 0/open 2.
6. Test inclusive From/To, empty future windows and reversed-date errors. Average
   turnaround excludes missing/negative timestamps and current Reopened complaints;
   no samples shows a dash. Two durations of 2 and 6 hours average 4 (automated test).
7. Check phone/tablet/desktop layouts and keyboard operation.

The separated Feedback page must be rechecked in the browser before approval. Earlier
screenshots show page loading, not complete acceptance. Verify all features together
again after the three code PRs merge, then refresh this documentation branch/RTM.
