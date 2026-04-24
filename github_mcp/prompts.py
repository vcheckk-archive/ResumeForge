"""
Prompt Templates — GitHub MCP
==============================

All Markdown formatting templates separated from logic.
Edit these strings to change output format without touching code.
"""

# ══════════════════════════════════════════════════════════════════════
# Per-Repository Project File
# ══════════════════════════════════════════════════════════════════════

PROJECT_HEADER = "# Project: {name}\n"

PROJECT_OVERVIEW = """## Overview

{description}
"""

PROJECT_PROBLEM = """## Problem Statement

{problem}
"""

PROJECT_SOLUTION = """## Solution

{solution}
"""

PROJECT_TECH_STACK_HEADER = "## Tech Stack\n\n"
PROJECT_TECH_CATEGORY = "### {category}\n\n"
PROJECT_TECH_ITEM = "- {item}\n"

PROJECT_FEATURES_HEADER = "## Key Features\n\n"
PROJECT_FEATURE_ITEM = "- {feature}\n"

PROJECT_CHALLENGES = """## Challenges & Learnings

{challenges}
"""

PROJECT_IMPACT = """## Impact / Results

{impact}
"""

PROJECT_REPO_DETAILS = """## Repository Details

- **URL:** [{url}]({url})
- **Primary Language:** {language}
- **Stars:** {stars}
- **Created:** {created}
- **Last Updated:** {updated}
"""

PROJECT_STRUCTURE = """## Project Structure

```
{structure}
```
"""

# ══════════════════════════════════════════════════════════════════════
# Portfolio Summary File
# ══════════════════════════════════════════════════════════════════════

SUMMARY_HEADER = "# Project Portfolio Summary\n"

SUMMARY_TOTAL = """## Total Projects

- **{count}** selected repositories processed
"""

SUMMARY_TECH_HEADER = "## Tech Stack Overview\n\n"
SUMMARY_TECH_CATEGORY = "### {category}\n\n"
SUMMARY_TECH_ITEM = "- {item}\n"

SUMMARY_DOMAINS_HEADER = "## Key Domains\n\n"
SUMMARY_DOMAIN_ITEM = "- {domain}\n"

SUMMARY_HIGHLIGHTS_HEADER = "## Highlight Projects\n\n"
SUMMARY_HIGHLIGHT_ENTRY = """### {name}

{description}

- **Tech:** {tech}
- **Stars:** {stars}

---
"""

SUMMARY_SKILLS_HEADER = "## Skill Signals\n\n"
SUMMARY_SKILL_ITEM = "- {skill}\n"

# ══════════════════════════════════════════════════════════════════════
# Fallback notices
# ══════════════════════════════════════════════════════════════════════

NO_DATA = "_No data available._\n"
NO_USER_CONTEXT = "_User context not provided. Run with project_context for richer output._\n"
