import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException

from models.learning import (
    Milestone,
    ProjectRecommendation,
    CertificationRecommendation,
    LearningResource,
    LearningPhase,
    ProgressSummary,
    LearningAnalytics,
    LearningRoadmap,
    LearningRoadmapGenerateRequest,
    MilestoneCompleteRequest,
    LearningRoadmapResponse,
    LearningRoadmapHistoryResponse,
)
from services.learning_ai_service import LearningRoadmapAIService
from services.learning_service import LearningRoadmapService


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.learning_roadmaps = MagicMock()
    db.digital_twin_memory = MagicMock()
    return db


def test_learning_pydantic_schemas():
    """
    Test 1: Verify Pydantic schema validation, defaults, and field mappings for Phase 8 models.
    """
    m = Milestone(
        milestone_id="m1",
        title="Build Docker Service",
        phase=1,
        category="skill",
        description="Containerize app",
        skills_unlocked=["Docker", "Linux"],
    )
    assert m.completed is False
    assert "Docker" in m.skills_unlocked

    p = ProjectRecommendation(
        project_id="p1",
        title="Microservice API",
        description="Build REST API",
        skills_covered=["FastAPI", "Docker"],
    )
    assert p.portfolio_value == "High"

    c = CertificationRecommendation(
        cert_id="c1",
        title="AWS Solutions Architect",
        issuer="AWS",
    )
    assert c.priority == "High"

    r = LearningResource(
        resource_id="r1",
        title="Docker Official Docs",
        url="https://docs.docker.com",
    )
    assert r.type == "Official Documentation"

    phase = LearningPhase(
        phase_number=1,
        title="Phase 1: Core Fundamentals",
        objectives=["Master Docker"],
        expected_outcomes=["Deploy container"],
        estimated_hours=25,
        milestones=[m],
        projects=[p],
        resources=[r],
    )
    assert phase.estimated_hours == 25
    assert len(phase.milestones) == 1


def test_learning_request_response_schemas():
    """
    Test 2: Verify request and response models for Learning Roadmap API.
    """
    req = LearningRoadmapGenerateRequest(
        target_role="Principal Systems Engineer",
        target_timeframe_weeks=12,
        focus_areas=["Distributed Systems", "Rust"],
    )
    assert req.target_timeframe_weeks == 12

    now = datetime.now(timezone.utc)
    res = LearningRoadmapResponse(
        id="507f1f77bcf86cd799439011",
        user_id="user_test_99",
        target_role="Principal Systems Engineer",
        current_readiness=55,
        target_readiness=95,
        roadmap=LearningRoadmap(
            target_role="Principal Systems Engineer",
            current_readiness=55,
            target_readiness=95,
        ),
        created_at=now,
    )
    assert res.user_id == "user_test_99"
    assert res.target_readiness == 95


def test_learning_ai_service_extract_skills():
    """
    Test 3: Verify LearningRoadmapAIService._extract_skills merges Profile, Resume, GitHub, and Memory skills.
    """
    context = {
        "profile": {"skills": ["Python", "FastAPI"]},
        "resume": {"parsed_data": {"skills": ["FastAPI", "Docker", "SQL"]}},
        "github_analysis": {"top_languages": ["Python", "TypeScript"]},
        "memory": {"core_skills": ["Python", "AWS"]},
    }
    skills = LearningRoadmapAIService._extract_skills(context)
    assert "Python" in skills
    assert "FastAPI" in skills
    assert "Docker" in skills
    assert "TypeScript" in skills
    assert "AWS" in skills
    assert len(skills) == 6


def test_learning_ai_service_extract_missing_skills():
    """
    Test 4: Verify LearningRoadmapAIService._extract_missing_skills extracts gaps and includes sensible defaults.
    """
    context = {
        "memory": {"missing_skills": ["Kubernetes"]},
        "career_analysis": {"weaknesses": ["System Design"]},
        "ats_analysis": {"missing_skills": ["Redis"]},
        "job_matching": {"missing_skills": ["GraphQL"]},
    }
    missing = LearningRoadmapAIService._extract_missing_skills(context)
    assert "Kubernetes" in missing
    assert "System Design" in missing
    assert "Redis" in missing
    assert "GraphQL" in missing
    assert "Docker" in missing  # default added because count < 6


