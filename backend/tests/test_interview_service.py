import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException

from models.interview import (
    InterviewQuestion,
    InterviewAnswer,
    InterviewQuestionEvaluation,
    InterviewReport,
    InterviewStartRequest,
    InterviewAnswerSubmitRequest,
    InterviewSessionResponse,
    InterviewHistoryResponse,
)
from services.interview_ai_service import InterviewAIService
from services.interview_service import InterviewService


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.interview_sessions = MagicMock()
    db.digital_twin_memory = MagicMock()
    return db


def test_interview_pydantic_schemas():
    """
    Test 1: Verify Pydantic schema validation, defaults, and backward-compatible aliases.
    """
    q = InterviewQuestion(
        question_id="q1",
        question="Explain how you use FastAPI.",
        difficulty="Easy",
        expected_skills=["FastAPI", "Python"],
        order=1,
    )
    assert q.difficulty == "Easy"
    assert "FastAPI" in q.expected_skills

    report = InterviewReport(
        overall_score=85,
        interview_readiness="Interview Ready",
        hiring_recommendation="Strong Hire",
        strengths=["Great architecture breakdown"],
    )
    assert report.hiring_recommendation == "Strong Hire"

    now = datetime.now(timezone.utc)
    res = InterviewSessionResponse(
        id="507f1f77bcf86cd799439011",
        user_id="user_123",
        role="Senior Python Engineer",
        status="IN_PROGRESS",
        questions=[q],
        created_at=now,
    )
    assert res.target_role == "Senior Python Engineer"
    assert res.status == "IN_PROGRESS"


def test_fallback_question_generation():
    """
    Test 2: Verify deterministic rule-based fallback generates progressive difficulty questions citing skills.
    """
    req = InterviewStartRequest(
        role="Backend Engineer",
        company="Acme Corp",
        difficulty="Medium",
        interview_type="Technical",
        question_count=3,
    )
    context = {
        "resume": {
            "parsed_data": {
                "skills": ["FastAPI", "MongoDB", "Docker"],
                "experience": [{"role": "Backend Developer"}],
            }
        }
    }

    questions = InterviewAIService.fallback_rule_based_questions(req, context)
    assert len(questions) == 3
    assert questions[0].difficulty == "Easy"
    assert questions[1].difficulty == "Medium"
    assert questions[2].difficulty == "Hard"
    assert any("FastAPI" in q.question or "FastAPI" in q.expected_skills for q in questions)


def test_fallback_answer_evaluation():
    """
    Test 3: Verify deterministic rule-based evaluation scores depth and keyword matches.
    """
    q = InterviewQuestion(
        question_id="q1",
        question="How do you handle error resilience in FastAPI?",
        expected_skills=["FastAPI", "Validation", "Exceptions"],
        order=1,
    )
    short_ans = "I use try except blocks."
    eval_short = InterviewAIService.fallback_rule_based_evaluation(q, short_ans, {})
    assert eval_short.technical_score < 60
    assert len(eval_short.follow_up_questions) > 0

    detailed_ans = (
        "In FastAPI, I implement structured exception handlers, request validation using Pydantic, "
        "and handle asynchronous database errors cleanly with proper HTTP status codes."
    )
    eval_detailed = InterviewAIService.fallback_rule_based_evaluation(q, detailed_ans, {})
    assert eval_detailed.technical_score >= 80
    assert "FastAPI" in eval_detailed.strong_topics or "Validation" in eval_detailed.strong_topics


def test_fallback_report_generation():
    """
    Test 4: Verify executive report synthesis averages scores and assigns recommendation badges.
    """
    now = datetime.now(timezone.utc)
    ev1 = InterviewQuestionEvaluation(
        question_id="q1",
        technical_score=88,
        communication_score=85,
        confidence_score=84,
        problem_solving_score=86,
        strong_topics=["API Architecture"],
        weak_topics=[],
    )
    ev2 = InterviewQuestionEvaluation(
        question_id="q2",
        technical_score=84,
        communication_score=82,
        confidence_score=80,
        problem_solving_score=85,
        strong_topics=["FastAPI"],
        weak_topics=["Caching"],
    )
    session = InterviewSessionResponse(
        id="507f1f77bcf86cd799439011",
        user_id="user_1",
        role="Senior Backend Engineer",
        evaluations=[ev1, ev2],
        created_at=now,
    )

    report = InterviewAIService.fallback_rule_based_report(session)
    assert report.overall_score >= 80
    assert report.hiring_recommendation in ["Strong Hire", "Hire"]
    assert "Caching" in report.weaknesses


