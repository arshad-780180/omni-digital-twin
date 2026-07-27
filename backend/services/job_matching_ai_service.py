import re
import json
import logging
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime, timezone

from ai.llm_provider import get_llm_provider
from models.job_match import (
    JobMatchAnalyzeRequest,
    JobMatchAnalysisResponse,
    JobRequirements,
    RoleRecommendationItem,
    LearningGapItem,
    SalaryInsights,
    AICareerAdvice,
)

logger = logging.getLogger("omni.ai.job_match")

# Common technical keywords for requirement extraction in fallback engine
COMMON_TECH_KEYWORDS = {
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust", "ruby", "php", "swift", "kotlin",
    "react", "angular", "vue", "next.js", "node.js", "express", "fastapi", "django", "flask", "spring",
    "docker", "kubernetes", "aws", "gcp", "azure", "terraform", "ci/cd", "git", "linux",
    "mongodb", "postgresql", "mysql", "redis", "elasticsearch", "sql", "graphql", "rest", "api",
    "machine learning", "deep learning", "ai", "nlp", "llm", "pytorch", "tensorflow",
}


class JobMatchingAIService:
    @classmethod
    async def analyze_job_match(
        cls,
        user_id: str,
        digital_twin_context: Dict[str, Any],
        request: JobMatchAnalyzeRequest,
    ) -> Tuple[JobMatchAnalysisResponse, str]:
        """
        Executes Gemini AI Job Matching evaluation against Digital Twin context.
        If Gemini fails, automatically falls back to deterministic matching.
        """
        resume_doc = digital_twin_context.get("resume") or {}
        profile_doc = digital_twin_context.get("profile") or {}
        github_doc = digital_twin_context.get("github") or {}
        career_doc = digital_twin_context.get("career") or {}
        ats_doc = digital_twin_context.get("ats") or {}

        # Collect user skills for prompt
        user_skills: List[str] = []
        if "parsed_data" in resume_doc and isinstance(resume_doc["parsed_data"], dict):
            user_skills.extend(resume_doc["parsed_data"].get("skills", []))
        if "skills" in profile_doc and isinstance(profile_doc["skills"], list):
            user_skills.extend(profile_doc["skills"])
        user_skills = list(set(user_skills))

        user_summary = "An ambitious software engineering professional."
        if "parsed_data" in resume_doc and isinstance(resume_doc["parsed_data"], dict):
            user_summary = resume_doc["parsed_data"].get("summary", user_summary)
        elif "bio" in profile_doc:
            user_summary = profile_doc.get("bio", user_summary)

        prompt = f"""
You are an expert AI Job Matching and Technical Recruiting Engine.
Analyze how well the candidate's Digital Twin aligns with the following target Job Description.

TARGET JOB OPPORTUNITY:
- Title: {request.job_title}
- Company: {request.company}
- Location: {request.location}
- Employment Type: {request.employment_type}
- Job Description:
{request.job_description}

CANDIDATE DIGITAL TWIN PROFILE:
- Skills: {', '.join(user_skills[:25]) if user_skills else 'General Software Development'}
- Professional Summary: {user_summary}
- GitHub Intelligence Score: {github_doc.get('analysis', {}).get('github_score', 'N/A')}
- Career Readiness Score: {career_doc.get('career_score', 'N/A')}

Generate a comprehensive, structured JSON response with NO extra commentary or markdown outside the JSON block.
The JSON MUST match this exact schema:
{{
  "overall_job_match_score": int (0-100),
  "technical_match_score": int (0-100),
  "experience_match_score": int (0-100),
  "education_match_score": int (0-100),
  "project_relevance_score": int (0-100),
  "skill_coverage_percentage": int (0-100),
  "missing_skills": ["skill1", "skill2"],
  "matched_skills": ["skill1", "skill2"],
  "missing_technologies": ["tech1", "tech2"],
  "strength_areas": ["area1", "area2"],
  "weak_areas": ["area1", "area2"],
  "career_readiness": "Beginner | Intermediate | Placement Ready | Advanced",
  "hiring_recommendation": "Strong Hire | Hire | Consider | Needs Development",
  "requirements": {{
    "required_skills": ["skill1", ...],
    "preferred_skills": ["skill1", ...],
    "frameworks": ["frame1", ...],
    "programming_languages": ["lang1", ...],
    "cloud_platforms": ["cloud1", ...],
    "databases": ["db1", ...],
    "soft_skills": ["soft1", ...],
    "experience_requirements": ["exp1", ...],
    "education_requirements": ["edu1", ...],
    "responsibilities": ["resp1", ...]
  }},
  "recommended_roles": [
    {{
      "role_name": "{request.job_title}",
      "category": "best_matching",
      "match_percentage": int (0-100),
      "explanation": "Why this role fits"
    }},
    {{
      "role_name": "Alternative Role",
      "category": "alternative",
      "match_percentage": int (0-100),
      "explanation": "Why this alternative fits"
    }},
    {{
      "role_name": "Stretch Role",
      "category": "stretch",
      "match_percentage": int (0-100),
      "explanation": "Why this stretch fits"
    }},
    {{
      "role_name": "Role To Avoid",
      "category": "avoid",
      "match_percentage": int (0-100),
      "explanation": "Why to avoid"
    }}
  ],
  "learning_plan": [
    {{
      "skill": "missing skill",
      "priority_order": 1,
      "estimated_difficulty": "Easy | Medium | Hard",
      "learning_timeline": "2 weeks",
      "reasoning": "Why learn this skill"
    }}
  ],
  "salary_estimate": {{
    "junior_range": "$70,000 - $90,000",
    "mid_level_range": "$95,000 - $125,000",
    "senior_range": "$130,000 - $165,000",
    "confidence_level": "High | Medium | Low",
    "disclaimer": "These salary ranges are estimates derived from profile metrics and market assumptions, not guaranteed offers."
  }},
  "career_advice": {{
    "executive_summary": "Executive summary of candidacy",
    "interview_preparation_advice": ["tip1", ...],
    "project_suggestions": ["proj1", ...],
    "certification_suggestions": ["cert1", ...],
    "portfolio_improvements": ["port1", ...],
    "resume_improvements": ["res1", ...],
    "github_improvements": ["git1", ...]
  }}
}}
"""

        try:
            llm = get_llm_provider()
            response_text = await llm.generate_text(prompt)
            cleaned_text = re.sub(r"```json|```", "", response_text).strip()
            data = json.loads(cleaned_text)

            # Ensure required fields and valid ranges
            data["user_id"] = user_id
            data["job_title"] = request.job_title
            data["company"] = request.company
            data["location"] = request.location or ""
            data["employment_type"] = request.employment_type or ""
            data["job_description"] = request.job_description
            data["analysis_method"] = "ai"

            # Validate against Pydantic schema
            analysis = JobMatchAnalysisResponse.model_validate(data)
            return analysis, "ai"

        except Exception as e:
            logger.warning(
                f"[JobMatchingAIService] Gemini AI failed ({str(e)}). Using deterministic rule-based fallback."
            )
            return cls.fallback_rule_based_job_match(user_id, digital_twin_context, request), "rule_based"

    @classmethod
    def fallback_rule_based_job_match(
        cls,
        user_id: str,
        digital_twin_context: Dict[str, Any],
        request: JobMatchAnalyzeRequest,
    ) -> JobMatchAnalysisResponse:
        """
        Deterministic rule-based job matching fallback when Gemini API fails or rate limits.
        Computes keyword overlap, skill coverage %, experience/education alignment, and generates
        actionable role recommendations and learning plans.
        """
        resume_doc = digital_twin_context.get("resume") or {}
        profile_doc = digital_twin_context.get("profile") or {}
        github_doc = digital_twin_context.get("github") or {}

        # 1. Gather Candidate Skills
        user_skills: List[str] = []
        if "parsed_data" in resume_doc and isinstance(resume_doc["parsed_data"], dict):
            user_skills.extend(resume_doc["parsed_data"].get("skills", []))
        if "skills" in profile_doc and isinstance(profile_doc["skills"], list):
            user_skills.extend(profile_doc["skills"])
        user_skills = list(set([s.strip().lower() for s in user_skills if isinstance(s, str)]))

        # 2. Extract keywords from Job Description
        jd_lower = request.job_description.lower()
        required_keywords = []
        for kw in COMMON_TECH_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", jd_lower):
                required_keywords.append(kw)

        if not required_keywords:
            required_keywords = ["python", "api", "git", "sql"]

        matched_skills = [s for s in required_keywords if any(s in us or us in s for us in user_skills)]
        missing_skills = [s for s in required_keywords if s not in matched_skills]

        # 3. Compute Multi-Dimensional Scores
        coverage_pct = int((len(matched_skills) / max(1, len(required_keywords))) * 100)
        coverage_pct = max(10, min(100, coverage_pct))

        technical_score = coverage_pct
        experience_score = min(95, 60 + len(matched_skills) * 5)
        education_score = 80 if resume_doc else 70

        projects = []
        if "parsed_data" in resume_doc and isinstance(resume_doc["parsed_data"], dict):
            projects = resume_doc["parsed_data"].get("projects", [])
        project_score = min(95, 65 + len(projects) * 6)

        overall_score = int(
            0.40 * technical_score
            + 0.25 * experience_score
            + 0.15 * education_score
            + 0.20 * project_score
        )
        overall_score = max(15, min(98, overall_score))

        # 4. Readiness & Recommendation
        if overall_score >= 85:
            career_readiness = "Advanced"
            hiring_rec = "Strong Hire"
        elif overall_score >= 75:
            career_readiness = "Placement Ready"
            hiring_rec = "Hire"
        elif overall_score >= 60:
            career_readiness = "Intermediate"
            hiring_rec = "Consider"
        else:
            career_readiness = "Beginner"
            hiring_rec = "Needs Development"

        # 5. Populate Requirements
        requirements = JobRequirements(
            required_skills=[kw.title() for kw in required_keywords],
            preferred_skills=[kw.title() for kw in missing_skills[:3]],
            frameworks=[kw.title() for kw in required_keywords if kw in {"react", "angular", "vue", "next.js", "express", "fastapi", "django", "flask", "spring"}],
            programming_languages=[kw.title() for kw in required_keywords if kw in {"python", "javascript", "typescript", "java", "c++", "c#", "go", "rust", "ruby", "php", "swift", "kotlin"}],
            cloud_platforms=[kw.title() for kw in required_keywords if kw in {"aws", "gcp", "azure"}],
            databases=[kw.title() for kw in required_keywords if kw in {"mongodb", "postgresql", "mysql", "redis", "elasticsearch", "sql", "graphql"}],
            soft_skills=["Communication", "Teamwork", "Problem Solving"],
            experience_requirements=["Relevant software development background"],
            education_requirements=["Bachelor's in Computer Science or equivalent practical experience"],
            responsibilities=["Design and implement scalable software architectures", "Collaborate with cross-functional teams"],
        )

        # 6. Role Recommendations
        recommended_roles = [
            RoleRecommendationItem(
                role_name=request.job_title,
                category="best_matching",
                match_percentage=overall_score,
                explanation=f"Direct target role matching {coverage_pct}% of required technical skills.",
            ),
            RoleRecommendationItem(
                role_name="Software Engineer",
                category="alternative",
                match_percentage=max(60, overall_score - 5),
                explanation="Alternative role leveraging core software engineering principles and foundational skills.",
            ),
            RoleRecommendationItem(
                role_name="Senior Staff Architect",
                category="stretch",
                match_percentage=max(40, overall_score - 20),
                explanation="Stretch leadership role requiring deeper system design and multi-team technical strategy.",
            ),
            RoleRecommendationItem(
                role_name="Legacy Systems Support Specialist",
                category="avoid",
                match_percentage=35,
                explanation="Avoid roles with outdated stacks that do not align with modern software growth goals.",
            ),
        ]

        # 7. Learning Plan
        learning_plan = []
        for idx, skill in enumerate(missing_skills[:5], 1):
            learning_plan.append(
                LearningGapItem(
                    skill=skill.title(),
                    priority_order=idx,
                    estimated_difficulty="Medium" if idx > 2 else "Easy",
                    learning_timeline="2 weeks" if idx <= 2 else "4 weeks",
                    reasoning=f"High-priority skill required for {request.job_title} alignment.",
                )
            )
        if not learning_plan:
            learning_plan.append(
                LearningGapItem(
                    skill="System Architecture Design",
                    priority_order=1,
                    estimated_difficulty="Medium",
                    learning_timeline="3 weeks",
                    reasoning="Enhance leadership and high-scale architecture competence.",
                )
            )

        # 8. Salary Insights & Advice
        salary_estimate = SalaryInsights(
            junior_range="$70,000 - $90,000",
            mid_level_range="$95,000 - $125,000",
            senior_range="$130,000 - $165,000",
            confidence_level="High" if resume_doc else "Medium",
            disclaimer="These salary ranges are estimates derived from profile metrics and market assumptions, not guaranteed offers.",
        )

        career_advice = AICareerAdvice(
            executive_summary=f"Candidate demonstrates {career_readiness.lower()} readiness with a {coverage_pct}% skill match for {request.job_title} at {request.company or 'target organization'}.",
            interview_preparation_advice=[
                f"Prepare behavioral stories demonstrating experience with {', '.join([s.title() for s in matched_skills[:3]])}." if matched_skills else "Highlight your core problem-solving methodologies.",
                "Review system design trade-offs and latency optimization benchmarks.",
            ],
            project_suggestions=[
                f"Build a full-stack portfolio project integrating {missing_skills[0].title() if missing_skills else 'cloud microservices'} with automated tests."
            ],
            certification_suggestions=[
                "AWS Certified Solutions Architect" if "aws" in jd_lower else "Professional Cloud Developer Certification"
            ],
            portfolio_improvements=[
                "Add live deployment demos and GitHub repository README architecture diagrams."
            ],
            resume_improvements=[
                "Quantify bullet points with latency improvements, cost reductions, and user scale metrics."
            ],
            github_improvements=[
                "Pin top projects with clean CI/CD pipelines and comprehensive unit test coverage."
            ],
        )

        return JobMatchAnalysisResponse(
            user_id=user_id,
            job_title=request.job_title,
            company=request.company,
            location=request.location or "",
            employment_type=request.employment_type or "",
            job_description=request.job_description,
            overall_job_match_score=overall_score,
            technical_match_score=technical_score,
            experience_match_score=experience_score,
            education_match_score=education_score,
            project_relevance_score=project_score,
            skill_coverage_percentage=coverage_pct,
            missing_skills=[kw.title() for kw in missing_skills],
            matched_skills=[kw.title() for kw in matched_skills],
            missing_technologies=[kw.title() for kw in missing_skills],
            strength_areas=[kw.title() for kw in matched_skills[:4]] if matched_skills else ["Core Programming"],
            weak_areas=[kw.title() for kw in missing_skills[:4]] if missing_skills else ["Advanced System Scaling"],
            career_readiness=career_readiness,
            hiring_recommendation=hiring_rec,
            requirements=requirements,
            recommended_roles=recommended_roles,
            learning_plan=learning_plan,
            salary_estimate=salary_estimate,
            career_advice=career_advice,
            analysis_method="rule_based",
        )
