from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional

from database.connection import get_db
from models.user import UserInDB
from models.job_match import (
    JobMatchAnalyzeRequest,
    JobMatchAnalysisResponse,
)
from auth.routes import get_current_user
from services.job_matching_service import JobMatchingService
from utils.logger import get_logger

logger = get_logger("job_matching.routes")
router = APIRouter(prefix="/jobs", tags=["job-matching"])


@router.post(
    "/analyze",
    response_model=JobMatchAnalysisResponse,
    summary="Analyze job match against Digital Twin",
    description="Evaluates candidate's Digital Twin against target job description, generating match scores, role recommendations, salary estimates, and learning plans.",
    status_code=status.HTTP_200_OK,
)
async def analyze_job_match(
    request: JobMatchAnalyzeRequest,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        report = await JobMatchingService.analyze_and_save_job_match(
            user_id=current_user.id,
            request=request,
            db=db,
        )
        return report
    except Exception as e:
        logger.error(f"[JobMatchingRoutes] Error analyzing job match: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze job match: {str(e)}",
        )


@router.get(
    "/latest",
    response_model=Optional[JobMatchAnalysisResponse],
    summary="Get latest job match evaluation",
    description="Returns the most recent job match analysis report for the authenticated user.",
    status_code=status.HTTP_200_OK,
)
async def get_latest_job_match(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        report = await JobMatchingService.get_latest_job_match(
            user_id=current_user.id,
            db=db,
        )
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No job match evaluations found for this user.",
            )
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[JobMatchingRoutes] Error fetching latest job match: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve latest job match evaluation: {str(e)}",
        )


@router.get(
    "/history",
    response_model=List[JobMatchAnalysisResponse],
    summary="Get job match analysis history",
    description="Returns a historical list of job match evaluations for the authenticated user, ordered by creation date.",
    status_code=status.HTTP_200_OK,
)
async def get_job_match_history(
    limit: int = Query(default=10, ge=1, le=50, description="Max number of historical records to return"),
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        history = await JobMatchingService.get_job_match_history(
            user_id=current_user.id,
            db=db,
            limit=limit,
        )
        return history
    except Exception as e:
        logger.error(f"[JobMatchingRoutes] Error fetching job match history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job match history: {str(e)}",
        )


@router.delete(
    "/{match_id}",
    summary="Delete a job match report",
    description="Deletes a specific job match report belonging to the authenticated user.",
    status_code=status.HTTP_200_OK,
)
async def delete_job_match(
    match_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        deleted = await JobMatchingService.delete_job_match(
            user_id=current_user.id,
            match_id=match_id,
            db=db,
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job match report not found or does not belong to the user.",
            )
        return {"success": True, "message": f"Job match report {match_id} deleted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[JobMatchingRoutes] Error deleting job match {match_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job match report: {str(e)}",
        )
