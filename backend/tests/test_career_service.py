import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from models.career import (
    CareerScoreBreakdown,
    StrengthItem,
    WeaknessItem,
    MissingSkillItem,
    RecommendedRole,
    CareerAnalysis,
    CareerAnalyzeResponse
)
from services.career_service import CareerService
from services.career_ai_service import CareerAIService


def test_pydantic_career_schemas():
    """1. Test validation of career Pydantic schemas (CareerScoreBreakdown, items, response)."""
    breakdown = CareerScoreBreakdown(
        technical_score=85,
        resume_score=80,
        github_score=90,
        project_score=75,
        communication_score=85
    )
    assert breakdown.technical_score == 85
    assert breakdown.github_score == 90

    strength = StrengthItem(title="Python Specialist", description="Strong expertise in Python", category="Technical")
    assert strength.category == "Technical"

    weakness = WeaknessItem(title="No Cloud Certs", description="Missing AWS/GCP certifications", impact="Medium", recommendation="Get AWS certified")
    assert weakness.impact == "Medium"

    missing = MissingSkillItem(skill="Docker", reason="Required for modern DevOps", priority="High")
    assert missing.priority == "High"

    role = RecommendedRole(role="Senior Backend Engineer", match_percentage=88, reason="Strong Python and API skills")
    assert role.match_percentage == 88


@pytest.mark.asyncio
async def test_load_user_context_success():
    """2. Test automatic loading of Resume, GitHub analysis, and User Profile from MongoDB."""
    mock_db = MagicMock()

    # Mock resume cursor
    mock_res_cursor = MagicMock()
    mock_res_cursor.sort.return_value = mock_res_cursor
    mock_res_cursor.limit.return_value = mock_res_cursor
    mock_res_cursor.to_list = AsyncMock(return_value=[{"_id": "res_123", "skills": ["Python"]}])
    mock_db.resumes.find.return_value = mock_res_cursor

    # Mock github cursor
    mock_gh_cursor = MagicMock()
    mock_gh_cursor.sort.return_value = mock_gh_cursor
    mock_gh_cursor.limit.return_value = mock_gh_cursor
    mock_gh_cursor.to_list = AsyncMock(return_value=[{"_id": "gh_123", "developer_level": "Senior"}])
    mock_db.github_analysis.find.return_value = mock_gh_cursor

    # Mock profile
    mock_db.profiles.find_one = AsyncMock(return_value={"user_id": "user_1", "skills": ["FastAPI"]})

    resume_doc, gh_doc, prof_doc = await CareerService.load_user_context("user_1", mock_db)

    assert resume_doc["_id"] == "res_123"
    assert gh_doc["_id"] == "gh_123"
    assert prof_doc["user_id"] == "user_1"
    assert mock_db.resumes.find.called
    assert mock_db.github_analysis.find.called
    assert mock_db.profiles.find_one.called


@pytest.mark.asyncio
async def test_load_user_context_empty():
    """3. Test loading context when user has no uploaded resume, github analysis, or profile."""
    mock_db = MagicMock()

    mock_res_cursor = MagicMock()
    mock_res_cursor.sort.return_value = mock_res_cursor
    mock_res_cursor.limit.return_value = mock_res_cursor
    mock_res_cursor.to_list = AsyncMock(return_value=[])
    mock_db.resumes.find.return_value = mock_res_cursor

    mock_gh_cursor = MagicMock()
    mock_gh_cursor.sort.return_value = mock_gh_cursor
    mock_gh_cursor.limit.return_value = mock_gh_cursor
    mock_gh_cursor.to_list = AsyncMock(return_value=[])
    mock_db.github_analysis.find.return_value = mock_gh_cursor
    mock_db.github_data.find_one = AsyncMock(return_value=None)

    mock_db.profiles.find_one = AsyncMock(return_value=None)

    resume_doc, gh_doc, prof_doc = await CareerService.load_user_context("user_empty", mock_db)
    assert resume_doc is None
    assert gh_doc is None
    assert prof_doc is None


