from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import httpx
from typing import Dict, List

from database.connection import get_db
from models.user import UserInDB
from models.github import (
    GitHubDataResponse,
    GitHubProfileInfo,
    RepositoryInfo,
    GitHubAnalyzeRequest,
    GitHubAnalyzeResponse,
)
from services.github_service import GitHubService
from services.github_ai_service import GitHubAIService
from auth.routes import get_current_user

router = APIRouter(prefix="/github", tags=["github"])

class GitHubSyncRequest(BaseModel):
    username: str

@router.post("/sync", response_model=GitHubDataResponse)
async def sync_github(request: GitHubSyncRequest, current_user: UserInDB = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    username = request.username
    
    async with httpx.AsyncClient() as client:
        # Fetch user's repositories
        # Note: Unauthenticated requests are limited to 60/hr
        response = await client.get(
            f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated",
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="GitHub user not found")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"GitHub API Error: {response.text}")
            
        repos = response.json()
        
    total_repos = len(repos)
    total_commits = 0
    
    # Aggregate languages
    language_counts: Dict[str, int] = {}
    
    for repo in repos:
        lang = repo.get("language")
        if lang:
            language_counts[lang] = language_counts.get(lang, 0) + 1
            
    sorted_languages = sorted(
        [{"language": k, "count": v} for k, v in language_counts.items()],
        key=lambda x: x["count"], 
        reverse=True
    )
    
    github_data = {
        "user_id": current_user.id,
        "username": username,
        "total_commits": total_commits,
        "top_languages": sorted_languages[:10],
        "total_repos": total_repos,
        "last_synced_at": datetime.utcnow()
    }
    
    await db.github_data.update_one(
        {"user_id": current_user.id},
        {"$set": github_data},
        upsert=True
    )
    
    doc = await db.github_data.find_one({"user_id": current_user.id})
    doc["id"] = str(doc.pop("_id"))
    
    return GitHubDataResponse(**doc)

@router.get("/report", response_model=GitHubDataResponse)
async def get_github_report(current_user: UserInDB = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await db.github_data.find_one({"user_id": current_user.id})
    if not doc:
        raise HTTPException(status_code=404, detail="No GitHub data found. Please sync first.")
        
    doc["id"] = str(doc.pop("_id"))
    return GitHubDataResponse(**doc)

# =========================================================
# Phase 2: AI GitHub Intelligence Engine Endpoints
# =========================================================

@router.post("/analyze", response_model=GitHubAnalyzeResponse)
async def analyze_github_profile(
    request: GitHubAnalyzeRequest,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    username = request.username.strip()
    profile = await GitHubService.fetch_user_profile(username)
    repos = await GitHubService.fetch_user_repositories(username)
    analysis, method = await GitHubAIService.analyze_portfolio(current_user.id, profile, repos, db)

    record = GitHubAnalyzeResponse(
        user_id=current_user.id,
        username=username,
        profile=profile,
        repositories=repos,
        analysis=analysis,
        analyzed_at=datetime.utcnow(),
        parsing_method=method
    )
    record_dict = record.model_dump()
    result = await db.github_analysis.insert_one(record_dict)
    record.id = str(result.inserted_id)

    # Also keep legacy github_data updated for backward compatibility
    language_counts: Dict[str, int] = {}
    for r in repos:
        if r.language and r.language != "Other":
            language_counts[r.language] = language_counts.get(r.language, 0) + 1
    sorted_languages = sorted(
        [{"language": k, "count": v} for k, v in language_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )
    legacy_data = {
        "user_id": current_user.id,
        "username": username,
        "total_commits": profile.public_repos * 5,
        "top_languages": sorted_languages[:10],
        "total_repos": profile.public_repos,
        "last_synced_at": datetime.utcnow()
    }
    await db.github_data.update_one(
        {"user_id": current_user.id},
        {"$set": legacy_data},
        upsert=True
    )

    return record

@router.get("/latest", response_model=GitHubAnalyzeResponse)
async def get_latest_github_analysis(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    cursor = db.github_analysis.find({"user_id": current_user.id}).sort("analyzed_at", -1)
    docs = await cursor.to_list(length=1)
    if not docs:
        raise HTTPException(status_code=404, detail="No GitHub analysis found. Please analyze a profile first.")
    doc = docs[0]
    doc["id"] = str(doc.pop("_id"))
    return GitHubAnalyzeResponse(**doc)

@router.get("/profile", response_model=GitHubProfileInfo)
async def get_github_profile_info(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    cursor = db.github_analysis.find({"user_id": current_user.id}).sort("analyzed_at", -1)
    docs = await cursor.to_list(length=1)
    if not docs:
        raise HTTPException(status_code=404, detail="No GitHub profile found. Please analyze a profile first.")
    return GitHubProfileInfo(**docs[0]["profile"])

@router.get("/repos", response_model=List[RepositoryInfo])
async def get_github_repositories(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    cursor = db.github_analysis.find({"user_id": current_user.id}).sort("analyzed_at", -1)
    docs = await cursor.to_list(length=1)
    if not docs:
        raise HTTPException(status_code=404, detail="No GitHub repositories found. Please analyze a profile first.")
    return [RepositoryInfo(**r) for r in docs[0]["repositories"]]

