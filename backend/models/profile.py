from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime

class ProfileBase(BaseModel):
    full_name: Optional[str] = None
    skills: List[str] = []
    social_links: List[str] = []

class ProfileCreate(ProfileBase):
    pass

class ProfileInDB(ProfileBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class ResumeBase(BaseModel):
    file_url: str

class ResumeInDB(ResumeBase):
    id: str
    user_id: str
    uploaded_at: datetime

class ProfileResponse(ProfileBase):
    id: str
    user_id: str
