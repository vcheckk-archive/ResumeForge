"""
Tailor MCP — ATS Resume Builder Tool (Gateway)
================================================
Single entry point: provide a Job Description and get an ATS-optimized
resume tailored from your complete biography data in the md/ folder.

Input Methods (any combination works):
  1. Direct text:          tailor_resume_for_job(job_description_text="...")
  2. Single file path:     tailor_resume_for_job(job_description_file="/path/to/jd.pdf")
  3. Folder of JD files:   tailor_resume_for_job(job_description_folder="/path/to/jd_folder/")
  4. Env var fallback:     Reads JD_INPUT_PATH from .env

Data Source:
  The md/ folder (output of linkedin_mcp, github_mcp, coding_mcp, resume_mcp).
  Default path: <project_root>/md/

Output:
  The tool returns a structured prompt to the host LLM (Claude, Cursor, etc.)
  instructing it to generate and save an ATS-optimized Markdown resume as:
    md/tailored/<CompanyName>_<JobTitle>.md
"""

from __future__ import annotations

import logging
from pathlib import Path

from .config import DEFAULT_MD_DIR, DEFAULT_OUTPUT_DIR
from .exceptions import (
    JobDescriptionError,
    MDFolderNotFoundError,
    NoMDFilesFoundError,
    TailorMCPError,
)
from .prompts import build_tailor_prompt
from .reader import read_all_md_files, read_jd_from_file, read_jd_from_folder

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# MCP Gateway Tool
# ──────────────────────────────────────────────────────────────────────


def tailor_resume_for_job(
    job_description_text: str | None = None,
    job_description_file: str | None = None,
    job_description_folder: str | None = None,
    md_folder: str | None = None,
    output_dir: str | None = None,
) -> str:
    """
    Generate an ATS-optimized resume tailored to a specific job description.

    This tool reads ALL generated Markdown files from the md/ folder
    (output of the 4 extraction tools) and combines them with the
    provided Job Description. It then returns a structured prompt to
    the calling LLM to generate a perfectly tailored resume.

    Input Methods (provide at least one):
        job_description_text:   Paste the JD directly as text.
        job_description_file:   Path to a JD file (TXT, PDF, DOCX, MD).
        job_description_folder: Path to a folder containing JD files.
                                All supported files will be read.
        If none provided:       Reads JD_INPUT_PATH from .env.

    Data Source:
        md_folder: Path to the md/ directory. Defaults to <project>/md/.
                   This folder must contain outputs from the other 4 tools.

    Output:
        output_dir: Where the tailored resume should be saved.
                    Defaults to md/tailored/.

    Returns:
        A structured prompt string for the host LLM containing:
          - System instructions for ATS optimization
          - The complete biography data from md/
          - The job description
          - File save instructions
    """
    project_root = Path(__file__).resolve().parent.parent

    try:
        # ── Step 1: Resolve and read the md/ folder ──────────────────
        md_path = Path(md_folder) if md_folder else project_root / DEFAULT_MD_DIR

        logger.info("Reading biography data from: %s", md_path)
        md_files = read_all_md_files(md_path)

        # Build the biography string with clear section headers
        biography_parts: list[str] = []
        for rel_path, content in md_files.items():
            biography_parts.append(
                f"══════ FILE: {rel_path} ══════\n{content}"
            )
        biography_data = "\n\n".join(biography_parts)

        logger.info(
            "Aggregated %d file(s), %d total characters",
            len(md_files), len(biography_data),
        )

        # ── Step 2: Resolve the Job Description ──────────────────────
        jd_text = _resolve_job_description(
            text=job_description_text,
            file=job_description_file,
            folder=job_description_folder,
        )

        logger.info("Job description loaded: %d characters", len(jd_text))

        # ── Step 3: Resolve output path ──────────────────────────────
        out_path = (
            Path(output_dir)
            if output_dir
            else project_root / DEFAULT_OUTPUT_DIR
        )
        out_path.mkdir(parents=True, exist_ok=True)

        # ── Step 4: Build and return the prompt ──────────────────────
        prompt = build_tailor_prompt(
            biography_data=biography_data,
            job_description=jd_text,
            output_path=str(out_path),
        )

        logger.info(
            "Prompt generated: %d characters. "
            "Returning to host LLM for resume generation.",
            len(prompt),
        )

        return prompt

    except (MDFolderNotFoundError, NoMDFilesFoundError) as e:
        logger.error("Data error: %s", e)
        return f"ERROR: {e}"

    except (JobDescriptionError, TailorMCPError) as e:
        logger.error("Input error: %s", e)
        return f"ERROR: {e}"

    except Exception as e:
        logger.exception("Unexpected error in tailor_resume_for_job")
        return f"ERROR: Unexpected error — {e}"


# ──────────────────────────────────────────────────────────────────────
# Job Description Resolution
# ──────────────────────────────────────────────────────────────────────


def _resolve_job_description(
    text: str | None = None,
    file: str | None = None,
    folder: str | None = None,
) -> str:
    """
    Resolve JD from the first available source:
      1. Direct text input
      2. Single file path (TXT, PDF, DOCX, MD)
      3. Folder of JD files
      4. JD_INPUT_PATH from .env (can be file or folder)

    Raises:
        JobDescriptionError: If no JD can be resolved from any source.
    """
    parts: list[str] = []

    # Source 1: Direct text
    if text and text.strip():
        parts.append(text.strip())
        logger.info("JD source: direct text (%d chars)", len(text.strip()))

    # Source 2: Single file
    if file:
        file_path = Path(file)
        try:
            content = read_jd_from_file(file_path)
            parts.append(content)
            logger.info("JD source: file — %s", file_path.name)
        except Exception as e:
            logger.warning("Could not read JD file '%s': %s", file, e)

    # Source 3: Folder
    if folder:
        folder_path = Path(folder)
        try:
            content = read_jd_from_folder(folder_path)
            parts.append(content)
            logger.info("JD source: folder — %s", folder_path)
        except Exception as e:
            logger.warning("Could not read JD folder '%s': %s", folder, e)

    # Source 4: .env fallback
    if not parts:
        try:
            from env_loader import get_env
            env_path = get_env("JD_INPUT_PATH")
            if env_path:
                p = Path(env_path)
                if p.is_file():
                    content = read_jd_from_file(p)
                    parts.append(content)
                    logger.info("JD source: .env file — %s", p.name)
                elif p.is_dir():
                    content = read_jd_from_folder(p)
                    parts.append(content)
                    logger.info("JD source: .env folder — %s", p)
        except Exception as e:
            logger.warning("Could not read JD from .env path: %s", e)

    if not parts:
        raise JobDescriptionError(
            "No job description provided.",
            details="Provide job_description_text, job_description_file, "
                    "job_description_folder, or set JD_INPUT_PATH in .env.",
        )

    return "\n\n".join(parts)
