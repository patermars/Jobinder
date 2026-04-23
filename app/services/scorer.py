from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app.config import EMBEDDING_MODEL


class MatchScorer:
    def __init__(self):
        self._model = None

    @property
    def model(self):
        if self._model is None:
            self._model = SentenceTransformer(EMBEDDING_MODEL)
        return self._model

    def semantic_similarity(self, text_a: str, text_b: str) -> float:
        embeddings = self.model.encode([text_a[:2048], text_b[:2048]])
        sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return round(float(sim), 4)

    def compute_match_score(self, resume_text: str, job_text: str, skill_overlap: dict, category_match: bool) -> float:
        semantic = self.semantic_similarity(resume_text, job_text)
        skill_score = skill_overlap.get("coverage_percent", 0) / 100
        cat_bonus = 0.1 if category_match else 0
        score = (semantic * 0.4) + (skill_score * 0.5) + cat_bonus
        return round(min(score, 1.0) * 100, 1)

    def rank_matches(self, resume_text: str, jobs: list[dict]) -> list[dict]:
        if not jobs:
            return []
        resume_emb = self.model.encode([resume_text[:2048]])
        job_texts = [j.get("document", j.get("description", ""))[:2048] for j in jobs]
        job_embs = self.model.encode(job_texts)
        sims = cosine_similarity(resume_emb, job_embs)[0]
        ranked = []
        for i, job in enumerate(jobs):
            ranked.append({**job, "similarity": round(float(sims[i]), 4)})
        ranked.sort(key=lambda x: x["similarity"], reverse=True)
        return ranked

    def score_resume(self, skills_count: int, experience_years: float, education_count: int, has_summary: bool) -> float:
        skill_s = min(skills_count / 15, 1.0) * 35
        exp_s = min(experience_years / 10, 1.0) * 30
        edu_s = min(education_count / 2, 1.0) * 20
        sum_s = 15 if has_summary else 0
        return round(skill_s + exp_s + edu_s + sum_s, 1)
