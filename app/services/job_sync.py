"""
Job sync service:
- Persists fetched jobs to SQLite (local DB)
- Syncs new jobs into ChromaDB (RAG)
- Runs automatically every 12 hours via APScheduler
"""
import json
import sqlite3
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from app.config import DATA_DIR, SYNC_QUERIES
from app.services.job_fetcher import fetch_all_jobs

logger = logging.getLogger(__name__)

DB_PATH = DATA_DIR / "jobs.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_conn() as conn:
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


def save_jobs(jobs: list[dict]) -> int:
    """Insert new jobs, skip duplicates. Returns count of new rows."""
    new_count = 0
    with _get_conn() as conn:
        for job in jobs:
            try:
                conn.execute(
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
                if conn.execute("SELECT changes()").fetchone()[0]:
                    new_count += 1
            except Exception as e:
                logger.warning(f"Failed to save job {job.get('id')}: {e}")
    return new_count


def load_all_from_db() -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute("SELECT * FROM jobs").fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["requirements"] = json.loads(d["requirements"] or "[]")
        d["preferred"] = json.loads(d["preferred"] or "[]")
        result.append(d)
    return result


def get_db_stats() -> dict:
    with _get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        sources = conn.execute(
            "SELECT source, COUNT(*) as cnt FROM jobs GROUP BY source"
        ).fetchall()
        last_sync = conn.execute(
            "SELECT MAX(fetched_at) FROM jobs"
        ).fetchone()[0]
    return {
        "total_jobs": total,
        "by_source": {row[0]: row[1] for row in sources},
        "last_sync": last_sync,
    }


def _sync_to_rag(jobs: list[dict]):
    from app.services.container import rag
    rag.index_jobs(jobs)


def run_sync():
    """Fetch → save to SQLite → index new jobs in ChromaDB."""
    logger.info(f"Job sync started — queries: {SYNC_QUERIES}")
    try:
        # APScheduler runs in a plain thread — create a fresh event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            jobs = loop.run_until_complete(fetch_all_jobs(SYNC_QUERIES))
        finally:
            loop.close()

        logger.info(f"Fetched {len(jobs)} jobs from APIs")
        new_count = save_jobs(jobs)
        if jobs:
            _sync_to_rag(jobs)
        logger.info(f"Job sync complete — {new_count} new, {len(jobs)} total fetched")
        return {"fetched": len(jobs), "new": new_count}
    except Exception as e:
        logger.exception(f"Job sync failed: {e}")
        return {"error": str(e)}


_scheduler = BackgroundScheduler()


def start_scheduler():
    init_db()
    _scheduler.add_job(run_sync, "interval", hours=12, id="job_sync", replace_existing=True,
                       next_run_time=datetime.now())
    _scheduler.start()
    logger.info("Job sync scheduler started (runs now + every 12 hours)")


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
