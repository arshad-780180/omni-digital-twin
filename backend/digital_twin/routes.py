import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from database.connection import get_db
from models.user import UserInDB
from models.digital_twin_memory import (
    DigitalTwinMemoryResponse,
    DigitalTwinSummaryResponse,
    DigitalTwinTimelineEvent,
)
from services.digital_twin_memory_service import DigitalTwinMemoryService
from auth.routes import get_current_user
from utils.logger import get_logger

logger = get_logger("digital_twin.routes")

router = APIRouter(prefix="/twin", tags=["digital_twin"])


@router.get(
    "",
    response_model=DigitalTwinMemoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Complete Digital Twin Memory",
    description="Retrieves the persistent, evolving career memory document for the currently authenticated user.",
)
async def get_digital_twin_memory(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> DigitalTwinMemoryResponse:
    try:
        memory = await DigitalTwinMemoryService.load_memory(current_user.id, db)
        return memory
    except Exception as e:
        logger.error(f"[DigitalTwinRoutes] Error loading memory for user={current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load Digital Twin memory.",
        )


@router.get(
    "/summary",
    response_model=DigitalTwinSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Executive Digital Twin Career Summary",
    description="Returns an AI-generated (or rule-based fallback) executive career summary of the user's Digital Twin memory.",
)
async def get_digital_twin_summary(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> DigitalTwinSummaryResponse:
    try:
        summary = await DigitalTwinMemoryService.get_summary(current_user.id, db)
        return summary
    except Exception as e:
        logger.error(f"[DigitalTwinRoutes] Error generating summary for user={current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Digital Twin summary.",
        )


@router.get(
    "/timeline",
    response_model=List[DigitalTwinTimelineEvent],
    status_code=status.HTTP_200_OK,
    summary="Get Memory Evolution Timeline",
    description="Returns the chronological timeline of milestone events and module evaluations in the user's Digital Twin.",
)
async def get_digital_twin_timeline(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[DigitalTwinTimelineEvent]:
    try:
        memory = await DigitalTwinMemoryService.load_memory(current_user.id, db)
        return memory.timeline
    except Exception as e:
        logger.error(f"[DigitalTwinRoutes] Error loading timeline for user={current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load Digital Twin timeline.",
        )


@router.post(
    "/rebuild",
    response_model=DigitalTwinMemoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Rebuild Digital Twin Memory from Historical Analyses",
    description="Reconstructs persistent memory from scratch by aggregating all historical reports across OMNI collections.",
)
async def rebuild_digital_twin_memory(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> DigitalTwinMemoryResponse:
    try:
        memory = await DigitalTwinMemoryService.rebuild_memory_from_history(current_user.id, db)
        return memory
    except Exception as e:
        logger.error(f"[DigitalTwinRoutes] Error rebuilding memory for user={current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rebuild Digital Twin memory.",
        )
