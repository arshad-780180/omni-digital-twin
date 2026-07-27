import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from datetime import datetime, timezone

from services.digital_twin_memory_service import DigitalTwinMemoryService
from services.digital_twin_memory_ai_service import DigitalTwinMemoryAIService
from models.digital_twin_memory import DigitalTwinMemoryResponse, DigitalTwinSummaryResponse


@pytest.mark.asyncio
async def test_create_memory_initial_baseline():
    """1. Test creating an initial baseline memory document."""
    mock_db = MagicMock()
    mock_db.digital_twin_memory.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id=ObjectId("640000000000000000000001"))
    )

    res = await DigitalTwinMemoryService.create_memory("user_123", mock_db)
    assert isinstance(res, DigitalTwinMemoryResponse)
    assert res.user_id == "user_123"
    assert res.current_role == "Software Engineer"
    assert res.metadata["version"] == 1
    assert len(res.timeline) == 1
    assert res.timeline[0].event == "Digital Twin memory initialized"


@pytest.mark.asyncio
async def test_load_memory_existing():
    """2. Test loading existing user memory from database."""
    mock_db = MagicMock()
    mock_doc = {
        "_id": ObjectId("640000000000000000000001"),
        "user_id": "user_123",
        "current_role": "Senior Engineer",
        "target_roles": ["Lead Architect"],
        "core_skills": ["Python", "FastAPI"],
        "emerging_skills": [],
        "missing_skills": [],
        "preferred_domains": [],
        "preferred_companies": [],
        "github_strengths": [],
        "resume_strengths": [],
        "career_strengths": [],
        "ats_history_summary": [],
        "job_matching_summary": [],
        "learning_history": [],
        "interview_history": [],
        "personality_observations": [],
        "communication_observations": [],
        "career_goals": [],
        "confidence_scores": {"overall": 0.9},
        "timeline": [
            {
                "date": "2026-07-27 10:00",
                "event": "Initialized",
                "source_module": "system",
                "category": "milestone",
            }
        ],
        "metadata": {"version": 2, "update_count": 1},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    mock_db.digital_twin_memory.find_one = AsyncMock(return_value=mock_doc)

    res = await DigitalTwinMemoryService.load_memory("user_123", mock_db)
    assert res.id == "640000000000000000000001"
    assert res.current_role == "Senior Engineer"
    assert "Python" in res.core_skills


@pytest.mark.asyncio
async def test_update_memory_resume():
    """3. Test updating memory via resume payload with skill deduplication."""
    mock_db = MagicMock()
    existing_doc = {
        "_id": ObjectId("640000000000000000000001"),
        "user_id": "user_123",
        "current_role": "Software Engineer",
        "target_roles": [],
        "core_skills": ["python"],
        "emerging_skills": [],
        "missing_skills": [],
        "preferred_domains": [],
        "preferred_companies": [],
        "github_strengths": [],
        "resume_strengths": [],
        "career_strengths": [],
        "ats_history_summary": [],
        "job_matching_summary": [],
        "learning_history": [],
        "interview_history": [],
        "personality_observations": [],
        "communication_observations": [],
        "career_goals": [],
        "confidence_scores": {"overall": 0.85},
        "timeline": [],
        "metadata": {"version": 1, "update_count": 0},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    mock_db.digital_twin_memory.find_one = AsyncMock(return_value=existing_doc)
    mock_db.digital_twin_memory.replace_one = AsyncMock()

    payload = {
        "parsed_data": {
            "name": "Jane Doe",
            "skills": ["Python", "Docker", "Kubernetes"],
            "experience": [{"role": "Backend Engineer"}],
        }
    }

    res = await DigitalTwinMemoryService.update_memory("user_123", "resume", payload, mock_db)
    assert res is not None
    assert "Docker" in res.core_skills
    # Case-insensitive dedup: "python" already existed so "Python" shouldn't duplicate
    assert len([s for s in res.core_skills if s.lower() == "python"]) == 1
    assert res.metadata["version"] == 2
    assert len(res.timeline) == 1
    assert res.timeline[0].source_module == "resume"


@pytest.mark.asyncio
async def test_update_memory_github():
    """4. Test updating memory via github payload."""
    mock_db = MagicMock()
    existing_doc = {
        "_id": ObjectId("640000000000000000000001"),
        "user_id": "user_123",
        "current_role": "Software Engineer",
        "target_roles": [],
        "core_skills": ["Python"],
        "emerging_skills": [],
        "missing_skills": [],
        "preferred_domains": [],
        "preferred_companies": [],
        "github_strengths": [],
        "resume_strengths": [],
        "career_strengths": [],
        "ats_history_summary": [],
        "job_matching_summary": [],
        "learning_history": [],
        "interview_history": [],
        "personality_observations": [],
        "communication_observations": [],
        "career_goals": [],
        "confidence_scores": {"overall": 0.85},
        "timeline": [],
        "metadata": {"version": 1, "update_count": 0},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    mock_db.digital_twin_memory.find_one = AsyncMock(return_value=existing_doc)
    mock_db.digital_twin_memory.replace_one = AsyncMock()

    payload = {
        "top_languages": ["Python", "TypeScript", "Go"],
        "analysis": {"strengths": ["Consistent contributor", "Clean architecture"]},
        "github_score": 88,
    }

    res = await DigitalTwinMemoryService.update_memory("user_123", "github", payload, mock_db)
    assert res is not None
    assert "TypeScript" in res.core_skills
    assert "Consistent contributor" in res.github_strengths
    assert res.metadata["version"] == 2


@pytest.mark.asyncio
async def test_update_memory_career_ats_job_matching():
    """5. Test updating memory via career, ats, and job_matching modules."""
    mock_db = MagicMock()
    existing_doc = {
        "_id": ObjectId("640000000000000000000001"),
        "user_id": "user_123",
        "current_role": "Software Engineer",
        "target_roles": [],
        "core_skills": ["Python"],
        "emerging_skills": [],
        "missing_skills": [],
        "preferred_domains": [],
        "preferred_companies": [],
        "github_strengths": [],
        "resume_strengths": [],
        "career_strengths": [],
        "ats_history_summary": [],
        "job_matching_summary": [],
        "learning_history": [],
        "interview_history": [],
        "personality_observations": [],
        "communication_observations": [],
        "career_goals": [],
        "confidence_scores": {"overall": 0.85},
        "timeline": [],
        "metadata": {"version": 1, "update_count": 0},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    mock_db.digital_twin_memory.find_one = AsyncMock(return_value=existing_doc)
    mock_db.digital_twin_memory.replace_one = AsyncMock()

    # ATS Update
    ats_payload = {
        "job_title": "AI Engineer",
        "company": "DeepMind",
        "match_score": 82,
        "missing_keywords": ["PyTorch"],
        "matched_keywords": ["Python"],
    }
    res = await DigitalTwinMemoryService.update_memory("user_123", "ats", ats_payload, mock_db)
    assert "AI Engineer" in res.target_roles
    assert "DeepMind" in res.preferred_companies
    assert "PyTorch" in res.missing_skills
    assert len(res.ats_history_summary) == 1


@pytest.mark.asyncio
async def test_rebuild_memory_from_history():
    """6. Test rebuilding complete memory from historical collections."""
    mock_db = MagicMock()
    mock_db.digital_twin_memory.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id=ObjectId("640000000000000000000001"))
    )
    mock_db.digital_twin_memory.replace_one = AsyncMock()

    # Mock profile
    mock_db.profiles.find_one = AsyncMock(return_value={"user_id": "user_123", "full_name": "Test User", "skills": ["Python"]})

    # Mock resumes
    mock_res_cursor = MagicMock()
    mock_res_cursor.sort.return_value = mock_res_cursor
    mock_res_cursor.limit.return_value = mock_res_cursor
    mock_res_cursor.to_list = AsyncMock(return_value=[
        {"parsed_data": {"name": "Test User", "skills": ["Docker", "Kubernetes"]}}
    ])
    mock_db.resumes.find.return_value = mock_res_cursor

    # Mock other cursors as empty
    for col in [mock_db.github_analysis, mock_db.career_analysis, mock_db.ats_analysis, mock_db.job_matches]:
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[])
        col.find.return_value = mock_cursor

    res = await DigitalTwinMemoryService.rebuild_memory_from_history("user_123", mock_db)
    assert res is not None
    assert "Docker" in res.core_skills
    assert "Python" in res.core_skills


@pytest.mark.asyncio
async def test_summarize_long_histories():
    """7. Test capping timeline and history summaries when exceeding thresholds."""
    doc = {
        "timeline": [{"event": f"Event {i}"} for i in range(60)],
        "ats_history_summary": [f"ATS {i}" for i in range(40)],
        "job_matching_summary": [f"Job {i}" for i in range(40)],
    }
    capped = DigitalTwinMemoryService.summarize_long_histories(doc)
    assert len(capped["timeline"]) == 50
    assert len(capped["ats_history_summary"]) == 30
    assert len(capped["job_matching_summary"]) == 30


@pytest.mark.asyncio
async def test_ai_summary_and_fallback():
    """8. Test AI summary synthesis and rule-based fallback."""
    user_id = "user_123"
    memory_doc = {
        "current_role": "Senior Engineer",
        "target_roles": ["Lead Architect"],
        "core_skills": ["Python", "FastAPI", "React"],
        "github_strengths": ["Clean code"],
        "resume_strengths": ["Led 5 projects"],
        "missing_skills": ["Kubernetes"],
    }

    # Test fallback directly
    summary = DigitalTwinMemoryAIService.fallback_rule_based_summary(memory_doc)
    assert isinstance(summary, DigitalTwinSummaryResponse)
    assert "Senior Engineer" in summary.executive_summary
    assert "Clean code" in summary.top_strengths

    # Test summarize_memory wrapper
    sum_resp, method = await DigitalTwinMemoryAIService.summarize_memory(user_id, memory_doc)
    assert isinstance(sum_resp, DigitalTwinSummaryResponse)
    assert method in ["gemini-pro", "rule_based"]
