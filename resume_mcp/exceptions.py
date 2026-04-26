"""
Resume History MCP — Exceptions
================================
Custom exception hierarchy for the resume_mcp module.
All exceptions carry a human-readable message and optional detail payload.
"""

from __future__ import annotations


class ResumeMCPError(Exception):
    """Base exception for all resume_mcp errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.details = details

    def __str__(self) -> str:
        base = super().__str__()
        return f"{base} — {self.details}" if self.details else base


# ── Input errors ──────────────────────────────────────────────────────


class FolderNotFoundError(ResumeMCPError):
    """Raised when the supplied resume folder does not exist."""


class NoResumesFoundError(ResumeMCPError):
    """Raised when no supported resume files are found in the folder."""


# ── Extraction errors ─────────────────────────────────────────────────


class ExtractionError(ResumeMCPError):
    """Raised when a resume file cannot be parsed by any extractor."""

    def __init__(self, file: str, reason: str) -> None:
        super().__init__(f"Failed to extract '{file}'", details=reason)
        self.file = file


class PDFExtractionError(ExtractionError):
    """Raised when both pdfplumber and PyMuPDF fail on a PDF."""


class DOCXExtractionError(ExtractionError):
    """Raised when python-docx fails on a DOCX file."""


# ── Processing errors ─────────────────────────────────────────────────


class AggregationError(ResumeMCPError):
    """Raised when resume data cannot be merged into ResumeHistory."""


class DeduplicationError(ResumeMCPError):
    """Raised when the deduplication engine encounters an unrecoverable state."""


# ── Output errors ─────────────────────────────────────────────────────


class MarkdownWriteError(ResumeMCPError):
    """Raised when the output Markdown file cannot be written."""
