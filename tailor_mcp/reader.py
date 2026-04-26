"""
Tailor MCP — Reader
====================
Utilities to:
  1. Recursively read all .md files from the md/ folder
     (outputs of linkedin_mcp, github_mcp, coding_mcp, resume_mcp).
  2. Parse a Job Description from text, TXT, PDF, or DOCX file.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .config import MD_SUBDIRS, SUPPORTED_JD_EXTENSIONS
from .exceptions import (
    JDFileParseError,
    MDFolderNotFoundError,
    NoMDFilesFoundError,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Biography Aggregator — reads all md/ output
# ──────────────────────────────────────────────────────────────────────


def read_all_md_files(md_root: Path) -> dict[str, str]:
    """
    Recursively read every .md file under md_root and return a dict
    mapping relative path → file content.

    Scans subdirectories: linkedin/, github/, coding/, resume/

    Returns:
        {"linkedin/identity.md": "...", "github/projects_summary.md": "...", ...}

    Raises:
        MDFolderNotFoundError: If md_root does not exist.
        NoMDFilesFoundError: If no .md files are found.
    """
    if not md_root.exists():
        raise MDFolderNotFoundError(
            f"MD folder not found: {md_root}",
            details="Run the 4 extraction tools first to generate md/ content.",
        )

    files: dict[str, str] = {}

    for subdir in MD_SUBDIRS:
        sub_path = md_root / subdir
        if not sub_path.exists():
            logger.warning("Subdirectory not found, skipping: %s", sub_path)
            continue

        for md_file in sorted(sub_path.rglob("*.md")):
            try:
                rel = md_file.relative_to(md_root)
                content = md_file.read_text(encoding="utf-8")
                if content.strip():
                    files[str(rel)] = content
                    logger.debug("Read: %s (%d chars)", rel, len(content))
            except Exception as e:
                logger.warning("Failed to read %s: %s", md_file, e)

    if not files:
        raise NoMDFilesFoundError(
            f"No .md files found in {md_root}",
            details="Run linkedin_ingest_archive, github_build_profile, "
                    "coding_extract_profiles, and resume_history_analyze first.",
        )

    logger.info(
        "Aggregated %d markdown file(s) from %s",
        len(files), md_root,
    )
    return files


# ──────────────────────────────────────────────────────────────────────
# Job Description Parser
# ──────────────────────────────────────────────────────────────────────


def read_jd_from_file(file_path: Path) -> str:
    """
    Read a Job Description from a file (TXT, MD, PDF, or DOCX).

    Returns:
        The extracted text content.

    Raises:
        JDFileParseError: If the file cannot be read or parsed.
    """
    if not file_path.exists():
        raise JDFileParseError(
            f"JD file not found: {file_path}",
            details="Provide a valid file path.",
        )

    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_JD_EXTENSIONS:
        raise JDFileParseError(
            f"Unsupported file type: {suffix}",
            details=f"Supported: {', '.join(SUPPORTED_JD_EXTENSIONS)}",
        )

    try:
        if suffix in (".txt", ".md"):
            return file_path.read_text(encoding="utf-8").strip()

        elif suffix == ".pdf":
            return _extract_pdf(file_path)

        elif suffix == ".docx":
            return _extract_docx(file_path)

    except JDFileParseError:
        raise
    except Exception as e:
        raise JDFileParseError(
            f"Failed to parse JD file: {file_path.name}",
            details=str(e),
        ) from e

    return ""


def read_jd_from_folder(folder_path: Path) -> str:
    """
    Scan a folder for JD files. Reads all supported files and
    concatenates their content.

    Priority order: .txt → .md → .pdf → .docx

    Returns:
        Combined text from all JD files found.

    Raises:
        JDFileParseError: If no supported files are found.
    """
    if not folder_path.exists() or not folder_path.is_dir():
        raise JDFileParseError(
            f"JD folder not found: {folder_path}",
            details="Provide a valid folder path.",
        )

    parts: list[str] = []
    priority = [".txt", ".md", ".pdf", ".docx"]

    for ext in priority:
        for f in sorted(folder_path.glob(f"*{ext}")):
            try:
                content = read_jd_from_file(f)
                if content.strip():
                    parts.append(f"--- Source: {f.name} ---\n{content}")
                    logger.info("Read JD file: %s (%d chars)", f.name, len(content))
            except JDFileParseError as e:
                logger.warning("Skipped JD file %s: %s", f.name, e)

    if not parts:
        raise JDFileParseError(
            f"No readable JD files in: {folder_path}",
            details=f"Supported types: {', '.join(SUPPORTED_JD_EXTENSIONS)}",
        )

    return "\n\n".join(parts)


# ──────────────────────────────────────────────────────────────────────
# Private Helpers
# ──────────────────────────────────────────────────────────────────────


def _extract_pdf(file_path: Path) -> str:
    """Extract text from PDF using pdfplumber, fallback to PyMuPDF."""
    text = ""

    # Primary: pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(str(file_path)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
            text = "\n".join(pages).strip()
        if text:
            return text
    except Exception as e:
        logger.debug("pdfplumber failed on %s: %s", file_path.name, e)

    # Fallback: PyMuPDF
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(file_path))
        pages = [page.get_text() for page in doc]
        doc.close()
        text = "\n".join(pages).strip()
        if text:
            return text
    except Exception as e:
        logger.debug("PyMuPDF failed on %s: %s", file_path.name, e)

    if not text:
        raise JDFileParseError(
            f"Could not extract text from PDF: {file_path.name}",
            details="Both pdfplumber and PyMuPDF failed.",
        )

    return text


def _extract_docx(file_path: Path) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        from docx import Document
        doc = Document(str(file_path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs).strip()
        if not text:
            raise JDFileParseError(
                f"DOCX file is empty: {file_path.name}",
            )
        return text
    except JDFileParseError:
        raise
    except Exception as e:
        raise JDFileParseError(
            f"Failed to parse DOCX: {file_path.name}",
            details=str(e),
        ) from e
