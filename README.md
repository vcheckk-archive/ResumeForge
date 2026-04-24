# Profile Builder MCP Server

A centralized **Model Context Protocol (MCP)** server that ingests career data from **LinkedIn**, **GitHub**, and **coding platforms** to produce clean, structured Markdown files optimized for resume development.

**One `.env` file. Three data sources. Complete resume-ready Markdown output.**

---

## Features

- **Single Config** — Set all inputs in one `.env` file
- **Single Server** — One `server.py` serves all tools via MCP
- **Plug-and-Play** — Each data source is a separate module; add new ones easily
- **Resume-Focused** — Output is structured for direct use in resume generation
- **Graceful Failures** — Errors are collected, never crash

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/profile_builder.git
cd profile_builder
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` with your details:

```env
# LinkedIn — path to your extracted data export
LINKEDIN_ARCHIVE_PATH=C:\Users\you\Downloads\LinkedInExport

# GitHub — profile URL + optional token for private repos
GITHUB_PROFILE=https://github.com/your-username
GITHUB_TOKEN=ghp_your_token_here

# Coding — paste your profile URLs
CODING_PROFILES=https://leetcode.com/u/your-user, https://codeforces.com/profile/your-user
```

### 3. Run

```bash
python server.py
```

---

## Registered Tools

| Tool | What It Does | Input |
|---|---|---|
| `linkedin_ingest_archive` | Parses LinkedIn CSV export into 7 resume sections | Archive folder path or `.env` |
| `github_build_profile` | Extracts GitHub projects into per-repo Markdown | Profile URL or `.env` |
| `coding_extract_profiles` | Pulls coding stats from LeetCode & Codeforces | Profile URLs or `.env` |

All tools read from `.env` when no arguments are provided, making them zero-config for MCP clients.

---

## Output Structure

```
md/
├── linkedin/
│   ├── identity.md
│   ├── summary.md
│   ├── experience.md
│   ├── education.md
│   ├── skills.md
│   ├── certifications.md
│   └── projects.md
│
├── github/
│   ├── projects/
│   │   ├── repo_name_1.md
│   │   └── repo_name_2.md
│   └── projects_summary.md
│
└── coding/
    ├── leetcode.md
    ├── codeforces.md
    └── summary.md
```

---

## Architecture

```
profile_builder/
├── server.py              # Central MCP Server (single entry point)
├── env_loader.py          # Shared .env reader (used by all tools)
├── .env                   # YOUR config (git-ignored)
├── .env.example           # Template
├── .gitignore
├── pyproject.toml
├── requirements.txt
│
├── linkedin_mcp/          # Tool: LinkedIn Archive
│   ├── tool.py            #   linkedin_ingest_archive()
│   ├── parser.py          #   CSV discovery + parsing
│   ├── markdown_writer.py #   Markdown generation
│   ├── config.py          #   File mappings, categories
│   ├── prompts.py         #   Output templates
│   ├── schemas.py         #   Typed dataclasses
│   ├── exceptions.py      #   Custom errors
│   └── utils.py           #   Helpers
│
├── github_mcp/            # Tool: GitHub Projects
│   ├── tool.py            #   github_build_profile()
│   ├── api.py             #   GraphQL + REST client
│   ├── analyzer.py        #   Tech stack inference
│   ├── markdown_writer.py #   Per-repo + summary .md
│   ├── config.py          #   API URLs, tech keywords
│   ├── prompts.py         #   Output templates
│   ├── schemas.py         #   Typed dataclasses
│   └── exceptions.py      #   Custom errors
│
└── coding_mcp/            # Tool: Coding Platforms
    ├── tool.py            #   coding_extract_profiles()
    ├── api.py             #   LeetCode GraphQL + Codeforces REST
    ├── markdown_writer.py #   Per-platform + summary .md
    ├── config.py          #   URL patterns, thresholds
    ├── prompts.py         #   Output templates
    ├── schemas.py         #   Typed dataclasses
    └── exceptions.py      #   Custom errors
```

---

## MCP Client Configuration

### Claude Desktop

```json
{
  "mcpServers": {
    "profile-builder": {
      "command": "conda",
      "args": ["run", "-n", "gpu-env", "python", "server.py"],
      "cwd": "/path/to/profile_builder"
    }
  }
}
```

### Cursor

```json
{
  "mcpServers": {
    "profile-builder": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/path/to/profile_builder"
    }
  }
}
```

---

## Tool Reference

### `linkedin_ingest_archive`

```python
# Reads LINKEDIN_ARCHIVE_PATH from .env
linkedin_ingest_archive()

# Or pass path directly
linkedin_ingest_archive(folder_path="/path/to/archive")
```

**Output:** 7 Markdown files covering identity, summary, experience, education, skills, certifications, and projects.

**Data source:** [LinkedIn Data Export](https://www.linkedin.com/mypreferences/d/download-my-data)

---

### `github_build_profile`

```python
# Reads GITHUB_PROFILE + GITHUB_TOKEN from .env
github_build_profile()

# Or pass directly
github_build_profile(github_profile="https://github.com/username")

# With project interview context for richer output
github_build_profile(
    github_profile="https://github.com/username",
    repo_names=["project1", "project2"],
    project_context={
        "project1": {
            "problem": "What problem it solves",
            "role": "My role",
            "challenges": "What was hard",
            "impact": "Results achieved",
            "technologies": "Python, FastAPI",
            "key_features": "Feature1, Feature2"
        }
    }
)
```

**Token modes:**
- With `GITHUB_TOKEN` → private + public repos via GraphQL (5000 req/hr)
- Without token → public repos only via REST (60 req/hr)

**Accepts:** `https://github.com/user`, `github.com/user`, or just `user`

---

### `coding_extract_profiles`

```python
# Reads CODING_PROFILES from .env
coding_extract_profiles()

# Or pass directly (URLs or shorthand)
coding_extract_profiles("https://leetcode.com/u/user, https://codeforces.com/profile/user")
coding_extract_profiles("leetcode: user, codeforces: user")
```

**Supported platforms:**

| Platform | Method | Data Extracted |
|---|---|---|
| LeetCode | GraphQL API | Problems solved, difficulty breakdown, rating, badges, contests |
| Codeforces | Official REST API | Rating, max rating, rank, contest count |

---

## Adding New Tools

### New MCP Tool Module

```bash
mkdir new_mcp
touch new_mcp/__init__.py new_mcp/tool.py
```

```python
# new_mcp/tool.py
def my_new_tool(input_data: str) -> dict:
    """Your tool description here."""
    return {"result": "..."}
```

```python
# server.py — add these lines:
from new_mcp.tool import my_new_tool
mcp.tool()(my_new_tool)
```

### New Coding Platform

1. Add URL pattern to `coding_mcp/config.py → PLATFORM_PATTERNS`
2. Write `fetch_<platform>(username)` function in `coding_mcp/api.py`
3. Register in `PLATFORM_FETCHERS` dict at bottom of `api.py`

---

## Requirements

- Python 3.10+
- `mcp[cli]` — MCP SDK (FastMCP server)
- `pandas` — CSV parsing (LinkedIn)
- `httpx` — HTTP client (GitHub + coding APIs)

---

## License

MIT
