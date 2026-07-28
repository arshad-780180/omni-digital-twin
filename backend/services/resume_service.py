import os
import re
import json
from datetime import datetime, timezone
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
    AchievementItem
)
from ai.llm_provider import get_llm_provider
from services.digital_twin_memory_service import DigitalTwinMemoryService
from utils.logger import get_logger

logger = get_logger("resume")


class ResumeService:
    @staticmethod
    def extract_text_pdf(file_path: str) -> str:
        text = ""
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    content = page.extract_text()
                    if content:
                        text += content + "\n"
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {str(e)}")
        return text

    @staticmethod
    def extract_text_docx(file_path: str) -> str:
        text = ""
        try:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                if para.text:
                    text += para.text + "\n"
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {str(e)}")
        return text

    @classmethod
    def extract_text_from_file(cls, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return cls.extract_text_pdf(file_path)
        elif ext in [".doc", ".docx"]:
            return cls.extract_text_docx(file_path)
        raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def fallback_regex_parse(text: str) -> ParsedResumeData:
        data = ParsedResumeData()

        # Basic Email Regex
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        if email_match:
            data.email = email_match.group(0)

        # Basic Phone Regex
        phone_match = re.search(r"(\+?\d{1,3}[-.\s]??\d{3}[-.\s]??\d{3}[-.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-.\s]??\d{4}|\d{10})", text)
        if phone_match:
            data.phone = phone_match.group(0)

        # LinkedIn Regex
        linkedin_match = re.search(r"linkedin\.com/in/[a-zA-Z0-9_-]+", text, re.IGNORECASE)
        if linkedin_match:
            data.linkedin = "https://" + linkedin_match.group(0)

        # GitHub Regex
        github_match = re.search(r"github\.com/[a-zA-Z0-9_-]+", text, re.IGNORECASE)
        if github_match:
            data.github = "https://" + github_match.group(0)

        # Extract Name (Heuristic: First non-empty line with <= 4 words)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:5]:
            if len(line.split()) <= 4 and not any(char.isdigit() for char in line):
                data.name = line
                break

        # Fallback keyword skills matching
        tech_keywords = [
            "python", "javascript", "typescript", "react", "node", "express", "mongodb",
            "sql", "postgresql", "fastapi", "django", "docker", "kubernetes", "aws",
            "git", "html", "css", "tailwind", "java", "c++", "c#", "go", "rust",
            "machine learning", "data science", "ai", "redux", "graphql", "rest api"
        ]
        found_skills = set()
        lower_text = text.lower()
        for kw in tech_keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", lower_text):
                found_skills.add(kw.capitalize())

        if found_skills:
            data.skills = sorted(list(found_skills))

        # Capture basic summary if available
        for i, line in enumerate(lines):
            if "summary" in line.lower() or "objective" in line.lower():
                if i + 1 < len(lines):
                    data.summary = lines[i + 1]
                break

        return data

    @classmethod
    async def analyze_resume_with_ai(cls, text: str) -> Tuple[ParsedResumeData, str]:
        prompt = f"""
You are an expert AI resume parser. Extract structured data from the following resume text and return ONLY a valid JSON object matching this schema:
{{
  "name": str or null,
  "email": str or null,
  "phone": str or null,
  "linkedin": str or null,
  "github": str or null,
  "education": list,
  "experience": list,
  "skills": list of str,
  "projects": list,
  "certifications": list,
  "achievements": list
}}

Resume Text:
---
{text[:8000]}
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
            logger.warning(f"AI parsing failed ({str(e)}), falling back to regex: {str(e)}")
            # include full exception details in logs for debugging
            logger.exception("AI parser exception")
            fallback_data = cls.fallback_regex_parse(text)
            return fallback_data, "regex_fallback"

    @classmethod
    async def process_resume(
        cls,
        user_id: str,
        file_path: str,
        db
    ) -> Tuple[ResumeUploadResponse, ResumeRecordInDB]:
        logger.info("Starting resume processing")
        raw_text = cls.extract_text_from_file(file_path)
        logger.info("Text extraction completed")
        logger.info(f"Extracted {len(raw_text)} characters")
        if not raw_text.strip():
            logger.warning(f"Extracted empty text from {file_path}")

        parsed_data, parsing_method = await cls.analyze_resume_with_ai(raw_text)
        logger.info("Resume parsing completed")
        logger.info(f"Parsing method: {parsing_method}")

        # Merge extracted skills with existing user profile skills
        logger.info("Loading user profile")
        profile = await db.profiles.find_one({"user_id": user_id})
        if profile:
            logger.info("Updating skills")
            existing_skills = profile.get("skills", []) or []
            # ensure parsed_data.skills is a list
            parsed_skills = parsed_data.skills or []
            updated_skills = list(set(existing_skills + parsed_skills))
            await db.profiles.update_one(
                {"user_id": user_id},
                {"$set": {"skills": updated_skills, "updated_at": datetime.now(timezone.utc)}}
            )

        # Save structured resume record to database
        logger.info("Creating ResumeRecordInDB")
        record = ResumeRecordInDB(
            user_id=user_id,
            file_url=file_path,
            uploaded_at=datetime.now(timezone.utc),
            parsed_data=parsed_data,
            parsing_method=parsing_method
        )
        record_dict = record.model_dump()

        logger.info("Inserting resume into MongoDB")
        try:
            result = await db.resumes.insert_one(record_dict)
        except Exception as e:
            logger.exception("Failed to insert resume into MongoDB")
            raise

        record_dict["id"] = str(result.inserted_id)

        logger.info("Updating Digital Twin memory")
        try:
            await DigitalTwinMemoryService.update_memory(user_id, "resume", record_dict, db)
        except Exception:
            logger.exception("Memory update failed")

        logger.info("Returning response")
        resp = ResumeUploadResponse(
            message="Resume uploaded and analyzed successfully",
            file_url=file_path,
            extracted_skills=parsed_data.skills or [],
            parsed_data=parsed_data,
            generated_by=parsing_method
        )
        return resp, ResumeRecordInDB(**record_dict)
