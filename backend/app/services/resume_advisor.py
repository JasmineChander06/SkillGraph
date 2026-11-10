"""Resume Advisor & Quality Critique Engine.

Audits candidate resumes across 4 objective engineering dimensions:
1. Quantification & Impact (metrics, numbers, %, $)
2. Action Verb Strength (active leadership verbs vs passive voice)
3. Technical Keyword & Role Density (extracted skills via skill_extractor)
4. Brevity & Fluff Elimination (penalizing cliches, buzzwords, and vague phrases)
"""

from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple

from app.schemas.resume_advisor import (
    BulletImprovement,
    DimensionScores,
    ResumeCritiqueResponse,
)
from app.services.skill_extractor import extract_skills

# Cliches and vague buzzwords that weaken technical resumes
CLICHE_PATTERNS = [
    (r"\bhard[\s-]?work(ing|er)\b", "hardworking"),
    (r"\bteam[\s-]?player\b", "team player"),
    (r"\bdetail[\s-]?oriented\b", "detail-oriented"),
    (r"\b(fast|quick)[\s-]?learner\b", "fast learner"),
    (r"\bself[\s-]?motivat(ed|ion)\b", "self-motivated"),
    (r"\bgo[\s-]?getter\b", "go-getter"),
    (r"\bresults?[\s-]?driven\b", "results-driven"),
    (r"\bpassionate\b", "passionate"),
    (r"\benthusiastic\b", "enthusiastic"),
    (r"\bdynamic\b", "dynamic"),
    (r"\bsynerg(y|ies|istic)\b", "synergy"),
    (r"\bthink(ing)?\s+outside\s+the\s+box\b", "thinking outside the box"),
    (r"\bproactive\b", "proactive"),
    (r"\bgood\s+communication(\s+skills)?\b", "good communication skills"),
    (r"\bexcellent\s+communication(\s+skills)?\b", "excellent communication skills"),
    (r"\bresponsible\s+for\b", "responsible for"),
    (r"\bworked\s+on\b", "worked on"),
    (r"\bhelped\s+(to|with)?\b", "helped with"),
    (r"\bassisted\s+(in|with)?\b", "assisted with"),
]

# High-impact active technical engineering verbs
STRONG_VERBS = {
    "accelerated", "architected", "automated", "benchmarked", "built", "centralized",
    "configured", "consolidated", "containerized", "debugged", "decreased", "delivered",
    "deployed", "designed", "developed", "diagnosed", "engineered", "established",
    "executed", "extracted", "factored", "implemented", "increased", "indexed",
    "integrated", "isolated", "launched", "leveraged", "maintained", "maximized",
    "migrated", "minimized", "modernized", "monitored", "optimized", "orchestrated",
    "overhauled", "partitioned", "provisioned", "re-architected", "rebuilt", "reduced",
    "refactored", "resolved", "restructured", "scaled", "sharded", "simplified",
    "spearheaded", "standardized", "streamlined", "structured", "tested", "tracked",
    "transformed", "troubleshot", "upgraded", "validated", "yielded"
}

# Weak passive phrasing to avoid
PASSIVE_PHRASES = [
    "responsible for", "worked on", "assisted with", "helped", "participated in",
    "involved in", "handled", "supported", "tasked with", "contributed to", "duties included"
]


def audit_quantification(text: str) -> Tuple[float, List[str], List[str]]:
    """Evaluate metric density: presence of numbers, percentages, multipliers, latency figures."""
    metric_patterns = [
        r"\b\d+(\.\d+)?%",                         # 45%, 99.9%
        r"\b\$\d+([kmbKMB])?",                     # $50k, $1.2M
        r"\b\d+\s*(x|X)\b",                        # 10x, 3x
        r"\b\d+\s*(ms|s|sec|seconds?|minutes?)\b",  # 250ms, 1.2s
        r"\b\d+([kmbKMB])\+?\s*(users?|req|requests?|events?|qps|rps|tps|records?|rows?)\b",  # 500k req/s
        r"\b(reduced|increased|improved|cut|saved|boosted)\s+by\s+\d+",  # reduced by 30%
        r"\b\d+[\d,]*\+?\s+(users?|customers?|clients?|endpoints?|services?|microservices?)\b",
    ]

    detected_metrics = []
    for pat in metric_patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        if matches:
            detected_metrics.extend([m[0] if isinstance(m, tuple) else m for m in matches])

    count = len(detected_metrics)
    if count >= 6:
        score = 25.0
    elif count >= 4:
        score = 21.0
    elif count >= 2:
        score = 15.0
    elif count == 1:
        score = 10.0
    else:
        score = 4.0

    strengths = []
    additions = []
    if count >= 3:
        strengths.append(f"Strong quantification: detected {count} measurable impact metrics, percentages, or scale indicators.")
    else:
        additions.append("Add measurable outcomes to your bullet points (e.g., 'reduced API latency by 35%', 'scaled system to 50k daily active users').")

    return score, strengths, additions


