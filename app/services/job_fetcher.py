"""
Job fetchers for external job boards via legal APIs:
- Adzuna: aggregates Indeed, Glassdoor, and others
- JSearch (RapidAPI): aggregates LinkedIn, Indeed, Glassdoor, Naukri, Wellfound, Handshake
"""
import httpx
import uuid
import logging
from app.config import ADZUNA_APP_ID, ADZUNA_APP_KEY, ADZUNA_COUNTRY, JSEARCH_API_KEY, JSEARCH_COUNTRY

logger = logging.getLogger(__name__)


def _make_id(prefix: str, external_id: str) -> str:
    return f"{prefix}_{str(uuid.uuid5(uuid.NAMESPACE_URL, external_id))[:8]}"


async def fetch_adzuna(query: str, country: str = None, results_per_page: int = 20) -> list[dict]:
    """Adzuna aggregates Indeed, Glassdoor, and 100+ boards."""
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        return []
    country = (country or ADZUNA_COUNTRY).lower()
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": results_per_page,
        "what": query,
        "content-type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning(f"Adzuna fetch failed for '{query}': {e}")
        return []

    jobs = []
    for item in data.get("results", []):
        jobs.append({
            "id": _make_id("adzuna", item.get("id", str(uuid.uuid4()))),
            "title": item.get("title", ""),
            "company": item.get("company", {}).get("display_name", "Unknown"),
            "description": item.get("description", ""),
            "requirements": [],
            "preferred": [],
            "location": item.get("location", {}).get("display_name", ""),
            "salary_range": _adzuna_salary(item),
            "job_type": "Full-time",
            "category": item.get("category", {}).get("label", ""),
            "source": "adzuna",
            "url": item.get("redirect_url", ""),
        })
    return jobs


def _adzuna_salary(item: dict) -> str:
    low = item.get("salary_min")
    high = item.get("salary_max")
    if low and high:
        return f"${int(low):,} - ${int(high):,}"
    if low:
        return f"${int(low):,}+"
    return ""


async def fetch_jsearch(query: str, num_pages: int = 2) -> list[dict]:
    """
    JSearch via RapidAPI — aggregates LinkedIn, Indeed, Glassdoor,
    Naukri, Wellfound, Handshake, and more.
    """
    if not JSEARCH_API_KEY:
        return []
    country_name = {"IN": "India", "US": "USA", "GB": "UK", "CA": "Canada", "AU": "Australia"}
    location = country_name.get(JSEARCH_COUNTRY.upper(), JSEARCH_COUNTRY)
    full_query = f"{query} in {location}"
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            for page in range(1, num_pages + 1):
                params = {"query": full_query, "page": str(page), "num_pages": "1"}
                for attempt in range(2):
                    try:
                        resp = await client.get(url, headers=headers, params=params)
                        if resp.status_code != 200:
                            logger.warning(f"JSearch page {page} for '{full_query}': HTTP {resp.status_code}")
                            break
                        for item in resp.json().get("data", []):
                            jobs.append({
                                "id": _make_id("jsearch", item.get("job_id", str(uuid.uuid4()))),
                                "title": item.get("job_title", ""),
                                "company": item.get("employer_name", "Unknown"),
                                "description": item.get("job_description", ""),
                                "requirements": item.get("job_required_skills") or [],
                                "preferred": [],
                                "location": _jsearch_location(item),
                                "salary_range": _jsearch_salary(item),
                                "job_type": item.get("job_employment_type", "Full-time"),
                                "category": item.get("job_category") or "",
                                "source": item.get("job_publisher", "jsearch"),
                                "url": item.get("job_apply_link", ""),
                            })
                        break
                    except httpx.TimeoutException:
                        if attempt == 0:
                            logger.warning(f"JSearch timeout on page {page} for '{full_query}', retrying...")
                        else:
                            logger.warning(f"JSearch timeout on page {page} for '{full_query}', skipping")
    except Exception as e:
        logger.warning(f"JSearch fetch failed for '{full_query}': {e}")
    return jobs


def _jsearch_location(item: dict) -> str:
    city = item.get("job_city", "")
    state = item.get("job_state", "")
    country = item.get("job_country", "")
    parts = [p for p in [city, state, country] if p]
    return ", ".join(parts) if parts else item.get("job_is_remote") and "Remote" or ""


def _jsearch_salary(item: dict) -> str:
    low = item.get("job_min_salary")
    high = item.get("job_max_salary")
    period = item.get("job_salary_period", "")
    if low and high:
        return f"${int(low):,} - ${int(high):,} {period}".strip()
    return ""


async def fetch_all_jobs(queries: list[str]) -> list[dict]:
    """Fetch from all sources for each query, deduplicate by id."""
    seen, results = set(), []
    for query in queries:
        for job in await fetch_adzuna(query) + await fetch_jsearch(query):
            if job["id"] not in seen:
                seen.add(job["id"])
                results.append(job)
    return results
