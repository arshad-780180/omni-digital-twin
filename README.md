# OMNI Digital Twin — AI Personal Career Operating System (v1.0 Production Release)

OMNI Digital Twin is an AI-powered Career Operating System designed to aggregate a user's professional footprint—including uploaded resumes, GitHub repositories, developer profiles, target job descriptions, mock interviews, personalized learning plans, and executive analytics—into unified, actionable career intelligence.

---

## 🌟 What's New in Version 1.0 — Analytics & Career Intelligence Dashboard (Production Release)

Version 1.0 introduces the production-ready Analytics & Career Intelligence Dashboard that unifies all 9 OMNI intelligence modules into a single executive command center:
- **Deterministic Overall Career Health Score (`/api/analytics/dashboard`)**: Mathematically aggregates weighted scores from Career Readiness (25%), ATS Optimization (20%), Job Match (20%), Mock Interview Performance (20%), Learning Progress (10%), plus up to 5 points in project/milestone bonuses into a transparent 0-100 Career Health Score with circular status badges (`Excellent`, `Strong`, `Moderate`, `Needs Attention`).
- **AI Executive Career Synthesis Engine**: Synthesizes top demonstrated strengths, weakest areas, biggest improvements, career risks, recommended next actions, and estimated readiness timeframes using Google Gemini AI with 100% deterministic rule-based heuristic fallbacks.
- **11-Skill Engineering Competency Matrix (`/api/analytics/skills`)**: Evaluates `Python`, `FastAPI`, `SQL`, `Docker`, `AWS`, `Git`, `React`, `MongoDB`, `Machine Learning`, `Data Structures`, and `Algorithms` across current levels (`Beginner`, `Intermediate`, `Advanced`, `Expert`), growth trends, and proficiency scores.
- **Chronological Career Evolution Timeline (`/api/analytics/timeline`)**: Interactive chronological progression feed tracking every major event across Profile, Resume, GitHub, Career, ATS, Interview, Job Match, and Learning modules.
- **Downloadable ReportLab PDF Report Export (`/api/analytics/export`)**: Instant professional PDF generation and browser download for `Career Report`, `Analytics Summary`, `Progress Report`, and `Career Timeline`.
- **100% Deterministic Fallback Coverage**: Guarantees complete executive analytics, charts, and downloadable reports even when Gemini AI is offline or unconfigured.

---

## 🏗️ System Architecture

```
+-------------------------------------------------------------------------------------------------------------------------------+
|                                                     React + Vite Frontend                                                     |
+-------------------------------------------------------------------------------------------------------------------------------+
                                                                 ^
                                                                 | REST / JSON (JWT Auth)
                                                                 v
+-------------------------------------------------------------------------------------------------------------------------------+
|                                                      FastAPI API Gateway                                                      |
|                                 (CORS, Global Exception Handlers, Env Validator, UTC Timezones)                               |
+-------------------------------------------------------------------------------------------------------------------------------+
   ^             ^             ^             ^              ^                ^                ^                ^            ^
   |             |             |             |              |                |                |                |            |
   v             v             v             v              v                v                v                v            v
+------+     +-------+     +-------+     +-------+     +---------+      +---------+      +---------+     +----------+  +---------+
|Resume|     |GitHub |     |Career |     |  ATS  |     |   Job   |      | Digital |      |  Mock   |     | Learning |  |Analytics|
|Engine|     |Engine |     |Engine |     |Engine |     |Matching |      |  Twin   |      |Interview|     | Roadmap  |  |Dashboard|
+------+     +-------+     +-------+     +-------+     +---------+      +---------+      +---------+     +----------+  +---------+
   ^             ^             ^             ^              ^                ^                ^                ^            ^
   |             |             |             |              |                |                |                |            |
   +-------------+-------------+-------------+--------------+----------------+----------------+----------------+------------+
                                                            ^
                                                            | Concurrently Aggregates 9 Modules
                                                            v
+-------------------------------------------------------------------------------------------------------------------------------+
|                                  DigitalTwinService (Centralized Aggregation Single Source)                                   |
+-------------------------------------------------------------------------------------------------------------------------------+
                                                            ^
                                                            | Motor AsyncIO
                                                            v
+-------------------------------------------------------------------------------------------------------------------------------+
|                                                  MongoDB Atlas / Local Mongo                                                  |
| (users, profiles, resumes, github_analysis, career_readiness, ats_analysis, job_matches, digital_twin_memory,                 |
|  interview_sessions, learning_roadmaps)                                                                                       |
+-------------------------------------------------------------------------------------------------------------------------------+
```

