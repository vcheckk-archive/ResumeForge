"""
Tailor MCP — Exceptions
========================
Custom exception hierarchy for the tailor_mcp module.
All exceptions carry a human-readable message and optional detail payload.
"""

from __future__ import annotations


class TailorMCPError(Exception):
    """Base exception for all tailor_mcp errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.details = details

    def __str__(self) -> str:
        base = super().__str__()
        return f"{base} — {self.details}" if self.details else base


# ── Input errors ──────────────────────────────────────────────────────


class MDFolderNotFoundError(TailorMCPError):
    """Raised when the md/ folder does not exist or is empty."""


class NoMDFilesFoundError(TailorMCPError):
    """Raised when no .md files are found in md/."""


class JobDescriptionError(TailorMCPError):
    """Raised when no job description is provided or cannot be read."""


class JDFileParseError(TailorMCPError):
    """Raised when a job description file (PDF/DOCX/TXT) cannot be parsed."""
