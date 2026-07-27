import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import json

from models.analytics import (
    CareerHealthScore,
    CareerAnalytics,
    ATSAnalytics,
    JobMatchAnalytics,
    InterviewAnalytics,
    LearningAnalyticsSummary,
    DigitalTwinAnalytics,
    SkillAnalytics,
    TimelineEvent,
    ExecutiveInsights,
    DashboardSummary,
)
from services.analytics_service import AnalyticsService, REQUIRED_SKILLS
from services.analytics_ai_service import AnalyticsAIService


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.career_analysis = MagicMock()
    db.ats_analysis = MagicMock()
    db.job_matches = MagicMock()
    db.interview_sessions = MagicMock()
    db.learning_roadmaps = MagicMock()
    db.digital_twin_memory = MagicMock()
    db.profiles = MagicMock()
    db.resumes = MagicMock()
    db.github_analysis = MagicMock()
    return db


def test_analytics_pydantic_schemas():
    """
    Test 1: Verify instantiation, default values, and validation of all 11 Pydantic schemas in models/analytics.py.
    """
    health = CareerHealthScore(
        overall_score=85,
        readiness_component=22.5,
        ats_component=17.0,
        job_match_component=16.0,
        interview_component=18.0,
        learning_component=8.5,
        project_milestone_bonus=3.0,
        status="Excellent",
    )
    assert health.overall_score == 85
    assert health.status == "Excellent"

    career = CareerAnalytics(
        current_score=82,
        historical_trend=[75, 78, 82],
        monthly_improvement=7.0,
    )
    assert career.current_score == 82
    assert len(career.historical_trend) == 3

    ats = ATSAnalytics(
        latest_score=80,
        average_score=75.5,
        historical_trend=[70, 75, 80],
        keyword_coverage=85.0,
        top_missing_skills=["Kubernetes", "GraphQL"],
    )
    assert ats.keyword_coverage == 85.0
    assert "Kubernetes" in ats.top_missing_skills

    job = JobMatchAnalytics(
        latest_match_score=88,
        average_match_score=82.0,
        best_matching_role="Senior Cloud Engineer",
        hiring_recommendation_trend=["Hire", "Strong Hire"],
    )
    assert job.best_matching_role == "Senior Cloud Engineer"

    intv = InterviewAnalytics(
        technical_score_trend=[75, 85],
        communication_trend=[80, 88],
        confidence_trend=[78, 82],
        problem_solving_trend=[70, 80],
        average_interview_score=82.5,
        interview_success_rate=90.0,
    )
    assert intv.interview_success_rate == 90.0

    lr = LearningAnalyticsSummary(
        learning_progress=60.0,
        completed_milestones=6,
        completed_projects=2,
        completed_certifications=1,
        learning_velocity=1.5,
    )
    assert lr.completed_projects == 2

    twin = DigitalTwinAnalytics(
        core_skills=["Python", "FastAPI"],
        emerging_skills=["Docker"],
        missing_skills=["Kubernetes"],
        career_evolution_timeline=["Profile Created", "GitHub Connected"],
        strength_growth=2,
        weakness_reduction=1,
    )
    assert "Python" in twin.core_skills

    skill = SkillAnalytics(
        skill_name="Python",
        current_level="Advanced",
        growth_trend="Accelerating",
        target_level="Expert",
        score=90,
    )
    assert skill.skill_name == "Python"
    assert skill.score == 90

    evt = TimelineEvent(
        event_id="evt_1",
        event_type="Resume Uploaded",
        title="Resume Parsed",
        description="Parsed resume successfully",
        timestamp=datetime.now(timezone.utc),
        module_source="resume",
        impact_score=15,
    )
    assert evt.module_source == "resume"

    ins = ExecutiveInsights(
        current_strengths=["Strong readiness"],
        weakest_areas=["ATS keyword match"],
        biggest_improvement="Upward interview score",
        career_risks=["Keyword gaps"],
        recommended_next_action="Optimize resume keywords",
        estimated_readiness="85% - Interview Ready",
        ai_generated=False,
    )
    assert ins.ai_generated is False

    summary = DashboardSummary(
        user_id="user_test_123",
        career_health_score=health,
        career_readiness_score=82,
        ats_score=80,
        job_match_score=88,
        interview_score=85,
        learning_progress=60.0,
        digital_twin_confidence=89.5,
        career_goal_progress=91.1,
        overall_career_health_score=85,
        career_analytics=career,
        ats_analytics=ats,
        job_match_analytics=job,
        interview_analytics=intv,
        learning_analytics=lr,
        digital_twin_analytics=twin,
        skill_matrix=[skill],
        timeline=[evt],
        insights=ins,
    )
    assert summary.user_id == "user_test_123"
    assert summary.overall_career_health_score == 85