---

## 🚀 Key Modules & Capabilities

1. **Analytics & Career Intelligence Dashboard (Phase 9 — v1.0 Production Release)**
   - **Unified Executive Dashboard**: Computes Career Health Score, Digital Twin Confidence, and Career Goal Progress.
   - **11-Skill Growth Matrix & Timeline**: Visual matrix and chronological milestone feed across all modules.
   - **ReportLab PDF Export**: One-click download of professional PDF career reports.
2. **AI Personalized Learning Roadmap Engine (Phase 8)**
   - **Continuous AI Career Mentor**: Adapts roadmap phases and milestones based on Resume skills, GitHub code highlights, ATS gaps, and Mock Interview weak topics.
   - **Interactive Milestones**: Check off completed skills and projects to grow career readiness scores and sync with Digital Twin memory.
3. **AI Mock Interview Coach (Phase 7)**
   - **Adaptive Question Generator**: Progressive technical questions referencing actual candidate skills.
   - **Per-Question 6-Dimension Evaluation**: Technical, Communication, Confidence, Problem Solving, Completeness, and Real-World Thinking scores with ideal answers.
4. **Digital Twin Memory Engine (Phase 6)**
   - **Living Persistent Representation**: Continuously merges insights across all modules into `db.digital_twin_memory`.
   - **Career Synthesis & Evolution Timeline**: Records milestone achievements, interview improvements, and project completions chronologically.
5. **AI Job Matching Engine (Phase 5)**
   - **Multi-Factor Fit Evaluation**: Role Fit, Technical Fit, Experience Fit, and Project Fit scoring against target job descriptions.
6. **ATS Resume Optimization Engine (Phase 4)**
   - **ATS Keyword Gap Analysis**: Identifies missing skills and provides actionable resume rewrite recommendations.
7. **AI Career Readiness Engine (Phase 3)**
   - **Readiness Benchmarking**: Synthesizes Resume, GitHub, and Profile data into executive career readiness evaluations.
8. **GitHub Intelligence Engine (Phase 2)**
   - **Repository & Portfolio Analysis**: Analyzes top languages, architecture patterns, clean code practices, and security habits.
9. **Resume Intelligence Engine (Phase 1)**
   - **PDF/DOCX Parsing & Skill Extraction**: Automated resume parsing with structured Pydantic schemas.
10. **Centralized Digital Twin Service (v0.5 Architecture)**
    - **Single Source of Truth**: Concurrently aggregates all 9 modules via `asyncio.gather` without duplicating business logic.

---

## 🛠️ Getting Started

### 1. Requirements
- Python 3.10+
- Node.js 18+
- MongoDB 6.0+

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

Create a `.env` file in `backend/`:
```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=omnimind
# Optional: Get a free key from Google AI Studio
# GEMINI_API_KEY=your_gemini_api_key
# JWT_SECRET_KEY=your_jwt_secret
```

Start FastAPI development server:
```bash
uvicorn main:app --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The frontend will be accessible at `http://localhost:5173`.

---

## 🧪 Testing & Verification

OMNI includes a comprehensive automated unit and end-to-end integration test suite (`106/106` tests passing across all 11 modules with 0 regressions):

```bash
cd backend
.\.venv\Scripts\pytest.exe tests -v
```

### Tested Modules:
- `tests/test_analytics_service.py` (18 tests) — Phase 9 Analytics & Career Intelligence Dashboard (v1.0)
- `tests/test_learning_service.py` (16 tests) — Phase 8 AI Learning Roadmap Engine
- `tests/test_interview_service.py` (13 tests) — Phase 7 AI Mock Interview Intelligence
- `tests/test_digital_twin_memory_service.py` (8 tests) — Phase 6 Digital Twin Memory Engine
- `tests/test_job_matching_service.py` (6 tests) — Phase 5 AI Job Matching Engine
- `tests/test_ats_service.py` (13 tests) — Phase 4 ATS Resume Optimization Engine
- `tests/test_career_service.py` (12 tests) — Phase 3 Career Readiness Engine
- `tests/test_github_service.py` (7 tests) — Phase 2 GitHub Intelligence Engine
- `tests/test_resume_service.py` (7 tests) — Phase 1 Resume Intelligence Engine
- `tests/test_digital_twin_service.py` (2 tests) — Centralized Aggregation Layer
- `tests/test_e2e_integration.py` (4 tests) — Full End-to-End Pipeline Integration
