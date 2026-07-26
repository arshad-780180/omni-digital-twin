import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from datetime import datetime

from models.github import (
    GitHubProfileInfo,
    RepositoryInfo,
    RepositoryAnalysisItem,
    RoadmapStepItem,
    GitHubAIAnalysis,
    GitHubAnalyzeResponse,
)
from services.github_service import GitHubService
from services.github_ai_service import GitHubAIService


def test_pydantic_github_schemas():
    profile = GitHubProfileInfo(
        username="testuser",
        name="Test User",
        public_repos=12,
        followers=100
    )
    assert profile.username == "testuser"
    assert profile.public_repos == 12

    repo = RepositoryInfo(
        name="omni-platform",
        description="Digital Twin Platform",
        language="Python",
        stargazers_count=45
    )
    assert repo.name == "omni-platform"
    assert repo.stargazers_count == 45

    analysis = GitHubAIAnalysis(
        developer_level="Senior",
        github_score=88,
        strengths=["Architecture", "Python"],
        missing_skills=["Kubernetes"]
    )
    assert analysis.developer_level == "Senior"
    assert analysis.github_score == 88


@pytest.mark.asyncio
async def test_fetch_user_profile_success():
    fake_json = {
        "login": "octocat",
        "name": "The Octocat",
        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
        "bio": "GitHub mascot",
        "public_repos": 8,
        "followers": 3900,
        "following": 9,
        "html_url": "https://github.com/octocat"
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = fake_json
        mock_get.return_value = mock_response

        profile = await GitHubService.fetch_user_profile("octocat")
        assert profile.username == "octocat"
        assert profile.name == "The Octocat"
        assert profile.followers == 3900


@pytest.mark.asyncio
async def test_fetch_user_profile_not_found():
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(HTTPException) as exc_info:
            await GitHubService.fetch_user_profile("nonexistent_user_99999")
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_fetch_user_repositories():
    fake_repos = [
        {
            "name": "repo1",
            "description": "Python repo",
            "html_url": "https://github.com/octocat/repo1",
            "language": "Python",
            "stargazers_count": 10,
            "forks_count": 2,
            "updated_at": "2026-07-27T00:00:00Z"
        },
        {
            "name": "repo2",
            "description": "React repo",
            "html_url": "https://github.com/octocat/repo2",
            "language": "JavaScript",
            "stargazers_count": 50,
            "forks_count": 15,
            "updated_at": "2026-07-27T01:00:00Z"
        }
    ]

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = fake_repos
        mock_get.return_value = mock_response

        repos = await GitHubService.fetch_user_repositories("octocat")
        assert len(repos) == 2
        # repo2 has more stars so it should be sorted first
        assert repos[0].name == "repo2"
        assert repos[0].stargazers_count == 50


def test_fallback_rule_based_analysis():
    profile = GitHubProfileInfo(
        username="devuser",
        public_repos=20,
        followers=50
    )
    repos = [
        RepositoryInfo(
            name="api-service",
            description="Backend service",
            language="Python",
            stargazers_count=12
        )
    ]
    resume_skills = ["Python", "Kubernetes", "AWS", "Terraform"]

    analysis = GitHubAIService.fallback_rule_based_analysis(profile, repos, resume_skills)
    assert analysis.github_score > 50
    assert analysis.developer_level in ["Junior", "Mid-Level", "Senior", "Lead"]
    # Kubernetes, AWS, Terraform are not in repos (which only has Python)
    assert "Kubernetes" in analysis.missing_skills
    assert "AWS" in analysis.missing_skills
    assert len(analysis.personalized_roadmap) == 3


@pytest.mark.asyncio
async def test_analyze_portfolio_ai_success():
    profile = GitHubProfileInfo(username="octocat", public_repos=10, followers=100)
    repos = [RepositoryInfo(name="testrepo", language="Python", stargazers_count=5)]
    fake_llm_json = """
    {
      "developer_level": "Senior",
      "github_score": 85,
      "strengths": ["Clean Code", "Python Mastery"],
      "weaknesses": ["Docs could improve"],
      "portfolio_review": "Excellent repository structure.",
      "repository_analysis": [
        {
          "name": "testrepo",
          "summary": "Solid Python library",
          "architecture_score": 85,
          "quality_score": 90,
          "technologies": ["Python"],
          "strengths": ["Well tested"]
        }
      ],
      "career_recommendations": ["Aim for Lead Architect roles"],
      "missing_skills": ["Rust"],
      "personalized_roadmap": [
        {
          "step_number": 1,
          "title": "Learn Rust",
          "description": "System programming language",
          "recommended_resources": ["The Rust Book"]
        }
      ]
    }
    """

    with patch("services.github_ai_service.get_llm_provider") as mock_provider:
        mock_instance = MagicMock()
        mock_instance.generate_text = AsyncMock(return_value=fake_llm_json)
        mock_provider.return_value = mock_instance

        mock_db = MagicMock()
        mock_db.profiles.find_one = AsyncMock(return_value={"user_id": "u1", "skills": ["Python", "SQL"]})

        analysis, method = await GitHubAIService.analyze_portfolio("u1", profile, repos, mock_db)
        assert method == "ai"
        assert analysis.developer_level == "Senior"
        assert analysis.github_score == 85
        assert "Rust" in analysis.missing_skills


@pytest.mark.asyncio
async def test_analyze_portfolio_ai_fallback():
    profile = GitHubProfileInfo(username="octocat", public_repos=5, followers=10)
    repos = [RepositoryInfo(name="testrepo", language="Python")]

    with patch("services.github_ai_service.get_llm_provider") as mock_provider:
        mock_instance = MagicMock()
        mock_instance.generate_text = AsyncMock(side_effect=Exception("API limit"))
        mock_provider.return_value = mock_instance

        mock_db = MagicMock()
        mock_db.profiles.find_one = AsyncMock(return_value={"user_id": "u1", "skills": ["Python"]})

        analysis, method = await GitHubAIService.analyze_portfolio("u1", profile, repos, mock_db)
        assert method == "rule_based_fallback"
        assert analysis.github_score > 0
        assert len(analysis.strengths) > 0
