import logging
import inspect
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from models.digital_twin_memory import (
    DigitalTwinMemoryResponse,
    DigitalTwinTimelineEvent,
    DigitalTwinSummaryResponse,
)
from services.digital_twin_memory_ai_service import DigitalTwinMemoryAIService
from utils.logger import get_logger

logger = get_logger("digital_twin.memory")


def _dedup_list(existing: List[str], new_items: List[str], max_items: int = 50) -> List[str]:
    """
    Case-insensitive deduplication that preserves existing order and casing.
    """
    seen = {item.lower(): True for item in existing if isinstance(item, str)}
    result = list(existing)
    for item in new_items:
        if isinstance(item, str) and item.strip():
            cleaned = item.strip()
            if cleaned.lower() not in seen:
                seen[cleaned.lower()] = True
                result.append(cleaned)
    return result[:max_items]


async def _safe_find_one(collection, query: dict) -> Optional[Dict[str, Any]]:
    try:
        res = collection.find_one(query)
        if inspect.isawaitable(res):
            return await res
        return res if isinstance(res, dict) else None
    except Exception:
        return None


async def _safe_find_list(collection, query: dict, limit: int = 20) -> List[Dict[str, Any]]:
    try:
        cursor = collection.find(query).sort("created_at", 1).limit(limit)
        res = cursor.to_list(length=limit)
        if inspect.isawaitable(res):
            items = await res
        else:
            items = res
        return items if isinstance(items, list) else []
    except Exception:
        return []


