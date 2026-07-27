import json
import re
import logging
from typing import Tuple, Dict, Any, List

from models.digital_twin_memory import DigitalTwinSummaryResponse
from ai.llm_provider import get_llm_provider
from utils.logger import get_logger

logger = get_logger("digital_twin.ai")


class DigitalTwinMemoryAIService:
    """
    AI summarization and insight synthesis service for the Digital Twin Memory Engine.
    Uses Google Gemini with deterministic fallback so memory summarization never fails.
    """

    @classmethod
    async def summarize_memory(
        cls,
        user_id: str,
        memory_doc: Dict[str, Any],
    ) -> Tuple[DigitalTwinSummaryResponse, str]:
        """
        Synthesizes the user's accumulated Digital Twin memory into an executive career summary.
        Returns (DigitalTwinSummaryResponse, analysis_method).
        """
        try:
            logger.info(f"[DigitalTwinMemoryAI] Generating AI memory summary for user={user_id}")
            prompt = cls._build_summary_prompt(memory_doc)

            llm = get_llm_provider()
            raw_text = await llm.generate_text(
                prompt=prompt,
                system_instruction=(
                    "You are the OMNI Digital Twin AI Career Synthesizer. "
                    "Analyze the candidate's persistent career memory and output only valid JSON matching the requested schema."
                ),
            )

            cleaned_text = raw_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            data = json.loads(cleaned_text)
            summary = DigitalTwinSummaryResponse(
                executive_summary=data.get("executive_summary", "Professional candidate profile synthesized from persistent memory."),
                top_strengths=data.get("top_strengths", [])[:5],
                primary_skill_gaps=data.get("primary_skill_gaps", [])[:5],
                recommended_trajectory=data.get("recommended_trajectory", "Continue technical depth and domain specialization."),
                confidence_score=float(data.get("confidence_score", 0.90)),
                key_milestones=data.get("key_milestones", [])[:5],
                generated_by="ai",
                confidence=0.90,
            )
            return summary, "ai"

        except Exception as e:
            logger.warning(f"[DigitalTwinMemoryAI] AI summarization failed, using rule-based fallback: {str(e)}")
            summary = cls.fallback_rule_based_summary(memory_doc)
            return summary, "rule_based"

    @classmethod
    def fallback_rule_based_summary(
        cls,
        memory_doc: Dict[str, Any],
    ) -> DigitalTwinSummaryResponse:
        """
        Deterministic summary generation from stored memory attributes.
        Guarantees 100% availability without HTTP 500 errors.
        """
        current_role = memory_doc.get("current_role") or "Software Professional"
        target_roles = memory_doc.get("target_roles", [])
        core_skills = memory_doc.get("core_skills", [])
        missing_skills = memory_doc.get("missing_skills", [])
        timeline = memory_doc.get("timeline", [])

        # Construct executive summary text
        role_str = f"{current_role}"
        if target_roles:
            role_str += f" targeting {' / '.join(target_roles[:2])}"
        skills_str = ", ".join(core_skills[:6]) if core_skills else "various technical competencies"

        exec_summary = (
            f"{role_str} with expertise in {skills_str}. "
            f"Accumulated {len(timeline)} verified milestones across OMNI Digital Twin intelligence modules."
        )

        top_strengths: List[str] = []
        for s in memory_doc.get("github_strengths", [])[:2]:
            if s not in top_strengths:
                top_strengths.append(s)
        for s in memory_doc.get("resume_strengths", [])[:2]:
            if s not in top_strengths:
                top_strengths.append(s)
        for s in memory_doc.get("career_strengths", [])[:2]:
            if s not in top_strengths:
                top_strengths.append(s)
        if not top_strengths and core_skills:
            top_strengths = core_skills[:4]

        milestone_texts: List[str] = []
        for event in timeline[-5:]:
            if isinstance(event, dict):
                m_text = f"{event.get('date', '')}: {event.get('event', '')}".strip(": ")
                if m_text:
                    milestone_texts.append(m_text)
            elif hasattr(event, "event"):
                milestone_texts.append(f"{event.date}: {event.event}")

        trajectory = "Senior Technical Leadership" if len(timeline) >= 4 else "Skill Consolidation & Role Alignment"
        if target_roles:
            trajectory = f"Progression toward {target_roles[0]}"

        # Compute dynamic confidence based on memory richness
        confidence_val = min(0.95, 0.70 + (0.05 * min(5, len(timeline))))

        return DigitalTwinSummaryResponse(
            executive_summary=exec_summary,
            top_strengths=top_strengths,
            primary_skill_gaps=missing_skills[:5],
            recommended_trajectory=trajectory,
            confidence_score=round(confidence_val, 2),
            key_milestones=milestone_texts,
            generated_by="rule_based",
            confidence=round(confidence_val, 2),
        )

    @staticmethod
    def _build_summary_prompt(memory_doc: Dict[str, Any]) -> str:
        return f"""
Analyze the following OMNI Digital Twin persistent memory and generate a concise executive career summary.

Candidate Current Role: {memory_doc.get('current_role', 'Not specified')}
Target Roles: {memory_doc.get('target_roles', [])}
Core Skills: {memory_doc.get('core_skills', [])}
Emerging Skills: {memory_doc.get('emerging_skills', [])}
Missing Skills / Gaps: {memory_doc.get('missing_skills', [])}
Preferred Companies: {memory_doc.get('preferred_companies', [])}
Preferred Domains: {memory_doc.get('preferred_domains', [])}
GitHub Strengths: {memory_doc.get('github_strengths', [])}
Resume Strengths: {memory_doc.get('resume_strengths', [])}
Career Strengths: {memory_doc.get('career_strengths', [])}
ATS History Summaries: {memory_doc.get('ats_history_summary', [])}
Job Matching Summaries: {memory_doc.get('job_matching_summary', [])}
Timeline Milestones Count: {len(memory_doc.get('timeline', []))}

Respond STRICTLY with valid JSON in the following format:
{{
  "executive_summary": "2-3 professional sentences summarizing candidate profile and career readiness.",
  "top_strengths": ["Strength 1", "Strength 2", "Strength 3", "Strength 4"],
  "primary_skill_gaps": ["Gap 1", "Gap 2", "Gap 3"],
  "recommended_trajectory": "Concise trajectory statement (e.g. Progression to Staff Engineer in FinTech)",
  "confidence_score": 0.92,
  "key_milestones": ["Milestone 1 description", "Milestone 2 description"]
}}
"""
