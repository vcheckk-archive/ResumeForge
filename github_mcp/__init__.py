"""
GitHub MCP Tool
===============

Extracts project data from GitHub repositories and produces
resume-focused Markdown documents.

Modules:
    tool            - 3 public tool functions for MCP registration
    api             - GitHub GraphQL + REST API client
    analyzer        - Tech stack inference, README parsing, repo scoring
    markdown_writer - Per-repo and summary Markdown generation
    config          - API URLs, tech keywords, output paths
    prompts         - All Markdown formatting templates
    schemas         - Typed dataclasses for data flow
    exceptions      - Custom exception hierarchy
"""

__version__ = "1.0.0"
__author__ = "Profile Builder"
