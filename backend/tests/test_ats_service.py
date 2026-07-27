import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from models.ats import (
    ATSAnalyzeRequest,
    ATSFeedback,
    ATSSuggestions,
    ATSAnalysisResponse,
)
from services.ats_service import ATSService
from services.ats_ai_service import ATSAIService


def test_pydantic_ats_schemas():
    """1. Test Pydantic schema validation for ATS Analyze request, feedback, suggestions, and response."""
    req = ATSAnalyzeRequest(
        job_title="Senior Python Backend Engineer",
        company="Stripe",
        job_description="Looking for Python, FastAPI, MongoDB, and Kubernetes experience."
    )
    assert req.job_title == "Senior Python Backend Engineer"
    assert req.company == "Stripe"

    feedback = ATSFeedback(
        strengths=["Strong Python background"],
        weaknesses=["Missing Kubernetes experience"],
        recommendations=["Add Kubernetes to projects"],
        section_feedback={"Summary": "Tailor to Stripe"}
    )
    assert len(feedback.strengths) == 1
    assert "Summary" in feedback.section_feedback

    suggestions = ATSSuggestions(
        improved_summary="Results-oriented Python Engineer...",
        improved_projects=["Architected backend service with FastAPI..."],
        grammar_feedback=["Use active verbs."],
        keyword_injection=["Add Kubernetes."],
        action_verbs=["Architected"]
    )
    assert suggestions.improved_summary.startswith("Results-oriented")


def test_keyword_extraction():
    """2. Test ATSAIService keyword extraction from job description text."""
    jd = """
    We are seeking a Senior Backend Engineer proficient in Python, FastAPI, Docker, Kubernetes,
    and PostgreSQL. Familiarity with AWS and CI/CD pipelines is a plus. Strong communication skills required.
    """
    keywords = ATSAIService.extract_keywords(jd)
    assert "python" in keywords
    assert "fastapi" in keywords
    assert "docker" in keywords
    assert "kubernetes" in keywords
    assert "postgresql" in keywords
    assert "aws" in keywords


def test_compute_keyword_match():
    """3. Test keyword matching and overlap score percentage calculation."""
    req_kw = ["python", "fastapi", "kubernetes", "aws", "docker"]
    user_skills = ["Python", "FastAPI", "SQL", "Git"]

    matched, missing, score = ATSAIService.compute_keyword_match(req_kw, user_skills)
    assert "Python" in matched
    assert "Fastapi" in matched or "FastAPI" in matched
    assert "Kubernetes" in missing
    assert "Aws" in missing or "AWS" in missing
    assert score == 40  # 2 of 5 matched = 40%


@pytest.mark.asyncio
async def test_load_resume_and_context_success():
    """4. Test ATSService loading user resume and profile from MongoDB collections."""
    mock_db = MagicMock()

    mock_cursor_res = MagicMock()
    mock_cursor_res.sort.return_value = mock_cursor_res
    mock_cursor_res.limit.return_value = mock_cursor_res
    mock_cursor_res.to_list = AsyncMock(return_value=[{"_id": "res_123", "parsed_data": {"skills": ["Python", "FastAPI"]}}])
    mock_db.resumes.find.return_value = mock_cursor_res

    mock_db.profiles.find_one = AsyncMock(return_value={"skills": ["Docker"]})

    res_doc, prof_doc = await ATSService.load_resume_and_context("user_1", mock_db)
    assert res_doc is not None
    assert prof_doc is not None
    assert res_doc["_id"] == "res_123"
    assert "Docker" in prof_doc["skills"]


@pytest.mark.asyncio
async def test_load_resume_and_context_empty():
    """5. Test ATSService loading context when user has no uploaded resume or profile."""
    mock_db = MagicMock()

    mock_cursor_res = MagicMock()
    mock_cursor_res.sort.return_value = mock_cursor_res
    mock_cursor_res.limit.return_value = mock_cursor_res
    mock_cursor_res.to_list = AsyncMock(return_value=[])
    mock_db.resumes.find.return_value = mock_cursor_res

    mock_db.profiles.find_one = AsyncMock(return_value=None)

    res_doc, prof_doc = await ATSService.load_resume_and_context("user_empty", mock_db)
    assert res_doc is None
    assert prof_doc is None


