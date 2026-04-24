"""
Platform API Clients — Coding MCP
===================================

LeetCode:    Direct GraphQL (problems, ranking, badges, contests)
Codeforces:  Official REST API (rating, rank, contests)

To add a new platform:
  1. Add pattern to config.PLATFORM_PATTERNS
  2. Write a fetch_<platform>(username) -> CodingProfile function here
  3. Register it in PLATFORM_FETCHERS dict at bottom
"""

from __future__ import annotations

import logging
import time

import httpx

from . import config
from .exceptions import PlatformAPIError, ProfileNotFoundError
from .schemas import CodingProfile, DifficultyBreakdown

logger = logging.getLogger(__name__)


def _retry_get(client: httpx.Client, url: str, **kwargs) -> httpx.Response:
    """GET with retry logic."""
    for attempt in range(config.MAX_RETRIES + 1):
        try:
            resp = client.get(url, timeout=config.REQUEST_TIMEOUT, **kwargs)
            return resp
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            if attempt == config.MAX_RETRIES:
                raise
            logger.warning("Retry %d for %s: %s", attempt + 1, url, exc)
            time.sleep(config.RETRY_DELAY)
    raise PlatformAPIError("unknown", 0, "Max retries exceeded")


# ──────────────────────────────────────────────────────────────────────
# LeetCode (GraphQL)
# ──────────────────────────────────────────────────────────────────────

_LC_QUERY = """
query getUserProfile($username: String!) {
  matchedUser(username: $username) {
    profile { ranking }
    badges { name }
    submitStats {
      acSubmissionNum { difficulty count }
    }
  }
  userContestRanking(username: $username) {
    attendedContestsCount
    rating
    globalRanking
  }
}
"""


def fetch_leetcode(username: str) -> CodingProfile:
    """Fetch LeetCode profile via direct GraphQL."""
    client = httpx.Client()
    try:
        resp = client.post(
            config.LEETCODE_GRAPHQL_URL,
            json={"query": _LC_QUERY, "variables": {"username": username}},
            headers={
                "Content-Type": "application/json",
                "Referer": "https://leetcode.com",
            },
            timeout=config.REQUEST_TIMEOUT,
        )

        if resp.status_code != 200:
            raise PlatformAPIError("LeetCode", resp.status_code, resp.text[:200])

        data = resp.json()
        matched = data.get("data", {}).get("matchedUser")
        if not matched:
            raise ProfileNotFoundError("LeetCode", username)

        # Problems solved
        stats = matched.get("submitStats", {}).get("acSubmissionNum", [])
        difficulty = DifficultyBreakdown()
        total = 0
        for s in stats:
            d = s.get("difficulty", "").lower()
            c = s.get("count", 0)
            if d == "easy":
                difficulty.easy = c
            elif d == "medium":
                difficulty.medium = c
            elif d == "hard":
                difficulty.hard = c
            elif d == "all":
                total = c

        # Ranking + badges
        ranking = matched.get("profile", {}).get("ranking")
        badges = [b["name"] for b in matched.get("badges", []) if b.get("name")]

        # Contest data
        contest = data.get("data", {}).get("userContestRanking") or {}

        profile = CodingProfile(
            platform="LeetCode",
            platform_id="leetcode",
            username=username,
            url=f"https://leetcode.com/u/{username}/",
            problems_solved=total,
            difficulty=difficulty,
            rating=round(contest.get("rating", 0), 1) if contest.get("rating") else None,
            global_ranking=contest.get("globalRanking"),
            contests_participated=contest.get("attendedContestsCount", 0),
            achievements=badges,
            strength_level=_classify("leetcode", total),
        )
        logger.info("LeetCode: %s — %d solved", username, total)
        return profile
    finally:
        client.close()


# ──────────────────────────────────────────────────────────────────────
# Codeforces (REST API)
# ──────────────────────────────────────────────────────────────────────


def fetch_codeforces(username: str) -> CodingProfile:
    """Fetch Codeforces profile via official REST API."""
    client = httpx.Client()
    try:
        # User info
        resp = _retry_get(client, f"{config.CODEFORCES_API_URL}/user.info?handles={username}")
        if resp.status_code != 200:
            raise PlatformAPIError("Codeforces", resp.status_code, resp.text[:200])

        data = resp.json()
        if data.get("status") != "OK":
            raise ProfileNotFoundError("Codeforces", username)

        user = data["result"][0]

        # Contest count
        time.sleep(0.3)  # Rate limit: 5 req/sec
        rating_resp = _retry_get(client, f"{config.CODEFORCES_API_URL}/user.rating?handle={username}")
        contests = 0
        if rating_resp.status_code == 200:
            rd = rating_resp.json()
            if rd.get("status") == "OK":
                contests = len(rd.get("result", []))

        rating = user.get("rating")
        profile = CodingProfile(
            platform="Codeforces",
            platform_id="codeforces",
            username=username,
            url=f"https://codeforces.com/profile/{username}",
            rating=rating,
            max_rating=user.get("maxRating"),
            rank=user.get("rank"),
            contests_participated=contests,
            strength_level=_classify("codeforces", rating) if rating else "Unrated",
            extra={
                "max_rank": user.get("maxRank"),
                "contribution": user.get("contribution"),
                "friend_count": user.get("friendOfCount"),
            },
        )
        logger.info("Codeforces: %s — rating=%s rank=%s", username, rating, user.get("rank"))
        return profile
    finally:
        client.close()


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────


def _classify(platform_id: str, value: int | float | None) -> str:
    if value is None:
        return "Unknown"
    for low, high, label in config.STRENGTH_LEVELS.get(platform_id, []):
        if low <= value < high:
            return label
    return "Unknown"


# ── Router — add new platforms here ──────────────────────────────────

PLATFORM_FETCHERS = {
    "leetcode": fetch_leetcode,
    "codeforces": fetch_codeforces,
}