def test_calculate_career_health_score_excellent():
    """
    Test 2: Verify deterministic Career Health Score calculation for high scores (status Excellent).
    """
    res = AnalyticsService.calculate_career_health_score(
        readiness_score=90,
        ats_score=88,
        job_match_score=86,
        interview_score=92,
        learning_progress=80.0,
        completed_projects=2,
        completed_milestones=4,
    )
    assert res.overall_score >= 85
    assert res.status == "Excellent"


def test_calculate_career_health_score_strong():
    """
    Test 3: Verify deterministic Career Health Score calculation for medium-high scores (status Strong).
    """
    res = AnalyticsService.calculate_career_health_score(
        readiness_score=80,
        ats_score=75,
        job_match_score=75,
        interview_score=80,
        learning_progress=70.0,
    )
    # 20.0 + 15.0 + 15.0 + 16.0 + 7.0 = 73
    assert 70 <= res.overall_score < 85
    assert res.status == "Strong"


def test_calculate_career_health_score_moderate():
    """
    Test 4: Verify deterministic Career Health Score calculation for moderate scores (status Moderate).
    """
    res = AnalyticsService.calculate_career_health_score(
        readiness_score=55,
        ats_score=60,
        job_match_score=58,
        interview_score=52,
        learning_progress=30.0,
    )
    assert 50 <= res.overall_score < 70
    assert res.status == "Moderate"


def test_calculate_career_health_score_needs_attention():
    """
    Test 5: Verify deterministic Career Health Score calculation for low scores (status Needs Attention).
    """
    res = AnalyticsService.calculate_career_health_score(
        readiness_score=40,
        ats_score=35,
        job_match_score=45,
        interview_score=42,
        learning_progress=10.0,
    )
    assert res.overall_score < 50
    assert res.status == "Needs Attention"


def test_calculate_career_health_score_with_bonus():
    """
    Test 6: Verify project and milestone bonus points are capped at 5.0 and correctly added.
    """
    res_no_bonus = AnalyticsService.calculate_career_health_score(
        readiness_score=72,
        ats_score=70,
        job_match_score=70,
        interview_score=70,
        learning_progress=50.0,
        completed_projects=0,
        completed_milestones=0,
    )
    # 72 * 0.25 (18) + 14 + 14 + 14 + 5 = 65
    res_with_bonus = AnalyticsService.calculate_career_health_score(
        readiness_score=72,
        ats_score=70,
        job_match_score=70,
        interview_score=70,
        learning_progress=50.0,
        completed_projects=5,  # 5 * 2.0 = 10 -> should be capped at 5.0
        completed_milestones=10,
    )
    # 65 + 5 = 70
    assert res_with_bonus.project_milestone_bonus == 5.0
    assert res_with_bonus.overall_score == min(100, res_no_bonus.overall_score + 5)


@pytest.mark.asyncio
async def test_get_career_analytics():
    """
    Test 7: Verify get_career_analytics with mock DB history and score trend calculations.
    """
    db = MagicMock()
    with patch.object(
        AnalyticsService,
        "_safe_find_history",
        AsyncMock(
            return_value=[
                {"overall_readiness_score": 68, "created_at": datetime(2026, 6, 1, tzinfo=timezone.utc)},
                {"overall_readiness_score": 75, "created_at": datetime(2026, 7, 1, tzinfo=timezone.utc)},
            ]
        ),
    ):
        res = await AnalyticsService.get_career_analytics("user_1", db)
        assert res.current_score == 75
        assert res.historical_trend == [68, 75]
        assert res.monthly_improvement == 7.0
        assert len(res.history_labels) == 2


