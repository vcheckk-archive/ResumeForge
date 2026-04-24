"""
Markdown Writer — GitHub MCP
=============================

Generates per-repo project .md files and the portfolio summary .md.
Uses templates from prompts.py. No hardcoded format strings.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from . import config, prompts
from .exceptions import OutputWriteError
from .schemas import (
    PortfolioSummary,
    ProjectContext,
    ProjectDocument,
    RepoDetail,
)

logger = logging.getLogger(__name__)


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


# ──────────────────────────────────────────────────────────────────────
# Per-Repo Markdown
# ──────────────────────────────────────────────────────────────────────


def write_project_md(doc: ProjectDocument, output_dir: Path) -> str:
    """
    Generate a single <repo_name>.md file.

    Args:
        doc: ProjectDocument with repo detail + optional user context.
        output_dir: Directory for the projects/ subfolder.

    Returns:
        Absolute path to the written file.
    """
    projects_dir = _ensure_dir(output_dir / config.PROJECTS_SUBDIR)
    repo = doc.repo
    ctx = doc.context or ProjectContext()

    lines: list[str] = []

    # Header
    lines.append(prompts.PROJECT_HEADER.format(name=repo.name))

    # Overview — merge README first paragraph + description + user context
    overview = _build_overview(repo, ctx)
    lines.append(prompts.PROJECT_OVERVIEW.format(description=overview))

    # Problem Statement
    problem = ctx.problem or _extract_readme_section(repo.readme_text, "problem")
    if problem:
        lines.append(prompts.PROJECT_PROBLEM.format(problem=problem))

    # Solution
    solution = _extract_readme_section(repo.readme_text, "solution|how it works|architecture")
    if solution:
        lines.append(prompts.PROJECT_SOLUTION.format(solution=solution))

    # Tech Stack
    if repo.tech_stack:
        lines.append(prompts.PROJECT_TECH_STACK_HEADER)
        for category, items in repo.tech_stack.items():
            lines.append(prompts.PROJECT_TECH_CATEGORY.format(category=category))
            for item in items:
                lines.append(prompts.PROJECT_TECH_ITEM.format(item=item))
            lines.append("\n")

    # Key Features
    features = repo.inferred_features
    if ctx.key_features:
        # User-provided features take priority
        features = [f.strip() for f in ctx.key_features.split(",") if f.strip()]
    if features:
        lines.append(prompts.PROJECT_FEATURES_HEADER)
        for feat in features:
            lines.append(prompts.PROJECT_FEATURE_ITEM.format(feature=feat))
        lines.append("\n")

    # Challenges & Learnings
    challenges = ctx.challenges or _extract_readme_section(repo.readme_text, "challenge|learning|lesson")
    if challenges:
        lines.append(prompts.PROJECT_CHALLENGES.format(challenges=challenges))

    # Impact / Results
    impact = ctx.impact or _extract_readme_section(repo.readme_text, "impact|result|outcome|demo")
    if impact:
        lines.append(prompts.PROJECT_IMPACT.format(impact=impact))

    # Project Structure (top-level only)
    if repo.top_level_structure:
        structure = "\n".join(repo.top_level_structure[:20])
        lines.append(prompts.PROJECT_STRUCTURE.format(structure=structure))

    # Repository Details
    lines.append(prompts.PROJECT_REPO_DETAILS.format(
        url=repo.url or "N/A",
        language=repo.primary_language or "N/A",
        stars=repo.stars,
        created=repo.created_at or "N/A",
        updated=repo.updated_at or "N/A",
    ))

    # Write file
    safe_name = re.sub(r'[^\w\-]', '_', repo.name.lower())
    filepath = projects_dir / f"{safe_name}.md"

    try:
        content = "".join(lines)
        filepath.write_text(content, encoding="utf-8")
        logger.info("Wrote %s (%d bytes)", filepath.name, len(content))
        return str(filepath)
    except Exception as exc:
        raise OutputWriteError(str(filepath), str(exc)) from exc


# ──────────────────────────────────────────────────────────────────────
# Portfolio Summary
# ──────────────────────────────────────────────────────────────────────


def write_summary_md(
    documents: list[ProjectDocument], output_dir: Path
) -> str:
    """
    Generate projects_summary.md aggregating all processed repos.

    Returns:
        Absolute path to the written summary file.
    """
    _ensure_dir(output_dir)
    summary = _build_portfolio_summary(documents)
    lines: list[str] = []

    # Header
    lines.append(prompts.SUMMARY_HEADER)

    # Total projects
    lines.append(prompts.SUMMARY_TOTAL.format(count=summary.total_projects))

    # Tech Stack Overview
    if summary.all_tech_stack:
        lines.append(prompts.SUMMARY_TECH_HEADER)
        for category, items in sorted(summary.all_tech_stack.items()):
            lines.append(prompts.SUMMARY_TECH_CATEGORY.format(category=category))
            for item in sorted(items):
                lines.append(prompts.SUMMARY_TECH_ITEM.format(item=item))
            lines.append("\n")

    # Key Domains
    if summary.all_domains:
        lines.append(prompts.SUMMARY_DOMAINS_HEADER)
        for domain in sorted(summary.all_domains):
            lines.append(prompts.SUMMARY_DOMAIN_ITEM.format(domain=domain))
        lines.append("\n")

    # Highlight Projects (top 5 by stars, then by features)
    if summary.highlight_projects:
        lines.append(prompts.SUMMARY_HIGHLIGHTS_HEADER)
        for doc in documents:
            if doc.repo.name in summary.highlight_projects:
                tech_str = ", ".join(
                    item
                    for items in doc.repo.tech_stack.values()
                    for item in items[:3]
                ) or "N/A"
                lines.append(prompts.SUMMARY_HIGHLIGHT_ENTRY.format(
                    name=doc.repo.name,
                    description=doc.repo.description or "_No description_",
                    tech=tech_str,
                    stars=doc.repo.stars,
                ))

    # Skill Signals
    if summary.skill_signals:
        lines.append(prompts.SUMMARY_SKILLS_HEADER)
        for skill in summary.skill_signals:
            lines.append(prompts.SUMMARY_SKILL_ITEM.format(skill=skill))
        lines.append("\n")

    filepath = output_dir / config.SUMMARY_FILENAME

    try:
        content = "".join(lines)
        filepath.write_text(content, encoding="utf-8")
        logger.info("Wrote %s (%d bytes)", filepath.name, len(content))
        return str(filepath)
    except Exception as exc:
        raise OutputWriteError(str(filepath), str(exc)) from exc


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────


def _build_overview(repo: RepoDetail, ctx: ProjectContext) -> str:
    """Build overview by merging description, README intro, and user context."""
    parts: list[str] = []

    if repo.description:
        parts.append(repo.description)

    if ctx.role:
        parts.append(f"**Role:** {ctx.role}")

    if ctx.technologies:
        parts.append(f"**Technologies:** {ctx.technologies}")

    # Extract first paragraph from README
    if repo.readme_text:
        first_para = _extract_first_paragraph(repo.readme_text)
        if first_para and first_para != repo.description:
            parts.append(first_para)

    return "\n\n".join(parts) if parts else "_No overview available._"


def _extract_first_paragraph(readme: str) -> str | None:
    """Extract the first non-heading, non-empty paragraph from README."""
    lines = readme.split("\n")
    paragraph_lines: list[str] = []
    started = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if started:
                break
            continue
        if stripped.startswith("#"):
            if started:
                break
            continue
        if stripped.startswith("![") or stripped.startswith("<"):
            continue  # Skip images and HTML
        started = True
        paragraph_lines.append(stripped)

    text = " ".join(paragraph_lines).strip()
    return text[:500] if text else None


def _extract_readme_section(
    readme: str | None, pattern: str
) -> str | None:
    """Extract content under a heading matching the pattern."""
    if not readme:
        return None

    lines = readme.split("\n")
    section_lines: list[str] = []
    in_section = False

    for line in lines:
        stripped = line.strip()
        if re.match(rf"^#{1,3}\s*.*({pattern})", stripped, re.IGNORECASE):
            in_section = True
            continue
        if in_section and re.match(r"^#{1,3}\s+", stripped):
            break
        if in_section and stripped:
            section_lines.append(stripped)

    text = "\n".join(section_lines).strip()
    return text[:1000] if text else None


def _build_portfolio_summary(documents: list[ProjectDocument]) -> PortfolioSummary:
    """Aggregate data across all project documents."""
    summary = PortfolioSummary(total_projects=len(documents))

    for doc in documents:
        repo = doc.repo

        # Languages
        for lang in repo.languages:
            summary.all_languages[lang.name] = (
                summary.all_languages.get(lang.name, 0) + lang.bytes
            )

        # Tech stack
        for cat, items in repo.tech_stack.items():
            if cat not in summary.all_tech_stack:
                summary.all_tech_stack[cat] = set()
            summary.all_tech_stack[cat].update(items)

        # Domains
        summary.all_domains.update(repo.domains)

    # Highlight projects: top 5 by stars, then by tech stack breadth
    sorted_docs = sorted(
        documents,
        key=lambda d: (d.repo.stars, len(d.repo.tech_stack)),
        reverse=True,
    )
    summary.highlight_projects = [d.repo.name for d in sorted_docs[:5]]

    # Skill signals: derived from aggregated tech stack
    skill_counts: dict[str, int] = {}
    for doc in documents:
        for cat in doc.repo.tech_stack:
            skill_counts[cat] = skill_counts.get(cat, 0) + 1

    summary.skill_signals = [
        f"{cat} (across {count} project{'s' if count > 1 else ''})"
        for cat, count in sorted(skill_counts.items(), key=lambda x: -x[1])
    ]

    return summary
