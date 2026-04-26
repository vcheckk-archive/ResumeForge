"""
Resume History MCP — Config
============================
All constants, patterns, and tuning parameters in one place.
Edit here to tune extraction behaviour — no logic files need to change.
"""

from __future__ import annotations

import re

# ── Supported file types ───────────────────────────────────────────────
SUPPORTED_EXTENSIONS: set[str] = {".pdf", ".docx"}

# ── Default output directory (relative to project root) ───────────────
DEFAULT_OUTPUT_DIR: str = "md/resume"
OUTPUT_FILE_NAME: str = "resume_history.md"

# ──────────────────────────────────────────────────────────────────────
# Section header keywords
# Each list is checked case-insensitively against detected headings.
# Ordered by specificity — first match wins.
# ──────────────────────────────────────────────────────────────────────

SECTION_KEYWORDS: dict[str, list[str]] = {
    "summary": [
        "summary", "objective", "profile", "about me", "career objective",
        "professional summary", "overview", "professional profile",
    ],
    "experience": [
        "experience", "work experience", "employment", "professional experience",
        "work history", "internship", "internships", "career history",
        "positions held", "professional background",
    ],
    "projects": [
        "projects", "project", "academic projects", "personal projects",
        "notable projects", "key projects", "portfolio", "technical projects",
        "side projects", "open source",
    ],
    "skills": [
        "skills", "technical skills", "technologies", "tools", "core competencies",
        "competencies", "expertise", "key skills", "programming languages",
        "languages", "frameworks", "toolset", "skill set",
    ],
    "education": [
        "education", "academic background", "academic history",
        "qualifications", "degrees", "schooling",
    ],
    "certifications": [
        "certifications", "certification", "certificates", "licenses",
        "awards", "achievements", "courses", "training", "credentials",
        "professional development",
    ],
    "publications": [
        "publications", "papers", "research", "conferences",
    ],
    "languages": [
        "languages spoken", "spoken languages", "human languages",
    ],
    "interests": [
        "interests", "hobbies", "extracurricular", "activities",
    ],
}

# ── Company-specific resume detection patterns ─────────────────────────
COMPANY_INDICATORS: list[re.Pattern] = [
    re.compile(r"\b(google|amazon|microsoft|apple|meta|netflix|uber|airbnb|"
               r"flipkart|infosys|wipro|tcs|accenture|deloitte|pwc|ibm|"
               r"oracle|salesforce|atlassian|adobe|shopify|stripe|openai|"
               r"anthropic|deepmind|nvidia)\b", re.IGNORECASE),
]

# ── Identity extraction patterns ───────────────────────────────────────
IDENTITY_PATTERNS: dict[str, re.Pattern] = {
    "email":    re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}"),
    "phone":    re.compile(r"(\+?\d[\d\s\-().]{7,}\d)"),
    "linkedin": re.compile(r"linkedin\.com/in/[\w-]+", re.IGNORECASE),
    "github":   re.compile(r"github\.com/[\w-]+", re.IGNORECASE),
    "website":  re.compile(r"https?://(?!linkedin|github)[\w./\-]+", re.IGNORECASE),
}

# ── Deduplication thresholds ───────────────────────────────────────────
FUZZY_MATCH_THRESHOLD: int = 82      # Minimum similarity score (0-100) for project/job match
SKILL_NORMALIZE: bool = True         # Lowercase + strip before dedup
PREFER_LATEST: bool = True           # When conflict: latest resume wins

# ── Extraction: lenient mode ───────────────────────────────────────────
LENIENT_MIN_LINE_LENGTH: int = 3     # Minimum chars to keep a line
LENIENT_SECTION_MIN_CONFIDENCE: float = 0.0   # Accept ALL detected sections

# ── Page limit (memory protection) ────────────────────────────────────
MAX_PAGES_PER_PDF: int = 50
