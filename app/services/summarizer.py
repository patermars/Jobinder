from transformers import pipeline
from app.config import SUMMARIZATION_MODEL


class ResumeSummarizer:
    def __init__(self):
        self._pipe = None

    @property
    def pipe(self):
        if self._pipe is None:
            self._pipe = pipeline("summarization", model=SUMMARIZATION_MODEL)
        return self._pipe

    def summarize(self, text: str, max_length: int = 200, min_length: int = 50) -> str:
        if len(text.split()) < min_length:
            return text
        chunks = self._chunk_text(text, max_tokens=900)
        summaries = []
        for chunk in chunks:
            result = self.pipe(chunk, max_length=max_length, min_length=min_length, do_sample=False)
            summaries.append(result[0]["summary_text"])
        if len(summaries) > 1:
            combined = " ".join(summaries)
            if len(combined.split()) > max_length:
                result = self.pipe(combined[:2048], max_length=max_length, min_length=min_length, do_sample=False)
                return result[0]["summary_text"]
            return combined
        return summaries[0]

    def extract_highlights(self, text: str, num_highlights: int = 5) -> list[str]:
        summary = self.summarize(text, max_length=300)
        sentences = [s.strip() for s in summary.replace(".", ".\n").split("\n") if s.strip()]
        return sentences[:num_highlights]

    def _chunk_text(self, text: str, max_tokens: int = 900) -> list[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), max_tokens):
            chunks.append(" ".join(words[i:i + max_tokens]))
        return chunks
