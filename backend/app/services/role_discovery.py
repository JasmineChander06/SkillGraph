"""Role Discovery Service — Taxonomy exploration, related-role suggestions, and comparative analysis.

Features:
* Rich role details (responsibilities, prerequisites, core skills, optional skills, projects, related roles).
* Clear distinction between established titles and emerging specialized titles.
* Realistic entry-level accessibility warnings.
* Deterministic Jaccard skill overlap and bridge-skill transition calculations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from app.services import market_insights, skill_analyzer
from app.services.skill_extractor import get_skill_meta

# ---------------------------------------------------------------------------
# Maturity & Emergence Taxonomy Definitions
# ---------------------------------------------------------------------------

ROLE_MATURITY_REGISTRY: Dict[str, Dict[str, Any]] = {
    "backend-engineer": {
        "maturity": "established",
        "entry_level_accessible": True,
        "accessibility_guidance": (
            "Accessible to entry-level engineers with a solid foundation in Python or another server-side "
            "language, basic SQL, and web protocols. Junior positions and internships are commonplace."
        ),
        "emerging_context": None,
    },
    "data-analyst": {
        "maturity": "established",
        "entry_level_accessible": True,
        "accessibility_guidance": (
            "One of the most accessible entry points into data careers. Requires strong SQL, spreadsheet "
            "fluency, and reporting/visualization skills (Tableau, Power BI). Formal CS degree rarely required."
        ),
        "emerging_context": None,
    },
    "data-engineer": {
        "maturity": "established",
        "entry_level_accessible": True,
        "accessibility_guidance": (
            "Accessible at entry-to-mid level with strong programming (Python), data modeling, and SQL expertise. "
            "Production distributed pipeline experience (Spark, Kafka) is typically developed on the job."
        ),
        "emerging_context": None,
    },
    "machine-learning-engineer": {
        "maturity": "established",
        "entry_level_accessible": False,
        "accessibility_guidance": (
            "Rarely accessible as a first engineering role without graduate training or prior software engineering "
            "experience. Demands rigorous understanding of statistics, model architectures, and production deployment."
        ),
        "emerging_context": None,
    },
    "harness-engineer": {
        "maturity": "emerging",
        "entry_level_accessible": False,
        "accessibility_guidance": (
            "Not accessible to entry-level candidates. Requires deep prior experience with continuous delivery "
            "pipelines, container orchestration (Kubernetes), canary rollouts, and platform reliability."
        ),
        "emerging_context": (
            "An emerging platform engineering discipline born from the complexity of automated canary testing, "
            "feature management, and evaluation harnesses. Bridges traditional DevOps and quality infrastructure."
        ),
    },
    "forward-deployed-engineer": {
        "maturity": "emerging",
        "entry_level_accessible": False,
        "accessibility_guidance": (
            "Not suitable as a first engineering role. Requires mature full-stack technical capability, rapid "
            "unstructured prototyping, and high-stakes executive customer communication."
        ),
        "emerging_context": (
            "Popularized by mission-driven enterprise software vendors (Palantir, Databricks). Forward deployed "
            "engineers embed on-site with strategic customers to build bespoke integrations and high-impact workflows."
        ),
    },
    "forward-deployed-ai-engineer": {
        "maturity": "emerging",
        "entry_level_accessible": False,
        "accessibility_guidance": (
            "Senior role requiring multi-year software engineering tenure combined with modern LLM orchestration "
            "and on-premise enterprise security compliance."
        ),
        "emerging_context": (
            "A specialized hybrid role addressing the enterprise AI adoption bottleneck: taking foundation models "
            "and deploying them within client-governed VPCs with strict RAG, fine-tuning, and data privacy guardrails."
        ),
    },
    "ai-agent-engineer": {
        "maturity": "emerging",
        "entry_level_accessible": False,
        "accessibility_guidance": (
            "Requires substantial backend architecture and systems design knowledge before specializing. "
            "Stateful planning, function calling, and deterministic tool loops are error-prone without solid fundamentals."
        ),
        "emerging_context": (
            "Rapidly emerging discipline centered on building autonomous, multi-step LLM agents that plan, execute "
            "code, call external APIs, and recover from failures using frameworks like LangGraph and CrewAI."
        ),
    },
    "llmops-engineer": {
        "maturity": "emerging",
        "entry_level_accessible": False,
        "accessibility_guidance": (
            "Not accessible to beginners. Candidates typically possess 3+ years in DevOps, SRE, or MLOps and understand "
            "GPU memory constraints, streaming token protocols, and low-latency infrastructure."
        ),
        "emerging_context": (
            "Specialized operational domain tackling the unique challenges of generative AI: vLLM/TGI serving fabrics, "
            "GPU cluster utilization, prompt caching, quantization, latency benchmarking, and automated model rollback."
        ),
    },
    "ai-evaluation-engineer": {
        "maturity": "emerging",
        "entry_level_accessible": False,
        "accessibility_guidance": (
            "Requires foundational expertise in experimental design, statistics, benchmark curation, and NLP evaluation. "
            "Not an entry-level prompt writing role."
        ),
        "emerging_context": (
            "Emerged directly from the challenge of validating non-deterministic model behavior. AI Evaluation Engineers "
            "curate gold-standard ground-truth datasets, design rubric-based LLM-as-a-judge pipelines, and run red-teaming."
        ),
    },
    "ai-infrastructure-engineer": {
        "maturity": "emerging",
        "entry_level_accessible": False,
        "accessibility_guidance": (
            "Strictly a senior-level role. Requires multi-year background in Linux kernel tuning, distributed storage, "
            "InfiniBand/RDMA networking fabrics, and large-scale GPU orchestration."
        ),
        "emerging_context": (
            "One of the highest-demand and most technically demanding emerging roles in the industry. AI Infrastructure "
            "Engineers build the distributed training fabrics and high-throughput compute systems that train foundation models."
        ),
    },
}


def enrich_skill_object(skill_id: str) -> Dict[str, Any]:
    """Return enriched skill information with canonical name, category, and study estimate."""
    meta = get_skill_meta(skill_id)
    return {
        "id": skill_id,
        "canonical_name": meta.get("canonical", skill_id.replace("_", " ").title()),
        "category": meta.get("category", "Domain"),
        "importance": meta.get("importance", "medium"),
        "estimated_hours": meta.get("estimated_hours", 25),
    }


def list_roles_explorer(
    family: Optional[str] = None,
    level: Optional[str] = None,
    maturity: Optional[str] = None,
    query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search and filter roles across the career taxonomy.
    """
    all_roles = skill_analyzer.list_roles()
    results = []

    for role_summary in all_roles:
        role_id = role_summary["id"]
        maturity_meta = ROLE_MATURITY_REGISTRY.get(role_id, {
            "maturity": "emerging",
            "entry_level_accessible": False,
            "accessibility_guidance": "Consult prerequisites.",
            "emerging_context": None,
        })

        # Apply filters
        if family and role_summary["role_family"].lower() != family.lower():
            continue
        if level and role_summary["experience_level"].lower() != level.lower():
            continue
        if maturity and maturity_meta["maturity"].lower() != maturity.lower():
            continue
        if query:
            q = query.lower()
            text_match = (
                q in role_summary["canonical_title"].lower()
                or q in role_summary["description"].lower()
                or q in role_id
            )
            if not text_match:
                continue

        profile = skill_analyzer.get_role(role_id) or {}
        core_skill_names = [
            get_skill_meta(sid).get("canonical", sid.replace("_", " ").title())
            for sid in profile.get("core_skills", [])[:4]
        ]

        item = {
            **role_summary,
            "maturity": maturity_meta["maturity"],
            "entry_level_accessible": maturity_meta["entry_level_accessible"],
            "accessibility_guidance": maturity_meta["accessibility_guidance"],
            "emerging_context": maturity_meta["emerging_context"],
            "highlight_skills": core_skill_names,
            "core_skill_count": len(profile.get("core_skills", [])),
        }
        results.append(item)

    return results


