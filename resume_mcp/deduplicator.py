"""
Resume History MCP — Deduplicator
===================================
Removes duplicate entries across all merged resume data.

Rules:
  - Projects  : fuzzy name match (≥ threshold) → keep best description
  - Experience: fuzzy (role + company) match   → keep best description
  - Skills    : exact match after normalization → keep once
  - Education : institution + degree match     → keep once
  - Certs     : exact match after normalization → keep once

Uses rapidfuzz for fuzzy matching (fast, no ML dependency).
Falls back to simple substring match if rapidfuzz is unavailable.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict

from .config import FUZZY_MATCH_THRESHOLD, PREFER_LATEST, SKILL_NORMALIZE
from .exceptions import DeduplicationError
from .schemas import DeduplicationReport, ResumeHistory

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Fuzzy match helper (graceful degradation)
# ──────────────────────────────────────────────────────────────────────


def _similarity(a: str, b: str) -> float:
    """Return similarity score 0-100 between two strings."""
    try:
        from rapidfuzz.fuzz import token_sort_ratio
        return token_sort_ratio(a.lower(), b.lower())
    except ImportError:
        # Fallback: Jaccard similarity on word sets
        a_words = set(a.lower().split())
        b_words = set(b.lower().split())
        if not a_words or not b_words:
            return 0.0
        intersection = a_words & b_words
        union = a_words | b_words
        return 100 * len(intersection) / len(union)


def _normalize(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text.lower()).strip()


# ──────────────────────────────────────────────────────────────────────
# Public Interface
# ──────────────────────────────────────────────────────────────────────


def deduplicate(history: ResumeHistory) -> ResumeHistory:
    """
    Deduplicate all collections in a ResumeHistory in-place.
    Returns the same object with a populated dedup_report.
    """
    report = DeduplicationReport()

    try:
        input_count = (
            len(history.projects)
            + len(history.experiences)
            + len(history.skills)
            + len(history.education)
            + len(history.certifications)
        )

        history.projects    = _dedup_fuzzy(history.projects, "name", report.projects_merged)
        history.experiences = _dedup_experiences(history.experiences, report.jobs_merged)
        history.skills, report.skills_deduplicated = _dedup_skills(history.skills)
        history.education, report.education_deduplicated = _dedup_exact_list(
            history.education, keys=["institution", "degree"]
        )
        history.certifications, report.certs_deduplicated = _dedup_exact_strings(
            history.certifications
        )

        output_count = (
            len(history.projects)
            + len(history.experiences)
            + len(history.skills)
            + len(history.education)
            + len(history.certifications)
        )

        report.total_input_items = input_count
        report.total_output_items = output_count

        logger.info(
            "Dedup complete: %d → %d items (%d removed)",
            input_count, output_count, input_count - output_count,
        )

    except Exception as e:
        raise DeduplicationError("Deduplication failed", details=str(e)) from e

    history.dedup_report = report
    return history


# ──────────────────────────────────────────────────────────────────────
# Dedup helpers
# ──────────────────────────────────────────────────────────────────────


def _dedup_fuzzy(
    items: list[dict],
    name_key: str,
    merged_log: list[str],
) -> list[dict]:
    """
    Fuzzy-dedup a list of dicts by a name key.
    Keep the item with the longest/most-detailed description.
    """
    if not items:
        return items

    groups: list[list[dict]] = []

    for item in items:
        item_name = str(item.get(name_key, item.get("raw", "")))[:80]
        placed = False
        for group in groups:
            rep_name = str(group[0].get(name_key, group[0].get("raw", "")))[:80]
            if _similarity(item_name, rep_name) >= FUZZY_MATCH_THRESHOLD:
                group.append(item)
                placed = True
                break
        if not placed:
            groups.append([item])

    result: list[dict] = []
    for group in groups:
        if len(group) == 1:
            result.append(group[0])
        else:
            # Keep the one with the longest description
            best = max(
                group,
                key=lambda x: len(str(x.get("description", x.get("raw", "")))),
            )
            merged_name = str(best.get(name_key, best.get("raw", "")))[:60]
            merged_log.append(merged_name)
            result.append(best)

    return result


def _dedup_experiences(items: list[dict], merged_log: list[str]) -> list[dict]:
    """Dedup experience entries by (role + company) fuzzy match."""
    if not items:
        return items

    def key_for(item: dict) -> str:
        role = str(item.get("role", item.get("title", "")))
        company = str(item.get("company", item.get("organization", "")))
        raw = str(item.get("raw", ""))
        return f"{role} {company}".strip() or raw[:80]

    groups: list[list[dict]] = []
    for item in items:
        k = key_for(item)
        placed = False
        for group in groups:
            if _similarity(k, key_for(group[0])) >= FUZZY_MATCH_THRESHOLD:
                group.append(item)
                placed = True
                break
        if not placed:
            groups.append([item])

    result: list[dict] = []
    for group in groups:
        if len(group) == 1:
            result.append(group[0])
        else:
            best = max(group, key=lambda x: len(str(x.get("raw", ""))))
            merged_log.append(key_for(best)[:60])
            result.append(best)

    return result


def _dedup_skills(skills: list[str]) -> tuple[list[str], int]:
    """Exact dedup of skills after normalization."""
    seen: set[str] = set()
    result: list[str] = []
    for skill in skills:
        normalized = _normalize(skill) if SKILL_NORMALIZE else skill
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(skill.strip())
    return result, len(skills) - len(result)


def _dedup_exact_list(items: list[dict], keys: list[str]) -> tuple[list[dict], int]:
    """Exact dedup of a list of dicts based on a composite key."""
    seen: set[str] = set()
    result: list[dict] = []
    for item in items:
        composite = "|".join(_normalize(str(item.get(k, ""))) for k in keys)
        if not composite.strip("|") or composite not in seen:
            seen.add(composite)
            result.append(item)
    return result, len(items) - len(result)


def _dedup_exact_strings(items: list[str]) -> tuple[list[str], int]:
    """Exact dedup of a string list after normalization."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = _normalize(item)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(item.strip())
    return result, len(items) - len(result)
