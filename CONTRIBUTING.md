# Contributing to ResumeForge

Thank you for your interest in contributing! This document explains how to get involved.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Adding a New Tool Module](#adding-a-new-tool-module)
- [Adding a New Coding Platform](#adding-a-new-coding-platform)
- [Coding Standards](#coding-standards)
- [Submitting a Pull Request](#submitting-a-pull-request)

---

## Code of Conduct

By participating in this project, you agree to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). Please treat everyone with respect.

---

## How to Contribute

There are many ways to contribute:

- 🐛 **Report a bug** — Open an [issue](../../issues/new?template=bug_report.md)
- 💡 **Suggest a feature** — Open a [feature request](../../issues/new?template=feature_request.md)
- 📖 **Improve documentation** — Fix typos, clarify instructions, add examples
- 🔌 **Add a new platform** — Extend `coding_mcp` with HackerRank, GFG, etc.
- 🧩 **Add a new tool module** — Build a new `*_mcp/` package

---

## Development Setup

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/ResumeForge.git
cd ResumeForge

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your environment
cp .env.example .env
# Edit .env with your own values

# 5. Verify setup
python -c "from server import mcp; print(list(mcp._tool_manager._tools.keys()))"
```

---

## Project Structure

```
ResumeForge/
├── server.py              # Central MCP server — register tools here
├── env_loader.py          # Shared .env reader
├── .env.example           # Config template
│
├── linkedin_mcp/          # Tool: LinkedIn archive ingestion
├── github_mcp/            # Tool: GitHub project extraction
├── coding_mcp/            # Tool: Coding platform stats
├── resume_mcp/            # Tool: Resume history analysis
│
├── .github/
│   ├── workflows/         # CI pipelines
│   └── ISSUE_TEMPLATE/    # Bug + feature templates
│
└── docs/                  # Extended documentation (optional)
```

Each `*_mcp/` module follows this pattern:

| File | Responsibility |
|---|---|
| `tool.py` | MCP gateway function — single public entry point |
| `api.py` / `extractor.py` | Data fetching / parsing |
| `schemas.py` | Typed dataclasses |
| `config.py` | All constants, patterns, thresholds |
| `prompts.py` | All Markdown templates |
| `markdown_writer.py` | File output |
| `exceptions.py` | Custom error hierarchy |

---

## Adding a New Tool Module

1. Create the package:
   ```bash
   mkdir my_source_mcp
   touch my_source_mcp/__init__.py my_source_mcp/tool.py ...
   ```

2. Implement the gateway function in `tool.py`:
   ```python
   def my_source_extract(input_data: str | None = None) -> dict:
       """One-line summary of what this tool does."""
       ...
       return {"success": True, "output_path": "..."}
   ```

3. Register in `server.py`:
   ```python
   from my_source_mcp.tool import my_source_extract
   mcp.tool()(my_source_extract)
   ```

4. Add the config key to `.env.example`.

5. Open a PR with a clear description of the data source and API method used.

---

## Adding a New Coding Platform

1. Add URL regex pattern to `coding_mcp/config.py` → `PLATFORM_PATTERNS`
2. Write `fetch_<platform>(username: str) -> CodingProfile` in `coding_mcp/api.py`
3. Add an entry to `PLATFORM_FETCHERS` dict in `coding_mcp/api.py`
4. Test with a real profile URL

---

## Coding Standards

- **Python 3.10+** with type annotations (`from __future__ import annotations`)
- **Docstrings** on all public functions
- **Logging** via `logging.getLogger(__name__)` — no `print()` statements in library code
- **Exceptions** — raise typed exceptions from `exceptions.py`, never bare `Exception`
- **Config** — all constants in `config.py`, never hardcoded in logic files
- **Prompts** — all Markdown templates in `prompts.py`, never inline in logic

---

## Submitting a Pull Request

1. **Open an issue first** for non-trivial changes so we can discuss approach
2. **Branch from `main`**: `git checkout -b feat/my-feature`
3. **Write clear commit messages**: `feat: add HackerRank extractor`
4. **Test your changes** before opening the PR
5. **Fill in the PR template** — describe what changed and why
6. A maintainer will review within a few days

Thank you for making ResumeForge better! 🚀