@pytest.mark.asyncio
async def test_ai_success():
    """4. Test successful Gemini AI career analysis generating valid structured report."""
    fake_llm_json = """
    {
      "career_score": 88,
      "breakdown": {
        "technical_score": 90,
        "resume_score": 85,
        "github_score": 88,
        "project_score": 85,
        "communication_score": 90
      },
      "career_level": "Senior Developer",
      "strengths": [
        {"title": "Python Expert", "description": "Extensive backend Python usage", "category": "Technical"}
      ],
      "weaknesses": [
        {"title": "No Kubernetes", "description": "Lacks container orchestration", "impact": "Medium", "recommendation": "Deploy a K8s cluster"}
      ],
      "missing_skills": [
        {"skill": "Kubernetes", "reason": "Cloud scalability", "priority": "High"}
      ],
      "recommended_roles": [
        {"role": "Senior Backend Developer", "match_percentage": 92, "reason": "Matches 90% of skills"}
      ],
      "summary": "An exceptional backend developer ready for senior leadership roles."
    }
    """

    with patch("services.career_ai_service.get_llm_provider") as mock_provider:
        mock_instance = MagicMock()
        mock_instance.generate_text = AsyncMock(return_value=fake_llm_json)
        mock_provider.return_value = mock_instance

        analysis, method = await CareerAIService.analyze_career(
            "u1",
            {"parsed_data": {"skills": ["Python"]}},
            {"analysis": {"github_score": 90}},
            {"skills": ["FastAPI"]}
        )
        assert method == "ai"
        assert analysis.overall_score == 88
        assert analysis.career_level == "Placement Ready"
        assert "Python" in analysis.strengths


@pytest.mark.asyncio
async def test_ai_fallback():
    """5. Test rule-based fallback when Gemini AI throws rate limit exception."""
    with patch("services.career_ai_service.get_llm_provider") as mock_provider:
        mock_instance = MagicMock()
        mock_instance.generate_text = AsyncMock(side_effect=Exception("API Rate Limit Exceeded"))
        mock_provider.return_value = mock_instance

        analysis, method = await CareerAIService.analyze_career(
            "u1",
            {"parsed_data": {"skills": ["Python", "SQL"], "experience": ["Eng1", "Eng2"]}},
            {"analysis": {"github_score": 80}},
            {"skills": ["FastAPI", "Docker"]}
        )
        assert method == "rule_based"
        assert analysis.overall_score > 0
        assert analysis.career_level in ["Beginner", "Intermediate", "Placement Ready", "Advanced"]


def test_empty_resume():
    """6. Test deterministic calculation when resume data is missing/empty."""
    analysis = CareerAIService.fallback_rule_based_career(
        None,
        {"analysis": {"github_score": 85}, "repositories": [{}, {}, {}]},
        {"skills": ["Python", "JavaScript"]}
    )
    assert analysis.overall_score > 0
    assert analysis.breakdown.resume_score == 50  # Default base score when None
    assert analysis.breakdown.github_score == 85


def test_empty_github_analysis():
    """7. Test deterministic calculation when GitHub analysis is missing/empty."""
    analysis = CareerAIService.fallback_rule_based_career(
        {"parsed_data": {"skills": ["Python", "C++"], "experience": ["Role1"]}},
        None,
        {"skills": ["Python"]}
    )
    assert analysis.overall_score > 0
    assert analysis.breakdown.github_score == 50  # Default fallback when GitHub is None


def test_missing_profile():
    """8. Test deterministic calculation when User Profile is missing/empty."""
    analysis = CareerAIService.fallback_rule_based_career(
        {"parsed_data": {"skills": ["Go", "Kubernetes"]}},
        {"analysis": {"github_score": 78}},
        None
    )
    assert analysis.overall_score > 0
    assert analysis.breakdown.technical_score > 0
    assert len(analysis.strengths) > 0


def test_score_calculation():
    """9. Test exact score weighting (Resume 30%, GitHub 30%, Projects 20%, Profile 20%)."""
    # Let's craft inputs with known scores:
    # res_score -> 60 + 5 skills*2 + 2 roles*5 = 80
    # gh_score -> 90
    # proj_score -> 65 + 3 projs*8 = 89
    # prof_score -> 60 + 5 skills*3 = 75
    # Weighted = 0.3*80(24) + 0.3*90(27) + 0.2*89(17.8) + 0.2*75(15) = 83
    res_doc = {
        "parsed_data": {
            "skills": ["A", "B", "C", "D", "E"],
            "experience": ["R1", "R2"],
            "projects": ["P1", "P2", "P3"]
        }
    }
    gh_doc = {"analysis": {"github_score": 90}}
    prof_doc = {"skills": ["S1", "S2", "S3", "S4", "S5"]}

    analysis = CareerAIService.fallback_rule_based_career(res_doc, gh_doc, prof_doc)
    assert analysis.overall_score == 83
    assert analysis.career_level == "Placement Ready"
    assert analysis.breakdown.technical_score == int((90 + 89 + 75) / 3)


