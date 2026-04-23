# Jobinder

NLP-powered system that matches resumes to jobs, generates feedback, and provides recruiter tools.

## NLP Components

| Component | Model | Purpose |
|-----------|-------|---------|
| Text Classification | `facebook/bart-large-mnli` (zero-shot) | Job category prediction |
| Summarization | `sshleifer/distilbart-cnn-12-6` | Resume highlights |
| Question Answering | `deepset/roberta-base-squad2` | Recruiter queries |
| RAG | `all-MiniLM-L6-v2` + ChromaDB | Semantic job search |
| Agents | Custom orchestration | Resume reviewer + Job matcher |

## Features

- **Resume Analysis** — parse PDF/DOCX/TXT, extract skills, classify category, score quality, identify strengths/weaknesses
- **Job Matching** — semantic similarity + skill overlap + category matching with weighted scoring
- **Skill Gap Analysis** — compare resume skills against job requirements
- **Recruiter Q&A** — ask natural language questions about resumes
- **Interview Question Generator** — technical, behavioral, situational questions based on candidate skills
- **Career Path Suggestions** — role progression recommendations
- **Analytics Dashboard** — job database stats, skills demand, category/location breakdown
- **Job Database (RAG)** — add, search, list, delete jobs with vector search
- **Batch Processing** — bulk resume/job operations
- **Resume Comparison** — rank multiple candidates

## Setup

```bash
# Create venv
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

## Project Structure

```
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Models, paths, categories
│   ├── schemas.py           # Pydantic models
│   ├── routers/
│   │   ├── resumes.py       # /api/resumes/*
│   │   ├── jobs.py          # /api/jobs/*
│   │   ├── matching.py      # /api/match/*
│   │   └── analytics.py     # /api/analytics/*
│   └── services/
│       ├── classifier.py    # Zero-shot classification
│       ├── summarizer.py    # Text summarization
│       ├── qa_engine.py     # Extractive QA
│       ├── rag_engine.py    # ChromaDB vector store
│       ├── resume_parser.py # PDF/DOCX/TXT parsing
│       ├── skill_extractor.py # Taxonomy-based extraction
│       ├── scorer.py        # Match scoring
│       ├── interview_gen.py # Question generation
│       └── agents.py        # Orchestrator agents
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── data/
│   ├── sample_jobs.json     # 12 pre-loaded jobs
│   └── skills_taxonomy.json # 150+ skills across 8 categories
└── requirements.txt
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/resumes/analyze` | Full resume analysis |
| POST | `/api/resumes/classify` | Classify job category |
| POST | `/api/resumes/summarize` | Summarize resume |
| POST | `/api/resumes/extract-skills` | Extract skills |
| POST | `/api/jobs/add` | Add job posting |
| GET | `/api/jobs/search?query=...` | Semantic job search |
| GET | `/api/jobs/list` | List all jobs |
| POST | `/api/match/find` | Find matching jobs |
| POST | `/api/match/full-analysis` | Complete analysis + matches + interview Qs |
| POST | `/api/match/skill-gap` | Skill gap analysis |
| POST | `/api/match/interview-questions` | Generate interview questions |
| POST | `/api/match/qa` | Ask questions about resume/job |
| GET | `/api/analytics/dashboard` | Dashboard stats |
| GET | `/api/analytics/skills-demand` | Skills demand analysis |

## Notes

- Models download automatically on first use (~2GB total)
- First request will be slow (model loading), subsequent requests are fast
- ChromaDB runs in-memory; sample jobs auto-load from `data/sample_jobs.json`
- GPU recommended but CPU works fine
