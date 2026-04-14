"""
main.py — CLI entry point for the AI Code Review Agent.

Usage:
  python main.py https://github.com/owner/repo
  python main.py https://github.com/owner/repo --focus security,bugs --open-pr
  python main.py https://github.com/owner/repo --max 10 --severity high
  python main.py --local ./my-project
"""

import argparse
import sys
from rich.console import Console
from config import EnvConfig

console = Console()


def validate_env() -> bool:
    if not EnvConfig.ANTHROPIC_API_KEY:
        console.print("[bold red]Error:[/bold red] ANTHROPIC_API_KEY is not set.")
        console.print("Copy [dim].env.example[/dim] → [dim].env[/dim] and add your key.")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="AI Code Review Agent — powered by Claude"
    )
    parser.add_argument("repo", nargs="?", help="GitHub repo URL to review")
    parser.add_argument("--local", type=str, help="Path to local repo (alternative to URL)")
    parser.add_argument("--focus", type=str,
                        help="Comma-separated focus areas: bugs,security,performance,style,refactor,documentation (default: all)")
    parser.add_argument("--severity", type=str, choices=["low", "medium", "high", "critical"],
                        help="Minimum severity to report (default: medium)")
    parser.add_argument("--max", type=int, help="Max files to review (default: 20)")
    parser.add_argument("--open-pr", action="store_true",
                        help="Open a GitHub PR with findings (requires GITHUB_TOKEN)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't open PRs, just generate reports")
    parser.add_argument("--live", action="store_true",
                        help="Open real GitHub PRs (requires GITHUB_TOKEN)")
    args = parser.parse_args()

    if not args.repo and not args.local:
        parser.print_help()
        sys.exit(1)

    # Override env from CLI
    if args.focus:
        EnvConfig.REVIEW_FOCUS = [f.strip() for f in args.focus.split(",")]
    if args.severity:
        EnvConfig.SEVERITY_THRESHOLD = args.severity
    if args.max:
        EnvConfig.MAX_FILES = args.max
    if args.dry_run:
        EnvConfig.DRY_RUN = True
    if args.live:
        EnvConfig.DRY_RUN = False

    if not validate_env():
        sys.exit(1)

    from agent.orchestrator import CodeReviewAgent
    agent = CodeReviewAgent()

    if args.local:
        # Wrap local path as a fake URL for the agent
        from pathlib import Path
        from tools.repo_loader import collect_files, read_file, get_language
        from agent.reviewer import review_file, synthesize_repo_review
        from tools.reporter import (
            generate_markdown_report, save_json_report,
            save_refactored_files, print_terminal_summary,
        )
        local_path = Path(args.local).resolve()
        repo_name = local_path.name
        console.print(f"[cyan]Reviewing local repo:[/cyan] {local_path}")
        files = collect_files(local_path)
        file_reviews = []
        for fpath in files:
            rel = str(fpath.relative_to(local_path))
            code = read_file(fpath)
            lang = get_language(fpath)
            if code.strip():
                fr = review_file(rel, code, lang)
                file_reviews.append(fr)
                console.print(f"  {fr.overall_score}/100  {rel}")
        if file_reviews:
            repo_review = synthesize_repo_review(
                str(local_path), repo_name, len(files), file_reviews
            )
            generate_markdown_report(repo_review)
            save_json_report(repo_review)
            save_refactored_files(repo_review)
            print_terminal_summary(repo_review)
    else:
        agent.run(args.repo, open_pr=args.open_pr)


if __name__ == "__main__":
    main()
