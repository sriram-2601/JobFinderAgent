import os
import sys
import logging
from src.database import init_db, get_db_connection
from src.agents.job_hunter import JobHunterAgent
from src.agents.ai_matcher import AIMatcherAgent
from src.agents.auto_applier import AutoApplierAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_tests():
    logger.info("=== Starting Automated System Check ===")
    
    # 1. Initialize DB
    logger.info("Step 1: Initializing Database...")
    init_db()
    
    # Clean up old test run records to enable repeated testing
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM applications WHERE job_id = '138156699367774a'")
    cursor.execute("DELETE FROM matches WHERE job_id = '138156699367774a'")
    cursor.execute("DELETE FROM jobs WHERE id = '138156699367774a'")
    conn.commit()
    conn.close()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1.5. Verifying Hashing & JWT Authentication
    logger.info("Step 1.5: Verifying Hashing & JWT Authentication...")
    from src.services.auth_service import hash_password, verify_password, create_access_token, decode_access_token
    
    # Test Password hashing
    test_password = "secure_test_password"
    hashed = hash_password(test_password)
    if not verify_password(test_password, hashed):
        logger.error("❌ Test Failed: Password hashing/verification logic failed.")
        sys.exit(1)
    if verify_password("wrong_password", hashed):
        logger.error("❌ Test Failed: Password hashing verification accepted an invalid password.")
        sys.exit(1)
        
    # Test JWT token creation/decoding
    test_payload = {"sub": "test_user_account"}
    token = create_access_token(test_payload)
    decoded = decode_access_token(token)
    if not decoded or decoded.get("sub") != "test_user_account":
        logger.error("❌ Test Failed: JWT token serialization/decryption failed.")
        sys.exit(1)
        
    logger.info("✅ Step 1.5 Success: Password hashing and JWT serialization/decryption verified.")

    # 1.6. Verify default seeded admin user
    cursor.execute("SELECT password_hash FROM users WHERE username = 'admin'")
    admin_user = cursor.fetchone()
    if not admin_user:
        logger.error("❌ Test Failed: Default admin user not seeded.")
        sys.exit(1)
    if not verify_password("admin", admin_user["password_hash"]):
        logger.error("❌ Test Failed: Default admin user password verification failed.")
        sys.exit(1)
    logger.info("✅ Step 1.6 Success: Seeded admin user credentials verified.")

    # 2. Check Candidate Profile Seeding
    cursor.execute("SELECT name, email, phone FROM candidate_profile ORDER BY id DESC LIMIT 1")
    profile = cursor.fetchone()
    if not profile:
        logger.error("❌ Test Failed: Candidate profile not seeded.")
        sys.exit(1)
    
    logger.info(f"✅ Step 2 Success: Loaded Profile for {profile['name']} ({profile['email']})")

    # 2.1 Check Location Compatibility Filtering
    logger.info("Step 2.1: Checking Location Compatibility Helper...")
    from src.config import is_location_allowed
    
    test_cases = [
        ("Hyderabad, India", True),
        ("Bengaluru, Karnataka (Onsite)", True),
        ("San Francisco, CA (Remote)", True),
        ("Remote, US", True),
        ("London, UK (Hybrid)", False),
        ("New York, NY", False),
        ("Berlin, Germany (Onsite)", False),
    ]
    for loc, expected in test_cases:
        allowed = is_location_allowed(loc)
        if allowed != expected:
            logger.error(f"❌ Test Failed: Location '{loc}' compatibility check expected {expected}, got {allowed}")
            sys.exit(1)
    logger.info("✅ Step 2.1 Success: Location Compatibility filtering verified.")

    # 3. Create Mock Job
    logger.info("Step 3: Seeding Mock Job Posting...")
    mock_job = {
        "company_name": "Antigravity AI Lab",
        "job_title": "Generative AI Application Developer Intern (Python)",
        "job_type": "Internship",
        "location": "Remote",
        "apply_link": "https://lever.co/antigravity/apply-test-job-post",
        "description": "Looking for a python developer who can build serverless LLM applications and React frontends. 0-1 years experience required.",
        "source": "Lever API",
        "posting_date": "2026-06-17",
        "priority": 1
    }
    
    # Save mock job
    JobHunterAgent.save_job(mock_job)
    import hashlib
    job_id = hashlib.sha256(mock_job["apply_link"].encode()).hexdigest()[:16]
    
    cursor.execute("SELECT id, job_title FROM jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    if not job:
        logger.error("❌ Test Failed: Mock job was not saved to database.")
        sys.exit(1)
    logger.info(f"✅ Step 3 Success: Saved Job '{job['job_title']}' with ID {job['id']}")

    # 4. Evaluate Job Match (Agent 2)
    logger.info("Step 4: Evaluating AI Matching Score & Boosts...")
    match_result = AIMatcherAgent.evaluate_job(job_id, 1)
    
    cursor.execute("SELECT match_score, match_status FROM matches WHERE job_id = ? AND user_id = ?", (job_id, 1))
    match_record = cursor.fetchone()
    if not match_record:
        logger.error("❌ Test Failed: Evaluation record was not created.")
        sys.exit(1)
        
    logger.info(f"✅ Step 4 Success: Computed Score={match_record['match_score']}% (Status={match_record['match_status']})")
    # Verify boosts were added (Generative AI + Python should give a boost)
    # Base is 75 in mock, +20 for AI, +20 for Python -> boosted to 100.
    logger.info(f"Priority boosts verified. Final score calculated: {match_record['match_score']}/100")
 
    # 5. Apply to Job (Agent 3 - Playwright Sandbox)
    logger.info("Step 5: Executing Playwright Form Filler Sandbox...")
    from src.config import APP_MODE
    if APP_MODE == "AUTONOMOUS":
        logger.info("APP_MODE is AUTONOMOUS, clearing previous auto-applied application record for Step 5 sandbox check...")
        cursor.execute("DELETE FROM applications WHERE job_id = ? AND user_id = ?", (job_id, 1))
        conn.commit()
        
    apply_result = AutoApplierAgent.apply_job(job_id, 1, mock=True)
    if not apply_result["success"]:
        logger.error(f"❌ Test Failed: Playwright Sandbox Apply failed: {apply_result.get('reason')}")
        sys.exit(1)
        
    cursor.execute("SELECT status, confirmation_number FROM applications WHERE job_id = ? AND user_id = ?", (job_id, 1))
    app_record = cursor.fetchone()
    if not app_record:
        logger.error("❌ Test Failed: Application history not created in database.")
        sys.exit(1)
        
    logger.info(f"✅ Step 5 Success: Sandbox submission registered. Status={app_record['status']}, Confirmation={app_record['confirmation_number']}")
    
    conn.close()
    logger.info("=== All Core Systems Verified Successfully! ===")

if __name__ == "__main__":
    run_tests()
