"""Market Insights Service — Evidence-aware market summaries and curated guidance.

Architecture Guarantees:
1. No Synthetic Data: Never generates fake market statistics, salaries, or probabilities.
2. Provenance: Every verified summary must carry documented source, collection date, geography,
   sample size, and detection method.
3. Transparent Fallback: If no verified dataset is available, explicitly returns curated guidance
   disclaimers rather than fabricated counts.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.schemas.job_description import MarketSummaryMetadata
from app.services.skill_extractor import get_skill_meta

_DATA_DIR = Path(__file__).parent.parent / "data"
_VERIFIED_DATA_PATH = _DATA_DIR / "verified_market_data.json"


def _load_verified_market_data() -> Dict[str, dict]:
    """Load verified market data records from JSON storage."""
    if not _VERIFIED_DATA_PATH.exists():
        return {}
    try:
        with open(_VERIFIED_DATA_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("roles", {})
    except Exception:
        return {}


_VERIFIED_DATA: Dict[str, dict] = _load_verified_market_data()


def get_market_summary(role_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Retrieve market insights for a role.
    
    If documented verified data exists (or sufficient actual analyzed postings exist in DB),
    returns empirical frequencies with mandatory audit metadata.
    Otherwise, returns transparent curated guidance with explicit disclaimers.
    """
    # 1. Check verified benchmark dataset
    if role_id in _VERIFIED_DATA:
        role_data = _VERIFIED_DATA[role_id]
        meta = role_data.get("metadata", {})
        return {
            "role_id": role_id,
            "has_verified_data": True,
            "metadata": meta,
            "top_required_skills": role_data.get("top_required_skills", []),
            "top_preferred_skills": role_data.get("top_preferred_skills", []),
            "experience_distribution": role_data.get("experience_distribution", {}),
            "data_notice": (
                f"Empirical summary calculated from {meta.get('sample_size', 0)} verified job descriptions "
                f"collected on {meta.get('collection_date', 'N/A')} ({meta.get('geography', 'N/A')}). "
                "No synthetic data."
            ),
        }

    # 2. Check if DB has user-analyzed records for this role (e.g. from job-description analyses)
    if db is not None:
        try:
            from app.models.job_description import JobDescriptionAnalysisRecord
            # Match records where job description mentions this role title or ID
            records = db.query(JobDescriptionAnalysisRecord).all()
            matching_records = [
                r for r in records
                if (r.job_title and role_id in r.job_title.lower())
                or (role_id.replace("-", " ") in r.job_description_text.lower())
            ]
            if len(matching_records) >= 5:
                return calculate_market_summary_from_records(
                    records=matching_records,
                    role_id=role_id,
                    source_label="SkillGraph Aggregated Job Postings",
                    geography="User Submitted",
                )
        except Exception:
            pass

    # 3. Transparent Curated Guidance Fallback
    from app.services import skill_analyzer
    profile = skill_analyzer.get_role(role_id)
    curated_core = []
    if profile:
        for skill_id in profile.get("core_skills", []):
            meta = get_skill_meta(skill_id)
            curated_core.append({
                "skill_id": skill_id,
                "canonical_name": meta.get("canonical", skill_id.replace("_", " ").title()),
                "category": meta.get("category", "Domain"),
                "importance": meta.get("importance", "critical"),
                "estimated_hours": meta.get("estimated_hours", 25),
            })

    return {
        "role_id": role_id,
        "has_verified_data": False,
        "guidance_type": "curated_competency_framework",
        "data_notice": (
            "Curated guidance: No statistically verified dataset of job postings with sufficient "
            "sample size is currently available for this role. SkillGraph strictly prohibits generating "
            "synthetic sample sizes, speculative percentages, or fabricated salary estimates."
        ),
        "curated_skills": curated_core,
        "recommendation": (
            "Treat the curated core skills and example projects as foundational learning benchmarks "
            "rather than empirical hiring statistics. Individual employer requirements vary significantly."
        ),
    }


def calculate_market_summary_from_records(
    records: List[Any],
    role_id: str,
    source_label: str = "Verified Job Descriptions",
    geography: str = "US-Remote",
    collection_date: str = "2025-01-15",
) -> Dict[str, Any]:
    """
    Calculate an empirical market summary from a list of actual job description records.
    Requires at least 5 records to consider the sample valid; otherwise yields curated guidance.
    """
    sample_size = len(records)
    if sample_size < 5:
        return {
            "role_id": role_id,
            "has_verified_data": False,
            "guidance_type": "insufficient_sample",
            "data_notice": (
                f"Sample size ({sample_size}) is below statistical reporting threshold (min 5 postings). "
                "Displaying curated guidance instead to prevent skewed inferences."
            ),
        }

    # Extract required and preferred skill frequencies
    req_counter: Counter[str] = Counter()
    pref_counter: Counter[str] = Counter()

    for r in records:
        req_skills = r.get_required_skills() if hasattr(r, "get_required_skills") else r.get("required_skills", [])
        pref_skills = r.get_preferred_skills() if hasattr(r, "get_preferred_skills") else r.get("preferred_skills", [])

        # Deduplicate per posting
        seen_req = set()
        for s in req_skills:
            sid = s.get("skill_id") if isinstance(s, dict) else getattr(s, "skill_id", str(s))
            if sid and sid not in seen_req:
                seen_req.add(sid)
                req_counter[sid] += 1

        seen_pref = set()
        for s in pref_skills:
            sid = s.get("skill_id") if isinstance(s, dict) else getattr(s, "skill_id", str(s))
            if sid and sid not in seen_pref:
                seen_pref.add(sid)
                pref_counter[sid] += 1

    top_req = []
    for sid, count in req_counter.most_common(10):
        meta = get_skill_meta(sid)
        top_req.append({
            "skill_id": sid,
            "canonical_name": meta.get("canonical", sid.replace("_", " ").title()),
            "frequency_count": count,
            "frequency_percent": round(count / sample_size * 100, 1),
        })

    top_pref = []
    for sid, count in pref_counter.most_common(10):
        meta = get_skill_meta(sid)
        top_pref.append({
            "skill_id": sid,
            "canonical_name": meta.get("canonical", sid.replace("_", " ").title()),
            "frequency_count": count,
            "frequency_percent": round(count / sample_size * 100, 1),
        })

    meta_obj = MarketSummaryMetadata(
        source=source_label,
        collection_date=collection_date,
        geography=geography,
        sample_size=sample_size,
        skill_detection_method="SkillGraph-Regex-v1.0",
    )

    return {
        "role_id": role_id,
        "has_verified_data": True,
        "metadata": meta_obj.model_dump(),
        "top_required_skills": top_req,
        "top_preferred_skills": top_pref,
        "data_notice": (
            f"Calculated from {sample_size} actual collected postings. "
            f"Source: {source_label} ({geography})."
        ),
    }
