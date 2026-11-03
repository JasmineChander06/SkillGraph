"""Skill extractor: detects skills in free text using whole-word pattern matching.

Key design choices
------------------
* Whole-word matching prevents false positives such as "Java" inside "JavaScript".
* The C / C++ ambiguity is resolved with a dedicated negative-lookahead pattern that
  ensures "C" is only matched when it is NOT immediately followed by "++" or "#".
* Matching is case-insensitive.
* Each skill_id is returned at most once (deduplicated).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

from app.schemas.analysis import SkillMatch

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).parent.parent / "data"
_ALIASES_PATH = _DATA_DIR / "skill_aliases.json"


def _load_skill_catalogue() -> dict:
    """Load skill_aliases.json once at module import time."""
    with open(_ALIASES_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("skills", {})


_SKILL_CATALOGUE: dict = _load_skill_catalogue()

# ---------------------------------------------------------------------------
# Pattern compilation
# ---------------------------------------------------------------------------

# Importance ordering used by callers.
IMPORTANCE_ORDER: Dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


def _make_pattern(term: str, skill_id: str) -> re.Pattern:
    """
    Build a whole-word regex pattern for *term*.

    Special-cases
    -------------
    * ``c_lang`` ("C"): the pattern requires that "C" is NOT followed by "++" or "#"
      so that "C++" and "C#" do not erroneously match the bare "C" skill.
    * "C++" and "C#" surface forms: escaped so that ``+`` and ``#`` are treated as
      literals.
    * Boundaries reject alphanumeric, underscore, '+', and '#' characters to prevent
      partial matches (e.g. 'C' in 'C++', 'Java' in 'JavaScript') while allowing
      punctuation boundaries such as periods, commas, parentheses, etc.
    """
    escaped = re.escape(term)

    # Word boundary that forbids alphanumeric, +, and # on both sides
    return re.compile(
        r"(?<![A-Za-z0-9_+#])" + escaped + r"(?![A-Za-z0-9_+#])",
        re.IGNORECASE,
    )


def _build_pattern_index() -> List[Tuple[str, str, str, List[re.Pattern]]]:
    """
    Pre-compile all surface-form patterns for every skill.

    Returns a list of tuples:
        (skill_id, canonical_name, category, [compiled_patterns])
    """
    index: List[Tuple[str, str, str, List[re.Pattern]]] = []

    for skill_id, meta in _SKILL_CATALOGUE.items():
        canonical = meta.get("canonical", skill_id)
        category = meta.get("category", "")
        aliases: List[str] = meta.get("aliases", [])

        surface_forms: List[Tuple[str, str]] = [(canonical, "canonical")] + [
            (alias, "alias") for alias in aliases
        ]

        patterns: List[Tuple[re.Pattern, str]] = [
            (_make_pattern(form, skill_id), source)
            for form, source in surface_forms
        ]
        index.append((skill_id, canonical, category, patterns))  # type: ignore[arg-type]

    return index  # type: ignore[return-value]


# One-time compilation at module load
_PATTERN_INDEX: List[Tuple[str, str, str, List[Tuple[re.Pattern, str]]]] = (  # type: ignore[assignment]
    _build_pattern_index()  # type: ignore[assignment]
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_skills(text: str) -> List[SkillMatch]:
    """
    Extract all recognisable skills from *text*.

    Parameters
    ----------
    text:
        Free-form text (e.g. resume body).

    Returns
    -------
    List[SkillMatch]
        Deduplicated list of detected skills.  Each skill appears at most once.
    """
    seen: set[str] = set()
    results: List[SkillMatch] = []

    # Normalise whitespace
    normalised = " ".join(text.split())

    for skill_id, canonical, category, patterns in _PATTERN_INDEX:
        if skill_id in seen:
            continue

        for pattern, source in patterns:
            if pattern.search(normalised):
                seen.add(skill_id)
                results.append(
                    SkillMatch(
                        skill_id=skill_id,
                        canonical_name=canonical,
                        category=category,
                        matched_via=source,
                    )
                )
                break  # first match is sufficient; move on to next skill

    return results


def get_skill_meta(skill_id: str) -> dict:
    """Return raw skill metadata from the catalogue, or an empty dict."""
    return _SKILL_CATALOGUE.get(skill_id, {})

