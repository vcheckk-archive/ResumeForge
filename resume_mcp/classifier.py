"""
Resume History MCP — Classifier
=================================
Identifies whether a resume is generic or company-targeted.
Sets `resume_type` and `target_company` on the RawResume object.
"""

from __future__ import annotations

import logging
import re

from .config import COMPANY_INDICATORS
from .schemas import RawResume

logger = logging.getLogger(__name__)

# ── Extra signals: file name patterns ─────────────────────────────────
_FILENAME_COMPANY_RE = re.compile(
    r"(?:resume|cv)[_\-\s]*([\w\s]+)$", re.IGNORECASE
)

# ── Signal weights ─────────────────────────────────────────────────────
# A score >= THRESHOLD → classified as company-specific
_COMPANY_SCORE_THRESHOLD = 2


def classify(resume: RawResume) -> RawResume:
    """
    Classify a RawResume as generic or company-specific.
    Modifies in-place and returns the same object.

    Signals considered:
      - File name mentions a company name
      - Body text contains company name keywords
      - Presence of cover-letter-like targeted language
    """
    score = 0
    company_hits: list[str] = []

    # ── Signal 1: filename ─────────────────────────────────────────────
    stem = resume.file_path.stem.lower().replace("_", " ").replace("-", " ")
    for pattern in COMPANY_INDICATORS:
        match = pattern.search(stem)
        if match:
            score += 3
            company_hits.append(match.group(0).title())

    # ── Signal 2: body text company mentions ───────────────────────────
    text_sample = resume.full_text[:3000]  # first 3000 chars is enough
    for pattern in COMPANY_INDICATORS:
        for match in pattern.finditer(text_sample):
            score += 1
            company_hits.append(match.group(0).title())
            if score >= _COMPANY_SCORE_THRESHOLD:
                break

    # ── Signal 3: targeted language ───────────────────────────────────
    targeted_phrases = [
        r"why i want to (work|join) at",
        r"passionate about (your|the) (mission|product|team)",
        r"tailored (for|to)",
        r"specific(ally)? for",
    ]
    for phrase in targeted_phrases:
        if re.search(phrase, resume.full_text[:2000], re.IGNORECASE):
            score += 2
            break

    # ── Classification ─────────────────────────────────────────────────
    if score >= _COMPANY_SCORE_THRESHOLD and company_hits:
        resume.resume_type = "company_specific"
        # Use most-mentioned company as primary target
        from collections import Counter
        resume.target_company = Counter(company_hits).most_common(1)[0][0]
        logger.info(
            "'%s' → company_specific (target: %s, score: %d)",
            resume.file_name, resume.target_company, score,
        )
    else:
        resume.resume_type = "generic"
        logger.info("'%s' → generic (score: %d)", resume.file_name, score)

    return resume
