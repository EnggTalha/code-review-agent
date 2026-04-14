"""
agent/orchestrator.py — Main agentic loop for the Code Review Agent.
Coordinates: clone → walk → review → report → PR.
"""

from __future__ import annotations
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from config import EnvConfig, FileReview
from tools.repo_loader import clone_or_load, collect_files, read_file, get_language
from tools.reporter import (
    generate_markdown_report, save_json_report,
    save_refactored_files, print_terminal_summary,
)
from tools.pr_opener import open_review_pr
from agent.reviewer import review_file, synthesize_repo_review

console = Console()


class CodeReviewAgent:
    """
    Autonomous code review agent.

    Flow:
    1. Clone the target GitHub repo (free, GitPython)
    2. Walk and collect source files (respects limits + ignore patterns)
    3. Claude reviews each file → structured issues + refactored code
    4. Synthesize repo-level report with executive summary
    5. Generate Markdown + JSON reports
    6. Save refactored files as patches
    7. Open a GitHub PR with findings (optional)
    """

    def run(self, repo_url: str, open_pr: bool = False) -> None:
        console.print(f"\n[bold cyan]AI Code Review Agent[/bold cyan]")
        console.print(f"Target: [bold]{repo_url}[/bold]")
        console.print(
            f"Mode: {'[yellow]DRY RUN[/yellow]' if EnvConfig.DRY_RUN else '[red]LIVE[/red]'} | "
            f"Focus: {', '.join(EnvConfig.REVIEW_FOCUS)} | "
            f"Threshold: {EnvConfig.SEVERITY_THRESHOLD}+\n"
        )

        # ── Step 1: Clone ───────────────────────────────────────────────
        try:
            repo_path, repo_name = clone_or_load(repo_url)
        except RuntimeError as e:
            console.print(f"[red]✗ Clone failed:[/red] {e}")
            return

        # ── Step 2: Collect files ───────────────────────────────────────
        files = collect_files(repo_path)
        if not files:
            console.print("[yellow]No reviewable source files found.[/yellow]")
            return

        total_files = _count_all_source_files(repo_path)

        # ── Step 3: Review each file ────────────────────────────────────
        file_reviews: list[FileReview] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Reviewing files...", total=len(files))

            for fpath in files:
                rel_path = str(fpath.relative_to(repo_path))
                progress.update(task, description=f"Reviewing [cyan]{rel_path}[/cyan]")

                code = read_file(fpath)
                language = get_language(fpath)

                if not code.strip():
                    progress.advance(task)
                    continue

                review = review_file(rel_path, code, language)
                file_reviews.append(review)

                # Live feedback
                issue_count = len(review.issues)
                score_color = "green" if review.overall_score >= 70 else "yellow" if review.overall_score >= 50 else "red"
                console.print(
                    f"  [{score_color}]{review.overall_score:>3}/100[/{score_color}]  "
                    f"{issue_count} issue{'s' if issue_count != 1 else '':1}  "
                    f"[dim]{rel_path}[/dim]"
                )

                progress.advance(task)

        if not file_reviews:
            console.print("[yellow]No file reviews completed.[/yellow]")
            return

        # ── Step 4: Synthesize repo review ──────────────────────────────
        repo_review = synthesize_repo_review(
            repo_url, repo_name, total_files, file_reviews
        )

        # ── Step 5: Generate reports ────────────────────────────────────
        md_path   = generate_markdown_report(repo_review)
        json_path = save_json_report(repo_review)

        # ── Step 6: Save refactored files ───────────────────────────────
        refactored = save_refactored_files(repo_review)

        # ── Step 7: Open PR ─────────────────────────────────────────────
        pr_url = None
        if open_pr or not EnvConfig.DRY_RUN:
            pr_url = open_review_pr(repo_review, refactored)

        # ── Print summary ───────────────────────────────────────────────
        print_terminal_summary(repo_review)

        console.print("[bold green]✓ Review complete![/bold green]")
        console.print(f"  📄 Markdown report: [dim]{md_path}[/dim]")
        console.print(f"  📦 JSON report:     [dim]{json_path}[/dim]")
        if refactored:
            console.print(f"  🔧 Refactored files: [dim]{len(refactored)} saved[/dim]")
        if pr_url:
            console.print(f"  🔗 PR: [link={pr_url}]{pr_url}[/link]")


def _count_all_source_files(repo_path: Path) -> int:
    from config import SUPPORTED_EXTENSIONS, IGNORE_PATTERNS
    count = 0
    for path in repo_path.rglob("*"):
        if path.is_file() and path.suffix in SUPPORTED_EXTENSIONS:
            rel = str(path.relative_to(repo_path))
            if not any(p in rel.split("/") for p in IGNORE_PATTERNS):
                count += 1
    return count
