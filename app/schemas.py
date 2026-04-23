from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ResumeUpload(BaseModel):
    filename: str
    text: str
    uploaded_at: datetime = Field(default_factory=datetime.now)


class JobPosting(BaseModel):
    id: Optional[str] = None
    title: str
    company: str
    description: str
    requirements: list[str] = []
    preferred: list[str] = []
    location: str = ""
    salary_range: str = ""
    job_type: str = "Full-time"
    category: Optional[str] = None
    posted_at: datetime = Field(default_factory=datetime.now)


class MatchResult(BaseModel):
    job_id: str
    job_title: str
    company: str
    score: float
    category_match: bool
    skill_overlap: list[str]
    missing_skills: list[str]
    summary: str


class ResumeAnalysis(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    skills: list[str] = []
    experience_years: float = 0
    education: list[str] = []
    category: str = ""
    category_confidence: float = 0.0
    summary: str = ""
    strengths: list[str] = []
    weaknesses: list[str] = []
    overall_score: float = 0.0


class QARequest(BaseModel):
    question: str
    resume_text: str = ""
    job_id: str = ""


class QAResponse(BaseModel):
    answer: str
    confidence: float
    source: str = ""


class SkillGap(BaseModel):
    skill: str
    importance: str  # critical, important, nice-to-have
    suggestion: str


class SkillGapAnalysis(BaseModel):
    matched_skills: list[str]
    missing_skills: list[SkillGap]
    fit_percentage: float
    recommendations: list[str]


class InterviewQuestion(BaseModel):
    question: str
    category: str  # technical, behavioral, situational
    difficulty: str  # easy, medium, hard
    expected_topics: list[str]


class CareerPath(BaseModel):
    current_role: str
    suggested_roles: list[str]
    skills_to_acquire: list[str]
    timeline: str


class BatchMatchRequest(BaseModel):
    resume_texts: list[str]
    job_ids: list[str] = []
    top_k: int = 5
