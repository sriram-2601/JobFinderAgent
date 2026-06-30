import logging
from datetime import datetime, timedelta
from src.database import get_db_connection
from src.services.email_service import EmailService
from src.services.telegram_service import TelegramService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationAgent:
    @classmethod
    def generate_daily_summary(cls) -> bool:
        """Runs daily at 10 PM. Compiles and sends all events of the day"""
        logger.info("Generating Daily Job Search Summary...")
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Discovered jobs today
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE date(discovered_at) = ?", (today_str,))
        discovered_count = cursor.fetchone()[0]
        
        # Matches today
        cursor.execute("""
            SELECT j.job_title, j.company_name, m.match_score, m.match_status 
            FROM jobs j 
            JOIN matches m ON j.id = m.job_id 
            WHERE date(m.evaluated_at) = ?
        """, (today_str,))
        matches = cursor.fetchall()
        
        # Applications today
        cursor.execute("""
            SELECT j.job_title, j.company_name, a.status, a.confirmation_number 
            FROM jobs j 
            JOIN applications a ON j.id = a.job_id 
            WHERE date(a.applied_at) = ?
        """, (today_str,))
        applications = cursor.fetchall()
        conn.close()

        # Format HTML content
        match_rows = ""
        for m in matches:
            color = "#10b981" if m["match_score"] >= 80 else ("#f59e0b" if m["match_score"] >= 70 else "#ef4444")
            match_rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{m['job_title']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{m['company_name']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; color: {color}; font-weight: bold;">{m['match_score']}%</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{m['match_status']}</td>
            </tr>
            """
            
        app_rows = ""
        for a in applications:
            color = "#10b981" if a["status"] == "APPLIED" else "#ef4444"
            app_rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{a['job_title']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{a['company_name']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; color: {color}; font-weight: bold;">{a['status']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{a['confirmation_number'] or 'N/A'}</td>
            </tr>
            """

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; color: #333; background-color: #f4f5f7;">
                <div style="max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; border: 1px solid #e1e4e8;">
                    <h2 style="color: #4f46e5; border-bottom: 2px solid #4f46e5; padding-bottom: 10px;">Daily Job Search Summary</h2>
                    <p style="font-size: 16px;">Here is your summary report for <strong>{today_str}</strong>:</p>
                    
                    <div style="background-color: #eef2ff; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                        <ul style="margin: 0; padding-left: 20px;">
                            <li><strong>Jobs Discovered:</strong> {discovered_count}</li>
                            <li><strong>Jobs Evaluated:</strong> {len(matches)}</li>
                            <li><strong>Applications Submitted:</strong> {len(applications)}</li>
                        </ul>
                    </div>

                    <h3>Evaluated Matches</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <thead>
                            <tr style="background-color: #f3f4f6;">
                                <th style="padding: 8px; text-align: left;">Role</th>
                                <th style="padding: 8px; text-align: left;">Company</th>
                                <th style="padding: 8px; text-align: left;">Score</th>
                                <th style="padding: 8px; text-align: left;">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {match_rows if match_rows else '<tr><td colspan="4" style="padding: 8px; text-align: center;">No matches evaluated today.</td></tr>'}
                        </tbody>
                    </table>

                    <h3>Applications History</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background-color: #f3f4f6;">
                                <th style="padding: 8px; text-align: left;">Role</th>
                                <th style="padding: 8px; text-align: left;">Company</th>
                                <th style="padding: 8px; text-align: left;">Status</th>
                                <th style="padding: 8px; text-align: left;">Conf Code</th>
                            </tr>
                        </thead>
                        <tbody>
                            {app_rows if app_rows else '<tr><td colspan="4" style="padding: 8px; text-align: center;">No applications submitted today.</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </body>
        </html>
        """
        
        # Send Email & Telegram
        subject = f"📅 Daily Job Search Summary: {today_str}"
        EmailService.send_html_email(EmailService.SMTP_USERNAME, subject, html_content)
        
        tg_text = (
            f"📅 *Daily Summary ({today_str})*\n\n"
            f"• Jobs Crawled: `{discovered_count}`\n"
            f"• Matches Analyzed: `{len(matches)}`\n"
            f"• Submissions: `{len(applications)}`"
        )
        TelegramService.send_message(tg_text)
        return True

    @classmethod
    def generate_weekly_summary(cls) -> bool:
        """Runs Sunday at 10 PM. Compiles and sends all events of the week"""
        logger.info("Generating Weekly Summary...")
        
        last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Discovered jobs this week
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE discovered_at >= ?", (last_week,))
        discovered_count = cursor.fetchone()[0]
        
        # Applications this week
        cursor.execute("SELECT COUNT(*) FROM applications WHERE applied_at >= ?", (last_week,))
        applied_count = cursor.fetchone()[0]

        # Success rate and details
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM applications 
            WHERE applied_at >= ? 
            GROUP BY status
        """, (last_week,))
        stats = cursor.fetchall()
        
        conn.close()

        stat_summary = ""
        for s in stats:
            stat_summary += f"<li><strong>{s['status']}:</strong> {s['count']}</li>"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; color: #333; background-color: #f4f5f7;">
                <div style="max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; border: 1px solid #e1e4e8;">
                    <h2 style="color: #4f46e5; border-bottom: 2px solid #4f46e5; padding-bottom: 10px;">Weekly Application Analytics</h2>
                    <p style="font-size: 16px;">Here is your progress report for the last 7 days:</p>
                    
                    <div style="background-color: #f0fdf4; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                        <ul style="margin: 0; padding-left: 20px;">
                            <li><strong>Jobs Discovered:</strong> {discovered_count}</li>
                            <li><strong>Applications Submitted:</strong> {applied_count}</li>
                        </ul>
                    </div>

                    <h3>Application Stages Status</h3>
                    <ul style="padding-left: 20px;">
                        {stat_summary if stat_summary else '<li>No applications submitted this week.</li>'}
                    </ul>
                </div>
            </body>
        </html>
        """
        
        subject = "📊 Weekly Job Platform Analytics Report"
        EmailService.send_html_email(EmailService.SMTP_USERNAME, subject, html_content)
        
        tg_text = (
            f"📊 *Weekly Analytics Report*\n\n"
            f"• Weekly Crawls: `{discovered_count}`\n"
            f"• Weekly Submissions: `{applied_count}`\n"
            f"Please check your email for the detailed breakdown."
        )
        TelegramService.send_message(tg_text)
        return True

    @classmethod
    def generate_monthly_summary(cls) -> bool:
        """Runs 1st Day of Month at 9 AM. Monthly report"""
        logger.info("Generating Monthly Summary...")
        
        last_month = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Discovered jobs this month
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE discovered_at >= ?", (last_month,))
        discovered_count = cursor.fetchone()[0]
        
        # Applications this month
        cursor.execute("SELECT COUNT(*) FROM applications WHERE applied_at >= ?", (last_month,))
        applied_count = cursor.fetchone()[0]

        # Success rate
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM applications 
            WHERE applied_at >= ? 
            GROUP BY status
        """, (last_month,))
        stats = cursor.fetchall()
        
        conn.close()

        stat_summary = ""
        for s in stats:
            stat_summary += f"<li><strong>{s['status']}:</strong> {s['count']}</li>"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; color: #333; background-color: #f4f5f7;">
                <div style="max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; border: 1px solid #e1e4e8;">
                    <h2 style="color: #4f46e5; border-bottom: 2px solid #4f46e5; padding-bottom: 10px;">Monthly Job Platform Report</h2>
                    <p style="font-size: 16px;">Here is your autonomous activity log for the past 30 days:</p>
                    
                    <div style="background-color: #fffbeb; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                        <ul style="margin: 0; padding-left: 20px;">
                            <li><strong>Jobs Discovered:</strong> {discovered_count}</li>
                            <li><strong>Applications Submitted:</strong> {applied_count}</li>
                        </ul>
                    </div>

                    <h3>Application Status Summary</h3>
                    <ul style="padding-left: 20px;">
                        {stat_summary if stat_summary else '<li>No applications submitted this month.</li>'}
                    </ul>
                </div>
            </body>
        </html>
        """
        
        subject = "🏆 Monthly Autonomous Job Platform Report"
        EmailService.send_html_email(EmailService.SMTP_USERNAME, subject, html_content)
        
        tg_text = (
            f"🏆 *Monthly Summary Report*\n\n"
            f"• Jobs Discovered: `{discovered_count}`\n"
            f"• Total Submissions: `{applied_count}`\n"
            f"Your monthly status analytics has been generated and sent to email."
        )
        TelegramService.send_message(tg_text)
        return True
