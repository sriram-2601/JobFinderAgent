import os
from pathlib import Path
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

if os.getenv("VERCEL"):
    DATA_DIR = Path("/tmp")
else:
    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

# Ensure subdirectories exist
(DATA_DIR / "screenshots").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "logs").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "resumes").mkdir(parents=True, exist_ok=True)

# Application Configuration
APP_MODE = os.getenv("APP_MODE", "APPROVAL")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/jobfinder.db")
JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_jwt_key_for_job_hunter_dashboard_development_12345")

# API Keys and External Credentials
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# Email Settings
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "sriramnbv26@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USERNAME = os.getenv("IMAP_USERNAME", "sriramnbv26@gmail.com")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")

# Telegram Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Encryption configuration for securing passwords in database
_key = os.getenv("ENCRYPTION_KEY", "")
if not _key:
    # Fallback to a stable derived key if not specified
    _key = Fernet.generate_key().decode()
    # We print a warning, but in production they should specify one
ENCRYPTION_KEY = _key.encode() if isinstance(_key, str) else _key
cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_value(value: str) -> str:
    """Encrypt a sensitive string (e.g. SMTP passwords or custom API tokens)"""
    if not value:
        return ""
    return cipher_suite.encrypt(value.encode()).decode()

def decrypt_value(encrypted_value: str) -> str:
    """Decrypt an encrypted string"""
    if not encrypted_value:
        return ""
    try:
        return cipher_suite.decrypt(encrypted_value.encode()).decode()
    except Exception:
        return "[Decryption Failed]"

# Priority boosts configurations as outlined in system rules
PRIORITY_BOOSTS = {
    "AI": 20,
    "Python": 20,
    "Data": 15,
    "Full Stack": 15,
    "React": 10,
    "Node": 10,
    "Cloud": 10,
    "Testing": 10,
    "IT Support": 10,
    "General Developer": 15
}

def is_location_allowed(location: str) -> bool:
    """
    Check if a job location is allowed based on:
    - If in India: Onsite, Hybrid, and Remote are all allowed.
    - If outside India: Only Remote is allowed (candidate cannot travel to another country).
    """
    if not location:
        return True
        
    loc_lower = location.lower()
    
    # 1. Determine if the location explicitly mentions India or Indian cities/states
    indian_keywords = [
        "india", "bengaluru", "bangalore", "hyderabad", "mumbai", "pune", "delhi", 
        "gurgaon", "noida", "chennai", "kolkata", "ahmedabad", "jaipur", "karnataka", 
        "telangana", "maharashtra", "haryana", "tamil nadu", "gurugram"
    ]
    is_in_india = any(kw in loc_lower for kw in indian_keywords)
    
    # 2. Determine if the location is remote
    remote_keywords = ["remote", "work from home", "wfh", "anywhere", "telecommute"]
    is_remote = any(kw in loc_lower for kw in remote_keywords)
    
    if is_in_india:
        # Both remote, hybrid, and onsite are good in India
        return True
        
    if is_remote:
        # Remote work is always allowed even if it is outside India
        return True
        
    # If it is not in India and not remote, it requires relocation to another country, which is not allowed.
    return False

