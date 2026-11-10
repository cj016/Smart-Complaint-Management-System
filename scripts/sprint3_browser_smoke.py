"""Optional full-browser SCMS smoke on a RUNNING LOCAL Flask dev server.

Usage:
  python -m pip install playwright python-dotenv
  python -m playwright install chromium
  python scripts/sprint3_browser_smoke.py

Create demo Admin and Officer before running; never commit login passwords.
All checks use actual Chromium UI and live localhost APIs, not mocked results.
This script creates a test citizen, modifies the local DB, and takes screenshots.
"""
import os
import re
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
try:
    from playwright.sync_api import sync_playwright, expect
except ImportError as exc:
    raise SystemExit("Install Playwright: python -m pip install playwright") from exc

BASE = os.getenv("SCMS_BROWSER_URL", "http://127.0.0.1:5000").rstrip("/")
ADMIN = "admin@scms.test"
ADMIN_PW = os.getenv("SCMS_DEMO_ADMIN_PASSWORD")
OFFICER = os.getenv("SCMS_SMOKE_OFFICER_EMAIL", "officer1@scms.test")
OFFICER_PW = os.getenv("SCMS_SMOKE_OFFICER_PASSWORD")
OFFICER_NAME = os.getenv("SCMS_SMOKE_OFFICER_NAME", "Demo Officer")
CITIZEN_PW = "TestCitizen!2026"
CITIZEN_EMAIL = "smoke-" + uuid.uuid4().hex[:12] + "@example.test"
EVIDENCE = ROOT / "docs" / "screenshots" / "sprint3-browser"
EVIDENCE.mkdir(parents=True, exist_ok=True)
PASSED = []


def check(name, fn):
    try:
        fn()
    except Exception as exc:
        print("FAIL:", name, type(exc).__name__, str(exc), file=sys.stderr)
        raise
    else:
        PASSED.append(name)
        print("PASS:", name)


def login(page, email, password, mode):
    page.goto(BASE + "/login")
    page.locator("#login-" + mode).click()
    page.locator("#email").fill(email)
    page.locator("#password").fill(password)
    page.locator("#login-form button[type=submit]").click()
    destination = r"/my-complaints" if mode == "citizen" else r"/admin"
    page.wait_for_url(
        re.compile(r"^" + re.escape(BASE) + destination),
        timeout=12000,
    )


def logout(page):
    page.get_by_role("button", name="Logout").click()
    page.wait_for_url("**/login")


