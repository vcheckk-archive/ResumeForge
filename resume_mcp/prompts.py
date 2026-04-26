"""
Resume History MCP — Prompts / Markdown Templates
====================================================
All output formatting is defined here.
Change template strings here to update the Markdown layout
without touching any logic files.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .schemas import ResumeHistory, TimelineEntry

# ── Date format ───────────────────────────────────────────────────────
DATE_FORMAT = "%B %Y"  # e.g. April 2024


def render_resume_history(history: "ResumeHistory") -> str:
    """Render the complete resume_history.md content."""
    sections: list[str] = []

    sections.append(_render_header(history))
    sections.append(_render_identity(history))
    sections.append(_render_timeline(history))
    sections.append(_render_experience(history))
    sections.append(_render_projects(history))
    sections.append(_render_skills(history))
    sections.append(_render_education(history))
    sections.append(_render_certifications(history))
    sections.append(_render_evolution_insights(history))
    sections.append(_render_unclassified(history))
    sections.append(_render_notes(history))

    return "\n\n---\n\n".join(s for s in sections if s.strip())


# ──────────────────────────────────────────────────────────────────────
# Section renderers
# ──────────────────────────────────────────────────────────────────────


def _render_header(history: "ResumeHistory") -> str:
    name = history.identity.get("name", "Unknown")
    generated = datetime.now().strftime(DATE_FORMAT)
    sources = len(history.source_files)
    return (
        f"# Career Profile — Derived from Resume History\n\n"
        f"> Generated: {generated}  \n"
        f"> Sources: {sources} resume file(s)  \n"
        f"> Files: {', '.join(history.source_files)}"
    )


def _render_identity(history: "ResumeHistory") -> str:
    identity = history.identity
    if not identity:
        return ""

    lines = ["## Identity"]
    field_labels = {
        "name": "Name",
        "email": "Email",
        "phone": "Phone",
        "linkedin": "LinkedIn",
        "github": "GitHub",
        "website": "Website",
    }
    for key, label in field_labels.items():
        val = identity.get(key, "")
        if val:
            lines.append(f"- **{label}:** {val}")

    return "\n".join(lines)


def _render_timeline(history: "ResumeHistory") -> str:
    if not history.timeline:
        return ""

    lines = ["## Career Timeline"]

    # Group by year
    from itertools import groupby
    sorted_events = sorted(history.timeline, key=lambda e: e.date)

    grouped: dict[int, list] = {}
    for event in sorted_events:
        year = event.date.year
        grouped.setdefault(year, []).append(event)

    for year in sorted(grouped.keys()):
        lines.append(f"\n### {year}")
        for event in grouped[year]:
            icon = {
                "skill_added":   "🛠",
                "project_added": "📦",
                "role_added":    "💼",
                "cert_added":    "🏅",
            }.get(event.event_type, "•")
            lines.append(f"- {icon} {event.label}")

    return "\n".join(lines)


def _render_experience(history: "ResumeHistory") -> str:
    if not history.experiences:
        return ""

    lines = ["## Experience"]
    for i, exp in enumerate(history.experiences, 1):
        role = exp.get("role", exp.get("title", f"Role #{i}"))
        company = exp.get("company", exp.get("organization", ""))
        dates = exp.get("dates", exp.get("period", ""))
        raw = exp.get("raw", "")
        description = exp.get("description", "")

        heading = f"### {role}"
        if company:
            heading += f" — {company}"
        lines.append(heading)
        if dates:
            lines.append(f"*{dates}*")
        if description:
            lines.append(description)
        elif raw:
            # Raw mode — preserve for LLM processing
            lines.append(f"```\n{raw}\n```")
        lines.append("")

    return "\n".join(lines)


def _render_projects(history: "ResumeHistory") -> str:
    if not history.projects:
        return ""

    lines = ["## Projects"]
    for i, proj in enumerate(history.projects, 1):
        name = proj.get("name", proj.get("title", f"Project #{i}"))
        description = proj.get("description", "")
        tech = proj.get("technologies", proj.get("tech", ""))
        raw = proj.get("raw", "")

        lines.append(f"### {name}")
        if tech:
            lines.append(f"**Tech:** {tech}")
        if description:
            lines.append(description)
        elif raw:
            lines.append(f"```\n{raw}\n```")
        lines.append("")

    return "\n".join(lines)


def _render_skills(history: "ResumeHistory") -> str:
    if not history.skills:
        return ""

    lines = ["## Skills"]

    # Group into buckets using basic heuristics
    languages = []
    frameworks = []
    tools = []
    other = []

    lang_keywords = {"python", "java", "javascript", "typescript", "c", "c++", "c#",
                     "go", "rust", "kotlin", "swift", "ruby", "php", "sql", "r",
                     "scala", "dart", "matlab", "bash", "html", "css"}
    framework_keywords = {"react", "angular", "vue", "django", "flask", "fastapi",
                          "spring", "express", "next", "nuxt", "tensorflow", "pytorch",
                          "keras", "sklearn", "scikit", "hadoop", "spark", "airflow"}
    tool_keywords = {"git", "docker", "kubernetes", "aws", "gcp", "azure", "linux",
                     "jenkins", "github", "gitlab", "postman", "jira", "figma",
                     "postgres", "mysql", "mongodb", "redis", "kafka", "terraform"}

    for skill in history.skills:
        sk = skill.lower()
        if any(kw in sk for kw in lang_keywords):
            languages.append(skill)
        elif any(kw in sk for kw in framework_keywords):
            frameworks.append(skill)
        elif any(kw in sk for kw in tool_keywords):
            tools.append(skill)
        else:
            other.append(skill)

    if languages:
        lines.append(f"**Languages:** {', '.join(dict.fromkeys(languages))}")
    if frameworks:
        lines.append(f"**Frameworks & Libraries:** {', '.join(dict.fromkeys(frameworks))}")
    if tools:
        lines.append(f"**Tools & Platforms:** {', '.join(dict.fromkeys(tools))}")
    if other:
        lines.append(f"**Other:** {', '.join(dict.fromkeys(other))}")

    return "\n".join(lines)


def _render_education(history: "ResumeHistory") -> str:
    if not history.education:
        return ""

    lines = ["## Education"]
    for edu in history.education:
        institution = edu.get("institution", edu.get("school", ""))
        degree = edu.get("degree", "")
        field = edu.get("field", edu.get("major", ""))
        dates = edu.get("dates", edu.get("period", ""))
        raw = edu.get("raw", "")

        if institution or degree:
            heading = f"### {degree}" if degree else "### Degree"
            if institution:
                heading += f" — {institution}"
            lines.append(heading)
            if field:
                lines.append(f"**Field:** {field}")
            if dates:
                lines.append(f"*{dates}*")
        elif raw:
            lines.append(f"```\n{raw}\n```")
        lines.append("")

    return "\n".join(lines)


def _render_certifications(history: "ResumeHistory") -> str:
    if not history.certifications:
        return ""

    lines = ["## Certifications"]
    for cert in history.certifications:
        lines.append(f"- {cert}")

    return "\n".join(lines)


def _render_evolution_insights(history: "ResumeHistory") -> str:
    lines = ["## Career Evolution Insights"]

    # Count skill growth across timeline
    skill_events = [e for e in history.timeline if e.event_type == "skill_added"]
    proj_events  = [e for e in history.timeline if e.event_type == "project_added"]
    role_events  = [e for e in history.timeline if e.event_type == "role_added"]
    cert_events  = [e for e in history.timeline if e.event_type == "cert_added"]

    lines.append(
        f"- **Total unique skills accumulated:** {len(history.skills)}"
    )
    if skill_events:
        lines.append(
            f"- **Skill growth events tracked:** {len(skill_events)} "
            f"(first: {skill_events[0].date.strftime(DATE_FORMAT)}, "
            f"latest: {skill_events[-1].date.strftime(DATE_FORMAT)})"
        )
    lines.append(
        f"- **Unique projects across all resumes:** {len(history.projects)}"
    )
    lines.append(
        f"- **Experience entries (post-dedup):** {len(history.experiences)}"
    )
    if history.dedup_report:
        dr = history.dedup_report
        lines.append(
            f"- **Items deduplicated:** "
            f"{dr.total_input_items - dr.total_output_items} "
            f"({dr.total_input_items} → {dr.total_output_items})"
        )
        if dr.projects_merged:
            lines.append(
                f"- **Projects merged:** {', '.join(dr.projects_merged[:5])}"
                + (" ..." if len(dr.projects_merged) > 5 else "")
            )
    if len(history.source_files) > 1:
        lines.append(
            f"\n> ⚠️ **Note:** This profile was built from {len(history.source_files)} "
            f"resume versions. Unclassified sections are preserved below for "
            f"LLM-assisted enrichment."
        )

    return "\n".join(lines)


def _render_unclassified(history: "ResumeHistory") -> str:
    if not history.raw_sections_unclassified:
        return ""

    lines = [
        "## Unclassified Raw Sections",
        "> These sections could not be automatically categorized.",
        "> Pass to an LLM for further extraction and enrichment.\n",
    ]
    for sec in history.raw_sections_unclassified:
        lines.append(f"### {sec.heading}")
        lines.append(f"```\n{sec.content}\n```")
        lines.append("")

    return "\n".join(lines)


def _render_notes(history: "ResumeHistory") -> str:
    lines = ["## Notes"]

    if history.extraction_warnings:
        lines.append("### Extraction Warnings")
        for warn in history.extraction_warnings:
            lines.append(f"- ⚠️ {warn}")

    lines.append("\n### Processing Metadata")
    lines.append(f"- Source files: {', '.join(history.source_files)}")
    lines.append(f"- Skills deduplicated: {history.dedup_report.skills_deduplicated}")
    lines.append(f"- Certs deduplicated: {history.dedup_report.certs_deduplicated}")

    return "\n".join(lines)