def get_role_full_details(role_id: str) -> Optional[Dict[str, Any]]:
    """
    Return comprehensive details for a single role:
    * Responsibilities
    * Prerequisites
    * Core skills (enriched)
    * Optional/recommended skills (enriched)
    * Example projects
    * Maturity & emergence guidance
    * Related roles
    * Market summary (evidence-aware)
    """
    profile = skill_analyzer.get_role(role_id)
    if not profile:
        return None

    maturity_meta = ROLE_MATURITY_REGISTRY.get(role_id, {
        "maturity": "emerging",
        "entry_level_accessible": False,
        "accessibility_guidance": "Specialized role.",
        "emerging_context": None,
    })

    # Enrich skills
    enriched_core = [enrich_skill_object(sid) for sid in profile.get("core_skills", [])]
    enriched_recommended = [enrich_skill_object(sid) for sid in profile.get("recommended_skills", [])]
    enriched_optional = [enrich_skill_object(sid) for sid in profile.get("optional_skills", [])]
    enriched_prereqs = [enrich_skill_object(sid) for sid in profile.get("prerequisites", [])]

    # Compute top related roles
    related = get_related_roles(role_id, top_n=3)

    # Market insights
    market_summary = market_insights.get_market_summary(role_id)

    return {
        **profile,
        "maturity": maturity_meta["maturity"],
        "entry_level_accessible": maturity_meta["entry_level_accessible"],
        "accessibility_guidance": maturity_meta["accessibility_guidance"],
        "emerging_context": maturity_meta["emerging_context"],
        "core_skills_details": enriched_core,
        "recommended_skills_details": enriched_recommended,
        "optional_skills_details": enriched_optional,
        "prerequisites_details": enriched_prereqs,
        "related_roles": related,
        "market_summary": market_summary,
    }


