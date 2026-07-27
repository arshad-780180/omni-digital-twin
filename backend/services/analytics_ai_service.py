import json
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from models.analytics import ExecutiveInsights
from ai.llm_provider import get_llm_provider

logger = logging.getLogger("omni.analytics.ai")


class AnalyticsAIService:
    """
    AI Executive Insights Engine for Phase 9 Analytics Dashboard with 100% deterministic rule-based fallback.
    Synthesizes executive summaries, strengths, weakest areas, biggest improvements, career risks,
    recommended actions, and readiness estimates from aggregated Digital Twin analytics.
    """

    @classmethod
    async def generate_executive_insights(
        cls,
        user_id: str,
        context: Dict[str, Any],
        analytics_data: Dict[str, Any],
    ) -> ExecutiveInsights:
        """
        Generates executive career insights using Google Gemini AI, with automatic
        fallback to deterministic heuristic rules if AI generation fails.
        """
        try:
            provider = get_llm_provider()

            # Extract user context details
            prof = context.get("profile") or {}
            mem = context.get("memory") or {}
            target_role = prof.get("target_role") or "Senior Software Engineer"
            core_skills = mem.get("core_skills") or prof.get("skills") or ["Python", "System Design"]
            missing_skills = mem.get("missing_skills") or ["Kubernetes", "Cloud Architecture"]

            # Extract numerical analytics
            overall = analytics_data.get("overall_career_health_score", 75)
            readiness = analytics_data.get("career_readiness_score", 70)
            ats = analytics_data.get("ats_score", 65)
            job_match = analytics_data.get("job_match_score", 72)
            interview = analytics_data.get("interview_score", 75)
            learning_pct = analytics_data.get("learning_progress", 40.0)

            prompt = f"""
You are OMNI AI Executive Career Intelligence Advisor. Analyze the candidate's complete Digital Twin metrics and provide an executive summary.

Candidate Profile:
- Target Role: {target_role}
- Core Skills: {', '.join(core_skills[:8])}
- Missing Skills / Gaps: {', '.join(missing_skills[:6])}

Aggregated Numerical Scores:
- Overall Career Health Score: {overall}/100
- Career Readiness Score: {readiness}/100
- ATS Resume Optimization Score: {ats}/100
- Job Match Fit Score: {job_match}/100
- Mock Interview Performance Score: {interview}/100
- Learning Roadmap Progress: {learning_pct}%

Return a strictly valid JSON object adhering to the following schema:
{{
  "current_strengths": ["string (2 to 4 bullet points representing top demonstrated competencies)"],
  "weakest_areas": ["string (2 to 3 bullet points representing critical gaps or low-scoring areas)"],
  "biggest_improvement": "string (one concise sentence summarizing the candidate's most significant trajectory gain)",
  "career_risks": ["string (1 to 3 bullet points identifying potential risks if gaps remain unaddressed)"],
  "recommended_next_action": "string (one clear, highly actionable recommendation for the candidate's next step in OMNI)",
  "estimated_readiness": "string (e.g., '82% - Highly competitive for target role within 3 weeks')"
}}

Do NOT include markdown backticks or extra formatting. Return valid JSON only.
"""
            raw_text = await provider.generate_text(prompt)
            clean_json = cls._clean_json(raw_text)
            data = json.loads(clean_json)
            data["ai_generated"] = True
            return ExecutiveInsights.model_validate(data)

        except Exception as e:
            logger.warning(
                f"[AnalyticsAI] Notice: AI executive insights generation failed ({str(e)}). "
                "Using 100% deterministic rule-based fallback."
            )
            return cls.fallback_generate_insights(user_id, context, analytics_data)

    @classmethod
    def fallback_generate_insights(
        cls,
        user_id: str,
        context: Dict[str, Any],
        analytics_data: Dict[str, Any],
    ) -> ExecutiveInsights:
        """
        100% deterministic rule-based fallback for Executive Insights.
        Synthesizes strengths, weakest areas, improvement, risks, and next action from actual scores.
        """
        prof = context.get("profile") or {}
        mem = context.get("memory") or {}
        core_skills = mem.get("core_skills") or prof.get("skills") or ["Python", "FastAPI", "SQL"]
        missing_skills = mem.get("missing_skills") or ["Kubernetes", "System Design", "Cloud Infrastructure"]

        overall = int(analytics_data.get("overall_career_health_score", 75))
        readiness = int(analytics_data.get("career_readiness_score", 70))
        ats = int(analytics_data.get("ats_score", 65))
        job_match = int(analytics_data.get("job_match_score", 70))
        interview = int(analytics_data.get("interview_score", 75))
        learning_pct = float(analytics_data.get("learning_progress", 40.0))

        # Determine current strengths
        strengths = []
        if readiness >= 75:
            strengths.append(f"Strong overall career readiness footprint ({readiness}/100)")
        if interview >= 75:
            strengths.append(f"High proficiency in technical mock interview communication ({interview}/100)")
        if core_skills:
            strengths.append(f"Demonstrated mastery in core engineering competencies: {', '.join(core_skills[:3])}")
        if len(strengths) < 2:
            strengths.append("Verified GitHub repository portfolio and structured resume presentation")
            strengths.append("Consistent engagement with Digital Twin career intelligence tools")

        # Determine weakest areas
        weaknesses = []
        if ats < 70:
            weaknesses.append(f"ATS resume keyword match percentage requires optimization ({ats}/100)")
        if learning_pct < 50.0:
            weaknesses.append(f"Learning roadmap milestone completion is in early stages ({learning_pct:.0f}%)")
        if missing_skills:
            weaknesses.append(f"Identified skill gaps for target roles: {', '.join(missing_skills[:3])}")
        if len(weaknesses) < 2:
            weaknesses.append("Advanced system design architecture patterns for large-scale distributed systems")
            weaknesses.append("Specialized domain certifications for senior leadership roles")

        # Determine biggest improvement
        if interview >= ats and interview >= readiness:
            improvement = "Consistent upward trajectory in technical problem-solving and mock interview communication"
        elif learning_pct >= 50.0:
            improvement = "Rapid acquisition of core engineering skills via structured learning milestones"
        else:
            improvement = "Unified professional footprint aggregation across GitHub, Resume, and Profile intelligence"

        # Determine career risks
        risks = []
        if ats < 65:
            risks.append("Unresolved ATS keyword gaps could result in early resume screening rejections")
        if len(missing_skills) >= 3:
            risks.append("Targeting advanced roles without formal demonstration of cloud or containerization tools")
        if len(risks) == 0:
            risks.append("Increasing competition in target roles requires continuous portfolio and GitHub updates")

        # Determine recommended next action
        scores_map = {
            "ATS Resume Optimization": ats,
            "Mock Interview Practice": interview,
            "Learning Roadmap Milestones": int(learning_pct),
            "Job Matching Evaluation": job_match,
        }
        lowest_area = min(scores_map, key=scores_map.get)
        if lowest_area == "ATS Resume Optimization":
            next_action = "Run an ATS resume optimization audit against your target job description to improve keyword coverage."
        elif lowest_area == "Mock Interview Practice":
            next_action = "Complete a personalized AI mock interview session focusing on System Design and technical communication."
        elif lowest_area == "Learning Roadmap Milestones":
            next_action = "Check off your next technical milestone in the AI Career Mentor roadmap to accelerate readiness score."
        else:
            next_action = "Evaluate your Digital Twin fit against target job descriptions to identify specific missing competencies."

        # Estimated readiness
        if overall >= 80:
            est_readiness = f"{overall}% - Interview Ready within 1 to 2 weeks for target roles"
        elif overall >= 65:
            est_readiness = f"{overall}% - Proficient candidate; on track for target role within 4 weeks"
        else:
            est_readiness = f"{overall}% - Developing footprint; recommended completion of learning roadmap milestones"

        return ExecutiveInsights(
            current_strengths=strengths,
            weakest_areas=weaknesses,
            biggest_improvement=improvement,
            career_risks=risks,
            recommended_next_action=next_action,
            estimated_readiness=est_readiness,
            ai_generated=False,
        )

    @staticmethod
    def _clean_json(text: str) -> str:
        """
        Strips markdown formatting or backticks from raw LLM responses.
        """
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        return text.strip()