def run():
    if not ADMIN_PW:
        raise SystemExit("Missing SCMS_DEMO_ADMIN_PASSWORD in ignored local .env")
    if not OFFICER_PW:
        raise SystemExit(
            "Set SCMS_SMOKE_OFFICER_PASSWORD; "
            "Officer credentials are required for the full browser smoke test."
        )
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 850}, accept_downloads=True)
        page.set_default_timeout(12000)
        page.goto(BASE + "/health")
        if "\"ok\"" not in page.locator("body").inner_text():
            raise RuntimeError("Flask /health not healthy. Start the app and migrate first.")
        check("guest root redirects to shared login", lambda: (
            page.goto(BASE + "/"), page.wait_for_url("**/login"),
            expect(page.locator("#login-citizen")).to_be_visible(),
            expect(page.locator("#login-staff")).to_be_visible()
        ))

        def test_admin():
            login(page, ADMIN, ADMIN_PW, "staff")
            expect(page.locator("#dashboard-title")).to_contain_text("Admin")
            expect(page.locator("#escalate-btn")).to_be_visible()
            page.screenshot(path=str(EVIDENCE / "admin-dashboard.png"), full_page=True)
            page.goto(BASE + "/admin/reports")
            expect(page.locator("#report-filters")).to_be_visible()
            expect(page.locator("#report-content")).to_be_visible()
            page.screenshot(path=str(EVIDENCE / "admin-reports.png"), full_page=True)
            page.goto(BASE + "/admin/feedback")
            expect(page.locator("body")).to_contain_text(re.compile("feedback", re.I))
            logout(page)
        check("Admin login/dashboard/reports/feedback", test_admin)

        def test_registration():
            page.goto(BASE + "/register")
            page.locator("#name").fill("Sprint Three Citizen")
            page.locator("#email").fill(CITIZEN_EMAIL)
            page.locator("#password").fill(CITIZEN_PW)
            page.locator("#confirm").fill(CITIZEN_PW)
            with page.expect_response(lambda r: "/api/v1/auth/register" in r.url) as result:
                page.locator("#register-form button[type=submit]").click()
            response = result.value
            payload = response.json()
            if not response.ok:
                raise RuntimeError("Citizen register failed: " + str(payload))
            if not payload.get("verified", False):
                otp = payload.get("dev_otp")
                if not otp:
                    raise RuntimeError("Dev OTP missing: use APP_ENV=development, "
                                       "or complete OTP manually before running smoke")
                page.locator("#otp").fill(str(otp))
                page.locator("#otp-form button[type=submit]").click()
                page.wait_for_url("**/login", timeout=10000)
            else:
                page.wait_for_url("**/login", timeout=10000)
            login(page, CITIZEN_EMAIL, CITIZEN_PW, "citizen")
            expect(page.locator("#complaints-section")).to_be_visible()
            page.screenshot(path=str(EVIDENCE / "citizen-dashboard.png"), full_page=True)
        check("Citizen registration/OTP/login", test_registration)

        c_id = [None]

        def lodge():
            page.goto(BASE + "/lodge")
            page.locator("#category").select_option(label="Roads")
            page.locator("#location").fill("Sprint 3 browser smoke test area")
            page.locator("#description").fill("Pothole reported by automated browser test")
            page.locator("#submit-btn").click()
            expect(page.locator("#success")).to_be_visible(timeout=12000)
            c_id[0] = page.locator("#new-id").inner_text().strip()
            assert re.fullmatch(r"SCMS-\d{4}-\d{5}", c_id[0]), c_id[0]
            page.goto(BASE + "/my-complaints")
            expect(page.locator("#complaints-section")).to_be_visible()
            row = page.locator("#complaints-table tbody tr").filter(has_text=c_id[0])
            expect(row).to_be_visible()
            row.get_by_role("link", name="Track").click()
            page.wait_for_url(re.compile(r"/track\?complaintId="))
            expect(page.locator("#result-id")).to_have_text(c_id[0])
        check("Citizen lodge/My Complaints/track", lodge)
        logout(page)

        def admin_assign():
            login(page, ADMIN, ADMIN_PW, "staff")
            row = page.locator("#complaints-table tbody tr").filter(has_text=c_id[0])
            expect(row).to_be_visible()
            row.get_by_role("button", name="Manage " + c_id[0]).click()
            expect(page.locator("#assign-form")).to_be_visible()
            options = page.locator("#officer-select option")
            if options.count() == 0:
                raise RuntimeError("No Officers available. Create one with scripts/create_user.py.")
            match = options.filter(has_text=OFFICER_NAME)
            if match.count() != 1:
                raise RuntimeError("Expected exactly one Officer named " + OFFICER_NAME +
                                   ". Set SCMS_SMOKE_OFFICER_NAME if your account differs.")
            page.locator("#officer-select").select_option(value=match.first.get_attribute("value"))
            page.locator("#assign-btn").click()
            expect(page.locator("#assign-message")).to_contain_text("Assigned", timeout=12000)
            page.screenshot(path=str(EVIDENCE / "admin-assignment.png"), full_page=True)
            logout(page)
        check("Admin assigns complaint", admin_assign)

        if OFFICER_PW:
            def officer_resolve():
                login(page, OFFICER, OFFICER_PW, "staff")
                row = page.locator("#complaints-table tbody tr").filter(has_text=c_id[0])
                expect(row).to_be_visible()
                expect(page.locator("#escalate-btn")).to_be_hidden()
                row.get_by_role("button", name="Manage " + c_id[0]).click()
                expect(page.locator("#assign-form")).to_be_hidden()
                expect(page.locator("#reassign-form")).to_be_hidden()
                page.locator("#status-select").select_option(label="In Progress")
                page.locator("#status-btn").click()
                expect(page.locator("#status-message")).to_contain_text("In Progress")
                page.locator("#status-select").select_option(label="Resolved")
                page.locator("#remarks-input").fill("Issue repaired and verified for Sprint 3")
                page.locator("#status-btn").click()
                expect(page.locator("#status-message")).to_contain_text("Resolved")
                page.screenshot(path=str(EVIDENCE / "officer-resolved.png"), full_page=True)
                logout(page)
            check("Officer can update only assigned complaint", officer_resolve)

            def citizen_feedback_reopen():
                login(page, CITIZEN_EMAIL, CITIZEN_PW, "citizen")
                page.goto(BASE + "/track?complaintId=" + c_id[0])
                expect(page.locator("#result-status")).to_have_text("Resolved")
                page.goto(BASE + "/feedback?complaintId=" + c_id[0])
                page.locator("#feedback-rating").select_option("4")
                page.locator("#feedback-comment").fill("Resolved satisfactorily")
                page.locator("#feedback-submit").click()
                expect(page.locator("#feedback-message")).to_contain_text("submitted")
                page.goto(BASE + "/my-complaints")
                row = page.locator("#complaints-table tbody tr").filter(has_text=c_id[0])
                row.get_by_role("button", name="Reopen " + c_id[0]).click()
                page.locator("#reopen-reason").fill("Rechecking complaint after resolution")
                page.locator("#reopen-submit").click()
                expect(page.locator("#reopen-message")).to_contain_text("reopened")
                page.goto(BASE + "/track?complaintId=" + c_id[0])
                expect(page.locator("#result-status")).to_have_text("Reopened")
                page.screenshot(path=str(EVIDENCE / "citizen-reopened.png"), full_page=True)
                logout(page)
            check("Citizen feedback/reopen/timeline", citizen_feedback_reopen)

            def final_admin_report():
                login(page, ADMIN, ADMIN_PW, "staff")
                page.goto(BASE + "/admin/reports")
                expect(page.locator("#report-content")).to_be_visible()
                with page.expect_download(timeout=15000) as download:
                    page.locator("#export-csv").click()
                assert download.value.suggested_filename.endswith(".csv")
                logout(page)
            check("Admin report CSV export", final_admin_report)
        else:
            print("SKIP: Officer resolution, Citizen feedback/reopen, CSV final check")

        for width in (360, 768, 1280, 1920):
            page.set_viewport_size({"width": width, "height": 900})
            page.goto(BASE + "/login")
            page.screenshot(path=str(EVIDENCE / f"login-{width}.png"), full_page=True)
            overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
            if overflow:
                raise AssertionError(f"Horizontal overflow on login at {width}px")
            PASSED.append(f"Login responsive {width}px")
        browser.close()
    print("\nPASSED", len(PASSED), "browser checks")
    print("Evidence:", EVIDENCE)
    print("NOTE: These are smoke checks, not a substitute for the full Test Plan.")


if __name__ == "__main__":
    try:
        run()
    except Exception:
        raise SystemExit(1)