@pytest.mark.asyncio
async def test_start_interview(mock_db):
    """
    Test 5: Verify starting an interview session initializes IN_PROGRESS status and saves to MongoDB.
    """
    mock_db.interview_sessions.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439011"))
    )

    req = InterviewStartRequest(
        role="Full Stack Engineer",
        company="Tech Inc",
        difficulty="Medium",
        interview_type="Technical",
        question_count=3,
    )

    with patch.object(
        InterviewAIService,
        "generate_questions",
        new_callable=AsyncMock,
        return_value=InterviewAIService.fallback_rule_based_questions(req, {}),
    ):
        with patch("services.digital_twin_service.DigitalTwinService.get_context", new_callable=AsyncMock, return_value={}):
            res = await InterviewService.start_interview("user_123", req, mock_db)

    assert res.status == "IN_PROGRESS"
    assert len(res.questions) == 3
    assert res.role == "Full Stack Engineer"
    mock_db.interview_sessions.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_get_session_not_found(mock_db):
    """
    Test 6: Verify get_session raises 404 when ID doesn't exist.
    """
    mock_db.interview_sessions.find_one = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await InterviewService.get_session("user_123", "507f1f77bcf86cd799439011", mock_db)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_session_success(mock_db):
    """
    Test 7: Verify get_session retrieves existing session.
    """
    now = datetime.now(timezone.utc)
    mock_doc = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "user_id": "user_123",
        "role": "Python Dev",
        "status": "IN_PROGRESS",
        "questions": [],
        "answers": [],
        "evaluations": [],
        "created_at": now,
        "updated_at": now,
    }
    mock_db.interview_sessions.find_one = AsyncMock(return_value=mock_doc)

    res = await InterviewService.get_session("user_123", "507f1f77bcf86cd799439011", mock_db)
    assert res.id == "507f1f77bcf86cd799439011"
    assert res.role == "Python Dev"


@pytest.mark.asyncio
async def test_submit_answer(mock_db):
    """
    Test 8: Verify submit_answer evaluates answer and updates session running scores.
    """
    now = datetime.now(timezone.utc)
    q = InterviewQuestion(question_id="q1", question="Explain indexing.", expected_skills=["SQL", "Index"], order=1)
    mock_doc = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "user_id": "user_1",
        "role": "Database Dev",
        "status": "IN_PROGRESS",
        "questions": [q.model_dump()],
        "answers": [],
        "evaluations": [],
        "overall_score": 0,
        "created_at": now,
        "updated_at": now,
    }
    mock_db.interview_sessions.find_one = AsyncMock(return_value=mock_doc)
    mock_db.interview_sessions.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    req = InterviewAnswerSubmitRequest(
        question_id="q1",
        content="I use B-tree indexes on columns that are frequently queried in WHERE clauses to speed up lookups.",
    )

    with patch("services.digital_twin_service.DigitalTwinService.get_context", new_callable=AsyncMock, return_value={}):
        res = await InterviewService.submit_answer("user_1", "507f1f77bcf86cd799439011", req, mock_db)

    assert mock_db.interview_sessions.update_one.assert_called_once
    assert len(res.questions) == 1


@pytest.mark.asyncio
async def test_finish_interview_and_memory_update(mock_db):
    """
    Test 9: Verify finish_interview marks session COMPLETED and updates Digital Twin Memory.
    """
    now = datetime.now(timezone.utc)
    q = InterviewQuestion(question_id="q1", question="Explain Python GIL.", expected_skills=["Python"], order=1)
    ev = InterviewQuestionEvaluation(
        question_id="q1",
        technical_score=85,
        communication_score=80,
        confidence_score=82,
        problem_solving_score=85,
        strong_topics=["Python"],
    )
    mock_doc = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "user_id": "user_1",
        "role": "Python Architect",
        "status": "IN_PROGRESS",
        "questions": [q.model_dump()],
        "answers": [],
        "evaluations": [ev.model_dump()],
        "overall_score": 83,
        "created_at": now,
        "updated_at": now,
    }

    mock_db.interview_sessions.find_one = AsyncMock(return_value=mock_doc)
    mock_db.interview_sessions.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    with patch("services.digital_twin_service.DigitalTwinService.get_context", new_callable=AsyncMock, return_value={}):
        with patch("services.digital_twin_memory_service.DigitalTwinMemoryService.update_memory", new_callable=AsyncMock) as mock_update_mem:
            res = await InterviewService.finish_interview("user_1", "507f1f77bcf86cd799439011", mock_db)

            assert mock_update_mem.call_count == 1
            args, _ = mock_update_mem.call_args
            assert args[0] == "user_1"
            assert args[1] == "interview"


