import re
import json
from typing import List, Tuple
from models.github import (
    GitHubProfileInfo,
    RepositoryInfo,
    RepositoryAnalysisItem,
    RoadmapStepItem,
    GitHubAIAnalysis,
)
from ai.llm_provider import get_llm_provider


class GitHubAIService:
    @classmethod
    async def analyze_portfolio(
        cls,
        user_id: str,
        profile: GitHubProfileInfo,
        repos: List[RepositoryInfo],
        db
    ) -> Tuple[GitHubAIAnalysis, str]:
        """
        Analyzes user's GitHub profile & repositories using Gemini AI.
        Compares with user's resume skills from MongoDB db.profiles.
        Returns (GitHubAIAnalysis, parsing_method).
        """
        # 1. Fetch user profile skills from database to compare with GitHub
        resume_skills: List[str] = []
        try:
            if db is not None:
                user_profile = await db.profiles.find_one({"user_id": user_id})
                if user_profile and "skills" in user_profile:
                    resume_skills = [str(s) for s in user_profile.get("skills", [])]
        except Exception as e:
            print(f"[GitHubAIService] Could not fetch profile skills: {e}")

        # 2. Extract repository language breakdown
        repo_summaries = []
        languages_set = set()
        for r in repos[:10]:
            if r.language and r.language != "Other":
                languages_set.add(r.language)
            repo_summaries.append(
                f"- {r.name} ({r.language}): {r.description or 'No description'} "
                f"[{r.stargazers_count} stars, {r.forks_count} forks]"
            )

        repo_text_block = "\n".join(repo_summaries) if repo_summaries else "No public repositories available."

        prompt = f"""
You are an expert AI Principal Engineer and Engineering Manager. Perform a comprehensive technical audit of the developer's GitHub portfolio below.
Evaluate their developer maturity level, score their GitHub portfolio out of 100, analyze their repositories, compare their GitHub skills with their resume skills ({', '.join(resume_skills) if resume_skills else 'None listed'}), and provide career recommendations and a personalized learning roadmap.

Return strictly a valid JSON object conforming to the schema below, with no markdown code fences or extra text.

Schema:
{{
  "developer_level": "Junior | Mid-Level | Senior | Lead",
  "github_score": 75,
  "strengths": ["Strength 1", "Strength 2", "Strength 3"],
  "weaknesses": ["Growth area 1", "Growth area 2"],
  "portfolio_review": "A detailed 3-4 sentence professional evaluation of their repositories, coding diversity, and impact.",
  "repository_analysis": [
    {{
      "name": "Repo name",
      "summary": "1-2 sentence architectural summary",
      "architecture_score": 80,
      "quality_score": 85,
      "technologies": ["Tech1", "Tech2"],
      "strengths": ["Clean code", "Good docs"]
    }}
  ],
  "career_recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"],
  "missing_skills": ["Skill missing from GitHub compared to Resume or industry expectations"],
  "personalized_roadmap": [
    {{
      "step_number": 1,
      "title": "Roadmap step title",
      "description": "Actionable step description",
      "recommended_resources": ["Resource 1", "Resource 2"]
    }}
  ]
}}

GitHub Username: {profile.username}
Public Repositories Count: {profile.public_repos}
Followers: {profile.followers}
Top Repositories:
{repo_text_block}
Resume Skills: {', '.join(resume_skills) if resume_skills else 'None listed'}
"""

        try:
            llm = get_llm_provider()
            response_text = await llm.generate_text(prompt)
            cleaned_text = re.sub(r'```json|```', '', response_text).strip()
            data = json.loads(cleaned_text)
            analysis = GitHubAIAnalysis.model_validate(data)
            return analysis, "ai"
        except Exception as e:
            print(f"[GitHubAIService] AI analysis failed ({e}). Using rule-based fallback.")
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
