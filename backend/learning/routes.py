from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

from database.connection import get_db
from models.user import UserInDB
from models.learning import (
    LearningRoadmapGenerateRequest,
    MilestoneCompleteRequest,
    LearningRoadmapResponse,
    LearningRoadmapHistoryResponse,
)
from auth.routes import get_current_user
from services.learning_service import LearningRoadmapService
from utils.logger import get_logger

logger = get_logger("learning.routes")

router = APIRouter(prefix="/learning", tags=["learning"])


@router.post(
    "/generate",
    response_model=LearningRoadmapResponse,
    summary="Generate an AI Personalized Learning Roadmap",
    description="Generates an adaptive career learning plan using the candidate's complete Digital Twin context.",
)
async def generate_roadmap(
    request: LearningRoadmapGenerateRequest,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await LearningRoadmapService.generate_roadmap(current_user.id, request, db)


@router.get(
    "/latest",
    response_model=LearningRoadmapResponse,
    summary="Get user's latest learning roadmap",
    description="Retrieves the most recent active learning roadmap for the authenticated user.",
)
async def get_latest_roadmap(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    res = await LearningRoadmapService.get_latest_roadmap(current_user.id, db)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No learning roadmap found for this user.",
        )
    return res


@router.get(
    "/history",
    response_model=LearningRoadmapHistoryResponse,
    summary="Get user's learning roadmap history",
    description="Retrieves all historical learning roadmaps and progression analytics for the authenticated user.",
)
async def get_roadmap_history(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await LearningRoadmapService.get_roadmap_history(current_user.id, db)


@router.post(
    "/milestone/{id}/complete",
    response_model=LearningRoadmapResponse,
    summary="Complete a learning milestone on the latest roadmap",
    description="Marks a milestone as completed on the active roadmap, recalculates readiness, and synchronizes with Digital Twin memory.",
)
async def complete_milestone_latest(
    id: str,
    request: Optional[MilestoneCompleteRequest] = None,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    req = request or MilestoneCompleteRequest(milestone_id=id)
    return await LearningRoadmapService.complete_milestone(
        user_id=current_user.id,
        roadmap_id="latest",
        milestone_id=id,
        request=req,
        db=db,
    )


@router.post(
    "/{id}/milestone/{milestone_id}/complete",
    response_model=LearningRoadmapResponse,
    summary="Complete a learning milestone on a specific roadmap",
    description="Marks a milestone as completed on a specific roadmap ID, recalculates readiness, and updates Digital Twin memory.",
)
async def complete_milestone_by_roadmap(
    id: str,
    milestone_id: str,
    request: Optional[MilestoneCompleteRequest] = None,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    req = request or MilestoneCompleteRequest(milestone_id=milestone_id)
    return await LearningRoadmapService.complete_milestone(
        user_id=current_user.id,
        roadmap_id=id,
        milestone_id=milestone_id,
        request=req,
        db=db,
    )


@router.post(
    "/recalculate",
    response_model=LearningRoadmapResponse,
    summary="Recalculate roadmap readiness and milestone progress",
    description="Re-evaluates progress against fresh Digital Twin memory and marks milestones completed if skills are acquired.",
)
async def recalculate_roadmap(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await LearningRoadmapService.recalculate_roadmap(current_user.id, "latest", db)


@router.get(
    "/{id}",
    response_model=LearningRoadmapResponse,
    summary="Get learning roadmap by ID",
    description="Retrieves a specific learning roadmap by its ID.",
)
async def get_roadmap_by_id(
    id: str,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await LearningRoadmapService.get_roadmap_by_id(current_user.id, id, db)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a learning roadmap",
    description="Deletes a specific learning roadmap by its ID.",
)
async def delete_roadmap(
    id: str,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await LearningRoadmapService.delete_roadmap(current_user.id, id, db)
    return None
