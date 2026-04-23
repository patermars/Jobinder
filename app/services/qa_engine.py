from transformers import pipeline
from app.config import QA_MODEL


class QAEngine:
    def __init__(self):
        self._pipe = None

    @property
    def pipe(self):
        if self._pipe is None:
            self._pipe = pipeline("question-answering", model=QA_MODEL)
        return self._pipe

    def answer(self, question: str, context: str) -> dict:
        if not context.strip():
            return {"answer": "No context provided.", "confidence": 0.0}
        ctx = context[:4096]
        result = self.pipe(question=question, context=ctx)
        return {
            "answer": result["answer"],
            "confidence": round(result["score"], 4),
            "start": result["start"],
            "end": result["end"]
        }

    def answer_multiple(self, questions: list[str], context: str) -> list[dict]:
        return [self.answer(q, context) for q in questions]

    def recruiter_query(self, question: str, resume_text: str, job_text: str = "") -> dict:
        combined = resume_text
        if job_text:
            combined = f"Resume: {resume_text}\n\nJob Description: {job_text}"
        return self.answer(question, combined)
