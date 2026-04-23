import re
import json
from pathlib import Path
from app.config import DATA_DIR


class SkillExtractor:
    def __init__(self):
        self._taxonomy = None

    @property
    def taxonomy(self) -> dict:
        if self._taxonomy is None:
            tax_file = DATA_DIR / "skills_taxonomy.json"
            if tax_file.exists():
                with open(tax_file) as f:
                    self._taxonomy = json.load(f)
            else:
                self._taxonomy = self._default_taxonomy()
        return self._taxonomy

    def extract(self, text: str) -> list[str]:
        text_lower = text.lower()
        found = set()
        for category, skills in self.taxonomy.items():
            for skill in skills:
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    found.add(skill)
        return sorted(found)

    def extract_with_categories(self, text: str) -> dict[str, list[str]]:
        text_lower = text.lower()
        result = {}
        for category, skills in self.taxonomy.items():
            matched = []
            for skill in skills:
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    matched.append(skill)
            if matched:
                result[category] = sorted(matched)
        return result

    def compare_skills(self, resume_skills: list[str], job_skills: list[str]) -> dict:
        resume_set = {s.lower() for s in resume_skills}
        job_set = {s.lower() for s in job_skills}
        matched = resume_set & job_set
        missing = job_set - resume_set
        extra = resume_set - job_set
        coverage = len(matched) / len(job_set) * 100 if job_set else 100
        return {
            "matched": sorted(matched),
            "missing": sorted(missing),
            "extra": sorted(extra),
            "coverage_percent": round(coverage, 1)
        }

    def _default_taxonomy(self) -> dict:
        return {
            "Programming Languages": ["Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB", "Perl", "Lua", "Dart", "Elixir", "Haskell"],
            "Web Frameworks": ["React", "Angular", "Vue", "Django", "Flask", "FastAPI", "Express", "Next.js", "Spring Boot", "Rails", "Laravel", "ASP.NET", "Svelte", "Gatsby", "Nuxt"],
            "Data & ML": ["TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Keras", "XGBoost", "LightGBM", "Spark", "Hadoop", "Airflow", "dbt", "MLflow", "Hugging Face", "OpenCV", "NLTK", "SpaCy"],
            "Cloud & DevOps": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", "GitHub Actions", "CI/CD", "Linux", "Nginx", "Apache", "Prometheus", "Grafana"],
            "Databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra", "DynamoDB", "SQLite", "Oracle", "SQL Server", "Neo4j", "InfluxDB", "Firestore"],
            "Tools & Practices": ["Git", "Jira", "Agile", "Scrum", "REST API", "GraphQL", "gRPC", "Microservices", "TDD", "OAuth", "JWT", "WebSocket", "Kafka", "RabbitMQ", "Celery"],
            "Soft Skills": ["Leadership", "Communication", "Problem Solving", "Teamwork", "Critical Thinking", "Project Management", "Mentoring", "Presentation", "Collaboration", "Time Management"]
        }
