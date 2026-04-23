from app.services.classifier import JobClassifier
from app.services.summarizer import ResumeSummarizer
from app.services.qa_engine import QAEngine
from app.services.rag_engine import RAGEngine
from app.services.skill_extractor import SkillExtractor
from app.services.scorer import MatchScorer
from app.services.resume_parser import ResumeParser
from app.services.interview_gen import InterviewGenerator


class ResumeReviewerAgent:
    def __init__(self, classifier: JobClassifier, summarizer: ResumeSummarizer,
                 skill_extractor: SkillExtractor, scorer: MatchScorer, parser: ResumeParser):
        self.classifier = classifier
        self.summarizer = summarizer
        self.skill_extractor = skill_extractor
        self.scorer = scorer
        self.parser = parser

    def review(self, resume_text: str) -> dict:
        parsed = self.parser.parse_text(resume_text)
        skills = self.skill_extractor.extract(resume_text)
        skills_by_cat = self.skill_extractor.extract_with_categories(resume_text)
        classification = self.classifier.classify(resume_text)
        summary = self.summarizer.summarize(resume_text)
        highlights = self.summarizer.extract_highlights(resume_text)
        overall_score = self.scorer.score_resume(
            skills_count=len(skills),
            experience_years=parsed["experience_years"],
            education_count=len(parsed["education"]),
            has_summary=len(summary) > 50
        )

        strengths = []
        weaknesses = []
        if len(skills) >= 10:
            strengths.append(f"Strong technical profile with {len(skills)} identified skills")
        elif len(skills) < 5:
            weaknesses.append("Limited technical skills detected — consider adding more keywords")
        if parsed["experience_years"] >= 5:
            strengths.append(f"{parsed['experience_years']}+ years of experience")
        elif parsed["experience_years"] == 0:
            weaknesses.append("No experience duration detected — add years of experience")
        if parsed["education"]:
            strengths.append(f"Educational background: {', '.join(parsed['education'][:3])}")
        else:
            weaknesses.append("No formal education detected")
        if len(resume_text.split()) > 300:
            strengths.append("Comprehensive resume with detailed information")
        else:
            weaknesses.append("Resume is brief — consider adding more detail")

        return {
            "name": parsed["name"],
            "email": parsed["email"],
            "phone": parsed["phone"],
            "skills": skills,
            "skills_by_category": skills_by_cat,
            "experience_years": parsed["experience_years"],
            "education": parsed["education"],
            "category": classification["category"],
            "category_confidence": classification["confidence"],
            "top_categories": classification["all_scores"],
            "summary": summary,
            "highlights": highlights,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "overall_score": overall_score
        }


class JobMatcherAgent:
    def __init__(self, rag_engine: RAGEngine, classifier: JobClassifier,
                 skill_extractor: SkillExtractor, scorer: MatchScorer,
                 interview_gen: InterviewGenerator):
        self.rag = rag_engine
        self.classifier = classifier
        self.skill_extractor = skill_extractor
        self.scorer = scorer
        self.interview_gen = interview_gen

    def match(self, resume_text: str, top_k: int = 5, filters: dict = None) -> list[dict]:
        resume_skills = self.skill_extractor.extract(resume_text)
        resume_category = self.classifier.classify(resume_text)
        candidates = self.rag.search(resume_text, top_k=top_k * 2, filters=filters)
        ranked = self.scorer.rank_matches(resume_text, candidates)
        results = []
        for job in ranked[:top_k]:
            job_text = job.get("document", "")
            job_skills = self.skill_extractor.extract(job_text)
            skill_comparison = self.skill_extractor.compare_skills(resume_skills, job_skills)
            job_category = job.get("metadata", {}).get("category", "")
            cat_match = job_category.lower() == resume_category["category"].lower() if job_category else False
            match_score = self.scorer.compute_match_score(
                resume_text, job_text, skill_comparison, cat_match
            )
            results.append({
                "job_id": job.get("id", ""),
                "job_title": job.get("metadata", {}).get("title", "Unknown"),
                "company": job.get("metadata", {}).get("company", "Unknown"),
                "location": job.get("metadata", {}).get("location", ""),
                "salary_range": job.get("metadata", {}).get("salary_range", ""),
                "score": match_score,
                "semantic_similarity": job.get("similarity", 0),
                "category_match": cat_match,
                "skill_overlap": skill_comparison["matched"],
                "missing_skills": skill_comparison["missing"],
                "extra_skills": skill_comparison["extra"],
                "skill_coverage": skill_comparison["coverage_percent"],
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def full_analysis(self, resume_text: str, top_k: int = 5) -> dict:
        matches = self.match(resume_text, top_k=top_k)
        resume_skills = self.skill_extractor.extract(resume_text)
        classification = self.classifier.classify(resume_text)
        interview_questions = self.interview_gen.generate(
            skills=resume_skills,
            job_title=matches[0]["job_title"] if matches else "",
            num_questions=8
        )

        all_missing = set()
        for m in matches:
            all_missing.update(m.get("missing_skills", []))
        career_suggestions = self._suggest_career_paths(classification["category"], resume_skills)

        return {
            "matches": matches,
            "resume_category": classification["category"],
            "category_confidence": classification["confidence"],
            "total_skills": len(resume_skills),
            "interview_questions": interview_questions,
            "skill_gaps": sorted(all_missing),
            "career_suggestions": career_suggestions
        }

    def _suggest_career_paths(self, current_category: str, skills: list[str]) -> list[dict]:
        paths = {
            "Software Engineering": ["Senior Software Engineer", "Tech Lead", "Staff Engineer", "Engineering Manager", "CTO"],
            "Data Science": ["Senior Data Scientist", "ML Engineer", "Data Science Manager", "Head of Analytics", "Chief Data Officer"],
            "Frontend Development": ["Senior Frontend Engineer", "UI Architect", "Frontend Lead", "UX Engineer", "Design Technologist"],
            "Backend Development": ["Senior Backend Engineer", "Platform Engineer", "Backend Architect", "Principal Engineer"],
            "DevOps": ["Senior DevOps Engineer", "SRE Lead", "Platform Team Lead", "Infrastructure Architect", "VP Engineering"],
            "Machine Learning": ["Senior ML Engineer", "ML Architect", "AI Research Scientist", "Head of ML", "VP of AI"],
            "Product Management": ["Senior PM", "Group PM", "Director of Product", "VP Product", "CPO"],
        }
        suggested_roles = paths.get(current_category, ["Senior Engineer", "Tech Lead", "Engineering Manager"])
        skills_to_acquire = []
        if "Kubernetes" not in [s.lower() for s in skills]:
            skills_to_acquire.append("Kubernetes")
        if "System Design" not in [s.lower() for s in skills]:
            skills_to_acquire.append("System Design")
        if "Leadership" not in [s.lower() for s in skills]:
            skills_to_acquire.append("Leadership")

        return [{
            "current_role": current_category,
            "suggested_roles": suggested_roles,
            "skills_to_acquire": skills_to_acquire,
            "timeline": "1-3 years for next role transition"
        }]
