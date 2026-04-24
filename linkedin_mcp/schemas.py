"""
Data Schemas
============

Type-safe dataclasses that flow between parser → markdown_writer.
Every field is documented.  All fields use ``str | None`` for optional
values so the writer can gracefully handle missing data.

Design Principles:
    - Immutable data containers (frozen where practical).
    - No business logic — pure data.
    - Easily serializable for future JSON/API output.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Identity:
    """Core identity extracted from Profile.csv + Email Addresses.csv."""

    first_name: str
    last_name: str
    headline: str | None = None
    location: str | None = None
    email: str | None = None
    websites: list[str] = field(default_factory=list)
    industry: str | None = None


@dataclass
class Summary:
    """Professional summary / about section."""

    text: str


@dataclass
class Experience:
    """A single work experience entry from Positions.csv."""

    title: str
    company: str
    description: str | None = None
    location: str | None = None
    started_on: str | None = None
    finished_on: str | None = None


@dataclass
class Education:
    """A single education entry from Education.csv."""

    school_name: str
    degree: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    notes: str | None = None
    activities: str | None = None


@dataclass
class Certification:
    """A single certification from Certifications.csv."""

    name: str
    authority: str | None = None
    url: str | None = None
    started_on: str | None = None
    finished_on: str | None = None
    license_number: str | None = None


@dataclass
class Project:
    """A single project from Projects.csv."""

    title: str
    description: str | None = None
    url: str | None = None
    started_on: str | None = None
    finished_on: str | None = None


@dataclass
class SkillGroup:
    """A named group of skills (e.g. "AI / ML / Data Science")."""

    category: str
    skills: list[str] = field(default_factory=list)


@dataclass
class ParsedArchive:
    """
    Complete parsed output from the LinkedIn archive.

    This is the single data object passed from the parser to the writer.
    """

    identity: Identity | None = None
    summary: Summary | None = None
    experiences: list[Experience] = field(default_factory=list)
    education: list[Education] = field(default_factory=list)
    skill_groups: list[SkillGroup] = field(default_factory=list)
    certifications: list[Certification] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)


@dataclass
class IngestResult:
    """
    Return value of the ``linkedin_ingest_archive`` MCP tool.

    Designed to give the caller full visibility into what happened.
    """

    processed_files: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)
    output_paths: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    success: bool = True
