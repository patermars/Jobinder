import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.routers import resumes, jobs, matching, analytics
from app.services.job_sync import start_scheduler, stop_scheduler, init_db, load_all_from_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Seed ChromaDB from persisted SQLite jobs on every startup
    from app.services.container import rag
    saved_jobs = load_all_from_db()
    if saved_jobs:
        rag.index_jobs(saved_jobs)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="ResuMatch AI",
    description="Resume + Job Matching System",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(resumes.router)
app.include_router(jobs.router)
app.include_router(matching.router)
app.include_router(analytics.router)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def root():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ResuMatch AI"}
