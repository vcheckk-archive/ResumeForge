"""
Data Schemas — GitHub MCP
=========================

Typed dataclasses flowing between api → analyzer → markdown_writer.
All fields documented. Optional fields use ``str | None``.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RepoMeta:
    """
    Lightweight repo metadata returned by the discovery step.
    Used by the MCP client to present the repo list for selection.
    """

    name: str
    description: str | None = None
    url: str | None = None
    primary_language: str | None = None
    stars: int = 0
    topics: list[str] = field(default_factory=list)
    is_fork: bool = False
    is_empty: bool = False
    is_private: bool = False
    created_at: str | None = None
    updated_at: str | None = None
    has_readme: bool = False
    relevance_score: float = 0.0


@dataclass
class LanguageBreakdown:
    """A single language's size and percentage."""

    name: str
    bytes: int = 0
    percentage: float = 0.0


@dataclass
class RepoDetail:
    """
    Deep extraction data for a single repository.
    Populated by the api + analyzer modules.
    """

    name: str
    description: str | None = None
    url: str | None = None
    stars: int = 0
    primary_language: str | None = None
    languages: list[LanguageBreakdown] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    readme_text: str | None = None
    key_files: list[str] = field(default_factory=list)
    top_level_structure: list[str] = field(default_factory=list)

    # Inferred by analyzer
    tech_stack: dict[str, list[str]] = field(default_factory=dict)
    inferred_features: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)


@dataclass
class ProjectContext:
    """
    User-provided context from the "project interview" layer.
    Passed by the MCP client after asking the user these questions.
    """

    problem: str | None = None
    role: str | None = None
    technologies: str | None = None
    challenges: str | None = None
    impact: str | None = None
    key_features: str | None = None


@dataclass
class ProjectDocument:
    """
    Merged data (RepoDetail + ProjectContext) ready for Markdown generation.
    """

    repo: RepoDetail
    context: ProjectContext | None = None


@dataclass
class PortfolioSummary:
    """Aggregated data across all processed projects."""

    total_projects: int = 0
    all_languages: dict[str, int] = field(default_factory=dict)
    all_tech_stack: dict[str, set[str]] = field(default_factory=dict)
    all_domains: set[str] = field(default_factory=set)
    highlight_projects: list[str] = field(default_factory=list)
    skill_signals: list[str] = field(default_factory=list)


@dataclass
class DiscoverResult:
    """Return value of github_discover_repos."""

    repos: list[dict] = field(default_factory=list)
    total_count: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class ExtractResult:
    """Return value of github_extract_projects."""

    output_paths: list[str] = field(default_factory=list)
    extracted_repos: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    success: bool = True


@dataclass
class SummaryResult:
    """Return value of github_generate_summary."""

    output_path: str = ""
    total_projects: int = 0
    errors: list[str] = field(default_factory=list)
    success: bool = True