def get_related_roles(role_id: str, top_n: int = 4) -> List[Dict[str, Any]]:
    """
    Suggest related roles based on Jaccard skill overlap and role family relevance.
    """
    source_profile = skill_analyzer.get_role(role_id)
    if not source_profile:
        return []

    source_core = set(source_profile.get("core_skills", []))
    source_all = source_core.union(
        set(source_profile.get("recommended_skills", [])),
        set(source_profile.get("optional_skills", [])),
    )

    all_roles = skill_analyzer.list_roles()
    candidates = []

    for other in all_roles:
        other_id = other["id"]
        if other_id == role_id:
            continue

        other_profile = skill_analyzer.get_role(other_id)
        if not other_profile:
            continue

        target_core = set(other_profile.get("core_skills", []))
        target_all = target_core.union(
            set(other_profile.get("recommended_skills", [])),
            set(other_profile.get("optional_skills", [])),
        )

        # Core overlap & Jaccard index
        shared_core = source_core.intersection(target_core)
        union_core = source_core.union(target_core)
        jaccard_core = (len(shared_core) / len(union_core) * 100) if union_core else 0.0

        # All-skills overlap
        shared_all = source_all.intersection(target_all)
        union_all = source_all.union(target_all)
        jaccard_all = (len(shared_all) / len(union_all) * 100) if union_all else 0.0

        # Blend core overlap (70%) and overall overlap (30%)
        composite_score = round(0.7 * jaccard_core + 0.3 * jaccard_all, 1)

        # Bridge skills: core in target but not in source
        bridge_skill_ids = sorted(list(target_core - source_core))
        bridge_skills = [enrich_skill_object(sid) for sid in bridge_skill_ids]

        shared_skill_objs = [enrich_skill_object(sid) for sid in sorted(list(shared_core))]

        maturity_meta = ROLE_MATURITY_REGISTRY.get(other_id, {
            "maturity": "emerging",
            "entry_level_accessible": False,
        })

        candidates.append({
            "role_id": other_id,
            "canonical_title": other_profile.get("canonical_title", other_id),
            "role_family": other_profile.get("role_family", ""),
            "experience_level": other_profile.get("experience_level", ""),
            "maturity": maturity_meta["maturity"],
            "entry_level_accessible": maturity_meta["entry_level_accessible"],
            "overlap_percentage": composite_score,
            "shared_core_count": len(shared_core),
            "shared_skills": shared_skill_objs,
            "bridge_skills": bridge_skills,
        })

    # Sort primarily by composite score descending
    candidates.sort(key=lambda c: c["overlap_percentage"], reverse=True)
    return candidates[:top_n]