@pytest.mark.asyncio
async def test_get_ats_analytics():
    """
    Test 8: Verify get_ats_analytics keyword coverage and unique missing skills.
    """
    db = MagicMock()
    with patch.object(
        AnalyticsService,
        "_safe_find_history",
        AsyncMock(
            return_value=[
                {
                    "ats_match_percentage": 70,
                    "matched_keywords": ["python", "fastapi"],
                    "missing_keywords": ["kubernetes", "docker"],
                },
                {
                    "ats_match_percentage": 82,
                    "matched_keywords": ["python", "fastapi", "docker"],
                    "missing_keywords": ["kubernetes"],
                },
            ]
        ),
    ):
        res = await AnalyticsService.get_ats_analytics("user_1", db)
        assert res.latest_score == 82
        assert res.average_score == 76.0
        assert "kubernetes" in res.top_missing_skills
        assert res.keyword_coverage > 0


@pytest.mark.asyncio
async def test_get_job_match_analytics():
    """
    Test 9: Verify get_job_match_analytics average match score and hiring recommendation trends.
    """
    db = MagicMock()
    with patch.object(
        AnalyticsService,
        "_safe_find_history",
        AsyncMock(
            return_value=[
                {"fit_score": 68, "role_title": "Backend Engineer", "missing_skills": ["a", "b"]},
                {"fit_score": 85, "role_title": "Senior Backend Engineer", "missing_skills": ["a"]},
            ]
        ),
    ):
        res = await AnalyticsService.get_job_match_analytics("user_1", db)
        assert res.latest_match_score == 85
        assert res.average_match_score == 76.5
        assert res.best_matching_role == "Senior Backend Engineer"
        assert "Strong Hire" in res.hiring_recommendation_trend


@pytest.mark.asyncio
async def test_get_interview_analytics():
    """
    Test 10: Verify get_interview_analytics technical/communication trend lines and success rate calculation.
    """
    db = MagicMock()
    with patch.object(
        AnalyticsService,
        "_safe_find_history",
        AsyncMock(
            return_value=[
                {
                    "overall_score": 75,
                    "technical_score": 72,
                    "communication_score": 80,
                    "confidence_score": 75,
                    "problem_solving_score": 70,
                },
                {
                    "overall_score": 82,
                    "technical_score": 80,
                    "communication_score": 85,
                    "confidence_score": 82,
                    "problem_solving_score": 78,
                },
            ]
        ),
    ):
        res = await AnalyticsService.get_interview_analytics("user_1", db)
        assert res.average_interview_score == 78.5
        assert res.interview_success_rate == 100.0  # both >= 70
        assert res.technical_score_trend == [72, 80]


@pytest.mark.asyncio
async def test_get_learning_analytics():
    """
    Test 11: Verify get_learning_analytics milestone count, velocity, and streak.
    """
    db = MagicMock()
    with patch.object(
        AnalyticsService,
        "_safe_find_history",
        AsyncMock(
            return_value=[
                {
                    "progress_percentage": 65.0,
                    "completed_items": ["m1", "m2", "m3", "m4", "m5", "m6"],
                    "estimated_completion": "4 weeks",
                }
            ]
        ),
    ):
        res = await AnalyticsService.get_learning_analytics("user_1", db)
        assert res.learning_progress == 65.0
        assert res.completed_milestones == 6
        assert res.completed_projects == 2  # 6 // 3
        assert res.learning_velocity == 3.0  # 6 / 2.0


