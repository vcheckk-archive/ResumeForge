"""
Prompt Templates — Coding MCP
"""

# ── Per-Platform Headers ──────────────────────────────────────────────

PLATFORM_HEADER = "# {platform} Profile\n"

SUMMARY_SECTION = """## Summary

- **Username:** [{username}]({url})
- **Total Problems Solved:** {problems_solved}
- **Competitive Strength:** {strength_level}
"""

DIFFICULTY_SECTION = """## Difficulty Breakdown

| Difficulty | Count |
|---|---|
| Easy | {easy} |
| Medium | {medium} |
| Hard | {hard} |
"""

RATING_SECTION = """## Rating

- **Current Rating:** {rating}
- **Max Rating:** {max_rating}
- **Rank:** {rank}
"""

CONTEST_SECTION = """## Contests

- **Participated:** {contests}
"""

RANKING_SECTION = """## Ranking

- **Global Ranking:** {global_ranking}
"""

ACHIEVEMENTS_HEADER = "## Achievements\n\n"
ACHIEVEMENT_ITEM = "- {badge}\n"

EXTRA_SECTION = """## Additional Info

"""
EXTRA_ITEM = "- **{key}:** {value}\n"

BROWSER_NOTICE = """
> **Note:** {platform} profiles are client-rendered and cannot be accessed via API.
> Please provide data manually or use browser-based extraction.
"""

# ── Summary File ──────────────────────────────────────────────────────

AGG_HEADER = "# Coding Profile Summary\n"

AGG_TOTAL = """## Total Problems Solved

- **Aggregated:** {total} problems across {platform_count} platform(s)
"""

AGG_PLATFORM_HEADER = "## Platform Breakdown\n\n"
AGG_PLATFORM_ROW = "| {platform} | {solved} | {rating} | {strength} |\n"
AGG_PLATFORM_TABLE_HEADER = "| Platform | Problems Solved | Rating | Strength |\n|---|---|---|---|\n"

AGG_SKILL_HEADER = "## Skill Signals\n\n"
AGG_SKILL_ITEM = "- {signal}\n"

AGG_STRENGTH_HEADER = "## Competitive Strength\n\n"
AGG_STRENGTH_ITEM = "- **{platform}:** {strength}\n"

AGG_ACHIEVEMENTS_HEADER = "## Key Achievements\n\n"
AGG_ACHIEVEMENT_ITEM = "- **{platform}:** {achievement}\n"

NO_DATA = "_No data available._\n"