@pytest.mark.asyncio
async def test_mongodb_save_and_api_response():
    """10. Test CareerService saving report to MongoDB and returning CareerAnalyzeResponse."""
    mock_db = MagicMock()

    mock_cursor_res = MagicMock()
    mock_cursor_res.sort.return_value = mock_cursor_res
    mock_cursor_res.limit.return_value = mock_cursor_res
    mock_cursor_res.to_list = AsyncMock(return_value=[{"parsed_data": {"skills": ["Python"]}}])
    mock_db.resumes.find.return_value = mock_cursor_res

    mock_cursor_gh = MagicMock()
    mock_cursor_gh.sort.return_value = mock_cursor_gh
    mock_cursor_gh.limit.return_value = mock_cursor_gh
    mock_cursor_gh.to_list = AsyncMock(return_value=[{"analysis": {"github_score": 82}}])
    mock_db.github_analysis.find.return_value = mock_cursor_gh
    mock_db.profiles.find_one = AsyncMock(return_value={"skills": ["Python"]})

    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = "507f1f77bcf86cd799439011"
    mock_db.career_analysis.insert_one = AsyncMock(return_value=mock_insert_result)

    with patch("services.career_service.CareerAIService.analyze_career") as mock_analyze:
        fake_analysis = CareerAnalysis(
            overall_score=85,
            breakdown=CareerScoreBreakdown(
                technical_score=88,
                resume_score=84,
                github_score=86,
                project_score=82,
                communication_score=78
            ),
            career_level="Placement Ready",
            strengths=["Python", "FastAPI"],
            weaknesses=["Kubernetes"],
            missing_skills=["Kubernetes"],
            recommended_roles=["Backend Developer"],
            summary="Strong profile."
        )
        mock_analyze.return_value = (fake_analysis, "ai")

        response = await CareerService.generate_career_readiness_report("user_123", mock_db)
        assert response.id == "507f1f77bcf86cd799439011"
        assert response.user_id == "user_123"
        assert response.career_score == 85
        assert response.analysis_method == "ai"
        assert mock_db.career_analysis.insert_one.called


@pytest.mark.asyncio
async def test_history_endpoint():
    """11. Test CareerService.get_career_history returning list sorted by newest."""
    mock_db = MagicMock()

    fake_docs = [
        {
            "_id": "id_2",
            "user_id": "u1",
            "career_score": 88,
            "technical_score": 90,
            "resume_score": 85,
            "github_score": 88,
            "project_score": 85,
            "communication_score": 80,
            "career_level": "Placement Ready",
            "strengths": ["Python"],
            "weaknesses": ["Docker"],
            "missing_skills": ["Docker"],
            "recommended_roles": ["Backend Developer"],
            "summary": "Report 2",
            "analysis_method": "ai",
            "created_at": datetime(2026, 7, 27, 10, 0, 0)
        },
        {
            "_id": "id_1",
            "user_id": "u1",
            "career_score": 80,
            "technical_score": 82,
            "resume_score": 80,
            "github_score": 80,
            "project_score": 78,
            "communication_score": 75,
            "career_level": "Intermediate",
            "strengths": ["Python"],
            "weaknesses": ["Docker"],
            "missing_skills": ["Docker"],
            "recommended_roles": ["Backend Developer"],
            "summary": "Report 1",
            "analysis_method": "rule_based",
            "created_at": datetime(2026, 7, 26, 10, 0, 0)
        }
    ]

    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=fake_docs)
    mock_db.career_analysis.find.return_value = mock_cursor

    reports = await CareerService.get_career_history("u1", mock_db)
    assert len(reports) == 2
    assert reports[0].id == "id_2"
    assert reports[0].career_score == 88
    assert reports[1].id == "id_1"
    assert reports[1].career_score == 80


@pytest.mark.asyncio
async def test_latest_report_endpoint():
    """12. Test CareerService.get_latest_career_report returning the newest document."""
    mock_db = MagicMock()
    fake_doc = {
        "_id": "id_latest",
        "user_id": "u1",
        "career_score": 92,
        "technical_score": 94,
        "resume_score": 90,
        "github_score": 92,
        "project_score": 90,
        "communication_score": 88,
        "career_level": "Advanced",
        "strengths": ["Python", "ML"],
        "weaknesses": [],
        "missing_skills": [],
        "recommended_roles": ["AI Engineer"],
        "summary": "Top engineer.",
        "analysis_method": "ai",
        "created_at": datetime.now(timezone.utc)
    }

    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[fake_doc])
    mock_db.career_analysis.find.return_value = mock_cursor

    latest = await CareerService.get_latest_career_report("u1", mock_db)
    assert latest is not None
    assert latest.id == "id_latest"
    assert latest.career_score == 92
    assert latest.career_level == "Advanced"
