import logging
from datetime import datetime
from src.database import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SkillGapAnalyzerAgent:
    @classmethod
    def analyze_skills_gap(cls) -> dict:
        """
        Analyze all jobs discovered, identify top missing skills from candidate profile,
        and generate a structured learning roadmap.
        """
        logger.info("Running Skill Gap Analysis...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get candidate's current skills
        cursor.execute("SELECT skills FROM candidate_profile ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        candidate_skills = []
        if row and row["skills"]:
            candidate_skills = [s.strip().lower() for s in row["skills"].split(",")]
            
        # Update missing status in skills_gap table
        cursor.execute("SELECT id, skill_name FROM skills_gap")
        gap_rows = cursor.fetchall()
        for r in gap_rows:
            is_missing = 1 if r["skill_name"].lower() not in candidate_skills else 0
            cursor.execute("UPDATE skills_gap SET missing_in_profile = ? WHERE id = ?", (is_missing, r["id"]))
        conn.commit()
        
        # Fetch top missing skills sorted by frequency
        cursor.execute("""
            SELECT skill_name, occurrence_count 
            FROM skills_gap 
            WHERE missing_in_profile = 1 
            ORDER BY occurrence_count DESC 
            LIMIT 10
        """)
        top_missing = cursor.fetchall()
        conn.close()

        # Format roadmap steps based on frequency rank
        roadmap_steps = []
        for idx, item in enumerate(top_missing):
            skill = item["skill_name"]
            count = item["occurrence_count"]
            
            # Formulate structured suggestions based on popular tools
            resource = "Free Course / Official Documentation"
            difficulty = "Medium"
            if skill.lower() in ["docker", "kubernetes", "containers"]:
                resource = "Docker & Kubernetes guides (Roadmap.sh / FreeCodeCamp)"
                difficulty = "Medium"
            elif skill.lower() in ["aws", "cloud", "lambda", "s3"]:
                resource = "AWS Skill Builder / AWS Certified Cloud Practitioner"
                difficulty = "Medium"
            elif skill.lower() in ["langchain", "llm", "llama", "rag", "langgraph"]:
                resource = "DeepLearning.AI (Short Courses on LangChain & Agentic LLMs)"
                difficulty = "Hard"
            elif skill.lower() in ["redis", "celery", "caching"]:
                resource = "Redis University Free Courses"
                difficulty = "Medium"
            elif skill.lower() in ["typescript", "ts"]:
                resource = "TypeScript HandBook (Official website)"
                difficulty = "Easy"

            roadmap_steps.append({
                "rank": idx + 1,
                "skill_name": skill,
                "job_mentions": count,
                "recommended_resource": resource,
                "difficulty_level": difficulty,
                "suggested_hours": 10 + (idx * 2)
            })

        logger.info(f"Skill Gap Analysis completed. Found {len(roadmap_steps)} gap items.")
        return {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "trending_missing_skills": roadmap_steps
        }
