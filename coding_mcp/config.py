"""
Configuration — Coding MCP
===========================

LeetCode and Codeforces only. Add new platforms by appending to
PLATFORM_PATTERNS and PLATFORM_FETCHERS in api.py.
"""

from pathlib import Path
import re

# ── Output ────────────────────────────────────────────────────────────

DEFAULT_OUTPUT_DIR: Path = Path("md") / "coding"
SUMMARY_FILENAME = "summary.md"

# ── Platform URL Patterns ─────────────────────────────────────────────

PLATFORM_PATTERNS: list[dict] = [
    {
        "id": "leetcode",
        "name": "LeetCode",
        "domain": "leetcode.com",
        "username_regex": re.compile(
            r"(?:https?://)?(?:www\.)?leetcode\.com/(?:u/)?([A-Za-z0-9_-]+)/?",
            re.IGNORECASE,
        ),
        "output_file": "leetcode.md",
    },
    {
        "id": "codeforces",
        "name": "Codeforces",
        "domain": "codeforces.com",
        "username_regex": re.compile(
            r"(?:https?://)?(?:www\.)?codeforces\.com/profile/([A-Za-z0-9_.-]+)/?",
            re.IGNORECASE,
        ),
        "output_file": "codeforces.md",
    },
]

# ── API Endpoints ─────────────────────────────────────────────────────

LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"
CODEFORCES_API_URL = "https://codeforces.com/api"

# ── Request Settings ──────────────────────────────────────────────────

REQUEST_TIMEOUT = 15.0
MAX_RETRIES = 2
RETRY_DELAY = 1.0

# ── Competitive Strength Thresholds ──────────────────────────────────

STRENGTH_LEVELS = {
    "leetcode": [
        (0, 50, "Beginner"),
        (50, 150, "Intermediate"),
        (150, 400, "Advanced"),
        (400, 9999, "Expert"),
    ],
    "codeforces": [
        (0, 1200, "Beginner (Newbie)"),
        (1200, 1600, "Intermediate (Specialist)"),
        (1600, 2100, "Advanced (Expert/CM)"),
        (2100, 9999, "Elite (Master+)"),
    ],
}
