from fastapi import APIRouter, Depends, Query, Response
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

from database.connection import get_db
from models.user import UserInDB
from models.analytics import (
    DashboardSummary,
    CareerAnalytics,
    ATSAnalytics,
    JobMatchAnalytics,
    InterviewAnalytics,
    LearningAnalyticsSummary,
    SkillAnalytics,
    TimelineEvent,
)
from auth.routes import get_current_user
from services.analytics_service import AnalyticsService
from utils.logger import get_logger

logger = get_logger("analytics.routes")

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/dashboard",
    response_model=DashboardSummary,
    summary="Get unified executive analytics dashboard",
    description="Aggregates insights from every OMNI module and computes the deterministic Career Health Score.",
)
async def get_dashboard_summary(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await AnalyticsService.get_dashboard_summary(current_user.id, db)


@router.get(
    "/career",
    response_model=CareerAnalytics,
    summary="Get career readiness analytics",
    description="Retrieves career readiness score trends and monthly improvement.",
)
async def get_career_analytics(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await AnalyticsService.get_career_analytics(current_user.id, db)


@router.get(
    "/ats",
    response_model=ATSAnalytics,
    summary="Get ATS resume optimization analytics",
    description="Retrieves ATS match trends, keyword coverage, and top missing skills.",
)
async def get_ats_analytics(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await AnalyticsService.get_ats_analytics(current_user.id, db)


@router.get(
    "/job-match",
    response_model=JobMatchAnalytics,
    summary="Get job match analytics",
    description="Retrieves opportunity match trends, alternative roles, and skill gap evolution.",
)
async def get_job_match_analytics(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await AnalyticsService.get_job_match_analytics(current_user.id, db)


@router.get(
    "/interviews",
    response_model=InterviewAnalytics,
    summary="Get mock interview analytics",
    description="Retrieves multi-dimension interview performance trends and success rates.",
)
async def get_interview_analytics(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await AnalyticsService.get_interview_analytics(current_user.id, db)


@router.get(
    "/learning",
    response_model=LearningAnalyticsSummary,
    summary="Get learning roadmap analytics",
    description="Retrieves learning progress, velocity, milestone completion, and weekly streak.",
)
async def get_learning_analytics(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await AnalyticsService.get_learning_analytics(current_user.id, db)


@router.get(
    "/skills",
    response_model=List[SkillAnalytics],
    summary="Get 11-skill evaluation matrix",
    description="Retrieves visual matrix for Python, FastAPI, SQL, Docker, AWS, Git, React, MongoDB, Machine Learning, Data Structures, and Algorithms.",
)
async def get_skill_matrix(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    from services.digital_twin_service import DigitalTwinService

    context = await DigitalTwinService.get_context(current_user.id, db)
    return await AnalyticsService.get_skill_matrix(current_user.id, context)


@router.get(
    "/timeline",
    response_model=List[TimelineEvent],
    summary="Get chronological career evolution timeline",
    description="Retrieves chronological milestones across profile, resume, github, career, ats, interview, learning, job match, and digital twin memory.",
)
async def get_timeline(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    from services.digital_twin_service import DigitalTwinService

    context = await DigitalTwinService.get_context(current_user.id, db)
    return await AnalyticsService.get_timeline(current_user.id, context)


@router.get(
    "/export",
    summary="Export downloadable PDF report",
    description="Generates a downloadable PDF report (career, summary, progress, or timeline).",
)
async def export_report(
    report_type: str = Query(
        "career",
        description="Type of report to export: career, summary, progress, or timeline",
    ),
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    pdf_bytes = await AnalyticsService.export_report(
        current_user.id, report_type, db
    )
    headers = {
        "Content-Disposition": f"attachment; filename=omni_{report_type}_report.pdf"
    }
    return Response(
        content=pdf_bytes, media_type="application/pdf", headers=headers
    )
