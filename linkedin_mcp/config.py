"""
Configuration Module
====================

Central source of truth for all constants used across the pipeline.

To adapt this tool to a different LinkedIn export format, edit **only**
this file — specifically ``RELEVANT_FILES`` (column names) and
``SKILL_CATEGORIES`` (grouping keywords).

Design Principles:
    - Single Responsibility: all magic strings live here, nowhere else.
    - Open/Closed: add new sections by appending to RELEVANT_FILES and
      SECTION_ORDER — no other module needs modification.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Relevant CSV files — the ONLY files we process
# ---------------------------------------------------------------------------
# Each entry maps a logical section name to:
#   filename : primary filename to look for (case-insensitive match)
#   required_headers : minimum columns that MUST be present for fallback
#                      header-based detection
#   optional : if True, missing file is not an error

RELEVANT_FILES: dict[str, dict] = {
    "profile": {
        "filename": "Profile.csv",
        "required_headers": ["First Name", "Last Name", "Headline"],
        "optional": False,
    },
    "profile_summary": {
        "filename": "Profile Summary.csv",
        "required_headers": ["Profile Summary"],
        "optional": True,
    },
    "email": {
        "filename": "Email Addresses.csv",
        "required_headers": ["Email Address"],
        "optional": True,
    },
    "positions": {
        "filename": "Positions.csv",
        "required_headers": ["Company Name", "Title"],
        "optional": True,
    },
    "education": {
        "filename": "Education.csv",
        "required_headers": ["School Name"],
        "optional": True,
    },
    "skills": {
        "filename": "Skills.csv",
        "required_headers": ["Name"],
        "optional": True,
    },
    "certifications": {
        "filename": "Certifications.csv",
        "required_headers": ["Name", "Authority"],
        "optional": True,
    },
    "projects": {
        "filename": "Projects.csv",
        "required_headers": ["Title"],
        "optional": True,
    },
}

# ---------------------------------------------------------------------------
# Explicitly excluded files / folders — logged as "skipped"
# ---------------------------------------------------------------------------
EXCLUDED_PATTERNS: list[str] = [
    "Jobs",
    "Connections.csv",
    "messages.csv",
    "Ad_Targeting.csv",
    "Company Follows.csv",
    "Invitations.csv",
    "Events.csv",
    "Learning.csv",
    "SavedJobAlerts.csv",
    "PhoneNumbers.csv",
    "Whatsapp Phone Numbers.csv",
    "Registration.csv",
    "Rich_Media.csv",
    "guide_messages.csv",
    "learning_coach_messages.csv",
    "learning_role_play_messages.csv",
    "Job Applicant Saved Screening Question Responses.csv",
    "Job Applicant Saved Answers.csv",
    "Job Applications.csv",
    "Job Seeker Preferences.csv",
    "Saved Jobs.csv",
    "Verifications",
]

# ---------------------------------------------------------------------------
# Section ordering for processing and output
# ---------------------------------------------------------------------------
SECTION_ORDER: list[str] = [
    "identity",
    "summary",
    "experience",
    "education",
    "skills",
    "certifications",
    "projects",
]

# ---------------------------------------------------------------------------
# Output configuration
# ---------------------------------------------------------------------------
DEFAULT_OUTPUT_DIR: Path = Path("md") / "linkedin"

# ---------------------------------------------------------------------------
# Skill categorization keywords
# ---------------------------------------------------------------------------
# Each category has a display name and a set of keywords (lowercase).
# Skills are matched in order — first match wins.
# A skill that matches no category falls into "Other".

SKILL_CATEGORIES: list[dict[str, str | set[str]]] = [
    {
        "name": "Programming Languages",
        "keywords": {
            "python", "java", "javascript", "html", "css",
            "c", "c++", "c#", "typescript", "go", "rust", "ruby",
            "php", "swift", "kotlin", "r", "scala", "sql",
            "python (programming language)",
            "cascading style sheets (css)",
        },
    },
    {
        "name": "AI / ML / Data Science",
        "keywords": {
            "tensorflow", "deep learning", "deeplearning", "opencv",
            "machine learning", "machine learning algorithms",
            "natural language processing (nlp)", "nlp",
            "large language models (llm)", "large language models(llms)",
            "image processing", "feature engineering", "feature extraction",
            "forecasting", "classification", "data preparation",
            "chatbot development", "chatbots", "matplotlib",
        },
    },
    {
        "name": "Frameworks & Tools",
        "keywords": {
            "react.js", "react", "spring boot", "mern stack",
            "mongodb", "firebase", "rest apis", "pymongo",
            "application programming interfaces (api)",
            "back-end web development", "full-stack development",
            "telegram",
        },
    },
    {
        "name": "Soft Skills & Management",
        "keywords": {
            "communication", "teamwork", "problem solving",
            "project management", "leadership", "collaboration",
        },
    },
    {
        "name": "Other",
        "keywords": set(),  # catch-all — matches anything left over
    },
]

# ---------------------------------------------------------------------------
# CSV parsing defaults
# ---------------------------------------------------------------------------
CSV_ENCODINGS: list[str] = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
