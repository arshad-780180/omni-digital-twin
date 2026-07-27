import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.learning import (
    LearningRoadmap,
    LearningRoadmapResponse,
    LearningRoadmapHistoryResponse,
    LearningHistoryItem,
    LearningRoadmapGenerateRequest,
    MilestoneCompleteRequest,
    ProgressSummary,
    LearningAnalytics,
)
from services.digital_twin_service import DigitalTwinService
from services.digital_twin_memory_service import DigitalTwinMemoryService
from services.learning_ai_service import LearningRoadmapAIService

logger = logging.getLogger("omni.learning.service")


class LearningRoadmapService:
    """
    Core business service for Phase 8 AI Personalized Learning Roadmap Engine.
    Manages roadmap generation, interactive milestone completions, readiness recalculation,
    and automatic synchronization with candidate's persistent Digital Twin Memory.
    """

    @classmethod
    async def generate_roadmap(
        cls,
        user_id: str,
        request: LearningRoadmapGenerateRequest,
        db: AsyncIOMotorDatabase,
    ) -> LearningRoadmapResponse:
        """
        Concurrently loads candidate Digital Twin context, generates an AI learning roadmap,
        persists it to MongoDB, and initializes Digital Twin memory tracking.
        """
        context = await DigitalTwinService.get_context(user_id, db)
        roadmap: LearningRoadmap = await LearningRoadmapAIService.generate_roadmap(user_id, request, context)

        now = datetime.now(timezone.utc)
        total_milestones = len(roadmap.milestones)
        total_phases = len(roadmap.learning_phases)

        doc = {
            "user_id": user_id,
            "target_role": roadmap.target_role,
            "current_readiness": roadmap.current_readiness,
            "target_readiness": roadmap.target_readiness,
            "roadmap": roadmap.model_dump(),
            "milestones": [m.model_dump() for m in roadmap.milestones],
            "completed_items": [],
            "progress_percentage": 0.0,
            "estimated_completion": roadmap.estimated_completion,
            "analytics": LearningAnalytics(
                learning_velocity=0.0,
                skills_learned_count=0,
                projects_completed_count=0,
                readiness_growth=max(0, roadmap.target_readiness - roadmap.current_readiness),
                estimated_completion_weeks=request.target_timeframe_weeks,
            ).model_dump(),
            "progress_summary": ProgressSummary(
                completed_milestones=0,
                total_milestones=total_milestones,
                progress_percentage=0.0,
                completed_phases=0,
                total_phases=total_phases,
                current_phase=1,
                skills_acquired_count=0,
            ).model_dump(),
            "created_at": now,
            "updated_at": now,
        }

        res = await db.learning_roadmaps.insert_one(doc)
        doc["_id"] = res.inserted_id

        # Automatically record initial roadmap event in Digital Twin Memory
        try:
            await DigitalTwinMemoryService.update_memory(
                user_id=user_id,
                source_module="learning",
                payload={
                    "new_skills": [],
                    "completed_projects": [],
                    "learning_velocity": 0.0,
                    "career_progress": roadmap.current_readiness,
                },
                db=db,
            )
        except Exception as e:
            logger.warning(f"[LearningService] Notice while initializing memory: {str(e)}")

        return cls._to_response(doc)

    @classmethod
    async def get_latest_roadmap(
        cls,
        user_id: str,
        db: AsyncIOMotorDatabase,
    ) -> Optional[LearningRoadmapResponse]:
        """
        Retrieves the user's latest active learning roadmap.
        """
        doc = await db.learning_roadmaps.find_one({"user_id": user_id}, sort=[("created_at", -1)])
        if not doc:
            return None
        return cls._to_response(doc)

    @classmethod
    async def get_roadmap_by_id(
        cls,
        user_id: str,
        roadmap_id: str,
        db: AsyncIOMotorDatabase,
    ) -> LearningRoadmapResponse:
        """
        Retrieves a specific learning roadmap by ID and user_id.
        """
        query: Dict[str, Any] = {"user_id": user_id}
        if ObjectId.is_valid(roadmap_id):
            query["_id"] = ObjectId(roadmap_id)
        else:
            query["id"] = roadmap_id

        doc = await db.learning_roadmaps.find_one(query)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning roadmap not found.",
            )
        return cls._to_response(doc)

    @classmethod
    async def get_roadmap_history(
        cls,
        user_id: str,
        db: AsyncIOMotorDatabase,
    ) -> LearningRoadmapHistoryResponse:
        """
        Retrieves all historical learning roadmaps for a user with progress analytics.
        """
        cursor = db.learning_roadmaps.find({"user_id": user_id}).sort("created_at", -1)
        docs = await cursor.to_list(length=50)

        history_items: List[LearningHistoryItem] = []
        latest_res: Optional[LearningRoadmapResponse] = None

        for idx, doc in enumerate(docs):
            doc_id = str(doc.get("_id") or doc.get("id"))
            item = LearningHistoryItem(
                id=doc_id,
                user_id=user_id,
                target_role=doc.get("target_role", "Software Engineer"),
                current_readiness=int(doc.get("current_readiness", 45)),
                target_readiness=int(doc.get("target_readiness", 95)),
                progress_percentage=float(doc.get("progress_percentage", 0.0)),
                created_at=doc.get("created_at", datetime.now(timezone.utc)),
                updated_at=doc.get("updated_at"),
            )
            history_items.append(item)
            if idx == 0:
                latest_res = cls._to_response(doc)

        return LearningRoadmapHistoryResponse(
            user_id=user_id,
            total_roadmaps=len(docs),
            latest_roadmap=latest_res,
            history=history_items,
        )

    @classmethod
    async def complete_milestone(
        cls,
        user_id: str,
        roadmap_id: Optional[str],
        milestone_id: str,
        request: MilestoneCompleteRequest,
        db: AsyncIOMotorDatabase,
    ) -> LearningRoadmapResponse:
        """
        Marks an interactive milestone as completed, recalculates progress percentage
        and career readiness score, unlocks subsequent skills, and synchronizes with Digital Twin Memory.
        """
        if not roadmap_id or roadmap_id.lower() == "latest":
            latest = await cls.get_latest_roadmap(user_id, db)
            if not latest:
                raise HTTPException(status_code=404, detail="No active learning roadmap found.")
            target_id = latest.id
        else:
            target_id = roadmap_id

        query: Dict[str, Any] = {"user_id": user_id}
        if ObjectId.is_valid(target_id):
            query["_id"] = ObjectId(target_id)
        else:
            query["id"] = target_id

        doc = await db.learning_roadmaps.find_one(query)
        if not doc:
            raise HTTPException(status_code=404, detail="Learning roadmap not found.")

        now = datetime.now(timezone.utc)
        milestones = doc.get("milestones", [])
        roadmap_data = doc.get("roadmap", {})
        phases = roadmap_data.get("learning_phases", [])

        skills_unlocked: List[str] = list(request.completed_items)
        completed_projects: List[str] = []
        milestone_found = False

        # 1. Update in flat milestones list
        for m in milestones:
            if isinstance(m, dict):
                m_id = str(m.get("milestone_id") or "")
                if m_id == milestone_id or m.get("title") == milestone_id:
                    m["completed"] = True
                    m["completed_at"] = now
                    milestone_found = True
                    skills = m.get("skills_unlocked", [])
                    if isinstance(skills, list):
                        for s in skills:
                            if isinstance(s, str) and s not in skills_unlocked:
                                skills_unlocked.append(s)
                    if m.get("category") == "project":
                        completed_projects.append(str(m.get("title", "Project Milestone")))

        # 2. Update in nested learning_phases milestones
        for phase in phases:
            if isinstance(phase, dict):
                p_milestones = phase.get("milestones", [])
                if isinstance(p_milestones, list):
                    for m in p_milestones:
                        if isinstance(m, dict):
                            m_id = str(m.get("milestone_id") or "")
                            if m_id == milestone_id or m.get("title") == milestone_id:
                                m["completed"] = True
                                m["completed_at"] = now
                                milestone_found = True
                                skills = m.get("skills_unlocked", [])
                                if isinstance(skills, list):
                                    for s in skills:
                                        if isinstance(s, str) and s not in skills_unlocked:
                                            skills_unlocked.append(s)

        if not milestone_found:
            raise HTTPException(status_code=404, detail=f"Milestone {milestone_id} not found in roadmap.")

        # Update completed_items list
        completed_items = doc.get("completed_items", [])
        if milestone_id not in completed_items:
            completed_items.append(milestone_id)
        for s in skills_unlocked:
            if s not in completed_items:
                completed_items.append(s)
        doc["completed_items"] = completed_items

        # Recompute progress and current_readiness
        total_milestones = max(1, len(milestones))
        completed_count = sum(1 for m in milestones if isinstance(m, dict) and m.get("completed"))
        progress_percentage = round((completed_count / total_milestones) * 100.0, 1)

        initial_readiness = int(doc.get("current_readiness", 45))
        target_readiness = int(doc.get("target_readiness", 95))
        new_readiness = min(target_readiness, initial_readiness + int((target_readiness - initial_readiness) * (progress_percentage / 100.0)))

        doc["progress_percentage"] = progress_percentage
        doc["current_readiness"] = new_readiness
        doc["updated_at"] = now

        # Update ProgressSummary and Analytics
        doc["progress_summary"] = ProgressSummary(
            completed_milestones=completed_count,
            total_milestones=total_milestones,
            progress_percentage=progress_percentage,
            completed_phases=sum(1 for p in phases if isinstance(p, dict) and all(m.get("completed") for m in p.get("milestones", []) if isinstance(m, dict))),
            total_phases=len(phases),
            current_phase=min(len(phases), 1 + sum(1 for p in phases if isinstance(p, dict) and all(m.get("completed") for m in p.get("milestones", []) if isinstance(m, dict)))),
            skills_acquired_count=len(skills_unlocked),
        ).model_dump()

        doc["analytics"] = LearningAnalytics(
            learning_velocity=round(completed_count * 1.5, 1),
            skills_learned_count=len(skills_unlocked),
            projects_completed_count=len(completed_projects),
            readiness_growth=max(0, new_readiness - 45),
            estimated_completion_weeks=max(1, 8 - int(progress_percentage / 12.5)),
        ).model_dump()

        await db.learning_roadmaps.replace_one(query, doc)

        # 3. Synchronize with Digital Twin Memory automatically
        try:
            await DigitalTwinMemoryService.update_memory(
                user_id=user_id,
                source_module="learning",
                payload={
                    "new_skills": skills_unlocked,
                    "completed_projects": completed_projects,
                    "learning_velocity": progress_percentage,
                    "career_progress": new_readiness,
                },
                db=db,
            )
            logger.info(f"[LearningService] Automatically synchronized milestone '{milestone_id}' completion with Digital Twin Memory.")
        except Exception as e:
            logger.warning(f"[LearningService] Notice while updating Digital Twin Memory: {str(e)}")

        return cls._to_response(doc)

    @classmethod
    async def recalculate_roadmap(
        cls,
        user_id: str,
        roadmap_id: Optional[str],
        db: AsyncIOMotorDatabase,
    ) -> LearningRoadmapResponse:
        """
        Recalculates learning progress against fresh Digital Twin memory and marks milestones
        completed if candidate has already acquired the required skills.
        """
        latest = await cls.get_latest_roadmap(user_id, db)
        if not latest:
            raise HTTPException(status_code=404, detail="No active learning roadmap found.")

        query: Dict[str, Any] = {"user_id": user_id}
        if ObjectId.is_valid(latest.id):
            query["_id"] = ObjectId(latest.id)
        else:
            query["id"] = latest.id

        doc = await db.learning_roadmaps.find_one(query)
        if not doc:
            raise HTTPException(status_code=404, detail="Learning roadmap not found.")

        # Load fresh context to compare against core_skills
        context = await DigitalTwinService.get_context(user_id, db)
        mem = context.get("memory") or {}
        core_skills_set = {s.lower() for s in mem.get("core_skills", []) if isinstance(s, str)}

        now = datetime.now(timezone.utc)
        milestones = doc.get("milestones", [])
        for m in milestones:
            if isinstance(m, dict) and not m.get("completed"):
                unlocked = m.get("skills_unlocked", [])
                if unlocked and all(isinstance(s, str) and s.lower() in core_skills_set for s in unlocked):
                    m["completed"] = True
                    m["completed_at"] = now

        # Recalculate progress
        total_milestones = max(1, len(milestones))
        completed_count = sum(1 for m in milestones if isinstance(m, dict) and m.get("completed"))
        progress_percentage = round((completed_count / total_milestones) * 100.0, 1)

        initial_readiness = int(doc.get("current_readiness", 45))
        target_readiness = int(doc.get("target_readiness", 95))
        new_readiness = min(target_readiness, initial_readiness + int((target_readiness - initial_readiness) * (progress_percentage / 100.0)))

        doc["progress_percentage"] = progress_percentage
        doc["current_readiness"] = new_readiness
        doc["updated_at"] = now

        await db.learning_roadmaps.replace_one(query, doc)
        return cls._to_response(doc)

    @classmethod
    async def delete_roadmap(
        cls,
        user_id: str,
        roadmap_id: str,
        db: AsyncIOMotorDatabase,
    ) -> bool:
        """
        Deletes a specific learning roadmap.
        """
        query: Dict[str, Any] = {"user_id": user_id}
        if ObjectId.is_valid(roadmap_id):
            query["_id"] = ObjectId(roadmap_id)
        else:
            query["id"] = roadmap_id

        res = await db.learning_roadmaps.delete_one(query)
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Learning roadmap not found.")
        return True

    @staticmethod
    def _to_response(doc: Dict[str, Any]) -> LearningRoadmapResponse:
        """
        Converts MongoDB document to validated LearningRoadmapResponse.
        """
        data = dict(doc)
        if "_id" in data:
            data["id"] = str(data.pop("_id"))
        elif "id" in data:
            data["id"] = str(data["id"])

        return LearningRoadmapResponse.model_validate(data)