def audit_action_verbs(text: str) -> Tuple[float, List[str], List[str]]:
    """Evaluate leadership and active engineering verbs versus passive phrasing."""
    lower_text = text.lower()
    words = re.findall(r"\b[a-z]{3,}\b", lower_text)
    detected_strong = {w for w in words if w in STRONG_VERBS}

    detected_passive = []
    for phrase in PASSIVE_PHRASES:
        if phrase in lower_text:
            detected_passive.append(phrase)

    strong_count = len(detected_strong)
    passive_count = len(detected_passive)

    # Base score on strong verbs
    if strong_count >= 8:
        score = 25.0
    elif strong_count >= 5:
        score = 21.0
    elif strong_count >= 3:
        score = 16.0
    elif strong_count >= 1:
        score = 11.0
    else:
        score = 5.0

    # Penalty for passive voice
    score = max(3.0, score - (passive_count * 2.0))

    strengths = []
    additions = []
    if strong_count >= 5 and passive_count == 0:
        strengths.append(f"Active leadership voice: utilized {strong_count} high-signal engineering verbs with zero passive phrasing.")
    if passive_count > 0:
        additions.append(f"Replace passive phrasing ({', '.join(detected_passive[:3])}) with direct action verbs (e.g. 'architected', 'spearheaded', 'orchestrated').")

    return score, strengths, additions


def audit_technical_keywords(text: str) -> Tuple[float, List[str], List[str]]:
    """Evaluate technical skill and tool density using the ontology."""
    extracted = extract_skills(text)
    count = len(extracted)

    if count >= 10:
        score = 25.0
    elif count >= 6:
        score = 21.0
    elif count >= 3:
        score = 16.0
    elif count >= 1:
        score = 10.0
    else:
        score = 4.0

    strengths = []
    additions = []
    if count >= 6:
        sample_skills = [
            getattr(s, "canonical_name", s.get("canonical_name") if isinstance(s, dict) else str(s))
            for s in extracted[:5]
        ]
        strengths.append(f"Solid technical vocabulary: recognized {count} verified engineering tools and skills ({', '.join(sample_skills)}).")
    else:
        additions.append("Increase technical keyword density: explicitly specify tools, databases, protocols, and libraries rather than generic 'coding' or 'development'.")

    return score, strengths, additions


def audit_brevity_and_fluff(text: str) -> Tuple[float, List[str], List[str], List[str]]:
    """Detect fluff, cliches, and filler phrases, returning deductions and removal suggestions."""
    detected_fluff: Set[str] = set()
    for pat, label in CLICHE_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            detected_fluff.add(label)

    fluff_list = sorted(list(detected_fluff))
    penalty = len(fluff_list) * 3.5
    score = max(4.0, 25.0 - penalty)

    strengths = []
    things_to_remove = []
    if not fluff_list:
        strengths.append("High signal-to-noise ratio: free of empty filler buzzwords, clichés, and vague adjectives.")
    else:
        for f in fluff_list:
            things_to_remove.append(f"Eliminate generic buzzword '{f}' — demonstrate competence through shipped project outcomes instead.")

    return score, strengths, things_to_remove, fluff_list


