import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from models.job_match import (
    JobMatchAnalyzeRequest,
    JobMatchAnalysisResponse,
    JobRequirements,
    RoleRecommendationItem,
    LearningGapItem,
    SalaryInsights,
    AICareerAdvice,
)
from services.job_matching_service import JobMatchingService
from services.job_matching_ai_service import JobMatchingAIService


def test_job_match_pydantic_schemas():
    """1. Test Pydantic schema validation for Job Match requests and responses."""
    req = JobMatchAnalyzeRequest(
        job_title="Senior Python Backend Engineer",
        company="Google",
        location="Remote",
        employment_type="Full-time",
        job_description="Looking for Python, FastAPI, MongoDB, Docker, and Kubernetes expertise.",
    )
    assert req.job_title == "Senior Python Backend Engineer"
    assert req.company == "Google"

    req_data = JobRequirements(
        required_skills=["Python", "FastAPI", "MongoDB"],
        preferred_skills=["Kubernetes"],
    )
    assert "Python" in req_data.required_skills

    role_item = RoleRecommendationItem(
        role_name="Senior Backend Engineer",
        category="best_matching",
        match_percentage=88,
        explanation="Direct fit for target role.",
    )
    assert role_item.category == "best_matching"

    salary_data = SalaryInsights(
        junior_range="$75k-$95k",
        mid_level_range="$100k-$130k",
        senior_range="$140k-$175k",
        confidence_level="High",
    )
    assert "market assumptions" in salary_data.disclaimer

    resp = JobMatchAnalysisResponse(
        user_id="test_user",
        job_title="Senior Python Backend Engineer",
        company="Google",
        job_description="Looking for Python, FastAPI, MongoDB, Docker, and Kubernetes expertise.",
        overall_job_match_score=85,
        technical_match_score=90,
        experience_match_score=80,
        education_match_score=80,
        project_relevance_score=85,
        skill_coverage_percentage=90,
        matched_skills=["Python", "FastAPI", "MongoDB"],
        missing_skills=["Kubernetes"],
        career_readiness="Advanced",
        hiring_recommendation="Strong Hire",
        requirements=req_data,
        recommended_roles=[role_item],
        salary_estimate=salary_data,
        analysis_method="ai",
    )
    assert resp.overall_job_match_score == 85
    assert resp.hiring_recommendation == "Strong Hire"
    assert resp.created_at.tzinfo == timezone.utc


def test_job_match_score_calculation():
    """2. Test rule-based job match score calculations."""
    req = JobMatchAnalyzeRequest(
        job_title="Backend Developer",
        company="TechCorp",
        job_description="We need a Python, FastAPI, MongoDB, and AWS engineer.",
    )
    digital_twin_context = {
        "resume": {
            "parsed_data": {
                "skills": ["Python", "FastAPI", "MongoDB"],
                "projects": [{"title": "API Project"}, {"title": "Auth Service"}],
            }
        },
        "profile": {"skills": ["Git", "Linux"]},
        "github": {"analysis": {"github_score": 85}},
    }

    result = JobMatchingAIService.fallback_rule_based_job_match(
        user_id="user_123",
        digital_twin_context=digital_twin_context,
        request=req,
    )
    assert result.overall_job_match_score > 0
    assert result.technical_match_score > 0
    assert "Python" in result.matched_skills
    assert "Aws" in result.missing_skills or "aws" in [s.lower() for s in result.missing_skills]
    assert len(result.recommended_roles) == 4
    assert result.salary_estimate.disclaimer is not None
    assert result.analysis_method == "rule_based"


