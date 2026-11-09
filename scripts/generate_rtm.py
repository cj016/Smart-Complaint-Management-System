"""Run the automated tests and write docs/RTM.md (SCMS-Team9 SRS section 8, T-05).

Usage (from the project root):  python scripts/generate_rtm.py

A requirement is marked P (Passed) only if every test file mapped to it passes right now.
F means a mapped test file failed. N means there is no automated test for it yet.
"A" (tested and Approved) is left for the QA Lead to set by hand after sign-off.
"""
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Req ID, short name, SRS test case(s), test files, comment when nothing automated covers it
RTM = [
    ("SCMS-F-001", "Citizen registration with OTP", "TC-Reg-01", ["test_auth_register.py"], ""),
    ("SCMS-F-002", "Authenticate registered user", "TC-Auth-01", ["test_auth_login.py"], ""),
    ("SCMS-F-003", "Hash and salt stored passwords", "TC-Sec-01", ["test_password.py"], ""),
    ("SCMS-F-004", "Lock account after failed logins", "TC-Auth-02",
     ["test_auth_lockout.py"], ""),
    ("SCMS-F-010", "Lodge new complaint", "TC-Lodge-01", ["test_lodge_complaint.py"], ""),
    ("SCMS-F-011", "Auto-generate Complaint ID", "TC-Lodge-02", ["test_complaint_id.py"], ""),
    ("SCMS-F-012", "Validate mandatory complaint fields", "TC-Lodge-03",
     ["test_complaint_validation.py"], ""),
    ("SCMS-F-013", "Attach photo evidence to complaint", "TC-Lodge-04",
     ["test_photo_attachments.py", "test_lodge_with_photos.py"], ""),
    ("SCMS-F-020", "Track complaint status by ID", "TC-Track-01", ["test_tracking_by_id.py"], ""),
    ("SCMS-F-021", "Track complaint status by account", "TC-Track-02",
     ["test_tracking_by_account.py"], ""),
    ("SCMS-F-022", "View complaint status timeline", "TC-Track-03",
     ["test_tracking_timeline.py"], ""),
    ("SCMS-F-023", "In-app / email-SMS status notifications", "TC-Track-04", [],
     "No automated test yet"),
    ("SCMS-F-024", "Reopen resolved or closed complaint", "TC-Track-05",
     ["test_f024_reopen.py"], ""),
    ("SCMS-F-030", "Assign complaint to officer", "TC-Admin-01", ["test_admin_assign.py"], ""),
    ("SCMS-F-031", "View all complaints in admin dashboard", "TC-Admin-02",
     ["test_admin_dashboard.py"], ""),
    ("SCMS-F-032", "Filter/sort complaints by category, priority, status", "TC-Admin-03",
     ["test_admin_dashboard.py"], ""),
    ("SCMS-F-033", "Update status with resolution remarks", "TC-Admin-04",
     ["test_admin_status.py"], ""),
    ("SCMS-F-034", "Auto-escalate overdue complaints (SLA)", "TC-Admin-05",
     ["test_admin_escalation.py"], ""),
    ("SCMS-F-035", "Reassign complaint to different officer/dept.", "TC-Admin-06",
     ["test_admin_reassign.py"], ""),
    ("SCMS-F-040", "Send status-change notification", "TC-Notify-01", [],
     "No automated test yet"),
    ("SCMS-F-041", "Rate resolution and give feedback", "TC-Feedback-01",
     ["test_f041_feedback.py"], ""),
    ("SCMS-F-042", "Generate category/department-wise reports", "TC-Report-01",
     ["test_f042_reports.py"], ""),
    ("SCMS-NF-001", "Dashboard response time target", "TC-Perf-01",
     ["test_dashboard_performance.py"], "pytest timing test, see DEVIATIONS.md"),
    ("SCMS-NF-002", "99.5% monthly uptime", "Ops reports", [],
     "Measured by monitoring after deployment"),
    ("SCMS-NF-003", "Encryption of PII", "TC-Sec-02", [], "No automated test yet"),
    ("SCMS-NF-004", "Responsive UI (360px-1920px)", "TC-UX-01", ["test_responsive_ui.py"],
     "Automated part only; manual DevTools check in docs/screenshots"),
    ("SCMS-NF-005", "Horizontal scalability (1k-50k users)", "TC-Scale-01", [],
     "Needs a load test on the deployed system"),
    ("SCMS-NF-006", "Modular MVC codebase", "TC-Maint-01", [],
     "Code review checklist, not automated"),
    ("SCMS-SR-001", "TLS 1.2+ mandatory on all connections", "TC-Sec-03", [],
     "Deployment setting, see DEVIATIONS.md"),
    ("SCMS-SR-002", "Role-based access control", "TC-Sec-04", ["test_rbac.py"], ""),
    ("SCMS-SR-003", "Input sanitization (SQLi / XSS)", "TC-Sec-05", [],
     "OWASP ZAP scan not run yet"),
    ("SCMS-SR-004", "Tamper-evident audit log", "TC-Sec-06", [], "Not implemented yet"),
    ("SCMS-SR-005", "CSRF protection on state-changing requests", "TC-Sec-07", [],
     "Not implemented yet"),
]


def run_pytest(args):
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", *args],
                          cwd=ROOT, capture_output=True, text=True)
    lines = [ln for ln in proc.stdout.strip().splitlines() if ln.strip()]
    return proc.returncode == 0, (lines[-1] if lines else "no output")


def main():
    results = {}
    for _, _, _, files, _ in RTM:
        for name in files:
            if name not in results:
                path = ROOT / "tests" / name
                results[name] = run_pytest([str(path)]) if path.exists() else \
                    (False, "file not found")

    all_ok, summary = run_pytest([])

    rows, counts = [], {"P": 0, "F": 0, "N": 0}
    for req, short, case, files, note in RTM:
        if not files:
            status, comment = "N", note
        elif all(results[f][0] for f in files):
            status = "P"
            evidence = "; ".join(f"tests/{f}" for f in files)
            comment = f"{note} ({evidence})" if note else evidence
        else:
            status = "F"
            comment = "FAILED: " + "; ".join(f for f in files if not results[f][0])
        counts[status] += 1
        rows.append(f"| {req} | {short} | {case} | {status} | {comment} |")

    out = [
        "# Requirements Traceability Matrix (RTM) - test status",
        "",
        "Replaces the status column of SRS section 8 (see docs/DEVIATIONS.md). Generated by "
        "`python scripts/generate_rtm.py`, which runs the automated tests and marks a "
        "requirement **P** only if every test file listed for it passes.",
        "",
        "Status: **N** = not tested, **P** = passed, **F** = a mapped test failed, "
        "**A** = tested and approved (set by the QA Lead after sign-off).",
        "",
        f"Last run: {date.today().isoformat()}. Full suite: `{summary}`. "
        f"Requirements: {counts['P']} passed, {counts['F']} failed, {counts['N']} not tested "
        f"(of {len(RTM)}).",
        "",
        "| Req ID | Requirement (short) | Test case(s) | Status | Comments / evidence |",
        "|---|---|---|---|---|",
        *rows,
        "",
    ]
    (ROOT / "docs" / "RTM.md").write_text("\n".join(out))
    print(f"Wrote docs/RTM.md - {counts['P']} P, {counts['F']} F, {counts['N']} N. {summary}")
    return 0 if all_ok and counts["F"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
