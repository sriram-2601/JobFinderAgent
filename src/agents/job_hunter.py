import hashlib
import logging
import re
import time
import urllib.parse
from datetime import datetime, timedelta
import feedparser
import httpx
from bs4 import BeautifulSoup
from src.database import get_db_connection
from src.config import is_location_allowed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of tech startup company board tokens for direct API checks
Greenhouse_Companies = ["vercel", "openai", "pinecone", "retool", "figma", "stripe", "langchain", "anthropic", "clerk", "datadog", "grammarly", "hashicorp", "sentry", "gitlab", "postman", "docker", "elastic", "mongodb", "confluent", "snowflake", "databricks", "salesforce", "hubspot", "zoom", "slack", "asana", "miro", "notion", "airtable", "linear", "replit", "github", "warp", "sourcegraph", "dbtlabs", "cockroachlabs", "temporal", "resend", "dub", "inflection", "adept", "mistral", "cohere", "huggingface", "runway", "synthesia", "elevenlabs", "midjourney", "stabilityai"]
Lever_Companies = ["lever", "vercel", "figma", "cockroachlabs", "notion", "github", "sourcegraph", "dbtlabs", "replit", "linear", "warp", "temporal", "resend", "dub", "cohere", "huggingface", "runway"]

class JobHunterAgent:
    @staticmethod
    def calculate_priority(post_date_str: str) -> int:
        """
        Calculate priority based on posting date:
        Priority 1: Within last 1 hour
        Priority 2: Within last 24 hours
        Priority 3: Within last 3 days
        Priority 4: Within last 7 days
        Ignore: > 14 days
        """
        try:
            # Parse standard dates or return default priority if not parsable
            post_date = datetime.strptime(post_date_str, "%Y-%m-%d")
            diff = datetime.now() - post_date
            if diff <= timedelta(hours=1):
                return 1
            elif diff <= timedelta(days=1):
                return 2
            elif diff <= timedelta(days=3):
                return 3
            elif diff <= timedelta(days=7):
                return 4
            else:
                return 5  # To be ignored
        except Exception:
            # Default to Priority 2 (last 24 hours) for fresh discoverability
            return 2

    @classmethod
    def filter_job(cls, title: str, description: str) -> bool:
        """
        Check if job is entry level / fresher IT and does not require senior experience.
        """
        title_lower = title.lower()
        desc_lower = description.lower() if description else ""

        # Exclusions: Reject senior roles
        exclude_keywords = ["senior", "lead", "principal", "architect", "manager", "director", "staff", "sr."]
        if any(kw in title_lower for kw in exclude_keywords):
            return False

        # Target IT Roles checklist
        target_roles = [
            "developer", "engineer", "sde", "intern", "programmer", "analyst", 
            "qa", "tester", "support", "cloud", "devops", "security", "database", "sql"
        ]
        if not any(tr in title_lower for tr in target_roles):
            return False

        # Experience filters: Ignore roles explicitly requiring 2+ years of experience
        exp_match = re.search(r"(\d+)\+?\s*(?:years|yrs)\b", desc_lower)
        if exp_match:
            try:
                years = int(exp_match.group(1))
                if years > 2:
                    return False
            except ValueError:
                pass

        return True

    @classmethod
    def save_job(cls, job: dict) -> bool:
        """Save job to DB, returns True if it's a new job (not a duplicate)"""
        # Create a unique ID using hash of the apply link
        unique_id = hashlib.sha256(job["apply_link"].encode()).hexdigest()[:16]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id FROM jobs WHERE id = ?", (unique_id,))
            exists = cursor.fetchone()
            if exists:
                conn.close()
                return False  # Already exists (duplicate)

            cursor.execute("""
            INSERT INTO jobs (id, company_name, job_title, job_type, location, salary, apply_link, description, skills, experience_required, posting_date, source, priority, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                unique_id,
                job["company_name"],
                job["job_title"],
                job.get("job_type", "Full-Time"),
                job["location"],
                job.get("salary", "Not Specified"),
                job["apply_link"],
                job["description"],
                job.get("skills", ""),
                job.get("experience_required", 0.0),
                job.get("posting_date", datetime.now().strftime("%Y-%m-%d")),
                job["source"],
                job.get("priority", 2),
            ))
            conn.commit()
            conn.close()
            logger.info(f"New job discovered: {job['job_title']} at {job['company_name']}")
            return True
        except Exception as e:
            logger.error(f"Error saving job: {e}")
            conn.close()
            return False

    @classmethod
    def discover_greenhouse_jobs(cls) -> list:
        """Fetch jobs from public greenhouse API for configured company tokens"""
        jobs = []
        for company in Greenhouse_Companies:
            url = f"https://api.greenhouse.io/v1/boards/{company}/jobs?content=true"
            try:
                resp = httpx.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    postings = data.get("jobs", [])
                    for post in postings:
                        title = post.get("title", "")
                        desc = post.get("content", "")
                        # Simple HTML cleaner
                        clean_desc = BeautifulSoup(desc, "html.parser").get_text()
                        
                        location = post.get("location", {}).get("name", "Remote")
                        if not is_location_allowed(location):
                            continue
                        
                        if cls.filter_job(title, clean_desc):
                            apply_link = post.get("absolute_url", "")
                            
                            jobs.append({
                                "company_name": company.capitalize(),
                                "job_title": title,
                                "job_type": "Full-Time",
                                "location": location,
                                "apply_link": apply_link,
                                "description": clean_desc[:1000] + "...", # truncate descriptive text for db storage
                                "source": "Greenhouse API",
                                "posting_date": datetime.now().strftime("%Y-%m-%d"),
                                "priority": 2
                            })
            except Exception as e:
                logger.error(f"Error fetching greenhouse jobs for {company}: {e}")
        return jobs

    @classmethod
    def discover_lever_jobs(cls) -> list:
        """Fetch jobs from public Lever API for company tokens"""
        jobs = []
        for company in Lever_Companies:
            url = f"https://api.lever.co/v0/postings/{company}"
            try:
                resp = httpx.get(url, timeout=10)
                if resp.status_code == 200:
                    postings = resp.json()
                    for post in postings:
                        title = post.get("title", "")
                        desc = post.get("description", "") + " " + post.get("descriptionHtml", "")
                        clean_desc = BeautifulSoup(desc, "html.parser").get_text()
                        
                        location = post.get("categories", {}).get("location", "Remote")
                        if not is_location_allowed(location):
                            continue
                        
                        if cls.filter_job(title, clean_desc):
                            apply_link = post.get("applyUrl", "")
                            
                            jobs.append({
                                "company_name": company.capitalize(),
                                "job_title": title,
                                "job_type": post.get("categories", {}).get("commitment", "Full-Time"),
                                "location": location,
                                "apply_link": apply_link,
                                "description": clean_desc[:1000] + "...",
                                "source": "Lever API",
                                "posting_date": datetime.now().strftime("%Y-%m-%d"),
                                "priority": 2
                            })
            except Exception as e:
                logger.error(f"Error fetching lever jobs for {company}: {e}")
        return jobs

    @classmethod
    def discover_rss_jobs(cls) -> list:
        """Crawl open Y Combinator and job RSS feeds"""
        jobs = []
        rss_feeds = [
            ("https://news.ycombinator.com/jobsrss", "YC Jobs RSS"),
            ("https://remoteok.com/remote-jobs.rss", "RemoteOK RSS"),
            ("https://www.workingnomads.com/jobs/feed", "WorkingNomads RSS")
        ]
        for url, source in rss_feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    title = entry.get("title", "")
                    description = entry.get("description", "")
                    clean_desc = BeautifulSoup(description, "html.parser").get_text()
                    
                    # Guess location for YC RSS or other feeds
                    location = "Remote"
                    if source == "YC Jobs RSS":
                        loc_match = re.search(r"\(([^)]+)\)", title)
                        if loc_match:
                            location = loc_match.group(1)
                        else:
                            if "remote" in title.lower() or "remote" in clean_desc.lower():
                                location = "Remote"
                            else:
                                location = "USA"

                    if not is_location_allowed(location):
                        continue

                    if cls.filter_job(title, clean_desc):
                        apply_link = entry.get("link", "")
                        
                        # Guess company from title "Company Name is hiring a Job Title" or "Job Title at Company Name"
                        company = "Unknown"
                        if "is hiring" in title:
                            company = title.split("is hiring")[0].strip()
                        elif " at " in title:
                            company = title.split(" at ")[-1].strip()
                            
                        jobs.append({
                            "company_name": company,
                            "job_title": title,
                            "job_type": "Full-Time",
                            "location": location,
                            "apply_link": apply_link,
                            "description": clean_desc[:1000] + "...",
                            "source": source,
                            "posting_date": datetime.now().strftime("%Y-%m-%d"),
                            "priority": 2
                        })
            except Exception as e:
                logger.error(f"Error parsing RSS {url}: {e}")
        return jobs

    @classmethod
    def discover_search_jobs(cls) -> list:
        """Query DuckDuckGo search for junior positions on multiple job portals (Free scraping method)"""
        jobs = []
        queries = [
            "site:linkedin.com/jobs/view \"software engineer\" India",
            "site:linkedin.com/jobs/view \"python developer\" remote",
            "site:linkedin.com/jobs/view \"software developer intern\" Hyderabad",
            "site:linkedin.com/jobs/view \"associate software engineer\" Bangalore",
            "site:linkedin.com/jobs/view \"fresher developer\"",
            "site:linkedin.com/jobs/view \"data analyst intern\" remote",
            "site:linkedin.com/jobs/view \"react developer intern\" India",
            "site:greenhouse.io \"software engineer intern\" Hyderabad",
            "site:lever.co \"associate software engineer\" remote",
            "site:ashbyhq.com \"python developer\" fresher",
            "site:smartrecruiters.com \"software developer\" entry level",
            "site:careers.google.com \"software engineer\" associate",
            "site:naukri.com/job-listings \"software engineer intern\"",
            "site:indeed.com/rc/clk \"junior developer\"",
            "site:linkedin.com/jobs/view \"associate software engineer\"",
            "site:upwork.com/jobs \"frontend developer\" entry",
            "site:lever.co \"software engineer intern\" remote",
            "site:greenhouse.io \"react developer\" remote",
            "site:ashbyhq.com \"backend engineer intern\" remote",
            "site:lever.co \"intern\" India",
            "site:wellfound.com \"software engineer intern\" remote",
            "site:weworkremotely.com \"junior developer\"",
            "site:remote.co \"junior developer\"",
            "site:glassdoor.com/Job \"software developer\" fresher remote",
            "site:simplyhired.com \"junior programmer\" remote",
            "site:ziprecruiter.com \"junior software engineer\""
        ]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        
        for query in queries:
            encoded_query = urllib.parse.quote_plus(query)
            # Fetch DDG HTML search
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            try:
                resp = httpx.get(url, headers=headers, timeout=15)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    links = soup.find_all("a", class_="result__snippet")
                    for link_tag in links:
                        # Extract target URL
                        href = link_tag.get("href", "")
                        parsed_url = urllib.parse.urlparse(href)
                        query_params = urllib.parse.parse_qs(parsed_url.query)
                        actual_url = query_params.get("uddg", [None])[0]
                        
                        if actual_url:
                            allowed_domains = [
                                "greenhouse.io", "lever.co", "ashbyhq.com", "smartrecruiters.com", 
                                "linkedin.com", "indeed.com", "naukri.com", "upwork.com", "careers.google.com",
                                "wellfound.com", "glassdoor.com", "simplyhired.com", "ziprecruiter.com",
                                "remote.co", "weworkremotely.com"
                            ]
                            if any(dom in actual_url.lower() for dom in allowed_domains):
                                title_tag = link_tag.find_previous("a", class_="result__url")
                                title = title_tag.get_text() if title_tag else "Entry Level IT Role"
                                snippet = link_tag.get_text()
                                
                                company = "Unknown"
                                # Attempt company name extraction from link e.g. greenhouse.io/company
                                path_parts = actual_url.split("/")
                                if len(path_parts) > 3:
                                    company = path_parts[3].capitalize()
                                
                                # Set correct crawler source tag
                                source_tag = "DDG Crawl ("
                                for dom in allowed_domains:
                                    if dom in actual_url.lower():
                                        source_tag += dom.split(".")[0].capitalize()
                                        break
                                source_tag += ")"

                                # Guess location from query, title, or snippet
                                location = "Remote"
                                if "hyderabad" in query.lower() or "hyderabad" in (title + " " + snippet).lower():
                                    location = "Hyderabad, India"
                                elif "bangalore" in (title + " " + snippet).lower() or "bengaluru" in (title + " " + snippet).lower():
                                    location = "Bengaluru, India"
                                elif "india" in (title + " " + snippet).lower():
                                    location = "India"
                                elif "remote" in (title + " " + snippet).lower() or "remote" in query.lower():
                                    location = "Remote"
                                elif any(kw in (title + " " + snippet).lower() for kw in ["san francisco", "new york", "london", "seattle", "austin", "boston", "chicago", "canada", "united states", "uk", "us"]):
                                    location = "International (Onsite)"
                                
                                if not is_location_allowed(location):
                                    continue

                                jobs.append({
                                    "company_name": company,
                                    "job_title": title,
                                    "job_type": "Full-Time",
                                    "location": location,
                                    "apply_link": actual_url,
                                    "description": snippet,
                                    "source": source_tag,
                                    "posting_date": datetime.now().strftime("%Y-%m-%d"),
                                    "priority": 1
                                })
                time.sleep(1) # politely throttle DDG crawls
            except Exception as e:
                logger.error(f"Error executing DuckDuckGo job search for query '{query}': {e}")
        return jobs

    @classmethod
    def discover_email_jobs(cls) -> list:
        """Scan email inbox for job opportunities and filter them"""
        from src.services.email_service import EmailService
        email_jobs = EmailService.scan_inbox_for_jobs()
        filtered = []
        for job in email_jobs:
            if cls.filter_job(job["job_title"], job["description"]):
                filtered.append(job)
        return filtered

    @classmethod
    def run_discovery_pipeline(cls) -> list:
        """Run all discoverers, filter, check duplicates, save to DB, and return list of fresh discoveries"""
        logger.info("Executing Job Discovery Pipeline...")
        
        all_jobs = []
        all_jobs.extend(cls.discover_greenhouse_jobs())
        all_jobs.extend(cls.discover_lever_jobs())
        all_jobs.extend(cls.discover_rss_jobs())
        all_jobs.extend(cls.discover_search_jobs())
        all_jobs.extend(cls.discover_email_jobs())
        
        fresh_jobs = []
        for job in all_jobs:
            if cls.save_job(job):
                fresh_jobs.append(job)
                
        logger.info(f"Discovery Pipeline Finished. Discovered {len(all_jobs)} jobs. Saved {len(fresh_jobs)} new entries.")
        return fresh_jobs