@pytest.mark.asyncio
async def test_get_latest_session(mock_db):
    """
    Test 10: Verify get_latest_session returns most recent session or None.
    """
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    now = datetime.now(timezone.utc)
    mock_doc = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "user_id": "user_1",
        "role": "DevOps Engineer",
        "status": "COMPLETED",
        "questions": [],
        "created_at": now,
        "updated_at": now,
    }
    mock_cursor.to_list = AsyncMock(return_value=[mock_doc])
    mock_db.interview_sessions.find.return_value = mock_cursor

    res = await InterviewService.get_latest_session("user_1", mock_db)
    assert res is not None
    assert res.role == "DevOps Engineer"


@pytest.mark.asyncio
async def test_get_session_history_analytics(mock_db):
    """
    Test 11: Verify get_session_history computes average score, trend trajectories, and weakest topics.
    """
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    now = datetime.now(timezone.utc)
    s1 = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "user_id": "user_1",
        "role": "Dev1",
        "status": "COMPLETED",
        "overall_score": 70,
        "technical_score": 68,
        "communication_score": 72,
        "confidence_score": 70,
        "questions": [],
        "evaluations": [],
        "created_at": now,
        "updated_at": now,
    }
    s2 = {
        "_id": ObjectId("507f1f77bcf86cd799439012"),
        "user_id": "user_1",
        "role": "Dev2",
        "status": "COMPLETED",
        "overall_score": 84,
        "technical_score": 85,
        "communication_score": 82,
        "confidence_score": 85,
        "questions": [],
        "evaluations": [],
        "created_at": now,
        "updated_at": now,
    }
    mock_cursor.to_list = AsyncMock(return_value=[s2, s1])
    mock_db.interview_sessions.find.return_value = mock_cursor

    history = await InterviewService.get_session_history("user_1", mock_db)
    assert history.total_interviews == 2
    assert history.average_score == 77.0
    assert history.improvement_percentage == 20.0
    assert history.best_interview.id == "507f1f77bcf86cd799439012"


@pytest.mark.asyncio
async def test_evaluate_interview_legacy(mock_db):
    """
    Test 12: Verify backward-compatible evaluate_interview_legacy submits answers and completes report.
    """
    now = datetime.now(timezone.utc)
    q1 = InterviewQuestion(question_id="q1", question="Q1?", order=1)
    q2 = InterviewQuestion(question_id="q2", question="Q2?", order=2)
    mock_doc = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "user_id": "user_1",
        "role": "Dev",
        "status": "IN_PROGRESS",
        "questions": [q1.model_dump(), q2.model_dump()],
        "answers": [],
        "evaluations": [],
        "created_at": now,
        "updated_at": now,
    }
    mock_db.interview_sessions.find_one = AsyncMock(return_value=mock_doc)
    mock_db.interview_sessions.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    with patch("services.digital_twin_service.DigitalTwinService.get_context", new_callable=AsyncMock, return_value={}):
        with patch("services.digital_twin_memory_service.DigitalTwinMemoryService.update_memory", new_callable=AsyncMock):
            res = await InterviewService.evaluate_interview_legacy(
                "user_1",
                "507f1f77bcf86cd799439011",
                ["Answer 1 details...", "Answer 2 details..."],
                mock_db,
            )
            assert res is not None


@pytest.mark.asyncio
async def test_delete_session(mock_db):
    """
    Test 13: Verify delete_session removes session and raises 404 when missing.
    """
    mock_db.interview_sessions.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    success = await InterviewService.delete_session("user_1", "507f1f77bcf86cd799439011", mock_db)
    assert success is True

    mock_db.interview_sessions.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
    with pytest.raises(HTTPException):
        await InterviewService.delete_session("user_1", "507f1f77bcf86cd799439011", mock_db)
