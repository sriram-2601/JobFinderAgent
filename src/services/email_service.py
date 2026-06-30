import smtplib
import imaplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from datetime import datetime
from src.config import (
    SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
    IMAP_SERVER, IMAP_PORT, IMAP_USERNAME, IMAP_PASSWORD
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    @classmethod
    def _is_configured(cls) -> bool:
        return bool(SMTP_USERNAME and SMTP_PASSWORD)

    @classmethod
    def send_html_email(cls, to_email: str, subject: str, html_content: str) -> bool:
        """Send an HTML email via SMTP"""
        if not cls._is_configured():
            logger.info(f"[Email Sandbox Mode] Skip sending email to {to_email}.\nSubject: {subject}\nContent: {html_content[:150]}...")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = SMTP_USERNAME
            msg["To"] = to_email

            part = MIMEText(html_content, "html")
            msg.attach(part)

            # Establish secure connection
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, [to_email], msg.as_string())
            server.quit()
            logger.info(f"Email sent successfully to {to_email} - Subject: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    @classmethod
    def send_job_alert(cls, job_data: dict, match_score: int) -> bool:
        """Send instant alert for a newly discovered job"""
        subject = f"🔥 New High Match Job: {job_data.get('job_title')} at {job_data.get('company_name')} ({match_score}%)"
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f5f7; padding: 20px; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; border: 1px solid #e1e4e8;">
                    <h2 style="color: #4f46e5;">New Match Found!</h2>
                    <p>We discovered a job post matching your profile:</p>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 8px 0; font-weight: bold; width: 150px;">Role:</td><td>{job_data.get('job_title')}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Company:</td><td>{job_data.get('company_name')}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Location:</td><td>{job_data.get('location')}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Match Score:</td><td><strong style="color: #10b981;">{match_score}%</strong></td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Source:</td><td>{job_data.get('source')}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Date Found:</td><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                    </table>
                    <div style="margin-top: 20px; text-align: center;">
                        <a href="{job_data.get('apply_link')}" style="background-color: #4f46e5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">View/Apply Job</a>
                    </div>
                </div>
            </body>
        </html>
        """
        return cls.send_html_email(SMTP_USERNAME, subject, html)

    @classmethod
    def send_application_notification(cls, job_data: dict, success: bool, confirmation: str = "", reason: str = "") -> bool:
        """Send email status after auto-apply execution"""
        status_text = "Submitted Successfully" if success else "Failed to Apply"
        color = "#10b981" if success else "#ef4444"
        subject = f"🚀 Application {status_text}: {job_data.get('job_title')} @ {job_data.get('company_name')}"
        
        details_html = f"<tr><td style='padding: 8px 0; font-weight: bold;'>Confirmation:</td><td>{confirmation}</td></tr>" if confirmation else ""
        error_html = f"<tr><td style='padding: 8px 0; font-weight: bold; color: red;'>Failure Reason:</td><td style='color: red;'>{reason}</td></tr>" if not success else ""
        desc_snippet = job_data.get("description", "No description available.")
        # Limit description size in email to maintain neat presentation
        if len(desc_snippet) > 400:
            desc_snippet = desc_snippet[:400] + "..."

        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f5f7; padding: 20px; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; border: 1px solid #e1e4e8;">
                    <h2 style="color: {color};">Application Update</h2>
                    <p>The Auto-Applier Agent attempted to submit an application:</p>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 8px 0; font-weight: bold; width: 150px;">Role:</td><td>{job_data.get('job_title')}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Company:</td><td>{job_data.get('company_name')}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Location:</td><td>{job_data.get('location')}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Job Source:</td><td>{job_data.get('source')}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Original Job Link:</td><td><a href="{job_data.get('apply_link')}" style="color: #4f46e5; text-decoration: underline; font-size: 13px;">{job_data.get('apply_link')}</a></td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Status:</td><td><strong style="color: {color};">{status_text}</strong></td></tr>
                        {details_html}
                        {error_html}
                    </table>
                    
                    <div style="margin-top: 15px; padding: 15px; background-color: #f9fafb; border-left: 4px solid #4f46e5; border-radius: 4px;">
                        <h4 style="margin: 0 0 8px 0; color: #4f46e5;">Job Description Snippet:</h4>
                        <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #555;">{desc_snippet}</p>
                    </div>

                    <div style="margin-top: 20px; text-align: center;">
                        <a href="{job_data.get('apply_link')}" style="background-color: #4f46e5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">View Job Details</a>
                    </div>
                </div>
            </body>
        </html>
        """
        return cls.send_html_email(SMTP_USERNAME, subject, html)

    @classmethod
    def scan_inbox_for_updates(cls) -> list:
        """
        Scan Gmail Inbox using IMAP for updates like OAs, interviews, rejections, offers, and confirmations.
        Returns:
            list: List of dicts representing parsed updates:
                [{"sender": str, "subject": str, "date": str, "category": str, "snippet": str}]
        """
        if not IMAP_PASSWORD or not IMAP_USERNAME:
            logger.info("IMAP not configured. Skipping email inbox scan.")
            return []

        updates = []
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            mail.login(IMAP_USERNAME, IMAP_PASSWORD)
            mail.select("inbox")

            # Search last 30 messages in Inbox
            status, messages = mail.search(None, 'ALL')
            
            if status == "OK" and messages[0]:
                for num in messages[0].split()[-30:]: # Check last 30 messages
                    status, data = mail.fetch(num, "(RFC822)")
                    if status != "OK":
                        continue
                    
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    subject = str(msg.get("subject", ""))
                    sender = str(msg.get("from", ""))
                    date_str = str(msg.get("date", ""))

                    # Extract body snippet
                    snippet = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode(errors="ignore")
                                    snippet = body[:200]
                                except Exception:
                                    pass
                                break
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode(errors="ignore")
                            snippet = body[:200]
                        except Exception:
                            pass
                    
                    if snippet:
                        snippet = " ".join(snippet.split())
                    else:
                        snippet = subject

                    # Determine category
                    subj_lower = subject.lower()
                    category = None
                    if any(k in subj_lower for k in ["online assessment", "hackerrank", "codility", "test invitation", "assessment link", "coding test"]):
                        category = "OA_RECEIVED"
                    elif any(k in subj_lower for k in ["interview", "schedule", "zoom link", "google meet", "chat with", "availability for"]):
                        category = "INTERVIEW_SCHEDULED"
                    elif any(k in subj_lower for k in ["unfortunate", "not selected", "thank you for your interest", "decided to move forward with other"]):
                        category = "REJECTED"
                    elif any(k in subj_lower for k in ["job offer", "offer letter", "congratulations", "welcome to the team"]):
                        category = "OFFER_RECEIVED"
                    elif any(k in subj_lower for k in ["received", "submitted", "confirm", "thank you for applying", "thanks for applying", "applying to", "application confirmation"]):
                        category = "APPLICATION_CONFIRMED"

                    if category:
                        updates.append({
                            "sender": sender,
                            "subject": subject,
                            "date": date_str,
                            "category": category,
                            "snippet": snippet
                        })
            mail.logout()
        except Exception as e:
            logger.error(f"Error occurred while scanning inbox: {e}")
        return updates

    @classmethod
    def send_status_update_notification(cls, company_name: str, job_title: str, new_status: str, email_subject: str, date_detected: str) -> bool:
        """Send email alert when the application status changes (e.g., OA received or Interview scheduled)"""
        status_titles = {
            "OA_RECEIVED": "📝 Online Assessment (OA) Request Detected",
            "INTERVIEW_SCHEDULED": "📞 Interview Invitation Received",
            "REJECTED": "💔 Application Status Update (Rejection)",
            "OFFER_RECEIVED": "🎉 Job Offer Received!"
        }
        
        title = status_titles.get(new_status, "Application Status Updated")
        subject = f"🔔 {title}: {job_title} @ {company_name}"
        color = "#ef4444" if new_status == "REJECTED" else "#4f46e5"
        if new_status == "OFFER_RECEIVED":
            color = "#10b981"
        elif new_status == "OA_RECEIVED":
            color = "#f59e0b"

        # Determine next steps description and preparation guides
        next_rounds = "Standard recruiting review."
        prep_tips = "Keep applying and tracking your applications on the dashboard."
        
        if new_status == "OA_RECEIVED":
            next_rounds = "Typically an online coding assessment (1-2 hours) hosting algorithmic challenges or MCQs."
            prep_tips = """
            • <strong>Topic Coverage</strong>: Review standard Arrays, Strings, HashMaps, and SQL queries.<br/>
            • <strong>Coding Sandboxes</strong>: Practice standard HackerRank/LeetCode Easy to Medium problems.<br/>
            • <strong>Integrity</strong>: Ensure you take the assessment in a quiet room; many ATS use webcam proctoring.
            """
        elif new_status == "INTERVIEW_SCHEDULED":
            next_rounds = "Live technical coding round, project architectural review, or a behavioral/HR check."
            prep_tips = """
            • <strong>Project Walkthrough</strong>: Prepare a 3-minute explanation of your <em>AWS Lambda Model Slicing</em> and <em>Sahaya Chatbot</em> projects.<br/>
            • <strong>Technical Foundations</strong>: Refresh OOPs concepts, Python dictionary mechanics, and basic React hooks.<br/>
            • <strong>Behavioral Prep</strong>: Structure answers using the STAR format (Situation, Task, Action, Result) for behavioral fit questions.
            """
        elif new_status == "OFFER_RECEIVED":
            next_rounds = "Review contract agreement documents and compensation packages."
            prep_tips = "Verify joining date parameters. Compile any queries you want to raise with the HR representative."

        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f5f7; padding: 20px; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; border: 1px solid #e1e4e8;">
                    <h2 style="color: {color}; border-bottom: 2px solid {color}; padding-bottom: 10px; margin-top: 0;">{title}</h2>
                    <p style="font-size: 15px; line-height: 1.6;">We detected a new communication update regarding your application:</p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                        <tr style="background-color: #f9fafb;"><td style="padding: 10px; font-weight: bold; width: 150px; border-bottom: 1px solid #eee;">Company:</td><td style="padding: 10px; border-bottom: 1px solid #eee;">{company_name}</td></tr>
                        <tr><td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #eee;">Applied Role:</td><td style="padding: 10px; border-bottom: 1px solid #eee;">{job_title}</td></tr>
                        <tr style="background-color: #f9fafb;"><td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #eee;">Next Stage:</td><td style="padding: 10px; border-bottom: 1px solid #eee; color: {color}; font-weight: bold;">{new_status.replace('_', ' ')}</td></tr>
                        <tr><td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #eee;">Email Subject:</td><td style="padding: 10px; border-bottom: 1px solid #eee; font-style: italic;">{email_subject}</td></tr>
                        <tr style="background-color: #f9fafb;"><td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #eee;">Detected Time:</td><td style="padding: 10px; border-bottom: 1px solid #eee;">{date_detected}</td></tr>
                    </table>

                    <div style="margin: 20px 0; padding: 15px; background-color: #eef2ff; border-radius: 6px;">
                        <h4 style="margin: 0 0 8px 0; color: #4f46e5; font-size: 14px; text-transform: uppercase;">What is the next round?</h4>
                        <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #333;">{next_rounds}</p>
                    </div>

                    <div style="margin: 20px 0; padding: 15px; background-color: #f0fdf4; border-radius: 6px; border-left: 4px solid #10b981;">
                        <h4 style="margin: 0 0 10px 0; color: #10b981; font-size: 14px; text-transform: uppercase;">Preparation Checklist:</h4>
                        <div style="margin: 0; font-size: 13px; line-height: 1.6; color: #333;">{prep_tips}</div>
                    </div>

                    <p style="font-size: 12px; color: #777; text-align: center; margin-top: 30px;">
                        This interview event has been logged in your dashboard calendar. You can update dates or paste video links directly on the dashboard.
                    </p>
                </div>
            </body>
        </html>
        """
        return cls.send_html_email(SMTP_USERNAME, subject, html)

    @classmethod
    def scan_inbox_for_jobs(cls) -> list:
        """
        Scan Gmail Inbox using IMAP for emails containing job opportunities/links to apply.
        Returns:
            list: List of dicts representing parsed jobs.
        """
        if not IMAP_PASSWORD or not IMAP_USERNAME:
            logger.info("IMAP not configured. Skipping job email scan.")
            return []

        from src.services.gemini_service import GeminiService
        discovered_jobs = []
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            mail.login(IMAP_USERNAME, IMAP_PASSWORD)
            mail.select("inbox")

            # Search last 50 messages in Inbox
            status, messages = mail.search(None, 'ALL')
            
            if status == "OK" and messages[0]:
                # We check the last 50 messages to find job postings
                msg_ids = messages[0].split()[-50:]
                for num in msg_ids:
                    status, data = mail.fetch(num, "(RFC822)")
                    if status != "OK":
                        continue
                    
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    subject = str(msg.get("subject", ""))
                    sender = str(msg.get("from", ""))
                    date_str = str(msg.get("date", ""))

                    # Extract body content (text/plain or text/html)
                    body_text = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type in ["text/plain", "text/html"]:
                                try:
                                    payload = part.get_payload(decode=True).decode(errors="ignore")
                                    body_text += "\n" + payload
                                except Exception:
                                    pass
                    else:
                        try:
                            body_text = msg.get_payload(decode=True).decode(errors="ignore")
                        except Exception:
                            pass
                    
                    if not body_text:
                        body_text = subject
                    
                    # Clean html if HTML
                    if "<html" in body_text.lower() or "<div" in body_text.lower():
                        try:
                            from bs4 import BeautifulSoup
                            body_text = BeautifulSoup(body_text, "html.parser").get_text()
                        except Exception:
                            pass
                            
                    body_text = " ".join(body_text.split())
                    # Limit body_text size sent to Gemini to keep it quick and cheap
                    snippet_limit = body_text[:3000]

                    # Check for job opportunities or apply links using Gemini
                    parsed_job = GeminiService.parse_job_email(subject, snippet_limit)
                    if parsed_job and parsed_job.get("is_job_opportunity") and parsed_job.get("apply_link"):
                        discovered_jobs.append({
                            "company_name": parsed_job.get("company_name", "Unknown"),
                            "job_title": parsed_job.get("job_title", "Software Engineer"),
                            "job_type": "Full-Time",
                            "location": parsed_job.get("location", "Remote"),
                            "apply_link": parsed_job.get("apply_link"),
                            "description": parsed_job.get("description", ""),
                            "source": f"Email ({sender})",
                            "posting_date": datetime.now().strftime("%Y-%m-%d"),
                            "priority": 2
                        })
            mail.logout()
        except Exception as e:
            logger.error(f"Error occurred while scanning inbox for jobs: {e}")
        return discovered_jobs

