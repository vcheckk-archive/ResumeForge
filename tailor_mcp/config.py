"""
Tailor MCP — Configuration
============================
All constants, paths, and thresholds for the tailor_mcp module.
"""

from __future__ import annotations

# ── Output ────────────────────────────────────────────────────────────
DEFAULT_MD_DIR = "md"
DEFAULT_OUTPUT_DIR = "md/tailored"

# ── Supported JD file types ──────────────────────────────────────────
SUPPORTED_JD_EXTENSIONS = {".txt", ".pdf", ".docx", ".md"}

# ── MD subdirectories to scan (outputs of the 4 MCP tools) ───────────
MD_SUBDIRS = ["linkedin", "github", "coding", "resume"]
