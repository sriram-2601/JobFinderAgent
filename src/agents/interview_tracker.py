import logging
import re
from datetime import datetime
from src.database import get_db_connection
from src.services.email_service import EmailService
from src.services.telegram_service import TelegramService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InterviewTrackerAgent:
    @classmethod
    def track_inbox_updates(cls) -> list:
        """
        Scan Gmail via IMAP, identify recruitment updates, and synchronize them with the database.
        Returns:
            list: List of synchronized updates
        """
        logger.info("Scanning Gmail inbox for application and interview updates...")
        email_updates = EmailService.scan_inbox_for_updates()
        
        if not email_updates:
            logger.info("No new application updates found in inbox.")
            return []

        conn = get_db_connection()
        cursor = conn.cursor()
        
        synced = []
        for update in email_updates:
            sender = update["sender"]
            subject = update["subject"]
            category = update["category"] # OA_RECEIVED, INTERVIEW_SCHEDULED, REJECTED, OFFER_RECEIVED
            
            # Extract company name from sender domain or subject
            company = cls._guess_company_name(sender, subject)
            if not company:
                continue

            # Look up active application matching company name
            cursor.execute("""
                SELECT a.id, j.job_title, j.company_name 
                FROM applications a
                JOIN jobs j ON a.job_id = j.id
                WHERE LOWER(j.company_name) LIKE ? 
                ORDER BY a.applied_at DESC LIMIT 1
            """, (f"%{company.lower()}%",))
            
            app_row = cursor.fetchone()
            if app_row:
                app_id = app_row["id"]
                job_title = app_row["job_title"]
                company_name = app_row["company_name"]

                if category == "APPLICATION_CONFIRMED":
                    # Update confirmation email details
                    cursor.execute("""
                        UPDATE applications 
                        SET email_confirmation_subject = ?,
                            email_confirmation_sender = ?,
                            email_confirmation_date = ?,
                            email_confirmation_snippet = ?
                        WHERE id = ?
                    """, (subject, sender, update.get("date", ""), update.get("snippet", ""), app_id))
                    synced.append({
                        "company": company_name,
                        "role": job_title,
                        "new_status": "EMAIL_CONFIRMED"
                    })
                    continue
                
                # Check current status of the application
                cursor.execute("SELECT status FROM applications WHERE id = ?", (app_id,))
                current_status = cursor.fetchone()[0]
                
                if current_status != category:
                    # Update application status
                    cursor.execute("UPDATE applications SET status = ? WHERE id = ?", (category, app_id))
                    
                    # Log interview schedule if applicable
                    if category in ["OA_RECEIVED", "INTERVIEW_SCHEDULED"]:
                        cursor.execute("""
                            INSERT INTO interviews (application_id, stage, scheduled_at, status, notes)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            app_id, 
                            "OA" if category == "OA_RECEIVED" else "TECHNICAL",
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "SCHEDULED",
                            f"Detected automatically from email subject: {subject}"
                        ))
                    
                    synced.append({
                        "company": company_name,
                        "role": job_title,
                        "new_status": category
                    })
                    
                    # Send telegram and email alerts
                    cls._send_telegram_status_alert(company_name, job_title, category, subject)
                    EmailService.send_status_update_notification(
                        company_name=company_name,
                        job_title=job_title,
                        new_status=category,
                        email_subject=subject,
                        date_detected=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                    
        conn.commit()
        conn.close()
        
        logger.info(f"Inbox scan finished. Synchronized {len(synced)} application statuses.")
        return synced

    @staticmethod
    def _guess_company_name(sender: str, subject: str) -> str:
        """Attempt to extract company name from email details"""
        # Try to find company name in domain, excluding common email clients
        domain_match = re.search(r"@([a-zA-Z0-9\-]+)\.[a-zA-Z]+", sender)
        if domain_match:
            domain = domain_match.group(1).lower()
            if domain not in ["gmail", "outlook", "hotmail", "yahoo", "proton", "google", "zoho", "mail"]:
                return domain
                
        # Try to search subject "Your application to Vercel" or "Vercel Interview"
        subj_clean = subject.replace("Re:", "").replace("Fwd:", "").strip()
        words = re.findall(r"\b[a-zA-Z0-9\-]+\b", subj_clean)
        # Check database company titles against words in subject
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT company_name FROM jobs")
        companies = [row["company_name"].lower() for row in cursor.fetchall()]
        conn.close()
        
        for w in words:
            w_lower = w.lower()
            if w_lower in companies:
                return w_lower
                
        return ""

    @staticmethod
    def _send_telegram_status_alert(company: str, role: str, status: str, subject: str):
        """Dispatch instant Telegram message summarizing the update"""
        emoji = "📋"
        status_msg = status
        
        if status == "OA_RECEIVED":
            emoji = "📝"
            status_msg = "Online Assessment (OA) Request Received"
        elif status == "INTERVIEW_SCHEDULED":
            emoji = "📞"
            status_msg = "Interview Invitation Received"
        elif status == "REJECTED":
            emoji = "💔"
            status_msg = "Application Status Update (Rejection)"
        elif status == "OFFER_RECEIVED":
            emoji = "🎉"
            status_msg = "Job Offer Received!"

        text = (
            f"{emoji} *Recruitment Update Alert*\n\n"
            f"*Company:* {company}\n"
            f"*Role:* {role}\n"
            f"*Status:* `{status_msg}`\n\n"
            f"*Subject:* _{subject}_"
        )
        TelegramService.send_message(text)