@pytest.mark.asyncio
async def test_get_digital_twin_analytics():
    """
    Test 12: Verify get_digital_twin_analytics skill extraction and timeline events from Digital Twin memory.
    """
    context = {
        "memory": {
            "core_skills": ["Python", "FastAPI"],
            "emerging_skills": ["Docker", "AWS"],
            "missing_skills": ["Kubernetes"],
            "timeline": [
                {"event": "Profile Created"},
                "GitHub Analyzed",
            ],
        }
    }
    res = await AnalyticsService.get_digital_twin_analytics("user_1", context)
    assert "Python" in res.core_skills
    assert "Docker" in res.emerging_skills
    assert len(res.career_evolution_timeline) == 2


@pytest.mark.asyncio
async def test_get_skill_matrix():
    """
    Test 13: Verify get_skill_matrix evaluates all 11 required skills.
    """
    context = {
        "profile": {"skills": ["Python", "SQL"]},
        "github_analysis": {"top_languages": ["FastAPI"]},
        "memory": {
            "core_skills": ["Python", "Git"],
            "emerging_skills": ["Docker", "AWS"],
            "missing_skills": ["Machine Learning"],
        },
    }
    res = await AnalyticsService.get_skill_matrix("user_1", context)
    assert len(res) == len(REQUIRED_SKILLS)
    names = [s.skill_name for s in res]
    for req in REQUIRED_SKILLS:
        assert req in names
    # Verify Python is Advanced
    py = next(s for s in res if s.skill_name == "Python")
    assert py.current_level == "Advanced"
    assert py.score == 85
    # Verify Machine Learning is Beginner
    ml = next(s for s in res if s.skill_name == "Machine Learning")
    assert ml.current_level == "Beginner"


