import json
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from models.interview import (
    InterviewStartRequest,
    InterviewQuestion,
    InterviewQuestionEvaluation,
    InterviewReport,
    InterviewSessionBase,
)
from ai.llm_provider import get_llm_provider

logger = logging.getLogger("omni.interview.ai")


class InterviewAIService:
    """
    AI-powered Mock Interview Intelligence Engine with 100% deterministic rule-based fallback.
    Generates personalized questions from Digital Twin context and evaluates candidate responses.
    """

    @classmethod
    async def generate_questions(
        cls,
        request: InterviewStartRequest,
        context: Dict[str, Any],
    ) -> List[InterviewQuestion]:
        """
        Generates progressive, personalized interview questions citing the candidate's actual skills,
        projects, and career goals from their Digital Twin.
        """
        # Extract context summaries for prompt
        skills = cls._extract_context_skills(context)
        resume_summary = cls._extract_resume_summary(context)
        github_summary = cls._extract_github_summary(context)

        count = max(1, min(15, request.question_count))
        prompt = f"""
You are an expert technical hiring manager at a top engineering company.
Generate exactly {count} personalized interview questions for a candidate applying for:
Role: {request.role}
Company: {request.company or 'Leading Engineering Firm'}
Difficulty: {request.difficulty}
Interview Type: {request.interview_type}

Candidate Digital Twin Context:
- Demonstrated Skills: {', '.join(skills[:15]) if skills else 'Software Engineering Fundamentals'}
- Resume Summary: {resume_summary}
- GitHub Highlights: {github_summary}

Requirements:
1. Make questions progressively escalate in difficulty (start Easy, then Medium, then Hard).
2. DO NOT ask generic textbook questions (e.g., "What is REST?"). Instead, reference their demonstrated skills or projects (e.g., "Your profile shows experience with FastAPI and React. How would you design...").
3. Return ONLY a valid JSON list of objects with this schema:
[
  {{
    "question_id": "q1",
    "question": "The question text referencing candidate context...",
    "difficulty": "Easy",
    "category": "Technical",
    "topic": "Backend API Design",
    "expected_skills": ["FastAPI", "REST", "Validation"],
    "estimated_time": 180,
    "generated_from": "Resume & Profile context",
    "order": 1
  }}
]
"""
        try:
            llm = get_llm_provider()
            raw_text = await llm.generate_text(prompt)
            clean_text = re.sub(r"```json|```", "", raw_text).strip()
            data = json.loads(clean_text)

            if isinstance(data, list) and len(data) > 0:
                questions: List[InterviewQuestion] = []
                for idx, idx_item in enumerate(data[:count]):
                    q_id = str(idx_item.get("question_id") or f"q_{idx+1}")
                    q_text = str(idx_item.get("question") or f"Describe your approach to {request.role} challenges.")
                    q_diff = str(idx_item.get("difficulty") or request.difficulty)
                    if q_diff not in ["Easy", "Medium", "Hard"]:
                        q_diff = "Medium"
                    q_cat = str(idx_item.get("category") or request.interview_type)
                    q_topic = str(idx_item.get("topic") or "General Engineering")
                    exp_skills = idx_item.get("expected_skills")
                    if not isinstance(exp_skills, list):
                        exp_skills = [request.role]
                    est_time = int(idx_item.get("estimated_time", 180))
                    gen_from = str(idx_item.get("generated_from", "Digital Twin Context"))

                    questions.append(
                        InterviewQuestion(
                            question_id=q_id,
                            question=q_text,
                            difficulty=q_diff,
                            category=q_cat,
                            topic=q_topic,
                            expected_skills=exp_skills,
                            estimated_time=est_time,
                            generated_from=gen_from,
                            order=idx + 1,
                        )
                    )
                if len(questions) > 0:
                    logger.info(f"[InterviewAIService] Successfully generated {len(questions)} AI questions.")
                    return questions
        except Exception as e:
            logger.warning(f"[InterviewAIService] AI Question generation fallback triggered: {e}")

        return cls.fallback_rule_based_questions(request, context)

    @classmethod
    async def evaluate_answer(
        cls,
        question: InterviewQuestion,
        answer: str,
        context: Dict[str, Any],
    ) -> InterviewQuestionEvaluation:
        """
        Evaluates a candidate's answer across Technical, Communication, Confidence, and Problem Solving dimensions.
        """
        prompt = f"""
You are an expert technical hiring manager evaluating an interview response.
Question ({question.difficulty} - {question.topic}): "{question.question}"
Expected Skills: {', '.join(question.expected_skills)}
Candidate Answer: "{answer}"

Evaluate this answer and return ONLY a valid JSON object matching this schema:
{{
  "question_id": "{question.question_id}",
  "technical_score": 85,
  "communication_score": 80,
  "confidence_score": 85,
  "problem_solving_score": 80,
  "completeness_score": 85,
  "real_world_thinking_score": 80,
  "feedback": "Constructive critique highlighting what was good and what was missing...",
  "ideal_answer": "An exemplary answer to this question...",
  "improvement_suggestions": ["Suggestion 1", "Suggestion 2"],
  "follow_up_questions": ["A tailored follow-up question digging deeper..."],
  "weak_topics": ["Topic area needing work"],
  "strong_topics": ["Topic area well explained"]
}}
Score each dimension from 0 to 100 based on accuracy, clarity, and depth.
"""
        try:
            llm = get_llm_provider()
            raw_text = await llm.generate_text(prompt)
            clean_text = re.sub(r"```json|```", "", raw_text).strip()
            data = json.loads(clean_text)

            if isinstance(data, dict):
                return InterviewQuestionEvaluation(
                    question_id=question.question_id,
                    technical_score=int(data.get("technical_score", 75)),
                    communication_score=int(data.get("communication_score", 75)),
                    confidence_score=int(data.get("confidence_score", 75)),
                    problem_solving_score=int(data.get("problem_solving_score", 75)),
                    completeness_score=int(data.get("completeness_score", 75)),
                    real_world_thinking_score=int(data.get("real_world_thinking_score", 75)),
                    feedback=str(data.get("feedback") or "Good technical explanation with solid structure."),
                    ideal_answer=str(data.get("ideal_answer") or f"A complete answer should address {', '.join(question.expected_skills)} thoroughly."),
                    improvement_suggestions=data.get("improvement_suggestions", ["Include real-world trade-off examples."]),
                    follow_up_questions=data.get("follow_up_questions", [f"How would this scale to 100,000 requests/sec with {question.topic}?"]),
                    weak_topics=data.get("weak_topics", []),
                    strong_topics=data.get("strong_topics", question.expected_skills[:2]),
                )
        except Exception as e:
            logger.warning(f"[InterviewAIService] AI Answer evaluation fallback triggered: {e}")

        return cls.fallback_rule_based_evaluation(question, answer, context)

    @classmethod
    async def generate_report(
        cls,
        session: InterviewSessionBase,
        context: Dict[str, Any],
    ) -> InterviewReport:
        """
        Synthesizes an executive interview report across all evaluated questions.
        """
        if not session.evaluations:
            return cls.fallback_rule_based_report(session)

        evals_summary = [
            f"Q{i+1} ({ev.question_id}): Tech={ev.technical_score}%, Comm={ev.communication_score}%, Feedback: {ev.feedback[:100]}"
            for i, ev in enumerate(session.evaluations)
        ]

        prompt = f"""
You are an Executive Technical Interview Panel reviewing a completed mock interview for:
Role: {session.role}
Company: {session.company or 'General Industry'}
Difficulty: {session.difficulty}

Question Evaluations:
{chr(10).join(evals_summary)}

Return ONLY a valid JSON object with this schema:
{{
  "overall_score": 84,
  "technical_score": 85,
  "communication_score": 82,
  "confidence_score": 84,
  "problem_solving_score": 85,
  "interview_readiness": "Interview Ready",
  "hiring_recommendation": "Strong Hire",
  "strengths": ["Strong architectural design", "Clear communication"],
  "weaknesses": ["Deep performance tuning"],
  "missed_concepts": ["Distributed caching edge cases"],
  "learning_priorities": ["Advanced concurrency in Python"],
  "recommended_projects": ["Build a rate-limited API gateway"],
  "recommended_certifications": ["AWS Certified Solutions Architect"],
  "executive_summary": "Candidate demonstrated strong engineering readiness for {session.role}..."
}}
"""
        try:
            llm = get_llm_provider()
            raw_text = await llm.generate_text(prompt)
            clean_text = re.sub(r"```json|```", "", raw_text).strip()
            data = json.loads(clean_text)

            if isinstance(data, dict):
                return InterviewReport(
                    overall_score=int(data.get("overall_score", 78)),
                    technical_score=int(data.get("technical_score", 78)),
                    communication_score=int(data.get("communication_score", 78)),
                    confidence_score=int(data.get("confidence_score", 78)),
                    problem_solving_score=int(data.get("problem_solving_score", 78)),
                    interview_readiness=str(data.get("interview_readiness", "Proficient")),
                    hiring_recommendation=str(data.get("hiring_recommendation", "Hire")),
                    strengths=data.get("strengths", ["Strong system familiarity", "Consistent problem breakdown"]),
                    weaknesses=data.get("weaknesses", ["Deep edge-case optimization"]),
                    missed_concepts=data.get("missed_concepts", []),
                    learning_priorities=data.get("learning_priorities", [f"Advanced {session.role} production patterns"]),
                    recommended_projects=data.get("recommended_projects", [f"End-to-end {session.role} demo app"]),
                    recommended_certifications=data.get("recommended_certifications", []),
                    executive_summary=str(data.get("executive_summary") or f"Candidate shows strong readiness for {session.role} roles with solid technical communication."),
                )
        except Exception as e:
            logger.warning(f"[InterviewAIService] AI Report generation fallback triggered: {e}")

        return cls.fallback_rule_based_report(session)

    # --- Deterministic Fallback Heuristics ---

    @classmethod
    def fallback_rule_based_questions(
        cls,
        request: InterviewStartRequest,
        context: Dict[str, Any],
    ) -> List[InterviewQuestion]:
        """
        100% deterministic rule-based question generator.
        Creates progressive difficulty questions citing actual candidate skills.
        """
        skills = cls._extract_context_skills(context)
        if not skills:
            skills = ["Python", "REST APIs", "Database Design", "System Architecture", "Git"]

        count = max(1, min(15, request.question_count))
        questions: List[InterviewQuestion] = []

        difficulties = ["Easy", "Medium", "Hard"]
        topics = [
            ("Core Competency Application", ["Clean Code", "Design Patterns"]),
            ("Backend & API Architecture", ["REST", "Authentication", "Validation"]),
            ("Database & State Management", ["SQL/NoSQL", "Indexing", "Transactions"]),
            ("System Scalability & Reliability", ["Caching", "Load Balancing", "Async Processing"]),
            ("Production Troubleshooting", ["Logging", "Monitoring", "Debugging"]),
        ]

        for i in range(count):
            q_id = f"q_{i+1}"
            diff = difficulties[min(i // 2, 2)] if count > 3 else difficulties[min(i, 2)]
            topic_name, exp_skills = topics[i % len(topics)]

            skill_ref = skills[i % len(skills)]
            if diff == "Easy":
                q_text = f"Your profile shows experience with {skill_ref}. Explain how you organize components and manage dependencies using this technology in a production project."
            elif diff == "Medium":
                q_text = f"In your work involving {skill_ref}, describe how you handle error resilience, input validation, and secure authentication workflows."
            else:
                q_text = f"How would you architect a high-traffic, fault-tolerant service for a {request.role} role that heavily utilizes {skill_ref}? Explain your caching and database scaling strategy."

            questions.append(
                InterviewQuestion(
                    question_id=q_id,
                    question=q_text,
                    difficulty=diff,
                    category=request.interview_type,
                    topic=topic_name,
                    expected_skills=[skill_ref] + exp_skills[:2],
                    estimated_time=180,
                    generated_from="Digital Twin Rule-Based Engine",
                    order=i + 1,
                )
            )
        return questions

    @classmethod
    def fallback_rule_based_evaluation(
        cls,
        question: InterviewQuestion,
        answer: str,
        context: Dict[str, Any],
    ) -> InterviewQuestionEvaluation:
        """
        100% deterministic rule-based answer evaluation.
        """
        words = answer.strip().split()
        word_count = len(words)

        # Base scores
        if word_count <= 6:
            tech_score = 45
            comm_score = 50
            conf_score = 50
            prob_score = 45
            comp_score = 40
            feedback = "The answer is too brief to evaluate technical depth."
        elif word_count < 20:
            tech_score = 70
            comm_score = 72
            conf_score = 75
            prob_score = 70
            comp_score = 68
            feedback = "Good introductory explanation, but could provide more real-world architectural trade-offs."
        else:
            tech_score = 84
            comm_score = 85
            conf_score = 86
            prob_score = 84
            comp_score = 82
            feedback = "Comprehensive explanation demonstrating solid familiarity with core engineering principles."

        # Boost score if expected skills mentioned
        matched_skills = [s for s in question.expected_skills if s.lower() in answer.lower()]
        if matched_skills:
            tech_score = min(96, tech_score + 6)
            prob_score = min(95, prob_score + 5)

        ideal = f"An exemplary response should address {', '.join(question.expected_skills)} and highlight scalability and error handling."
        suggestions = ["Include concrete metrics or project examples.", "Discuss potential trade-offs and edge cases."]
        follow_up = f"How would you monitor and debug performance regressions in this {question.topic} workflow?"

        return InterviewQuestionEvaluation(
            question_id=question.question_id,
            technical_score=tech_score,
            communication_score=comm_score,
            confidence_score=conf_score,
            problem_solving_score=prob_score,
            completeness_score=comp_score,
            real_world_thinking_score=tech_score,
            feedback=feedback,
            ideal_answer=ideal,
            improvement_suggestions=suggestions,
            follow_up_questions=[follow_up],
            weak_topics=[] if tech_score >= 75 else [question.topic],
            strong_topics=matched_skills or question.expected_skills[:1],
        )

    @classmethod
    def fallback_rule_based_report(cls, session: InterviewSessionBase) -> InterviewReport:
        """
        100% deterministic rule-based interview report synthesis.
        """
        evals = session.evaluations
        if not evals:
            return InterviewReport(
                overall_score=0,
                executive_summary="Interview session has no completed evaluations.",
            )

        tech_avg = int(sum(e.technical_score for e in evals) / len(evals))
        comm_avg = int(sum(e.communication_score for e in evals) / len(evals))
        conf_avg = int(sum(e.confidence_score for e in evals) / len(evals))
        prob_avg = int(sum(e.problem_solving_score for e in evals) / len(evals))
        overall = int((tech_avg * 0.35) + (comm_avg * 0.25) + (prob_avg * 0.25) + (conf_avg * 0.15))

        if overall >= 85:
            readiness = "Interview Ready"
            recommendation = "Strong Hire"
        elif overall >= 75:
            readiness = "Proficient"
            recommendation = "Hire"
        elif overall >= 65:
            readiness = "Developing"
            recommendation = "Consider"
        else:
            readiness = "Foundational"
            recommendation = "Needs Development"

        strengths: List[str] = []
        weaknesses: List[str] = []
        for e in evals:
            for s in e.strong_topics:
                if s not in strengths and len(strengths) < 5:
                    strengths.append(s)
            for w in e.weak_topics:
                if w not in weaknesses and len(weaknesses) < 5:
                    weaknesses.append(w)

        if not strengths:
            strengths = ["Strong core technical communication", "Consistent structured reasoning"]
        if not weaknesses:
            weaknesses = ["Deep performance tuning under high load"]

        summary = f"Candidate scored {overall}% overall ({readiness} / {recommendation}) across {len(evals)} interview questions for {session.role}."

        return InterviewReport(
            overall_score=overall,
            technical_score=tech_avg,
            communication_score=comm_avg,
            confidence_score=conf_avg,
            problem_solving_score=prob_avg,
            interview_readiness=readiness,
            hiring_recommendation=recommendation,
            strengths=strengths,
            weaknesses=weaknesses,
            missed_concepts=weaknesses,
            learning_priorities=[f"Advanced {w} architecture" for w in weaknesses[:2]],
            recommended_projects=[f"Build an end-to-end {session.role} production service"],
            recommended_certifications=[],
            executive_summary=summary,
        )

    # --- Helper context extractors ---

    @staticmethod
    def _extract_context_skills(context: Dict[str, Any]) -> List[str]:
        skills: List[str] = []
        # From memory
        memory = context.get("memory")
        if memory and isinstance(memory, dict):
            for key in ["core_skills", "emerging_skills"]:
                arr = memory.get(key)
                if arr and isinstance(arr, list):
                    for item in arr:
                        if isinstance(item, str) and item not in skills:
                            skills.append(item)
        # From resume
        resume = context.get("resume")
        if resume and isinstance(resume, dict):
            parsed = resume.get("parsed_data", {}) if "parsed_data" in resume else resume
            r_skills = parsed.get("skills", [])
            if isinstance(r_skills, list):
                for item in r_skills:
                    if isinstance(item, str) and item not in skills:
                        skills.append(item)
        # From profile
        profile = context.get("profile")
        if profile and isinstance(profile, dict):
            p_skills = profile.get("skills", [])
            if isinstance(p_skills, list):
                for item in p_skills:
                    if isinstance(item, str) and item not in skills:
                        skills.append(item)
        return skills

    @staticmethod
    def _extract_resume_summary(context: Dict[str, Any]) -> str:
        resume = context.get("resume")
        if not resume or not isinstance(resume, dict):
            return "No resume uploaded."
        parsed = resume.get("parsed_data", {}) if "parsed_data" in resume else resume
        exp = parsed.get("experience", [])
        roles = []
        if isinstance(exp, list):
            for e in exp[:3]:
                if isinstance(e, dict):
                    role_name = e.get("role") or e.get("title") or "Engineer"
                    roles.append(str(role_name))
        return f"{len(exp)} professional roles verified: {', '.join(roles)}." if roles else "Experienced software professional."

    @staticmethod
    def _extract_github_summary(context: Dict[str, Any]) -> str:
        gh = context.get("github_analysis")
        if not gh or not isinstance(gh, dict):
            return "No GitHub analysis available."
        analysis = gh.get("analysis", {}) if "analysis" in gh else gh
        score = gh.get("github_score") or analysis.get("score", 75)
        langs = gh.get("top_languages") or analysis.get("top_languages", [])
        return f"GitHub Score {score}/100. Top languages: {', '.join([str(l) for l in langs[:4]])}."
