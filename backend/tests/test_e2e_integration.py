import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId

from services.digital_twin_service import DigitalTwinService
from services.career_service import CareerService
from services.ats_service import ATSService
from models.career import JobAnalyzeRequest, CareerAnalyzeResponse
from models.ats import ATSAnalyzeRequest, ATSAnalysisResponse
from models.common import AIResponseBase
from utils.env_validator import validate_environment
from utils.errors import (
    OmniException,
    AIProviderError,
    DatabaseOperationError,
    ResourceNotFoundError,
    UnauthorizedError,
)


@pytest.mark.asyncio
async def test_e2e_digital_twin_pipeline_aggregation():
    """
    E2E Test 1: Verify DigitalTwinService aggregates data from all 5 OMNI modules
    (Profile, Resume, GitHub, Career, ATS) into one unified digital twin context.
    """
    mock_db = MagicMock()

    # Mock profile
    mock_db.profiles.find_one = AsyncMock(
        return_value={
            "user_id": "e2e_user_001",
            "full_name": "E2E Test Developer",
            "skills": ["Python", "FastAPI", "React", "MongoDB"],
        }
    )

    # Mock resume
    mock_cursor_res = MagicMock()
    mock_cursor_res.sort.return_value = mock_cursor_res
    mock_cursor_res.limit.return_value = mock_cursor_res
    mock_cursor_res.to_list = AsyncMock(
        return_value=[
            {
                "_id": ObjectId(),
                "user_id": "e2e_user_001",
                "parsed_data": {"skills": ["Python", "FastAPI"]},
            }
        ]
    )
    mock_db.resumes.find.return_value = mock_cursor_res

    # Mock github
    mock_cursor_gh = MagicMock()
    mock_cursor_gh.sort.return_value = mock_cursor_gh
    mock_cursor_gh.limit.return_value = mock_cursor_gh
    mock_cursor_gh.to_list = AsyncMock(
        return_value=[
            {
                "_id": ObjectId(),
                "user_id": "e2e_user_001",
                "username": "e2e_dev",
                "analysis": {"developer_level": "Senior"},
            }
        ]
    )
    mock_db.github_analysis.find.return_value = mock_cursor_gh

    # Mock career
    mock_cursor_car = MagicMock()
    mock_cursor_car.sort.return_value = mock_cursor_car
    mock_cursor_car.limit.return_value = mock_cursor_car
    mock_cursor_car.to_list = AsyncMock(
        return_value=[{"_id": ObjectId(), "user_id": "e2e_user_001", "career_score": 85}]
    )
    mock_db.career_analysis.find.return_value = mock_cursor_car

    # Mock ats
    mock_cursor_ats = MagicMock()
    mock_cursor_ats.sort.return_value = mock_cursor_ats
    mock_cursor_ats.limit.return_value = mock_cursor_ats
    mock_cursor_ats.to_list = AsyncMock(
        return_value=[{"_id": ObjectId(), "user_id": "e2e_user_001", "ats_score": 90}]
    )
    mock_db.ats_analysis.find.return_value = mock_cursor_ats

    # Retrieve context
    context = await DigitalTwinService.get_context("e2e_user_001", mock_db)

    assert context["profile"]["full_name"] == "E2E Test Developer"
    assert "Python" in context["profile"]["skills"]
    assert context["resume"]["parsed_data"]["skills"] == ["Python", "FastAPI"]
    assert context["github_analysis"]["analysis"]["developer_level"] == "Senior"
    assert context["career_analysis"]["career_score"] == 85
    assert context["ats_analysis"]["ats_score"] == 90


