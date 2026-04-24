"""
Custom Exception Hierarchy
==========================

Provides granular, descriptive exceptions for every failure mode in the
LinkedIn Archive MCP pipeline.  Each exception carries a human-readable
message suitable for returning directly through the MCP tool response.

Hierarchy:
    LinkedInArchiveError          (base)
    ├── ArchiveNotFoundError      – folder path does not exist
    ├── InvalidArchiveError       – folder exists but contains no usable CSVs
    ├── CSVParsingError           – a single CSV failed to parse
    ├── HeaderMismatchError       – CSV headers don't match expected schema
    └── OutputWriteError          – could not write Markdown output
"""


class LinkedInArchiveError(Exception):
    """Base exception for all LinkedIn Archive MCP errors."""

    def __init__(self, message: str, details: str | None = None):
        self.details = details
        super().__init__(message)


class ArchiveNotFoundError(LinkedInArchiveError):
    """Raised when the provided folder path does not exist or is not a directory."""

    def __init__(self, folder_path: str):
        super().__init__(
            f"Archive folder not found: '{folder_path}'",
            details="Ensure the path points to an extracted LinkedIn archive directory.",
        )


class InvalidArchiveError(LinkedInArchiveError):
    """Raised when the folder contains no recognizable LinkedIn CSV files."""

    def __init__(self, folder_path: str):
        super().__init__(
            f"No relevant LinkedIn CSV files found in: '{folder_path}'",
            details="Expected files like Profile.csv, Positions.csv, Skills.csv, etc.",
        )


class CSVParsingError(LinkedInArchiveError):
    """Raised when a specific CSV file cannot be read or decoded."""

    def __init__(self, file_path: str, reason: str):
        super().__init__(
            f"Failed to parse CSV: '{file_path}'",
            details=reason,
        )


class HeaderMismatchError(LinkedInArchiveError):
    """Raised when CSV headers do not match the expected schema."""

    def __init__(self, file_path: str, expected: list[str], actual: list[str]):
        super().__init__(
            f"Header mismatch in '{file_path}'",
            details=f"Expected columns containing: {expected}. Found: {actual}",
        )


class OutputWriteError(LinkedInArchiveError):
    """Raised when Markdown output cannot be written to disk."""

    def __init__(self, output_path: str, reason: str):
        super().__init__(
            f"Failed to write output: '{output_path}'",
            details=reason,
        )
