import re
import json
from typing import Tuple, Dict, Any, List
from models.career import CareerAnalysis, CareerScoreBreakdown
from ai.llm_provider import get_llm_provider


class CareerAIService:
    @classmethod
    async def analyze_career(
        cls,
        user_id: str,
        resume_doc: Dict[str, Any],
        github_doc: Dict[str, Any],
        profile_doc: Dict[str, Any]
    ) -> Tuple[CareerAnalysis, str]:
        """
        Analyzes merged career footprint from Phase 1 (Resume), Phase 2 (GitHub), and User Profile.
        Returns (CareerAnalysis, analysis_method).
        """
        # Prepare summaries for prompt
        resume_summary = "None available"
        resume_skills: List[str] = []
        if resume_doc and "parsed_data" in resume_doc:
            parsed = resume_doc["parsed_data"]
            resume_skills = parsed.get("skills", [])
            resume_summary = (
                f"Name: {parsed.get('name', 'N/A')}, "
                f"Experience: {len(parsed.get('experience', []))} roles, "
                f"Projects: {len(parsed.get('projects', []))} projects, "
                f"Skills: {', '.join(resume_skills[:15])}"
            )

        github_summary = "None available"
        github_score_val = 60
        if github_doc and "analysis" in github_doc:
            gh_ana = github_doc["analysis"]
            github_score_val = gh_ana.get("github_score", 70)
            github_summary = (
                f"Developer Level: {gh_ana.get('developer_level', 'Mid-Level')}, "
                f"GitHub Score: {github_score_val}/100, "
                f"Strengths: {', '.join(gh_ana.get('strengths', [])[:5])}, "
                f"Repos analyzed: {len(github_doc.get('repositories', []))}"
            )
        elif github_doc and "total_repos" in github_doc:
            github_summary = f"Total Repos: {github_doc.get('total_repos', 0)}, Languages: {len(github_doc.get('top_languages', []))}"

        profile_skills: List[str] = []
        if profile_doc and "skills" in profile_doc:
            profile_skills = [str(s) for s in profile_doc.get("skills", [])]

        all_skills = list(set(resume_skills + profile_skills))

        prompt = f"""
You are an expert Principal AI Career Readiness & Placement Evaluator. Analyze the candidate's complete professional digital twin footprint below (including Resume, GitHub portfolio, and Profile skills) and generate a comprehensive Career Readiness Report.

Return strictly a valid JSON object matching the schema below, with no markdown code fences or extra text.

Schema:
{{
  "overall_score": 86,
  "breakdown": {{
    "technical_score": 91,
    "resume_score": 84,
    "github_score": {github_score_val},
    "project_score": 82,
    "communication_score": 73
  }},
  "career_level": "Beginner | Intermediate | Placement Ready | Advanced",
  "strengths": ["Python", "FastAPI", "REST APIs", "Backend Development"],
  "weaknesses": ["Testing", "Docker", "Cloud", "CI/CD"],
  "missing_skills": ["Docker", "Redis", "AWS", "Kubernetes", "RabbitMQ"],
  "recommended_roles": ["Backend Developer", "Python Developer", "AI Engineer"],
  "summary": "Candidate demonstrates strong backend development capability with Python and FastAPI..."
}}

Candidate Data:
- Resume Profile: {resume_summary}
- GitHub Intelligence: {github_summary}
- Aggregated Profile Skills: {', '.join(all_skills[:20]) if all_skills else 'None listed'}
"""

        try:
            llm = get_llm_provider()
            response_text = await llm.generate_text(prompt)
            cleaned_text = re.sub(r'```json|```', '', response_text).strip()
            data = json.loads(cleaned_text)
            analysis = CareerAnalysis.model_validate(data)
            return analysis, "ai"
        except Exception as e:
            print(f"[CareerAIService] AI analysis failed ({e}). Using rule-based fallback.")
            fallback = cls.fallback_rule_based_career(resume_doc, github_doc, profile_doc)
            return fallback, "rule_based"

    @staticmethod
    def fallback_rule_based_career(
        resume_doc: Dict[str, Any],
        github_doc: Dict[str, Any],
        profile_doc: Dict[str, Any]
    ) -> CareerAnalysis:
        """
        Deterministic rule-based fallback engine using suggested weighting:
        Resume: 30%, GitHub: 30%, Projects: 20%, Profile: 20%.
        Never crashes, always returns a valid response.
        """
        # 1. Resume Score (30%)
        res_score = 50
        resume_skills: List[str] = []
        if resume_doc and "parsed_data" in resume_doc:
            parsed = resume_doc["parsed_data"]
            resume_skills = parsed.get("skills", [])
            res_score = min(95, 60 + len(resume_skills) * 2 + len(parsed.get("experience", [])) * 5)
        elif resume_doc:
            res_score = 65

        # 2. GitHub Score (30%)
        gh_score = 50
        if github_doc and "analysis" in github_doc:
            gh_score = github_doc["analysis"].get("github_score", 70)
        elif github_doc and "total_repos" in github_doc:
            gh_score = min(95, 50 + github_doc.get("total_repos", 0) * 3)

        # 3. Project Score (20%)
        proj_score = 60
        if resume_doc and "parsed_data" in resume_doc:
            num_projs = len(resume_doc["parsed_data"].get("projects", []))
            proj_score = min(95, 65 + num_projs * 8)
        if github_doc and "repositories" in github_doc:
            num_repos = len(github_doc.get("repositories", []))
            proj_score = max(proj_score, min(95, 65 + num_repos * 4))

        # 4. Profile Score (20%)
        prof_score = 50
        profile_skills: List[str] = []
        if profile_doc and "skills" in profile_doc:
            profile_skills = [str(s) for s in profile_doc.get("skills", [])]
            prof_score = min(95, 60 + len(profile_skills) * 3)
        elif profile_doc:
            prof_score = 65

        # Calculate weighted Overall Score
        overall_score = int(0.30 * res_score + 0.30 * gh_score + 0.20 * proj_score + 0.20 * prof_score)

        # Technical & Communication estimates
        technical_score = int((gh_score + proj_score + prof_score) / 3)
        communication_score = int((res_score + 75) / 2)

        # Determine Career Level
        if overall_score >= 85:
            career_level = "Advanced"
        elif overall_score >= 75:
            career_level = "Placement Ready"
        elif overall_score >= 60:
            career_level = "Intermediate"
        else:
            career_level = "Beginner"

        all_skills = list(set(resume_skills + profile_skills))
        strengths = all_skills[:5] if all_skills else ["Python", "FastAPI", "Software Engineering"]
        weaknesses = ["Cloud Deployment", "Automated Testing", "CI/CD Pipelines", "System Design"]
        missing_skills = ["Docker", "Kubernetes", "AWS", "Redis", "GraphQL"]
        recommended_roles = ["Backend Developer", "Python Engineer", "Full Stack Developer", "Software Engineer"]

        summary = (
            f"Candidate demonstrates an {career_level.lower()} engineering profile with an overall career score of {overall_score}/100. "
            f"Key strengths include {', '.join(strengths[:3])}. To become placement-ready for top product companies, "
            "focus on mastering cloud deployment, automated testing, and CI/CD workflows."
        )

        return CareerAnalysis(
            overall_score=overall_score,
            breakdown=CareerScoreBreakdown(
                technical_score=technical_score,
                resume_score=res_score,
                github_score=gh_score,
                project_score=proj_score,
                communication_score=communication_score
            ),
            career_level=career_level,
            strengths=strengths,
            weaknesses=weaknesses,
            missing_skills=missing_skills,
            recommended_roles=recommended_roles,
            summary=summary
        )
