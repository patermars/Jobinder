from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.container import parser, classifier, summarizer, skill_extractor, reviewer

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 10MB)")
    content = await file.read()
    parsed = parser.parse_file(file.filename, content)
    return {"status": "success", "parsed": parsed}


@router.post("/analyze")
async def analyze_resume(file: UploadFile = File(None), text: str = Form(None)):
    if file:
        content = await file.read()
        parsed = parser.parse_file(file.filename, content)
        resume_text = parsed["raw_text"]
    elif text:
        resume_text = text
    else:
        raise HTTPException(400, "Provide a file or text")
    review = reviewer.review(resume_text)
    return review


@router.post("/summarize")
async def summarize_resume(text: str = Form(...)):
    summary = summarizer.summarize(text)
    highlights = summarizer.extract_highlights(text)
    return {"summary": summary, "highlights": highlights}


@router.post("/classify")
async def classify_resume(text: str = Form(...)):
    return classifier.classify(text)


@router.post("/extract-skills")
async def extract_skills(text: str = Form(...)):
    skills = skill_extractor.extract(text)
    categorized = skill_extractor.extract_with_categories(text)
    return {"skills": skills, "by_category": categorized}
