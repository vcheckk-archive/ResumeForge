"""
Resume History MCP Tool — Gateway
====================================
Single entry point: scan a folder of resume files (PDF/DOCX),
extract, deduplicate, build timeline, and produce a clean Markdown
career profile.

Usage:
    # Reads RESUME_HISTORY_PATH from .env
    resume_history_analyze()

    # Or pass path directly
    resume_history_analyze(folder_path="/path/to/resumes")

Pipeline:
    1. Discover & order files (oldest → newest by mtime)
    2. Extract each file  (pdfplumber → PyMuPDF → docx)
    3. Classify each file (generic | company_specific)
    4. Aggregate all data into ResumeHistory
    5. Deduplicate (fuzzy for projects/jobs, exact for skills/certs)
    6. Build career timeline
    7. Write md/resume/resume_history.md
"""

from __future__ import annotations

import logging
from pathlib import Path

from .aggregator import aggregate
from .classifier import classify
from .config import DEFAULT_OUTPUT_DIR, SUPPORTED_EXTENSIONS
from .deduplicator import deduplicate
from .exceptions import (
    ExtractionError,
    FolderNotFoundError,
    MarkdownWriteError,
    NoResumesFoundError,
    ResumeMCPError,
)
from .extractor import extract
from .markdown_writer import write_resume_history
from .schemas import AnalysisResult, RawResume
from .timeline import build_timeline

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# MCP Gateway Tool
# ──────────────────────────────────────────────────────────────────────


def resume_history_analyze(
    folder_path: str | None = None,
    output_dir: str | None = None,
) -> dict:
    """
    Analyze a folder of resume files and produce a deduplicated,
    chronological Markdown career profile.

    Args:
        folder_path: Path to folder containing PDF/DOCX resumes.
                     If not provided, reads RESUME_HISTORY_PATH from .env.
        output_dir:  Custom output directory. Defaults to md/resume/
                     in the project root.

    Returns:
        {
            "success": bool,
            "files_processed": [...],
            "files_failed": [...],
            "output_path": "md/resume/resume_history.md",
            "dedup_report": {
                "projects_merged": [...],
                "jobs_merged": [...],
                "skills_deduplicated": N,
                ...
            },
            "extraction_warnings": [...],
            "errors": [...]
        }
    """
    result = AnalysisResult()

    try:
        # ── Step 0: Resolve folder path ──────────────────────────────
        if not folder_path:
            from env_loader import get_env
            folder_path = get_env("RESUME_HISTORY_PATH")

        if not folder_path:
            raise FolderNotFoundError(
                "No folder_path provided and RESUME_HISTORY_PATH not set in .env"
            )

        folder = Path(folder_path)
        if not folder.exists():
            raise FolderNotFoundError(f"Folder does not exist: {folder}")
        if not folder.is_dir():
            raise FolderNotFoundError(f"Path is not a folder: {folder}")

        # ── Step 1: Discover files ────────────────────────────────────
        files = _discover_files(folder)
        if not files:
            raise NoResumesFoundError(
                f"No supported resume files found in '{folder}'",
                details=f"Supported types: {', '.join(SUPPORTED_EXTENSIONS)}",
            )

        logger.info("Discovered %d resume file(s) in '%s'", len(files), folder)

        # ── Step 2 & 3: Extract + Classify each file ─────────────────
        resumes: list[RawResume] = []
        for file in files:
            try:
                raw = extract(file)
                classify(raw)
                resumes.append(raw)
                result.files_processed.append(file.name)
                logger.info("Processed: %s (type=%s)", file.name, raw.resume_type)
            except ExtractionError as e:
                result.files_failed.append(file.name)
                result.errors.append(str(e))
                logger.warning("Skipped '%s': %s", file.name, e)

        if not resumes:
            raise NoResumesFoundError(
                "All resume files failed extraction",
                details="Check extraction_warnings in output for details",
            )

        # ── Step 4: Aggregate ─────────────────────────────────────────
        history = aggregate(resumes)

        # ── Step 5: Deduplicate ───────────────────────────────────────
        history = deduplicate(history)

        # ── Step 6: Timeline ──────────────────────────────────────────
        history = build_timeline(resumes, history)

        # ── Step 7: Write Markdown ────────────────────────────────────
        out_path = (
            Path(output_dir)
            if output_dir
            else Path(__file__).resolve().parent.parent / DEFAULT_OUTPUT_DIR
        )
        output_file = write_resume_history(history, out_path)
        result.output_path = output_file

        # ── Populate result ───────────────────────────────────────────
        dr = history.dedup_report
        result.dedup_report = {
            "projects_merged": dr.projects_merged,
            "jobs_merged": dr.jobs_merged,
            "skills_deduplicated": dr.skills_deduplicated,
            "certs_deduplicated": dr.certs_deduplicated,
            "education_deduplicated": dr.education_deduplicated,
            "total_input_items": dr.total_input_items,
            "total_output_items": dr.total_output_items,
        }
        result.extraction_warnings = history.extraction_warnings

        logger.info(
            "Done — output: %s | processed: %d | failed: %d | warnings: %d",
            output_file,
            len(result.files_processed),
            len(result.files_failed),
            len(result.extraction_warnings),
        )

    except (FolderNotFoundError, NoResumesFoundError) as e:
        result.success = False
        result.errors.append(str(e))
        logger.error("Input error: %s", e)

    except MarkdownWriteError as e:
        result.success = False
        result.errors.append(str(e))
        logger.error("Write error: %s", e)

    except ResumeMCPError as e:
        result.success = False
        result.errors.append(str(e))
        logger.error("Pipeline error: %s", e)

    except Exception as e:
        result.success = False
        result.errors.append(f"Unexpected error: {e}")
        logger.exception("Unexpected error in resume_history_analyze")

    return {
        "success": result.success,
        "files_processed": result.files_processed,
        "files_failed": result.files_failed,
        "output_path": result.output_path,
        "dedup_report": result.dedup_report,
        "extraction_warnings": result.extraction_warnings,
        "errors": result.errors,
    }


# ──────────────────────────────────────────────────────────────────────
# File Discovery
# ──────────────────────────────────────────────────────────────────────


def _discover_files(folder: Path) -> list[Path]:
    """
    Find all supported resume files in a folder (non-recursive).
    Sorted oldest → newest by last modified time.
    Temp/hidden files are excluded.
    """
    files: list[Path] = []
    for f in folder.iterdir():
        if not f.is_file():
            continue
        if f.name.startswith(".") or f.name.startswith("~"):
            continue  # skip hidden/temp files
        if f.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(f)

    # Sort oldest → newest by mtime (defines career timeline order)
    files.sort(key=lambda f: f.stat().st_mtime)
    return files
