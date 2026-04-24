"""
Exceptions — Coding MCP
"""


class CodingMCPError(Exception):
    def __init__(self, message: str, details: str | None = None):
        self.details = details
        super().__init__(message)


class PlatformAPIError(CodingMCPError):
    def __init__(self, platform: str, status: int, msg: str = ""):
        super().__init__(f"{platform} API error ({status})", details=msg)
        self.platform = platform


class ProfileNotFoundError(CodingMCPError):
    def __init__(self, platform: str, username: str):
        super().__init__(
            f"Profile not found: {username} on {platform}",
            details="Check the username or URL.",
        )


class UnsupportedPlatformError(CodingMCPError):
    def __init__(self, domain: str):
        super().__init__(
            f"Unsupported platform: {domain}",
            details="Supported: LeetCode, Codeforces, GeeksforGeeks, HackerRank, HackerEarth",
        )
