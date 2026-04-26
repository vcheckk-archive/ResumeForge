"""
Resume History MCP — Schemas
==============================
Typed dataclasses used throughout the resume_mcp pipeline.
All fields are Optional-friendly to support lenient extraction mode.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


# ──────────────────────────────────────────────────────────────────────
# Per-file raw extraction result
# ──────────────────────────────────────────────────────────────────────


@dataclass
class RawSection:
    """A single extracted section from a resume file."""
    heading: str          # Detected heading text (e.g. "EXPERIENCE")
    content: str          # Raw text content of the section
    confidence: float     # 0.0–1.0 — how confident the detector is
    page: int = 0         # Source page number (PDF only)


@dataclass
class RawResume:
    """All data extracted from a single resume file."""
    file_path: Path
    file_name: str
    modified_date: datetime
    resume_type: str = "generic"      # "generic" | "company_specific"
    target_company: str = ""          # Populated for company-specific resumes

    # Structured sections — always present, may be empty strings/lists
    identity: dict = field(default_factory=dict)
    summary: str = ""
    experiences: list[dict] = field(default_factory=list)
    projects: list[dict] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    education: list[dict] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)

    # Lenient mode: sections the engine could not confidently classify
    raw_sections: list[RawSection] = field(default_factory=list)

    # Full raw text — passed to LLM for further enrichment
    full_text: str = ""

    # Extraction metadata
    extractor_used: str = ""          # "pdfplumber" | "pymupdf" | "docx"
    extraction_warnings: list[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────
# Aggregated career history across all resumes
# ──────────────────────────────────────────────────────────────────────


@dataclass
class TimelineEntry:
    """A single event in the career timeline."""
    date: datetime
    source_file: str
    event_type: str        # "role_added" | "skill_added" | "project_added" | "cert_added"
    label: str             # Human-readable description
    detail: str = ""


@dataclass
class DeduplicationReport:
    """Summary of what the dedup engine merged/dropped."""
    projects_merged: list[str] = field(default_factory=list)
    jobs_merged: list[str] = field(default_factory=list)
    skills_deduplicated: int = 0
    certs_deduplicated: int = 0
    education_deduplicated: int = 0
    total_input_items: int = 0
    total_output_items: int = 0


@dataclass
class ResumeHistory:
    """Final aggregated, deduplicated career history."""
    identity: dict = field(default_factory=dict)
    experiences: list[dict] = field(default_factory=list)
    projects: list[dict] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    education: list[dict] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    summaries: list[str] = field(default_factory=list)
    timeline: list[TimelineEntry] = field(default_factory=list)
    raw_sections_unclassified: list[RawSection] = field(default_factory=list)
    dedup_report: DeduplicationReport = field(default_factory=DeduplicationReport)
    source_files: list[str] = field(default_factory=list)
    extraction_warnings: list[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────
# Tool result
# ──────────────────────────────────────────────────────────────────────


@dataclass
class AnalysisResult:
    """Return value of resume_history_analyze()."""
    success: bool = True
    files_processed: list[str] = field(default_factory=list)
    files_failed: list[str] = field(default_factory=list)
    output_path: str = ""
    dedup_report: dict = field(default_factory=dict)
    extraction_warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