def test_learning_ai_service_fallback_roadmap():
    """
    Test 5: Verify 100% deterministic fallback learning roadmap generation creates 4 complete phases.
    """
    req = LearningRoadmapGenerateRequest(target_role="Senior Cloud Engineer", target_timeframe_weeks=10)
    context = {
        "profile": {"skills": ["Python", "Linux"]},
        "memory": {"missing_skills": ["AWS", "Kubernetes", "Terraform", "CI/CD"]},
    }
    roadmap = LearningRoadmapAIService.fallback_generate_roadmap(req, context)
    assert roadmap.target_role == "Senior Cloud Engineer"
    assert len(roadmap.learning_phases) == 4
    assert len(roadmap.certifications) >= 2
    assert len(roadmap.practice_schedule) >= 2
    assert len(roadmap.milestones) > 0
    assert len(roadmap.projects) > 0
    assert len(roadmap.resources) > 0


@pytest.mark.asyncio
async def test_learning_ai_service_generate_roadmap_with_llm():
    """
    Test 6: Verify generate_roadmap parses valid LLM JSON response correctly.
    """
    req = LearningRoadmapGenerateRequest(target_role="AI Engineer", target_timeframe_weeks=8)
    context = {"profile": {"skills": ["Python"]}}

    mock_json = """
    {
      "target_role": "AI Engineer",
      "current_readiness": 50,
      "target_readiness": 95,
      "estimated_completion": "8 weeks",
      "priority_skills": ["PyTorch", "Transformers"],
      "learning_phases": [
        {
          "phase_number": 1,
          "title": "Phase 1: Deep Learning Fundamentals",
          "objectives": ["Master PyTorch"],
          "expected_outcomes": ["Build CNN/RNN"],
          "estimated_hours": 30,
          "difficulty": "Intermediate",
          "milestones": [
            {
              "milestone_id": "m1",
              "title": "Train Custom CNN",
              "phase": 1,
              "category": "skill",
              "description": "Train image classifier",
              "skills_unlocked": ["PyTorch", "Computer Vision"]
            }
          ]
        }
      ],
      "certifications": [],
      "practice_schedule": ["Daily 2 hrs"],
      "mock_interview_schedule": ["Week 4: ML Design"],
      "revision_plan": ["Weekly review"],
      "final_career_goal": "Secure an offer as AI Engineer"
    }
    """

    with patch("services.learning_ai_service.get_llm_provider") as mock_provider:
        mock_instance = MagicMock()
        mock_instance.generate_text = AsyncMock(return_value=mock_json)
        mock_provider.return_value = mock_instance

        roadmap = await LearningRoadmapAIService.generate_roadmap("user_ai", req, context)
        assert roadmap.target_role == "AI Engineer"
        assert roadmap.priority_skills == ["PyTorch", "Transformers"]
        assert len(roadmap.learning_phases) == 1
        assert len(roadmap.milestones) == 1


@pytest.mark.asyncio
async def test_learning_ai_service_generate_roadmap_llm_failure_fallback():
    """
    Test 7: Verify generate_roadmap automatically falls back to deterministic rules when LLM throws an error.
    """
    req = LearningRoadmapGenerateRequest(target_role="DevOps Engineer", target_timeframe_weeks=6)
    context = {"profile": {"skills": ["Git"]}}

    with patch("services.learning_ai_service.get_llm_provider") as mock_provider:
        mock_instance = MagicMock()
        mock_instance.generate_text = AsyncMock(side_effect=Exception("LLM Service Unavailable"))
        mock_provider.return_value = mock_instance

        roadmap = await LearningRoadmapAIService.generate_roadmap("user_devops", req, context)
        assert roadmap.target_role == "DevOps Engineer"
        assert len(roadmap.learning_phases) == 4
        assert len(roadmap.milestones) > 0


@pytest.mark.asyncio
async def test_learning_service_generate_roadmap(mock_db):
    """
    Test 8: Verify LearningRoadmapService.generate_roadmap creates roadmap in DB and links Digital Twin Memory.
    """
    req = LearningRoadmapGenerateRequest(target_role="Senior Python Developer", target_timeframe_weeks=8)

    mock_db.learning_roadmaps.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439011"))
    )

    with patch.object(
        LearningRoadmapService,
        "generate_roadmap",
        wraps=LearningRoadmapService.generate_roadmap,
    ):
        with patch("services.digital_twin_service.DigitalTwinService.get_context", new_callable=AsyncMock) as mock_ctx:
            mock_ctx.return_value = {"profile": {"skills": ["Python", "SQL"]}}
            with patch("services.digital_twin_memory_service.DigitalTwinMemoryService.update_memory", new_callable=AsyncMock) as mock_mem:
                mock_mem.return_value = {"status": "success"}

                res = await LearningRoadmapService.generate_roadmap("user_test", req, mock_db)
                assert res.id == "507f1f77bcf86cd799439011"
                assert res.target_role == "Senior Python Developer"
                assert mock_db.learning_roadmaps.insert_one.called
                assert mock_mem.called


