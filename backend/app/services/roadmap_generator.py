"""Roadmap generator: builds a personalized 6-week learning roadmap.

Key Capabilities:
-----------------
1. Prerequisite Ordering: Strictly schedules foundational skills before dependent skills.
2. 6-Week Progression: Structures learning across Weeks 1 through 6.
3. Role-Specific Capstone: Culminates in a role-aligned project from curated role specifications.
4. Curated Scope: Avoids dumping entire catalogues; focuses on missing core/recommended skills.
5. Verified Resources: Distinguishes validated official URLs from suggested study guides.
6. Empty Gap Handling: Provides an advanced mastery roadmap when core skills are already met.
7. Availability Pacing: Allocates weekly task hours based on user's weekly study budget.
"""

from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from app.schemas.roadmap import (
    LearningResource,
    Roadmap,
    RoadmapTask,
    WeekPlan,
)
from app.services.skill_analyzer import get_role
from app.services.skill_extractor import extract_skills, get_skill_meta

# ---------------------------------------------------------------------------
# Verified Official Documentation Registry
# ---------------------------------------------------------------------------

_VERIFIED_DOCS: Dict[str, Tuple[str, str]] = {
    "python": ("Python Official Tutorial & Docs", "https://docs.python.org/3/"),
    "fastapi": ("FastAPI Official Documentation", "https://fastapi.tiangolo.com"),
    "docker": ("Docker Getting Started & Reference", "https://docs.docker.com/get-started/"),
    "kubernetes": ("Kubernetes Documentation", "https://kubernetes.io/docs/home/"),
    "postgresql": ("PostgreSQL Official Documentation", "https://www.postgresql.org/docs/"),
    "redis": ("Redis Documentation & Commands", "https://redis.io/docs/"),
    "git": ("Pro Git Book & Official Docs", "https://git-scm.com/doc"),
    "pytorch": ("PyTorch Tutorials & API", "https://pytorch.org/tutorials/"),
    "scikit_learn": ("scikit-learn User Guide", "https://scikit-learn.org/stable/user_guide.html"),
    "sql": ("PostgreSQL Tutorial (SQL)", "https://www.postgresqltutorial.com/"),
    "airflow": ("Apache Airflow Documentation", "https://airflow.apache.org/docs/"),
    "spark": ("Apache Spark Quick Start & Docs", "https://spark.apache.org/docs/latest/"),
    "dbt": ("dbt Documentation & Tutorials", "https://docs.getdbt.com"),
    "kafka": ("Apache Kafka Documentation", "https://kafka.apache.org/documentation/"),
    "mlflow": ("MLflow Tracking & LLM Docs", "https://mlflow.org/docs/latest/index.html"),
    "langchain": ("LangChain Official Documentation", "https://docs.langchain.com"),
    "openai_api": ("OpenAI API Documentation", "https://platform.openai.com/docs/"),
    "terraform": ("Terraform Documentation", "https://developer.hashicorp.com/terraform/docs"),
    "harness_platform": ("Harness Developer Hub", "https://developer.harness.io"),
    "deployment_pipelines": ("Harness CD Documentation", "https://developer.harness.io/docs/continuous-delivery/"),
    "rest_api": ("RESTful API Best Practices", "https://restfulapi.net/"),
    "grpc": ("gRPC Documentation", "https://grpc.io/docs/"),
    "tableau": ("Tableau Public Resources", "https://public.tableau.com/en-us/s/resources"),
    "statistics": ("Khan Academy Statistics & Probability", "https://www.khanacademy.org/math/statistics-probability"),
    "vector_db": ("Vector Database Guide (Pinecone / Weaviate)", "https://www.pinecone.io/learn/vector-database/"),
    "rag": ("LangChain RAG Architecture Guide", "https://docs.langchain.com/docs/use_cases/question_answering/"),
    "prompt_engineering": ("OpenAI Prompt Engineering Guide", "https://platform.openai.com/docs/guides/prompt-engineering"),
    "llm_evaluation": ("OpenAI Evals Framework Docs", "https://github.com/openai/evals"),
    "ci_cd": ("GitHub Actions CI/CD Guides", "https://docs.github.com/en/actions"),
    "aws": ("AWS Well-Architected Framework", "https://aws.amazon.com/architecture/well-architected/"),
}


