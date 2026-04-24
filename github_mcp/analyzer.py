"""
Repository Analyzer
====================

Analyzes raw GitHub data to infer tech stack, domains, and features.
"""

from __future__ import annotations

import logging
import re

from . import config
from .schemas import LanguageBreakdown, RepoDetail, RepoMeta

logger = logging.getLogger(__name__)


def score_repo(repo: RepoMeta) -> float:
    """
    Score a repo for resume relevance (0.0 - 1.0).
    Non-fork, has README, has stars, recent activity score higher.
    """
    score = 0.5

    if repo.is_fork:
        score -= 0.3
    if repo.is_empty:
        score -= 0.4
    if repo.has_readme:
        score += 0.15
    if repo.stars > 0:
        score += min(repo.stars * 0.02, 0.15)
    if repo.description:
        score += 0.1
    if repo.topics:
        score += min(len(repo.topics) * 0.02, 0.1)

    # Low relevance name patterns
    name_lower = repo.name.lower()
    for pattern in config.LOW_RELEVANCE_PATTERNS:
        if pattern in name_lower:
            score -= 0.15
            break

    return max(0.0, min(1.0, score))


def build_repo_detail(raw: dict, tree_data: dict) -> RepoDetail:
    """
    Merge raw API data + tree data into a RepoDetail with inferred tech stack.
    """
    languages = [
        LanguageBreakdown(
            name=l["name"],
            bytes=l.get("bytes", 0),
            percentage=l.get("percentage", 0.0),
        )
        for l in raw.get("languages", [])
    ]

    detail = RepoDetail(
        name=raw["name"],
        description=raw.get("description"),
        url=raw.get("url"),
        stars=raw.get("stars", 0),
        primary_language=raw.get("primary_language"),
        languages=languages,
        topics=raw.get("topics", []),
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
        readme_text=raw.get("readme_text"),
        key_files=tree_data.get("key_files", []),
        top_level_structure=tree_data.get("top_level", []),
    )

    # Infer tech stack
    detail.tech_stack = infer_tech_stack(detail)
    detail.domains = infer_domains(detail)
    detail.inferred_features = extract_features_from_readme(detail.readme_text)

    return detail


def infer_tech_stack(detail: RepoDetail) -> dict[str, list[str]]:
    """
    Infer tech stack from languages, topics, key files, and README.
    Returns dict: category -> list of matched technologies.
    """
    # Collect all signals into a single set (lowercased)
    signals: set[str] = set()

    # From languages
    for lang in detail.languages:
        signals.add(lang.name.lower())

    # From topics
    for topic in detail.topics:
        signals.add(topic.lower())

    # From key files
    for filepath in detail.key_files:
        basename = filepath.split("/")[-1]
        if basename in config.TECH_INDICATOR_FILES:
            signals.add(config.TECH_INDICATOR_FILES[basename].lower())

    # From README (scan for keywords)
    if detail.readme_text:
        readme_lower = detail.readme_text.lower()
        for cat_data in config.TECH_STACK_KEYWORDS.values():
            for keywords in cat_data.values():
                for kw in keywords:
                    if kw in readme_lower:
                        signals.add(kw)

    # Match signals against categories
    result: dict[str, list[str]] = {}

    # Programming languages (from languages API)
    lang_names = [l.name for l in detail.languages]
    if lang_names:
        result["Languages"] = lang_names

    for category, subcats in config.TECH_STACK_KEYWORDS.items():
        matches: set[str] = set()
        for subcat_keywords in subcats.values():
            for kw in subcat_keywords:
                if kw in signals:
                    # Capitalize nicely
                    matches.add(kw.title().replace("-", " ").replace(".", ""))
        if matches:
            result[category] = sorted(matches)

    return result


def infer_domains(detail: RepoDetail) -> list[str]:
    """Classify the repo into domain categories."""
    signals: set[str] = set()

    for topic in detail.topics:
        signals.add(topic.lower())
    for lang in detail.languages:
        signals.add(lang.name.lower())
    if detail.readme_text:
        readme_lower = detail.readme_text.lower()
        for domain_keywords in config.DOMAIN_KEYWORDS.values():
            for kw in domain_keywords:
                if kw in readme_lower:
                    signals.add(kw)

    domains: list[str] = []
    for domain_name, keywords in config.DOMAIN_KEYWORDS.items():
        if signals & keywords:
            domains.append(domain_name)

    return domains


def extract_features_from_readme(readme_text: str | None) -> list[str]:
    """
    Extract bullet-point features from README if there's a Features section.
    """
    if not readme_text:
        return []

    features: list[str] = []
    in_features = False

    for line in readme_text.split("\n"):
        stripped = line.strip()

        # Detect features section header
        if re.match(r"^#{1,3}\s*(key\s+)?features", stripped, re.IGNORECASE):
            in_features = True
            continue

        # Stop at next heading
        if in_features and re.match(r"^#{1,3}\s+", stripped):
            break

        # Capture bullet points
        if in_features and re.match(r"^[-*]\s+", stripped):
            feature = re.sub(r"^[-*]\s+", "", stripped).strip()
            if feature and len(feature) > 5:
                features.append(feature)

    return features[:15]  # Cap at 15
