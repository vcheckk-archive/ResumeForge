"""
Resume History MCP — Timeline
================================
Builds a chronological career evolution timeline from sorted RawResume
objects, tracking when each entity (skill, project, role, cert) first
appeared and how the profile evolved over versions.
"""

from __future__ import annotations

import logging
from datetime import datetime

from .schemas import RawResume, ResumeHistory, TimelineEntry

logger = logging.getLogger(__name__)


def build_timeline(resumes: list[RawResume], history: ResumeHistory) -> ResumeHistory:
    """
    Populate history.timeline with chronological events derived from
    comparing successive resume versions (oldest → newest).

    Modifies history in-place and returns it.
    """
    if not resumes:
        return history

    timeline: list[TimelineEntry] = []
    seen_skills: set[str] = set()
    seen_projects: set[str] = set()
    seen_certs: set[str] = set()

    for resume in resumes:
        date = resume.modified_date

        # ── New skills ─────────────────────────────────────────────────
        for skill in resume.skills:
            key = skill.lower().strip()
            if key and key not in seen_skills:
                seen_skills.add(key)
                timeline.append(TimelineEntry(
                    date=date,
                    source_file=resume.file_name,
                    event_type="skill_added",
                    label=f"Skill appeared: {skill}",
                    detail=f"First seen in '{resume.file_name}'",
                ))

        # ── New projects ───────────────────────────────────────────────
        for project in resume.projects:
            name = _project_name(project)
            key = name.lower().strip()
            if key and key not in seen_projects:
                seen_projects.add(key)
                timeline.append(TimelineEntry(
                    date=date,
                    source_file=resume.file_name,
                    event_type="project_added",
                    label=f"Project appeared: {name}",
                    detail=f"First seen in '{resume.file_name}'",
                ))

        # ── New roles ──────────────────────────────────────────────────
        for exp in resume.experiences:
            role_label = _experience_label(exp)
            timeline.append(TimelineEntry(
                date=date,
                source_file=resume.file_name,
                event_type="role_added",
                label=f"Role recorded: {role_label}",
                detail=f"From '{resume.file_name}' ({resume.resume_type})",
            ))

        # ── New certifications ─────────────────────────────────────────
        for cert in resume.certifications:
            key = cert.lower().strip()
            if key and key not in seen_certs:
                seen_certs.add(key)
                timeline.append(TimelineEntry(
                    date=date,
                    source_file=resume.file_name,
                    event_type="cert_added",
                    label=f"Certification: {cert}",
                    detail=f"First seen in '{resume.file_name}'",
                ))

    # Sort chronologically
    timeline.sort(key=lambda e: e.date)
    history.timeline = timeline

    logger.info("Timeline built: %d events from %d resume(s)", len(timeline), len(resumes))
    return history


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────


def _project_name(project: dict) -> str:
    return str(project.get("name", project.get("title", project.get("raw", ""))[:60]))


def _experience_label(exp: dict) -> str:
    role = str(exp.get("role", exp.get("title", "")))
    company = str(exp.get("company", exp.get("organization", "")))
    raw = str(exp.get("raw", ""))[:60]
    if role and company:
        return f"{role} @ {company}"
    if role:
        return role
    if company:
        return company
    return raw
