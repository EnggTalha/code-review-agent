"""
tools/repo_loader.py — Clone a GitHub repo and walk its source files.
No API key needed — uses GitPython (free).
"""

from __future__ import annotations
import shutil
from pathlib import Path
from typing import List, Tuple
from rich.console import Console
import git

from config import (
    EnvConfig, REPOS_DIR, SUPPORTED_EXTENSIONS, IGNORE_PATTERNS
)

console = Console()


def clone_or_load(repo_url: str) -> Tuple[Path, str]:
    """
    Clone a GitHub repo (or reuse cached clone).
    Returns (local_path, repo_name).
    """
    repo_name = _parse_repo_name(repo_url)
    local_path = REPOS_DIR / repo_name

    if local_path.exists():
        console.print(f"[dim]Using cached clone: {local_path}[/dim]")
        try:
            repo = git.Repo(local_path)
            repo.remotes.origin.pull()
            console.print("[dim]Pulled latest changes.[/dim]")
        except Exception:
            pass
        return local_path, repo_name

    console.print(f"[cyan]Cloning[/cyan] {repo_url} ...")
    try:
        git.Repo.clone_from(repo_url, local_path, depth=1)
        console.print(f"[green]✓[/green] Cloned → {local_path}")
    except git.exc.GitCommandError as e:
        raise RuntimeError(f"Failed to clone repo: {e}")

    return local_path, repo_name


def collect_files(repo_path: Path) -> List[Path]:
    """
    Walk the repo and return source files to review.
    Respects MAX_FILES, MAX_FILE_SIZE_KB, IGNORE_PATTERNS, and SUPPORTED_EXTENSIONS.
    """
    files: List[Path] = []

    for path in sorted(repo_path.rglob("*")):
        if not path.is_file():
            continue
        if _should_ignore(path, repo_path):
            continue
        if path.suffix not in SUPPORTED_EXTENSIONS:
            continue

        size_kb = path.stat().st_size / 1024
        if size_kb > EnvConfig.MAX_FILE_SIZE_KB:
            console.print(f"  [dim]Skipping {path.name} — {size_kb:.0f}KB > limit[/dim]")
            continue

        files.append(path)

        if len(files) >= EnvConfig.MAX_FILES:
            console.print(f"[yellow]File cap reached ({EnvConfig.MAX_FILES}). Use --max to increase.[/yellow]")
            break

    console.print(f"[green]✓[/green] {len(files)} files collected for review.")
    return files


def read_file(path: Path) -> str:
    """Read a source file, returning its content as a string."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"# Could not read file: {e}"


def get_language(path: Path) -> str:
    return SUPPORTED_EXTENSIONS.get(path.suffix, "Unknown")


def cleanup_clone(repo_name: str) -> None:
    """Delete a cached clone to free disk space."""
    local_path = REPOS_DIR / repo_name
    if local_path.exists():
        shutil.rmtree(local_path)
        console.print(f"[dim]Removed cached clone: {local_path}[/dim]")


# ── Helpers ────────────────────────────────────────────────────────────
def _parse_repo_name(url: str) -> str:
    """Extract owner/repo slug from a GitHub URL."""
    url = url.rstrip("/").rstrip(".git")
    parts = url.split("/")
    return f"{parts[-2]}__{parts[-1]}"


def _should_ignore(path: Path, repo_root: Path) -> bool:
    relative = str(path.relative_to(repo_root))
    for pattern in IGNORE_PATTERNS:
        if pattern.startswith("*"):
            if path.name.endswith(pattern[1:]):
                return True
        elif pattern in relative.split("/"):
            return True
    return False