def generate_bullet_improvements(text: str) -> List[BulletImprovement]:
    """Generate targeted Google XYZ-formula before/after rewrites based on resume content."""
    lines = [line.strip("- *• \t") for line in text.splitlines() if len(line.strip("- *• \t")) > 20]
    improvements: List[BulletImprovement] = []

    # Inspect for lines with passive phrasing
    for line in lines:
        lower_line = line.lower()
        if any(p in lower_line for p in ["responsible for", "worked on", "assisted with", "helped"]):
            cleaned = re.sub(r"^(responsible for|worked on|assisted with|helped with|helped to)\s+", "", line, flags=re.IGNORECASE)
            improvements.append(BulletImprovement(
                original=line[:100] + ("..." if len(line) > 100 else ""),
                improved=f"Architected and deployed {cleaned}, accelerating delivery by 30% and reducing infrastructure costs.",
                reason="Replaced passive assignment with strong action verb ('Architected') and measurable business impact."
            ))
            if len(improvements) >= 2:
                break

    # Provide high-signal standard recommendations if few passive lines found
    if len(improvements) < 3:
        improvements.append(BulletImprovement(
            original="Built backend APIs using FastAPI and connected to PostgreSQL database.",
            improved="Engineered 14 production REST endpoints in FastAPI with SQLAlchemy, handling 2,500 daily requests with sub-50ms p95 latency.",
            reason="Google XYZ Formula: Specifies what was built (endpoints), how it was measured (requests/latency), and tools used."
        ))
    if len(improvements) < 3:
        improvements.append(BulletImprovement(
            original="Handled Docker containers and deployment to cloud servers.",
            improved="Orchestrated multi-stage Docker container builds and automated CI/CD deployment pipelines, cutting release cycle time from 4 hours to 12 minutes.",
            reason="Quantifies operational velocity increase and replaces vague 'handled' with 'orchestrated'."
        ))
    if len(improvements) < 3:
        improvements.append(BulletImprovement(
            original="Wrote unit tests and fixed bugs in the codebase.",
            improved="Implemented automated test suite with pytest covering 94% of core business logic, preventing regressions across 12 releases.",
            reason="Elevates routine maintenance into a quantifiable engineering quality safeguard."
        ))

    return improvements[:4]


def critique_resume_text(text: str) -> ResumeCritiqueResponse:
    """Analyze resume text and return structured rating, dimension scores, and suggestions."""
    if not text or len(text.strip()) < 30:
        return ResumeCritiqueResponse(
            overall_score=15,
            rating_label="Needs Critical Revision",
            dimension_scores=DimensionScores(
                quantification=3.0,
                action_verbs=4.0,
                keyword_density=4.0,
                brevity_and_clarity=4.0,
            ),
            strengths=[],
            things_to_add=[
                "Upload a comprehensive resume containing project bullet points, tools, and technical experience.",
                "Detail the specific technologies, architectures, and measurable results of your engineering projects."
            ],
            things_to_remove=[],
            bullet_improvements=generate_bullet_improvements(""),
            summary="The provided resume is too short to extract adequate technical signal. Expand on your project bullet points and quantified outcomes."
        )

    # 1. Audits
    quant_score, quant_strengths, quant_additions = audit_quantification(text)
    verb_score, verb_strengths, verb_additions = audit_action_verbs(text)
    kw_score, kw_strengths, kw_additions = audit_technical_keywords(text)
    clarity_score, clarity_strengths, things_to_remove, fluff_list = audit_brevity_and_fluff(text)

    # Check for GitHub link
    has_github = bool(re.search(r"github\.com/[a-zA-Z0-9_\-]+", text, re.IGNORECASE))
    if has_github:
        kw_strengths.append("Contains direct link to public GitHub profile/repositories.")
    else:
        quant_additions.append("Include a link to your public GitHub profile (github.com/yourusername) or live demonstration links for key projects.")

    # 2. Score Calculation
    total_score = int(round(quant_score + verb_score + kw_score + clarity_score))
    total_score = max(5, min(100, total_score))

    # 3. Rating Label
    if total_score >= 90:
        rating_label = "Exceptional"
    elif total_score >= 75:
        rating_label = "Competitive"
    elif total_score >= 60:
        rating_label = "Developing"
    else:
        rating_label = "Needs Critical Revision"

    # 4. Aggregations
    strengths = quant_strengths + verb_strengths + kw_strengths + clarity_strengths
    things_to_add = quant_additions + verb_additions + kw_additions

    # Deduplicate additions
    seen_add = set()
    deduped_add = []
    for item in things_to_add:
        if item not in seen_add:
            seen_add.add(item)
            deduped_add.append(item)

    bullet_improvements = generate_bullet_improvements(text)

    summary = (
        f"Resume evaluated at {total_score}/100 ({rating_label}). "
        f"Strengths: {len(strengths)} positive signal areas detected. "
        f"Action items: {len(deduped_add)} high-priority additions and {len(things_to_remove)} fluff phrases flagged for removal."
    )

    return ResumeCritiqueResponse(
        overall_score=total_score,
        rating_label=rating_label,
        dimension_scores=DimensionScores(
            quantification=round(quant_score, 1),
            action_verbs=round(verb_score, 1),
            keyword_density=round(kw_score, 1),
            brevity_and_clarity=round(clarity_score, 1),
        ),
        strengths=strengths,
        things_to_add=deduped_add,
        things_to_remove=things_to_remove,
        bullet_improvements=bullet_improvements,
        summary=summary,
    )
