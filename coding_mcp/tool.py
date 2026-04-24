"""
Coding Platforms MCP Tool — Gateway
=====================================

Single entry point: paste profile links and get Markdown output.

Usage:
    coding_extract_profiles("https://leetcode.com/u/username, https://codeforces.com/profile/username")
    coding_extract_profiles("leetcode: username, codeforces: username")

Supports LeetCode and Codeforces. More platforms can be added to
config.PLATFORM_PATTERNS and api.PLATFORM_FETCHERS.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from . import config
from .api import PLATFORM_FETCHERS, fetch_leetcode, fetch_codeforces
from .exceptions import CodingMCPError
from .markdown_writer import write_platform_md, write_summary_md
from .schemas import CodingProfile

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Link Parser
# ──────────────────────────────────────────────────────────────────────

def _parse_profiles(input_text: str) -> list[dict]:
    """
    Extract platform profiles from any input format:
      - URLs:  "https://leetcode.com/u/user1, https://codeforces.com/profile/user2"
      - Text:  "leetcode: user1, codeforces: user2"
      - Env:   Reads CODING_PROFILES env var as fallback

    Returns list of dicts: [{"platform": {...}, "username": "...", "url": "..."}]
    """
    text = input_text.strip()

    # Fallback to .env if input is empty
    if not text:
        from env_loader import get_env
        text = get_env("CODING_PROFILES")
    if not text:
        return []

    found: list[dict] = []
    used_platforms: set[str] = set()

    # Strategy 1: Match URLs against platform patterns
    for platform in config.PLATFORM_PATTERNS:
        for match in platform["username_regex"].finditer(text):
            pid = platform["id"]
            if pid not in used_platforms:
                username = match.group(1)
                found.append({
                    "platform": platform,
                    "username": username,
                    "url": match.group(0),
                })
                used_platforms.add(pid)

    # Strategy 2: Match "platform: username" shorthand
    shorthand = re.findall(r"(leetcode|codeforces)\s*[:=]\s*([A-Za-z0-9_.-]+)", text, re.IGNORECASE)
    for platform_name, username in shorthand:
        pid = platform_name.lower()
        if pid not in used_platforms:
            for platform in config.PLATFORM_PATTERNS:
                if platform["id"] == pid:
                    found.append({
                        "platform": platform,
                        "username": username,
                        "url": "",
                    })
                    used_platforms.add(pid)
                    break

    return found


# ──────────────────────────────────────────────────────────────────────
# Gateway Tool
# ──────────────────────────────────────────────────────────────────────


def coding_extract_profiles(
    profiles_input: str | None = None,
    output_dir: str | None = None,
) -> dict:
    """
    Extract coding profiles from LeetCode and Codeforces and generate
    resume-ready Markdown files.

    Args:
        profiles_input: Profile links or shorthand text. Accepts:
            - URLs: "https://leetcode.com/u/user, https://codeforces.com/profile/user"
            - Shorthand: "leetcode: user, codeforces: user"
            - Mixed: "Here are my profiles: https://leetcode.com/u/user"
            - Empty string: reads CODING_PROFILES env var
        output_dir: (Optional) Custom output directory.

    Returns:
        {
            "profiles": [...],
            "output_paths": [...],
            "summary_path": "...",
            "failed_platforms": [...],
            "errors": [],
            "success": true
        }
    """
    out_path = Path(output_dir) if output_dir else Path(__file__).resolve().parent.parent / config.DEFAULT_OUTPUT_DIR
    errors: list[str] = []
    output_paths: list[str] = []
    profiles: list[CodingProfile] = []
    profile_dicts: list[dict] = []
    failed: list[dict] = []

    # ── Parse input ───────────────────────────────────────────────────
    parsed = _parse_profiles(profiles_input or "")

    if not parsed:
        return {
            "profiles": [],
            "output_paths": [],
            "summary_path": "",
            "failed_platforms": [],
            "errors": ["No valid profile links found in input. "
                       "Supported: leetcode.com, codeforces.com"],
            "success": False,
        }

    logger.info("Detected %d platform(s): %s",
                len(parsed), [p["platform"]["name"] for p in parsed])

    # ── Fetch each platform ───────────────────────────────────────────
    for entry in parsed:
        platform = entry["platform"]
        pid = platform["id"]
        username = entry["username"]

        fetcher = PLATFORM_FETCHERS.get(pid)
        if not fetcher:
            failed.append({"platform": platform["name"], "username": username,
                           "reason": "No fetcher available"})
            continue

        try:
            logger.info("Fetching %s: %s", platform["name"], username)
            profile = fetcher(username)

            # Fix URL if not set
            if not profile.url and entry["url"]:
                profile.url = entry["url"]

            profiles.append(profile)

            # Write per-platform .md
            path = write_platform_md(profile, out_path, platform["output_file"])
            output_paths.append(path)

            # Build serializable dict
            profile_dicts.append({
                "platform": profile.platform,
                "username": profile.username,
                "url": profile.url,
                "problems_solved": profile.problems_solved,
                "difficulty": {
                    "easy": profile.difficulty.easy,
                    "medium": profile.difficulty.medium,
                    "hard": profile.difficulty.hard,
                },
                "rating": profile.rating,
                "max_rating": profile.max_rating,
                "rank": profile.rank,
                "global_ranking": profile.global_ranking,
                "contests": profile.contests_participated,
                "achievements": profile.achievements,
                "strength_level": profile.strength_level,
            })

        except CodingMCPError as exc:
            failed.append({"platform": platform["name"], "username": username,
                           "reason": str(exc)})
            errors.append(f"{platform['name']}: {exc}")
            logger.warning("Failed %s: %s", platform["name"], exc)
        except Exception as exc:
            failed.append({"platform": platform["name"], "username": username,
                           "reason": str(exc)})
            errors.append(f"{platform['name']}: Unexpected error: {exc}")
            logger.exception("Error fetching %s", platform["name"])

    # ── Write summary ─────────────────────────────────────────────────
    summary_path = ""
    if profiles:
        summary_path = write_summary_md(profiles, out_path)

    success = len(profiles) > 0

    logger.info("Done: %d extracted, %d failed", len(profiles), len(failed))

    return {
        "profiles": profile_dicts,
        "output_paths": output_paths,
        "summary_path": summary_path,
        "failed_platforms": failed,
        "errors": errors,
        "success": success,
    }
