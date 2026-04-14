"""
agent/reviewer.py — Claude-powered code review and refactoring engine.
Analyzes each file for bugs, security issues, performance, and style.
Produces structured issues with before/after code diffs.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
import anthropic
from rich.console import Console

from config import (
    EnvConfig, CodeIssue, FileReview, RepoReview,
    SEVERITY_ORDER
)

console = Console()
_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=EnvConfig.ANTHROPIC_API_KEY)
    return _client


# ── File-level review ──────────────────────────────────────────────────

def review_file(file_path: str, code: str, language: str) -> FileReview:
    """
    Send a source file to Claude for full review.
    Returns structured issues + optional refactored version.
    """
    lines = code.splitlines()
    loc = len([l for l in lines if l.strip() and not l.strip().startswith("#")])

    focus = ", ".join(EnvConfig.REVIEW_FOCUS) if "all" not in EnvConfig.REVIEW_FOCUS else "bugs, security, performance, style, refactor, documentation"

    prompt = f"""You are a senior software engineer conducting a thorough code review.

FILE: {file_path}
LANGUAGE: {language}
REVIEW FOCUS: {focus}

CODE:
```{language.lower()}
{code}
```

Analyze this code carefully. Find ALL issues in the focus areas.

Respond ONLY with a JSON object (no markdown fences, no explanation):
{{
  "file_path": "{file_path}",
  "language": "{language}",
  "lines_of_code": {loc},
  "overall_score": <integer 0-100, 100=perfect code>,
  "summary": "2-3 sentence overall assessment",
  "issues": [
    {{
      "file": "{file_path}",
      "line_start": <int>,
      "line_end": <int>,
      "severity": "low|medium|high|critical",
      "category": "bug|security|performance|style|refactor|documentation",
      "title": "Short descriptive title",
      "description": "What is wrong and why it matters",
      "suggestion": "How to fix it",
      "code_before": "the problematic code snippet (exact, from file)",
      "code_after": "the fixed/improved version"
    }}
  ],
  "refactored_code": "The COMPLETE refactored file with ALL issues fixed (null if no changes needed)"
}}

Severity guide:
- critical: security vulnerability, data loss, crash
- high: significant bug, major performance issue
- medium: code smell, moderate performance, missing error handling
- low: style, naming, minor improvement"""

    try:
        resp = get_client().messages.create(
            model="claude-opus-4-5",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)

        # Filter by severity threshold
        threshold = SEVERITY_ORDER.get(EnvConfig.SEVERITY_THRESHOLD, 1)
        data["issues"] = [
            i for i in data.get("issues", [])
            if SEVERITY_ORDER.get(i.get("severity", "low"), 0) >= threshold
        ]

        return FileReview(**data)

    except json.JSONDecodeError as e:
        console.print(f"  [red]JSON parse error for {file_path}:[/red] {e}")
        return _empty_review(file_path, language, loc, error=str(e))
    except Exception as e:
        console.print(f"  [red]Review failed for {file_path}:[/red] {e}")
        return _empty_review(file_path, language, loc, error=str(e))


# ── Repo-level synthesis ───────────────────────────────────────────────

def synthesize_repo_review(
    repo_url: str,
    repo_name: str,
    total_files: int,
    file_reviews: list[FileReview],
) -> RepoReview:
    """
    Use Claude to synthesize all file reviews into a repo-level report
    with executive summary, top issues, and overall score.
    """
    console.print("[cyan]Synthesizing repo-level review...[/cyan]")

    all_issues = [issue for fr in file_reviews for issue in fr.issues]
    critical = sum(1 for i in all_issues if i.severity == "critical")
    high     = sum(1 for i in all_issues if i.severity == "high")
    medium   = sum(1 for i in all_issues if i.severity == "medium")
    low      = sum(1 for i in all_issues if i.severity == "low")

    avg_score = int(sum(fr.overall_score for fr in file_reviews) / max(len(file_reviews), 1))

    # Pick top issues (critical first, then high)
    sorted_issues = sorted(all_issues, key=lambda i: SEVERITY_ORDER.get(i.severity, 0), reverse=True)
    top_issues = sorted_issues[:10]

    # Ask Claude for executive summary
    issues_summary = "\n".join([
        f"- [{i.severity.upper()}] {i.title} in {i.file} (line {i.line_start})"
        for i in sorted_issues[:20]
    ])

    prompt = f"""You are a senior engineering lead. Write a concise executive summary for this codebase review.

Repo: {repo_url}
Files reviewed: {len(file_reviews)} / {total_files}
Average quality score: {avg_score}/100
Issues found: {critical} critical, {high} high, {medium} medium, {low} low

Top issues:
{issues_summary}

Write a 3-4 sentence executive summary covering:
1. Overall code quality assessment
2. Most critical concerns to address immediately
3. General patterns or systemic issues
4. One positive observation if any

Return ONLY the plain text summary, no JSON, no headers."""

    try:
        resp = get_client().messages.create(
            model="claude-opus-4-5",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        executive_summary = resp.content[0].text.strip()
    except Exception as e:
        executive_summary = f"Summary generation failed: {e}"

    return RepoReview(
        repo_url=repo_url,
        repo_name=repo_name,
        total_files=total_files,
        reviewed_files=len(file_reviews),
        file_reviews=file_reviews,
        critical_count=critical,
        high_count=high,
        medium_count=medium,
        low_count=low,
        overall_score=avg_score,
        top_issues=top_issues,
        executive_summary=executive_summary,
    )


# ── Helpers ────────────────────────────────────────────────────────────

def _empty_review(file_path: str, language: str, loc: int, error: str = "") -> FileReview:
    return FileReview(
        file_path=file_path,
        language=language,
        lines_of_code=loc,
        issues=[],
        overall_score=0,
        summary=f"Review could not be completed. Error: {error}",
    )
