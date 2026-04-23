import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# --- External Job Board API Keys ---
# Adzuna: https://developer.adzuna.com  (free tier: 250 req/month)
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
ADZUNA_COUNTRY = os.getenv("ADZUNA_COUNTRY", "in")  # in=India, us=USA, gb=UK, ca=Canada, au=Australia

# JSearch via RapidAPI: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
# Aggregates: Indeed, LinkedIn, Glassdoor, Naukri, Wellfound, Handshake, ZipRecruiter
JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY", "")
JSEARCH_COUNTRY = os.getenv("JSEARCH_COUNTRY", "IN")  # IN=India, US=USA, GB=UK, CA=Canada

# Queries used for the 12-hour sync job
SYNC_QUERIES = os.getenv(
    "SYNC_QUERIES",
    "software engineer,data scientist,machine learning engineer,devops engineer,product manager"
).split(",")

CLASSIFICATION_MODEL = "facebook/bart-large-mnli"
SUMMARIZATION_MODEL = "sshleifer/distilbart-cnn-12-6"
QA_MODEL = "deepset/roberta-base-squad2"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

JOB_CATEGORIES = [
    "Software Engineering", "Data Science", "Product Management",
    "DevOps", "Machine Learning", "Frontend Development",
    "Backend Development", "Full Stack Development", "Mobile Development",
    "Cloud Engineering", "Cybersecurity", "Database Administration",
    "UI/UX Design", "Quality Assurance", "Business Analysis",
    "Project Management", "Technical Writing", "Sales Engineering",
    "Site Reliability Engineering", "AI Research"
]

CHROMA_COLLECTION = "job_postings"
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
