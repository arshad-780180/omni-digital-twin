import os
import re
import json
from datetime import datetime
from typing import List, Tuple, Optional
import PyPDF2
import docx

from models.resume import (
    ParsedResumeData,
    ResumeUploadResponse,
    ResumeRecordInDB,
    EducationItem,
    ExperienceItem,
    ProjectItem,
    CertificationItem,
    AchievementItem,
)
from ai.llm_provider import get_llm_provider


class ResumeService:
    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """Extracts text from a .pdf or .docx resume file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_lower = file_path.lower()
        if file_lower.endswith(".pdf"):
            text = ""
            try:
                with open(file_path, "rb") as pdf_file:
                    reader = PyPDF2.PdfReader(pdf_file)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                raise ValueError(f"Failed to parse PDF: {str(e)}")
            return text

        elif file_lower.endswith(".docx"):
            try:
                doc = docx.Document(file_path)
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                return "\n".join(paragraphs)
            except Exception as e:
                raise ValueError(f"Failed to parse DOCX: {str(e)}")

        else:
            raise ValueError("Unsupported file format. Only .pdf and .docx are supported.")

    @classmethod
    async def analyze_resume_with_ai(cls, raw_text: str) -> Tuple[ParsedResumeData, str]:
        """
        Analyzes raw resume text using Gemini API.
        Returns a tuple of (ParsedResumeData, parsing_method).
        If AI fails, gracefully falls back to regex-based parsing.
        """
        prompt = f"""
You are an expert HR AI and technical recruiter. Parse the following resume text and extract structured information.
Return strictly a valid JSON object conforming to the schema below, with no markdown code fences or extra text.

Schema:
{{
  "name": "Full name of the candidate or null",
  "email": "Email address or null",
  "phone": "Phone number or null",
  "linkedin": "LinkedIn profile URL or username or null",
  "github": "GitHub profile URL or username or null",
  "education": [
    {{
      "degree": "Degree name",
      "institution": "University/College name",
      "start_date": "Start date or year",
      "end_date": "End date or year",
      "description": "Description or GPA"
    }}
  ],
  "experience": [
    {{
      "role": "Job title",
      "company": "Company name",
      "start_date": "Start date",
      "end_date": "End date",
      "description": "Responsibilities and achievements",
      "technologies": ["Tech1", "Tech2"]
    }}
  ],
  "skills": ["Skill1", "Skill2", "Skill3"],
  "projects": [
    {{
      "title": "Project name",
      "description": "Description of project",
      "technologies": ["Tech1", "Tech2"],
      "link": "URL or null"
    }}
  ],
  "certifications": [
    {{
      "name": "Certification name",
      "issuer": "Issuing organization",
      "date": "Date obtained"
    }}
  ],
  "achievements": [
    {{
      "title": "Achievement or award title",
      "description": "Details"
    }}
  ]
}}

Resume Text:
---
{raw_text[:8000]}
---
"""
        try:
            llm = get_llm_provider()
            response_text = await llm.generate_text(prompt)
            cleaned_text = re.sub(r'```json|```', '', response_text).strip()
            data = json.loads(cleaned_text)
            parsed_data = ParsedResumeData.model_validate(data)
            return parsed_data, "ai"
        except Exception as e:
            print(f"[ResumeService] AI parsing failed ({str(e)}). Falling back to regex parser.")
            fallback_data = cls.fallback_regex_parse(raw_text)
            return fallback_data, "regex_fallback"

    @staticmethod
    def fallback_regex_parse(raw_text: str) -> ParsedResumeData:
        """
        Fallback parser that extracts core fields via regex/keywords if AI fails.
        """
        # Email extraction
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', raw_text)
        email = email_match.group(0) if email_match else None

        # Phone extraction
        phone_match = re.search(r'(\+\d{1,3}[-.\s]??\d{10}|\(\d{3}\)\s*\d{3}[-.\s]??\d{4}|\d{3}[-.\s]??\d{3}[-.\s]??\d{4})', raw_text)
        phone = phone_match.group(0) if phone_match else None

        # LinkedIn extraction
        linkedin_match = re.search(r'(https?://)?(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+', raw_text, re.IGNORECASE)
        linkedin = linkedin_match.group(0) if linkedin_match else None

        # GitHub extraction
        github_match = re.search(r'(https?://)?(www\.)?github\.com/[a-zA-Z0-9_-]+', raw_text, re.IGNORECASE)
        github = github_match.group(0) if github_match else None

        # Skill extraction
        common_skills = [
            "python", "javascript", "react", "node", "fastapi", "sql", "mongodb", "aws",
            "docker", "git", "java", "c++", "c#", "html", "css", "typescript", "angular",
            "vue", "kubernetes", "azure", "gcp", "linux", "django", "flask", "redis"
        ]
        extracted_skills = []
        text_lower = raw_text.lower()
        for skill in common_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                extracted_skills.append(skill.capitalize())

        return ParsedResumeData(
            name=None,
            email=email,
            phone=phone,
            linkedin=linkedin,
            github=github,
            skills=extracted_skills,
            education=[],
            experience=[],
            projects=[],
            certifications=[],
            achievements=[]
        )

    @classmethod
    async def process_resume(cls, user_id: str, file_path: str, db) -> Tuple[ResumeUploadResponse, ResumeRecordInDB]:
        """
        Full pipeline: extract text -> parse with AI -> save to MongoDB -> merge skills.
        """
        raw_text = cls.extract_text_from_file(file_path)
        parsed_data, parsing_method = await cls.analyze_resume_with_ai(raw_text)

        # Merge extracted skills with existing user profile skills
        profile = await db.profiles.find_one({"user_id": user_id})
        if profile:
            existing_skills = profile.get("skills", [])
            updated_skills = list(set(existing_skills + parsed_data.skills))
            await db.profiles.update_one(
                {"user_id": user_id},
                {"$set": {"skills": updated_skills, "updated_at": datetime.utcnow()}}
            )

        # Save structured resume record to database
        record = ResumeRecordInDB(
            user_id=user_id,
            file_url=file_path,
            uploaded_at=datetime.utcnow(),
            parsed_data=parsed_data,
            parsing_method=parsing_method
        )
        record_dict = record.model_dump()
        result = await db.resumes.insert_one(record_dict)
        record.id = str(result.inserted_id)

        response = ResumeUploadResponse(
            message="Resume uploaded and analyzed successfully",
            file_url=file_path,
            extracted_skills=parsed_data.skills,
            parsed_data=parsed_data
        )
        return response, record
