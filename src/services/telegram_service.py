import httpx
import logging
import threading
import time
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramService:
    @classmethod
    def _is_configured(cls) -> bool:
        return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

    @classmethod
    def send_message(cls, text: str) -> bool:
        """Send a message to the configured Telegram chat ID"""
        if not cls._is_configured():
            logger.info(f"[Telegram Sandbox Mode] Skip sending message: {text}")
            return True

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            resp = httpx.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                logger.info("Telegram notification sent successfully.")
                return True
            else:
                logger.error(f"Failed to send Telegram notification: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Telegram API Exception: {e}")
            return False

    @classmethod
    def send_job_alert(cls, job_data: dict, match_score: int) -> bool:
        """Send a formatted message for a high-match job"""
        text = (
            f"🔥 *New High Match Job Found!*\n\n"
            f"*Company:* {job_data.get('company_name')}\n"
            f"*Role:* {job_data.get('job_title')}\n"
            f"*Location:* {job_data.get('location')}\n"
            f"*Match Score:* `{match_score}%`\n"
            f"*Posted:* {job_data.get('posting_date') or 'N/A'}\n"
            f"*Source:* {job_data.get('source')}\n\n"
            f"[Apply / View details]({job_data.get('apply_link')})"
        )
        return cls.send_message(text)

    @classmethod
    def send_application_alert(cls, job_data: dict, success: bool, confirmation: str = "", reason: str = "") -> bool:
        """Send a formatted notification after applying"""
        status = "✅ *Applied Successfully*" if success else "❌ *Application Failed*"
        conf_details = f"\n*Confirmation:* `{confirmation}`" if confirmation else ""
        fail_details = f"\n*Reason:* `{reason}`" if not success else ""
        
        text = (
            f"🚀 *Application Attempted*\n\n"
            f"*Role:* {job_data.get('job_title')}\n"
            f"*Company:* {job_data.get('company_name')}\n"
            f"*Status:* {status}{conf_details}{fail_details}\n"
            f"*Time:* {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return cls.send_message(text)

    @classmethod
    def send_screening_question(cls, job_id: str, question: str, options: list = None) -> bool:
        """Send screening question that requires user response"""
        opt_text = ""
        if options:
            opt_text = "\n*Options:*\n" + "\n".join([f"- {opt}" for opt in options])

        text = (
            f"❓ *Form Automation Question Alert*\n\n"
            f"Playwright encountered a screening question with low confidence (<80%):\n\n"
            f"*Question:* {question}{opt_text}\n\n"
            f"To answer, reply to this message using command:\n"
            f"`/ans {job_id} your answer here`"
        )
        return cls.send_message(text)

    @classmethod
    def send_referral_alert(cls, job_title: str, company: str, contact_name: str, contact_title: str) -> bool:
        """Send alert that a referral outreach is drafted"""
        text = (
            f"🤝 *Referral Opportunity Found!*\n\n"
            f"For high-match job `{job_title}` at *{company}*:\n"
            f"*Contact Name:* {contact_name}\n"
            f"*Title:* {contact_title}\n\n"
            f"Outreach templates are generated and ready on your Dashboard!"
        )
        return cls.send_message(text)

    @classmethod
    def poll_for_replies(cls, on_answer_callback):
        """
        Background listener for Telegram commands.
        Callback format: on_answer_callback(job_id, answer_text)
        """
        if not cls._is_configured():
            logger.info("Telegram long polling disabled in sandbox mode.")
            return

        def _polling_loop():
            offset = 0
            logger.info("Starting Telegram Bot listener thread...")
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            
            while True:
                try:
                    params = {"offset": offset, "timeout": 30}
                    resp = httpx.get(url, params=params, timeout=35)
                    if resp.status_code == 200:
                        updates = resp.json().get("result", [])
                        for update in updates:
                            update_id = update.get("update_id")
                            offset = update_id + 1
                            
                            message = update.get("message", {})
                            text = message.get("text", "")
                            
                            if text.startswith("/ans"):
                                # Format: /ans job_id your answer here
                                parts = text.split(" ", 2)
                                if len(parts) >= 3:
                                    job_id = parts[1]
                                    ans = parts[2]
                                    logger.info(f"Received answer from Telegram: job={job_id}, ans={ans}")
                                    on_answer_callback(job_id, ans)
                                    cls.send_message(f"✅ Answer registered for Job ID `{job_id}`.")
                                else:
                                    cls.send_message("❌ Invalid format. Use: `/ans <job_id> <your answer>`")
                    
                except Exception as e:
                    logger.error(f"Error in Telegram polling loop: {e}")
                time.sleep(2)

        thread = threading.Thread(target=_polling_loop, daemon=True)
        thread.start()
