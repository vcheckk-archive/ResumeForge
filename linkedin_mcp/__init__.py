"""
LinkedIn Archive MCP Tool
=========================

A Model Context Protocol (MCP) server that ingests LinkedIn data exports
and produces clean, resume-focused Markdown files.

Modules:
    server          - FastMCP server entry point
    parser          - CSV discovery, validation, and parsing
    markdown_writer - Structured Markdown generation
    config          - Constants, file mappings, and section ordering
    prompts         - Markdown templates and formatting strings
    schemas         - Type-safe dataclasses for inter-module data flow
    exceptions      - Custom exception hierarchy
    utils           - Date formatting, text cleanup, I/O helpers
"""

__version__ = "1.0.0"
__author__ = "Profile Builder"
