# Verification & Testing Guide

This guide describes how to run automated and manual test scripts to verify the functionality of the platform's SQLite database, crawlers, AI matcher, and browser automations.

---

## 1. Automated System Test Script
We have provided a verification script at `src/test_system.py`. This script tests the core integrations (Database, Gemini Mock Eval, Playwright Sandbox, and Notification Alerts) in a safe sandbox mode that does not execute actual external network queries.

To run the verification script, execute the following command in your terminal:
```bash
python -m src.test_system
```

Expected output should confirm:
1. Candidate profile seeded and fetched successfully.
2. AI Matcher score calculation and priority boosts computed correctly.
3. Playwright sandbox mode executing, creating a mock screenshot, and updating the database.
4. Email and Telegram dispatches executing in sandbox logging mode.

---

## 2. Testing Individual Services

### A. Gemini Matcher Sandbox Check
To verify Gemini's prompt and evaluation logic without actual API hits, ensure your `.env` does *not* contain a `GEMINI_API_KEY`. Running evaluations will fall back to the built-in mock analyzer which scores jobs based on title matching rules.

To verify with actual Gemini API:
1. Set `GEMINI_API_KEY` in `.env`.
2. Run a manual search on the dashboard.
3. Verify that real evaluation matching scores, missing skills list, and cover letters are generated in the **Matched Jobs** tab.

### B. Playwright Form Filler check
To run Playwright in headed mode (visible browser window) for debugging:
1. Open `src/services/playwright_service.py`.
2. Change `headless=True` to `headless=False` in `browser = p.chromium.launch(headless=True)`.
3. Set `mock=False` in `AutoApplierAgent.apply_job()` or override it in `src/api/main.py` when calling `/api/jobs/{job_id}/apply`.
4. Trigger manual apply on the dashboard and observe the browser navigate Greenhouse or Lever, fill in name, email, and upload the resume.

### C. Alerts and Credentials Verification
To verify email alerts:
1. Ensure `SMTP_USERNAME` and `SMTP_PASSWORD` (Gmail App Password) are set in `.env`.
2. Run `python -c "from src.services.email_service import EmailService; EmailService.send_html_email('sriramnbv26@gmail.com', 'Test Alert', '<h1>Working!</h1>')"`
3. Confirm you receive the test email.
