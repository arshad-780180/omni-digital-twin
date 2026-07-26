from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class EducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

class ExperienceItem(BaseModel):
    role: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)

class ProjectItem(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    link: Optional[str] = None

class CertificationItem(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    date: Optional[str] = None

class AchievementItem(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class ParsedResumeData(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    education: List[EducationItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    certifications: List[CertificationItem] = Field(default_factory=list)
    achievements: List[AchievementItem] = Field(default_factory=list)

class ResumeUploadResponse(BaseModel):
    message: str
    file_url: str
    extracted_skills: List[str] = Field(default_factory=list)
    parsed_data: ParsedResumeData

class ResumeRecordInDB(BaseModel):
    id: Optional[str] = None
    user_id: str
    file_url: str
    uploaded_at: datetime
    parsed_data: ParsedResumeData
    parsing_method: str = "ai"
