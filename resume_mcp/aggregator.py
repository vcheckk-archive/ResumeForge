"""
Resume History MCP — Aggregator
=================================
Merges a list of RawResume objects (sorted oldest→newest) into
a single ResumeHistory, applying the primary-truth rules:
  - Latest generic resume → primary truth
  - Older resumes / company-specific → supplement missing data only
"""

from __future__ import annotations

import logging
from datetime import datetime

from .exceptions import AggregationError
from .schemas import RawResume, RawSection, ResumeHistory

logger = logging.getLogger(__name__)


def aggregate(resumes: list[RawResume]) -> ResumeHistory:
    """
    Merge all RawResume objects into one ResumeHistory.

    Args:
        resumes: List sorted oldest → newest.

    Returns:
        ResumeHistory with combined data (pre-dedup).
    """
    if not resumes:
        raise AggregationError("No resumes to aggregate")

    history = ResumeHistory()
    history.source_files = [r.file_name for r in resumes]

    # ── Pass 1: Collect all data ─────────────────────────────────────────
    # Process oldest → newest so that latest data wins on direct overwrites.
    identity_candidates: list[dict] = []
    all_warnings: list[str] = []

    for resume in resumes:
        if resume.identity:
            identity_candidates.append(resume.identity)

        if resume.summary:
            history.summaries.append(resume.summary)

        history.experiences.extend(resume.experiences)
        history.projects.extend(resume.projects)
        history.skills.extend(resume.skills)
        history.education.extend(resume.education)
        history.certifications.extend(resume.certifications)
        history.raw_sections_unclassified.extend(
            s for s in resume.raw_sections if s.confidence == 0.0
        )
        all_warnings.extend(resume.extraction_warnings)

    history.extraction_warnings = all_warnings

    # ── Pass 2: Identity — latest generic resume wins ────────────────────
    # Merge by preferring later keys over earlier ones
    merged_identity: dict = {}
    for identity in identity_candidates:
        merged_identity.update({k: v for k, v in identity.items() if v})
    history.identity = merged_identity

    logger.info(
        "Aggregated %d resume(s) → %d exp, %d projects, %d skills, %d certs",
        len(resumes),
        len(history.experiences),
        len(history.projects),
        len(history.skills),
        len(history.certifications),
    )

    return history
