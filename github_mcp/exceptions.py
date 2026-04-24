"""
Custom Exception Hierarchy — GitHub MCP
=======================================

Hierarchy:
    GitHubMCPError            (base)
    ├── GitHubAPIError        – API call failure (non-rate-limit)
    ├── RateLimitError        – 403 / rate limit exceeded
    ├── RepoNotFoundError     – specific repo doesn't exist or no access
    ├── AuthenticationError   – token invalid or insufficient scope
    └── OutputWriteError      – cannot write Markdown output
"""


class GitHubMCPError(Exception):
    """Base exception for all GitHub MCP errors."""

    def __init__(self, message: str, details: str | None = None):
        self.details = details
        super().__init__(message)


class GitHubAPIError(GitHubMCPError):
    """Raised when a GitHub API call fails."""

    def __init__(self, endpoint: str, status_code: int, message: str = ""):
        super().__init__(
            f"GitHub API error ({status_code}): {endpoint}",
            details=message or f"HTTP {status_code}",
        )
        self.status_code = status_code


class RateLimitError(GitHubMCPError):
    """Raised when GitHub API rate limit is exceeded."""

    def __init__(self, reset_at: str | None = None):
        msg = "GitHub API rate limit exceeded"
        if reset_at:
            msg += f". Resets at: {reset_at}"
        super().__init__(msg, details="Provide an auth_token to increase rate limits (5000/hr vs 60/hr).")


class RepoNotFoundError(GitHubMCPError):
    """Raised when a specific repo doesn't exist or is inaccessible."""

    def __init__(self, owner: str, name: str):
        super().__init__(
            f"Repository not found: {owner}/{name}",
            details="Check the name, or provide an auth_token for private repos.",
        )


class AuthenticationError(GitHubMCPError):
    """Raised when the auth token is invalid or has insufficient scope."""

    def __init__(self, message: str = ""):
        super().__init__(
            "GitHub authentication failed",
            details=message or "Check that your token is valid and has 'repo' scope.",
        )


class OutputWriteError(GitHubMCPError):
    """Raised when Markdown output cannot be written to disk."""

    def __init__(self, output_path: str, reason: str):
        super().__init__(
            f"Failed to write output: '{output_path}'",
            details=reason,
        )