def setup_digital_twin_mocks(
    mock_db,
    profile_data=None,
    resume_list=None,
    github_list=None,
    career_list=None,
    ats_list=None,
):
    # Profile
    mock_db.profiles.find_one = AsyncMock(return_value=profile_data)

    # Resume
    mock_cursor_res = MagicMock()
    mock_cursor_res.sort.return_value = mock_cursor_res
    mock_cursor_res.limit.return_value = mock_cursor_res
    mock_cursor_res.to_list = AsyncMock(return_value=resume_list or [])
    mock_db.resumes.find.return_value = mock_cursor_res

    # GitHub
    mock_cursor_gh = MagicMock()
    mock_cursor_gh.sort.return_value = mock_cursor_gh
    mock_cursor_gh.limit.return_value = mock_cursor_gh
    mock_cursor_gh.to_list = AsyncMock(return_value=github_list or [])
    mock_db.github_analysis.find.return_value = mock_cursor_gh
    mock_db.github_data.find_one = AsyncMock(return_value=None)

    # Career
    mock_cursor_car = MagicMock()
    mock_cursor_car.sort.return_value = mock_cursor_car
    mock_cursor_car.limit.return_value = mock_cursor_car
    mock_cursor_car.to_list = AsyncMock(return_value=career_list or [])
    mock_db.career_analysis.find.return_value = mock_cursor_car

    # ATS
    mock_cursor_ats = MagicMock()
    mock_cursor_ats.sort.return_value = mock_cursor_ats
    mock_cursor_ats.limit.return_value = mock_cursor_ats
    mock_cursor_ats.to_list = AsyncMock(return_value=ats_list or [])
    mock_db.ats_analysis.find.return_value = mock_cursor_ats


@pytest.mark.asyncio
async def test_e2e_career_readiness_engine_uses_digital_twin_context():
    """
    E2E Test 2: Verify Career Readiness Engine uses DigitalTwinService context
    and returns a valid AIResponseBase model with correct UTC timestamps.
    """
    mock_db = MagicMock()
    setup_digital_twin_mocks(
        mock_db,
        profile_data={
            "user_id": "e2e_user_001",
            "skills": ["Python", "FastAPI", "React", "Docker"],
        },
        resume_list=[
            {
                "_id": ObjectId(),
                "user_id": "e2e_user_001",
                "parsed_data": {
                    "skills": ["Python", "FastAPI"],
                    "experience": [{"role": "Software Engineer", "company": "Tech Corp"}],
                    "projects": [{"title": "API Engine"}],
                },
            }
        ],
        github_list=[
            {
                "_id": ObjectId(),
                "user_id": "e2e_user_001",
                "analysis": {
                    "score": 88,
                    "developer_level": "Mid-Senior",
                    "strengths": ["Clean Code", "API Design"],
                },
            }
        ],
    )
    mock_db.career_analysis.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId()))

    report = await CareerService.generate_career_readiness_report("e2e_user_001", mock_db)

    assert isinstance(report, CareerAnalyzeResponse)
    assert isinstance(report, AIResponseBase)
    assert report.user_id == "e2e_user_001"
    assert report.career_score >= 0
    assert report.generated_by in ["ai", "rule_based"]
    assert report.created_at.tzinfo == timezone.utc


@pytest.mark.asyncio
async def test_e2e_ats_optimization_engine_uses_digital_twin_context():
    """
    E2E Test 3: Verify ATS Resume Optimization Engine uses DigitalTwinService context
    and returns a valid AIResponseBase model.
    """
    mock_db = MagicMock()
    setup_digital_twin_mocks(
        mock_db,
        profile_data={
            "user_id": "e2e_user_001",
            "skills": ["Python", "FastAPI", "React"],
        },
        resume_list=[
            {
                "_id": ObjectId(),
                "user_id": "e2e_user_001",
                "parsed_data": {
                    "skills": ["Python", "FastAPI", "MongoDB"],
                    "experience": [],
                    "projects": [],
                },
            }
        ],
    )
    mock_db.ats_analysis.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId()))

    req = ATSAnalyzeRequest(
        job_title="Senior Python Backend Engineer",
        job_description="We are looking for a Senior Python Engineer with FastAPI, Docker, and Kubernetes skills.",
    )

    report = await ATSService.analyze_resume_against_job("e2e_user_001", req, mock_db)

    assert isinstance(report, ATSAnalysisResponse)
    assert isinstance(report, AIResponseBase)
    assert report.user_id == "e2e_user_001"
    assert report.job_title == "Senior Python Backend Engineer"
    assert any("fastapi" in k.lower() for k in report.matched_keywords)
    assert report.generated_by in ["ai", "rule_based"]
    assert report.created_at.tzinfo == timezone.utc


def test_e2e_centralized_error_handling_and_env_validator():
    """
    E2E Test 4: Verify startup env validation and centralized exception hierarchy codes.
    """
    env_status = validate_environment(strict=False)
    assert "MONGODB_URL" in env_status
    assert "JWT_SECRET_KEY" in env_status

    assert OmniException("Test Bad Request").status_code == 400
    assert UnauthorizedError().status_code == 401
    assert ResourceNotFoundError().status_code == 404
    assert DatabaseOperationError().status_code == 500
    assert AIProviderError().status_code == 503
