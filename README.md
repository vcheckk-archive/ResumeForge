<div align="center">

# ⚡ ResumeForge

### A modular MCP server that turns your career data into structured Markdown — ready for AI-powered resume generation.

[![CI](https://img.shields.io/github/actions/workflow/status/vijayakanth06/ResumeForge/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/vijayakanth06/ResumeForge/actions)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![MCP Server](https://badge.mcpx.dev?type=server&features=tools)](https://github.com/vijayakanth06/ResumeForge)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)

**[📖 How It Works](#how-it-works) · [🚀 Quick Start](#quick-start) · [🔧 Tools](#tools) · [🔌 MCP Client Setup](#mcp-client-setup) · [🤝 Contributing](CONTRIBUTING.md)**

</div>

---

## What Is ResumeForge?

ResumeForge is a **plug-and-play MCP (Model Context Protocol) server** with four specialized tools, each targeting a different layer of your professional identity:

| Source | Tool | What It Produces |
|---|---|---|
| 🔗 **LinkedIn** | `linkedin_ingest_archive` | 7 Markdown files: identity, summary, experience, education, skills, certifications, projects |
| 🐙 **GitHub** | `github_build_profile` | Per-repo Markdown + portfolio summary from public & private repos |
| 💻 **Coding Platforms** | `coding_extract_profiles` | Stats from LeetCode & Codeforces — rating, problems, contests |
| 📄 **Resume Files** | `resume_history_analyze` | Deduplicated career timeline from multiple PDF/DOCX resumes |

**One `.env` file configures everything. One `server.py` runs everything.**

Connect ResumeForge to Claude Desktop, Cursor, or any MCP-compatible client and call the tools directly in your AI chat.

---

## How It Works

```
Your Data Sources              ResumeForge MCP Tools           Output
─────────────────              ─────────────────────           ──────
LinkedIn Export       ──────►  linkedin_ingest_archive   ──►  md/linkedin/*.md
GitHub Profile        ──────►  github_build_profile      ──►  md/github/**/*.md
LeetCode / Codeforces ──────►  coding_extract_profiles   ──►  md/coding/*.md
Resume Folder (PDF)   ──────►  resume_history_analyze    ──►  md/resume/*.md
                                        │
                               ─────────┼──────────────────────────────────
                               Structured Markdown ready for any LLM/AI agent
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/vijayakanth06/ResumeForge.git
cd ResumeForge
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Open `.env` and fill in your details:

```env
# 1. LinkedIn — path to your extracted data export folder
LINKEDIN_ARCHIVE_PATH=/path/to/LinkedInExport

# 2. GitHub — profile URL + token for private repo access
GITHUB_PROFILE=https://github.com/your-username
GITHUB_TOKEN=ghp_your_classic_token_here

# 3. Coding — comma-separated profile URLs
CODING_PROFILES=https://leetcode.com/u/your-user, https://codeforces.com/profile/your-user

# 4. Resume folder — folder containing your PDF/DOCX resume files
RESUME_HISTORY_PATH=/path/to/your/resumes
```

> **Note:** All fields are optional. Each tool only uses its own config key.

### 3. Run

```bash
python server.py
```

---

## Tools

### `linkedin_ingest_archive`

Parses your official [LinkedIn Data Export](https://www.linkedin.com/mypreferences/d/download-my-data) into 7 clean Markdown files.

```python
# Zero-config — reads LINKEDIN_ARCHIVE_PATH from .env
linkedin_ingest_archive()

# Or pass the path explicitly
linkedin_ingest_archive(folder_path="/path/to/LinkedInExport")
```

**Output:** `md/linkedin/` → `identity.md`, `summary.md`, `experience.md`, `education.md`, `skills.md`, `certifications.md`, `projects.md`

---

### `github_build_profile`

Discovers your repositories via GitHub GraphQL + REST API, scores them by resume relevance, and writes per-repo Markdown.

```python
# Zero-config — reads GITHUB_PROFILE + GITHUB_TOKEN from .env
github_build_profile()

# Pass profile URL directly
github_build_profile(github_profile="https://github.com/your-username")

# With rich project context for better output
github_build_profile(
    github_profile="https://github.com/your-username",
    repo_names=["project-a", "project-b"],
    project_context={
        "project-a": {
            "problem": "What problem it solves",
            "role": "My specific role",
            "impact": "Measurable outcome",
            "technologies": "Python, FastAPI, PostgreSQL",
        }
    }
)
```

**Token modes:**
- `GITHUB_TOKEN` set (Classic token, `repo` scope) → public + private repos via GraphQL (5,000 req/hr)
- No token → public repos only via REST (60 req/hr)

**Output:** `md/github/projects/<repo>.md` + `md/github/projects_summary.md`

---

### `coding_extract_profiles`

Pulls your competitive programming stats directly from platform APIs.

```python
# Zero-config — reads CODING_PROFILES from .env
coding_extract_profiles()

# Pass URLs directly
coding_extract_profiles("https://leetcode.com/u/user, https://codeforces.com/profile/user")

# Or use shorthand
coding_extract_profiles("leetcode: user, codeforces: user")
```

| Platform | API Method | Data Extracted |
|---|---|---|
| LeetCode | GraphQL API | Problems solved, difficulty breakdown, rating, rank, badges, contests |
| Codeforces | Official REST | Current rating, max rating, rank title, contest count |

**Output:** `md/coding/leetcode.md`, `md/coding/codeforces.md`, `md/coding/summary.md`

---

### `resume_history_analyze`

Ingests a folder of past resume versions (PDF + DOCX), deduplicates across versions, reconstructs a career timeline using file dates, and produces one clean Markdown profile.

```python
# Zero-config — reads RESUME_HISTORY_PATH from .env
resume_history_analyze()

# Or pass folder directly
resume_history_analyze(folder_path="/path/to/resumes")
```

**Pipeline:**
1. **Discovery** — scans folder, sorts files by `mtime` (oldest → newest)
2. **Extraction** — `pdfplumber` primary, `PyMuPDF` fallback, `python-docx` for DOCX
3. **Lenient mode** — unclassified sections preserved raw for LLM enrichment
4. **Classification** — detects generic vs company-targeted resumes
5. **Aggregation** — oldest-to-newest merge, latest resume wins conflicts
6. **Deduplication** — fuzzy match (rapidfuzz) for projects/jobs, exact for skills/certs
7. **Timeline** — per-event chronological career progression

**Output:** `md/resume/resume_history.md`

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
│   │   └── <repo-name>.md   (one per selected repo)
│   └── projects_summary.md
│
├── coding/
│   ├── leetcode.md
│   ├── codeforces.md
│   └── summary.md
│
└── resume/
    └── resume_history.md
```

> **Note:** The `md/` directory is git-ignored. It contains your personal career data and is regenerated on each run.

---

## MCP Client Setup

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or  
`%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "resumeforge": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/absolute/path/to/ResumeForge"
    }
  }
}
```

### Cursor

Go to **Settings → MCP → Add Server**:

```json
{
  "mcpServers": {
    "resumeforge": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/absolute/path/to/ResumeForge"
    }
  }
}
```

### With Conda

```json
{
  "mcpServers": {
    "resumeforge": {
      "command": "conda",
      "args": ["run", "-n", "your-env-name", "python", "server.py"],
      "cwd": "/absolute/path/to/ResumeForge"
    }
  }
}
```

---

## Architecture

Each data source is a fully self-contained module. Adding a new source means creating a new `*_mcp/` package — zero changes to existing code.

```
ResumeForge/
├── server.py              # Central MCP server — single entry point
├── env_loader.py          # Shared .env reader — used by all tools
├── .env.example           # Config template
│
├── linkedin_mcp/          # Tool: LinkedIn archive
│   ├── tool.py            #   linkedin_ingest_archive()
│   ├── parser.py          #   CSV discovery + parsing
│   ├── markdown_writer.py #   Markdown generation
│   ├── config.py          #   File mappings, section categories
│   ├── prompts.py         #   Markdown templates
│   ├── schemas.py         #   Typed dataclasses
│   ├── exceptions.py      #   Custom error hierarchy
│   └── utils.py           #   Helpers
│
├── github_mcp/            # Tool: GitHub projects
│   ├── tool.py            #   github_build_profile()
│   ├── api.py             #   GraphQL + REST client with rate-limit handling
│   ├── analyzer.py        #   Tech stack inference + relevance scoring
│   ├── markdown_writer.py #   Per-repo + summary Markdown
│   ├── config.py          #   API URLs, tech keywords, thresholds
│   ├── prompts.py         #   Markdown templates
│   ├── schemas.py         #   Typed dataclasses
│   └── exceptions.py      #   Custom errors
│
├── coding_mcp/            # Tool: Coding platforms
│   ├── tool.py            #   coding_extract_profiles()
│   ├── api.py             #   LeetCode GraphQL + Codeforces REST fetchers
│   ├── markdown_writer.py #   Per-platform + summary Markdown
│   ├── config.py          #   URL patterns, API endpoints, strength thresholds
│   ├── prompts.py         #   Markdown templates
│   ├── schemas.py         #   Typed dataclasses
│   └── exceptions.py      #   Custom errors
│
├── resume_mcp/            # Tool: Resume history analysis
│   ├── tool.py            #   resume_history_analyze()
│   ├── extractor.py       #   pdfplumber → PyMuPDF fallback + DOCX
│   ├── classifier.py      #   generic vs company-specific detection
│   ├── aggregator.py      #   merge all RawResumes
│   ├── deduplicator.py    #   fuzzy + exact dedup engine
│   ├── timeline.py        #   career progression reconstruction
│   ├── markdown_writer.py #   final Markdown output
│   ├── prompts.py         #   Markdown templates
│   ├── schemas.py         #   Typed dataclasses
│   ├── config.py          #   section keywords, thresholds
│   └── exceptions.py      #   custom errors
│
└── .github/
    ├── workflows/ci.yml          # CI: import checks on Python 3.10/3.11/3.12
    ├── ISSUE_TEMPLATE/           # Bug + feature templates
    └── PULL_REQUEST_TEMPLATE.md
```

---

## Extending ResumeForge

### Add a new MCP tool module

1. Create `new_source_mcp/` with `tool.py`, `schemas.py`, `config.py`, `exceptions.py`
2. Implement `new_source_extract(input: str | None = None) -> dict`
3. Register in `server.py`:
   ```python
   from new_source_mcp.tool import new_source_extract
   mcp.tool()(new_source_extract)
   ```
4. Add config key to `.env.example`

### Add a new coding platform

1. Add URL regex to `coding_mcp/config.py` → `PLATFORM_PATTERNS`
2. Write `fetch_<platform>(username)` in `coding_mcp/api.py`
3. Register in `PLATFORM_FETCHERS` dict

---

## Requirements

| Dependency | Purpose |
|---|---|
| `mcp[cli] >= 1.2.0` | FastMCP server SDK |
| `pandas >= 2.0.0` | LinkedIn CSV parsing |
| `httpx >= 0.27.0` | Async HTTP client (GitHub + coding APIs) |
| `pdfplumber >= 0.11.0` | PDF text extraction (primary) |
| `PyMuPDF >= 1.24.0` | PDF extraction fallback |
| `python-docx >= 1.1.0` | DOCX extraction |
| `python-dateutil >= 2.9.0` | Smart date parsing |
| `rapidfuzz >= 3.6.0` | Fuzzy string matching for deduplication |

**Python 3.10+ required.**

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, coding standards, and how to add new platforms or tools.

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a full history of releases.

---

## License

MIT — see [LICENSE](LICENSE) for details.
