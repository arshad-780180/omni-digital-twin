import logging
import inspect
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from bson.errors import InvalidId

from models.job_match import JobMatchAnalyzeRequest, JobMatchAnalysisResponse
from services.job_matching_ai_service import JobMatchingAIService
from services.digital_twin_service import DigitalTwinService
from services.digital_twin_memory_service import DigitalTwinMemoryService

logger = logging.getLogger("omni.services.job_match")


async def _safe_find_one_latest(collection, query: dict) -> Optional[Dict[str, Any]]:
    try:
        cursor = collection.find(query).sort("created_at", -1).limit(1)
        res = cursor.to_list(length=1)
        if inspect.isawaitable(res):
            items = await res
        else:
            items = res
        if items and isinstance(items, list) and len(items) > 0 and isinstance(items[0], dict):
            return items[0]
        return None
    except Exception:
        try:
            res = collection.find_one(query)
            if inspect.isawaitable(res):
                return await res
            return res
        except Exception:
            return None


async def _safe_find_list(collection, query: dict, limit: int = 10) -> List[Dict[str, Any]]:
    try:
        cursor = collection.find(query).sort("created_at", -1).limit(limit)
        res = cursor.to_list(length=limit)
        if inspect.isawaitable(res):
            items = await res
        else:
            items = res
        if items and isinstance(items, list):
            return items
        return []
    except Exception:
        return []


class JobMatchingService:
    """
    Business logic layer for AI Job Matching Engine.
    Strictly uses DigitalTwinService for candidate context and delegates no logic to routes.
    """

    @classmethod
    async def analyze_and_save_job_match(
        cls,
        user_id: str,
        request: JobMatchAnalyzeRequest,
        db: AsyncIOMotorDatabase,
    ) -> JobMatchAnalysisResponse:
        """
        Retrieves user Digital Twin context, runs AI/fallback job match analysis,
        persists structured document to db.job_matches, and returns Pydantic schema.
        """
        logger.info(f"[JobMatchingService] Analyzing job match for user={user_id}, title='{request.job_title}'")
        digital_twin_context = await DigitalTwinService.get_context(user_id, db)

        analysis, method = await JobMatchingAIService.analyze_job_match(
            user_id, digital_twin_context, request
        )

        now = datetime.now(timezone.utc)
        doc = analysis.model_dump() if hasattr(analysis, "model_dump") else analysis.dict()

        # Enforce timestamp standards and ownership
        doc["user_id"] = user_id
        doc["created_at"] = now
        doc["updated_at"] = now
        doc["analysis_method"] = method
        doc.pop("id", None)  # Remove None ID before insert

        res = await db.job_matches.insert_one(doc)
        if inspect.isawaitable(res):
            res = await res

        if hasattr(res, "inserted_id") and res.inserted_id:
            analysis.id = str(res.inserted_id)

        logger.info(
            f"[JobMatchingService] Saved job match report id={analysis.id} (method={method}, score={analysis.overall_job_match_score})"
        )

        try:
            await DigitalTwinMemoryService.update_memory(user_id, "job_matching", doc, db)
        except Exception as memory_err:
            logger.warning(f"[JobMatchingService] Memory update hook failed: {memory_err}")

        return analysis

    @classmethod
    async def get_latest_job_match(
        cls,
        user_id: str,
        db: AsyncIOMotorDatabase,
    ) -> Optional[JobMatchAnalysisResponse]:
        """
        Retrieves the most recent job match analysis for a user.
        """
        doc = await _safe_find_one_latest(db.job_matches, {"user_id": user_id})
        if not doc:
            return None

        if "_id" in doc:
            doc["id"] = str(doc["_id"])
        return JobMatchAnalysisResponse.model_validate(doc)

    @classmethod
    async def get_job_match_history(
        cls,
        user_id: str,
        db: AsyncIOMotorDatabase,
        limit: int = 10,
    ) -> List[JobMatchAnalysisResponse]:
        """
        Retrieves a user's historical job match evaluations ordered by created_at DESC.
        """
        docs = await _safe_find_list(db.job_matches, {"user_id": user_id}, limit=limit)
        results: List[JobMatchAnalysisResponse] = []
        for d in docs:
            if "_id" in d:
                d["id"] = str(d["_id"])
            results.append(JobMatchAnalysisResponse.model_validate(d))
        return results

    @classmethod
    async def delete_job_match(
        cls,
        user_id: str,
        match_id: str,
        db: AsyncIOMotorDatabase,
    ) -> bool:
        """
        Deletes a specific job match report by match_id and user_id.
        """
        query_id: Any = match_id
        try:
            query_id = ObjectId(match_id)
        except InvalidId:
            query_id = match_id

        res = await db.job_matches.delete_one({"_id": query_id, "user_id": user_id})
        if inspect.isawaitable(res):
            res = await res

        deleted = getattr(res, "deleted_count", 0) > 0
        if not deleted and isinstance(query_id, ObjectId):
            # Try string match_id fallback if ObjectId deletion failed
            res_str = await db.job_matches.delete_one({"_id": str(match_id), "user_id": user_id})
            if inspect.isawaitable(res_str):
                res_str = await res_str
            deleted = getattr(res_str, "deleted_count", 0) > 0

        return deleted
