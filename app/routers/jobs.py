from fastapi import APIRouter, HTTPException
from app.schemas import JobPosting
from app.services.container import rag, classifier, skill_extractor
from app.services.job_sync import run_sync, get_db_stats, load_all_from_db
import uuid

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


@router.post("/add")
async def add_job(job: JobPosting):
    if not job.id:
        job.id = str(uuid.uuid4())[:8]
    if not job.category:
        result = classifier.classify(f"{job.title} {job.description}")
        job.category = result["category"]
    rag.index_jobs([job.model_dump()])
    return {"status": "success", "job_id": job.id, "category": job.category}


@router.post("/add-batch")
async def add_jobs_batch(jobs: list[JobPosting]):
    for job in jobs:
        if not job.id:
            job.id = str(uuid.uuid4())[:8]
        if not job.category:
            result = classifier.classify(f"{job.title} {job.description}")
            job.category = result["category"]
    rag.index_jobs([j.model_dump() for j in jobs])
    return {"status": "success", "count": len(jobs)}


@router.get("/search")
async def search_jobs(query: str, top_k: int = 5):
    results = rag.search(query, top_k=top_k)
    return {"results": results, "count": len(results)}


@router.get("/list")
async def list_jobs():
    jobs = rag.get_all_jobs()
    return {"jobs": jobs, "count": len(jobs)}


@router.get("/{job_id}")
async def get_job(job_id: str):
    job = rag.get_job_by_id(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    rag.delete_job(job_id)
    return {"status": "deleted"}


@router.get("/stats/overview")
async def job_stats():
    return rag.get_stats()


@router.post("/sync")
async def trigger_sync():
    """Manually trigger a job fetch from all external sources."""
    result = run_sync()
    return result


@router.get("/sync/status")
async def sync_status():
    """Show SQLite DB stats and last sync time."""
    return get_db_stats()


@router.post("/sync/load-db")
async def load_db_into_rag():
    """Re-index all SQLite jobs into ChromaDB (useful after restart)."""
    jobs = load_all_from_db()
    rag.index_jobs(jobs)
    return {"status": "indexed", "count": len(jobs)}
