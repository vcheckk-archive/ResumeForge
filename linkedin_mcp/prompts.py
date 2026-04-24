"""
Prompt Templates Module
=======================

All Markdown formatting templates live here — separated from logic so they
can be edited, localized, or swapped without touching any processing code.

Usage:
    from linkedin_mcp.prompts import TEMPLATES
    md = TEMPLATES["identity_header"].format(name="Jane Doe")

Design Principles:
    - Plug-and-play: change any template string to alter output format.
    - No logic: pure string constants.
    - Consistent naming: ``<section>_<element>`` convention.
"""

# ═══════════════════════════════════════════════════════════════════════════
# File-level headers
# ═══════════════════════════════════════════════════════════════════════════

IDENTITY_HEADER = "# Identity\n"
SUMMARY_HEADER = "# Professional Summary\n"
EXPERIENCE_HEADER = "# Experience\n"
EDUCATION_HEADER = "# Education\n"
SKILLS_HEADER = "# Skills\n"
CERTIFICATIONS_HEADER = "# Certifications\n"
PROJECTS_HEADER = "# Projects\n"

# ═══════════════════════════════════════════════════════════════════════════
# Identity section
# ═══════════════════════════════════════════════════════════════════════════

IDENTITY_NAME = "- **Name:** {first_name} {last_name}\n"
IDENTITY_HEADLINE = "- **Headline:** {headline}\n"
IDENTITY_LOCATION = "- **Location:** {location}\n"
IDENTITY_EMAIL = "- **Email:** {email}\n"
IDENTITY_INDUSTRY = "- **Industry:** {industry}\n"
IDENTITY_WEBSITE = "- **Portfolio:** [{url}]({url})\n"

# ═══════════════════════════════════════════════════════════════════════════
# Summary section
# ═══════════════════════════════════════════════════════════════════════════

SUMMARY_BODY = "{text}\n"

# ═══════════════════════════════════════════════════════════════════════════
# Experience section
# ═══════════════════════════════════════════════════════════════════════════

EXPERIENCE_ENTRY = """## {title}

- **Company:** {company}
- **Duration:** {duration}
{location_line}{description_block}
---
"""

EXPERIENCE_LOCATION_LINE = "- **Location:** {location}\n"

EXPERIENCE_DESCRIPTION = """
{description}
"""

# ═══════════════════════════════════════════════════════════════════════════
# Education section
# ═══════════════════════════════════════════════════════════════════════════

EDUCATION_ENTRY = """## {degree}

- **Institution:** {school_name}
- **Duration:** {duration}
{notes_line}
---
"""

EDUCATION_NOTES_LINE = "- **Coursework / Notes:** {notes}\n"

# ═══════════════════════════════════════════════════════════════════════════
# Skills section
# ═══════════════════════════════════════════════════════════════════════════

SKILLS_CATEGORY_HEADER = "## {category}\n\n"
SKILLS_ITEM = "- {skill}\n"

# ═══════════════════════════════════════════════════════════════════════════
# Certifications section
# ═══════════════════════════════════════════════════════════════════════════

CERTIFICATION_ENTRY = """## {name}

- **Issuer:** {authority}
- **Date:** {date}
{license_line}{url_line}
---
"""

CERTIFICATION_LICENSE_LINE = "- **License:** {license_number}\n"
CERTIFICATION_URL_LINE = "- **URL:** [{url}]({url})\n"

# ═══════════════════════════════════════════════════════════════════════════
# Projects section
# ═══════════════════════════════════════════════════════════════════════════

PROJECT_ENTRY = """## {title}

- **Duration:** {duration}
{url_line}
{description}

---
"""

PROJECT_URL_LINE = "- **URL:** [{url}]({url})\n"

# ═══════════════════════════════════════════════════════════════════════════
# Utility
# ═══════════════════════════════════════════════════════════════════════════

NO_DATA_NOTICE = "_No data available for this section._\n"
DURATION_PRESENT = "Present"
DURATION_FORMAT = "{start} – {end}"
DURATION_UNKNOWN = "N/A"
