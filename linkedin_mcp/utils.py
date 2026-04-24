"""
Utility Functions
=================

Pure helper functions shared across modules.  Every function is
deterministic with no side effects (except ``ensure_directory``).

Functions:
    clean_text        – strip whitespace, normalize empty → None
    format_duration   – build "Mon YYYY – Mon YYYY" strings
    safe_get          – safely extract a column from a DataFrame row
    ensure_directory  – create output directory if needed
    parse_website_field – extract URLs from LinkedIn's website format
"""

from __future__ import annotations

import logging
from pathlib import Path

from . import prompts

logger = logging.getLogger(__name__)


def clean_text(value: object) -> str | None:
    """
    Convert a value to a stripped string, or ``None`` if empty / NaN.

    Works safely with pandas NaN, None, empty strings, and whitespace.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    return text


def format_duration(start: str | None, end: str | None) -> str:
    """
    Build a human-readable duration string.

    Examples:
        ("Jul 2025", "Oct 2025")  → "Jul 2025 – Oct 2025"
        ("Jul 2025", None)        → "Jul 2025 – Present"
        (None, None)              → "N/A"
    """
    s = clean_text(start)
    e = clean_text(end)

    if not s and not e:
        return prompts.DURATION_UNKNOWN
    if not e:
        e = prompts.DURATION_PRESENT
    if not s:
        s = prompts.DURATION_UNKNOWN

    return prompts.DURATION_FORMAT.format(start=s, end=e)


def safe_get(row: object, column: str) -> str | None:
    """
    Safely extract a value from a pandas Series (row) by column name.

    Returns ``None`` if the column doesn't exist or the value is empty.
    """
    try:
        return clean_text(getattr(row, column, None) if hasattr(row, column) else row[column])  # type: ignore[index]
    except (KeyError, TypeError, AttributeError):
        return None


def ensure_directory(path: Path) -> Path:
    """Create the directory (and parents) if it doesn't exist. Returns the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def parse_website_field(raw: str | None) -> list[str]:
    """
    Parse LinkedIn's website field format into a list of URLs.

    LinkedIn exports websites as: ``[LABEL:URL],[LABEL:URL]``
    Example: ``[PORTFOLIO:https://example.com]``

    Returns a list of extracted URLs.
    """
    if not raw:
        return []

    cleaned = clean_text(raw)
    if not cleaned:
        return []

    urls: list[str] = []
    # Split by ],[  to handle multiple entries
    entries = cleaned.replace("][", "]|[").split("|")
    for entry in entries:
        entry = entry.strip("[] ")
        if ":" in entry:
            # Take everything after the first colon (label:url)
            parts = entry.split(":", 1)
            if len(parts) == 2:
                url = parts[1].strip()
                # Reconstruct if the URL itself had a colon (https:)
                if url and not url.startswith("http"):
                    # Label might contain the scheme, try full split
                    full = entry
                    idx = full.find("http")
                    if idx != -1:
                        url = full[idx:]
                if url and url.startswith("http"):
                    urls.append(url)

    return urls
