import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, APIRouter, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from src.database import get_db_connection, init_db
from src.config import APP_MODE, BASE_DIR
from src.agents.job_hunter import JobHunterAgent
from src.agents.ai_matcher import AIMatcherAgent
from src.agents.auto_applier import AutoApplierAgent
from src.agents.skill_gap_analyzer import SkillGapAnalyzerAgent
from src.agents.interview_tracker import InterviewTrackerAgent
from src.agents.notification_agent import NotificationAgent
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize DB on server start
init_db()

app = FastAPI(title="Autonomous AI Job Search Platform API", version="1.0.0")

# Enable CORS for React dashboard development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount screenshots directory to serve confirmation images
screenshots_dir = os.path.join(str(BASE_DIR), "data", "screenshots")
os.makedirs(screenshots_dir, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=screenshots_dir), name="screenshots")

# Pydantic Schemas
class ProfileUpdate(BaseModel):
    name: str
    email: str
    phone: str
    linkedin: str
    github: str
    portfolio: str
    skills: str
    experience: str

class SettingsUpdate(BaseModel):
    app_mode: str
    gemini_api_key: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None

class InterviewCreate(BaseModel):
    application_id: int
    stage: str
    scheduled_at: str
    notes: Optional[str] = ""

class UserRegister(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = ""
    email: Optional[str] = ""

class UserLogin(BaseModel):
    username: str
    password: str

class GoogleLoginRequest(BaseModel):
    id_token: str

# HTTP Bearer Token security dependency
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    from src.services.auth_service import decode_access_token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Verify user exists in database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, email FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return dict(user)

# ==========================================
# PUBLIC AUTH API ENDPOINTS
# ==========================================

@app.post("/api/auth/register")
def register(user: UserRegister):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")
    
    from src.services.auth_service import hash_password
    hashed = hash_password(user.password)
    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, email)
            VALUES (?, ?, ?, ?)
        """, (user.username, hashed, user.full_name, user.email))
        user_id = cursor.lastrowid
        
        # Create default candidate profile
        cursor.execute("""
            INSERT INTO candidate_profile (name, email, phone, linkedin, github, portfolio, skills, education, certifications, projects, achievements, experience, user_id)
            VALUES (?, ?, '', '', '', '', 'Python, SQL, HTML, CSS, JavaScript, React', '[]', '[]', '[]', '[]', 'Fresher', ?)
        """, (user.full_name or user.username, user.email or "", user_id))
        
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    conn.close()
    return {"message": "User registered successfully"}

@app.post("/api/auth/login")
def login(credentials: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (credentials.username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    from src.services.auth_service import verify_password, create_access_token
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    token = create_access_token({"sub": user["username"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "fullName": user["full_name"],
            "email": user["email"]
        }
    }

@app.get("/api/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "fullName": current_user["fullName"],
        "email": current_user["email"]
    }

@app.get("/api/auth/config")
def get_auth_config():
    from src.config import GOOGLE_CLIENT_ID
    return {
        "google_client_id": GOOGLE_CLIENT_ID
    }

@app.post("/api/auth/google")
async def login_google(payload: GoogleLoginRequest):
    if payload.id_token.startswith("MOCK_GOOGLE_TOKEN_"):
        # Bypass verification for simulated Google flow
        google_email = payload.id_token.replace("MOCK_GOOGLE_TOKEN_", "")
        google_name = "SRIRAM VENKAT MATTAPARTHI"
    else:
        from src.config import GOOGLE_CLIENT_ID
        if not GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Google Authentication is not configured on the backend.")
            
        import jwt
        import httpx
        
        try:
            jwks_url = "https://www.googleapis.com/oauth2/v3/certs"
            jwk_client = jwt.PyJWKClient(jwks_url)
            signing_key = jwk_client.get_signing_key_from_jwt(payload.id_token)
            
            idinfo = jwt.decode(
                payload.id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=GOOGLE_CLIENT_ID,
                issuer="https://accounts.google.com"
            )
        except Exception as e:
            logger.error(f"Google ID Token verification failed: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid Google credentials: {str(e)}")
            
        google_email = idinfo.get("email")
        google_name = idinfo.get("name", "Google User")
    
    if not google_email:
        raise HTTPException(status_code=400, detail="Google login failed: email not shared.")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (google_email,))
    user = cursor.fetchone()
    
    if not user:
        import uuid
        dummy_password_hash = "[Google Auth Account - " + str(uuid.uuid4()) + "]"
        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, email)
                VALUES (?, ?, ?, ?)
            """, (google_email, dummy_password_hash, google_name, google_email))
            user_id = cursor.lastrowid
            
            # Create default candidate profile
            cursor.execute("""
                INSERT INTO candidate_profile (name, email, phone, linkedin, github, portfolio, skills, education, certifications, projects, achievements, experience, user_id)
                VALUES (?, ?, '', '', '', '', 'Python, SQL, HTML, CSS, JavaScript, React', '[]', '[]', '[]', '[]', 'Fresher', ?)
            """, (google_name, google_email, user_id))
            
            conn.commit()
            
            cursor.execute("SELECT * FROM users WHERE username = ?", (google_email,))
            user = cursor.fetchone()
        except Exception as e:
            conn.close()
            raise HTTPException(status_code=500, detail=f"Failed to auto-register Google account: {str(e)}")
            
    conn.close()
    
    from src.services.auth_service import create_access_token
    token = create_access_token({"sub": user["username"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "fullName": user["full_name"],
            "email": user["email"]
        }
    }

# ==========================================
# PROTECTED BUSINESS API ROUTER
# ==========================================
api_router = APIRouter(dependencies=[Depends(get_current_user)])

@api_router.get("/api/profile")
def get_profile(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidate_profile WHERE user_id = ? ORDER BY id DESC LIMIT 1", (current_user["id"],))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Parse education, projects, certifications JSON
    profile = dict(row)
    for col in ["education", "projects", "certifications", "achievements"]:
        if profile.get(col):
            try:
                profile[col] = json.loads(profile[col])
            except Exception:
                pass
    return profile

@api_router.post("/api/profile")
def update_profile(profile: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM candidate_profile WHERE user_id = ?", (current_user["id"],))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
                UPDATE candidate_profile
                SET name=?, email=?, phone=?, linkedin=?, github=?, portfolio=?, skills=?, experience=?
                WHERE user_id=?
            """, (profile.name, profile.email, profile.phone, profile.linkedin, profile.github, profile.portfolio, profile.skills, profile.experience, current_user["id"]))
        else:
            cursor.execute("""
                INSERT INTO candidate_profile (name, email, phone, linkedin, github, portfolio, skills, experience, education, certifications, projects, achievements, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, '[]', '[]', '[]', '[]', ?)
            """, (profile.name, profile.email, profile.phone, profile.linkedin, profile.github, profile.portfolio, profile.skills, profile.experience, current_user["id"]))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    conn.close()
    return {"message": "Profile updated successfully"}

@api_router.post("/api/profile/resume")
async def upload_resume(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    # Enforce file size limit of 10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Read file size
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds the 10MB limit.")
        
    # Validate extension
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".pdf", ".doc", ".docx"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOC, and DOCX are allowed.")
        
    resumes_dir = os.path.join(str(BASE_DIR), "data", "resumes")
    os.makedirs(resumes_dir, exist_ok=True)
    
    # Save the file using user_id to prevent collision
    safe_filename = f"user_{current_user['id']}_resume{ext}"
    dest_path = os.path.join(resumes_dir, safe_filename)
    
    try:
        content = await file.read()
        with open(dest_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")
        
    # Update candidate profile with the resume path
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM candidate_profile WHERE user_id = ?", (current_user["id"],))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
                UPDATE candidate_profile
                SET resume_path = ?
                WHERE user_id = ?
            """, (dest_path, current_user["id"]))
        else:
            # Create a default profile with the resume path
            cursor.execute("""
                INSERT INTO candidate_profile (name, email, phone, linkedin, github, portfolio, skills, experience, education, certifications, projects, achievements, resume_path, user_id)
                VALUES (?, ?, '', '', '', '', '', '', '[]', '[]', '[]', '[]', ?, ?)
            """, (current_user["fullName"] or current_user["username"], current_user["email"] or "", dest_path, current_user["id"]))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    conn.close()
    
    return {"message": "Resume uploaded successfully", "resume_path": dest_path}


@api_router.get("/api/jobs")
def get_jobs(limit: int = 50):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY discovered_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@api_router.get("/api/matches")
def get_matches(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT j.job_title, j.company_name, j.location, j.source, j.apply_link, j.description,
               m.id as match_id, m.job_id, m.match_score, m.match_status, m.missing_skills, m.optimize_suggestions, m.cover_letter
        FROM matches m
        JOIN jobs j ON m.job_id = j.id
        WHERE m.user_id = ?
        ORDER BY m.evaluated_at DESC
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@api_router.get("/api/applications")
def get_applications(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.applied_at, a.mode, a.status, a.confirmation_number, a.screenshot_path, a.response_message,
               a.email_confirmation_subject, a.email_confirmation_sender, a.email_confirmation_date, a.email_confirmation_snippet,
               j.job_title, j.company_name, j.location, j.source, j.apply_link, j.description, m.match_score
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        JOIN matches m ON (j.id = m.job_id AND m.user_id = a.user_id)
        WHERE a.user_id = ?
        ORDER BY a.applied_at DESC
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    
    apps = []
    for r in rows:
        d = dict(r)
        if d.get("screenshot_path"):
            filename = os.path.basename(d["screenshot_path"])
            d["screenshot_url"] = f"/screenshots/{filename}"
        else:
            d["screenshot_url"] = ""
        apps.append(d)
    return apps

@api_router.post("/api/jobs/{job_id}/evaluate")
def evaluate_job(job_id: str, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    background_tasks.add_task(AIMatcherAgent.evaluate_job, job_id, current_user["id"])
    return {"message": "Job evaluation started in background"}

@api_router.post("/api/jobs/{job_id}/apply")
def apply_job(job_id: str, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    background_tasks.add_task(AutoApplierAgent.apply_job, job_id, current_user["id"], True)
    return {"message": "Automated application run started in background"}

@api_router.post("/api/matches/{match_id}/approve")
def approve_match(match_id: int, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE matches SET match_status = 'APPROVED' WHERE id = ? AND user_id = ?", (match_id, current_user["id"]))
    cursor.execute("SELECT job_id FROM matches WHERE id = ? AND user_id = ?", (match_id, current_user["id"]))
    row = cursor.fetchone()
    conn.commit()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Match not found")

    background_tasks.add_task(AutoApplierAgent.apply_job, row["job_id"], current_user["id"], True)
    return {"message": "Match approved and Auto-Apply triggered"}

@api_router.post("/api/matches/{match_id}/reject")
def reject_match(match_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE matches SET match_status = 'REJECTED' WHERE id = ? AND user_id = ?", (match_id, current_user["id"]))
    conn.commit()
    conn.close()
    return {"message": "Match rejected successfully"}

@api_router.get("/api/referrals")
def get_referrals(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, j.job_title, j.company_name 
        FROM referrals r
        JOIN jobs j ON r.job_id = j.id
        WHERE r.user_id = ?
        ORDER BY r.found_at DESC
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@api_router.get("/api/interviews")
def get_interviews(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.*, j.job_title, j.company_name 
        FROM interviews i
        JOIN applications a ON i.application_id = a.id
        JOIN jobs j ON a.job_id = j.id
        WHERE a.user_id = ?
        ORDER BY i.scheduled_at ASC
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@api_router.post("/api/interviews")
def create_interview(item: InterviewCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM applications WHERE id = ? AND user_id = ?", (item.application_id, current_user["id"]))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="Unauthorized application ID")
    try:
        cursor.execute("""
            INSERT INTO interviews (application_id, stage, scheduled_at, status, notes, user_id)
            VALUES (?, ?, ?, 'SCHEDULED', ?, ?)
        """, (item.application_id, item.stage, item.scheduled_at, item.notes, current_user["id"]))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    conn.close()
    return {"message": "Interview scheduled successfully"}

@api_router.get("/api/skills-gap")
def get_skills_gap():
    return SkillGapAnalyzerAgent.analyze_skills_gap()

@api_router.get("/api/analytics")
def get_analytics(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Total Stats
    cursor.execute("SELECT COUNT(*) FROM jobs")
    found = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM applications WHERE user_id = ?", (current_user["id"],))
    applied = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM applications WHERE user_id = ? AND (status='INTERVIEW_SCHEDULED' OR status='OA_RECEIVED')", (current_user["id"],))
    interviews = cursor.fetchone()[0]
 
    # Time-based application stats
    now = datetime.now()
    one_day_ago = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    seven_days_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    thirty_days_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
 
    cursor.execute("SELECT COUNT(*) FROM applications WHERE applied_at >= ? AND user_id = ?", (one_day_ago, current_user["id"]))
    applied_daily = cursor.fetchone()[0]
 
    cursor.execute("SELECT COUNT(*) FROM applications WHERE applied_at >= ? AND user_id = ?", (seven_days_ago, current_user["id"]))
    applied_weekly = cursor.fetchone()[0]
 
    cursor.execute("SELECT COUNT(*) FROM applications WHERE applied_at >= ? AND user_id = ?", (thirty_days_ago, current_user["id"]))
    applied_monthly = cursor.fetchone()[0]
    
    # 2. Daily Applications
    cursor.execute("""
        SELECT date(applied_at) as date, COUNT(*) as count 
        FROM applications 
        WHERE user_id = ?
        GROUP BY date 
        ORDER BY date DESC LIMIT 7
    """, (current_user["id"],))
    daily_apps = [dict(r) for r in cursor.fetchall()]
    
    # 3. Match Scores distributions
    cursor.execute("SELECT match_score FROM matches WHERE user_id = ?", (current_user["id"],))
    scores = [r[0] for r in cursor.fetchall()]
    
    # 4. Top Job Sources
    cursor.execute("SELECT source, COUNT(*) as count FROM jobs GROUP BY source ORDER BY count DESC LIMIT 5")
    sources = [dict(r) for r in cursor.fetchall()]
    
    # 5. Top Roles
    cursor.execute("""
        SELECT 
            CASE 
                WHEN job_title LIKE '%AI%' OR job_title LIKE '%LLM%' OR job_title LIKE '%Machine Learning%' THEN 'AI & ML'
                WHEN job_title LIKE '%Python%' OR job_title LIKE '%Backend%' THEN 'Backend'
                WHEN job_title LIKE '%React%' OR job_title LIKE '%Frontend%' OR job_title LIKE '%UI%' THEN 'Frontend'
                WHEN job_title LIKE '%Full Stack%' OR job_title LIKE '%FullStack%' THEN 'Full Stack'
                ELSE 'General Software Engineering'
            END as category,
            COUNT(*) as count
        FROM jobs
        GROUP BY category
        ORDER BY count DESC
    """)
    roles = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
 
    return {
        "summary": {
            "jobs_found": found,
            "jobs_applied": applied,
            "interview_requests": interviews,
            "response_rate": round((interviews / applied * 100), 2) if applied > 0 else 0.0,
            "applied_daily": applied_daily,
            "applied_weekly": applied_weekly,
            "applied_monthly": applied_monthly
        },
        "daily_applications": daily_apps,
        "match_scores": scores,
        "top_sources": sources,
        "top_roles": roles
    }

@api_router.get("/api/settings")
def get_settings():
    from src.config import GOOGLE_CLIENT_ID
    return {
        "app_mode": APP_MODE,
        "smtp_username": os.getenv("SMTP_USERNAME", "sriramnbv26@gmail.com"),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        "google_client_id": GOOGLE_CLIENT_ID
    }

@api_router.post("/api/settings")
def update_settings(settings: SettingsUpdate):
    os.environ["APP_MODE"] = settings.app_mode
    logger.info(f"App settings updated. Mode set to: {settings.app_mode}")
    return {"message": "Settings updated in memory successfully"}

@api_router.post("/api/trigger-search")
def trigger_search(background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Manually trigger job hunting search"""
    uid = current_user["id"]
    def task():
        fresh = JobHunterAgent.run_discovery_pipeline()
        for f in fresh:
            unique_id = hashlib.sha256(f["apply_link"].encode()).hexdigest()[:16]
            AIMatcherAgent.evaluate_job(unique_id, uid)
            
    background_tasks.add_task(task)
    return {"message": "Job discovery and AI Matcher pipeline started in background"}

@api_router.post("/api/trigger-inbox-scan")
def trigger_inbox_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(InterviewTrackerAgent.track_inbox_updates)
    return {"message": "Inbox scan for interview updates started in background"}

@api_router.post("/api/trigger-email-job-scan")
def trigger_email_job_scan(background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Trigger job hunting specifically from emails in the background"""
    uid = current_user["id"]
    def task():
        email_jobs = JobHunterAgent.discover_email_jobs()
        fresh = []
        for job in email_jobs:
            if JobHunterAgent.save_job(job):
                fresh.append(job)
                unique_id = hashlib.sha256(job["apply_link"].encode()).hexdigest()[:16]
                AIMatcherAgent.evaluate_job(unique_id, uid)
        logger.info(f"Manual Job Email scan completed. Discovered {len(email_jobs)} jobs, saved {len(fresh)} new.")
        
    background_tasks.add_task(task)
    return {"message": "Email job scan initiated in the background"}

# Register the router on the main app
app.include_router(api_router)

# Initialize background scheduler
scheduler = BackgroundScheduler()

def scheduled_job_discovery():
    logger.info("Scheduler: Triggering automated job discovery pipeline...")
    try:
        fresh = JobHunterAgent.run_discovery_pipeline()
        if not fresh:
            return
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users")
        users = cursor.fetchall()
        conn.close()
        
        for f in fresh:
            unique_id = hashlib.sha256(f["apply_link"].encode()).hexdigest()[:16]
            for user in users:
                AIMatcherAgent.evaluate_job(unique_id, user["id"])
    except Exception as e:
        logger.error(f"Error in automated job discovery scheduler: {e}")

# Run job discovery every 1 hour (3600 seconds)
scheduler.add_job(scheduled_job_discovery, 'interval', hours=1, id='job_discovery_job')

# Schedule daily summaries at 10 PM
scheduler.add_job(NotificationAgent.generate_daily_summary, 'cron', hour=22, minute=0, id='daily_summary_job')
# Schedule weekly summaries on Sunday at 10 PM
scheduler.add_job(NotificationAgent.generate_weekly_summary, 'cron', day_of_week='sun', hour=22, minute=0, id='weekly_summary_job')
# Schedule monthly summaries on 1st day of month at 9 AM
scheduler.add_job(NotificationAgent.generate_monthly_summary, 'cron', day=1, hour=9, minute=0, id='monthly_summary_job')

# Start the scheduler on FastAPI startup
@app.on_event("startup")
def start_scheduler():
    logger.info("Starting background scheduler...")
    scheduler.start()

@app.on_event("shutdown")
def stop_scheduler():
    logger.info("Stopping background scheduler...")
    scheduler.shutdown()

# Serve static frontend files
from fastapi.responses import FileResponse

dist_path = os.path.join(str(BASE_DIR), "frontend", "dist")
if os.path.exists(dist_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")

    @app.get("/{catchall:path}")
    async def serve_react_app(catchall: str):
        # Exclude API endpoints and screenshots from catchall routing
        if catchall.startswith("api") or catchall.startswith("screenshots"):
            raise HTTPException(status_code=404)
        return FileResponse(os.path.join(dist_path, "index.html"))

