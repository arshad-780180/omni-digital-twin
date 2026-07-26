# Phase 1: AI Resume Intelligence Engine

## Overview
The AI Resume Intelligence Engine replaces legacy regular-expression and keyword-matching resume parsing with a structured, LLM-powered extraction pipeline using Google Gemini (`gemini-1.5-flash`). It supports both **PDF** and **DOCX** files, validates parsed output against strict Pydantic schemas, saves structured records to MongoDB while preserving original uploaded documents, and provides a resilient regular-expression fallback parser if LLM generation encounters network timeouts or quota limits.

---

## Architecture & Workflow

```mermaid
graph TD
    A[Client Upload (.pdf or .docx)] --> B[POST /api/profile/resume]
    B --> C[ResumeService.process_resume]
    C --> D{File Extension?}
    D -->|.pdf| E[PyPDF2 / pdfplumber Text Extraction]
    D -->|.docx| F[python-docx Text Extraction]
    E --> G[AI Parsing: Gemini API]
    F --> G
    G --> H{Valid JSON & Schema?}
    H -->|Yes| I[ParsedResumeData (AI)]
    H -->|No / Error| J[Fallback Regex Parser]
    J --> K[ParsedResumeData (Regex Fallback)]
    I --> L[Save Original File to /uploads]
    K --> L
    L --> M[Insert Record into db.resumes]
    M --> N[Merge Skills into db.profiles]
    N --> O[Return Backward-Compatible Response + parsed_data]
```

---

## Supported File Formats
1. **PDF (`.pdf`)**: Parsed using `PyPDF2` (page-by-page text extraction).
2. **Word (`.docx`)**: Parsed using `python-docx` (paragraph text extraction).

---

## Extracted Fields (`ParsedResumeData`)
The engine extracts the following 11 structured fields:
1. **`name`** (`str` | null): Full name of the candidate.
2. **`email`** (`str` | null): Primary email address.
3. **`phone`** (`str` | null): Primary phone number.
4. **`linkedin`** (`str` | null): LinkedIn profile URL or username.
5. **`github`** (`str` | null): GitHub profile URL or username.
6. **`education`** (`List[EducationItem]`): Degree, institution, start date, end date, and description.
7. **`experience`** (`List[ExperienceItem]`): Job title, company name, start date, end date, description, and list of technologies used.
8. **`skills`** (`List[str]`): Professional skills and tools.
9. **`projects`** (`List[ProjectItem]`): Project title, description, technologies, and repository/demo link.
10. **`certifications`** (`List[CertificationItem]`): Certification name, issuing body, and date obtained.
11. **`achievements`** (`List[AchievementItem]`): Notable awards or achievements.

---

## Database Schema & MongoDB Integration
- **`db.resumes`**: Stores each uploaded resume record:
  ```json
  {
    "_id": "64d...",
    "user_id": "user_id_string",
    "file_url": "uploads/user_id_resume.pdf",
    "uploaded_at": "2026-07-27T00:00:00Z",
    "parsed_data": {
      "name": "Alice Smith",
      "email": "alice@example.com",
      "skills": ["Python", "FastAPI", "MongoDB"],
      ...
    },
    "parsing_method": "ai"  // or "regex_fallback"
  }
  ```
- **`db.profiles`**: Automatically merges new skills extracted from the resume into the user's main profile `skills` array.

---

## API Endpoints
### `POST /api/profile/resume`
- **Request Body**: `multipart/form-data` containing `file` (`.pdf` or `.docx`).
- **Response**:
  ```json
  {
    "message": "Resume uploaded and analyzed successfully",
    "file_url": "uploads/user123_resume.pdf",
    "extracted_skills": ["Python", "FastAPI", "MongoDB"],
    "parsed_data": { ... }
  }
  ```
- **Backward Compatibility**: Ensures existing frontend UI components reading `extracted_skills` continue to function without modification.

### `GET /api/profile/resume/latest`
- **Response**: Returns the most recent `ResumeRecordInDB` record for the authenticated user from `db.resumes`, including full structured `parsed_data`.
