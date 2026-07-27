from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

from database.connection import get_db
from models.user import UserInDB
from models.ats import ATSAnalyzeRequest, ATSAnalysisResponse
from auth.routes import get_current_user
from services.ats_service import ATSService

router = APIRouter(prefix="/ats", tags=["ats"])


@router.post(
    "/analyze",
    response_model=ATSAnalysisResponse,
    summary="Optimize resume against job description",
    description="Evaluates user's latest resume against a target job description, identifying keyword matches, missing skills, and optimization suggestions."
)
async def analyze_ats_resume(
    request: ATSAnalyzeRequest,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    if not request.job_description or not request.job_title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job title and job description are required."
        )

    try:
        report = await ATSService.analyze_resume_against_job(
            user_id=current_user.id,
            request=request,
            db=db
        )
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate ATS analysis: {str(e)}"
        )


@router.get(
    "/latest",
    response_model=ATSAnalysisResponse,
    summary="Get latest ATS optimization report",
    description="Returns the most recent ATS resume optimization report for the user."
)
async def get_latest_ats_analysis(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    report = await ATSService.get_latest_analysis(current_user.id, db)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No ATS resume optimization report found."
        )
    return report


@router.get(
    "/history",
    response_model=List[ATSAnalysisResponse],
    summary="Get ATS optimization history",
    description="Returns previous ATS analyses sorted by newest first."
)
async def get_ats_history(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    reports = await ATSService.get_history(current_user.id, db)
    return reports


@router.delete(
    "/{analysis_id}",
    summary="Delete ATS analysis report",
    description="Deletes a specific ATS analysis report by ID."
)
async def delete_ats_analysis(
    analysis_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    success = await ATSService.delete_analysis(current_user.id, analysis_id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ATS analysis not found or already deleted."
        )
    return {"status": "success", "message": "ATS analysis deleted."}