@pytest.mark.asyncio
async def test_job_match_ai_success():
    """3. Test successful Gemini AI job matching response parsing."""
    req = JobMatchAnalyzeRequest(
        job_title="Software Engineer",
        company="Stripe",
        job_description="Python API developer with cloud experience.",
    )
    fake_ai_json = """
    {
      "overall_job_match_score": 88,
      "technical_match_score": 90,
      "experience_match_score": 85,
      "education_match_score": 80,
      "project_relevance_score": 90,
      "skill_coverage_percentage": 90,
      "missing_skills": ["Kubernetes"],
      "matched_skills": ["Python", "API"],
      "missing_technologies": ["Kubernetes"],
      "strength_areas": ["Python API design"],
      "weak_areas": ["Container orchestration"],
      "career_readiness": "Advanced",
      "hiring_recommendation": "Strong Hire",
      "requirements": {
        "required_skills": ["Python", "API"],
        "preferred_skills": ["Kubernetes"]
      },
      "recommended_roles": [
        {
          "role_name": "Software Engineer",
          "category": "best_matching",
          "match_percentage": 88,
          "explanation": "Great skill alignment."
        }
      ],
      "learning_plan": [
        {
          "skill": "Kubernetes",
          "priority_order": 1,
          "estimated_difficulty": "Medium",
          "learning_timeline": "3 weeks",
          "reasoning": "Required cloud technology."
        }
      ],
      "salary_estimate": {
        "junior_range": "$80,000 - $100,000",
        "mid_level_range": "$110,000 - $135,000",
        "senior_range": "$145,000 - $180,000",
        "confidence_level": "High",
        "disclaimer": "These salary ranges are estimates derived from profile metrics and market assumptions, not guaranteed offers."
      },
      "career_advice": {
        "executive_summary": "Strong candidate for Python roles.",
        "interview_preparation_advice": ["Focus on API scalability."]
      }
    }
    """

    mock_llm = MagicMock()
    mock_llm.generate_text = AsyncMock(return_value=fake_ai_json)

    with patch("services.job_matching_ai_service.get_llm_provider", return_value=mock_llm):
        analysis, method = await JobMatchingAIService.analyze_job_match(
            user_id="user_ai",
            digital_twin_context={},
            request=req,
        )

        assert method == "ai"
        assert analysis.overall_job_match_score == 88
        assert analysis.hiring_recommendation == "Strong Hire"
        assert analysis.salary_estimate.mid_level_range == "$110,000 - $135,000"


@pytest.mark.asyncio
async def test_job_match_fallback_engine():
    """4. Test automatic fallback to deterministic matching when AI fails."""
    req = JobMatchAnalyzeRequest(
        job_title="Cloud Engineer",
        company="AWS",
        job_description="Seeking AWS, Docker, Kubernetes, and Python developer.",
    )

    with patch("services.job_matching_ai_service.get_llm_provider", side_effect=Exception("Gemini timeout")):
        analysis, method = await JobMatchingAIService.analyze_job_match(
            user_id="user_fallback",
            digital_twin_context={"resume": {"parsed_data": {"skills": ["Python", "Docker"]}}},
            request=req,
        )

        assert method == "rule_based"
        assert analysis.overall_job_match_score > 0
        assert "Python" in analysis.matched_skills or "python" in [s.lower() for s in analysis.matched_skills]


@pytest.mark.asyncio
async def test_digital_twin_integration():
    """5. Verify JobMatchingService uses DigitalTwinService to load profile/resume context."""
    req = JobMatchAnalyzeRequest(
        job_title="Fullstack Engineer",
        company="Meta",
        job_description="React, Node.js, and MongoDB required.",
    )
    mock_db = MagicMock()
    mock_insert_res = MagicMock()
    mock_insert_res.inserted_id = ObjectId("640000000000000000000001")
    mock_db.job_matches.insert_one = AsyncMock(return_value=mock_insert_res)

    mock_context = {
        "profile": {"skills": ["React", "Node.js"]},
        "resume": {"parsed_data": {"skills": ["MongoDB"]}},
        "github": {"analysis": {"github_score": 90}},
    }

    with patch("services.job_matching_service.DigitalTwinService.get_context", new=AsyncMock(return_value=mock_context)) as mock_dt:
        result = await JobMatchingService.analyze_and_save_job_match(
            user_id="user_dt",
            request=req,
            db=mock_db,
        )
        mock_dt.assert_called_once_with("user_dt", mock_db)
        assert result.id == "640000000000000000000001"
        assert result.user_id == "user_dt"


@pytest.mark.asyncio
async def test_mongodb_persistence_and_endpoints():
    """6. Verify JobMatchingService get_latest_job_match, get_job_match_history, and delete_job_match."""
    mock_db = MagicMock()

    # 1) get_latest_job_match
    fake_doc = {
        "_id": ObjectId("640000000000000000000002"),
        "user_id": "user_100",
        "job_title": "Staff Engineer",
        "company": "Netflix",
        "job_description": "Microservices and Java.",
        "overall_job_match_score": 92,
        "created_at": datetime.now(timezone.utc),
    }

    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[fake_doc])
    mock_db.job_matches.find.return_value = mock_cursor

    latest = await JobMatchingService.get_latest_job_match("user_100", mock_db)
    assert latest is not None
    assert latest.job_title == "Staff Engineer"
    assert latest.overall_job_match_score == 92

    # 2) get_job_match_history
    history = await JobMatchingService.get_job_match_history("user_100", mock_db, limit=5)
    assert len(history) == 1
    assert history[0].company == "Netflix"

    # 3) delete_job_match
    mock_del_res = MagicMock()
    mock_del_res.deleted_count = 1
    mock_db.job_matches.delete_one = AsyncMock(return_value=mock_del_res)

    deleted = await JobMatchingService.delete_job_match("user_100", "640000000000000000000002", mock_db)
    assert deleted is True
