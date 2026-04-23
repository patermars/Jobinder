from transformers import pipeline
from app.config import CLASSIFICATION_MODEL, JOB_CATEGORIES


class JobClassifier:
    def __init__(self):
        self._pipe = None

    @property
    def pipe(self):
        if self._pipe is None:
            self._pipe = pipeline("zero-shot-classification", model=CLASSIFICATION_MODEL)
        return self._pipe

    def classify(self, text: str, categories: list[str] = None) -> dict:
        cats = categories or JOB_CATEGORIES
        result = self.pipe(text[:1024], cats, multi_label=False)
        return {
            "category": result["labels"][0],
            "confidence": result["scores"][0],
            "all_scores": dict(zip(result["labels"][:5], result["scores"][:5]))
        }

    def classify_batch(self, texts: list[str], categories: list[str] = None) -> list[dict]:
        return [self.classify(t, categories) for t in texts]
