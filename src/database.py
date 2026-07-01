import sqlite3
import json
from datetime import datetime
from src.config import DATABASE_URL

def get_db_connection():
    """Establish a connection to the SQLite database"""
    # Parse file path from sqlite:///data/jobfinder.db
    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables and inject the candidate profile if empty"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Candidate Profile Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidate_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        linkedin TEXT,
        github TEXT,
        portfolio TEXT,
        skills TEXT,       -- comma separated
        education TEXT,    -- JSON list
        certifications TEXT, -- JSON list
        projects TEXT,     -- JSON list
        achievements TEXT, -- JSON list
        experience TEXT,   -- summary or JSON list
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Jobs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, -- SHA256 of apply_link / unique crawler key
        company_name TEXT,
        job_title TEXT,
        job_type TEXT, -- Full-Time, Internship, etc.
        location TEXT,
        salary TEXT,
        apply_link TEXT UNIQUE,
        description TEXT,
        skills TEXT, -- Comma separated required skills
        experience_required REAL, -- years
        posting_date TEXT,
        source TEXT, -- LinkedIn, Indeed, Greenhouse, etc.
        priority INTEGER, -- 1 to 4
        active BOOLEAN DEFAULT 1,
        discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. Matches Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT,
        match_score INTEGER,
        missing_skills TEXT, -- comma separated
        rank_relevance TEXT,
        optimize_suggestions TEXT,
        cover_letter TEXT,
        screening_qa TEXT, -- JSON structure
        match_status TEXT, -- REJECTED, PENDING_REVIEW, APPROVED
        evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    )
    """)

    # 4. Applications Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        mode TEXT, -- APPROVAL, AUTONOMOUS
        status TEXT, -- APPLIED, OA_RECEIVED, INTERVIEW_SCHEDULED, REJECTED, OFFER_RECEIVED
        confirmation_number TEXT,
        screenshot_path TEXT,
        log_path TEXT,
        response_message TEXT,
        email_confirmation_subject TEXT,
        email_confirmation_sender TEXT,
        email_confirmation_date TEXT,
        email_confirmation_snippet TEXT,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    )
    """)

    # 4.1 Migration: Ensure applications table has columns
    for col in ["response_message", "email_confirmation_subject", "email_confirmation_sender", "email_confirmation_date", "email_confirmation_snippet"]:
        try:
            cursor.execute(f"ALTER TABLE applications ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass

    # 4.2 Migration: Ensure candidate_profile table has resume_path column
    try:
        cursor.execute("ALTER TABLE candidate_profile ADD COLUMN resume_path TEXT")
    except sqlite3.OperationalError:
        pass

    # 5. Notifications Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT,
        channel TEXT, -- EMAIL, TELEGRAM
        type TEXT, -- INSTANT, DAILY, WEEKLY, MONTHLY
        content TEXT,
        status TEXT, -- SENT, FAILED
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    )
    """)

    # 6. Referrals Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT,
        contact_name TEXT,
        contact_title TEXT,
        contact_info TEXT,
        referral_message TEXT,
        recruiter_message TEXT,
        follow_up_message TEXT,
        status TEXT, -- FOUND, CONTACTED, REPLIED, SECURED
        found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    )
    """)

    # 7. Recruiters Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recruiters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT,
        name TEXT,
        title TEXT,
        contact_info TEXT, -- Email, LinkedIn etc.
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 8. Interviews Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER,
        stage TEXT, -- OA, TECHNICAL, HR, BEHAVIORAL
        scheduled_at TEXT, -- ISO Date String
        status TEXT, -- SCHEDULED, COMPLETED, CANCELLED
        notes TEXT,
        FOREIGN KEY(application_id) REFERENCES applications(id)
    )
    """)

    # 9. Skills Gap Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skills_gap (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_name TEXT UNIQUE,
        occurrence_count INTEGER DEFAULT 0,
        in_demand_rank INTEGER,
        missing_in_profile BOOLEAN DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 10. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 11. Migration: Ensure tables have user_id columns for multi-user isolation
    for table in ["candidate_profile", "matches", "applications", "referrals", "interviews"]:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER")
        except sqlite3.OperationalError:
            pass

    # Inject default users if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        from src.services.auth_service import hash_password
        hashed = hash_password("admin")
        
        users_to_seed = [
            ("admin", hashed, "Sriram Venkat", "sriramnbv26@gmail.com"),
            ("narutouzumakhi85@gmail.com", hashed, "naruto uzumakhi", "narutouzumakhi85@gmail.com"),
            ("venkatnbv2000@gmail.com", hashed, "venkat", "venkatnbv2000@gmail.com"),
            ("sunithasd09@gmail.com", hashed, "Mattaparthi Sunitha", "sunithasd09@gmail.com"),
            ("geethamadhuri172008@gmail.com", hashed, "Geetha", "geethamadhuri172008@gmail.com"),
            ("bnithin638@gmail.com", hashed, "Nithin Banothu", "bnithin638@gmail.com")
        ]
        
        for username, password_hash, full_name, email in users_to_seed:
            cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, email)
            VALUES (?, ?, ?, ?)
            """, (username, password_hash, full_name, email))

    # Inject candidate profiles if empty
    cursor.execute("SELECT COUNT(*) FROM candidate_profile")
    if cursor.fetchone()[0] == 0:
        default_skills = "Python, Java, Oops, Html, CSS, JavaScript, React, Node.js, Numpy, Pandas, Deep Learning, TensorFlow, MongoDB, SQL, Data Structures & Algorithms, AWS, GitHub"
        
        default_education = [
            {
                "institution": "Keshav Memorial Institute of Technology, Hyderabad",
                "degree": "Bachelor of Technology in Computer Science Engineering (Data Science)",
                "duration": "2022 - 2026",
                "grade": ""
            },
            {
                "institution": "SriAadya Junior College",
                "degree": "Intermediate MPC",
                "duration": "2020 - 2022",
                "grade": "CGPA: 9.30/10.0"
            },
            {
                "institution": "Janapriya High School",
                "degree": "Secondary School of Education",
                "duration": "2020",
                "grade": "CGPA: 10.0/10.0"
            }
        ]

        default_certifications = [
            {
                "title": "Anthropic Certificate: Model Context Protocol Advanced Topics",
                "link": "https://verify.skilljar.com/c/o3em32xdehg2"
            },
            {
                "title": "Deep Learning Certificate: Attended a Guest Lecture on Deep learning in speech processing",
                "link": ""
            },
            {
                "title": "NextWave Certificate of achievement: Participated in Generative AI Mastery Workshop",
                "link": ""
            }
        ]

        default_projects = [
            {
                "title": "Serverless Machine Learning inference via Model Slicing",
                "date": "Oct 2025",
                "details": [
                    "Built a serverless ML inference system using AWS Lambda, storing models in Amazon S3 and containerizing deployment with Docker.",
                    "Applied model slicing to enable scalable and cost-efficient predictions, useful for real-time applications like recommendation systems and fraud detection."
                ]
            },
            {
                "title": "Sahaya – AI-Chatbot",
                "date": "Dec 2024",
                "details": [
                    "Built a mental health Chatbot using Firebase, Groq API.",
                    "Enhanced Website through a responsive design, improved UI/UX with advanced CSS and JavaScript, and seamless collaboration using Git."
                ]
            },
            {
                "title": "Smart Price Prediction",
                "date": "",
                "details": [
                    "Built a React-based e-commerce web application utilizing Vite and Vercel to dynamically predict optimal pricing based on catalog data.",
                    "Designed a responsive, glassmorphic UI to streamline product feature input (text and images), integrating with a simulated ML backend."
                ]
            }
        ]

        default_achievements = [
            "Project Expo Finalist: Qualified for the KMIT Project Expo (Dec 2025)"
        ]

        default_experience = "Fresher (0 Years Experience). Focuses on full-stack application development, serverless ML deployments, and interactive AI Chatbots."

        # Fetch dynamically
        cursor.execute("SELECT id, username, full_name, email FROM users")
        seeded_users = cursor.fetchall()
        
        for u in seeded_users:
            uid = u["id"]
            uname = u["username"]
            full_name = u["full_name"]
            email = u["email"]
            
            if uname == "admin":
                cursor.execute("""
                INSERT INTO candidate_profile (name, email, phone, linkedin, github, portfolio, skills, education, certifications, projects, achievements, experience, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    "SRIRAM VENKAT MATTAPARTHI", "sriramnbv26@gmail.com", "+91-6305477216",
                    "https://www.linkedin.com/in/ram-s-venkat/", "https://github.com/sriram-2601",
                    "https://portfolio-nine-tan-nr02ujpbgi.vercel.app/", default_skills,
                    json.dumps(default_education), json.dumps(default_certifications),
                    json.dumps(default_projects), json.dumps(default_achievements), default_experience, uid
                ))
            elif "naruto" in uname:
                skills = "Python, Django, Javascript, Node.js, React, Shadow Clone API, Rasengan JS, Git"
                education = [{"institution": "Konoha Ninja Academy", "degree": "Hokage Engineering Degree", "duration": "2020-2024", "grade": "S-Rank"}]
                projects = [{"title": "Konoha Security Shield", "date": "2025", "details": ["Designed real-time intrusion alerts and defensive barrier monitoring using Python and Node.js."]}]
                cursor.execute("""
                INSERT INTO candidate_profile (name, email, phone, linkedin, github, portfolio, skills, education, certifications, projects, achievements, experience, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    full_name, email, "+91-9999999999", "https://linkedin.com/in/naruto", "https://github.com/naruto",
                    "", skills, json.dumps(education), "[]", json.dumps(projects), "[]", "Ninja Software Engineer with S-rank skills", uid
                ))
            elif "venkatnbv2000" in uname:
                skills = "Java, Python, Javascript, React, SQL, HTML, CSS, Spring Boot"
                education = [{"institution": "JNTU Hyderabad", "degree": "B.Tech CSE", "duration": "2018-2022", "grade": "8.5 CGPA"}]
                projects = [{"title": "Inventory Management", "date": "2023", "details": ["Built inventory manager using React and Spring Boot with MySQL."]}]
                cursor.execute("""
                INSERT INTO candidate_profile (name, email, phone, linkedin, github, portfolio, skills, education, certifications, projects, achievements, experience, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    full_name, email, "+91-8888888888", "https://linkedin.com/in/venkat", "https://github.com/venkat",
                    "", skills, json.dumps(education), "[]", json.dumps(projects), "[]", "Full Stack Developer with 2 years of experience", uid
                ))
            elif "sunitha" in uname:
                skills = "Python, SQL, Pandas, NumPy, Tableau, PowerBI, Excel, Data Analysis"
                education = [{"institution": "Osmania University", "degree": "B.Sc Statistics", "duration": "2021-2024", "grade": "9.0 CGPA"}]
                projects = [{"title": "E-Commerce Customer Insights", "date": "2024", "details": ["Analyzed sales records to identify customer demographics using Python and Tableau."]}]
                cursor.execute("""
                INSERT INTO candidate_profile (name, email, phone, linkedin, github, portfolio, skills, education, certifications, projects, achievements, experience, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    full_name, email, "+91-7777777777", "https://linkedin.com/in/sunitha", "",
                    "", skills, json.dumps(education), "[]", json.dumps(projects), "[]", "Data Analyst specializing in statistical modeling and dashboarding", uid
                ))
            elif "geetha" in uname:
                skills = "Python, Selenium, Playwright, PyTest, Automation Testing, QA, Manual Testing, Jenkins"
                education = [{"institution": "CBIT Hyderabad", "degree": "B.Tech IT", "duration": "2020-2024", "grade": "8.2 CGPA"}]
                projects = [{"title": "Test Automation Framework", "date": "2024", "details": ["Designed hybrid test automation framework using Playwright and PyTest."]}]
                cursor.execute("""
                INSERT INTO candidate_profile (name, email, phone, linkedin, github, portfolio, skills, education, certifications, projects, achievements, experience, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    full_name, email, "+91-6666666666", "https://linkedin.com/in/geetha", "",
                    "", skills, json.dumps(education), "[]", json.dumps(projects), "[]", "QA Automation Engineer focused on web app testing", uid
                ))
            elif "bnithin638" in uname:
                skills = "JavaScript, Node.js, Express, MongoDB, SQL, Redis, Docker, Git"
                education = [{"institution": "VNR VJIET", "degree": "B.Tech CSE", "duration": "2021-2025", "grade": "8.8 CGPA"}]
                projects = [{"title": "High Throughput Chat App", "date": "2025", "details": ["Developed real-time chat application using Node.js, Socket.io, and Redis."]}]
                cursor.execute("""
                INSERT INTO candidate_profile (name, email, phone, linkedin, github, portfolio, skills, education, certifications, projects, achievements, experience, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    full_name, email, "+91-5555555555", "https://linkedin.com/in/nithin", "https://github.com/nithin",
                    "", skills, json.dumps(education), "[]", json.dumps(projects), "[]", "Backend Developer interested in distributed systems", uid
                ))

    # Ensure legacy records have correct user_id
    cursor.execute("UPDATE candidate_profile SET user_id = 1 WHERE user_id IS NULL")
    cursor.execute("UPDATE matches SET user_id = 1 WHERE user_id IS NULL")
    cursor.execute("UPDATE applications SET user_id = 1 WHERE user_id IS NULL")
    cursor.execute("UPDATE referrals SET user_id = 1 WHERE user_id IS NULL")
    cursor.execute("UPDATE interviews SET user_id = 1 WHERE user_id IS NULL")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
