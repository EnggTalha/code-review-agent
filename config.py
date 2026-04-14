"""
config.py — Central config and data models for the Code Review Agent.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
DATA_DIR   = BASE_DIR / "data"
REPOS_DIR  = DATA_DIR / "repos"
REPORTS_DIR = DATA_DIR / "reports"
PATCHES_DIR = DATA_DIR / "patches"
LOG_DIR    = BASE_DIR / "logs"

for d in [REPOS_DIR, REPORTS_DIR, PATCHES_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ── Env ────────────────────────────────────────────────────────────────
class EnvConfig:
    ANTHROPIC_API_KEY:   str = os.getenv("ANTHROPIC_API_KEY", "")
    GITHUB_TOKEN:        str = os.getenv("GITHUB_TOKEN", "")
    MAX_FILES:           int = int(os.getenv("MAX_FILES_PER_RUN", "20"))
    MAX_FILE_SIZE_KB:    int = int(os.getenv("MAX_FILE_SIZE_KB", "100"))
    DRY_RUN:            bool = os.getenv("DRY_RUN", "true").lower() == "true"
    SEVERITY_THRESHOLD:  str = os.getenv("SEVERITY_THRESHOLD", "medium")
    REVIEW_FOCUS:  List[str] = [
        f.strip() for f in os.getenv("REVIEW_FOCUS", "bugs,security,performance").split(",")
    ]


# ── Severity ordering ──────────────────────────────────────────────────
SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


# ── Data Models ────────────────────────────────────────────────────────
class CodeIssue(BaseModel):
    file:        str
    line_start:  int
    line_end:    int
    severity:    str          # low | medium | high | critical
    category:    str          # bug | security | performance | style | refactor
    title:       str
    description: str
    suggestion:  str
    code_before: Optional[str] = None
    code_after:  Optional[str] = None


class FileReview(BaseModel):
    file_path:       str
    language:        str
    lines_of_code:   int
    issues:          List[CodeIssue] = Field(default_factory=list)
    overall_score:   int             # 0–100 (100 = perfect)
    summary:         str
    refactored_code: Optional[str] = None   # full refactored file if changes made


class RepoReview(BaseModel):
    repo_url:         str
    repo_name:        str
    total_files:      int
    reviewed_files:   int
    file_reviews:     List[FileReview] = Field(default_factory=list)
    critical_count:   int = 0
    high_count:       int = 0
    medium_count:     int = 0
    low_count:        int = 0
    overall_score:    int = 0
    top_issues:       List[CodeIssue] = Field(default_factory=list)
    executive_summary: str = ""


# ── Supported languages ────────────────────────────────────────────────
SUPPORTED_EXTENSIONS = {
    ".py":   "Python",
    ".js":   "JavaScript",
    ".ts":   "TypeScript",
    ".jsx":  "JavaScript (React)",
    ".tsx":  "TypeScript (React)",
    ".java": "Java",
    ".go":   "Go",
    ".rs":   "Rust",
    ".cpp":  "C++",
    ".c":    "C",
    ".cs":   "C#",
    ".rb":   "Ruby",
    ".php":  "PHP",
}

# Files/dirs to always skip
IGNORE_PATTERNS = [
    "node_modules", "__pycache__", ".git", "venv", ".venv",
    "dist", "build", ".next", "coverage", "*.min.js",
    "*.lock", "package-lock.json", "yarn.lock",
]
