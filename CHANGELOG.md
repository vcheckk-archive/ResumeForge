# Changelog

All notable changes to ResumeForge are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Planned
- HackerRank and GeeksforGeeks platform support in `coding_mcp`
- Web UI dashboard for running tools interactively
- Docker image for zero-setup deployment

---

## [1.1.0] — 2025-04-26

### Added
- **`resume_mcp`** — Resume History Analysis Tool
  - Ingests folders of PDF + DOCX resume files
  - Dual PDF parser: `pdfplumber` primary, `PyMuPDF` fallback
  - Lenient extraction mode: all sections captured for LLM enrichment
  - Fuzzy deduplication via `rapidfuzz` for projects and job entries
  - Chronological career timeline reconstruction using file `mtime`
  - Company-specific resume classification
  - Output: `md/resume/resume_history.md`
- `RESUME_HISTORY_PATH` config key in `.env`

### Changed
- `requirements.txt` updated with new dependencies: `pdfplumber`, `PyMuPDF`, `python-docx`, `python-dateutil`, `rapidfuzz`

---

## [1.0.0] — 2025-04-24

### Added
- **`linkedin_mcp`** — LinkedIn Archive Ingestion Tool
  - Parses official LinkedIn data export (CSV files)
  - Outputs 7 resume-section Markdown files
- **`github_mcp`** — GitHub Project Intelligence Tool
  - GraphQL + REST GitHub API client
  - Auto-selects resume-worthy repositories by relevance score
  - Generates per-repo `.md` files and a portfolio summary
  - Token auto-loaded from `.env`
- **`coding_mcp`** — Coding Platforms Extractor
  - LeetCode via GraphQL API
  - Codeforces via official REST API
  - URL and shorthand input parsing
- **`server.py`** — Centralized FastMCP server (single entry point)
- **`env_loader.py`** — Shared `.env` reader used by all tools
- **`.env.example`** — Unified config template for all tools