@pytest.mark.asyncio
async def test_learning_service_get_latest_roadmap(mock_db):
    """
    Test 9: Verify get_latest_roadmap returns most recent active roadmap for user.
    """
    now = datetime.now(timezone.utc)
    mock_doc = {
        "_id": ObjectId("507f1f77bcf86cd799439022"),
        "user_id": "user_test",
        "target_role": "Backend Lead",
        "current_readiness": 60,
        "target_readiness": 95,
        "roadmap": LearningRoadmap(target_role="Backend Lead").model_dump(),
        "milestones": [],
        "completed_items": [],
        "progress_percentage": 15.0,
        "estimated_completion": "8 weeks",
        "created_at": now,
        "updated_at": now,
    }

    mock_db.learning_roadmaps.find_one = AsyncMock(return_value=mock_doc)
    res = await LearningRoadmapService.get_latest_roadmap("user_test", mock_db)
    assert res is not None
    assert res.id == "507f1f77bcf86cd799439022"
    assert res.target_role == "Backend Lead"


@pytest.mark.asyncio
async def test_learning_service_get_roadmap_by_id_success(mock_db):
    """
    Test 10: Verify get_roadmap_by_id fetches roadmap by ObjectId or string ID.
    """
    now = datetime.now(timezone.utc)
    mock_doc = {
        "_id": ObjectId("507f1f77bcf86cd799439033"),
        "user_id": "user_100",
        "target_role": "Full Stack Engineer",
        "current_readiness": 50,
        "target_readiness": 95,
        "roadmap": LearningRoadmap(target_role="Full Stack Engineer").model_dump(),
        "created_at": now,
    }

    mock_db.learning_roadmaps.find_one = AsyncMock(return_value=mock_doc)
    res = await LearningRoadmapService.get_roadmap_by_id("user_100", "507f1f77bcf86cd799439033", mock_db)
    assert res.id == "507f1f77bcf86cd799439033"
    assert res.target_role == "Full Stack Engineer"


@pytest.mark.asyncio
async def test_learning_service_get_roadmap_by_id_not_found(mock_db):
    """
    Test 11: Verify get_roadmap_by_id raises 404 HTTPException when ID is not found.
    """
    mock_db.learning_roadmaps.find_one = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc_info:
        await LearningRoadmapService.get_roadmap_by_id("user_100", "non_existent_id", mock_db)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_learning_service_complete_milestone(mock_db):
    """
    Test 12: Verify complete_milestone updates completion, readiness score, and syncs Digital Twin Memory.
    """
    now = datetime.now(timezone.utc)
    milestone = Milestone(
        milestone_id="m1",
        title="Dockerize App",
        phase=1,
        category="skill",
        skills_unlocked=["Docker", "Containerization"],
    )
    roadmap_obj = LearningRoadmap(
        target_role="Cloud Engineer",
        current_readiness=50,
        target_readiness=95,
        milestones=[milestone],
    )
    mock_doc = {
        "_id": ObjectId("507f1f77bcf86cd799439044"),
        "user_id": "user_cloud",
        "target_role": "Cloud Engineer",
        "current_readiness": 50,
        "target_readiness": 95,
        "roadmap": roadmap_obj.model_dump(),
        "milestones": [milestone.model_dump()],
        "completed_items": [],
        "progress_percentage": 0.0,
        "estimated_completion": "8 weeks",
        "created_at": now,
        "updated_at": now,
    }

    mock_db.learning_roadmaps.find_one = AsyncMock(return_value=mock_doc)
    mock_db.learning_roadmaps.replace_one = AsyncMock()

    with patch("services.digital_twin_memory_service.DigitalTwinMemoryService.update_memory", new_callable=AsyncMock) as mock_mem:
        req = MilestoneCompleteRequest(milestone_id="m1")
        res = await LearningRoadmapService.complete_milestone(
            "user_cloud", "507f1f77bcf86cd799439044", "m1", req, mock_db
        )
        assert res.progress_percentage == 100.0
        assert res.current_readiness == 95  # 50 + (95-50)*(100/100)
        assert "Docker" in res.completed_items
        assert mock_db.learning_roadmaps.replace_one.called
        assert mock_mem.called


