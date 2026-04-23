"""
Fetch jobs from external APIs and populate jobs.db.
Run: python populate_jobs.py
"""
import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Import the fetcher
import sys
sys.path.insert(0, str(Path(__file__).parent))
from app.services.job_fetcher import fetch_all_jobs

DB_PATH = Path("data/jobs.db")
DB_PATH.parent.mkdir(exist_ok=True)

# Queries to fetch
QUERIES = os.getenv("SYNC_QUERIES", "software engineer,data scientist,devops engineer").split(",")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            description TEXT,
            requirements TEXT,
            preferred TEXT,
            location TEXT,
            salary_range TEXT,
            job_type TEXT,
            category TEXT,
            source TEXT,
            url TEXT,
            fetched_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_jobs(jobs: list[dict]) -> int:
    conn = sqlite3.connect(DB_PATH)
    inserted = 0
    for job in jobs:
        cursor = conn.execute(
            """INSERT OR IGNORE INTO jobs
               (id, title, company, description, requirements, preferred,
                location, salary_range, job_type, category, source, url, fetched_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                job["id"], job["title"], job["company"], job["description"],
                json.dumps(job.get("requirements", [])),
                json.dumps(job.get("preferred", [])),
                job.get("location", ""), job.get("salary_range", ""),
                job.get("job_type", "Full-time"), job.get("category", ""),
                job.get("source", ""), job.get("url", ""),
                datetime.utcnow().isoformat(),
            ),
        )
        inserted += cursor.rowcount
    conn.commit()
    conn.close()
    return inserted


async def main():
    print(f"Fetching jobs for queries: {QUERIES}")
    jobs = await fetch_all_jobs(QUERIES)
    print(f"Fetched {len(jobs)} jobs from APIs")
    
    init_db()
    inserted = save_jobs(jobs)
    print(f"Saved {inserted} new jobs to {DB_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