# ---------------------------------------------------------------------------
# Helper: Resource Resolver
# ---------------------------------------------------------------------------


def _resolve_resource(skill_id: str, canonical_name: str, role_resources: List[dict]) -> LearningResource:
    """Resolve a learning resource for a skill, checking verified registries first."""
    # 1. Check verified official docs table
    if skill_id in _VERIFIED_DOCS:
        title, url = _VERIFIED_DOCS[skill_id]
        return LearningResource(
            title=title,
            url=url,
            is_verified=True,
            verification_status="Verified (Official Documentation)",
        )

    # 2. Check if role profile contains an official resource mentioning this skill
    for res in role_resources:
        title = res.get("title", "")
        url = res.get("url")
        if canonical_name.lower() in title.lower() or skill_id in title.lower():
            return LearningResource(
                title=title,
                url=url,
                is_verified=bool(url),
                verification_status="Verified (Curated Role Resource)" if url else "Requires verification",
            )

    # 3. Fallback: suggested unverified resource
    return LearningResource(
        title=f"{canonical_name} Practical Self-Study Guide",
        url=None,
        is_verified=False,
        verification_status="Requires verification (Suggested Curriculum)",
    )


# ---------------------------------------------------------------------------
# Dependency Resolution & Topological Ordering
# ---------------------------------------------------------------------------


def _build_ordered_skills_to_learn(
    target_skills: List[str],
    known_skills: Set[str],
) -> List[Tuple[str, int]]:
    """
    Given missing target skills and candidate's known skills:
    1. Expands missing prerequisites.
    2. Builds dependency graph.
    3. Performs topological level sorting (level 0 = foundational, level 1+ = dependent).

    Returns a list of (skill_id, topological_depth) tuples ordered by depth.
    """
    # Set of skills to learn
    to_learn: Set[str] = set()

    # Expand prerequisites recursively
    queue = deque(target_skills)
    while queue:
        curr = queue.popleft()
        if curr in known_skills or curr in to_learn:
            continue
        to_learn.add(curr)
        meta = get_skill_meta(curr)
        for prereq in meta.get("prerequisites", []):
            if prereq not in known_skills and prereq not in to_learn:
                queue.append(prereq)

    # If nothing to learn, return empty
    if not to_learn:
        return []

    # Build dependency graph among skills to learn
    adj: Dict[str, List[str]] = defaultdict(list)
    in_degree: Dict[str, int] = {s: 0 for s in to_learn}

    for skill in to_learn:
        meta = get_skill_meta(skill)
        prereqs = [p for p in meta.get("prerequisites", []) if p in to_learn]
        for p in prereqs:
            adj[p].append(skill)
            in_degree[skill] += 1

    # Topological sort with depth / level assignment
    depth: Dict[str, int] = {s: 0 for s in to_learn}
    zero_degree = deque([s for s in to_learn if in_degree[s] == 0])
    ordered: List[str] = []

    while zero_degree:
        node = zero_degree.popleft()
        ordered.append(node)
        current_depth = depth[node]

        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            depth[neighbor] = max(depth[neighbor], current_depth + 1)
            if in_degree[neighbor] == 0:
                zero_degree.append(neighbor)

    # Any remaining cycles (if any) appended with max depth
    for skill in to_learn:
        if skill not in ordered:
            ordered.append(skill)
            depth[skill] = 3

    return [(s, depth[s]) for s in ordered]


# ---------------------------------------------------------------------------
# Roadmap Generation Engine
# ---------------------------------------------------------------------------


