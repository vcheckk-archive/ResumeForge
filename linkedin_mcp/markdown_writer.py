"""
Markdown Writer Module
======================

Converts a ``ParsedArchive`` into clean, resume-ready Markdown files.

Each ``write_*`` function produces a single ``.md`` file's content using
templates from ``prompts.py``.  The ``write_all()`` function orchestrates
writing all files to the output directory.

Design Principles:
    - Uses templates from ``prompts.py`` — no hardcoded format strings.
    - Gracefully handles missing/empty data with fallback notices.
    - Each writer is independently testable.
"""

from __future__ import annotations

import logging
from pathlib import Path

from . import prompts
from .exceptions import OutputWriteError
from .schemas import ParsedArchive
from .utils import ensure_directory, format_duration

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────
# Individual section writers
# ──────────────────────────────────────────────────────────────────────────


def write_identity(archive: ParsedArchive) -> str:
    """Generate ``identity.md`` content."""
    lines: list[str] = [prompts.IDENTITY_HEADER]

    identity = archive.identity
    if not identity:
        lines.append(prompts.NO_DATA_NOTICE)
        return "\n".join(lines)

    lines.append(prompts.IDENTITY_NAME.format(
        first_name=identity.first_name,
        last_name=identity.last_name,
    ))

    if identity.headline:
        lines.append(prompts.IDENTITY_HEADLINE.format(headline=identity.headline))

    if identity.location:
        lines.append(prompts.IDENTITY_LOCATION.format(location=identity.location))

    if identity.email:
        lines.append(prompts.IDENTITY_EMAIL.format(email=identity.email))

    if identity.industry:
        lines.append(prompts.IDENTITY_INDUSTRY.format(industry=identity.industry))

    for url in identity.websites:
        lines.append(prompts.IDENTITY_WEBSITE.format(url=url))

    return "".join(lines)


def write_summary(archive: ParsedArchive) -> str:
    """Generate ``summary.md`` content."""
    lines: list[str] = [prompts.SUMMARY_HEADER, "\n"]

    if archive.summary and archive.summary.text:
        lines.append(prompts.SUMMARY_BODY.format(text=archive.summary.text))
    else:
        lines.append(prompts.NO_DATA_NOTICE)

    return "".join(lines)


def write_experience(archive: ParsedArchive) -> str:
    """Generate ``experience.md`` content."""
    lines: list[str] = [prompts.EXPERIENCE_HEADER, "\n"]

    if not archive.experiences:
        lines.append(prompts.NO_DATA_NOTICE)
        return "".join(lines)

    for exp in archive.experiences:
        duration = format_duration(exp.started_on, exp.finished_on)
        location_line = ""
        if exp.location:
            location_line = prompts.EXPERIENCE_LOCATION_LINE.format(location=exp.location)

        description_block = ""
        if exp.description:
            description_block = prompts.EXPERIENCE_DESCRIPTION.format(description=exp.description)

        lines.append(prompts.EXPERIENCE_ENTRY.format(
            title=exp.title,
            company=exp.company,
            duration=duration,
            location_line=location_line,
            description_block=description_block,
        ))

    return "".join(lines)


def write_education(archive: ParsedArchive) -> str:
    """Generate ``education.md`` content."""
    lines: list[str] = [prompts.EDUCATION_HEADER, "\n"]

    if not archive.education:
        lines.append(prompts.NO_DATA_NOTICE)
        return "".join(lines)

    for edu in archive.education:
        duration = format_duration(edu.start_date, edu.end_date)
        notes_line = ""
        if edu.notes:
            notes_line = prompts.EDUCATION_NOTES_LINE.format(notes=edu.notes)

        degree_display = edu.degree or "Education"

        lines.append(prompts.EDUCATION_ENTRY.format(
            degree=degree_display,
            school_name=edu.school_name,
            duration=duration,
            notes_line=notes_line,
        ))

    return "".join(lines)


def write_skills(archive: ParsedArchive) -> str:
    """Generate ``skills.md`` content with categorized grouping."""
    lines: list[str] = [prompts.SKILLS_HEADER, "\n"]

    if not archive.skill_groups:
        lines.append(prompts.NO_DATA_NOTICE)
        return "".join(lines)

    for group in archive.skill_groups:
        lines.append(prompts.SKILLS_CATEGORY_HEADER.format(category=group.category))
        for skill in sorted(group.skills):
            lines.append(prompts.SKILLS_ITEM.format(skill=skill))
        lines.append("\n")

    return "".join(lines)


def write_certifications(archive: ParsedArchive) -> str:
    """Generate ``certifications.md`` content."""
    lines: list[str] = [prompts.CERTIFICATIONS_HEADER, "\n"]

    if not archive.certifications:
        lines.append(prompts.NO_DATA_NOTICE)
        return "".join(lines)

    for cert in archive.certifications:
        date = format_duration(cert.started_on, cert.finished_on)

        license_line = ""
        if cert.license_number:
            license_line = prompts.CERTIFICATION_LICENSE_LINE.format(
                license_number=cert.license_number
            )

        url_line = ""
        if cert.url:
            url_line = prompts.CERTIFICATION_URL_LINE.format(url=cert.url)

        lines.append(prompts.CERTIFICATION_ENTRY.format(
            name=cert.name,
            authority=cert.authority or "N/A",
            date=date,
            license_line=license_line,
            url_line=url_line,
        ))

    return "".join(lines)


def write_projects(archive: ParsedArchive) -> str:
    """Generate ``projects.md`` content."""
    lines: list[str] = [prompts.PROJECTS_HEADER, "\n"]

    if not archive.projects:
        lines.append(prompts.NO_DATA_NOTICE)
        return "".join(lines)

    for proj in archive.projects:
        duration = format_duration(proj.started_on, proj.finished_on)

        url_line = ""
        if proj.url:
            url_line = prompts.PROJECT_URL_LINE.format(url=proj.url)

        description = proj.description or "_No description provided._"

        lines.append(prompts.PROJECT_ENTRY.format(
            title=proj.title,
            duration=duration,
            url_line=url_line,
            description=description,
        ))

    return "".join(lines)


# ──────────────────────────────────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────────────────────────────────

# Map of output filename → writer function
_WRITERS: dict[str, callable] = {
    "identity.md": write_identity,
    "summary.md": write_summary,
    "experience.md": write_experience,
    "education.md": write_education,
    "skills.md": write_skills,
    "certifications.md": write_certifications,
    "projects.md": write_projects,
}


def write_all(archive: ParsedArchive, output_dir: Path) -> list[str]:
    """
    Write all Markdown files to the output directory.

    Args:
        archive:    Parsed LinkedIn data.
        output_dir: Target directory (created if needed).

    Returns:
        List of absolute paths to written files.

    Raises:
        OutputWriteError: if any file cannot be written.
    """
    ensure_directory(output_dir)
    written: list[str] = []

    for filename, writer_fn in _WRITERS.items():
        filepath = output_dir / filename
        try:
            content = writer_fn(archive)
            filepath.write_text(content, encoding="utf-8")
            written.append(str(filepath))
            logger.info("Wrote %s (%d bytes)", filename, len(content))
        except Exception as exc:
            raise OutputWriteError(str(filepath), str(exc)) from exc

    return written
