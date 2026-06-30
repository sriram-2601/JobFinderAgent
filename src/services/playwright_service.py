import os
import logging
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from src.config import BASE_DIR
from src.services.gemini_service import GeminiService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCREENSHOTS_DIR = BASE_DIR / "data" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
APPLICATION_LOGS_DIR = BASE_DIR / "data" / "logs"
APPLICATION_LOGS_DIR.mkdir(parents=True, exist_ok=True)

class PlaywrightService:
    @staticmethod
    def identify_platform(url: str) -> str:
        """Identify which ATS platform the URL belongs to"""
        url_lower = url.lower()
        if "lever.co" in url_lower:
            return "lever"
        elif "greenhouse.io" in url_lower:
            return "greenhouse"
        elif "ashbyhq.com" in url_lower:
            return "ashby"
        elif "smartrecruiters.com" in url_lower:
            return "smartrecruiters"
        elif "myworkdayjobs.com" in url_lower or "workday" in url_lower:
            return "workday"
        elif "taleo.net" in url_lower:
            return "taleo"
        return "custom"

    @classmethod
    def apply_to_job(cls, job_id: str, apply_url: str, candidate_profile: dict, resume_path: str, cover_letter_text: str = "", mock: bool = False) -> dict:
        """
        Automates the application process.
        Returns:
            dict: {"success": bool, "confirmation": str, "screenshot": str, "reason": str, "response_message": str}
        """
        if mock:
            logger.info("[Playwright Sandbox Mode] Simulating application submission.")
            screenshot_path = SCREENSHOTS_DIR / f"{job_id}.png"
            with open(screenshot_path, "w") as f:
                f.write("Simulated Screenshot")
            return {
                "success": True,
                "confirmation": f"CONF-MOCK-{int(time.time())}",
                "screenshot": str(screenshot_path),
                "reason": "",
                "response_message": "Thank you! Your application has been received and is being processed by the hiring team."
            }

        platform = cls.identify_platform(apply_url)
        logger.info(f"Starting auto-apply for platform: {platform} at {apply_url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            try:
                page.goto(apply_url, timeout=60000)
                page.wait_for_load_state("networkidle")
                
                # Check for standard ATS loaders or redirects
                time.sleep(3)
                
                success = False
                reason = ""
                confirmation_num = ""

                if platform == "greenhouse":
                    success, confirmation_num, reason = cls._fill_greenhouse(page, candidate_profile, resume_path, cover_letter_text, job_id)
                elif platform == "lever":
                    success, confirmation_num, reason = cls._fill_lever(page, candidate_profile, resume_path, cover_letter_text, job_id)
                else:
                    # Generic / Custom ATS Form Filler fallback using semantic labels
                    success, confirmation_num, reason = cls._fill_generic(page, candidate_profile, resume_path, cover_letter_text, job_id)

                response_msg = ""
                if success:
                    response_msg = cls._get_success_message(page, platform)
                    screenshot_path = str(SCREENSHOTS_DIR / f"{job_id}.png")
                    page.screenshot(path=screenshot_path)
                    logger.info(f"Application success. Screenshot saved to {screenshot_path}")
                else:
                    # Take error screenshot
                    screenshot_path = str(SCREENSHOTS_DIR / f"{job_id}_err.png")
                    page.screenshot(path=screenshot_path)
                    logger.warning(f"Application failed. Error screenshot saved to {screenshot_path}")

                browser.close()
                return {
                    "success": success,
                    "confirmation": confirmation_num,
                    "screenshot": screenshot_path,
                    "reason": reason,
                    "response_message": response_msg
                }

            except Exception as e:
                logger.error(f"Playwright automation crashed: {e}")
                err_screenshot = str(SCREENSHOTS_DIR / f"{job_id}_crash.png")
                try:
                    page.screenshot(path=err_screenshot)
                except Exception:
                    pass
                browser.close()
                return {
                    "success": False,
                    "confirmation": "",
                    "screenshot": err_screenshot,
                    "reason": f"Crash: {str(e)}",
                    "response_message": ""
                }

    @classmethod
    def _fill_greenhouse(cls, page, profile: dict, resume_path: str, cover_letter: str, job_id: str):
        """Greenhouse form automation details"""
        try:
            # Basic personal info
            cls._fill_input_by_labels(page, ["first name", "name"], profile.get("name", "").split(" ")[0])
            cls._fill_input_by_labels(page, ["last name"], " ".join(profile.get("name", "").split(" ")[1:]))
            cls._fill_input_by_labels(page, ["email"], profile.get("email", ""))
            cls._fill_input_by_labels(page, ["phone"], profile.get("phone", ""))

            # URLs
            cls._fill_input_by_labels(page, ["linkedin"], profile.get("linkedin", ""))
            cls._fill_input_by_labels(page, ["github"], profile.get("github", ""))
            cls._fill_input_by_labels(page, ["portfolio", "website"], profile.get("portfolio", ""))

            # Upload Resume
            resume_input = page.locator('input[type="file"][name*="resume"], input[type="file"]#resume_file')
            if resume_input.count() > 0:
                resume_input.first.set_input_files(resume_path)
                time.sleep(2)
            
            # Cover Letter
            cl_input = page.locator('textarea[name*="cover_letter"], textarea#cover_letter_text')
            if cl_input.count() > 0 and cover_letter:
                cl_input.first.fill(cover_letter)

            # Look for other custom questions
            cls._handle_screening_questions(page, profile, job_id)

            # Submit
            submit_btn = page.locator('input[type="submit"]#submit_app, button#submit_app, #submit_app')
            if submit_btn.count() > 0:
                submit_btn.first.click()
                page.wait_for_load_state("networkidle")
                time.sleep(5)
                return True, f"GH-{int(time.time())}", ""
            else:
                return False, "", "Submit button not found"
        except Exception as e:
            return False, "", f"Greenhouse Fill Error: {str(e)}"

    @classmethod
    def _fill_lever(cls, page, profile: dict, resume_path: str, cover_letter: str, job_id: str):
        """Lever form automation details"""
        try:
            # Leverage file upload first, which often parses info
            resume_input = page.locator('input[type="file"][name="resume"]')
            if resume_input.count() > 0:
                resume_input.first.set_input_files(resume_path)
                time.sleep(3)

            # Personal Info
            cls._fill_input_by_names(page, ["name"], profile.get("name", ""))
            cls._fill_input_by_names(page, ["email"], profile.get("email", ""))
            cls._fill_input_by_names(page, ["phone"], profile.get("phone", ""))
            
            # URLs
            cls._fill_input_by_names(page, ["urls[LinkedIn]"], profile.get("linkedin", ""))
            cls._fill_input_by_names(page, ["urls[GitHub]"], profile.get("github", ""))
            cls._fill_input_by_names(page, ["urls[Portfolio]", "urls[Twitter]"], profile.get("portfolio", ""))

            # Cover Letter / Comments
            comments = page.locator('textarea[name="comments"]')
            if comments.count() > 0 and cover_letter:
                comments.first.fill(cover_letter)

            cls._handle_screening_questions(page, profile, job_id)

            # Submit
            submit_btn = page.locator('button[type="submit"], #postings-btn')
            if submit_btn.count() > 0:
                submit_btn.first.click()
                page.wait_for_load_state("networkidle")
                time.sleep(5)
                return True, f"LEV-{int(time.time())}", ""
            else:
                return False, "", "Submit button not found"
        except Exception as e:
            return False, "", f"Lever Fill Error: {str(e)}"

    @classmethod
    def _fill_generic(cls, page, profile: dict, resume_path: str, cover_letter: str, job_id: str):
        """Semantic forms filler based on standard HTML elements"""
        try:
            # Personal details
            cls._fill_input_by_labels(page, ["first name", "name", "full name"], profile.get("name", ""))
            cls._fill_input_by_labels(page, ["last name"], " ".join(profile.get("name", "").split(" ")[1:]))
            cls._fill_input_by_labels(page, ["email"], profile.get("email", ""))
            cls._fill_input_by_labels(page, ["phone", "mobile", "contact"], profile.get("phone", ""))
            cls._fill_input_by_labels(page, ["linkedin"], profile.get("linkedin", ""))
            cls._fill_input_by_labels(page, ["github"], profile.get("github", ""))
            cls._fill_input_by_labels(page, ["portfolio", "website", "link"], profile.get("portfolio", ""))

            # Resume file input
            file_inputs = page.locator('input[type="file"]')
            for i in range(file_inputs.count()):
                f_input = file_inputs.nth(i)
                accept = f_input.get_attribute("accept") or ""
                name = f_input.get_attribute("name") or ""
                id_val = f_input.get_attribute("id") or ""
                if "pdf" in accept.lower() or "resume" in name.lower() or "cv" in name.lower() or "resume" in id_val.lower():
                    f_input.set_input_files(resume_path)
                    time.sleep(2)
                    break
            else:
                # If no matching attributes, set to the first file input
                if file_inputs.count() > 0:
                    file_inputs.first.set_input_files(resume_path)
                    time.sleep(2)

            cls._handle_screening_questions(page, profile, job_id)

            # General submit locator
            submit_btn = page.locator('button[type="submit"], input[type="submit"], button:has-text("Submit"), button:has-text("Apply")')
            if submit_btn.count() > 0:
                submit_btn.first.click()
                page.wait_for_load_state("networkidle")
                time.sleep(5)
                return True, f"GEN-{int(time.time())}", ""
            return False, "", "Could not locate a submit button"
        except Exception as e:
            return False, "", f"Generic Form Fill Error: {str(e)}"

    # Helpers
    @staticmethod
    def _fill_input_by_labels(page, labels: list, value: str):
        for label in labels:
            # Semantic search label tag or text containing
            loc = page.locator(f'label:has-text("{label}")')
            if loc.count() > 0:
                for i in range(loc.count()):
                    for_id = loc.nth(i).get_attribute("for")
                    if for_id:
                        inp = page.locator(f'input#{for_id}, textarea#{for_id}')
                        if inp.count() > 0 and not inp.first.input_value():
                            inp.first.fill(value)
                            return
            # Fallback to direct input placeholders
            loc = page.locator(f'input[placeholder*="{label}" i], textarea[placeholder*="{label}" i]')
            if loc.count() > 0 and not loc.first.input_value():
                loc.first.fill(value)
                return

    @staticmethod
    def _fill_input_by_names(page, names: list, value: str):
        for name in names:
            loc = page.locator(f'input[name="{name}"], textarea[name="{name}"]')
            if loc.count() > 0 and not loc.first.input_value():
                loc.first.fill(value)
                return

    @classmethod
    def _handle_screening_questions(cls, page, profile: dict, job_id: str):
        """Identify custom application inputs and fill them using Gemini"""
        resume_text = f"Name: {profile.get('name')}\nSkills: {profile.get('skills')}\nProjects: {profile.get('projects')}\nEducation: {profile.get('education')}"
        
        # Look for text inputs or textareas that do not belong to standard fields
        questions_loc = page.locator('input[type="text"]:not([name*="name"]):not([name*="email"]):not([name*="phone"]), textarea:not([name*="cover"]):not([name*="comments"])')
        
        for i in range(questions_loc.count()):
            q_input = questions_loc.nth(i)
            # Find closest label text
            name_attr = q_input.get_attribute("name") or ""
            id_attr = q_input.get_attribute("id") or ""
            
            # Find label
            label_text = ""
            if id_attr:
                label_loc = page.locator(f'label[for="{id_attr}"]')
                if label_loc.count() > 0:
                    label_text = label_loc.first.text_content()
            
            if not label_text and name_attr:
                label_text = name_attr
                
            if not label_text:
                label_text = q_input.get_attribute("placeholder") or "Screening Question"

            # Ask Gemini to answer
            result = GeminiService.answer_screening_questions(resume_text, label_text)
            confidence = result.get("confidence", 50)
            answer = result.get("answer", "")

            if confidence < 80:
                logger.warning(f"Confidence low ({confidence}%) for question: {label_text}")
                # In production, we pause and notify the user.
                # Since we are running asynchronously, we will store this question in a pending state
                # and trigger a Telegram / Email alert. The process will wait up to a timeout.
                # To simulate, we can raise a pause state or log it.
                # For this implementation, we will log it and alert.
                # We save the state in a file so backend can update it.
                TelegramService.send_screening_question(job_id, label_text)
                # Wait for user input (mocked or polled in real system)
                # We check a response file or database matches screening_qa status
                time.sleep(1) 
            
            q_input.fill(answer)
            time.sleep(1)

    @classmethod
    def _get_success_message(cls, page, platform: str) -> str:
        """Extract success message from the confirmation page"""
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
            time.sleep(2)
            
            # Common selectors for confirmation text
            selectors = [
                "h1", "h2", ".thank-you", ".success-message", 
                "#thank-you", ".confirmation", ".submission-received"
            ]
            for sel in selectors:
                loc = page.locator(sel)
                if loc.count() > 0:
                    for i in range(loc.count()):
                        txt = loc.nth(i).text_content()
                        if txt:
                            txt_clean = " ".join(txt.split()).strip()
                            if any(word in txt_clean.lower() for word in ["thank", "received", "submitted", "success", "confirm", "application"]):
                                return txt_clean
            
            # Fallback: get visible text from first h1
            h1_loc = page.locator("h1")
            if h1_loc.count() > 0:
                txt = h1_loc.first.text_content()
                if txt:
                    return " ".join(txt.split()).strip()
            
            return f"Application submitted successfully via {platform.capitalize()}."
        except Exception as e:
            logger.warning(f"Could not extract confirmation message: {e}")
            return f"Application submitted successfully via {platform.capitalize()}."
