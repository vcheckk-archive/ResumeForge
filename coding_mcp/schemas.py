"""
Data Schemas — Coding MCP
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class DifficultyBreakdown:
    easy: int = 0
    medium: int = 0
    hard: int = 0


@dataclass
class CodingProfile:
    """Unified profile structure across all platforms."""
    platform: str
    platform_id: str
    username: str
    url: str = ""
    problems_solved: int = 0
    difficulty: DifficultyBreakdown = field(default_factory=DifficultyBreakdown)
    rating: float | None = None
    max_rating: float | None = None
    rank: str | None = None
    global_ranking: int | None = None
    contests_participated: int = 0
    achievements: list[str] = field(default_factory=list)
    strength_level: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class ExtractResult:
    """Return value of coding_extract_profiles."""
    profiles: list[dict] = field(default_factory=list)
    output_paths: list[str] = field(default_factory=list)
    summary_path: str = ""
    failed_platforms: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    success: bool = True
