from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from bson.errors import InvalidId

from models.ats import ATSAnalyzeRequest, ATSAnalysisResponse
from services.ats_ai_service import ATSAIService
from services.digital_twin_service import DigitalTwinService
from services.digital_twin_memory_service import DigitalTwinMemoryService
from utils.logger import get_logger

logger = get_logger("ats.service")


class ATSService:
    @staticmethod
    async def load_resume_and_context(
        user_id: str,
        db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Retrieves the latest parsed resume from db.resumes and user profile from db.profiles
        via DigitalTwinService. Never asks frontend to resend data.
        """
        context = await DigitalTwinService.get_context(user_id, db)
        return context.get("resume"), context.get("profile")

    @classmethod
    async def analyze_resume_against_job(
        cls,
        user_id: str,
        request: ATSAnalyzeRequest,
        db: AsyncIOMotorDatabase
    ) -> ATSAnalysisResponse:
        """
        Loads user context, executes AI/fallback ATS optimization, saves to db.ats_analysis,
        and returns validated ATSAnalysisResponse.
        """
        resume_doc, profile_doc = await cls.load_resume_and_context(user_id, db)

        (
            ats_score,
            required_keywords,
            matched_keywords,
            missing_keywords,
            feedback,
            suggestions,
            _method
        ) = await ATSAIService.optimize_resume(
            resume_doc,
            profile_doc,
            request.job_title,
            request.company,
            request.job_description
        )

        now = datetime.now(timezone.utc)
        resume_id_str = None
        if resume_doc:
            rid = resume_doc.get("_id") or resume_doc.get("id")
            if rid:
                resume_id_str = str(rid)

        doc = {
            "user_id": user_id,
            "resume_id": resume_id_str,
            "job_title": request.job_title,
            "company": request.company,
            "job_description": request.job_description,
            "required_keywords": required_keywords,
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "ats_score": ats_score,
            "resume_feedback": feedback.model_dump() if hasattr(feedback, "model_dump") else feedback.dict(),
            "ai_suggestions": suggestions.model_dump() if hasattr(suggestions, "model_dump") else suggestions.dict(),
            "created_at": now
        }

        result = await db.ats_analysis.insert_one(doc)
        doc["id"] = str(result.inserted_id)

        try:
            await DigitalTwinMemoryService.update_memory(user_id, "ats", doc, db)
        except Exception as memory_err:
            logger.warning(f"[ATSService] Memory update hook failed: {memory_err}")

        return ATSAnalysisResponse(**doc)

    @staticmethod
    async def get_latest_analysis(
        user_id: str,
        db: AsyncIOMotorDatabase
    ) -> Optional[ATSAnalysisResponse]:
        """
        Returns the most recent ATS analysis for the user.
        """
        cursor = db.ats_analysis.find({"user_id": user_id}).sort("created_at", -1).limit(1)
        reports = await cursor.to_list(length=1)
        if not reports:
            return None

        report_doc = reports[0]
        report_doc["id"] = str(report_doc.pop("_id", report_doc.get("id", "")))
        return ATSAnalysisResponse(**report_doc)

    @staticmethod
    async def get_history(
        user_id: str,
        db: AsyncIOMotorDatabase
    ) -> List[ATSAnalysisResponse]:
        """
        Returns previous ATS analyses sorted by newest first.
        """
        cursor = db.ats_analysis.find({"user_id": user_id}).sort("created_at", -1)
        reports = await cursor.to_list(length=50)

        results = []
        for r in reports:
            r["id"] = str(r.pop("_id", r.get("id", "")))
            results.append(ATSAnalysisResponse(**r))
        return results

    @staticmethod
    async def delete_analysis(
        user_id: str,
        analysis_id: str,
        db: AsyncIOMotorDatabase
    ) -> bool:
        """
        Deletes a specific ATS analysis document owned by user_id.
        """
        query_conditions = [{"user_id": user_id}]
        try:
            query = {"$and": [{"_id": ObjectId(analysis_id)}, {"user_id": user_id}]}
            res = await db.ats_analysis.delete_one(query)
            if res.deleted_count > 0:
                return True
        except (InvalidId, Exception):
            pass

        # Also try matching by string id field if stored as string
        res = await db.ats_analysis.delete_one({"id": analysis_id, "user_id": user_id})
        return res.deleted_count > 0