def compare_roles(
    role_a_id: str,
    role_b_id: str,
    user_skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Perform full bidirectional comparison between two roles:
    * Shared core skills
    * Skills unique to Role A
    * Skills unique to Role B
    * Overlap percentage (Jaccard similarity on core skills)
    * Transition bridge from A -> B (skills to learn, estimated hours)
    * Transition bridge from B -> A (skills to learn, estimated hours)
    * Seniority, accessibility, and maturity distinctions
    * User-specific skill match, possessed vs missing, and transferable skills (if user_skills provided)
    """
    prof_a = skill_analyzer.get_role(role_a_id)
    prof_b = skill_analyzer.get_role(role_b_id)

    if not prof_a:
        raise KeyError(f"Role '{role_a_id}' not found.")
    if not prof_b:
        raise KeyError(f"Role '{role_b_id}' not found.")

    core_a: Set[str] = set(prof_a.get("core_skills", []))
    core_b: Set[str] = set(prof_b.get("core_skills", []))

    all_a: Set[str] = core_a.union(
        set(prof_a.get("recommended_skills", [])),
        set(prof_a.get("optional_skills", [])),
    )
    all_b: Set[str] = core_b.union(
        set(prof_b.get("recommended_skills", [])),
        set(prof_b.get("optional_skills", [])),
    )

    shared_core = core_a.intersection(core_b)
    unique_to_a = core_a - core_b
    unique_to_b = core_b - core_a

    union_core = core_a.union(core_b)
    overlap_score = round(len(shared_core) / len(union_core) * 100, 1) if union_core else 0.0

    # Transition A -> B: needs unique_to_b core skills
    bridge_a_to_b = [enrich_skill_object(s) for s in sorted(unique_to_b)]
    hours_a_to_b = sum(s["estimated_hours"] for s in bridge_a_to_b)

    # Transition B -> A: needs unique_to_a core skills
    bridge_b_to_a = [enrich_skill_object(s) for s in sorted(unique_to_a)]
    hours_b_to_a = sum(s["estimated_hours"] for s in bridge_b_to_a)

    meta_a = ROLE_MATURITY_REGISTRY.get(role_a_id, {"maturity": "emerging", "entry_level_accessible": False})
    meta_b = ROLE_MATURITY_REGISTRY.get(role_b_id, {"maturity": "emerging", "entry_level_accessible": False})

    # User personalized skill alignment
    user_skill_set: Set[str] = set()
    if user_skills:
        for item in user_skills:
            if isinstance(item, str) and item.strip():
                user_skill_set.add(item.strip().lower())

    def _is_possessed(sid: str) -> bool:
        meta = get_skill_meta(sid)
        canonical = meta.get("canonical", sid.replace("_", " ")).lower()
        if sid.lower() in user_skill_set or canonical in user_skill_set:
            return True
        for alias in meta.get("aliases", []):
            if alias.lower() in user_skill_set:
                return True
        return False

    possessed_a = [enrich_skill_object(s) for s in sorted(core_a) if _is_possessed(s)]
    needed_a = [enrich_skill_object(s) for s in sorted(core_a) if not _is_possessed(s)]
    readiness_a = round(len(possessed_a) / len(core_a) * 100, 1) if core_a else 0.0

    possessed_b = [enrich_skill_object(s) for s in sorted(core_b) if _is_possessed(s)]
    needed_b = [enrich_skill_object(s) for s in sorted(core_b) if not _is_possessed(s)]
    readiness_b = round(len(possessed_b) / len(core_b) * 100, 1) if core_b else 0.0

    transferable_skills = [enrich_skill_object(s) for s in sorted(shared_core) if _is_possessed(s)]
    high_leverage_skills = [enrich_skill_object(s) for s in sorted(shared_core) if not _is_possessed(s)]

    return {
        "role_a": {
            "id": role_a_id,
            "canonical_title": prof_a.get("canonical_title", role_a_id),
            "role_family": prof_a.get("role_family", ""),
            "experience_level": prof_a.get("experience_level", ""),
            "maturity": meta_a["maturity"],
            "entry_level_accessible": meta_a["entry_level_accessible"],
            "core_skills": [enrich_skill_object(s) for s in prof_a.get("core_skills", [])],
        },
        "role_b": {
            "id": role_b_id,
            "canonical_title": prof_b.get("canonical_title", role_b_id),
            "role_family": prof_b.get("role_family", ""),
            "experience_level": prof_b.get("experience_level", ""),
            "maturity": meta_b["maturity"],
            "entry_level_accessible": meta_b["entry_level_accessible"],
            "core_skills": [enrich_skill_object(s) for s in prof_b.get("core_skills", [])],
        },
        "shared_core_skills": [enrich_skill_object(s) for s in sorted(shared_core)],
        "unique_to_role_a": [enrich_skill_object(s) for s in sorted(unique_to_a)],
        "unique_to_role_b": [enrich_skill_object(s) for s in sorted(unique_to_b)],
        "overlap_percentage": overlap_score,
        "shared_core_count": len(shared_core),
        "total_unique_core_count": len(union_core),
        "transition_a_to_b": {
            "target_role": prof_b.get("canonical_title", role_b_id),
            "bridge_skills": bridge_a_to_b,
            "bridge_skills_count": len(bridge_a_to_b),
            "estimated_hours": hours_a_to_b,
        },
        "transition_b_to_a": {
            "target_role": prof_a.get("canonical_title", role_a_id),
            "bridge_skills": bridge_b_to_a,
            "bridge_skills_count": len(bridge_b_to_a),
            "estimated_hours": hours_b_to_a,
        },
        "user_comparison": {
            "has_user_skills": len(user_skill_set) > 0,
            "user_skills_count": len(user_skill_set),
            "role_a": {
                "possessed_skills": possessed_a,
                "needed_skills": needed_a,
                "readiness_percent": readiness_a,
            },
            "role_b": {
                "possessed_skills": possessed_b,
                "needed_skills": needed_b,
                "readiness_percent": readiness_b,
            },
            "transferable_skills": transferable_skills,
            "high_leverage_skills": high_leverage_skills,
        },
    }