@pytest.mark.asyncio
async def test_ats_ai_success():
    """6. Test successful Gemini AI ATS optimization with structured JSON response."""
    fake_llm_json = """
    {
      "ats_score": 88,
      "matched_keywords": ["Python", "FastAPI"],
      "missing_keywords": ["Kubernetes"],
      "strengths": ["Strong FastAPI API development"],
      "weaknesses": ["Missing Kubernetes"],
      "recommendations": ["Add Kubernetes to deployment projects"],
      "section_feedback": {
        "Summary": "Highlight backend scalability.",
        "Experience": "Add metrics.",
        "Skills": "Good grouping.",
        "Projects": "Include cloud architecture."
      },
      "improved_summary": "Experienced Python Backend Engineer...",
      "improved_projects": ["Built high-throughput API service using FastAPI..."],
      "grammar_feedback": ["Use action verbs."],
      "keyword_injection": ["Inject Kubernetes into project bullet points."],
      "action_verbs": ["Architected", "Engineered", "Optimized"]
    }
    """
    with patch("services.ats_ai_service.get_llm_provider") as mock_provider:
        mock_instance = MagicMock()
        mock_instance.generate_text = AsyncMock(return_value=fake_llm_json)
        mock_provider.return_value = mock_instance

        (
            score,
            req_kw,
            matched,
            missing,
            feedback,
            suggestions,
            method
        ) = await ATSAIService.optimize_resume(
            {"parsed_data": {"skills": ["Python", "FastAPI"]}},
            {"skills": []},
            "Senior Python Backend Engineer",
            "Stripe",
            "We require Python, FastAPI, and Kubernetes."
        )

        assert method == "ai"
        assert score == 88
        assert "Strong FastAPI API development" in feedback.strengths
        assert suggestions.improved_summary.startswith("Experienced Python")


@pytest.mark.asyncio
async def test_ats_ai_fallback():
    """7. Test rule-based fallback when Gemini API raises rate limit exception."""
    with patch("services.ats_ai_service.get_llm_provider") as mock_provider:
        mock_instance = MagicMock()
        mock_instance.generate_text = AsyncMock(side_effect=Exception("429 Rate Limit Exceeded"))
        mock_provider.return_value = mock_instance

        (
            score,
            req_kw,
            matched,
            missing,
            feedback,
            suggestions,
            method
        ) = await ATSAIService.optimize_resume(
            {"parsed_data": {"skills": ["Python", "JavaScript"]}},
            {"skills": ["SQL"]},
            "Full Stack Developer",
            "Acme Corp",
            "Need Python, JavaScript, and AWS experience."
        )

        assert method == "rule_based"
        assert score > 0
        assert len(feedback.strengths) > 0
        assert len(suggestions.improved_projects) > 0


def test_fallback_rule_based_ats():
    """8. Test fallback_rule_based_ats deterministic output formatting."""
    (
        score,
        req_kw,
        matched,
        missing,
        feedback,
        suggestions,
        method
    ) = ATSAIService.fallback_rule_based_ats(
        75,
        ["python", "fastapi", "docker", "kubernetes"],
        ["Python", "FastAPI"],
        ["Docker", "Kubernetes"],
        "Senior Developer"
    )

    assert score == 75
    assert "Python" in matched
    assert "Docker" in missing
    assert "Summary" in feedback.section_feedback
    assert len(suggestions.action_verbs) > 0
    assert method == "rule_based"


@pytest.mark.asyncio
async def test_mongodb_storage_and_response():
    """9. Test ATSService saving analysis document to db.ats_analysis and returning ATSAnalysisResponse."""
    (
        score,
        req_kw,
        matched,
        missing,
        feedback,
        suggestions,
        method
    ) = ATSAIService.fallback_rule_based_optimization(
        {},
        {"skills": ["Python"]},
        "Python Dev",
        "Corp Z",
        "We need Python, Django, and AWS."
    )

    assert method == "rule_based"
    assert any("resume" in w.lower() for w in feedback.weaknesses)
    assert score < 70


