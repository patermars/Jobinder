from app.services.resume_parser import ResumeParser
from app.services.classifier import JobClassifier
from app.services.summarizer import ResumeSummarizer
from app.services.qa_engine import QAEngine
from app.services.rag_engine import RAGEngine
from app.services.skill_extractor import SkillExtractor
from app.services.scorer import MatchScorer
from app.services.interview_gen import InterviewGenerator
from app.services.agents import ResumeReviewerAgent, JobMatcherAgent

parser = ResumeParser()
classifier = JobClassifier()
summarizer = ResumeSummarizer()
qa_engine = QAEngine()
rag = RAGEngine()
skill_extractor = SkillExtractor()
scorer = MatchScorer()
interview_gen = InterviewGenerator()
reviewer = ResumeReviewerAgent(classifier, summarizer, skill_extractor, scorer, parser)
matcher = JobMatcherAgent(rag, classifier, skill_extractor, scorer, interview_gen)
