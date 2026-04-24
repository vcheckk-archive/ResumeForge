"""
LinkedIn Archive MCP Tool
=========================

Reads ``LINKEDIN_ARCHIVE_PATH`` from .env if no path is given.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .config import DEFAULT_OUTPUT_DIR
from .exceptions import LinkedInArchiveError
from .markdown_writer import write_all
from .parser import parse_archive
from .schemas import IngestResult

logger = logging.getLogger(__name__)


def linkedin_ingest_archive(
    folder_path: str | None = None,
    output_dir: str | None = None,
) -> dict:
    """
    Ingest a LinkedIn data export and produce resume-focused Markdown files.

    Args:
        folder_path: Path to the extracted LinkedIn archive folder.
                     If not provided, reads LINKEDIN_ARCHIVE_PATH from .env.
        output_dir:  (Optional) Output directory for Markdown files.
                     Defaults to md/linkedin/ in the project root.

    Returns:
        A dictionary with processed_files, skipped_files, output_paths,
        errors, and success status.
    """
    # Resolve folder path from .env if not provided
    if not folder_path:
        from env_loader import get_env
        folder_path = get_env("LINKEDIN_ARCHIVE_PATH")

    if not folder_path:
        return {
            "processed_files": [],
            "skipped_files": [],
            "output_paths": [],
            "errors": ["No folder_path provided and LINKEDIN_ARCHIVE_PATH not set in .env"],
            "success": False,
        }

    result = IngestResult()

    try:
        if output_dir:
            out_path = Path(output_dir)
        else:
            out_path = Path(__file__).resolve().parent.parent / DEFAULT_OUTPUT_DIR

        logger.info("Archive path : %s", folder_path)
        logger.info("Output path  : %s", out_path)

        archive, scan = parse_archive(folder_path)

        result.processed_files = list(scan.get("relevant", {}).values())
        result.skipped_files = scan.get("skipped", [])
        result.errors = scan.get("errors", [])

        result.output_paths = write_all(archive, out_path)

        logger.info(
            "Done — %d files written, %d processed, %d skipped, %d errors",
            len(result.output_paths),
            len(result.processed_files),
            len(result.skipped_files),
            len(result.errors),
        )

    except LinkedInArchiveError as exc:
        result.success = False
        result.errors.append(f"{exc.__class__.__name__}: {exc}")
        if exc.details:
            result.errors.append(f"  -> {exc.details}")
        logger.error("Pipeline failed: %s", exc)

    except Exception as exc:
        result.success = False
        result.errors.append(f"Unexpected error: {exc}")
        logger.exception("Unexpected error during ingestion")

    return {
        "processed_files": result.processed_files,
        "skipped_files": result.skipped_files,
        "output_paths": result.output_paths,
        "errors": result.errors,
        "success": result.success,
    }
