"""Job description analyzer: compares resume text against a pasted job description.

Key Architectural Guarantees:
------------------------------
1. Decoupled from Curated Profiles: Operates strictly on user-supplied text.
   Never infers or injects requirements from curated role profiles.
2. Stated Distinction Only: Distinguishes required vs preferred skills only where
   structural or lexical wording explicitly supports it.
3. No Synthetic Data: Never generates fake market stats, salaries, or probabilities.
4. Comprehensive Caveats: Transparently communicates NLP and text-matching limits.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

from app.schemas.analysis import SkillMatch
from app.schemas.job_description import (
    ExperienceRequirement,
    JobDescriptionAnalysisResult,
    MarketSummaryMetadata,
)
from app.services.skill_extractor import extract_skills, get_skill_meta

# ---------------------------------------------------------------------------
# Section Boundary Patterns
# ---------------------------------------------------------------------------

_REQUIRED_HEADER_PATTERN = re.compile(
    r"^(?:#+\s*)?(?:minimum|basic|core|mandatory)?\s*"
    r"(?:qualifications|requirements|must[\s-]haves?|what\s+you(?:(?:\'ll|\swill)?\s+need|bring)|"
    r"required(?:\s+skills|\s+experience|\s+qualifications)?)\s*[:?]?$",
    re.IGNORECASE,
)

_PREFERRED_HEADER_PATTERN = re.compile(
    r"^(?:#+\s*)?(?:preferred|bonus|nice[\s-]to[\s-]haves?|desired|optional|"
    r"what\s+(?:gives\s+you\s+an\s+edge|we\'d\s+love\s+to\s+see)|plus(?:es)?|good\s+to\s+have)\s*"
    r"(?:qualifications|skills|experience)?\s*[:?]?$",
    re.IGNORECASE,
)

_GENERAL_HEADER_PATTERN = re.compile(
    r"^(?:#+\s*)?(?:responsibilities|about\s+(?:the\s+role|us|the\s+team|company)|"
    r"what\s+you(?:(?:\'ll|\swill)\s+do)|duties|overview|summary|benefits|perks|compensation)\s*[:?]?$",
    re.IGNORECASE,
)

_INLINE_REQUIRED_CUE = re.compile(
    r"\b(?:must\s+have|required|requirement|minimum(?:\s+of)?|essential)\b",
    re.IGNORECASE,
)

_INLINE_PREFERRED_CUE = re.compile(
    r"\b(?:preferred|nice\s+to\s+have|bonus|plus|desired|optional|an\s+asset)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Experience & Degree Patterns
# ---------------------------------------------------------------------------

_TENURE_PATTERNS = [
    # "5+ years of experience in Python" or "3 to 5 years experience with Docker"
    re.compile(
        r"((?:at\s+least|minimum\s+of\s+)?(\d+(?:\.\d+)?)\s*(?:\+|plus)?\s*(?:to|-)\s*(\d+(?:\.\d+)?)\s*(?:\+|plus)?\s*years?(?:\s+of)?(?:\s+experience)?(?:\s+(?:in|with|of|using)\s+([A-Za-z0-9_\+#\.\s]{2,30}))?)",
        re.IGNORECASE,
    ),
    # "3+ years of experience with PostgreSQL" or "5 years experience"
    re.compile(
        r"((?:at\s+least|minimum\s+of\s+)?(\d+(?:\.\d+)?)\s*(?:\+|plus)\s*years?(?:\s+of)?(?:\s+experience)?(?:\s+(?:in|with|of|using)\s+([A-Za-z0-9_\+#\.\s]{2,30}))?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"((?:at\s+least|minimum\s+of\s+)?(\d+(?:\.\d+)?)\s+years?(?:\s+of)?\s+experience(?:\s+(?:in|with|of|using)\s+([A-Za-z0-9_\+#\.\s]{2,30}))?)",
        re.IGNORECASE,
    ),
]

_EDUCATION_PATTERN = re.compile(
    r"((?:bachelor(?:\'s)?|master(?:\'s)?|phd|doctorate|b\.?s\.?|m\.?s\.?)\s*(?:degree)?(?:\s+in\s+([A-Za-z0-9_\s]{2,40}))?)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Standard Caveats
# ---------------------------------------------------------------------------

DEFAULT_CAVEATS: List[str] = [
    "Requirements and skills are extracted purely from the supplied text using pattern matching; no unstated employer requirements are inferred.",
    "Section distinction (required vs preferred) depends on explicit structural headers (e.g. 'Requirements', 'Nice to have') or inline cues in the job description.",
    "Absence of a skill in a resume indicates lack of explicit textual mention, not necessarily absence of candidate capability.",
    "Presence of a skill in a resume does not prove depth of operational experience or production proficiency.",
    "Job descriptions often reflect aspirational 'wish lists' rather than rigid prerequisites.",
    "This analysis generates a textual alignment score and does NOT represent an employer hiring probability or algorithmic candidate ranking.",
]


# ---------------------------------------------------------------------------
# Section Segmenter
# ---------------------------------------------------------------------------


def segment_job_description(text: str) -> List[Tuple[str, str]]:
    """
    Segment job description text into distinct structural sections.

    Returns a list of (section_type, text_content) tuples where section_type
    is one of: 'required', 'preferred', or 'general'.
    """
    lines = text.splitlines()
    sections: List[Tuple[str, str]] = []

    current_type = "general"
    current_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_lines:
                current_lines.append(line)
            continue

        # Check for section header transitions
        if len(stripped) <= 65 and not stripped.startswith("-") and not stripped.startswith("*"):
            if _REQUIRED_HEADER_PATTERN.match(stripped):
                if current_lines:
                    sections.append((current_type, "\n".join(current_lines)))
                    current_lines = []
                current_type = "required"
                continue
            elif _PREFERRED_HEADER_PATTERN.match(stripped):
                if current_lines:
                    sections.append((current_type, "\n".join(current_lines)))
                    current_lines = []
                current_type = "preferred"
                continue
            elif _GENERAL_HEADER_PATTERN.match(stripped):
                if current_lines:
                    sections.append((current_type, "\n".join(current_lines)))
                    current_lines = []
                current_type = "general"
                continue

        current_lines.append(line)

    if current_lines:
        sections.append((current_type, "\n".join(current_lines)))

    return sections


# ---------------------------------------------------------------------------
# Experience Requirement Extractor
# ---------------------------------------------------------------------------


def extract_experience_requirements(text: str) -> List[ExperienceRequirement]:
    """Extract explicit tenure (years of experience) and degree requirements from text."""
    requirements: List[ExperienceRequirement] = []
    seen_raw: Set[str] = set()

    for pattern in _TENURE_PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group(1).strip()
            # Clean up trailing punctuation
            raw = raw.rstrip(".,;:")
            if raw.lower() in seen_raw:
                continue
            seen_raw.add(raw.lower())

            # Determine numerical years
            years_val: Optional[float] = None
            try:
                # Group 2 is the primary numeric string in our tenure patterns
                years_val = float(match.group(2))
            except (IndexError, TypeError, ValueError):
                pass

            topic: Optional[str] = None
            # If pattern captured a topic group
            groups = match.groups()
            if len(groups) >= 4 and groups[-1]:
                clean_topic = groups[-1].strip().rstrip(".,;:")
                if len(clean_topic) > 1:
                    topic = clean_topic

            requirements.append(
                ExperienceRequirement(
                    raw_text=raw,
                    years=years_val,
                    topic=topic,
                    requirement_type="tenure",
                )
            )

    for match in _EDUCATION_PATTERN.finditer(text):
        raw = match.group(1).strip().rstrip(".,;:")
        if raw.lower() in seen_raw:
            continue
        seen_raw.add(raw.lower())

        topic: Optional[str] = None
        if len(match.groups()) >= 2 and match.group(2):
            topic = match.group(2).strip().rstrip(".,;:")

        requirements.append(
            ExperienceRequirement(
                raw_text=raw,
                years=None,
                topic=topic,
                requirement_type="education",
            )
        )

    return requirements


# ---------------------------------------------------------------------------
# Main Analysis Engine
# ---------------------------------------------------------------------------


def analyze_job_description(
    resume_text: str,
    job_description_text: str,
) -> JobDescriptionAnalysisResult:
    """
    Perform comparative skill-gap analysis between a candidate's resume and a job description.

    Guarantees:
    - Never queries curated role profiles.
    - Evaluates required vs preferred distinctions only when explicitly present in the text.
    - Provides explicit caveats regarding match metric interpretation.
    """
    # 1. Extract all skills from the entire JD and resume
    all_jd_skills = extract_skills(job_description_text)
    resume_skills = extract_skills(resume_text)

    resume_skill_ids = {s.skill_id for s in resume_skills}
    resume_categories = {s.category for s in resume_skills if s.category}

    # 2. Segment JD to identify explicitly stated required vs preferred skills
    sections = segment_job_description(job_description_text)

    required_ids: Set[str] = set()
    preferred_ids: Set[str] = set()

    has_structural_sections = any(st in ("required", "preferred") for st, _ in sections)

    if has_structural_sections:
        for sec_type, sec_text in sections:
            sec_skills = extract_skills(sec_text)
            for skill in sec_skills:
                if sec_type == "required":
                    required_ids.add(skill.skill_id)
                elif sec_type == "preferred":
                    preferred_ids.add(skill.skill_id)
    else:
        # Check inline line-level cues if no structural headers exist
        for line in job_description_text.splitlines():
            line_skills = extract_skills(line)
            if not line_skills:
                continue
            if _INLINE_REQUIRED_CUE.search(line):
                for skill in line_skills:
                    required_ids.add(skill.skill_id)
            elif _INLINE_PREFERRED_CUE.search(line):
                for skill in line_skills:
                    preferred_ids.add(skill.skill_id)

    # Required takes precedence if a skill was caught in both
    preferred_ids = preferred_ids - required_ids

    # 3. Categorize extracted skills
    matched_skills: List[SkillMatch] = []
    missing_skills: List[SkillMatch] = []
    required_skills: List[SkillMatch] = []
    preferred_skills: List[SkillMatch] = []

    for skill in all_jd_skills:
        if skill.skill_id in resume_skill_ids:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

        if skill.skill_id in required_ids:
            required_skills.append(skill)
        elif skill.skill_id in preferred_ids:
            preferred_skills.append(skill)

    # 4. Potentially Related Skills:
    # Resume skills that are in the same category as missing skills, OR
    # resume skills matched against the preferred qualification tier.
    missing_categories = {s.category for s in missing_skills if s.category}
    potentially_related: List[SkillMatch] = []
    seen_related_ids: Set[str] = set()

    for r_skill in resume_skills:
        # Candidate has a skill matching preferred tier
        if r_skill.skill_id in preferred_ids and r_skill.skill_id not in seen_related_ids:
            potentially_related.append(r_skill)
            seen_related_ids.add(r_skill.skill_id)
        # Candidate has an alternative skill in the same domain/category as a missing required skill
        elif r_skill.category in missing_categories and r_skill.skill_id not in {s.skill_id for s in all_jd_skills}:
            if r_skill.skill_id not in seen_related_ids:
                potentially_related.append(r_skill)
                seen_related_ids.add(r_skill.skill_id)

    # 5. Experience requirements
    experience_reqs = extract_experience_requirements(job_description_text)

    # 6. Coverage calculation
    # If explicit required skills exist, calculate coverage against required skills.
    # Otherwise, calculate coverage against all extracted skills.
    if required_skills:
        total_eval_skills = len(required_skills)
        matched_eval_skills = sum(1 for s in required_skills if s.skill_id in resume_skill_ids)
    else:
        total_eval_skills = len(all_jd_skills)
        matched_eval_skills = len(matched_skills)

    coverage = (matched_eval_skills / total_eval_skills * 100.0) if total_eval_skills > 0 else 0.0

    # Build contextual caveats list
    caveats = list(DEFAULT_CAVEATS)
    if not required_skills and not preferred_skills:
        caveats.insert(
            0,
            "The job description did not contain recognizable 'Required' vs 'Preferred' sections. All extracted skills are treated uniformly as general qualifications.",
        )

    return JobDescriptionAnalysisResult(
        extracted_skills=all_jd_skills,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        potentially_related_skills=potentially_related,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        experience_requirements=experience_reqs,
        coverage_percent=round(coverage, 2),
        total_jd_skills=len(all_jd_skills),
        matched_count=len(matched_skills),
        missing_count=len(missing_skills),
        caveats=caveats,
    )


# ---------------------------------------------------------------------------
# Permitted Market Data Ingestion Contract (Architecture)
# ---------------------------------------------------------------------------


def create_market_summary_record(
    source: str,
    collection_date: str,
    geography: str,
    sample_size: int,
    skill_detection_method: str = "SkillGraph-Regex-v1.0",
) -> MarketSummaryMetadata:
    """
    Factory function ensuring that all historical market summary records
    satisfy the mandatory provenance and compliance contract.
    """
    return MarketSummaryMetadata(
        source=source,
        collection_date=collection_date,
        geography=geography,
        sample_size=sample_size,
        skill_detection_method=skill_detection_method,
    )