@pytest.mark.asyncio
async def test_learning_service_complete_milestone_not_found(mock_db):
    """
    Test 13: Verify complete_milestone raises 404 when milestone ID does not exist in roadmap.
    """
    now = datetime.now(timezone.utc)
    mock_doc = {
        "_id": ObjectId("507f1f77bcf86cd799439055"),
        "user_id": "user_test",
        "target_role": "Engineer",
        "current_readiness": 50,
        "target_readiness": 95,
        "roadmap": LearningRoadmap().model_dump(),
        "milestones": [],
        "created_at": now,
    }

    mock_db.learning_roadmaps.find_one = AsyncMock(return_value=mock_doc)
    req = MilestoneCompleteRequest(milestone_id="m99")
    with pytest.raises(HTTPException) as exc_info:
        await LearningRoadmapService.complete_milestone(
            "user_test", "507f1f77bcf86cd799439055", "m99", req, mock_db
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_learning_service_recalculate_roadmap(mock_db):
    """
    Test 14: Verify recalculate_roadmap automatically completes milestones whose skills are present in core_skills.
    """
    now = datetime.now(timezone.utc)
    milestone1 = Milestone(
        milestone_id="m1",
        title="Dockerize Service",
        skills_unlocked=["Docker"],
        completed=False,
    )
    milestone2 = Milestone(
        milestone_id="m2",
        title="Kubernetes Cluster",
        skills_unlocked=["Kubernetes"],
        completed=False,
    )
    mock_doc = {
        "_id": ObjectId("507f1f77bcf86cd799439066"),
        "user_id": "user_recalc",
        "target_role": "Platform Engineer",
        "current_readiness": 50,
        "target_readiness": 95,
        "roadmap": LearningRoadmap(milestones=[milestone1, milestone2]).model_dump(),
        "milestones": [milestone1.model_dump(), milestone2.model_dump()],
        "created_at": now,
    }

    mock_db.learning_roadmaps.find_one = AsyncMock(return_value=mock_doc)
    mock_db.learning_roadmaps.replace_one = AsyncMock()

    with patch("services.digital_twin_service.DigitalTwinService.get_context", new_callable=AsyncMock) as mock_ctx:
        mock_ctx.return_value = {
            "memory": {"core_skills": ["docker", "python", "aws"]},
        }
        res = await LearningRoadmapService.recalculate_roadmap("user_recalc", "latest", mock_db)
        assert res.progress_percentage == 50.0  # 1 out of 2 completed
        assert res.current_readiness > 50


@pytest.mark.asyncio
async def test_learning_service_get_roadmap_history(mock_db):
    """
    Test 15: Verify get_roadmap_history returns total roadmaps, latest roadmap, and summary items.
    """
    now = datetime.now(timezone.utc)
    mock_docs = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439077"),
            "user_id": "user_hist",
            "target_role": "Senior Engineer",
            "current_readiness": 70,
            "target_readiness": 95,
            "roadmap": LearningRoadmap(target_role="Senior Engineer").model_dump(),
            "progress_percentage": 50.0,
            "created_at": now,
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439088"),
            "user_id": "user_hist",
            "target_role": "Junior Engineer",
            "current_readiness": 40,
            "target_readiness": 90,
            "roadmap": LearningRoadmap(target_role="Junior Engineer").model_dump(),
            "progress_percentage": 100.0,
            "created_at": now,
        },
    ]

    cursor_mock = MagicMock()
    cursor_mock.to_list = AsyncMock(return_value=mock_docs)
    mock_db.learning_roadmaps.find.return_value.sort.return_value = cursor_mock

    res = await LearningRoadmapService.get_roadmap_history("user_hist", mock_db)
    assert res.total_roadmaps == 2
    assert res.latest_roadmap is not None
    assert len(res.history) == 2
    assert res.history[0].target_role == "Senior Engineer"


@pytest.mark.asyncio
async def test_learning_service_delete_roadmap(mock_db):
    """
    Test 16: Verify delete_roadmap deletes roadmap and returns True, or raises 404 if missing.
    """
    mock_db.learning_roadmaps.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    success = await LearningRoadmapService.delete_roadmap("user_del", "507f1f77bcf86cd799439099", mock_db)
    assert success is True

    mock_db.learning_roadmaps.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
    with pytest.raises(HTTPException) as exc_info:
        await LearningRoadmapService.delete_roadmap("user_del", "507f1f77bcf86cd799439099", mock_db)
    assert exc_info.value.status_code == 404
