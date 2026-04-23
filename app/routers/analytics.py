from fastapi import APIRouter
from app.services.container import rag, skill_extractor

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def dashboard():
    stats = rag.get_stats()
    jobs = rag.get_all_jobs()
    categories = {}
    locations = {}
    for job in jobs:
        meta = job.get("metadata", {})
        cat = meta.get("category", "Other")
        loc = meta.get("location", "Unknown")
        categories[cat] = categories.get(cat, 0) + 1
        locations[loc] = locations.get(loc, 0) + 1
    return {
        "total_jobs": stats["total_jobs"],
        "categories": categories,
        "locations": locations,
        "top_categories": sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10],
    }


@router.get("/skills-demand")
async def skills_demand():
    jobs = rag.get_all_jobs()
    skill_count = {}
    for job in jobs:
        doc = job.get("document", "")
        skills = skill_extractor.extract(doc)
        for skill in skills:
            skill_count[skill] = skill_count.get(skill, 0) + 1
    sorted_skills = sorted(skill_count.items(), key=lambda x: x[1], reverse=True)
    return {"skills_demand": sorted_skills[:30]}
