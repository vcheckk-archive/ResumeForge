"""
Resume History MCP — Markdown Writer
======================================
Writes the final resume_history.md to disk.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .exceptions import MarkdownWriteError
from .prompts import render_resume_history
from .schemas import ResumeHistory

logger = logging.getLogger(__name__)


def write_resume_history(history: ResumeHistory, out_dir: Path) -> str:
    """
    Render ResumeHistory to Markdown and write to disk.

    Args:
        history:  Fully aggregated + deduplicated ResumeHistory.
        out_dir:  Output directory Path.

    Returns:
        Absolute path to the written file.

    Raises:
        MarkdownWriteError: if the file cannot be written.
    """
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "resume_history.md"

        content = render_resume_history(history)
        out_file.write_text(content, encoding="utf-8")

        logger.info("Written: %s (%d bytes)", out_file, len(content.encode("utf-8")))
        return str(out_file)

    except OSError as e:
        raise MarkdownWriteError(
            f"Cannot write to '{out_dir}'", details=str(e)
        ) from e
    except Exception as e:
        raise MarkdownWriteError(
            "Unexpected error during Markdown generation", details=str(e)
        ) from e
