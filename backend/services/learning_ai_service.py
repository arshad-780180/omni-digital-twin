import json
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from models.learning import (
    LearningRoadmap,
    LearningPhase,
    Milestone,
    ProjectRecommendation,
    CertificationRecommendation,
    LearningResource,
    LearningRoadmapGenerateRequest,
)
from ai.llm_provider import get_llm_provider

logger = logging.getLogger("omni.learning.ai")


class LearningRoadmapAIService:
    """
    AI Personalized Learning Roadmap Engine with 100% deterministic rule-based fallback.
    Generates adaptive career learning plans using candidates' complete Digital Twin context.
    """

    @classmethod
    def _extract_skills(cls, context: Dict[str, Any]) -> List[str]:
        skills_set = set()
        # From Profile
        prof = context.get("profile") or {}
        for s in prof.get("skills", []):
            if isinstance(s, str) and s.strip():
                skills_set.add(s.strip())
        # From Resume
        res = context.get("resume") or {}
        parsed = res.get("parsed_data", {}) if isinstance(res, dict) else {}
        for s in parsed.get("skills", []):
            if isinstance(s, str) and s.strip():
                skills_set.add(s.strip())
        # From GitHub
        gh = context.get("github_analysis") or {}
        for l in gh.get("top_languages", []):
            if isinstance(l, str) and l.strip():
                skills_set.add(l.strip())
        # From Memory
        mem = context.get("memory") or {}
        for s in mem.get("core_skills", []):
            if isinstance(s, str) and s.strip():
                skills_set.add(s.strip())
        return list(skills_set)

    @classmethod
    def _extract_missing_skills(cls, context: Dict[str, Any]) -> List[str]:
        missing_set = set()
        # From Memory
        mem = context.get("memory") or {}
        for s in mem.get("missing_skills", []):
            if isinstance(s, str) and s.strip():
                missing_set.add(s.strip())
        # From Career Analysis
        car = context.get("career_analysis") or {}
        for s in car.get("weaknesses", []):
            if isinstance(s, str) and s.strip():
                missing_set.add(s.strip())
        # From ATS Analysis
        ats = context.get("ats_analysis") or {}
        for s in ats.get("missing_skills", []):
            if isinstance(s, str) and s.strip():
                missing_set.add(s.strip())
        # From Job Matching
        jm = context.get("job_matching") or {}
        for s in jm.get("missing_skills", []):
            if isinstance(s, str) and s.strip():
                missing_set.add(s.strip())
        # Default missing skills if candidate has none documented
        default_missing = ["Docker", "Kubernetes", "Redis", "CI/CD", "AWS", "System Design", "Microservices", "GraphQL"]
        existing_skills = {s.lower() for s in cls._extract_skills(context)}
        for d in default_missing:
            if d.lower() not in existing_skills and len(missing_set) < 6:
                missing_set.add(d)
        return list(missing_set)

    @classmethod
    def _extract_target_role(cls, request: LearningRoadmapGenerateRequest, context: Dict[str, Any]) -> str:
        if request.target_role and request.target_role.strip():
            return request.target_role.strip()
        mem = context.get("memory") or {}
        target_roles = mem.get("target_roles", [])
        if target_roles and isinstance(target_roles, list) and len(target_roles) > 0 and isinstance(target_roles[0], str):
            return target_roles[0].strip()
        prof = context.get("profile") or {}
        if prof.get("target_role"):
            return str(prof.get("target_role")).strip()
        return "Senior Backend Engineer"

    @classmethod
    async def generate_roadmap(
        cls,
        user_id: str,
        request: LearningRoadmapGenerateRequest,
        context: Dict[str, Any],
    ) -> LearningRoadmap:
        """
        Generates an adaptive AI learning roadmap using Gemini, with deterministic fallback.
        """
        target_role = cls._extract_target_role(request, context)
        current_skills = cls._extract_skills(context)
        missing_skills = cls._extract_missing_skills(context)

        try:
            llm = get_llm_provider()
            prompt = f"""
You are an expert AI Career Mentor and Principal Engineering Lead.
Generate a structured, personalized Learning Roadmap for a candidate aiming to become a top {target_role}.

Candidate Digital Twin Context:
- Demonstrated Skills: {', '.join(current_skills[:15]) if current_skills else 'Standard Software Engineering Skills'}
- Missing / Priority Skills to Acquire: {', '.join(missing_skills[:12]) if missing_skills else 'Cloud, System Design, DevOps'}
- Target Timeframe: {request.target_timeframe_weeks} weeks

Requirements:
1. Design exactly 4 Learning Phases progressing from fundamentals to advanced system design and production readiness.
2. Every phase must include:
   - objectives and expected_outcomes
   - 2-3 interactive milestones (milestone_id should be unique like "m1", "m2", etc.)
   - 1-2 practical project recommendations with difficulty and portfolio value
   - 2-3 learning resources (ranked by priority across Official Documentation, YouTube Course, Book, Interactive Platform, LeetCode Problem, System Design)
3. Include 2-3 high-relevance industry certifications.
4. Include a practice_schedule, mock_interview_schedule, and revision_plan.
5. Return ONLY valid JSON matching this schema:
{{
  "target_role": "{target_role}",
  "current_readiness": 48,
  "target_readiness": 95,
  "estimated_completion": "{request.target_timeframe_weeks} weeks",
  "priority_skills": {json.dumps(missing_skills[:6])},
  "learning_phases": [
    {{
      "phase_number": 1,
      "title": "Phase 1: Docker & Container Architecture",
      "objectives": ["Master containerization", "Build reproducible environments"],
      "expected_outcomes": ["Dockerize multi-container web apps"],
      "estimated_hours": 30,
      "difficulty": "Intermediate",
      "prerequisites": ["Linux CLI fundamentals"],
      "milestones": [
        {{
          "milestone_id": "m1",
          "title": "Build & Optimize Production Dockerfile",
          "phase": 1,
          "category": "skill",
          "description": "Create a multi-stage Dockerfile for a FastAPI/Node app with security hardening.",
          "skills_unlocked": ["Docker", "Containerization"]
        }}
      ],
      "projects": [
        {{
          "project_id": "p1",
          "title": "Containerized Microservice Stack",
          "description": "Develop a REST API backend with Postgres & Redis using Docker Compose.",
          "difficulty": "Intermediate",
          "estimated_time": "15 hours",
          "skills_covered": ["Docker", "PostgreSQL", "Redis"],
          "portfolio_value": "High"
        }}
      ],
      "resources": [
        {{
          "resource_id": "r1",
          "title": "Official Docker Documentation",
          "type": "Official Documentation",
          "url": "https://docs.docker.com",
          "priority": "High",
          "difficulty": "Intermediate"
        }}
      ],
      "checkpoint": "Successfully run complete backend suite via docker-compose up"
    }}
  ],
  "certifications": [
    {{
      "cert_id": "c1",
      "title": "AWS Certified Solutions Architect",
      "issuer": "Amazon Web Services",
      "difficulty": "Advanced",
      "priority": "High",
      "relevance": "Directly validates cloud architecture competence"
    }}
  ],
  "practice_schedule": ["Monday-Wednesday: 2 hours hands-on coding", "Thursday-Friday: 1 hour system design study"],
  "mock_interview_schedule": ["Week 3: System Design Mock Interview", "Week 6: Full Stack Technical Mock Interview"],
  "revision_plan": ["Weekly Sunday review of solved engineering challenges"],
  "final_career_goal": "Secure an offer as {target_role}"
}}
"""
            response_text = await llm.generate_text(prompt)
            match = re.search(r"(\{.*\})", response_text, re.DOTALL)
            if match:
                raw_json = match.group(1)
                parsed = json.loads(raw_json)
                roadmap = LearningRoadmap(**parsed)
                cls._populate_flat_lists(roadmap)
                logger.info(f"[LearningAI] Generated AI learning roadmap for {target_role}")
                return roadmap
            else:
                logger.warning("[LearningAI] No JSON block in LLM response; using rule-based fallback.")
        except Exception as e:
            logger.warning(f"[LearningAI] Notice: AI generation failed ({str(e)}). Using 100% deterministic fallback.")

        return cls.fallback_generate_roadmap(request, context)

    @classmethod
    def _populate_flat_lists(cls, roadmap: LearningRoadmap) -> None:
        """
        Populates top-level flat milestones, projects, and resources lists from learning_phases.
        """
        all_milestones: List[Milestone] = []
        all_projects: List[ProjectRecommendation] = []
        all_resources: List[LearningResource] = []
        for phase in roadmap.learning_phases:
            all_milestones.extend(phase.milestones)
            all_projects.extend(phase.projects)
            all_resources.extend(phase.resources)
        if not roadmap.milestones:
            roadmap.milestones = all_milestones
        if not roadmap.projects:
            roadmap.projects = all_projects
        if not roadmap.resources:
            roadmap.resources = all_resources

    @classmethod
    def fallback_generate_roadmap(
        cls,
        request: LearningRoadmapGenerateRequest,
        context: Dict[str, Any],
    ) -> LearningRoadmap:
        """
        100% deterministic rule-based learning roadmap generator.
        Guarantees structured, high-value career guidance even when LLM providers are unavailable.
        """
        target_role = cls._extract_target_role(request, context)
        current_skills = cls._extract_skills(context)
        missing_skills = cls._extract_missing_skills(context)

        priority_skills = missing_skills[:6] if missing_skills else ["Docker", "Kubernetes", "AWS", "System Design", "Redis", "CI/CD"]
        current_readiness = max(35, min(75, 45 + len(current_skills) * 2))

        phase1_skills = priority_skills[:2] if len(priority_skills) >= 2 else ["Docker", "REST API"]
        phase2_skills = priority_skills[2:4] if len(priority_skills) >= 4 else ["Redis", "Caching"]
        phase3_skills = priority_skills[4:6] if len(priority_skills) >= 6 else ["AWS", "CI/CD"]
        phase4_skills = ["System Design", "Microservices"]

        phases: List[LearningPhase] = [
            LearningPhase(
                phase_number=1,
                title="Phase 1: Container Architecture & Core Fundamentals",
                objectives=[f"Master {phase1_skills[0]} containerization", "Build reproducible engineering environments"],
                expected_outcomes=[f"Deploy multi-container apps using {phase1_skills[0]}"],
                estimated_hours=25,
                difficulty="Intermediate",
                prerequisites=["Linux CLI & Git Fundamentals"],
                milestones=[
                    Milestone(
                        milestone_id="m1",
                        title=f"Build Multi-Stage {phase1_skills[0]} Service",
                        phase=1,
                        category="skill",
                        description=f"Create a production-hardened containerized application for {target_role}.",
                        skills_unlocked=phase1_skills,
                    ),
                    Milestone(
                        milestone_id="m2",
                        title="Automated Test Coverage Verification",
                        phase=1,
                        category="project",
                        description="Implement unit and integration test suites with >80% code coverage.",
                        skills_unlocked=["PyTest", "Unit Testing"],
                    ),
                ],
                projects=[
                    ProjectRecommendation(
                        project_id="p1",
                        title="Containerized REST Backend",
                        description="Develop a clean architecture REST API complete with Docker Compose setup.",
                        difficulty="Intermediate",
                        estimated_time="15 hours",
                        skills_covered=phase1_skills + ["PostgreSQL"],
                        portfolio_value="High",
                    )
                ],
                resources=[
                    LearningResource(
                        resource_id="r1",
                        title="Official Docker & Container Architecture Documentation",
                        type="Official Documentation",
                        url="https://docs.docker.com",
                        priority="High",
                        difficulty="Intermediate",
                    ),
                    LearningResource(
                        resource_id="r2",
                        title="Containerizing Modern Microservices (Video Lab)",
                        type="YouTube Course",
                        url="https://www.youtube.com",
                        priority="High",
                        difficulty="Intermediate",
                    ),
                ],
                checkpoint="Verify service boots and passes automated tests inside container.",
            ),
            LearningPhase(
                phase_number=2,
                title="Phase 2: High-Performance Caching & Asynchronous Processing",
                objectives=[f"Implement {phase2_skills[0]} caching layers", "Design asynchronous task queues"],
                expected_outcomes=["Reduce API latency by 60% via in-memory caching"],
                estimated_hours=30,
                difficulty="Intermediate",
                prerequisites=[f"Completed Phase 1 ({phase1_skills[0]})"],
                milestones=[
                    Milestone(
                        milestone_id="m3",
                        title=f"Integrate {phase2_skills[0]} Distributed Cache",
                        phase=2,
                        category="skill",
                        description=f"Implement read-through and write-behind caching using {phase2_skills[0]}.",
                        skills_unlocked=phase2_skills,
                    ),
                    Milestone(
                        milestone_id="m4",
                        title="Background Worker Pipeline",
                        phase=2,
                        category="skill",
                        description="Configure Celery/RQ background task processing for heavy workloads.",
                        skills_unlocked=["Asynchronous Task Queues", "Background Workers"],
                    ),
                ],
                projects=[
                    ProjectRecommendation(
                        project_id="p2",
                        title="High-Throughput Analytics Processor",
                        description="Build a real-time event ingestion pipeline buffered by Redis queues.",
                        difficulty="Advanced",
                        estimated_time="20 hours",
                        skills_covered=phase2_skills + ["Background Workers"],
                        portfolio_value="High",
                    )
                ],
                resources=[
                    LearningResource(
                        resource_id="r3",
                        title="Redis In-Memory Database Best Practices",
                        type="Official Documentation",
                        url="https://redis.io/docs",
                        priority="High",
                        difficulty="Intermediate",
                    ),
                    LearningResource(
                        resource_id="r4",
                        title="Designing Resilient Task Queues",
                        type="System Design",
                        url="https://github.com/donnemartin/system-design-primer",
                        priority="Medium",
                        difficulty="Advanced",
                    ),
                ],
                checkpoint="Demonstrate sub-10ms response times for cached API queries.",
            ),
            LearningPhase(
                phase_number=3,
                title="Phase 3: Cloud Native Infrastructure & CI/CD Pipelines",
                objectives=[f"Automate deployment using {phase3_skills[0]}", "Build zero-downtime CI/CD workflows"],
                expected_outcomes=["Deploy scalable services with GitHub Actions & Cloud infrastructure"],
                estimated_hours=35,
                difficulty="Advanced",
                prerequisites=["Completed Phase 2"],
                milestones=[
                    Milestone(
                        milestone_id="m5",
                        title="Production CI/CD Automated Deployment",
                        phase=3,
                        category="skill",
                        description="Build GitHub Actions workflows for linting, testing, and automated deployment.",
                        skills_unlocked=["CI/CD", "GitHub Actions"],
                    ),
                    Milestone(
                        milestone_id="m6",
                        title=f"{phase3_skills[0]} Cloud Infrastructure Deployment",
                        phase=3,
                        category="project",
                        description=f"Deploy containerized workloads to managed {phase3_skills[0]} infrastructure.",
                        skills_unlocked=phase3_skills,
                    ),
                ],
                projects=[
                    ProjectRecommendation(
                        project_id="p3",
                        title="Cloud-Native Production Environment",
                        description="Implement an automated infrastructure pipeline with monitoring and alerts.",
                        difficulty="Advanced",
                        estimated_time="25 hours",
                        skills_covered=phase3_skills + ["Monitoring", "CI/CD"],
                        portfolio_value="High",
                    )
                ],
                resources=[
                    LearningResource(
                        resource_id="r5",
                        title="AWS Well-Architected Framework",
                        type="Official Documentation",
                        url="https://aws.amazon.com/architecture/well-architected/",
                        priority="High",
                        difficulty="Advanced",
                    ),
                    LearningResource(
                        resource_id="r6",
                        title="GitHub Actions CI/CD Mastery",
                        type="Interactive Platform",
                        url="https://docs.github.com/en/actions",
                        priority="High",
                        difficulty="Intermediate",
                    ),
                ],
                checkpoint="Verify automated deployment triggers on git push to main branch.",
            ),
            LearningPhase(
                phase_number=4,
                title="Phase 4: System Design Mastery & Technical Leadership",
                objectives=["Master distributed system architecture", "Prepare for Principal & Senior interviews"],
                expected_outcomes=["Design scalable architectures capable of handling 10,000+ RPS"],
                estimated_hours=30,
                difficulty="Advanced",
                prerequisites=["Completed Phase 3"],
                milestones=[
                    Milestone(
                        milestone_id="m7",
                        title="Distributed System Architecture Blueprint",
                        phase=4,
                        category="skill",
                        description="Create architectural diagrams and load-balancing strategies for high availability.",
                        skills_unlocked=phase4_skills,
                    ),
                    Milestone(
                        milestone_id="m8",
                        title="Complete AI Mock Interview Evaluation",
                        phase=4,
                        category="interview",
                        description="Achieve an overall score >= 85% on an advanced OMNI AI Mock Interview.",
                        skills_unlocked=["Technical Communication", "System Design Defense"],
                    ),
                ],
                projects=[
                    ProjectRecommendation(
                        project_id="p4",
                        title="Distributed Ride-Sharing / Social Media Architecture",
                        description="Complete system design specification with database sharding and CDN caching.",
                        difficulty="Advanced",
                        estimated_time="20 hours",
                        skills_covered=phase4_skills + ["Load Balancing", "Sharding"],
                        portfolio_value="High",
                    )
                ],
                resources=[
                    LearningResource(
                        resource_id="r7",
                        title="System Design Primer Open Source Reference",
                        type="System Design",
                        url="https://github.com/donnemartin/system-design-primer",
                        priority="High",
                        difficulty="Advanced",
                    ),
                    LearningResource(
                        resource_id="r8",
                        title="Designing Data-Intensive Applications (Book Reference)",
                        type="Book",
                        url="https://dataintensive.net/",
                        priority="High",
                        difficulty="Advanced",
                    ),
                ],
                checkpoint="Successfully defend system architecture in an OMNI Mock Interview.",
            ),
        ]

        certifications: List[CertificationRecommendation] = [
            CertificationRecommendation(
                cert_id="c1",
                title="AWS Certified Solutions Architect – Associate",
                issuer="Amazon Web Services",
                difficulty="Advanced",
                priority="High",
                relevance="Demonstrates verified cloud native architecture competency.",
            ),
            CertificationRecommendation(
                cert_id="c2",
                title="Certified Kubernetes Administrator (CKA)",
                issuer="Cloud Native Computing Foundation",
                difficulty="Advanced",
                priority="High",
                relevance="Validates production container orchestration skills.",
            ),
            CertificationRecommendation(
                cert_id="c3",
                title="Docker Certified Associate (DCA)",
                issuer="Docker, Inc.",
                difficulty="Intermediate",
                priority="Medium",
                relevance="Proves mastery over containerized engineering workflows.",
            ),
        ]

        roadmap = LearningRoadmap(
            target_role=target_role,
            current_readiness=current_readiness,
            target_readiness=95,
            estimated_completion=f"{request.target_timeframe_weeks} weeks",
            priority_skills=priority_skills,
            learning_phases=phases,
            certifications=certifications,
            practice_schedule=[
                "Monday - Wednesday: 2 hours hands-on coding & project build",
                "Thursday - Friday: 1 hour system design & core documentation review",
                "Saturday: 3 hours portfolio project integration & Docker testing",
            ],
            mock_interview_schedule=[
                "Week 3: System Design & Architecture Mock Interview",
                f"Week {max(4, request.target_timeframe_weeks - 1)}: Comprehensive {target_role} Mock Interview",
            ],
            revision_plan=[
                "Weekly Sunday check-in: review completed milestones & update OMNI Digital Twin memory",
                "Bi-weekly code refactoring session on portfolio projects",
            ],
            final_career_goal=f"Secure a high-impact role as {target_role}",
        )
        cls._populate_flat_lists(roadmap)
        return roadmap
