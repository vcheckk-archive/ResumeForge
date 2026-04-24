"""
Shared .env Loader
==================

Central utility that reads the project-root .env file once.
All tool modules import from here instead of reimplementing parsing.

Usage:
    from env_loader import load_env
    env = load_env()
    path = env.get("LINKEDIN_ARCHIVE_PATH", "")
"""

from __future__ import annotations

import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent
_ENV_FILE = _PROJECT_ROOT / ".env"

_cache: dict[str, str] | None = None


def load_env() -> dict[str, str]:
    """
    Load .env file from project root and return as a dict.
    Also injects values into os.environ for downstream libraries.
    Cached after first call.
    """
    global _cache
    if _cache is not None:
        return _cache

    _cache = {}

    if not _ENV_FILE.exists():
        return _cache

    try:
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key and value:
                _cache[key] = value
                # Also set in os.environ for subprocess compatibility
                os.environ.setdefault(key, value)
    except Exception:
        pass

    return _cache


def get_env(key: str, default: str = "") -> str:
    """Get a single env value (from .env file or os.environ)."""
    env = load_env()
    return env.get(key, "") or os.environ.get(key, "") or default
