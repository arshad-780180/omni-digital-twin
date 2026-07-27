import re
import json
from typing import List, Tuple, Optional, Any
from models.github import (
    GitHubProfileInfo,
    RepositoryInfo,
    RepositoryAnalysisItem,
    RoadmapStepItem,
    GitHubAIAnalysis,
)
from ai.llm_provider import get_llm_provider
from utils.logger import get_logger

logger = get_logger("github")


class GitHubAIService:
    @classmethod
    async def analyze_portfolio(
        cls,
        user_id: str,
        profile: GitHubProfileInfo,
        repos: List[RepositoryInfo],
        db: Optional[Any] = None
    ) -> Tuple[GitHubAIAnalysis, str]:
        """
        Analyzes profile and repositories using Gemini AI, falling back to deterministic
        rule-based analysis if AI is unavailable.
        """
        # 1. Fetch user skills from Profile if database handle provided
        resume_skills: List[str] = []
        try:
            if db is not None:
                user_profile = await db.profiles.find_one({"user_id": user_id})
                if user_profile and "skills" in user_profile:
                    resume_skills = [str(s) for s in user_profile.get("skills", [])]
        except Exception as e:
            logger.warning(f"Could not fetch profile skills: {e}")

        # 2. Extract repository language breakdown
        repo_summaries = []
        languages_set = set()
        total_stars = 0
        total_forks = 0
        for r in repos:
            total_stars += r.stargazers_count
            total_forks += r.forks_count
            if r.language:
                languages_set.add(r.language)
            repo_summaries.append(
                f"- {r.name} (lang: {r.language or 'None'}, stars: {r.stargazers_count}, forks: {r.forks_count}, desc: {r.description or 'None'}, commits: {getattr(r, 'commits_count', 0)})"
            )
        
        repos_text = "\n".join(repo_summaries[:20]) # Limit to 20 for prompt size
        skills_text = ", ".join(resume_skills) if resume_skills else "None provided"

        prompt = f"""
You are an expert Principal GitHub Technical Evaluator & Career Architect.
Analyze the following GitHub developer profile, repository metrics, and compare against known resume skills.
Return strictly a valid JSON object matching the exact schema below without markdown formatting or code fences.

Schema:
{{
  "developer_level": "Junior Developer | Mid-Level Developer | Senior Developer | Principal Engineer",
  "github_score": 75,
  "strengths": ["Strength 1", "Strength 2"],
  "weaknesses": ["Weakness 1", "Weakness 2"],
  "portfolio_review": "Executive summary review of repositories and coding activity.",
  "repository_analysis": [
    {{
      "repo_name": "repository-name",
      "architecture_score": 80,
      "code_quality_score": 85,
      "documentation_score": 70,
      "key_strengths": ["Clean structure"],
      "improvement_areas": ["Add CI/CD pipeline"],
      "summary": "Repository evaluation summary."
    }}
  ],
  "career_recommendations": ["Recommendation 1", "Recommendation 2"],
  "missing_skills": ["Skill 1 not shown in GitHub"],
  "personalized_roadmap": [
    {{
      "step_number": 1,
      "title": "Roadmap step title",
      "description": "Actionable task description",
      "recommended_resources": ["Resource or documentation link"]
    }}
  ]
}}

Candidate Data:
- Username: {profile.username}
- Public Repositories: {profile.public_repos}
- Total Stars Across Repos: {total_stars}
- Followers: {profile.followers}
- Profile Skills (from Resume/Profile): {skills_text}

Repositories Sample:
{repos_text}
"""
        try:
            llm = get_llm_provider()
            response_text = await llm.generate_text(prompt)
            cleaned_text = re.sub(r'```json|```', '', response_text).strip()
            data = json.loads(cleaned_text)
            analysis = GitHubAIAnalysis.model_validate(data)
            return analysis, "ai"
        except Exception as e:
            logger.warning(f"AI analysis failed ({e}). Using rule-based fallback.")
            fallback = cls.fallback_rule_based_analysis(profile, repos, resume_skills)
            return fallback, "rule_based_fallback"

    @staticmethod
    def fallback_rule_based_analysis(
        profile: GitHubProfileInfo,
        repos: List[RepositoryInfo],
        resume_skills: List[str]
    ) -> GitHubAIAnalysis:
        """
        Deterministic fallback analysis when AI generation hits quota or network error.
        """
        # Calculate score out of 100
        score = min(100, 50 + min(20, profile.public_repos * 2) + min(15, len(repos) * 3) + min(15, profile.followers * 2))

        # Determine developer level
        if score >= 85 or profile.public_repos >= 25:
            dev_level = "Senior"
        elif score >= 70 or profile.public_repos >= 10:
            dev_level = "Mid-Level"
        else:
            dev_level = "Junior"

        # Languages and repo items
        languages = list(set([r.language for r in repos if r.language and r.language != "Other"]))
        repo_items: List[RepositoryAnalysisItem] = []
        for r in repos[:6]:
            repo_items.append(
                RepositoryAnalysisItem(
                    name=r.name,
                    summary=r.description or f"A {r.language or 'general'} software project.",
                    architecture_score=min(95, 65 + r.stargazers_count * 5),
                    quality_score=min(95, 70 + r.stargazers_count * 3),
                    technologies=[r.language] if r.language else ["Code"],
                    strengths=["Structured codebase", "Active repository"]
                )
            )

        # Missing skills (skills in resume_skills that are not in languages)
        missing = [s for s in resume_skills if s.lower() not in [l.lower() for l in languages]]
        if not missing:
            missing = ["Automated Testing", "CI/CD Pipelines", "Cloud Deployment"]

        strengths = [
            f"Proficient in {', '.join(languages[:3]) if languages else 'software development'}",
            f"Maintains {profile.public_repos} public repositories with consistent commits",
            "Demonstrates practical hands-on implementation skills"
        ]

        weaknesses = [
            "Consider adding comprehensive architectural diagrams to READMEs",
            "Expand automated test coverage across core repositories"
        ]

        portfolio_review = (
            f"{profile.username} exhibits a {dev_level.lower()} engineering profile with {profile.public_repos} public "
            f"repositories across {', '.join(languages[:4]) if languages else 'multiple technologies'}. "
            "Their codebase demonstrates good project diversity and foundational engineering practices."
        )

        career_recs = [
            "Integrate automated CI/CD workflows using GitHub Actions",
            "Enhance documentation with API specifications and setup guides",
            "Contribute to open-source projects in your core language stack"
        ]

        roadmap = [
            RoadmapStepItem(
                step_number=1,
                title="Establish Comprehensive Test Suites",
                description="Add unit and integration testing using Pytest or Jest across your top repositories.",
                recommended_resources=["Pytest Official Guide", "Testing Best Practices"]
            ),
            RoadmapStepItem(
                step_number=2,
                title="Automate CI/CD Pipelines",
                description="Configure GitHub Actions to automatically run tests and linters on pull requests.",
                recommended_resources=["GitHub Actions Documentation", "Automated DevOps Workflows"]
            ),
            RoadmapStepItem(
                step_number=3,
                title="Cloud Deployment & Architecture",
                description="Containerize applications with Docker and deploy to production-grade cloud environments.",
                recommended_resources=["Docker Handbook", "Cloud Native Architecture"]
            )
        ]

        return GitHubAIAnalysis(
            developer_level=dev_level,
            github_score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            portfolio_review=portfolio_review,
            repository_analysis=repo_items,
            career_recommendations=career_recs,
            missing_skills=missing[:5],
            personalized_roadmap=roadmap
        )
