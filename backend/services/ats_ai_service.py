import json
import re
from typing import Dict, Any, List, Optional, Tuple

from ai.llm_provider import get_llm_provider
from models.ats import ATSFeedback, ATSSuggestions
from utils.logger import get_logger

logger = get_logger("ats")


class ATSAIService:
    @staticmethod
    def extract_keywords(job_description: str) -> List[str]:
        """
        Extracts technical keywords, frameworks, tools, and methodologies from a job description.
        """
        tech_vocabulary = {
            "python", "javascript", "typescript", "react", "node", "node.js", "express",
            "fastapi", "django", "flask", "java", "spring", "spring boot", "c++", "c#", ".net",
            "ruby", "rails", "go", "golang", "rust", "php", "laravel", "swift", "kotlin",
            "sql", "mysql", "postgresql", "mongodb", "nosql", "redis", "elasticsearch", "cassandra",
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd", "jenkins",
            "git", "github", "gitlab", "linux", "unix", "html", "css", "tailwind", "sass",
            "machine learning", "ai", "deep learning", "data science", "pandas", "numpy",
            "tensorflow", "pytorch", "scikit-learn", "nlp", "llm", "generative ai",
            "agile", "scrum", "kanban", "rest", "restful", "graphql", "grpc", "microservices",
            "system design", "data structures", "algorithms", "unit testing", "pytest", "jest"
        }

        jd_lower = job_description.lower()
        found_keywords = set()

        for term in tech_vocabulary:
            # Check for exact word or phrase boundary match
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, jd_lower):
                found_keywords.add(term)

        # Also extract any capitalized technical terms or tokens
        tokens = set(re.findall(r'\b[A-Za-z\.\-\+#]{3,}\b', jd_lower))
        for t in tokens:
            if t in tech_vocabulary:
                found_keywords.add(t)

        if not found_keywords:
            found_keywords = {"communication", "problem solving", "teamwork", "software development"}

        return sorted(list(found_keywords))

    @staticmethod
    def compute_keyword_match(
        required_keywords: List[str],
        user_skills: List[str]
    ) -> Tuple[List[str], List[str], int]:
        """
        Compares required keywords against user skills and returns matched, missing, and match percentage.
        """
        user_skills_lower = [s.lower() for s in user_skills]
        matched = []
        missing = []

        for req in required_keywords:
            req_lower = req.lower()
            found = False
            for user_sk in user_skills_lower:
                if req_lower in user_sk or user_sk in req_lower:
                    found = True
                    break

            # Format keyword nicely
            clean_term = req.title()
            if req_lower in ["javascript", "typescript"]:
                clean_term = clean_term.replace("script", "Script")
            elif req_lower in ["node.js", "react", "html", "css", "sql", "aws", "gcp", "ai", "ci/cd", "nlp", "llm"]:
                clean_term = req_lower.upper()

            if found:
                matched.append(clean_term)
            else:
                missing.append(clean_term)

        total = len(required_keywords)
        score = int((len(matched) / total) * 100) if total > 0 else 70
        return matched, missing, score

    @classmethod
    async def optimize_resume(
        cls,
        resume_doc: Optional[Dict[str, Any]],
        profile_doc: Optional[Dict[str, Any]],
        job_title: str,
        company: str,
        job_description: str
    ) -> Tuple[int, List[str], List[str], List[str], ATSFeedback, ATSSuggestions, str]:
        """
        Analyzes the resume against the job description using Gemini AI.
        Returns:
          (ats_score, required_keywords, matched_keywords, missing_keywords, feedback, suggestions, method)
        """
        # Gather candidate skills
        user_skills = []
        resume_text_summary = ""
        resume_projects = []
        resume_experience = []

        if resume_doc and "parsed_data" in resume_doc:
            pdata = resume_doc["parsed_data"]
            user_skills.extend(pdata.get("skills", []))
            resume_text_summary = pdata.get("summary", "") or pdata.get("objective", "")
            resume_projects = pdata.get("projects", [])
            resume_experience = pdata.get("experience", [])
            if isinstance(resume_projects, list):
                resume_projects = [str(p) for p in resume_projects]
            if isinstance(resume_experience, list):
                resume_experience = [str(e) for e in resume_experience]

        if profile_doc and "skills" in profile_doc:
            user_skills.extend(profile_doc.get("skills", []))

        user_skills = sorted(list(set(user_skills)))
        required_keywords = cls.extract_keywords(job_description)
        matched_keywords, missing_keywords, base_overlap_score = cls.compute_keyword_match(
            required_keywords,
            user_skills
        )

        # Build prompt for Gemini AI
        prompt = f"""
        You are an expert AI ATS (Applicant Tracking System) Resume Optimization Engine.
        Analyze the candidate's resume and skills against the target Job Description and return a structured JSON response.

        TARGET JOB:
        Title: {job_title}
        Company: {company or 'Unspecified'}
        Description:
        {job_description}

        CANDIDATE RESUME PROFILE:
        Skills: {', '.join(user_skills)}
        Summary: {resume_text_summary}
        Experience: {'; '.join(resume_experience)}
        Projects: {'; '.join(resume_projects)}

        KEYWORD OVERLAP:
        Matched Keywords: {', '.join(matched_keywords)}
        Missing Keywords: {', '.join(missing_keywords)}
        Base Keyword Overlap Percentage: {base_overlap_score}%

        Your task:
        1. Evaluate an ATS match score (0 to 100) combining keyword overlap, skill relevance, and experience alignment.
        2. Provide concrete resume feedback: strengths, weaknesses, recommendations, and section-by-section feedback.
        3. Provide actionable AI resume improvement suggestions: an improved professional summary tailored to this job, improved project bullet points, grammar feedback, keyword injection advice, and strong action verbs.

        Return ONLY valid JSON matching exactly this schema:
        {{
          "ats_score": <int 0-100>,
          "matched_keywords": {json.dumps(matched_keywords)},
          "missing_keywords": {json.dumps(missing_keywords)},
          "strengths": ["string", "string"],
          "weaknesses": ["string", "string"],
          "recommendations": ["string", "string"],
          "section_feedback": {{
            "Summary": "string",
            "Experience": "string",
            "Skills": "string",
            "Projects": "string"
          }},
          "improved_summary": "string",
          "improved_projects": ["string", "string"],
          "grammar_feedback": ["string", "string"],
          "keyword_injection": ["string", "string"],
          "action_verbs": ["string", "string"]
        }}
        """

        try:
            llm = get_llm_provider()
            raw_response = await llm.generate_text(prompt)

            # Clean JSON markdown fences if present
            clean_json = raw_response.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.startswith("```"):
                clean_json = clean_json[3:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
            clean_json = clean_json.strip()

            data = json.loads(clean_json)

            ats_score = int(data.get("ats_score", base_overlap_score))
            ats_score = max(0, min(100, ats_score))

            feedback = ATSFeedback(
                strengths=data.get("strengths", ["Relevant technical skills match job description keywords."]),
                weaknesses=data.get("weaknesses", [] if ats_score >= 80 else ["Some core target keywords are missing."]),
                recommendations=data.get("recommendations", ["Include missing keywords in project descriptions."]),
                section_feedback=data.get("section_feedback", {
                    "Summary": "Ensure target role keywords appear in the opening summary.",
                    "Skills": "Group technical skills clearly by domain.",
                    "Projects": "Highlight quantifiable achievements and metrics."
                })
            )

            suggestions = ATSSuggestions(
                improved_summary=data.get("improved_summary", f"Results-driven {job_title} with expertise in {', '.join(matched_keywords[:4])}."),
                improved_projects=data.get("improved_projects", [
                    f"Architected backend microservices utilizing {matched_keywords[0] if matched_keywords else 'modern frameworks'}, improving query response times by 35%."
                ]),
                grammar_feedback=data.get("grammar_feedback", ["Use active voice and past tense for completed achievements."]),
                keyword_injection=data.get("keyword_injection", [
                    f"Incorporate '{kw}' into your Skills or Experience bullets." for kw in missing_keywords[:3]
                ]),
                action_verbs=data.get("action_verbs", ["Architected", "Engineered", "Optimized", "Spearheaded", "Implemented"])
            )

            return (
                ats_score,
                [kw.title() for kw in required_keywords],
                matched_keywords,
                missing_keywords,
                feedback,
                suggestions,
                "ai"
            )

        except Exception as e:
            logger.warning(f"Gemini AI failed ({str(e)}), using deterministic rule-based fallback.")
            return cls.fallback_rule_based_ats(
                base_overlap_score,
                required_keywords,
                matched_keywords,
                missing_keywords,
                job_title
            )

    @classmethod
    def fallback_rule_based_optimization(
        cls,
        resume_doc: Optional[Dict[str, Any]],
        profile_doc: Optional[Dict[str, Any]],
        job_title: str,
        company: str,
        job_description: str
    ) -> Tuple[int, List[str], List[str], List[str], ATSFeedback, ATSSuggestions, str]:
        required_keywords = cls.extract_keywords(job_description)
        
        user_skills: List[str] = []
        if resume_doc and "parsed_data" in resume_doc and "skills" in resume_doc["parsed_data"]:
            user_skills.extend(resume_doc["parsed_data"]["skills"])
        if profile_doc and "skills" in profile_doc:
            user_skills.extend(profile_doc["skills"])
        user_skills = list(set(user_skills))

        matched_keywords, missing_keywords, base_overlap_score = cls.compute_keyword_match(
            required_keywords, user_skills
        )
        return cls.fallback_rule_based_ats(
            base_overlap_score,
            required_keywords,
            matched_keywords,
            missing_keywords,
            job_title
        )

    @staticmethod
    def fallback_rule_based_ats(
        base_overlap_score: int,
        required_keywords: List[str],
        matched_keywords: List[str],
        missing_keywords: List[str],
        job_title: str
    ) -> Tuple[int, List[str], List[str], List[str], ATSFeedback, ATSSuggestions, str]:
        """
        Deterministic rule-based fallback when Gemini API fails or rate limits.
        """
        ats_score = max(10, min(95, base_overlap_score))

        strengths = []
        if matched_keywords:
            strengths.append(f"Strong alignment in core technologies: {', '.join(matched_keywords[:4])}.")
        else:
            strengths.append("Candidate demonstrates general software engineering capabilities.")

        weaknesses = []
        if missing_keywords:
            weaknesses.append(f"Resume is missing high-priority ATS keywords: {', '.join(missing_keywords[:4])}.")
        else:
            weaknesses.append("Resume could benefit from more quantifiable project metrics.")

        recommendations = [
            f"Embed missing keywords ({', '.join(missing_keywords[:3])}) within your Experience and Project bullet points." if missing_keywords else "Ensure formatting is clean and ATS-friendly.",
            "Use strong action verbs and quantify achievements with percentages or latency metrics."
        ]

        section_feedback = {
            "Summary": f"Tailor your opening summary explicitly to the {job_title} position.",
            "Experience": "Quantify results (e.g., 'Reduced API latency by 40%').",
            "Skills": "Organize keywords by domain (Languages, Frameworks, Cloud, Databases).",
            "Projects": "Explicitly mention technologies used in each project title or subtitle."
        }

        feedback = ATSFeedback(
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            section_feedback=section_feedback
        )

        improved_summary = (
            f"Results-oriented {job_title} with demonstrated expertise in "
            f"{', '.join(matched_keywords[:4]) if matched_keywords else 'modern software engineering'}. "
            f"Adept at building scalable systems and delivering high-performance solutions."
        )

        improved_projects = [
            f"Engineered scalable backend service utilizing {matched_keywords[0] if matched_keywords else 'core frameworks'}, reducing response latency by 35%.",
            f"Implemented automated testing and deployment pipeline, increasing code coverage to 90%."
        ]

        grammar_feedback = [
            "Ensure all bullet points begin with a strong past-tense action verb.",
            "Avoid personal pronouns ('I', 'me', 'my') in ATS resumes."
        ]

        keyword_injection = [
            f"Add '{kw}' to your technical skills section or project highlights." for kw in missing_keywords[:4]
        ]

        action_verbs = ["Architected", "Engineered", "Spearheaded", "Optimized", "Automated", "Implemented"]

        suggestions = ATSSuggestions(
            improved_summary=improved_summary,
            improved_projects=improved_projects,
            grammar_feedback=grammar_feedback,
            keyword_injection=keyword_injection,
            action_verbs=action_verbs
        )

        return (
            ats_score,
            [kw.title() for kw in required_keywords],
            matched_keywords,
            missing_keywords,
            feedback,
            suggestions,
            "rule_based"
        )