@pytest.mark.asyncio
async def test_get_timeline():
    """
    Test 14: Verify get_timeline chronological ordering and merging of milestones across all modules.
    """
    context = {
        "profile": {"target_role": "Backend Lead", "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc)},
        "resume": {"file_name": "resume.pdf", "created_at": datetime(2026, 1, 5, tzinfo=timezone.utc)},
        "github_analysis": {"username": "coder", "created_at": datetime(2026, 1, 10, tzinfo=timezone.utc)},
        "career_analysis": {"overall_readiness_score": 80, "created_at": datetime(2026, 1, 15, tzinfo=timezone.utc)},
        "ats_analysis": {"ats_match_percentage": 85, "created_at": datetime(2026, 1, 20, tzinfo=timezone.utc)},
        "interview": {"overall_score": 88, "created_at": datetime(2026, 1, 25, tzinfo=timezone.utc)},
    }
    res = await AnalyticsService.get_timeline("user_1", context)
    assert len(res) >= 7  # 6 module events + 1 Career Health Increased event
    # Ensure sorted chronologically ascending
    for i in range(len(res) - 1):
        assert res[i].timestamp <= res[i + 1].timestamp


def test_analytics_ai_service_fallback():
    """
    Test 15: Verify AnalyticsAIService deterministic rule-based fallback without calling LLM.
    """
    context = {
        "profile": {"target_role": "Senior Engineer", "skills": ["Python", "FastAPI"]},
        "memory": {"core_skills": ["Python", "FastAPI"], "missing_skills": ["Kubernetes"]},
    }
    analytics_data = {
        "overall_career_health_score": 82,
        "career_readiness_score": 80,
        "ats_score": 75,
        "job_match_score": 84,
        "interview_score": 85,
        "learning_progress": 60.0,
    }
    res = AnalyticsAIService.fallback_generate_insights("user_1", context, analytics_data)
    assert res.ai_generated is False
    assert len(res.current_strengths) >= 2
    assert len(res.weakest_areas) >= 2
    assert res.recommended_next_action is not None
    assert "82%" in res.estimated_readiness


@pytest.mark.asyncio
async def test_analytics_ai_service_with_mock_llm():
    """
    Test 16: Verify AnalyticsAIService.generate_executive_insights with mocked Gemini LLM.
    """
    mock_json = json.dumps(
        {
            "current_strengths": ["Demonstrated Python mastery", "High interview score"],
            "weakest_areas": ["Kubernetes containerization", "Cloud system design"],
            "biggest_improvement": "Consistent upward trajectory in interview communication",
            "career_risks": ["ATS keyword gap in container technologies"],
            "recommended_next_action": "Complete personalized AI mock interview session on system design",
            "estimated_readiness": "84% - Highly competitive for target role within 2 weeks",
        }
    )
    mock_provider = MagicMock()
    mock_provider.generate_text = AsyncMock(return_value=f"```json\n{mock_json}\n```")

    with patch("services.analytics_ai_service.get_llm_provider", return_value=mock_provider):
        res = await AnalyticsAIService.generate_executive_insights(
            user_id="user_1",
            context={},
            analytics_data={"overall_career_health_score": 84},
        )
        assert res.ai_generated is True
        assert "Demonstrated Python mastery" in res.current_strengths
        assert "84%" in res.estimated_readiness


@pytest.mark.asyncio
async def test_get_dashboard_summary():
    """
    Test 17: Verify get_dashboard_summary aggregates all components concurrently and returns complete summary.
    """
    db = MagicMock()
    with patch(
        "services.digital_twin_service.DigitalTwinService.get_context",
        AsyncMock(return_value={"profile": {"target_role": "Dev"}, "memory": {}}),
    ), patch.object(
        AnalyticsService, "get_career_analytics", AsyncMock(return_value=CareerAnalytics(current_score=80))
    ), patch.object(
        AnalyticsService, "get_ats_analytics", AsyncMock(return_value=ATSAnalytics(latest_score=75))
    ), patch.object(
        AnalyticsService, "get_job_match_analytics", AsyncMock(return_value=JobMatchAnalytics(latest_match_score=82))
    ), patch.object(
        AnalyticsService, "get_interview_analytics", AsyncMock(return_value=InterviewAnalytics())
    ), patch.object(
        AnalyticsService, "get_learning_analytics", AsyncMock(return_value=LearningAnalyticsSummary(learning_progress=50.0))
    ), patch.object(
        AnalyticsService, "get_digital_twin_analytics", AsyncMock(return_value=DigitalTwinAnalytics())
    ), patch.object(
        AnalyticsService, "get_skill_matrix", AsyncMock(return_value=[])
    ), patch.object(
        AnalyticsService, "get_timeline", AsyncMock(return_value=[])
    ):
        summary = await AnalyticsService.get_dashboard_summary("user_1", db)
        assert summary.user_id == "user_1"
        assert summary.career_readiness_score == 80
        assert summary.ats_score == 75
        assert summary.job_match_score == 82
        assert summary.career_health_score.overall_score > 0
        assert summary.insights is not None


@pytest.mark.asyncio
async def test_export_report_pdf_generation():
    """
    Test 18: Verify export_report generates valid PDF byte buffer starting with %PDF header.
    """
    db = MagicMock()
    with patch.object(
        AnalyticsService,
        "get_dashboard_summary",
        AsyncMock(
            return_value=DashboardSummary(
                user_id="user_test_pdf",
                career_health_score=CareerHealthScore(overall_score=85, status="Excellent"),
                career_readiness_score=80,
                ats_score=82,
                job_match_score=88,
                interview_score=85,
                learning_progress=70.0,
                digital_twin_confidence=89.5,
                career_goal_progress=94.4,
                overall_career_health_score=85,
                career_analytics=CareerAnalytics(),
                ats_analytics=ATSAnalytics(),
                job_match_analytics=JobMatchAnalytics(),
                interview_analytics=InterviewAnalytics(),
                learning_analytics=LearningAnalyticsSummary(),
                digital_twin_analytics=DigitalTwinAnalytics(),
                skill_matrix=[],
                timeline=[],
                insights=ExecutiveInsights(
                    current_strengths=["Strong readiness"],
                    weakest_areas=["ATS keywords"],
                    biggest_improvement="Upward interview",
                    career_risks=["Keyword gap"],
                    recommended_next_action="Run audit",
                    estimated_readiness="85%",
                ),
            )
        ),
    ):
        pdf_bytes = await AnalyticsService.export_report("user_1", "career", db)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 50
        assert pdf_bytes.startswith(b"%PDF")
