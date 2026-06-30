import json
import logging
from datetime import datetime
from src.database import get_db_connection
from src.services.gemini_service import GeminiService
from src.config import PRIORITY_BOOSTS, APP_MODE
from src.services.email_service import EmailService
from src.services.telegram_service import TelegramService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIMatcherAgent:
    @classmethod
    def get_candidate_profile_text(cls, user_id: int = None) -> str:
        """Fetch candidate profile from DB and format as string"""
        if user_id is None:
            user_id = 1
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidate_profile WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return ""

        profile_text = (
            f"Name: {row['name']}\n"
            f"Email: {row['email']}\n"
            f"Phone: {row['phone']}\n"
            f"LinkedIn: {row['linkedin']}\n"
            f"GitHub: {row['github']}\n"
            f"Portfolio: {row['portfolio']}\n"
            f"Skills: {row['skills']}\n"
            f"Experience: {row['experience']}\n"
            f"Education: {row['education']}\n"
            f"Certifications: {row['certifications']}\n"
            f"Projects: {row['projects']}\n"
            f"Achievements: {row['achievements']}\n"
        )
        return profile_text

    @classmethod
    def calculate_boosted_score(cls, base_score: int, job_title: str) -> int:
        """Apply target priority boosts to the base match score"""
        boosted = base_score
        title_lower = job_title.lower()

        # +20 AI Roles
        ai_terms = ["ai", "generative ai", "llm", "prompt", "agentic", "machine learning", "ml", "nlp", "deep learning"]
        if any(term in title_lower for term in ai_terms):
            boosted += PRIORITY_BOOSTS["AI"]

        # +20 Python Roles
        if "python" in title_lower:
            boosted += PRIORITY_BOOSTS["Python"]

        # +15 Data Roles
        data_terms = ["data analyst", "data scientist", "data engineer", "analytics", "bi developer"]
        if any(term in title_lower for term in data_terms):
            boosted += PRIORITY_BOOSTS["Data"]

        # +15 Full Stack Roles
        fs_terms = ["full stack", "fullstack", "mern", "mean"]
        if any(term in title_lower for term in fs_terms):
            boosted += PRIORITY_BOOSTS["Full Stack"]

        # +10 React Roles
        if "react" in title_lower:
            boosted += PRIORITY_BOOSTS["React"]

        # +10 Node Roles
        if "node" in title_lower or "nodejs" in title_lower:
            boosted += PRIORITY_BOOSTS["Node"]

        # +10 Cloud Roles
        cloud_terms = ["cloud", "aws", "devops", "sre", "reliability"]
        if any(term in title_lower for term in cloud_terms):
            boosted += PRIORITY_BOOSTS["Cloud"]

        # +10 Testing Roles
        test_terms = ["test", "testing", "qa", "quality assurance", "automation tester"]
        if any(term in title_lower for term in test_terms):
            boosted += PRIORITY_BOOSTS["Testing"]

        # +10 IT Support Roles
        support_terms = ["support", "helpdesk", "technical support", "desktop support"]
        if any(term in title_lower for term in support_terms):
            boosted += PRIORITY_BOOSTS["IT Support"]

        # +15 General Developer / Engineer Roles
        general_terms = ["software engineer", "software developer", "developer", "engineer", "programmer", "frontend", "backend", "web developer", "java", "javascript", "c++", "go", "golang"]
        if any(term in title_lower for term in general_terms):
            boosted += PRIORITY_BOOSTS.get("General Developer", 15)

        return min(boosted, 100)

    @classmethod
    def evaluate_job(cls, job_id: str, user_id: int = None) -> dict:
        """
        Evaluate a single job from the database.
        Returns:
            dict: match details
        """
        if user_id is None:
            user_id = 1
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job_row = cursor.fetchone()
        conn.close()
 
        if not job_row:
            logger.error(f"Job ID {job_id} not found in database.")
            return {}
 
        resume_text = cls.get_candidate_profile_text(user_id)
        if not resume_text:
            logger.error(f"No candidate profile found in database for user_id={user_id}.")
            return {}
 
        logger.info(f"Evaluating job '{job_row['job_title']}' for user {user_id}...")
        analysis = GeminiService.analyze_job(
            resume_text, 
            job_row["job_title"], 
            job_row["description"]
        )
 
        base_score = analysis.get("match_score", 50)
        boosted_score = cls.calculate_boosted_score(base_score, job_row["job_title"])
        
        # Enforce location rules: if outside India, only Remote is allowed
        from src.config import is_location_allowed
        if not is_location_allowed(job_row["location"]):
            logger.warning(f"Overriding match score to 0. Location compatibility check failed for: {job_row['location']}")
            boosted_score = 0
            match_status = "REJECTED"
        else:
            # Decide status transition rules
            if boosted_score >= 80:
                match_status = "APPROVED"
            elif boosted_score >= 70:
                match_status = "PENDING_REVIEW"
            else:
                match_status = "REJECTED"
 
        # Save Match results to DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO matches (job_id, match_score, missing_skills, rank_relevance, optimize_suggestions, cover_letter, screening_qa, match_status, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            boosted_score,
            ",".join(analysis.get("missing_skills", [])),
            analysis.get("rank_relevance", "Low"),
            analysis.get("optimize_suggestions", ""),
            analysis.get("cover_letter", ""),
            json.dumps({"questions": []}), # placeholders for screening answers later
            match_status,
            user_id
        ))
        conn.commit()
        conn.close()
 
        logger.info(f"Job {job_id} match evaluated for user {user_id}. Score: {boosted_score} ({match_status})")
 
        # Save dynamic skills gaps to the skills_gap table
        cls._update_skills_gap(analysis.get("missing_skills", []))
 
        # Real-time notifications and actions
        if boosted_score >= 80:
            # Send real-time instant alerts
            EmailService.send_job_alert(dict(job_row), boosted_score)
            TelegramService.send_job_alert(dict(job_row), boosted_score)
 
            # Auto apply trigger if Autonomous mode is active
            if APP_MODE == "AUTONOMOUS":
                logger.info(f"Autonomous Mode enabled: Triggering Auto-Applier for job {job_id} for user {user_id}.")
                from src.agents.auto_applier import AutoApplierAgent
                # Trigger in separate thread or call directly
                AutoApplierAgent.apply_job(job_id, user_id)
        
        elif boosted_score >= 70:
            # Notify for manual review
            TelegramService.send_message(
                f"⚠️ *Manual Review Required*\n\n"
                f"*Role:* {job_row['job_title']}\n"
                f"*Company:* {job_row['company_name']}\n"
                f"*Score:* `{boosted_score}%`\n"
                f"Check dashboard to review and apply."
            )
 
        return {
            "job_id": job_id,
            "match_score": boosted_score,
            "status": match_status
        }

    @staticmethod
    def _update_skills_gap(missing_skills: list):
        """Register missing skills to database for weekly analysis"""
        if not missing_skills:
            return
        conn = get_db_connection()
        cursor = conn.cursor()
        for skill in missing_skills:
            skill_clean = skill.strip().capitalize()
            if not skill_clean:
                continue
            try:
                cursor.execute("""
                INSERT INTO skills_gap (skill_name, occurrence_count, in_demand_rank, missing_in_profile, updated_at)
                VALUES (?, 1, 99, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(skill_name) DO UPDATE SET
                occurrence_count = occurrence_count + 1,
                updated_at = CURRENT_TIMESTAMP
                """, (skill_clean,))
            except Exception as e:
                logger.error(f"Error registering skill gap: {e}")
        conn.commit()
        conn.close()
