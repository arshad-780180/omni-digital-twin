from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from models.career import CareerAnalyzeResponse
from services.career_ai_service import CareerAIService


class CareerService:
    @staticmethod
    async def load_user_context(
        user_id: str,
        db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Automatically retrieves latest Resume, GitHub analysis, and User Profile from MongoDB.
        Never asks frontend to resend data.
        """
        # 1. Latest Resume from Phase 1
        cursor_res = db.resumes.find({"user_id": user_id}).sort("created_at", -1).limit(1)
        resumes = await cursor_res.to_list(length=1)
        resume_doc = resumes[0] if resumes else None

        # 2. Latest GitHub Analysis from Phase 2 (fallback to db.github_data if needed)
        cursor_gh = db.github_analysis.find({"user_id": user_id}).sort("created_at", -1).limit(1)
        gh_list = await cursor_gh.to_list(length=1)
        github_doc = gh_list[0] if gh_list else None
        if not github_doc:
            github_doc = await db.github_data.find_one({"user_id": user_id})

        # 3. Latest Profile from db.profiles
        profile_doc = await db.profiles.find_one({"user_id": user_id})

        return resume_doc, github_doc, profile_doc

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

        now = datetime.utcnow()
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