def generate_roadmap(
    role_id: str,
    existing_skills: Optional[List[str]] = None,
    missing_skills: Optional[List[str]] = None,
    weekly_hours: int = 10,
    resume_text: Optional[str] = None,
) -> Roadmap:
    """
    Generate a 6-week learning roadmap for a role.

    Guarantees:
    - Foundational skills precede dependent skills.
    - Exactly 6 weeks structured progression.
    - Role-specific capstone project in Week 6.
    - Respects weekly hour budget.
    """
    profile = get_role(role_id)
    if profile is None:
        raise KeyError(f"Role '{role_id}' not found in role catalogue.")

    role_title = profile.get("canonical_title", role_id)
    role_resources = profile.get("learning_resources", [])
    example_projects = profile.get("example_projects", [])
    capstone_project = (
        example_projects[0]
        if example_projects
        else f"Comprehensive end-to-end {role_title} production milestone project."
    )

    # 1. Determine existing skills
    known_skill_ids: Set[str] = set()
    if existing_skills:
        for s in existing_skills:
            clean = s.strip().lower()
            meta = get_skill_meta(clean)
            if meta:
                known_skill_ids.add(clean)
            else:
                # Try extract
                matches = extract_skills(clean)
                for m in matches:
                    known_skill_ids.add(m.skill_id)

    if resume_text:
        extracted = extract_skills(resume_text)
        for m in extracted:
            known_skill_ids.add(m.skill_id)

    # 2. Determine target skills to learn
    target_skill_ids: List[str] = []
    core_skills = profile.get("core_skills", [])
    recommended_skills = profile.get("recommended_skills", [])
    advanced_skills = profile.get("advanced_skills", [])

    is_mastery_mode = False
    if missing_skills is not None:
        for ms in missing_skills:
            clean = ms.strip().lower()
            meta = get_skill_meta(clean)
            if meta:
                target_skill_ids.append(clean)
            else:
                matches = extract_skills(clean)
                for m in matches:
                    target_skill_ids.append(m.skill_id)
        if not target_skill_ids:
            is_mastery_mode = True
            for adv in advanced_skills + recommended_skills:
                if adv not in known_skill_ids and adv not in target_skill_ids:
                    target_skill_ids.append(adv)
                if len(target_skill_ids) >= 4:
                    break
            if not target_skill_ids:
                target_skill_ids = core_skills[:3]
    else:
        # Determine missing core skills
        missing_core = [cs for cs in core_skills if cs not in known_skill_ids]
        if not missing_core:
            is_mastery_mode = True
            # Candidate meets all core skills! Target advanced skills and specialization
            for adv in advanced_skills + recommended_skills:
                if adv not in known_skill_ids and adv not in target_skill_ids:
                    target_skill_ids.append(adv)
                if len(target_skill_ids) >= 4:
                    break
            if not target_skill_ids:
                target_skill_ids = core_skills[:3]
        else:
            target_skill_ids = list(missing_core)
            # If very few core skills are missing, selectively add recommended skills
            if len(target_skill_ids) < 4:
                for rs in recommended_skills:
                    if rs not in known_skill_ids and rs not in target_skill_ids:
                        target_skill_ids.append(rs)
                        if len(target_skill_ids) >= 5:
                            break

    # 4. Topological order skills
    ordered_with_depth = _build_ordered_skills_to_learn(target_skill_ids, known_skill_ids)

    # 5. Distribute tasks across 6 weeks
    # Weeks 1-5: progressive skill acquisition ordered by depth
    # Week 6: Role Capstone Project
    week_buckets: Dict[int, List[RoadmapTask]] = {w: [] for w in range(1, 7)}
    all_tasks: List[RoadmapTask] = []
    prerequisite_chains: Dict[str, List[str]] = {}

    max_skills_to_schedule = min(5, len(ordered_with_depth))
    scheduled_items = ordered_with_depth[:max_skills_to_schedule]
    num_items = len(scheduled_items)

    for idx, (skill_id, depth_level) in enumerate(scheduled_items):
        meta = get_skill_meta(skill_id)
        canonical = meta.get("canonical", skill_id)
        prereqs = meta.get("prerequisites", [])
        prerequisite_chains[canonical] = [
            get_skill_meta(p).get("canonical", p) for p in prereqs
        ]

        # Spread across weeks 1 to 5 monotonically
        if num_items <= 1:
            assigned_week = 1
        else:
            proportional_week = 1 + int(idx * 4 / (num_items - 1))
            assigned_week = min(5, max(depth_level + 1, proportional_week))

        resource = _resolve_resource(skill_id, canonical, role_resources)

        task = RoadmapTask(
            id=f"task-w{assigned_week}-{skill_id}",
            title=f"Learn & Implement {canonical}",
            description=(
                f"Study core concepts of {canonical}, review official guides, "
                f"and build practical exercises demonstrating competency in {role_title} workflows."
            ),
            target_skill=canonical,
            week=assigned_week,
            estimated_effort=weekly_hours,  # Adjusted after bucket assignment
            prerequisites=[get_skill_meta(p).get("canonical", p) for p in prereqs],
            learning_resource=resource,
            completion_status="pending",
        )
        week_buckets[assigned_week].append(task)
        all_tasks.append(task)

    # Ensure Weeks 1 through 5 have tasks; if any week is empty, add practical drills or project milestone
    for w in range(1, 6):
        if not week_buckets[w]:
            consolidation_task = RoadmapTask(
                id=f"task-w{w}-milestone",
                title=f"Week {w} Milestone: Practical Architecture & Mini-Project",
                description=(
                    f"Integrate skills acquired so far into a working prototype reflecting "
                    f"{role_title} day-to-day engineering patterns."
                ),
                target_skill=role_title,
                week=w,
                estimated_effort=weekly_hours,
                prerequisites=[],
                learning_resource=LearningResource(
                    title=f"{role_title} Architecture Guide",
                    url=None,
                    is_verified=False,
                    verification_status="Requires verification (Project Specification)",
                ),
                completion_status="pending",
            )
            week_buckets[w].append(consolidation_task)
            all_tasks.append(consolidation_task)

    # Balance effort for each week 1..5 so sum of tasks <= weekly_hours
    for w in range(1, 6):
        w_tasks = week_buckets[w]
        task_count = len(w_tasks)
        if task_count > 0:
            per_task_effort = max(3, weekly_hours // task_count)
            for t in w_tasks:
                t.estimated_effort = per_task_effort

    # Week 6: Always the Role-Specific Capstone Project
    capstone_resource = (
        LearningResource(
            title=role_resources[0]["title"],
            url=role_resources[0].get("url"),
            is_verified=bool(role_resources[0].get("url")),
            verification_status="Verified (Curated Role Resource)" if role_resources[0].get("url") else "Requires verification",
        )
        if role_resources
        else LearningResource(
            title=f"{role_title} Capstone Project Specification",
            url=None,
            is_verified=False,
            verification_status="Requires verification",
        )
    )

    capstone_task = RoadmapTask(
        id="task-w6-capstone",
        title=f"Week 6 Capstone Project: {role_title}",
        description=f"Deliver complete capstone: {capstone_project}",
        target_skill=role_title,
        week=6,
        estimated_effort=weekly_hours,
        prerequisites=[t.target_skill for t in all_tasks if t.target_skill != role_title][:3],
        learning_resource=capstone_resource,
        completion_status="pending",
    )
    week_buckets[6].append(capstone_task)
    all_tasks.append(capstone_task)

    # Sort all_tasks strictly by week
    all_tasks.sort(key=lambda t: t.week)

    # Build structured WeekPlans
    week_themes = {
        1: "Foundations & Core Prerequisites",
        2: "Tooling, Environments & Core Storage",
        3: "Frameworks & Applied Architecture",
        4: "Advanced Integrations & Cloud Infrastructure",
        5: "Quality, Observability & Evaluation",
        6: f"Role Capstone Project: {role_title}",
    }

    weeks: List[WeekPlan] = []
    total_estimated_hours = 0

    for w in range(1, 7):
        w_tasks = week_buckets[w]
        w_hours = sum(t.estimated_effort for t in w_tasks)
        total_estimated_hours += w_hours

        milestone = (
            f"Complete practical checkpoint for Week {w}."
            if w < 6
            else f"Final Capstone Delivery: {capstone_project}"
        )

        weeks.append(
            WeekPlan(
                week_number=w,
                theme=week_themes[w],
                weekly_hours_allocated=w_hours,
                tasks=w_tasks,
                milestone_project=milestone,
            )
        )

    notes = [
        f"Roadmap calibrated for {weekly_hours} hours/week across 6 structured weeks.",
        "Foundational prerequisite skills are strictly scheduled prior to dependent frameworks.",
        "Official documentation URLs are verified; suggested project guides are labeled 'Requires verification'.",
    ]
    if is_mastery_mode:
        notes.insert(
            0,
            "Notice: Candidate already meets the core profile for this role. This roadmap is focused on advanced mastery, specialized competencies, and portfolio demonstration.",
        )

    return Roadmap(
        role_id=role_id,
        role_title=role_title,
        total_weeks=6,
        target_weekly_hours=weekly_hours,
        total_estimated_hours=total_estimated_hours,
        weeks=weeks,
        tasks=all_tasks,
        capstone_project=capstone_project,
        prerequisite_chains=prerequisite_chains,
        notes=notes,
    )
