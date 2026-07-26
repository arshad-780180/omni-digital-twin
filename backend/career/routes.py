from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from typing import List, Optional, Union
import re

from database.connection import get_db
from models.user import UserInDB
from models.career import (
    JobAnalyzeRequest,
    CareerReportResponse,
    CareerAnalyzeResponse
)
from auth.routes import get_current_user
from services.career_service import CareerService

router = APIRouter(prefix="/career", tags=["career"])


# =========================================================
# Phase 3: AI Career Readiness Engine Endpoints
# =========================================================
@router.post("/analyze", response_model=Union[CareerAnalyzeResponse, CareerReportResponse])
async def analyze_career(
    request: Optional[JobAnalyzeRequest] = None,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Unified analyze endpoint:
    - If called without arguments or empty body, runs Phase 3 AI Career Readiness Engine
      (automatically reading db.resumes, db.github_analysis, and db.profiles).
    - If called with job_title and job_description, performs legacy ATS job match analysis.
    """
    if request and request.job_title and request.job_description:
        return await _legacy_analyze_job_match(request, current_user, db)

    try:
        report = await CareerService.generate_career_readiness_report(current_user.id, db)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI career readiness report: {str(e)}"
        )


@router.get("/latest", response_model=CareerAnalyzeResponse)
async def get_latest_career_report(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Returns the most recent AI Career Readiness report for the user.
    """
    report = await CareerService.get_latest_career_report(current_user.id, db)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No career readiness analysis found for this user."
        )
    return report


@router.get("/history", response_model=List[CareerAnalyzeResponse])
async def get_career_history(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Returns previous career readiness analyses sorted by newest first.
    """
    reports = await CareerService.get_career_history(current_user.id, db)
    return reports


# =========================================================
# Legacy ATS Job-Match Support (Backward Compatibility)
# =========================================================
async def _legacy_analyze_job_match(
    request: JobAnalyzeRequest,
    current_user: UserInDB,
    db: AsyncIOMotorDatabase
) -> CareerReportResponse:
    profile = await db.profiles.find_one({"user_id": current_user.id})
    github = await db.github_data.find_one({"user_id": current_user.id})

    user_skills = []
    if profile and "skills" in profile:
        user_skills.extend([s.lower() for s in profile["skills"]])
    if github and "top_languages" in github:
        user_skills.extend([l["language"].lower() for l in github["top_languages"]])

    user_skills = list(set(user_skills))

    tech_keywords = {
        "python", "javascript", "typescript", "react", "node", "node.js", "express",
        "fastapi", "django", "flask", "java", "spring", "c++", "c#", ".net",
        "ruby", "rails", "go", "golang", "rust", "php", "laravel",
        "sql", "mysql", "postgresql", "mongodb", "nosql", "redis", "elasticsearch",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd",
        "git", "github", "gitlab", "linux", "html", "css", "tailwind", "sass",
        "machine learning", "ai", "data science", "pandas", "numpy", "tensorflow", "pytorch",
        "agile", "scrum", "kanban", "rest", "graphql", "grpc", "microservices"
    }

    jd_tokens = set(re.findall(r'\b[a-zA-Z\.+#]+\b', request.job_description.lower()))
    required_skills = jd_tokens.intersection(tech_keywords)
    if not required_skills:
        required_skills = {"communication", "problem solving", "teamwork"}

    matched_skills = []
    missing_skills = []

    for req_skill in required_skills:
        found = False
        for user_skill in user_skills:
            if req_skill in user_skill or user_skill in req_skill:
                found = True
                break
        
        clean_skill = req_skill.title()
        if req_skill in ["javascript", "typescript"]:
            clean_skill = clean_skill.replace("script", "Script")
        elif req_skill in ["node.js", "react", "html", "css", "sql", "aws", "gcp", "ai", "ci/cd"]:
            clean_skill = req_skill.upper()
            
        if found:
            matched_skills.append(clean_skill)
        else:
            missing_skills.append(clean_skill)

    total_required = len(required_skills)
    match_score = 0
    if total_required > 0:
        match_score = int((len(matched_skills) / total_required) * 100)

    report_doc = {
        "user_id": current_user.id,
        "job_title": request.job_title,
        "match_score": match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "created_at": datetime.utcnow()
    }
    
    result = await db.career_reports.insert_one(report_doc)
    report_doc["id"] = str(result.inserted_id)
    
    return CareerReportResponse(**report_doc)


@router.post("/job-match", response_model=CareerReportResponse)
async def legacy_job_match(
    request: JobAnalyzeRequest,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    return await _legacy_analyze_job_match(request, current_user, db)


@router.get("/reports", response_model=List[CareerReportResponse])
async def get_career_reports(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    cursor = db.career_reports.find({"user_id": current_user.id}).sort("created_at", -1)
    reports = await cursor.to_list(length=50)
    
    for report in reports:
        report["id"] = str(report.pop("_id"))
        
    return reports
