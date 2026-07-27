import asyncio
import inspect
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase


async def _safe_find_one(collection, query: dict) -> Optional[Dict[str, Any]]:
    try:
        res = collection.find_one(query)
        if inspect.isawaitable(res):
            return await res
        return res if isinstance(res, dict) else None
    except Exception:
        return None


async def _safe_to_list(collection, query: dict) -> Optional[Dict[str, Any]]:
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
        return None


class DigitalTwinService:
    """
    Single source of truth for user context across OMNI Digital Twin modules.
    Provides unified access to profile, resume, GitHub, career readiness, and ATS analysis reports
    without duplicating queries or business logic.
    """

    @staticmethod
    async def get_profile(user_id: str, db: AsyncIOMotorDatabase) -> Optional[Dict[str, Any]]:
        return await _safe_find_one(db.profiles, {"user_id": user_id})

    @staticmethod
    async def get_resume(user_id: str, db: AsyncIOMotorDatabase) -> Optional[Dict[str, Any]]:
        return await _safe_to_list(db.resumes, {"user_id": user_id})

    @staticmethod
    async def get_github_analysis(user_id: str, db: AsyncIOMotorDatabase) -> Optional[Dict[str, Any]]:
        res = await _safe_to_list(db.github_analysis, {"user_id": user_id})
        if res:
            return res
        # Backward compatibility fallback to github_data
        return await _safe_find_one(db.github_data, {"user_id": user_id})

    @staticmethod
    async def get_career_analysis(user_id: str, db: AsyncIOMotorDatabase) -> Optional[Dict[str, Any]]:
        return await _safe_to_list(db.career_analysis, {"user_id": user_id})

    @staticmethod
    async def get_ats_analysis(user_id: str, db: AsyncIOMotorDatabase) -> Optional[Dict[str, Any]]:
        return await _safe_to_list(db.ats_analysis, {"user_id": user_id})

    @staticmethod
    async def get_job_matching(user_id: str, db: AsyncIOMotorDatabase) -> Optional[Dict[str, Any]]:
        return await _safe_to_list(db.job_matches, {"user_id": user_id})

    @staticmethod
    async def get_memory(user_id: str, db: AsyncIOMotorDatabase) -> Optional[Dict[str, Any]]:
        return await _safe_find_one(db.digital_twin_memory, {"user_id": user_id})

    @staticmethod
    async def get_interview_sessions(user_id: str, db: AsyncIOMotorDatabase) -> Optional[Dict[str, Any]]:
        return await _safe_to_list(db.interview_sessions, {"user_id": user_id})

    @staticmethod
    async def get_learning_roadmaps(user_id: str, db: AsyncIOMotorDatabase) -> Optional[Dict[str, Any]]:
        return await _safe_to_list(db.learning_roadmaps, {"user_id": user_id})

    @classmethod
    async def get_context(cls, user_id: str, db: AsyncIOMotorDatabase) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Retrieves the complete Digital Twin user context concurrently.
        Returns:
        {
            "profile": ...,
            "resume": ...,
            "github_analysis": ...,
            "career_analysis": ...,
            "ats_analysis": ...,
            "job_matching": ...,
            "memory": ...,
            "interview": ...,
            "learning_roadmap": ...
        }
        """
        (
            profile,
            resume,
            github_analysis,
            career_analysis,
            ats_analysis,
            job_matching,
            memory,
            interview,
            learning_roadmap,
        ) = await asyncio.gather(
            cls.get_profile(user_id, db),
            cls.get_resume(user_id, db),
            cls.get_github_analysis(user_id, db),
            cls.get_career_analysis(user_id, db),
            cls.get_ats_analysis(user_id, db),
            cls.get_job_matching(user_id, db),
            cls.get_memory(user_id, db),
            cls.get_interview_sessions(user_id, db),
            cls.get_learning_roadmaps(user_id, db),
        )

        return {
            "profile": profile,
            "resume": resume,
            "github_analysis": github_analysis,
            "career_analysis": career_analysis,
            "ats_analysis": ats_analysis,
            "job_matching": job_matching,
            "memory": memory,
            "interview": interview,
            "learning_roadmap": learning_roadmap,
        }
