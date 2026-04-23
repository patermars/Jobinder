from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.container import rag, classifier, summarizer, skill_extractor, scorer, parser, qa_engine, interview_gen, reviewer, matcher

router = APIRouter(prefix="/api/match", tags=["Matching"])


@router.post("/find")
async def find_matches(file: UploadFile = File(None), text: str = Form(None), top_k: int = Form(5)):
    resume_text = await _get_resume_text(file, text)
    matches = matcher.match(resume_text, top_k=top_k)
    return {"matches": matches, "count": len(matches)}


@router.post("/full-analysis")
async def full_analysis(file: UploadFile = File(None), text: str = Form(None), top_k: int = Form(5)):
    resume_text = await _get_resume_text(file, text)
    review = reviewer.review(resume_text)
    analysis = matcher.full_analysis(resume_text, top_k=top_k)
    return {
        "resume_review": review,
        "job_matches": analysis["matches"],
        "interview_questions": analysis["interview_questions"],
        "skill_gaps": analysis["skill_gaps"],
        "career_suggestions": analysis["career_suggestions"],
    }


@router.post("/skill-gap")
async def skill_gap_analysis(text: str = Form(...), job_id: str = Form(...)):
    job = rag.get_job_by_id(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    resume_skills = skill_extractor.extract(text)
    job_skills = skill_extractor.extract(job["document"])
    comparison = skill_extractor.compare_skills(resume_skills, job_skills)
    return {
        "matched_skills": comparison["matched"],
        "missing_skills": comparison["missing"],
        "extra_skills": comparison["extra"],
        "fit_percentage": comparison["coverage_percent"],
        "recommendations": [f"Consider learning {s}" for s in comparison["missing"][:5]]
    }


@router.post("/interview-questions")
async def generate_interview(text: str = Form(...), job_title: str = Form(""), num: int = Form(10)):
    skills = skill_extractor.extract(text)
    questions = interview_gen.generate(skills, job_title, num)
    return {"questions": questions}


@router.post("/qa")
async def ask_question(question: str = Form(...), resume_text: str = Form(""), job_id: str = Form("")):
    context = resume_text
    if job_id:
        job = rag.get_job_by_id(job_id)
        if job:
            context += f"\n\nJob: {job['document']}"
    if not context.strip():
        raise HTTPException(400, "Provide resume_text or job_id for context")
    result = qa_engine.answer(question, context)
    return result


@router.post("/compare")
async def compare_resumes(texts: list[str] = Form(...)):
    if len(texts) < 2:
        raise HTTPException(400, "Provide at least 2 resumes")
    results = []
    for i, text in enumerate(texts):
        review = reviewer.review(text)
        results.append({"index": i, "review": review})
    results.sort(key=lambda x: x["review"]["overall_score"], reverse=True)
    return {"rankings": results}


async def _get_resume_text(file, text):
    if file:
        content = await file.read()
        parsed = parser.parse_file(file.filename, content)
        return parsed["raw_text"]
    elif text:
        return text
    raise HTTPException(400, "Provide a file or text")
