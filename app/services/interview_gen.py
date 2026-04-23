import random


class InterviewGenerator:
    TECHNICAL_TEMPLATES = [
        "Explain how you have used {skill} in a production environment.",
        "What are the key differences between {skill} and its alternatives?",
        "Describe a challenging problem you solved using {skill}.",
        "How would you optimize a system built with {skill}?",
        "Walk me through your experience with {skill} and how it applies to this role.",
        "What best practices do you follow when working with {skill}?",
        "How do you stay current with developments in {skill}?",
    ]

    BEHAVIORAL_TEMPLATES = [
        "Tell me about a time you had to learn a new technology quickly.",
        "Describe a situation where you disagreed with a team member on a technical decision.",
        "How do you handle tight deadlines and competing priorities?",
        "Give an example of a project where you took initiative beyond your role.",
        "Tell me about a time you failed and what you learned from it.",
        "How do you approach mentoring junior team members?",
        "Describe a time when you had to communicate complex technical concepts to non-technical stakeholders.",
        "Tell me about a time you improved a process or workflow.",
    ]

    SITUATIONAL_TEMPLATES = [
        "If you discovered a critical bug in production on a Friday evening, what would you do?",
        "How would you approach building a {skill}-based solution from scratch?",
        "If you were asked to lead a project in an unfamiliar domain, how would you prepare?",
        "How would you handle a situation where requirements keep changing mid-sprint?",
        "If you had to choose between shipping a feature quickly or ensuring code quality, what would you prioritize?",
        "How would you design a system that needs to scale from 100 to 1 million users?",
    ]

    def generate(self, skills: list[str], job_title: str = "", num_questions: int = 10) -> list[dict]:
        questions = []
        tech_count = max(num_questions // 2, 1)
        behav_count = max(num_questions // 3, 1)
        sit_count = num_questions - tech_count - behav_count

        sample_skills = skills[:10] if skills else ["technology"]

        for i in range(tech_count):
            skill = sample_skills[i % len(sample_skills)]
            template = random.choice(self.TECHNICAL_TEMPLATES)
            questions.append({
                "question": template.format(skill=skill),
                "category": "technical",
                "difficulty": random.choice(["easy", "medium", "hard"]),
                "expected_topics": [skill, job_title] if job_title else [skill]
            })

        for _ in range(behav_count):
            questions.append({
                "question": random.choice(self.BEHAVIORAL_TEMPLATES),
                "category": "behavioral",
                "difficulty": "medium",
                "expected_topics": ["communication", "teamwork", "problem-solving"]
            })

        for _ in range(sit_count):
            skill = random.choice(sample_skills)
            template = random.choice(self.SITUATIONAL_TEMPLATES)
            questions.append({
                "question": template.format(skill=skill),
                "category": "situational",
                "difficulty": random.choice(["medium", "hard"]),
                "expected_topics": [skill, "decision-making"]
            })

        random.shuffle(questions)
        return questions[:num_questions]
