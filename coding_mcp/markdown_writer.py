"""
Markdown Writer — Coding MCP
"""

from __future__ import annotations

import logging
from pathlib import Path

from . import config, prompts
from .schemas import CodingProfile

logger = logging.getLogger(__name__)


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_platform_md(profile: CodingProfile, output_dir: Path, filename: str) -> str:
    """Generate a per-platform .md file."""
    _ensure_dir(output_dir)
    lines: list[str] = []

    # Header
    lines.append(prompts.PLATFORM_HEADER.format(platform=profile.platform))

    # Browser notice for unsupported platforms
    if profile.extra.get("note"):
        lines.append(prompts.BROWSER_NOTICE.format(platform=profile.platform))
        filepath = output_dir / filename
        filepath.write_text("".join(lines), encoding="utf-8")
        return str(filepath)

    # Summary
    lines.append(prompts.SUMMARY_SECTION.format(
        username=profile.username,
        url=profile.url,
        problems_solved=profile.problems_solved,
        strength_level=profile.strength_level or "N/A",
    ))

    # Difficulty breakdown (if has problems)
    if profile.problems_solved > 0:
        lines.append(prompts.DIFFICULTY_SECTION.format(
            easy=profile.difficulty.easy,
            medium=profile.difficulty.medium,
            hard=profile.difficulty.hard,
        ))

    # Rating (if exists)
    if profile.rating is not None:
        lines.append(prompts.RATING_SECTION.format(
            rating=profile.rating,
            max_rating=profile.max_rating or "N/A",
            rank=profile.rank or "N/A",
        ))

    # Global ranking
    if profile.global_ranking:
        lines.append(prompts.RANKING_SECTION.format(global_ranking=profile.global_ranking))

    # Contests
    if profile.contests_participated > 0:
        lines.append(prompts.CONTEST_SECTION.format(contests=profile.contests_participated))

    # Achievements
    if profile.achievements:
        lines.append(prompts.ACHIEVEMENTS_HEADER)
        for badge in profile.achievements:
            lines.append(prompts.ACHIEVEMENT_ITEM.format(badge=badge))
        lines.append("\n")

    # Extra info
    clean_extra = {k: v for k, v in profile.extra.items() if v and k != "note"}
    if clean_extra:
        lines.append(prompts.EXTRA_SECTION)
        for k, v in clean_extra.items():
            lines.append(prompts.EXTRA_ITEM.format(
                key=k.replace("_", " ").title(), value=v
            ))
        lines.append("\n")

    filepath = output_dir / filename
    content = "".join(lines)
    filepath.write_text(content, encoding="utf-8")
    logger.info("Wrote %s (%d bytes)", filename, len(content))
    return str(filepath)


def write_summary_md(profiles: list[CodingProfile], output_dir: Path) -> str:
    """Generate the aggregated summary.md."""
    _ensure_dir(output_dir)
    lines: list[str] = []

    lines.append(prompts.AGG_HEADER)

    # Total problems
    total = sum(p.problems_solved for p in profiles)
    lines.append(prompts.AGG_TOTAL.format(total=total, platform_count=len(profiles)))

    # Platform breakdown table
    lines.append(prompts.AGG_PLATFORM_HEADER)
    lines.append(prompts.AGG_PLATFORM_TABLE_HEADER)
    for p in profiles:
        lines.append(prompts.AGG_PLATFORM_ROW.format(
            platform=p.platform,
            solved=p.problems_solved or "N/A",
            rating=p.rating or "N/A",
            strength=p.strength_level or "N/A",
        ))
    lines.append("\n")

    # Skill signals
    signals: list[str] = []
    total_problems = sum(p.problems_solved for p in profiles)
    if total_problems > 0:
        signals.append(f"Problem Solving ({total_problems} problems across platforms)")
    if any(p.difficulty.hard > 0 for p in profiles):
        hard_total = sum(p.difficulty.hard for p in profiles)
        signals.append(f"Advanced Problem Solving ({hard_total} hard problems)")
    if any(p.contests_participated > 0 for p in profiles):
        contest_total = sum(p.contests_participated for p in profiles)
        signals.append(f"Competitive Programming ({contest_total} contests)")
    if any(p.rating and p.rating > 1500 for p in profiles):
        signals.append("Strong Algorithmic Skills (high rating)")

    if signals:
        lines.append(prompts.AGG_SKILL_HEADER)
        for s in signals:
            lines.append(prompts.AGG_SKILL_ITEM.format(signal=s))
        lines.append("\n")

    # Competitive strength
    lines.append(prompts.AGG_STRENGTH_HEADER)
    for p in profiles:
        if p.strength_level:
            lines.append(prompts.AGG_STRENGTH_ITEM.format(
                platform=p.platform, strength=p.strength_level
            ))
    lines.append("\n")

    # Key achievements
    all_achievements = [(p.platform, a) for p in profiles for a in p.achievements]
    if all_achievements:
        lines.append(prompts.AGG_ACHIEVEMENTS_HEADER)
        for platform, achievement in all_achievements:
            lines.append(prompts.AGG_ACHIEVEMENT_ITEM.format(
                platform=platform, achievement=achievement
            ))
        lines.append("\n")

    filepath = output_dir / config.SUMMARY_FILENAME
    content = "".join(lines)
    filepath.write_text(content, encoding="utf-8")
    logger.info("Wrote %s (%d bytes)", config.SUMMARY_FILENAME, len(content))
    return str(filepath)
