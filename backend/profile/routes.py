from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from datetime import datetime
import os
import shutil

from database.connection import get_db
from models.user import UserInDB
from models.profile import ProfileResponse, ProfileInDB, ProfileCreate
from models.resume import ResumeUploadResponse, ResumeRecordInDB
from services.resume_service import ResumeService
from auth.routes import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.get("", response_model=ProfileResponse)
async def get_profile(current_user: UserInDB = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    profile = await db.profiles.find_one({"user_id": current_user.id})
    if not profile:
        # Create an empty profile for the user if it doesn't exist
        new_profile = {
            "user_id": current_user.id,
            "full_name": current_user.full_name or "",
            "skills": [],
            "social_links": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await db.profiles.insert_one(new_profile)
        new_profile["id"] = str(result.inserted_id)
        return ProfileResponse(**new_profile)
        
    profile["id"] = str(profile.pop("_id"))
    return ProfileResponse(**profile)

@router.post("/resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...), current_user: UserInDB = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    filename_lower = file.filename.lower()
    if not (filename_lower.endswith(".pdf") or filename_lower.endswith(".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        
    file_location = f"{UPLOAD_DIR}/{current_user.id}_{file.filename}"
    
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")
        
    try:
        response, _ = await ResumeService.process_resume(current_user.id, file_location, db)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {str(e)}")

@router.get("/resume/latest", response_model=ResumeRecordInDB)
async def get_latest_resume(current_user: UserInDB = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    cursor = db.resumes.find({"user_id": current_user.id}).sort("uploaded_at", -1)
    docs = await cursor.to_list(length=1)
    if not docs:
        raise HTTPException(status_code=404, detail="No resume found for user")
    doc = docs[0]
    doc["id"] = str(doc.pop("_id"))
    return ResumeRecordInDB(**doc)

@router.post("/skills")
async def update_skills(skills: List[str], current_user: UserInDB = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    await db.profiles.update_one(
        {"user_id": current_user.id},
        {"$set": {"skills": skills, "updated_at": datetime.utcnow()}}
    )
    return {"message": "Skills updated successfully", "skills": skills}

