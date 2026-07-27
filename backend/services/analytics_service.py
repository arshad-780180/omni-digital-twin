import asyncio
import inspect
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import io

from motor.motor_asyncio import AsyncIOMotorDatabase
from models.analytics import (
    CareerHealthScore,
    CareerAnalytics,
    ATSAnalytics,
    JobMatchAnalytics,
    InterviewAnalytics,
    LearningAnalyticsSummary,
    DigitalTwinAnalytics,
    SkillAnalytics,
    TimelineEvent,
    ExecutiveInsights,
    DashboardSummary,
)
from services.digital_twin_service import DigitalTwinService
from services.analytics_ai_service import AnalyticsAIService

logger = logging.getLogger("omni.analytics.service")

# Required Skill Matrix core list
REQUIRED_SKILLS = [
    "Python",
    "FastAPI",
    "SQL",
    "Docker",
    "AWS",
    "Git",
    "React",
    "MongoDB",
    "Machine Learning",
    "Data Structures",
    "Algorithms",
]


class AnalyticsService:
    """
    Core business service for Phase 9 Analytics & Career Intelligence Dashboard (v1.0).
    Aggregates multi-source insights from DigitalTwinService without duplicating queries or logic.
    Implements deterministic Career Health Score algorithm and chronological timeline progression.
    """

    @staticmethod
    async def _safe_find_history(
        collection, user_id: str, limit: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Safely retrieves up to `limit` historical documents sorted chronologically (ascending).
        """
        try:
            cursor = collection.find({"user_id": user_id}).sort("created_at", 1).limit(limit)
            res = cursor.to_list(length=limit)
            if inspect.isawaitable(res):
                items = await res
            else:
                items = res
            return [i for i in (items or []) if isinstance(i, dict)]
        except Exception:
            return []

    @classmethod
    async def get_career_analytics(
        cls, user_id: str, db: AsyncIOMotorDatabase
    ) -> CareerAnalytics:
        history = await cls._safe_find_history(db.career_analysis, user_id, limit=6)
        scores = []
        labels = []
        for doc in history:
            score = doc.get("overall_readiness_score", 0)
            scores.append(int(score))
            created_at = doc.get("created_at")
            if isinstance(created_at, datetime):
                labels.append(created_at.strftime("%b %d"))
            else:
                labels.append("Audit")

        current_score = scores[-1] if scores else 70
        prev_score = scores[-2] if len(scores) >= 2 else current_score
        monthly_improvement = float(current_score - prev_score)

        return CareerAnalytics(
            current_score=current_score,
            historical_trend=scores or [current_score],
            monthly_improvement=monthly_improvement,
            target_score=90,
            estimated_goal_date="Within 6 weeks" if current_score >= 75 else "Within 8 weeks",
            history_labels=labels or ["Latest"],
        )

    @classmethod
    async def get_ats_analytics(
        cls, user_id: str, db: AsyncIOMotorDatabase
    ) -> ATSAnalytics:
        history = await cls._safe_find_history(db.ats_analysis, user_id, limit=6)
        scores = []
        timeline = []
        all_missing = []
        total_matched_count = 0
        total_keywords_count = 0

        for doc in history:
            score = doc.get("ats_match_percentage") or doc.get("match_score") or 0
            scores.append(int(score))
            created_at = doc.get("created_at")
            if isinstance(created_at, datetime):
                timeline.append(f"{created_at.strftime('%b %d')}: {score}% match")
            else:
                timeline.append(f"Audit: {score}% match")

            matched = doc.get("matched_keywords", [])
            missing = doc.get("missing_keywords", [])
            total_matched_count += len(matched)
            total_keywords_count += len(matched) + len(missing)
            for m in missing:
                if isinstance(m, str) and m.strip():
                    all_missing.append(m.strip())

        latest_score = scores[-1] if scores else 65
        avg_score = float(sum(scores) / len(scores)) if scores else 65.0
        keyword_coverage = (
            round((total_matched_count / total_keywords_count) * 100.0, 1)
            if total_keywords_count > 0
            else 68.5
        )

        # Deduplicate top missing skills
        unique_missing = []
        for s in all_missing:
            if s not in unique_missing:
                unique_missing.append(s)

        return ATSAnalytics(
            latest_score=latest_score,
            average_score=round(avg_score, 1),
            historical_trend=scores or [latest_score],
            keyword_coverage=keyword_coverage,
            top_missing_skills=unique_missing[:5] or ["Kubernetes", "System Design", "Cloud Infrastructure"],
            improvement_timeline=timeline or ["Initial Check: 65% match"],
        )

    @classmethod
    async def get_job_match_analytics(
        cls, user_id: str, db: AsyncIOMotorDatabase
    ) -> JobMatchAnalytics:
        history = await cls._safe_find_history(db.job_matches, user_id, limit=6)
        scores = []
        recs = []
        gaps_count = []
        best_role = "Senior Backend Engineer"
        alt_roles = ["Full Stack Engineer", "Cloud Systems Architect", "Technical Lead"]

        for doc in history:
            score = (
                doc.get("fit_score")
                or doc.get("overall_match_score")
                or doc.get("overall_fit_score")
                or 0
            )
            scores.append(int(score))
            role = doc.get("role_title") or doc.get("job_title")
            if role and isinstance(role, str):
                best_role = role
            # Determine recommendation
            if score >= 80:
                recs.append("Strong Hire")
            elif score >= 65:
                recs.append("Hire")
            else:
                recs.append("Consider")

            missing = doc.get("missing_skills", [])
            gaps_count.append(len(missing) if isinstance(missing, list) else 3)

        latest_score = scores[-1] if scores else 72
        avg_score = float(sum(scores) / len(scores)) if scores else 72.0

        return JobMatchAnalytics(
            latest_match_score=latest_score,
            average_match_score=round(avg_score, 1),
            best_matching_role=best_role,
            alternative_roles=alt_roles,
            hiring_recommendation_trend=recs or ["Hire"],
            skill_gap_evolution=gaps_count or [4, 3, 2],
        )

    @classmethod
    async def get_interview_analytics(
        cls, user_id: str, db: AsyncIOMotorDatabase
    ) -> InterviewAnalytics:
        history = await cls._safe_find_history(db.interview_sessions, user_id, limit=6)
        tech_trend = []
        comm_trend = []
        conf_trend = []
        prob_trend = []
        overall_scores = []
        success_count = 0

        for doc in history:
            ov = doc.get("overall_score", 0)
            tech = doc.get("technical_score", ov)
            comm = doc.get("communication_score", ov)
            conf = doc.get("confidence_score", ov)
            prob = doc.get("problem_solving_score", ov)

            overall_scores.append(int(ov))
            tech_trend.append(int(tech))
            comm_trend.append(int(comm))
            conf_trend.append(int(conf))
            prob_trend.append(int(prob))
            if ov >= 70:
                success_count += 1

        avg_score = (
            float(sum(overall_scores) / len(overall_scores)) if overall_scores else 75.0
        )
        success_rate = (
            round((success_count / len(overall_scores)) * 100.0, 1)
            if overall_scores
            else 85.0
        )

        return InterviewAnalytics(
            technical_score_trend=tech_trend or [75],
            communication_trend=comm_trend or [80],
            confidence_trend=conf_trend or [78],
            problem_solving_trend=prob_trend or [72],
            average_interview_score=round(avg_score, 1),
            most_improved_topic="Backend APIs & System Scaling",
            weakest_topic="Distributed Consensus & Caching",
            interview_success_rate=success_rate,
        )

    @classmethod
    async def get_learning_analytics(
        cls, user_id: str, db: AsyncIOMotorDatabase
    ) -> LearningAnalyticsSummary:
        history = await cls._safe_find_history(db.learning_roadmaps, user_id, limit=4)
        latest = history[-1] if history else {}

        prog = float(latest.get("progress_percentage", 0.0))
        completed_milestones = len(latest.get("completed_items", []))
        if not completed_milestones and prog > 0:
            completed_milestones = max(1, int(prog / 10.0))

        # Check projects/certs
        completed_projects = max(0, int(completed_milestones / 3))
        completed_certs = max(0, int(completed_milestones / 6))
        velocity = round(max(0.5, float(completed_milestones) / 2.0), 1)

        return LearningAnalyticsSummary(
            learning_progress=prog,
            completed_milestones=completed_milestones,
            completed_projects=completed_projects,
            completed_certifications=completed_certs,
            learning_velocity=velocity,
            weekly_streak=3,
            estimated_completion=latest.get("estimated_completion", "8 weeks"),
            roadmap_progress=prog,
        )

    @classmethod
    async def get_digital_twin_analytics(
        cls, user_id: str, context: Dict[str, Any]
    ) -> DigitalTwinAnalytics:
        mem = context.get("memory") or {}
        prof = context.get("profile") or {}

        core_skills = mem.get("core_skills") or prof.get("skills") or ["Python", "FastAPI", "SQL", "Git"]
        emerging_skills = mem.get("emerging_skills") or ["Docker", "AWS", "MongoDB"]
        missing_skills = mem.get("missing_skills") or ["Kubernetes", "GraphQL", "Apache Kafka"]

        timeline_entries = []
        for t in mem.get("timeline", []):
            if isinstance(t, dict):
                title = t.get("event") or t.get("title") or "Memory Event"
                timeline_entries.append(str(title))
            elif isinstance(t, str):
                timeline_entries.append(t)

        if not timeline_entries:
            timeline_entries = [
                "Digital Twin Memory Initialized",
                "Skills Merged from Resume & GitHub",
                "Competency Growth Registered",
            ]

        return DigitalTwinAnalytics(
            core_skills=core_skills,
            emerging_skills=emerging_skills,
            missing_skills=missing_skills,
            career_evolution_timeline=timeline_entries,
            strength_growth=len(core_skills),
            weakness_reduction=max(1, len(emerging_skills)),
            memory_timeline=timeline_entries,
        )

    @classmethod
    async def get_skill_matrix(
        cls, user_id: str, context: Dict[str, Any]
    ) -> List[SkillAnalytics]:
        """
        Creates a visual matrix showing Python, FastAPI, SQL, Docker, AWS, Git, React,
        MongoDB, Machine Learning, Data Structures, Algorithms and evaluates their level, trend, and target.
        """
        prof = context.get("profile") or {}
        res = context.get("resume") or {}
        gh = context.get("github_analysis") or {}
        mem = context.get("memory") or {}

        # Collect all user demonstrated skills in lowercase
        demo_skills = set()
        for s in prof.get("skills", []):
            if isinstance(s, str):
                demo_skills.add(s.lower().strip())
        for l in gh.get("top_languages", []):
            if isinstance(l, str):
                demo_skills.add(l.lower().strip())
        for s in mem.get("core_skills", []):
            if isinstance(s, str):
                demo_skills.add(s.lower().strip())

        emerging_skills = set(
            s.lower().strip()
            for s in mem.get("emerging_skills", [])
            if isinstance(s, str)
        )
        missing_skills = set(
            s.lower().strip() for s in mem.get("missing_skills", []) if isinstance(s, str)
        )

        matrix = []
        for skill_name in REQUIRED_SKILLS:
            lower_name = skill_name.lower()
            if lower_name in demo_skills:
                level = "Advanced"
                trend = "Accelerating"
                target = "Expert"
                score = 85
            elif lower_name in emerging_skills:
                level = "Intermediate"
                trend = "Upward"
                target = "Advanced"
                score = 70
            elif lower_name in missing_skills:
                level = "Beginner"
                trend = "Developing"
                target = "Intermediate"
                score = 45
            else:
                # Deterministic baseline heuristic
                if skill_name in ["Python", "SQL", "Git", "Data Structures"]:
                    level = "Advanced"
                    trend = "Stable"
                    target = "Expert"
                    score = 80
                elif skill_name in ["FastAPI", "Docker", "React", "MongoDB"]:
                    level = "Intermediate"
                    trend = "Upward"
                    target = "Advanced"
                    score = 72
                else:
                    level = "Beginner"
                    trend = "Developing"
                    target = "Advanced"
                    score = 55

            matrix.append(
                SkillAnalytics(
                    skill_name=skill_name,
                    current_level=level,
                    growth_trend=trend,
                    target_level=target,
                    score=score,
                )
            )

        return matrix

    @classmethod
    async def get_timeline(
        cls, user_id: str, context: Dict[str, Any]
    ) -> List[TimelineEvent]:
        """
        Generates a chronological progression timeline across all OMNI modules:
        Resume Uploaded -> GitHub Connected -> Career Analysis -> ATS Improved ->
        Interview Completed -> Learning Milestone -> Job Match Improved -> Career Health Increased.
        """
        events = []

        # 1. Profile
        prof = context.get("profile")
        if prof:
            events.append(
                TimelineEvent(
                    event_id="evt_profile",
                    event_type="User Profile Created",
                    title="Profile Initialized",
                    description=f"Target role configured: {prof.get('target_role', 'Engineer')}",
                    timestamp=prof.get("created_at") or datetime.now(timezone.utc),
                    module_source="profile",
                    impact_score=10,
                )
            )

        # 2. Resume
        res = context.get("resume")
        if res:
            events.append(
                TimelineEvent(
                    event_id="evt_resume",
                    event_type="Resume Uploaded",
                    title="Resume Initialized & Parsed",
                    description=f"Uploaded document '{res.get('file_name', 'resume.pdf')}' successfully parsed.",
                    timestamp=res.get("created_at") or datetime.now(timezone.utc),
                    module_source="resume",
                    impact_score=15,
                )
            )

        # 3. GitHub
        gh = context.get("github_analysis")
        if gh:
            events.append(
                TimelineEvent(
                    event_id="evt_github",
                    event_type="GitHub Connected",
                    title="GitHub Portfolio Synchronized",
                    description=f"Analyzed repository footprint for '{gh.get('username', 'developer')}'.",
                    timestamp=gh.get("created_at") or datetime.now(timezone.utc),
                    module_source="github",
                    impact_score=15,
                )
            )

        # 4. Career
        car = context.get("career_analysis")
        if car:
            events.append(
                TimelineEvent(
                    event_id="evt_career",
                    event_type="Career Analysis",
                    title="AI Career Readiness Evaluation",
                    description=f"Overall readiness score: {car.get('overall_readiness_score', 75)}/100.",
                    timestamp=car.get("created_at") or datetime.now(timezone.utc),
                    module_source="career",
                    impact_score=15,
                )
            )

        # 5. ATS
        ats = context.get("ats_analysis")
        if ats:
            score = ats.get("ats_match_percentage", 70)
            events.append(
                TimelineEvent(
                    event_id="evt_ats",
                    event_type="ATS Improved",
                    title="ATS Resume Optimization Audit",
                    description=f"Keyword match percentage achieved: {score}%.",
                    timestamp=ats.get("created_at") or datetime.now(timezone.utc),
                    module_source="ats",
                    impact_score=10,
                )
            )

        # 6. Job Match
        job = context.get("job_matching")
        if job:
            events.append(
                TimelineEvent(
                    event_id="evt_job",
                    event_type="Job Match Improved",
                    title="Opportunity Fit Evaluated",
                    description=f"Fit score achieved for {job.get('role_title', 'Role')}: {job.get('fit_score', 75)}%.",
                    timestamp=job.get("created_at") or datetime.now(timezone.utc),
                    module_source="job_match",
                    impact_score=10,
                )
            )

        # 7. Interview
        intv = context.get("interview")
        if intv:
            events.append(
                TimelineEvent(
                    event_id="evt_intv",
                    event_type="Interview Completed",
                    title="AI Mock Interview Completed",
                    description=f"Overall interview performance score: {intv.get('overall_score', 80)}/100.",
                    timestamp=intv.get("created_at") or datetime.now(timezone.utc),
                    module_source="interview",
                    impact_score=15,
                )
            )

        # 8. Learning Roadmap
        lr = context.get("learning_roadmap")
        if lr:
            events.append(
                TimelineEvent(
                    event_id="evt_lr",
                    event_type="Learning Milestone",
                    title="Learning Roadmap Milestone Check",
                    description=f"Progress achieved: {lr.get('progress_percentage', 35.0)}%.",
                    timestamp=lr.get("created_at") or datetime.now(timezone.utc),
                    module_source="learning",
                    impact_score=10,
                )
            )

        # Always append a Career Health Increased milestone
        events.append(
            TimelineEvent(
                event_id="evt_health",
                event_type="Career Health Increased",
                title="Career Intelligence Aggregated",
                description="Digital Twin Memory synthesized into unified v1.0 Career Health Score.",
                timestamp=datetime.now(timezone.utc),
                module_source="twin",
                impact_score=20,
            )
        )

        # Sort chronologically ascending
        events.sort(key=lambda x: x.timestamp)
        return events

    @classmethod
    def calculate_career_health_score(
        cls,
        readiness_score: int,
        ats_score: int,
        job_match_score: int,
        interview_score: int,
        learning_progress: float,
        completed_projects: int = 0,
        completed_milestones: int = 0,
    ) -> CareerHealthScore:
        """
        Deterministic scoring algorithm for Overall Career Health Score.
        Combines weighted scores from:
        - Career Readiness: 25%
        - ATS Match: 20%
        - Job Match: 20%
        - Interview: 20%
        - Learning Progress: 10%
        - Project & Milestone Bonus: up to 5 points (completed_projects * 2.0 + completed_milestones * 0.5)
        Do NOT allow AI to invent this score.
        """
        readiness_comp = float(readiness_score) * 0.25
        ats_comp = float(ats_score) * 0.20
        job_match_comp = float(job_match_score) * 0.20
        interview_comp = float(interview_score) * 0.20
        learning_comp = float(learning_progress) * 0.10
        bonus = min(
            5.0, float(completed_projects) * 2.0 + float(completed_milestones) * 0.5
        )

        raw_sum = (
            readiness_comp
            + ats_comp
            + job_match_comp
            + interview_comp
            + learning_comp
            + bonus
        )
        overall = int(min(100, max(0, round(raw_sum))))

        if overall >= 85:
            status = "Excellent"
        elif overall >= 70:
            status = "Strong"
        elif overall >= 50:
            status = "Moderate"
        else:
            status = "Needs Attention"

        return CareerHealthScore(
            overall_score=overall,
            readiness_component=round(readiness_comp, 1),
            ats_component=round(ats_comp, 1),
            job_match_component=round(job_match_comp, 1),
            interview_component=round(interview_comp, 1),
            learning_component=round(learning_comp, 1),
            project_milestone_bonus=round(bonus, 1),
            status=status,
        )

    @classmethod
    async def get_dashboard_summary(
        cls, user_id: str, db: AsyncIOMotorDatabase
    ) -> DashboardSummary:
        """
        Aggregates insights from every OMNI module into a single executive dashboard summary.
        """
        context = await DigitalTwinService.get_context(user_id, db)

        # Concurrently fetch individual analytics components
        (
            career_analytics,
            ats_analytics,
            job_match_analytics,
            interview_analytics,
            learning_analytics,
            digital_twin_analytics,
            skill_matrix,
            timeline,
        ) = await asyncio.gather(
            cls.get_career_analytics(user_id, db),
            cls.get_ats_analytics(user_id, db),
            cls.get_job_match_analytics(user_id, db),
            cls.get_interview_analytics(user_id, db),
            cls.get_learning_analytics(user_id, db),
            cls.get_digital_twin_analytics(user_id, context),
            cls.get_skill_matrix(user_id, context),
            cls.get_timeline(user_id, context),
        )

        readiness_score = career_analytics.current_score
        ats_score = ats_analytics.latest_score
        job_match_score = job_match_analytics.latest_match_score
        interview_score = (
            interview_analytics.technical_score_trend[-1]
            if interview_analytics.technical_score_trend
            else 75
        )
        learning_progress = learning_analytics.learning_progress

        health_score = cls.calculate_career_health_score(
            readiness_score=readiness_score,
            ats_score=ats_score,
            job_match_score=job_match_score,
            interview_score=interview_score,
            learning_progress=learning_progress,
            completed_projects=learning_analytics.completed_projects,
            completed_milestones=learning_analytics.completed_milestones,
        )

        overall = health_score.overall_score
        confidence = round(min(99.0, 60.0 + (overall * 0.35)), 1)
        goal_progress = round(
            min(100.0, (overall / 90.0) * 100.0), 1
        )  # target is 90 score

        analytics_data = {
            "overall_career_health_score": overall,
            "career_readiness_score": readiness_score,
            "ats_score": ats_score,
            "job_match_score": job_match_score,
            "interview_score": interview_score,
            "learning_progress": learning_progress,
        }

        insights = await AnalyticsAIService.generate_executive_insights(
            user_id=user_id, context=context, analytics_data=analytics_data
        )

        return DashboardSummary(
            user_id=user_id,
            career_health_score=health_score,
            career_readiness_score=readiness_score,
            ats_score=ats_score,
            job_match_score=job_match_score,
            interview_score=interview_score,
            learning_progress=learning_progress,
            digital_twin_confidence=confidence,
            career_goal_progress=goal_progress,
            overall_career_health_score=overall,
            career_analytics=career_analytics,
            ats_analytics=ats_analytics,
            job_match_analytics=job_match_analytics,
            interview_analytics=interview_analytics,
            learning_analytics=learning_analytics,
            digital_twin_analytics=digital_twin_analytics,
            skill_matrix=skill_matrix,
            timeline=timeline,
            insights=insights,
        )

    @classmethod
    async def export_report(
        cls, user_id: str, report_type: str, db: AsyncIOMotorDatabase
    ) -> bytes:
        """
        Generates a downloadable PDF report (Career Report, Analytics Summary,
        Progress Report, or Career Timeline) using built-in PDF formatting or ReportLab.
        """
        summary = await cls.get_dashboard_summary(user_id, db)

        # Generate a clean PDF buffer
        # Using simple PDF canvas format so it never fails even if reportlab is missing
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas

            buf = io.BytesIO()
            p = canvas.Canvas(buf, pagesize=letter)
            width, height = letter

            # Header
            p.setFont("Helvetica-Bold", 18)
            p.drawString(50, height - 50, f"OMNI Digital Twin — {report_type.upper()} REPORT")
            p.setFont("Helvetica", 10)
            p.drawString(
                50,
                height - 70,
                f"Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} | User ID: {user_id}",
            )

            p.line(50, height - 80, width - 50, height - 80)

            # Core Metrics
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, height - 110, "Executive Career Health Audit")

            p.setFont("Helvetica", 11)
            y = height - 135
            metrics = [
                (
                    "Overall Career Health Score:",
                    f"{summary.overall_career_health_score}/100 ({summary.career_health_score.status})",
                ),
                (
                    "Career Readiness Score:",
                    f"{summary.career_readiness_score}/100",
                ),
                ("ATS Resume Optimization Score:", f"{summary.ats_score}/100"),
                ("Job Match Fit Score:", f"{summary.job_match_score}/100"),
                (
                    "Mock Interview Performance:",
                    f"{summary.interview_score}/100",
                ),
                (
                    "Learning Roadmap Progress:",
                    f"{summary.learning_progress:.1f}%",
                ),
                (
                    "Digital Twin Confidence:",
                    f"{summary.digital_twin_confidence:.1f}%",
                ),
            ]

            for label, val in metrics:
                p.drawString(60, y, f"{label:<35} {val}")
                y -= 20

            # Insights
            y -= 15
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y, "AI Executive Summary & Recommendations")
            y -= 25

            p.setFont("Helvetica-Bold", 11)
            p.drawString(60, y, "Top Demonstrated Strengths:")
            y -= 18
            p.setFont("Helvetica", 10)
            for st in summary.insights.current_strengths[:3]:
                p.drawString(75, y, f"• {st}")
                y -= 16

            y -= 5
            p.setFont("Helvetica-Bold", 11)
            p.drawString(60, y, "Recommended Next Action:")
            y -= 18
            p.setFont("Helvetica", 10)
            p.drawString(75, y, f"-> {summary.insights.recommended_next_action}")
            y -= 30

            # Footer
            p.setFont("Helvetica-Oblique", 9)
            p.drawString(50, 40, "OMNI AI Career Readiness Platform v1.0 Production Release")

            p.showPage()
            p.save()
            pdf_bytes = buf.getvalue()
            buf.close()
            return pdf_bytes

        except ImportError:
            # Simple minimal PDF byte stream fallback if reportlab is not installed
            content_str = (
                f"OMNI DIGITAL TWIN — {report_type.upper()} REPORT\n\n"
                f"User ID: {user_id}\n"
                f"Overall Career Health Score: {summary.overall_career_health_score}/100 ({summary.career_health_score.status})\n"
                f"Career Readiness: {summary.career_readiness_score}/100\n"
                f"ATS Score: {summary.ats_score}/100\n"
                f"Job Match Score: {summary.job_match_score}/100\n"
                f"Interview Score: {summary.interview_score}/100\n"
                f"Learning Progress: {summary.learning_progress:.1f}%\n\n"
                f"Recommended Next Action:\n{summary.insights.recommended_next_action}\n"
            )
            # Basic PDF format wrapper
            pdf_header = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            pdf_body = (
                b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
                b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
                b"4 0 obj\n<< /Length " + str(len(content_str)).encode("ascii") + b" >>\nstream\n"
                b"BT\n/F1 12 Tf\n50 700 Td\n("
                + content_str.replace("\n", ") Tj\n0 -20 Td\n(").encode("latin1", "replace")
                + b") Tj\nET\nendstream\nendobj\n"
            )
            pdf_footer = b"trailer\n<< /Root 1 0 R >>\n%%EOF"
            return pdf_header + pdf_body + pdf_footer
