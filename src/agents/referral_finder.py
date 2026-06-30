import logging
import urllib.parse
import httpx
import re
from bs4 import BeautifulSoup
from src.database import get_db_connection
from src.services.telegram_service import TelegramService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReferralFinderAgent:
    @classmethod
    def find_referrals(cls, job_id: str) -> list:
        """
        Query search engine for recruiters/hiring managers at the company.
        Generate outreach message templates and store details in the database.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get job details
        cursor.execute("SELECT company_name, job_title, id FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        
        # Get candidate profile details
        cursor.execute("SELECT * FROM candidate_profile ORDER BY id DESC LIMIT 1")
        profile = cursor.fetchone()
        conn.close()

        if not job or not profile:
            logger.error("Job or candidate profile not found for referral search.")
            return []

        company = job["company_name"]
        role = job["job_title"]
        logger.info(f"Finding referrals/recruiters for {role} at {company}...")

        # Search Query for recruiters
        query = f'site:linkedin.com/in/ ("recruiter" OR "hiring manager" OR "engineering manager") "{company}"'
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }

        contacts = []
        try:
            resp = httpx.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                snippets = soup.find_all("a", class_="result__snippet")
                for snip in snippets:
                    title_tag = snip.find_previous("a", class_="result__url")
                    title_text = title_tag.get_text() if title_tag else ""
                    href = snip.get("href", "")
                    
                    # Parse name and title from DDG title: e.g. "John Doe - Tech Recruiter - Acme | LinkedIn"
                    name = "Outreach Contact"
                    title = "Recruitment / Hiring Team"
                    
                    if title_text:
                        parts = title_text.split("-")
                        if len(parts) >= 2:
                            name = parts[0].replace("| LinkedIn", "").strip()
                            title = parts[1].strip()
                    
                    # Extract raw LinkedIn URL
                    parsed_url = urllib.parse.urlparse(href)
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    linkedin_url = query_params.get("uddg", [href])[0]
                    
                    if "linkedin.com/in/" in linkedin_url:
                        contacts.append({
                            "name": name,
                            "title": title,
                            "linkedin": linkedin_url
                        })
        except Exception as e:
            logger.error(f"Error searching recruiters on LinkedIn: {e}")

        # Fallback if no contacts found
        if not contacts:
            contacts.append({
                "name": "Hiring Manager",
                "title": f"Engineering Leader at {company}",
                "linkedin": f"https://www.linkedin.com/company/{company.lower()}"
            })

        # Save to recruiters & referrals tables
        conn = get_db_connection()
        cursor = conn.cursor()
        
        saved_referrals = []
        for contact in contacts:
            # 1. Add to recruiters table
            cursor.execute("""
                INSERT INTO recruiters (company_name, name, title, contact_info)
                VALUES (?, ?, ?, ?)
            """, (company, contact["name"], contact["title"], contact["linkedin"]))
            
            # Generate personalized templates
            ref_msg, rec_msg, follow_msg = cls.generate_outreach_templates(
                candidate_name=profile["name"],
                contact_name=contact["name"],
                role=role,
                company=company,
                skills=profile["skills"]
            )
            
            # 2. Add to referrals table
            cursor.execute("""
                INSERT INTO referrals (job_id, contact_name, contact_title, contact_info, referral_message, recruiter_message, follow_up_message, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                contact["name"],
                contact["title"],
                contact["linkedin"],
                ref_msg,
                rec_msg,
                follow_msg,
                "FOUND"
            ))
            
            saved_referrals.append(contact)
            
        conn.commit()
        conn.close()

        # Send alert
        if contacts:
            main_contact = contacts[0]
            TelegramService.send_referral_alert(role, company, main_contact["name"], main_contact["title"])
            
        return saved_referrals

    @classmethod
    def generate_outreach_templates(cls, candidate_name: str, contact_name: str, role: str, company: str, skills: str) -> tuple:
        """Generate tailored outreach text blocks based on candidate skills and role"""
        # Split first name
        c_first = contact_name.split(" ")[0] if contact_name else "Hiring Team"
        
        # General Referral Ask to an Employee
        referral_message = (
            f"Hi {c_first},\n\n"
            f"I hope you're doing well! I saw an opening for {role} at {company} and was incredibly excited. "
            f"I recently graduated with a B.Tech in CSE (Data Science) and have hands-on experience deploying "
            f"serverless machine learning architectures using AWS Lambda and containerized Docker systems.\n\n"
            f"Given your background at {company}, I would be extremely grateful for any advice you have, "
            f"or if you would be open to referring me for this role. I've already prepared my application materials.\n\n"
            f"Thank you so much for your time and guidance!\n\n"
            f"Best regards,\n"
            f"{candidate_name}\n"
        )
        
        # Direct Pitch to a Recruiter / Hiring Manager
        recruiter_message = (
            f"Dear {contact_name},\n\n"
            f"I hope this message finds you well. I recently applied for the {role} position at {company} "
            f"and wanted to reach out directly to express my interest.\n\n"
            f"I am a recent Computer Science graduate specialized in full-stack engineering and cloud deployments. "
            f"Some highlights of my projects include:\n"
            f"• Building serverless ML inference applications using AWS Lambda & Docker\n"
            f"• Designing responsive frontends with React and Vite\n"
            f"• Developing mental health AI Chatbots utilizing Groq API and Firebase\n\n"
            f"I've attached my resume to my application, but would love the opportunity to briefly connect "
            f"and discuss how my technical skills in Python, React, and databases align with your team's goals.\n\n"
            f"Thank you for your consideration.\n\n"
            f"Warmly,\n"
            f"{candidate_name}\n"
        )
        
        # Follow-Up message after 3 days
        follow_up_message = (
            f"Hi {c_first},\n\n"
            f"I wanted to follow up briefly regarding the {role} position at {company} we chatted about last week. "
            f"I understand you are busy, but if there is any opportunity for a quick call or a referral, I'd "
            f"greatly appreciate it. Let me know if you would like me to share my resume directly.\n\n"
            f"Thank you again!\n\n"
            f"Best,\n"
            f"{candidate_name}"
        )
        
        return referral_message, recruiter_message, follow_up_message
