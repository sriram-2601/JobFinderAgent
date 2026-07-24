import logging
import os
from datetime import datetime
from src.database import get_db_connection
from src.services.playwright_service import PlaywrightService
from src.services.email_service import EmailService
from src.services.telegram_service import TelegramService
from src.config import BASE_DIR, APP_MODE, DATA_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoApplierAgent:
    @classmethod
    def apply_job(cls, job_id: str, user_id: int = None, mock: bool = True) -> dict:
        """
        Executes form filling and submissions via Playwright.
        """
        if user_id is None:
            user_id = 1
            
        # 1. Prevent duplicate applications
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM applications WHERE job_id = ? AND user_id = ?", (job_id, user_id))
        already_applied = cursor.fetchone()
        if already_applied:
            logger.warning(f"Already applied to job ID {job_id} for user {user_id}. Skipping.")
            conn.close()
            return {"success": False, "reason": "Duplicate application"}
 
        # Fetch candidate profile details
        cursor.execute("SELECT * FROM candidate_profile WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
        profile = cursor.fetchone()
        
        # Fetch job and match details
        cursor.execute("""
            SELECT j.*, m.cover_letter, m.match_score 
            FROM jobs j 
            JOIN matches m ON j.id = m.job_id 
            WHERE j.id = ? AND m.user_id = ?
        """, (job_id, user_id))
        job_match = cursor.fetchone()
        conn.close()
 
        if not profile or not job_match:
            logger.error(f"Profile or Job/Match data missing for application. job_id={job_id}, user_id={user_id}")
            return {"success": False, "reason": "Data missing"}
 
        # Define resume path: check profile for custom path
        resume_path = None
        if "resume_path" in profile.keys():
            resume_path = profile["resume_path"]
            
        if not resume_path or not os.path.exists(resume_path):
            # Fallback check
            resume_filename = "Sriram_Resume.pdf"
            resume_path = os.path.join(str(BASE_DIR), resume_filename)
            if not os.path.exists(resume_path):
                resume_path = os.path.join(os.getcwd(), resume_filename)
                if not os.path.exists(resume_path):
                    logger.error(f"Resume file not found at {resume_path}")
                    return {"success": False, "reason": "Resume PDF file not found"}
 
        logger.info(f"Automating application for user {user_id}: {job_match['job_title']} at {job_match['company_name']}")
 
        # Convert Row object to dictionary
        candidate_dict = dict(profile)
        job_dict = dict(job_match)
 
        # Execute Playwright apply (defaults to sandbox/mock mode for safety during development)
        result = PlaywrightService.apply_to_job(
            job_id=job_id,
            apply_url=job_dict["apply_link"],
            candidate_profile=candidate_dict,
            resume_path=resume_path,
            cover_letter_text=job_dict.get("cover_letter", ""),
            mock=mock
        )
 
        success = result.get("success", False)
        confirmation = result.get("confirmation", "")
        screenshot = result.get("screenshot", "")
        reason = result.get("reason", "")
        response_message = result.get("response_message", "")
 
        # Save application record
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Log path
        log_dir = os.path.join(str(DATA_DIR), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"{job_id}_{user_id}.log")
        with open(log_path, "w") as f:
            f.write(f"Application Date: {datetime.now().isoformat()}\n")
            f.write(f"Role: {job_dict['job_title']}\nCompany: {job_dict['company_name']}\n")
            f.write(f"Match Score: {job_dict['match_score']}\n")
            f.write(f"Status: {'Success' if success else 'Failed'}\n")
            if reason:
                f.write(f"Reason: {reason}\n")
            f.write(f"Confirmation Code: {confirmation}\n")
            if response_message:
                f.write(f"Response Message: {response_message}\n")
        
        cursor.execute("""
            INSERT INTO applications (job_id, applied_at, mode, status, confirmation_number, screenshot_path, log_path, response_message, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            APP_MODE,
            "APPLIED" if success else "REJECTED",
            confirmation,
            screenshot,
            log_path,
            response_message,
            user_id
        ))
        conn.commit()
        conn.close()
 
        # Dispatch real-time alerts
        EmailService.send_application_notification(job_dict, success, confirmation, reason)
        TelegramService.send_application_alert(job_dict, success, confirmation, reason)
 
        return {"success": success, "confirmation": confirmation, "screenshot": screenshot}