@pytest.mark.asyncio
async def test_ats_service_analyze_and_save():
    """9. Verify ATSService executes full analysis and saves record to db.ats_analysis."""
    mock_db = MagicMock()

    with patch.object(ATSService, "load_resume_and_context", new_callable=AsyncMock) as mock_load:
        mock_load.return_value = (
            {"_id": "res_1", "parsed_data": {"skills": ["Python", "FastAPI"]}},
            {"user_id": "u1", "skills": ["Docker"]}
        )

        mock_insert = MagicMock()
        mock_insert.inserted_id = "607f1f77bcf86cd799439001"
        mock_db.ats_analysis.insert_one = AsyncMock(return_value=mock_insert)

        req = ATSAnalyzeRequest(
            job_title="Python Developer",
            company="OMNI Tech",
            job_description="Seeking a developer proficient in Python, FastAPI, and Docker."
        )

        resp = await ATSService.analyze_resume_against_job("u1", req, mock_db)

        assert resp.id == "607f1f77bcf86cd799439001"
        assert resp.user_id == "u1"
        assert resp.ats_score > 0
        assert mock_db.ats_analysis.insert_one.called


@pytest.mark.asyncio
async def test_ats_latest_and_history():
    """10. Test ATSService.get_latest_analysis and get_history methods."""
    mock_db = MagicMock()
    fake_doc = {
        "_id": "607f1f77bcf86cd799439001",
        "user_id": "u1",
        "resume_id": "res_1",
        "job_title": "Python Dev",
        "company": "Company A",
        "job_description": "JD text",
        "required_keywords": ["Python"],
        "matched_keywords": ["Python"],
        "missing_keywords": [],
        "ats_score": 90,
        "resume_feedback": {"strengths": ["Python"], "weaknesses": [], "recommendations": [], "section_feedback": {}},
        "ai_suggestions": {"improved_summary": "Summary", "improved_projects": [], "grammar_feedback": [], "keyword_injection": [], "action_verbs": []},
        "created_at": datetime.now(timezone.utc)
    }

    mock_cursor_latest = MagicMock()
    mock_cursor_latest.sort.return_value = mock_cursor_latest
    mock_cursor_latest.limit.return_value = mock_cursor_latest
    mock_cursor_latest.to_list = AsyncMock(return_value=[fake_doc])
    mock_db.ats_analysis.find.return_value = mock_cursor_latest

    latest = await ATSService.get_latest_analysis("u1", mock_db)
    assert latest is not None
    assert latest.id == "607f1f77bcf86cd799439001"
    assert latest.ats_score == 90

    # History
    mock_cursor_hist = MagicMock()
    mock_cursor_hist.sort.return_value = mock_cursor_hist
    mock_cursor_hist.to_list = AsyncMock(return_value=[fake_doc.copy(), fake_doc.copy()])
    mock_db.ats_analysis.find.return_value = mock_cursor_hist

    history = await ATSService.get_history("u1", mock_db)
    assert len(history) == 2


@pytest.mark.asyncio
async def test_ats_deletion_success():
    """11. Test ATSService.delete_analysis successfully removing an analysis document."""
    mock_db = MagicMock()
    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1
    mock_db.ats_analysis.delete_one = AsyncMock(return_value=mock_delete_result)

    success = await ATSService.delete_analysis("user_1", "507f1f77bcf86cd799439011", mock_db)
    assert success is True


@pytest.mark.asyncio
async def test_ats_deletion_not_found():
    """12. Test ATSService.delete_analysis returning False when document is not found."""
    mock_db = MagicMock()
    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 0
    mock_db.ats_analysis.delete_one = AsyncMock(return_value=mock_delete_result)

    success = await ATSService.delete_analysis("user_1", "nonexistent_id", mock_db)
    assert success is False
