"""
CSV Parser Module
=================

Handles discovery, validation, and parsing of LinkedIn archive CSV files.

Architecture:
    1. ``scan_directory()`` walks the archive folder, classifying every
       file/folder as *relevant*, *skipped*, or *unknown*.
    2. ``parse_archive()`` orchestrates CSV reading and maps raw rows
       into the typed dataclasses defined in ``schemas.py``.

All CSV reads go through ``_safe_read_csv()`` which tries multiple
encodings and returns a cleaned DataFrame.

Adapting to new formats:
    - Add/modify entries in ``config.RELEVANT_FILES``
    - Add a ``_parse_<section>()`` method below
    - Register it in ``_SECTION_PARSERS`` at the bottom
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from . import config
from .exceptions import (
    ArchiveNotFoundError,
    CSVParsingError,
    InvalidArchiveError,
)
from .schemas import (
    Certification,
    Education,
    Experience,
    Identity,
    ParsedArchive,
    Project,
    SkillGroup,
    Summary,
)
from .utils import clean_text, parse_website_field, safe_get

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────
# Low-level CSV I/O
# ──────────────────────────────────────────────────────────────────────────


def _safe_read_csv(file_path: Path) -> pd.DataFrame:
    """
    Read a CSV file with encoding fallback and basic cleanup.

    Tries each encoding in ``config.CSV_ENCODINGS`` in order.
    Strips whitespace from all column headers and string values.

    Raises:
        CSVParsingError: if no encoding succeeds.
    """
    last_error: Exception | None = None

    for encoding in config.CSV_ENCODINGS:
        try:
            df = pd.read_csv(file_path, encoding=encoding, on_bad_lines="skip")

            # Clean headers
            df.columns = [col.strip() for col in df.columns]

            # Clean string values
            for col in df.select_dtypes(include=["object"]).columns:
                df[col] = df[col].map(
                    lambda x: x.strip() if isinstance(x, str) else x
                )

            # Drop fully-empty rows
            df.dropna(how="all", inplace=True)

            logger.info("Parsed %s (%d rows, encoding=%s)", file_path.name, len(df), encoding)
            return df

        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue

    raise CSVParsingError(str(file_path), str(last_error))


def _headers_match(df: pd.DataFrame, required: list[str]) -> bool:
    """Check whether a DataFrame contains all required columns (case-insensitive)."""
    actual = {col.lower() for col in df.columns}
    return all(h.lower() in actual for h in required)


# ──────────────────────────────────────────────────────────────────────────
# Directory scanning
# ──────────────────────────────────────────────────────────────────────────


def scan_directory(folder_path: str) -> dict[str, list[str]]:
    """
    Recursively scan the archive folder and classify every item.

    Returns:
        {
            "relevant": {"profile": "/path/Profile.csv", ...},
            "skipped":  ["Connections.csv", "Jobs/", ...],
            "unknown":  ["SomeOtherFile.csv", ...],
        }
    """
    root = Path(folder_path)
    if not root.exists() or not root.is_dir():
        raise ArchiveNotFoundError(folder_path)

    relevant: dict[str, Path] = {}
    skipped: list[str] = []
    unknown: list[str] = []

    # Build a lookup: lowercase filename → section name
    name_lookup: dict[str, str] = {}
    for section, meta in config.RELEVANT_FILES.items():
        name_lookup[meta["filename"].lower()] = section

    # Walk the directory tree
    for item in sorted(root.rglob("*")):
        relative = item.relative_to(root)
        relative_str = str(relative)

        # Check if excluded
        if _is_excluded(relative):
            skipped.append(relative_str)
            continue

        # Skip directories themselves (we process files)
        if item.is_dir():
            continue

        # Only process CSV files
        if item.suffix.lower() != ".csv":
            unknown.append(relative_str)
            continue

        # Try filename match
        matched_section = name_lookup.get(item.name.lower())
        if matched_section:
            relevant[matched_section] = item
            continue

        # Try header-based fallback detection
        fallback_section = _detect_by_headers(item)
        if fallback_section:
            relevant[fallback_section] = item
            continue

        unknown.append(relative_str)

    return {
        "relevant": {k: str(v) for k, v in relevant.items()},
        "skipped": skipped,
        "unknown": unknown,
    }


def _is_excluded(relative_path: Path) -> bool:
    """Check if a path matches any exclusion pattern."""
    parts = relative_path.parts
    for pattern in config.EXCLUDED_PATTERNS:
        pattern_lower = pattern.lower()
        for part in parts:
            if part.lower() == pattern_lower:
                return True
    return False


def _detect_by_headers(file_path: Path) -> str | None:
    """
    Attempt to identify a CSV by reading its headers and matching against
    known schemas.  Used as fallback when filename doesn't match.
    """
    try:
        df = pd.read_csv(file_path, nrows=0, encoding="utf-8")
        for section, meta in config.RELEVANT_FILES.items():
            if _headers_match(df, meta["required_headers"]):
                logger.info("Header-match: %s → section '%s'", file_path.name, section)
                return section
    except Exception:  # noqa: BLE001
        pass
    return None


# ──────────────────────────────────────────────────────────────────────────
# Section parsers
# ──────────────────────────────────────────────────────────────────────────


def _parse_identity(relevant: dict[str, Path], errors: list[str]) -> Identity | None:
    """Parse Profile.csv + Email Addresses.csv → Identity."""
    profile_path = relevant.get("profile")
    if not profile_path:
        return None

    try:
        df = _safe_read_csv(Path(profile_path))
        if df.empty:
            return None

        row = df.iloc[0]

        # Extract email from separate file
        email: str | None = None
        email_path = relevant.get("email")
        if email_path:
            try:
                edf = _safe_read_csv(Path(email_path))
                if not edf.empty:
                    # Prefer primary email
                    primary = edf[edf.get("Primary", pd.Series(dtype=str)).str.lower() == "yes"]
                    if not primary.empty:
                        email = safe_get(primary.iloc[0], "Email Address")
                    else:
                        email = safe_get(edf.iloc[0], "Email Address")
            except CSVParsingError as exc:
                errors.append(str(exc))

        # Parse websites
        websites = parse_website_field(safe_get(row, "Websites"))

        return Identity(
            first_name=safe_get(row, "First Name") or "Unknown",
            last_name=safe_get(row, "Last Name") or "",
            headline=safe_get(row, "Headline"),
            location=safe_get(row, "Geo Location"),
            email=email,
            websites=websites,
            industry=safe_get(row, "Industry"),
        )

    except CSVParsingError as exc:
        errors.append(str(exc))
        return None


def _parse_summary(relevant: dict[str, Path], identity_summary: str | None, errors: list[str]) -> Summary | None:
    """
    Parse summary from Profile.csv (Summary column) and Profile Summary.csv.

    Profile.csv's Summary field is the primary source.
    Profile Summary.csv is used as fallback.
    """
    # Primary: Profile.csv Summary field
    if identity_summary:
        return Summary(text=identity_summary)

    # Fallback: Profile Summary.csv
    summary_path = relevant.get("profile_summary")
    if summary_path:
        try:
            df = _safe_read_csv(Path(summary_path))
            if not df.empty:
                text = clean_text(df.iloc[0, 0])
                if text:
                    return Summary(text=text)
        except CSVParsingError as exc:
            errors.append(str(exc))

    return None


def _parse_experiences(relevant: dict[str, Path], errors: list[str]) -> list[Experience]:
    """Parse Positions.csv → list of Experience."""
    path = relevant.get("positions")
    if not path:
        return []

    try:
        df = _safe_read_csv(Path(path))
        experiences: list[Experience] = []
        for _, row in df.iterrows():
            title = safe_get(row, "Title")
            company = safe_get(row, "Company Name")
            if not title and not company:
                continue

            experiences.append(
                Experience(
                    title=title or "Untitled Role",
                    company=company or "Unknown Company",
                    description=safe_get(row, "Description"),
                    location=safe_get(row, "Location"),
                    started_on=safe_get(row, "Started On"),
                    finished_on=safe_get(row, "Finished On"),
                )
            )
        return experiences

    except CSVParsingError as exc:
        errors.append(str(exc))
        return []


def _parse_education(relevant: dict[str, Path], errors: list[str]) -> list[Education]:
    """Parse Education.csv → list of Education."""
    path = relevant.get("education")
    if not path:
        return []

    try:
        df = _safe_read_csv(Path(path))
        entries: list[Education] = []
        for _, row in df.iterrows():
            school = safe_get(row, "School Name")
            if not school:
                continue

            entries.append(
                Education(
                    school_name=school,
                    degree=safe_get(row, "Degree Name"),
                    start_date=safe_get(row, "Start Date"),
                    end_date=safe_get(row, "End Date"),
                    notes=safe_get(row, "Notes"),
                    activities=safe_get(row, "Activities"),
                )
            )
        return entries

    except CSVParsingError as exc:
        errors.append(str(exc))
        return []


def _parse_skills(relevant: dict[str, Path], errors: list[str]) -> list[SkillGroup]:
    """
    Parse Skills.csv and group into categories defined in config.

    Skills are matched against category keywords (case-insensitive).
    First matching category wins.  Unmatched skills go to "Other".
    """
    path = relevant.get("skills")
    if not path:
        return []

    try:
        df = _safe_read_csv(Path(path))
        all_skills: list[str] = []
        for _, row in df.iterrows():
            name = safe_get(row, "Name")
            if name:
                all_skills.append(name)

        if not all_skills:
            return []

        # Group skills into categories
        grouped: dict[str, list[str]] = {}
        for cat in config.SKILL_CATEGORIES:
            grouped[cat["name"]] = []  # type: ignore[index]

        for skill in all_skills:
            skill_lower = skill.lower()
            placed = False
            for cat in config.SKILL_CATEGORIES:
                cat_name: str = cat["name"]  # type: ignore[assignment]
                keywords: set[str] = cat["keywords"]  # type: ignore[assignment]
                if cat_name == "Other":
                    continue  # handle at the end
                if skill_lower in keywords:
                    grouped[cat_name].append(skill)
                    placed = True
                    break
            if not placed:
                grouped["Other"].append(skill)

        # Build SkillGroup list, omitting empty categories
        return [
            SkillGroup(category=name, skills=skills)
            for name, skills in grouped.items()
            if skills
        ]

    except CSVParsingError as exc:
        errors.append(str(exc))
        return []


def _parse_certifications(relevant: dict[str, Path], errors: list[str]) -> list[Certification]:
    """Parse Certifications.csv → list of Certification."""
    path = relevant.get("certifications")
    if not path:
        return []

    try:
        df = _safe_read_csv(Path(path))
        certs: list[Certification] = []
        for _, row in df.iterrows():
            name = safe_get(row, "Name")
            if not name:
                continue

            certs.append(
                Certification(
                    name=name,
                    authority=safe_get(row, "Authority"),
                    url=safe_get(row, "Url"),
                    started_on=safe_get(row, "Started On"),
                    finished_on=safe_get(row, "Finished On"),
                    license_number=safe_get(row, "License Number"),
                )
            )
        return certs

    except CSVParsingError as exc:
        errors.append(str(exc))
        return []


def _parse_projects(relevant: dict[str, Path], errors: list[str]) -> list[Project]:
    """Parse Projects.csv → list of Project."""
    path = relevant.get("projects")
    if not path:
        return []

    try:
        df = _safe_read_csv(Path(path))
        projects: list[Project] = []
        for _, row in df.iterrows():
            title = safe_get(row, "Title")
            if not title:
                continue

            projects.append(
                Project(
                    title=title,
                    description=safe_get(row, "Description"),
                    url=safe_get(row, "Url"),
                    started_on=safe_get(row, "Started On"),
                    finished_on=safe_get(row, "Finished On"),
                )
            )
        return projects

    except CSVParsingError as exc:
        errors.append(str(exc))
        return []


# ──────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────


def parse_archive(folder_path: str) -> tuple[ParsedArchive, dict]:
    """
    Parse a LinkedIn archive folder into a structured ``ParsedArchive``.

    Args:
        folder_path: Absolute path to the extracted archive folder.

    Returns:
        A tuple of (ParsedArchive, scan_result) where scan_result contains
        the lists of relevant/skipped/unknown files.

    Raises:
        ArchiveNotFoundError: if the folder doesn't exist.
        InvalidArchiveError:  if no relevant CSVs are found.
    """
    # Step 1: Scan directory
    scan = scan_directory(folder_path)
    relevant = scan["relevant"]

    if not relevant:
        raise InvalidArchiveError(folder_path)

    errors: list[str] = []

    # Step 2: Extract summary text from Profile.csv for the Summary parser
    profile_summary_text: str | None = None
    profile_path = relevant.get("profile")
    if profile_path:
        try:
            pdf = _safe_read_csv(Path(profile_path))
            if not pdf.empty:
                profile_summary_text = clean_text(pdf.iloc[0].get("Summary"))
        except CSVParsingError:
            pass  # will be caught again in _parse_identity

    # Step 3: Parse each section
    archive = ParsedArchive(
        identity=_parse_identity(relevant, errors),
        summary=_parse_summary(relevant, profile_summary_text, errors),
        experiences=_parse_experiences(relevant, errors),
        education=_parse_education(relevant, errors),
        skill_groups=_parse_skills(relevant, errors),
        certifications=_parse_certifications(relevant, errors),
        projects=_parse_projects(relevant, errors),
    )

    # Attach errors to scan result for reporting
    scan["errors"] = errors

    return archive, scan