class DigitalTwinMemoryService:
    """
    Core persistent memory service for OMNI Digital Twin.
    Continuously accumulates, merges, evolves, and rebuilds candidate career memory across all modules.
    """

    @classmethod
    async def create_memory(
        cls,
        user_id: str,
        db: AsyncIOMotorDatabase,
        initial_data: Optional[Dict[str, Any]] = None,
    ) -> DigitalTwinMemoryResponse:
        """
        Creates an initial baseline memory document for a user.
        """
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d %H:%M")

        baseline_doc: Dict[str, Any] = {
            "user_id": user_id,
            "current_role": "Software Engineer",
            "target_roles": [],
            "core_skills": [],
            "emerging_skills": [],
            "missing_skills": [],
            "preferred_domains": [],
            "preferred_companies": [],
            "github_strengths": [],
            "resume_strengths": [],
            "career_strengths": [],
            "ats_history_summary": [],
            "job_matching_summary": [],
            "learning_history": [],
            "interview_history": [],
            "personality_observations": [],
            "communication_observations": [],
            "career_goals": [],
            "confidence_scores": {"overall": 0.85},
            "timeline": [
                {
                    "date": date_str,
                    "event": "Digital Twin memory initialized",
                    "source_module": "system",
                    "category": "milestone",
                    "details": "Persistent career memory created."
                }
            ],
            "metadata": {
                "version": 1,
                "update_count": 0,
                "last_module_updated": "system",
            },
            "created_at": now,
            "updated_at": now,
        }

        if initial_data and isinstance(initial_data, dict):
            baseline_doc = cls.merge_memories(baseline_doc, "init", initial_data)

        res = await db.digital_twin_memory.insert_one(baseline_doc)
        if inspect.isawaitable(res):
            res = await res

        if hasattr(res, "inserted_id") and res.inserted_id:
            baseline_doc["id"] = str(res.inserted_id)

        logger.info(f"[DigitalTwinMemoryService] Created baseline memory for user={user_id}")
        return DigitalTwinMemoryResponse.model_validate(baseline_doc)

    @classmethod
    async def load_memory(
        cls,
        user_id: str,
        db: AsyncIOMotorDatabase,
    ) -> DigitalTwinMemoryResponse:
        """
        Retrieves user's Digital Twin memory document or initializes one if not present.
        """
        doc = await _safe_find_one(db.digital_twin_memory, {"user_id": user_id})
        if not doc:
            return await cls.create_memory(user_id, db)

        if "_id" in doc:
            doc["id"] = str(doc["_id"])
        return DigitalTwinMemoryResponse.model_validate(doc)

    @classmethod
    async def update_memory(
        cls,
        user_id: str,
        source_module: str,
        payload: Any,
        db: AsyncIOMotorDatabase,
    ) -> Optional[DigitalTwinMemoryResponse]:
        """
        Ingests structured insights from an OMNI module (resume, github, career, ats, job_matching)
        and merges them into the user's persistent memory document.
        Never throws exceptions that would disrupt the calling module.
        """
        try:
            doc = await _safe_find_one(db.digital_twin_memory, {"user_id": user_id})
            if not doc:
                memory_resp = await cls.create_memory(user_id, db)
                doc = memory_resp.model_dump() if hasattr(memory_resp, "model_dump") else memory_resp.dict()

            payload_dict: Dict[str, Any] = {}
            if isinstance(payload, dict):
                payload_dict = payload
            elif hasattr(payload, "model_dump"):
                payload_dict = payload.model_dump()
            elif hasattr(payload, "dict"):
                payload_dict = payload.dict()

            merged = cls.merge_memories(doc, source_module, payload_dict)
            merged = cls.summarize_long_histories(merged)
            merged["updated_at"] = datetime.now(timezone.utc)

            doc_id = doc.get("_id") or ObjectId(doc.get("id")) if doc.get("id") else None
            query = {"_id": doc_id} if doc_id else {"user_id": user_id}

            # Update document in MongoDB
            update_res = await db.digital_twin_memory.replace_one(query, merged)
            if inspect.isawaitable(update_res):
                await update_res

            if "_id" in merged:
                merged["id"] = str(merged["_id"])

            logger.info(
                f"[DigitalTwinMemoryService] Evolved user={user_id} memory via module='{source_module}' (v={merged.get('metadata', {}).get('version', 1)})"
            )
            return DigitalTwinMemoryResponse.model_validate(merged)
        except Exception as e:
            logger.error(f"[DigitalTwinMemoryService] Error updating memory for user={user_id}: {str(e)}", exc_info=True)
            return None

    @classmethod
    def merge_memories(
        cls,
        existing_doc: Dict[str, Any],
        source_module: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Smart merge logic that accumulates knowledge without blind overwriting.
        - Deduplicates arrays case-insensitively
        - Appends timestamped timeline events
        - Increments version metadata
        """
        merged = dict(existing_doc)
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

        # Ensure defaults exist
        for key in [
            "target_roles", "core_skills", "emerging_skills", "missing_skills",
            "preferred_domains", "preferred_companies", "github_strengths",
            "resume_strengths", "career_strengths", "ats_history_summary",
            "job_matching_summary", "learning_history", "interview_history",
            "personality_observations", "communication_observations", "career_goals",
            "timeline"
        ]:
            if key not in merged or not isinstance(merged[key], list):
                merged[key] = []

        if "metadata" not in merged or not isinstance(merged["metadata"], dict):
            merged["metadata"] = {"version": 1, "update_count": 0}
        merged["metadata"]["version"] = int(merged["metadata"].get("version", 0)) + 1
        merged["metadata"]["update_count"] = int(merged["metadata"].get("update_count", 0)) + 1
        merged["metadata"]["last_module_updated"] = source_module

        # Module-specific smart extraction
        if source_module == "resume":
            parsed = payload.get("parsed_data", {}) if "parsed_data" in payload else payload
            skills = parsed.get("skills", [])
            merged["core_skills"] = _dedup_list(merged["core_skills"], skills)

            name = parsed.get("name")
            if name and not merged.get("current_role"):
                merged["current_role"] = f"Developer ({name})"

            exp = parsed.get("experience", [])
            if exp and isinstance(exp, list) and len(exp) > 0 and isinstance(exp[0], dict):
                first_role = exp[0].get("role") or exp[0].get("title")
                if first_role:
                    merged["current_role"] = str(first_role)

            merged["resume_strengths"] = _dedup_list(
                merged["resume_strengths"],
                [f"Verified {len(exp)} professional roles", f"Mastered {len(skills)} technical skills"]
            )
            merged["timeline"].append({
                "date": now_str,
                "event": f"Resume parsed ({len(skills)} skills identified)",
                "source_module": "resume",
                "category": "milestone",
                "details": f"Added {len(skills)} skills to core memory."
            })

        elif source_module == "github":
            top_langs = payload.get("top_languages", [])
            merged["core_skills"] = _dedup_list(merged["core_skills"], top_langs)

            analysis = payload.get("analysis", {}) if "analysis" in payload else payload
            strengths = analysis.get("strengths", [])
            merged["github_strengths"] = _dedup_list(merged["github_strengths"], strengths)

            gh_score = payload.get("github_score", 0)
            merged["timeline"].append({
                "date": now_str,
                "event": f"GitHub Portfolio analyzed (Score: {gh_score}/100)",
                "source_module": "github",
                "category": "technical",
                "details": f"Identified top languages: {', '.join(top_langs[:3])}."
            })

        elif source_module == "career":
            roles = payload.get("recommended_roles", [])
            role_names = [r.get("role_name", "") if isinstance(r, dict) else str(r) for r in roles]
            merged["target_roles"] = _dedup_list(merged["target_roles"], role_names)

            strengths = payload.get("strengths", [])
            weaknesses = payload.get("weaknesses", [])
            merged["career_strengths"] = _dedup_list(merged["career_strengths"], strengths)
            merged["missing_skills"] = _dedup_list(merged["missing_skills"], weaknesses)

            readiness = payload.get("developer_level", "Mid-Level")
            merged["timeline"].append({
                "date": now_str,
                "event": f"Career Readiness evaluated ({readiness})",
                "source_module": "career",
                "category": "milestone",
                "details": f"Recommended roles: {', '.join(role_names[:2])}."
            })

        elif source_module == "ats":
            job_title = payload.get("job_title", "Target Role")
            company = payload.get("company", "")
            score = payload.get("match_score", 0)
            summary_str = f"ATS check for {job_title}" + (f" at {company}" if company else "") + f" — Score: {score}%"
            if summary_str not in merged["ats_history_summary"]:
                merged["ats_history_summary"].append(summary_str)

            missing_kws = payload.get("missing_keywords", [])
            matched_kws = payload.get("matched_keywords", [])
            merged["missing_skills"] = _dedup_list(merged["missing_skills"], missing_kws)
            merged["core_skills"] = _dedup_list(merged["core_skills"], matched_kws)

            if job_title and job_title not in merged["target_roles"]:
                merged["target_roles"] = _dedup_list(merged["target_roles"], [job_title])
            if company and company not in merged["preferred_companies"]:
                merged["preferred_companies"] = _dedup_list(merged["preferred_companies"], [company])

            merged["timeline"].append({
                "date": now_str,
                "event": f"ATS Resume Optimization ({score}% for {job_title})",
                "source_module": "ats",
                "category": "optimization",
                "details": f"Identified {len(missing_kws)} keyword gaps."
            })

        elif source_module == "job_matching":
            job_title = payload.get("job_title", "Job Role")
            company = payload.get("company", "")
            score = payload.get("overall_job_match_score", 0)
            rec = payload.get("hiring_recommendation", "Consider")
            summary_str = f"Job Match for {job_title}" + (f" ({company})" if company else "") + f" — Score: {score}% ({rec})"
            if summary_str not in merged["job_matching_summary"]:
                merged["job_matching_summary"].append(summary_str)

            matched_skills = payload.get("matched_skills", [])
            missing_skills = payload.get("missing_skills", [])
            merged["core_skills"] = _dedup_list(merged["core_skills"], matched_skills)
            merged["missing_skills"] = _dedup_list(merged["missing_skills"], missing_skills)

            if job_title:
                merged["target_roles"] = _dedup_list(merged["target_roles"], [job_title])
            if company:
                merged["preferred_companies"] = _dedup_list(merged["preferred_companies"], [company])

            merged["timeline"].append({
                "date": now_str,
                "event": f"Job Match Evaluated ({score}% - {rec})",
                "source_module": "job_matching",
                "category": "evaluation",
                "details": f"Evaluated candidate fit for {job_title}."
            })

        elif source_module == "profile":
            skills = payload.get("skills", [])
            merged["core_skills"] = _dedup_list(merged["core_skills"], skills)
            name = payload.get("full_name")
            if name and not merged.get("current_role"):
                merged["current_role"] = f"Developer ({name})"
            merged["timeline"].append({
                "date": now_str,
                "event": "User Profile synced",
                "source_module": "profile",
                "category": "milestone",
                "details": f"Synced {len(skills)} profile skills."
            })

        elif source_module == "interview":
            role = payload.get("role", "Target Role")
            company = payload.get("company", "")
            score = payload.get("overall_score", 0)
            diff = payload.get("difficulty", "Medium")
            int_type = payload.get("interview_type", "Technical")
            summary_str = f"Mock Interview for {role}" + (f" ({company})" if company else "") + f" [{int_type}/{diff}] — Overall Score: {score}%"
            if summary_str not in merged["interview_history"]:
                merged["interview_history"].append(summary_str)

            if role:
                merged["target_roles"] = _dedup_list(merged["target_roles"], [role])
            if company:
                merged["preferred_companies"] = _dedup_list(merged["preferred_companies"], [company])

            strengths = payload.get("strengths", [])
            weaknesses = payload.get("weaknesses", [])
            priorities = payload.get("learning_priorities", [])
            merged["core_skills"] = _dedup_list(merged["core_skills"], strengths)
            merged["missing_skills"] = _dedup_list(merged["missing_skills"], weaknesses)
            for p in priorities:
                if p and p not in merged["learning_history"]:
                    merged["learning_history"].append(p)

            merged["timeline"].append({
                "date": now_str,
                "event": f"Mock Interview Completed ({score}% for {role})",
                "source_module": "interview",
                "category": "evaluation",
                "details": f"Completed {diff} {int_type} interview with score {score}%."
            })

        elif source_module == "learning":
            new_skills = payload.get("new_skills", [])
            completed_projects = payload.get("completed_projects", [])
            completed_certs = payload.get("completed_certifications", [])
            velocity = payload.get("learning_velocity", 0)
            progress = payload.get("career_progress", 0)

            merged["core_skills"] = _dedup_list(merged["core_skills"], new_skills)
            acquired_set = {s.lower() for s in new_skills if isinstance(s, str)}
            merged["missing_skills"] = [
                s for s in merged.get("missing_skills", [])
                if isinstance(s, str) and s.lower() not in acquired_set
            ]

            for p in completed_projects:
                p_str = str(p) if not isinstance(p, dict) else str(p.get("title", "Project"))
                p_entry = f"Completed Project: {p_str}"
                if p_entry not in merged["learning_history"]:
                    merged["learning_history"].append(p_entry)

            for c in completed_certs:
                c_str = str(c) if not isinstance(c, dict) else str(c.get("title", "Certification"))
                c_entry = f"Completed Certification: {c_str}"
                if c_entry not in merged["learning_history"]:
                    merged["learning_history"].append(c_entry)

            if "metadata" not in merged or not isinstance(merged["metadata"], dict):
                merged["metadata"] = {}
            merged["metadata"]["learning_velocity"] = velocity
            merged["metadata"]["career_progress"] = progress

            merged["timeline"].append({
                "date": now_str,
                "event": f"Learning Roadmap Milestone Completed ({len(new_skills)} skills acquired)",
                "source_module": "learning",
                "category": "milestone",
                "details": f"Acquired skills: {', '.join(new_skills[:5]) if new_skills else 'Progressed roadmap'}."
            })

        return merged

    @classmethod
    def summarize_long_histories(cls, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prevents unbounded array growth by capping long summaries while retaining milestones.
        """
        if "timeline" in doc and isinstance(doc["timeline"], list) and len(doc["timeline"]) > 50:
            doc["timeline"] = doc["timeline"][:10] + doc["timeline"][-40:]
        if "ats_history_summary" in doc and isinstance(doc["ats_history_summary"], list) and len(doc["ats_history_summary"]) > 30:
            doc["ats_history_summary"] = doc["ats_history_summary"][-30:]
        if "job_matching_summary" in doc and isinstance(doc["job_matching_summary"], list) and len(doc["job_matching_summary"]) > 30:
            doc["job_matching_summary"] = doc["job_matching_summary"][-30:]
        return doc

    @classmethod
    async def rebuild_memory_from_history(
        cls,
        user_id: str,
        db: AsyncIOMotorDatabase,
    ) -> DigitalTwinMemoryResponse:
        """
        Rebuilds persistent memory from scratch by scanning all historical analyses
        stored in profiles, resumes, github_analysis, career_analysis, ats_analysis, and job_matches.
        """
        logger.info(f"[DigitalTwinMemoryService] Rebuilding memory from history for user={user_id}")
        baseline = await cls.create_memory(user_id, db)
        doc = baseline.model_dump() if hasattr(baseline, "model_dump") else baseline.dict()

        # 1) Profiles
        profile = await _safe_find_one(db.profiles, {"user_id": user_id})
        if profile:
            doc = cls.merge_memories(doc, "profile", profile)

        # 2) Resumes
        resumes = await _safe_find_list(db.resumes, {"user_id": user_id}, limit=10)
        for r in resumes:
            doc = cls.merge_memories(doc, "resume", r)

        # 3) GitHub Analysis
        github_docs = await _safe_find_list(db.github_analysis, {"user_id": user_id}, limit=5)
        for g in github_docs:
            doc = cls.merge_memories(doc, "github", g)

        # 4) Career Analysis
        career_docs = await _safe_find_list(db.career_analysis, {"user_id": user_id}, limit=10)
        for c in career_docs:
            doc = cls.merge_memories(doc, "career", c)

        # 5) ATS Analysis
        ats_docs = await _safe_find_list(db.ats_analysis, {"user_id": user_id}, limit=15)
        for a in ats_docs:
            doc = cls.merge_memories(doc, "ats", a)

        # 6) Job Matches
        job_docs = await _safe_find_list(db.job_matches, {"user_id": user_id}, limit=15)
        for j in job_docs:
            doc = cls.merge_memories(doc, "job_matching", j)

        doc = cls.summarize_long_histories(doc)
        doc["updated_at"] = datetime.now(timezone.utc)

        doc_id = doc.get("_id") or ObjectId(doc.get("id")) if doc.get("id") else None
        query = {"_id": doc_id} if doc_id else {"user_id": user_id}

        res = await db.digital_twin_memory.replace_one(query, doc, upsert=True)
        if inspect.isawaitable(res):
            await res

        if "_id" in doc:
            doc["id"] = str(doc["_id"])

        logger.info(f"[DigitalTwinMemoryService] Successfully rebuilt memory for user={user_id}")
        return DigitalTwinMemoryResponse.model_validate(doc)

    @classmethod
    async def get_summary(
        cls,
        user_id: str,
        db: AsyncIOMotorDatabase,
    ) -> DigitalTwinSummaryResponse:
        """
        Returns AI-synthesized (or rule-based fallback) executive career summary of the user's memory.
        """
        memory_resp = await cls.load_memory(user_id, db)
        memory_doc = memory_resp.model_dump() if hasattr(memory_resp, "model_dump") else memory_resp.dict()

        summary, method = await DigitalTwinMemoryAIService.summarize_memory(user_id, memory_doc)
        return summary
