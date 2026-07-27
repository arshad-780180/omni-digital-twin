from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

from database.connection import get_db
from models.user import UserInDB
from models.interview import (
    InterviewStartRequest,
    InterviewGenerateRequest,
    InterviewAnswerSubmitRequest,
    InterviewEvaluateRequest,
    InterviewSessionResponse,
    InterviewHistoryResponse,
)
from auth.routes import get_current_user
from services.interview_service import InterviewService
from utils.logger import get_logger

logger = get_logger("interview")

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post(
    "/start",
    response_model=InterviewSessionResponse,
    summary="Start a personalized AI mock interview session",
    description="Initializes a new mock interview session with progressive questions personalized from the user's Digital Twin.",
)
async def start_interview(
    request: InterviewStartRequest,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await InterviewService.start_interview(current_user.id, request, db)


@router.post(
    "/generate",
    response_model=InterviewSessionResponse,
    summary="Legacy AI interview generation endpoint",
    description="Backward-compatible wrapper around /api/interview/start.",
)
async def generate_interview(
    request: InterviewGenerateRequest,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    start_req = InterviewStartRequest(
        role=request.target_role,
        difficulty="Medium",
        interview_type="Technical",
        question_count=3,
    )
    return await InterviewService.start_interview(current_user.id, start_req, db)


@router.get(
    "/latest",
    response_model=InterviewSessionResponse,
    summary="Get latest mock interview session",
    description="Retrieves the user's most recent mock interview session.",
)
async def get_latest_session(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    res = await InterviewService.get_latest_session(current_user.id, db)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No mock interview sessions found.",
        )
    return res


@router.get(
    "/history",
    response_model=InterviewHistoryResponse,
    summary="Get mock interview session history and trend analytics",
    description="Returns all historical sessions along with average score, score trajectories, and weakest topics.",
)
async def get_session_history(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await InterviewService.get_session_history(current_user.id, db)


@router.get(
    "/{session_id}",
    response_model=InterviewSessionResponse,
    summary="Get mock interview session state",
    description="Retrieves a specific interview session by ID.",
)
async def get_session(
    session_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await InterviewService.get_session(current_user.id, session_id, db)


@router.post(
    "/{session_id}/answer",
    response_model=InterviewSessionResponse,
    summary="Submit an answer for evaluation",
    description="Submits an answer for a question, evaluates it, and returns updated scores and adaptive follow-up feedback.",
)
async def submit_answer(
    session_id: str,
    request: InterviewAnswerSubmitRequest,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await InterviewService.submit_answer(current_user.id, session_id, request, db)


@router.post(
    "/{session_id}/finish",
    response_model=InterviewSessionResponse,
    summary="Finish interview session and synthesize report",
    description="Marks session as COMPLETED, generates executive interview report, and automatically updates Digital Twin Memory.",
)
async def finish_interview(
    session_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await InterviewService.finish_interview(current_user.id, session_id, db)


@router.post(
    "/evaluate/{session_id}",
    response_model=InterviewSessionResponse,
    summary="Legacy evaluate interview endpoint",
    description="Backward-compatible wrapper that submits all answers and finishes the interview.",
)
async def evaluate_interview_legacy_path(
    session_id: str,
    request: InterviewEvaluateRequest,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await InterviewService.evaluate_interview_legacy(
        current_user.id, session_id, request.answers, db
    )


@router.post(
    "/evaluate",
    response_model=InterviewSessionResponse,
    summary="Legacy evaluate interview endpoint (body session_id)",
    description="Backward-compatible wrapper that submits all answers and finishes the interview.",
)
async def evaluate_interview_legacy_body(
    request: InterviewEvaluateRequest,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if not request.session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required.",
        )
    return await InterviewService.evaluate_interview_legacy(
        current_user.id, request.session_id, request.answers, db
    )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete mock interview session",
    description="Deletes an interview session by ID.",
)
async def delete_session(
    session_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await InterviewService.delete_session(current_user.id, session_id, db)
    return None
