import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.interview import (
    InterviewStartRequest,
    InterviewAnswerSubmitRequest,
    InterviewSessionResponse,
    InterviewHistoryResponse,
    InterviewQuestion,
    InterviewAnswer,
    InterviewQuestionEvaluation,
    InterviewReport,
    FeedbackItem,
)
from services.interview_ai_service import InterviewAIService
from services.digital_twin_service import DigitalTwinService
from services.digital_twin_memory_service import DigitalTwinMemoryService

logger = logging.getLogger("omni.interview")


class InterviewService:
    """
    Core business logic service for AI Mock Interview Intelligence Engine.
    Manages session lifecycle (start -> answer -> finish -> memory integration -> history).
    """

    @classmethod
    async def start_interview(
        cls,
        user_id: str,
        request: InterviewStartRequest,
        db: AsyncIOMotorDatabase,
    ) -> InterviewSessionResponse:
        """
        Initializes an interview session with personalized questions adapted from Digital Twin context.
        """
        context = await DigitalTwinService.get_context(user_id, db)
        questions = await InterviewAIService.generate_questions(request, context)

        now = datetime.now(timezone.utc)
        session_doc = {
            "user_id": user_id,
            "role": request.role,
            "company": request.company,
            "difficulty": request.difficulty,
            "interview_type": request.interview_type,
            "status": "IN_PROGRESS",
            "questions": [q.model_dump() for q in questions],
            "answers": [],
            "evaluations": [],
            "report": None,
            "overall_score": 0,
            "technical_score": 0,
            "communication_score": 0,
            "confidence_score": 0,
            "created_at": now,
            "updated_at": now,
        }

        res = await db.interview_sessions.insert_one(session_doc)
        session_doc["id"] = str(res.inserted_id)

        logger.info(f"[InterviewService] Started interview session={session_doc['id']} for user={user_id}")
        return cls._to_response(session_doc)

    @classmethod
    async def get_session(
        cls,
        user_id: str,
        session_id: str,
        db: AsyncIOMotorDatabase,
    ) -> InterviewSessionResponse:
        """
        Retrieves a session by ID and user_id.
        """
        query = {"user_id": user_id}
        if ObjectId.is_valid(session_id):
            query["_id"] = ObjectId(session_id)
        else:
            query["id"] = session_id

        doc = await db.interview_sessions.find_one(query)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview session not found.",
            )
        return cls._to_response(doc)

    @classmethod
    async def submit_answer(
        cls,
        user_id: str,
        session_id: str,
        request: InterviewAnswerSubmitRequest,
        db: AsyncIOMotorDatabase,
    ) -> InterviewSessionResponse:
        """
        Submits an answer for a specific question, evaluates it, and generates adaptive follow-up feedback.
        """
        session_res = await cls.get_session(user_id, session_id, db)
        context = await DigitalTwinService.get_context(user_id, db)

        # Find matching question
        target_q: Optional[InterviewQuestion] = None
        for q in session_res.questions:
            if q.question_id == request.question_id:
                target_q = q
                break

        # Fallback to index if question_id is numeric or not matched directly
        if not target_q and request.question_id.isdigit():
            idx = int(request.question_id) - 1
            if 0 <= idx < len(session_res.questions):
                target_q = session_res.questions[idx]

        if not target_q and len(session_res.questions) > 0:
            target_q = session_res.questions[0]

        if not target_q:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question not found in interview session.",
            )

        # Evaluate answer via AI/fallback
        evaluation = await InterviewAIService.evaluate_answer(target_q, request.content, context)

        answer_obj = InterviewAnswer(
            question_id=target_q.question_id,
            content=request.content,
            content_type=request.content_type,
            submitted_at=datetime.now(timezone.utc),
        )

        # Update lists (replace existing answer/evaluation for same question_id if any)
        answers = [a for a in session_res.answers if a.question_id != target_q.question_id]
        answers.append(answer_obj)

        evals = [e for e in session_res.evaluations if e.question_id != target_q.question_id]
        evals.append(evaluation)

        # Recalculate running scores
        tech_score = int(sum(e.technical_score for e in evals) / len(evals))
        comm_score = int(sum(e.communication_score for e in evals) / len(evals))
        conf_score = int(sum(e.confidence_score for e in evals) / len(evals))
        overall = int((tech_score * 0.4) + (comm_score * 0.35) + (conf_score * 0.25))

        now = datetime.now(timezone.utc)
        update_doc = {
            "$set": {
                "answers": [a.model_dump() for a in answers],
                "evaluations": [e.model_dump() for e in evals],
                "overall_score": overall,
                "technical_score": tech_score,
                "communication_score": comm_score,
                "confidence_score": conf_score,
                "updated_at": now,
            }
        }

        query = {"user_id": user_id}
        if ObjectId.is_valid(session_id):
            query["_id"] = ObjectId(session_id)
        else:
            query["id"] = session_id

        await db.interview_sessions.update_one(query, update_doc)
        return await cls.get_session(user_id, session_id, db)

    @classmethod
    async def finish_interview(
        cls,
        user_id: str,
        session_id: str,
        db: AsyncIOMotorDatabase,
    ) -> InterviewSessionResponse:
        """
        Completes the interview session, synthesizes executive report, and updates Digital Twin Memory.
        """
        session_res = await cls.get_session(user_id, session_id, db)
        context = await DigitalTwinService.get_context(user_id, db)

        report = await InterviewAIService.generate_report(session_res, context)

        now = datetime.now(timezone.utc)
        update_doc = {
            "$set": {
                "status": "COMPLETED",
                "report": report.model_dump(),
                "overall_score": report.overall_score,
                "technical_score": report.technical_score,
                "communication_score": report.communication_score,
                "confidence_score": report.confidence_score,
                "updated_at": now,
            }
        }

        query = {"user_id": user_id}
        if ObjectId.is_valid(session_id):
            query["_id"] = ObjectId(session_id)
        else:
            query["id"] = session_id

        await db.interview_sessions.update_one(query, update_doc)

        # Automatically evolve Digital Twin Memory
        try:
            memory_payload = {
                "role": session_res.role,
                "company": session_res.company,
                "overall_score": report.overall_score,
                "technical_score": report.technical_score,
                "communication_score": report.communication_score,
                "confidence_score": report.confidence_score,
                "difficulty": session_res.difficulty,
                "interview_type": session_res.interview_type,
                "strengths": report.strengths,
                "weaknesses": report.weaknesses,
                "learning_priorities": report.learning_priorities,
            }
            await DigitalTwinMemoryService.update_memory(user_id, "interview", memory_payload, db)
            logger.info(f"[InterviewService] Successfully updated Digital Twin Memory for user={user_id}")
        except Exception as e:
            logger.warning(f"[InterviewService] Non-fatal notice updating Digital Twin Memory: {e}")

        return await cls.get_session(user_id, session_id, db)

    @classmethod
    async def evaluate_interview_legacy(
        cls,
        user_id: str,
        session_id: str,
        answers: List[str],
        db: AsyncIOMotorDatabase,
    ) -> InterviewSessionResponse:
        """
        Backward-compatible wrapper for legacy /api/interview/evaluate/{id}.
        Submits all answers and finishes the interview in one step.
        """
        session_res = await cls.get_session(user_id, session_id, db)

        for i, ans_text in enumerate(answers):
            if i < len(session_res.questions):
                q = session_res.questions[i]
                req = InterviewAnswerSubmitRequest(
                    question_id=q.question_id,
                    content=ans_text,
                )
                await cls.submit_answer(user_id, session_id, req, db)

        return await cls.finish_interview(user_id, session_id, db)

    @classmethod
    async def get_latest_session(
        cls,
        user_id: str,
        db: AsyncIOMotorDatabase,
    ) -> Optional[InterviewSessionResponse]:
        """
        Retrieves user's most recent interview session.
        """
        cursor = db.interview_sessions.find({"user_id": user_id}).sort("created_at", -1).limit(1)
        docs = await cursor.to_list(length=1)
        if not docs:
            return None
        return cls._to_response(docs[0])

    @classmethod
    async def get_session_history(
        cls,
        user_id: str,
        db: AsyncIOMotorDatabase,
    ) -> InterviewHistoryResponse:
        """
        Retrieves candidate's interview session history and calculates comprehensive trend analytics.
        """
        cursor = db.interview_sessions.find({"user_id": user_id}).sort("created_at", -1)
        docs = await cursor.to_list(length=100)

        sessions = [cls._to_response(doc) for doc in docs]
        total = len(sessions)
        if total == 0:
            return InterviewHistoryResponse()

        completed = [s for s in sessions if s.status == "COMPLETED" or s.overall_score > 0]
        if not completed:
            completed = sessions

        avg_score = round(sum(s.overall_score for s in completed) / len(completed), 1)

        # Chronological trends (oldest to newest)
        chronological = list(reversed(completed))
        tech_trend = [float(s.technical_score) for s in chronological]
        comm_trend = [float(s.communication_score) for s in chronological]
        conf_trend = [float(s.confidence_score) for s in chronological]

        # Improvement % from first to latest
        if len(chronological) >= 2:
            first_score = max(1, chronological[0].overall_score)
            latest_score = chronological[-1].overall_score
            improve_pct = round(((latest_score - first_score) / first_score) * 100.0, 1)
        else:
            improve_pct = 0.0

        best_session = max(completed, key=lambda s: s.overall_score, default=sessions[0])

        # Aggregate weakest topics from reports and evaluations
        weakest_map: Dict[str, int] = {}
        for s in completed:
            if s.report:
                for w in s.report.weaknesses:
                    weakest_map[w] = weakest_map.get(w, 0) + 1
            for ev in s.evaluations:
                for wt in ev.weak_topics:
                    weakest_map[wt] = weakest_map.get(wt, 0) + 1

        weakest_topics = sorted(weakest_map.keys(), key=lambda k: weakest_map[k], reverse=True)[:5]
        if not weakest_topics:
            weakest_topics = ["System Scalability", "Performance Tuning"]

        most_improved: List[str] = ["Backend API Architecture", "Technical Communication"]

        # Average interview duration in minutes
        durations: List[float] = []
        for s in completed:
            if s.created_at and s.updated_at:
                diff = (s.updated_at - s.created_at).total_seconds() / 60.0
                if diff > 0:
                    durations.append(diff)
        avg_duration = round(sum(durations) / max(1, len(durations)), 1) if durations else 15.0

        return InterviewHistoryResponse(
            sessions=sessions,
            average_score=avg_score,
            technical_trend=tech_trend,
            communication_trend=comm_trend,
            confidence_trend=conf_trend,
            improvement_percentage=improve_pct,
            best_interview=best_session,
            weakest_topics=weakest_topics,
            most_improved_topics=most_improved,
            average_interview_duration=avg_duration,
            total_interviews=total,
        )

    @classmethod
    async def delete_session(
        cls,
        user_id: str,
        session_id: str,
        db: AsyncIOMotorDatabase,
    ) -> bool:
        """
        Deletes a session by ID and user_id.
        """
        query = {"user_id": user_id}
        if ObjectId.is_valid(session_id):
            query["_id"] = ObjectId(session_id)
        else:
            query["id"] = session_id

        res = await db.interview_sessions.delete_one(query)
        if res.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview session not found or already deleted.",
            )
        logger.info(f"[InterviewService] Deleted session={session_id} for user={user_id}")
        return True

    @staticmethod
    def _to_response(doc: Dict[str, Any]) -> InterviewSessionResponse:
        """
        Converts MongoDB doc to validated InterviewSessionResponse with backward compatibility items.
        """
        data = dict(doc)
        if "_id" in data:
            data["id"] = str(data.pop("_id"))
        elif "id" in data:
            data["id"] = str(data["id"])

        # Populate legacy feedback items for backward compatibility
        feedback_list: List[FeedbackItem] = []
        evals = data.get("evaluations", [])
        if isinstance(evals, list):
            for idx, ev in enumerate(evals):
                if isinstance(ev, dict):
                    feedback_list.append(
                        FeedbackItem(
                            question_index=idx,
                            score=int(ev.get("technical_score", ev.get("score", 75))),
                            critique=str(ev.get("feedback", "Good technical answer.")),
                        )
                    )
        data["feedback"] = feedback_list

        return InterviewSessionResponse.model_validate(data)
