from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from models.career import CareerAnalyzeResponse
from services.career_ai_service import CareerAIService
from services.digital_twin_service import DigitalTwinService
from services.digital_twin_memory_service import DigitalTwinMemoryService
from utils.logger import get_logger

logger = get_logger("career.service")


class CareerService:
    @staticmethod
    async def load_user_context(
        user_id: str,
        db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Automatically retrieves latest Resume, GitHub analysis, and User Profile from MongoDB
        via DigitalTwinService. Never asks frontend to resend data.
        """
        context = await DigitalTwinService.get_context(user_id, db)
        return context.get("resume"), context.get("github_analysis"), context.get("profile")

    @classmethod
    async def generate_career_readiness_report(
        cls,
        user_id: str,
        db: AsyncIOMotorDatabase
    ) -> CareerAnalyzeResponse:
        """
        Loads user context from DB, invokes CareerAIService, persists report in career_analysis,
        and returns CareerAnalyzeResponse.
        """
        resume_doc, github_doc, profile_doc = await cls.load_user_context(user_id, db)

        analysis, analysis_method = await CareerAIService.analyze_career(
            user_id,
            resume_doc or {},
            github_doc or {},
            profile_doc or {}
        )

        now = datetime.now(timezone.utc)
        doc = {
            "user_id": user_id,
            "career_score": analysis.overall_score,
            "technical_score": analysis.breakdown.technical_score,
            "resume_score": analysis.breakdown.resume_score,
            "github_score": analysis.breakdown.github_score,
            "project_score": analysis.breakdown.project_score,
            "communication_score": analysis.breakdown.communication_score,
            "career_level": analysis.career_level,
            "strengths": analysis.strengths,
            "weaknesses": analysis.weaknesses,
            "missing_skills": analysis.missing_skills,
            "recommended_roles": analysis.recommended_roles,
            "summary": analysis.summary,
            "analysis_method": analysis_method,
            "created_at": now
        }

        res = await db.career_analysis.insert_one(doc)
        doc["id"] = str(res.inserted_id)

        try:
            await DigitalTwinMemoryService.update_memory(user_id, "career", doc, db)
        except Exception as memory_err:
            logger.warning(f"[CareerService] Memory update hook failed: {memory_err}")

        return CareerAnalyzeResponse(**doc)

    @staticmethod
    async def get_latest_career_report(
        user_id: str,
        db: AsyncIOMotorDatabase
    ) -> Optional[CareerAnalyzeResponse]:
        """
        Retrieves the most recent CareerAnalyzeResponse from db.career_analysis.
        """
        cursor = db.career_analysis.find({"user_id": user_id}).sort("created_at", -1).limit(1)
        reports = await cursor.to_list(length=1)
        if not reports:
            return None

        report_doc = reports[0]
        report_doc["id"] = str(report_doc.pop("_id", report_doc.get("id", "")))
        return CareerAnalyzeResponse(**report_doc)

    @staticmethod
    async def get_career_history(
        user_id: str,
        db: AsyncIOMotorDatabase
    ) -> List[CareerAnalyzeResponse]:
        """
        Retrieves historical career readiness reports sorted by newest first.
        """
        cursor = db.career_analysis.find({"user_id": user_id}).sort("created_at", -1)
        reports = await cursor.to_list(length=50)

        results = []
        for r in reports:
            r["id"] = str(r.pop("_id", r.get("id", "")))
            results.append(CareerAnalyzeResponse(**r))
        return results
