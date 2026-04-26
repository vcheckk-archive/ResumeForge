"""
ResumeForge MCP Server
=======================

Centralized single point of contact for all MCP tools.
Loads .env config on startup. Each tool reads what it needs.

Tools:
  1. linkedin_ingest_archive   — LinkedIn data export → Markdown
  2. github_build_profile      — GitHub repos → Markdown
  3. coding_extract_profiles   — LeetCode/Codeforces → Markdown
  4. resume_history_analyze    — PDF/DOCX resumes → Markdown
  5. tailor_resume_for_job     — md/ + Job Description → ATS resume

To add a new tool:
  1. Create a new_mcp/ package with a tool.py
  2. Import the function below
  3. Register with mcp.tool()
"""

import logging
import sys

# Load .env BEFORE importing tools (so tokens are available)
from env_loader import load_env
load_env()

from mcp.server.fastmcp import FastMCP

# ── Import tools ──────────────────────────────────────────────────────
from linkedin_mcp.tool import linkedin_ingest_archive
from github_mcp.tool import github_build_profile
from coding_mcp.tool import coding_extract_profiles
from resume_mcp.tool import resume_history_analyze
from tailor_mcp.tool import tailor_resume_for_job

# ── Logging ───────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("resumeforge_mcp")

# ── Server ────────────────────────────────────────────────────────────

mcp = FastMCP("ResumeForgeServer")

# ── Register Tools ────────────────────────────────────────────────────

mcp.tool()(linkedin_ingest_archive)
mcp.tool()(github_build_profile)
mcp.tool()(coding_extract_profiles)
mcp.tool()(resume_history_analyze)
mcp.tool()(tailor_resume_for_job)

# ── Entry Point ───────────────────────────────────────────────────────

def main():
    logger.info("Starting ResumeForge MCP Server (stdio)")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
