from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId
import json
import re

from database.connection import get_db
from models.user import UserInDB
from models.interview import InterviewGenerateRequest, InterviewEvaluateRequest, InterviewSessionResponse, FeedbackItem
from auth.routes import get_current_user
from ai.llm_provider import get_llm_provider

router = APIRouter(prefix="/interview", tags=["interview"])

@router.post("/generate", response_model=InterviewSessionResponse)
async def generate_interview(request: InterviewGenerateRequest, current_user: UserInDB = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    llm = get_llm_provider()
    
    prompt = f"""
    You are an expert technical interviewer. Generate exactly 3 interview questions for a candidate applying for the role of '{request.target_role}'.
    Provide the output strictly as a JSON list of strings, with no markdown formatting and no other text.
    Example: ["Question 1?", "Question 2?", "Question 3?"]
    """
    
    try:
        response_text = await llm.generate_text(prompt)
        # Clean up possible markdown code blocks if the model still includes them
        cleaned_text = re.sub(r'```json|```', '', response_text).strip()
        questions = json.loads(cleaned_text)
        
        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError("Invalid format received from LLM")
            
    except Exception as e:
        print(f"LLM Error: {e}")
        # Fallback in case LLM fails or hits quota
        questions = [
            f"Can you describe a challenging project you worked on related to {request.target_role}?",
            "How do you handle technical debt in your codebase?",
            f"What are the most important skills for a {request.target_role} and why?"
        ]

    session_doc = {
        "user_id": current_user.id,
        "target_role": request.target_role,
        "questions": questions[:3], # Ensure we only get up to 3
        "answers": [],
        "feedback": [],
        "overall_score": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.interviews.insert_one(session_doc)
    session_doc["id"] = str(result.inserted_id)
    
    return InterviewSessionResponse(**session_doc)


@router.post("/evaluate/{interview_id}", response_model=InterviewSessionResponse)
async def evaluate_interview(interview_id: str, request: InterviewEvaluateRequest, current_user: UserInDB = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        obj_id = ObjectId(interview_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid interview ID")

    session = await db.interviews.find_one({"_id": obj_id, "user_id": current_user.id})
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    questions = session.get("questions", [])
    answers = request.answers
    
    if len(answers) != len(questions):
        raise HTTPException(status_code=400, detail="Number of answers must match number of questions")

    # Construct prompt for LLM evaluation
    qa_text = ""
    for i, (q, a) in enumerate(zip(questions, answers)):
        qa_text += f"Q{i}: {q}\nA{i}: {a}\n\n"

    prompt = f"""
    You are an expert technical interviewer evaluating a candidate for the role of '{session.get('target_role')}'.
    Evaluate the following Questions (Q) and Answers (A):
    
    {qa_text}
    
    Provide your evaluation strictly as a JSON object with the following schema, and no other text or markdown formatting:
    {{
        "feedback": [
            {{ "question_index": 0, "score": 8, "critique": "Brief feedback here..." }},
            {{ "question_index": 1, "score": 5, "critique": "Brief feedback here..." }}
        ],
        "overall_score": 75
    }}
    Note: 'score' in feedback should be out of 10. 'overall_score' should be out of 100.
    """

    llm = get_llm_provider()
    
    try:
        response_text = await llm.generate_text(prompt)
        cleaned_text = re.sub(r'```json|```', '', response_text).strip()
        eval_data = json.loads(cleaned_text)
        
        feedback = eval_data.get("feedback", [])
        overall_score = eval_data.get("overall_score", 0)
        
    except Exception as e:
        print(f"LLM Eval Error: {e}")
        # Fallback
        feedback = [{"question_index": i, "score": 7, "critique": "Good effort, but could use more technical depth."} for i in range(len(questions))]
        overall_score = 70

    # Update session in DB
    update_data = {
        "answers": answers,
        "feedback": feedback,
        "overall_score": overall_score,
        "updated_at": datetime.utcnow()
    }
    
    await db.interviews.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )
    
    session.update(update_data)
    session["id"] = str(session.pop("_id"))
    
    return InterviewSessionResponse(**session)
