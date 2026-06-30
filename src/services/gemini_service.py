import json
import logging
import google.generativeai as genai
from src.config import GEMINI_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini if key is provided
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini API configured successfully.")
else:
    logger.warning("GEMINI_API_KEY not found in environment. Running Gemini Service in SANDBOX/MOCK mode.")

class GeminiService:
    @staticmethod
    def _get_model():
        """Retrieve the Gemini model"""
        if not GEMINI_API_KEY:
            return None
        return genai.GenerativeModel("gemini-2.5-flash")

    @classmethod
    def analyze_job(cls, resume_text: str, job_title: str, job_description: str) -> dict:
        """
        Analyze a job listing against the candidate's resume.
        Returns:
            dict: {
                "match_score": int (0-100),
                "missing_skills": list,
                "rank_relevance": str (High, Medium, Low),
                "optimize_suggestions": str,
                "cover_letter": str
            }
        """
        model = cls._get_model()
        if not model:
            # Mock analysis for local testing/sandbox mode without API key
            logger.info("Using mock Gemini analysis (Sandbox Mode)")
            score = 75
            title_lower = job_title.lower()
            if any(r in title_lower for r in ["ai", "python", "ml", "llm", "agent"]):
                score += 15
            elif any(r in title_lower for r in ["react", "frontend", "full stack"]):
                score += 10
            score = min(score, 100)
            
            return {
                "match_score": score,
                "missing_skills": ["Docker", "Kubernetes", "AWS CloudFormation"],
                "rank_relevance": "High" if score >= 80 else ("Medium" if score >= 70 else "Low"),
                "optimize_suggestions": "Highlight serverless Docker deployment experience and AWS S3 model slicing more prominently.",
                "cover_letter": f"Dear Hiring Team,\n\nI am writing to express my interest in the {job_title} role..."
            }

        prompt = f"""
        You are an AI recruitment expert. Evaluate the matching score between the candidate's resume and the job description.
        
        Candidate Resume:
        {resume_text}
        
        Job Title: {job_title}
        Job Description:
        {job_description}
        
        Perform the following tasks:
        1. Calculate a base match score between 0 and 100 based strictly on skill and education alignment (do not apply any priority boosts, those are applied programmatically elsewhere).
        2. Identify any key skills or technologies in the job description that are missing from the candidate's resume.
        3. Rank the relevance of the job (High: score >= 80, Medium: score 70-79, Low: score < 70).
        4. Generate actionable, specific suggestions on how the candidate can optimize their resume for this specific job description.
        5. Generate a professional, short, and highly relevant cover letter tailored to the job requirements.
        
        You MUST return the output ONLY in JSON format with the following keys:
        {{
            "match_score": <int>,
            "missing_skills": [<string>],
            "rank_relevance": "<string>",
            "optimize_suggestions": "<string>",
            "cover_letter": "<string>"
        }}
        
        Ensure the output is valid JSON and nothing else.
        """
        try:
            response = model.generate_content(prompt)
            content = response.text.strip()
            # Parse JSON block
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error during Gemini job analysis: {e}")
            # Safe fallback
            return {
                "match_score": 50,
                "missing_skills": [],
                "rank_relevance": "Low",
                "optimize_suggestions": f"Error during analysis: {str(e)}",
                "cover_letter": "Hiring manager cover letter fallback."
            }

    @classmethod
    def answer_screening_questions(cls, resume_text: str, question: str) -> dict:
        """
        Answer a screening question based on the candidate's resume.
        Returns:
            dict: {
                "answer": str,
                "confidence": int (0-100)
            }
        """
        model = cls._get_model()
        if not model:
            # Sandbox Mode: Answer standard questions automatically
            logger.info("Using mock screening question answer (Sandbox Mode)")
            q_lower = question.lower()
            if "experience" in q_lower or "years" in q_lower:
                return {"answer": "0 years (recent graduate with hands-on internship-level academic projects)", "confidence": 95}
            if "salary" in q_lower:
                return {"answer": "Competitive / Negotiable", "confidence": 85}
            if "sponsorship" in q_lower or "visa" in q_lower:
                return {"answer": "No, I do not require sponsorship to work in the US/India.", "confidence": 90}
            return {"answer": "I have completed serverless machine learning deployments and built full stack React/Node.js web applications as detailed in my resume.", "confidence": 75}

        prompt = f"""
        You are an autonomous job application assistant. Answer the following job application screening question based ONLY on the candidate's resume.
        
        Candidate Resume:
        {resume_text}
        
        Screening Question:
        "{question}"
        
        Rules:
        1. Never fabricate experience.
        2. Always be honest. If the resume has no matching info, provide a professional, neutral answer or state that the candidate has academic/project experience in that area.
        3. Rate your confidence in the answer from 0 to 100 based on how well the resume addresses the question.
        
        Return the output strictly in this JSON format:
        {{
            "answer": "<string>",
            "confidence": <int>
        }}
        """
        try:
            response = model.generate_content(prompt)
            content = response.text.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error answering screening question: {e}")
            return {
                "answer": "I am a motivated fresher with academic project experience matching the requirements.",
                "confidence": 50
            }

    @classmethod
    def parse_job_email(cls, email_subject: str, email_body: str) -> dict:
        """
        Analyze email content to see if it represents a job posting or contains a job application link.
        """
        import re
        model = cls._get_model()
        if not model:
            # Sandbox/Mock Mode: simulate parsing if email subject or body contains job keywords
            logger.info("Using mock Gemini job email parsing (Sandbox Mode)")
            sb_lower = email_subject.lower()
            body_lower = email_body.lower()
            
            # Simple keyword heuristic for sandbox simulation
            is_job = any(k in sb_lower or k in body_lower for k in ["opportunity", "job", "hiring", "careers", "position", "opening", "intern", "developer"])
            
            if is_job:
                # Find some mock apply link in body or generate one
                apply_link = "https://boards.greenhouse.io/mock/jobs/99999"
                # Try to extract a URL from the email body if any is present
                urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', email_body)
                if urls:
                    for url in urls:
                        if any(dom in url for dom in ["greenhouse", "lever", "ashby", "linkedin", "apply"]):
                            apply_link = url
                            break
                    else:
                        apply_link = urls[0]
                
                # Guess company
                company = "MockCompany"
                at_match = re.search(r'\bat\s+([A-Z][a-zA-Z0-9]+)\b', email_subject + " " + email_body)
                if at_match:
                    company = at_match.group(1)
                else:
                    for word in (email_subject + " " + email_body).split():
                        word_clean = word.strip(".,;:!?()\"'")
                        if word_clean.istitle() and word_clean.lower() not in ["job", "hiring", "careers", "opportunity", "opening", "dear", "hello", "hi", "subject", "email", "body", "intern", "developer", "urgent"]:
                            company = word_clean
                            break
                        
                return {
                    "is_job_opportunity": True,
                    "company_name": company,
                    "job_title": "Software Engineer (Email)",
                    "location": "Remote",
                    "apply_link": apply_link,
                    "description": "Discovered from email: " + email_subject[:100]
                }
            return {"is_job_opportunity": False}

        prompt = f"""
        Analyze the following email subject and body to see if it represents a job opening, job opportunity, or contains a direct link to apply for a job.

        Email Subject: {email_subject}
        Email Body:
        {email_body}

        Determine if this is a job opportunity email. If yes, extract the company name, job title, location, direct apply link (look for URLs like greenhouse.io, lever.co, ashbyhq.com, linkedin.com/jobs, indeed.com, etc.), and a short description.
        If multiple links are present, select the one that is the direct application form or careers link.

        Return the result STRICTLY in JSON format with these keys:
        {{
            "is_job_opportunity": true/false,
            "company_name": "<string or null>",
            "job_title": "<string or null>",
            "location": "<string or null>",
            "apply_link": "<string or null>",
            "description": "<string or null>"
        }}

        Ensure the output is valid JSON and nothing else.
        """
        try:
            response = model.generate_content(prompt)
            content = response.text.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error during Gemini email job parsing: {e}")
            return {"is_job_opportunity": False}

