"""Skill analyser: gap analysis of a resume against a target role profile.

Given extracted resume text and a role ID, this module:
1. Detects all skills present in the text via ``skill_extractor``.
2. Classifies them against the role's core / recommended / optional tiers.
3. Computes a coverage percentage and identifies priority skill gaps.

Coverage formula
----------------
    coverage_percent = matched_core_skills / total_core_skills × 100

Limitation disclaimer
---------------------
The coverage score reflects how many *explicitly named* core skills were found in
the supplied text.  It is NOT a hiring probability, a proficiency measure, or a
guarantee of interview success.  Many factors (experience depth, projects, culture
fit, interview performance) are outside the scope of this analysis.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from app.schemas.analysis import AnalysisResult, SkillGap, SkillMatch
from app.services.skill_extractor import IMPORTANCE_ORDER, extract_skills, get_skill_meta

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).parent.parent / "data"
_ROLES_PATH = _DATA_DIR / "role_profiles.json"

_COVERAGE_NOTE = (
    "Coverage reflects the proportion of explicitly named core skills found in the "
    "supplied text. It is NOT a hiring probability, proficiency score, or guarantee "
    "of interview success. Employer requirements vary; treat this as a self-assessment "
    "guide only."
)


def _load_role_profiles() -> Dict[str, dict]:
    """Load role_profiles.json once at module import time."""
    with open(_ROLES_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("roles", {})


_ROLE_PROFILES: Dict[str, dict] = _load_role_profiles()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_roles() -> List[dict]:
    """Return a summary list of all role profiles."""
    summaries = []
    for role_id, profile in _ROLE_PROFILES.items():
        summaries.append(
            {
                "id": role_id,
                "canonical_title": profile.get("canonical_title", role_id),
                "role_family": profile.get("role_family", ""),
                "experience_level": profile.get("experience_level", ""),
                "entry_level_accessible": profile.get("entry_level_accessible", False),
                "description": profile.get("description", ""),
            }
        )
    return summaries


def get_role(role_id: str) -> dict | None:
    """Return the full profile for *role_id*, or None if not found."""
    return _ROLE_PROFILES.get(role_id)


def analyze(text: str, role_id: str) -> AnalysisResult:
    """
    Perform skill-gap analysis of *text* against the role identified by *role_id*.

    Parameters
    ----------
    text:
        Free-form resume text.
    role_id:
        A role identifier that must exist in ``role_profiles.json``.

    Returns
    -------
    AnalysisResult
        Structured analysis with matched skills, gaps, and coverage metric.

    Raises
    ------
    KeyError
        If *role_id* is not found in the role catalogue (caller should convert to 404).
    """
    profile = _ROLE_PROFILES.get(role_id)
    if profile is None:
        raise KeyError(f"Role '{role_id}' not found in role catalogue.")

    role_title: str = profile.get("canonical_title", role_id)
    core_skills: List[str] = profile.get("core_skills", [])
    recommended_skills: List[str] = profile.get("recommended_skills", [])
    optional_skills: List[str] = profile.get("optional_skills", [])

    # All skills detected anywhere in the text
    detected: List[SkillMatch] = extract_skills(text)
    detected_ids: set[str] = {sm.skill_id for sm in detected}

    # --- Classify matched / uncertain ----------------------------------------
    core_set = set(core_skills)
    recommended_set = set(recommended_skills)
    optional_set = set(optional_skills)

    matched_skills: List[SkillMatch] = []      # in text AND in core
    uncertain_skills: List[SkillMatch] = []    # in text AND in recommended/optional (not core)

    for sm in detected:
        if sm.skill_id in core_set:
            matched_skills.append(sm)
        elif sm.skill_id in recommended_set or sm.skill_id in optional_set:
            uncertain_skills.append(sm)

    matched_core_ids: set[str] = {sm.skill_id for sm in matched_skills}

    # --- Missing core skills -------------------------------------------------
    missing_skills: List[SkillGap] = []
    for skill_id in core_skills:
        if skill_id not in matched_core_ids:
            meta = get_skill_meta(skill_id)
            missing_skills.append(
                SkillGap(
                    skill_id=skill_id,
                    canonical_name=meta.get("canonical", skill_id),
                    category=meta.get("category", ""),
                    importance=meta.get("importance", "medium"),
                    estimated_hours=meta.get("estimated_hours", 0),
                )
            )

    # --- Coverage metric -----------------------------------------------------
    total_core = len(core_skills)
    matched_core_count = len(matched_skills)
    coverage = (matched_core_count / total_core * 100.0) if total_core > 0 else 0.0

    # --- Priority gaps (top 5 by importance) ---------------------------------
    priority_gaps = sorted(
        missing_skills,
        key=lambda g: IMPORTANCE_ORDER.get(g.importance, 99),
    )[:5]

    return AnalysisResult(
        role_id=role_id,
        role_title=role_title,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        uncertain_skills=uncertain_skills,
        coverage_percent=round(coverage, 2),
        coverage_note=_COVERAGE_NOTE,
        total_core_skills=total_core,
        matched_core_skills=matched_core_count,
        priority_gaps=priority_gaps,
    )

