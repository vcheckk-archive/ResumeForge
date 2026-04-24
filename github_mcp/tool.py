"""
GitHub MCP Tool — Unified Gateway
===================================

Single entry point for GitHub project extraction.
Reads GITHUB_PROFILE and GITHUB_TOKEN from .env if not passed as args.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from .analyzer import build_repo_detail, score_repo
from .api import GitHubClient
from .config import DEFAULT_OUTPUT_DIR
from .exceptions import GitHubMCPError
from .markdown_writer import write_project_md, write_summary_md
from .schemas import (
    ProjectContext,
    ProjectDocument,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────
# Token Loader (uses shared env_loader)
# ──────────────────────────────────────────────────────────────────────────

def _load_token(explicit_token: str | None = None) -> str | None:
    """Resolve token: param -> .env -> env var -> None."""
    if explicit_token:
        return explicit_token
    from env_loader import get_env
    return get_env("GITHUB_TOKEN") or None


# ──────────────────────────────────────────────────────────────────────────
# Username Extractor
# ──────────────────────────────────────────────────────────────────────────

def _extract_username(profile_input: str) -> str:
    """
    Extract GitHub username from various input formats:
      - "https://github.com/VijayaKanth-M"
      - "github.com/VijayaKanth-M"
      - "VijayaKanth-M"

    Returns the cleaned username string.
    """
    text = profile_input.strip().rstrip("/")

    # Match URL patterns
    match = re.match(
        r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9\-_.]+)",
        text,
    )
    if match:
        return match.group(1)

    # Already a plain username (no slashes, no dots)
    if re.match(r"^[A-Za-z0-9\-_.]+$", text):
        return text

    # Last resort: take the last path segment
    parts = text.split("/")
    return parts[-1] if parts else text


# ──────────────────────────────────────────────────────────────────────────
# Unified Gateway Tool
# ──────────────────────────────────────────────────────────────────────────


def github_build_profile(
    github_profile: str | None = None,
    repo_names: list[str] | None = None,
    project_context: dict | None = None,
    auth_token: str | None = None,
    output_dir: str | None = None,
) -> dict:
    """
    Build a complete GitHub project profile from a profile URL.

    This is the single gateway for all GitHub operations. It:
      1. Extracts the username from the profile URL
      2. Auto-loads auth token from .env / env var (or uses provided one)
      3. Discovers all repos and ranks them by resume relevance
      4. Extracts selected repos (or all relevant ones if none specified)
      5. Generates per-repo Markdown + portfolio summary

    Args:
        github_profile: GitHub profile URL or username.
                        Examples:
                          "https://github.com/VijayaKanth-M"
                          "github.com/VijayaKanth-M"
                          "VijayaKanth-M"
        repo_names:     (Optional) Specific repo names to extract.
                        If not provided, all non-fork, non-empty repos
                        with relevance score >= 0.4 are auto-selected.
        project_context: (Optional) Dict mapping repo_name to context:
                         {"repo-name": {"problem": "...", "role": "...",
                          "challenges": "...", "impact": "...",
                          "technologies": "...", "key_features": "..."}}
        auth_token:     (Optional) GitHub token. Auto-loaded from .env
                        or GITHUB_TOKEN env var if not provided.
        output_dir:     (Optional) Custom output directory path.

    Returns:
        {
            "username": "VijayaKanth-M",
            "mode": "authenticated" | "public",
            "total_repos_found": 42,
            "repos_processed": ["repo1", "repo2"],
            "repos_skipped": ["fork1", "empty1"],
            "output_paths": ["md/github/projects/repo1.md", ...],
            "summary_path": "md/github/projects_summary.md",
            "errors": [],
            "success": true
        }
    """
    # ── Resolve profile from .env if not provided ─────────────────────
    if not github_profile:
        from env_loader import get_env
        github_profile = get_env("GITHUB_PROFILE")

    if not github_profile:
        return {
            "username": "", "mode": "public", "total_repos_found": 0,
            "repos_processed": [], "repos_skipped": [],
            "output_paths": [], "summary_path": "",
            "errors": ["No github_profile provided and GITHUB_PROFILE not set in .env"],
            "success": False,
        }

    # ── Extract username ──────────────────────────────────────────────
    username = _extract_username(github_profile)
    logger.info("GitHub profile: %s (username: %s)", github_profile, username)

    # ── Resolve token ─────────────────────────────────────────────────
    token = _load_token(auth_token)
    mode = "authenticated" if token else "public"
    logger.info("Mode: %s", mode)

    # ── Prepare output ────────────────────────────────────────────────
    out_path = Path(output_dir) if output_dir else Path(__file__).resolve().parent.parent / DEFAULT_OUTPUT_DIR
    ctx_map = project_context or {}
    errors: list[str] = []
    output_paths: list[str] = []
    repos_processed: list[str] = []
    repos_skipped: list[str] = []
    summary_path = ""
    total_found = 0

    try:
        client = GitHubClient(token)

        try:
            # ── Step 1: Discover repos ────────────────────────────────
            repos, total_found = client.discover_repos(username)

            # Score all repos
            for repo in repos:
                repo.relevance_score = score_repo(repo)
            repos.sort(key=lambda r: r.relevance_score, reverse=True)

            logger.info("Discovered %d repos", total_found)

            # ── Step 2: Select repos ──────────────────────────────────
            if repo_names:
                # User specified repos — use those
                selected_names = set(repo_names)
            else:
                # Auto-select: non-fork, non-empty, score >= 0.4
                selected_names = set()
                for r in repos:
                    if r.is_fork or r.is_empty:
                        repos_skipped.append(r.name)
                        continue
                    if r.relevance_score >= 0.4:
                        selected_names.add(r.name)
                    else:
                        repos_skipped.append(r.name)

            logger.info("Selected %d repos for extraction", len(selected_names))

            # ── Step 3: Extract each repo ─────────────────────────────
            documents: list[ProjectDocument] = []

            for repo_meta in repos:
                if repo_meta.name not in selected_names:
                    continue

                try:
                    logger.info("Extracting: %s/%s", username, repo_meta.name)
                    raw = client.fetch_repo_detail(username, repo_meta.name)
                    tree = client.fetch_repo_tree(username, repo_meta.name)
                    detail = build_repo_detail(raw, tree)

                    # Build user context if provided
                    user_ctx = None
                    if repo_meta.name in ctx_map:
                        c = ctx_map[repo_meta.name]
                        user_ctx = ProjectContext(
                            problem=c.get("problem"),
                            role=c.get("role"),
                            technologies=c.get("technologies"),
                            challenges=c.get("challenges"),
                            impact=c.get("impact"),
                            key_features=c.get("key_features"),
                        )

                    doc = ProjectDocument(repo=detail, context=user_ctx)
                    path = write_project_md(doc, out_path)

                    documents.append(doc)
                    output_paths.append(path)
                    repos_processed.append(repo_meta.name)

                except GitHubMCPError as exc:
                    errors.append(f"{repo_meta.name}: {exc}")
                    logger.warning("Skipped %s: %s", repo_meta.name, exc)
                except Exception as exc:
                    errors.append(f"{repo_meta.name}: {exc}")
                    logger.exception("Error extracting %s", repo_meta.name)

            # ── Step 4: Generate summary ──────────────────────────────
            if documents:
                summary_path = write_summary_md(documents, out_path)
                logger.info("Summary generated for %d projects", len(documents))

        finally:
            client.close()

    except GitHubMCPError as exc:
        errors.append(f"{exc.__class__.__name__}: {exc}")
        logger.error("Pipeline failed: %s", exc)
    except Exception as exc:
        errors.append(f"Unexpected error: {exc}")
        logger.exception("Unexpected error")

    success = len(repos_processed) > 0

    logger.info(
        "Done: %d processed, %d skipped, %d errors",
        len(repos_processed), len(repos_skipped), len(errors),
    )

    return {
        "username": username,
        "mode": mode,
        "total_repos_found": total_found,
        "repos_processed": repos_processed,
        "repos_skipped": repos_skipped,
        "output_paths": output_paths,
        "summary_path": summary_path,
        "errors": errors,
        "success": success,
    }
