import re
import io
from pathlib import Path


class ResumeParser:
    def parse_text(self, text: str) -> dict:
        return {
            "name": self._extract_name(text),
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "education": self._extract_education(text),
            "experience_years": self._extract_experience_years(text),
            "raw_text": text
        }

    def parse_file(self, file_path: str, content: bytes = None) -> dict:
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            text = self._parse_pdf(content or open(file_path, "rb").read())
        elif ext in (".docx", ".doc"):
            text = self._parse_docx(content or open(file_path, "rb").read())
        elif ext == ".txt":
            text = (content or open(file_path, "rb").read()).decode("utf-8", errors="ignore")
        else:
            text = (content or open(file_path, "rb").read()).decode("utf-8", errors="ignore")
        return self.parse_text(text)

    def _parse_pdf(self, content: bytes) -> str:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return content.decode("utf-8", errors="ignore")

    def _parse_docx(self, content: bytes) -> str:
        try:
            from docx import Document
            doc = Document(io.BytesIO(content))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            return content.decode("utf-8", errors="ignore")

    def _extract_email(self, text: str) -> str:
        match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
        return match.group(0) if match else ""

    def _extract_phone(self, text: str) -> str:
        match = re.search(r"[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}", text)
        return match.group(0).strip() if match else ""

    def _extract_name(self, text: str) -> str:
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        for line in lines[:5]:
            if re.match(r"^[A-Z][a-z]+(\s+[A-Z][a-z]+){1,3}$", line):
                return line
        return lines[0] if lines else ""

    def _extract_education(self, text: str) -> list[str]:
        degrees = []
        patterns = [
            r"(?i)(B\.?S\.?|B\.?A\.?|M\.?S\.?|M\.?A\.?|Ph\.?D\.?|MBA|Bachelor|Master|Doctor)\w*\s+(?:of\s+|in\s+)?[\w\s,]+",
            r"(?i)(Computer Science|Engineering|Mathematics|Physics|Business|Information Technology)[\w\s]*"
        ]
        for p in patterns:
            matches = re.findall(p, text)
            degrees.extend(matches)
        return list(set(degrees))[:5]

    def _extract_experience_years(self, text: str) -> float:
        patterns = [
            r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)",
            r"experience\s*:?\s*(\d+)\+?\s*(?:years?|yrs?)",
        ]
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return 0.0
