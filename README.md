# 🤖 AI Code Review & Refactor Agent

> Point it at any GitHub repo. Claude reads the codebase, finds bugs, security vulnerabilities, and performance issues — then opens a Pull Request with fixes.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Claude](https://img.shields.io/badge/Powered%20by-Claude%20Opus-blueviolet?logo=anthropic)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## 📸 Demo

```
AI Code Review Agent
Target: https://github.com/owner/my-project
Mode: DRY RUN | Focus: bugs, security, performance | Threshold: medium+

Cloning https://github.com/owner/my-project ...
✓ Cloned → data/repos/owner__my-project
✓ 12 files collected for review.

Reviewing files... ━━━━━━━━━━━━━━━━━━━━━━━━ 100%

   45/100  3 issues  src/auth.py
   91/100  1 issue   src/utils.py
   33/100  6 issues  src/database.py
   78/100  2 issues  src/api.py

Synthesizing repo-level review...

╭─────────────────────────────────────────────────────╮
│ AI Code Review — owner__my-project                  │
│ Score: 62/100                                       │
│ 🔴 2 critical  🟠 4 high  🟡 6 medium  🟢 3 low    │
╰─────────────────────────────────────────────────────╯

┌──────────┬──────────────┬───────────────┬──────┬───────────────────────────────┐
│ Severity │ Category     │ File          │ Line │ Issue                         │
├──────────┼──────────────┼───────────────┼──────┼───────────────────────────────┤
│ CRITICAL │ security     │ auth.py       │  42  │ SQL injection vulnerability    │
│ CRITICAL │ security     │ auth.py       │  87  │ Hardcoded secret key          │
│ HIGH     │ bug          │ database.py   │  15  │ Missing connection close       │
│ HIGH     │ performance  │ database.py   │  67  │ N+1 query in loop             │
└──────────┴──────────────┴───────────────┴──────┴───────────────────────────────┘

✓ Review complete!
  📄 Markdown report: data/reports/owner__my-project_20240115.md
  📦 JSON report:     data/reports/owner__my-project_20240115.json
  🔧 Refactored files: 4 saved
  🔗 PR: https://github.com/owner/my-project/pull/42
```

---

## 🧠 How It Works

```
┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐
│  1. CLONE    │──▶│  2. WALK     │──▶│  3. REVIEW (Claude)  │
│              │   │              │   │                      │
│  GitPython   │   │  Collect     │   │  Per-file analysis:  │
│  depth=1     │   │  .py .js .ts │   │  bugs, security,     │
│  (free)      │   │  .go .java   │   │  performance, style  │
│              │   │  .rs .cpp    │   │  Score 0–100         │
└──────────────┘   └──────────────┘   └──────────────────────┘
                                                │
                                                ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐
│  6. PR       │◀──│  5. PATCHES  │◀──│  4. SYNTHESIZE       │
│              │   │              │   │                      │
│  GitHub API  │   │  Refactored  │   │  Repo-level report   │
│  New branch  │   │  versions of │   │  Executive summary   │
│  PR with     │   │  each file   │   │  Top issues ranked   │
│  findings    │   │  saved       │   │  Overall score       │
└──────────────┘   └──────────────┘   └──────────────────────┘
```

### What Claude checks for

| Category | Examples |
|---|---|
| 🐛 **Bugs** | Off-by-one errors, null pointer dereferences, incorrect logic, race conditions |
| 🔒 **Security** | SQL injection, hardcoded secrets, insecure deserialization, missing auth checks |
| ⚡ **Performance** | N+1 queries, O(n²) loops, missing indexes, memory leaks, unnecessary re-renders |
| ✨ **Style** | Naming conventions, dead code, magic numbers, overly complex functions |
| ♻️ **Refactor** | DRY violations, God classes, missing abstractions, coupling issues |
| 📝 **Documentation** | Missing docstrings, unclear variable names, undocumented side effects |

---

## ✨ Features

| Feature | Details |
|---|---|
| 🌐 Multi-language | Python, JS, TS, Java, Go, Rust, C/C++, C#, Ruby, PHP |
| 🧠 AI-powered | Claude Opus analyzes each file with full context |
| 🔧 Auto-refactor | Claude rewrites files with all issues fixed |
| 📄 Rich reports | Markdown + JSON reports with before/after diffs |
| 🔗 GitHub PR | Opens PRs with findings and refactored code |
| 🎯 Configurable focus | Tune to bugs-only, security-only, or all categories |
| 📊 Severity filter | Skip noise — only report medium+ or high+ issues |
| 💾 Local repo support | Review local codebases without pushing to GitHub |
| 🔁 Smart caching | Repos are cached — re-runs skip re-cloning |

---

## 🗂️ Project Structure

```
code-review-agent/
├── main.py                    # CLI entry point
├── config.py                  # Config, env vars, Pydantic models
├── requirements.txt
├── .env.example
│
├── agent/
│   ├── reviewer.py            # Claude: file review + refactoring
│   └── orchestrator.py        # Main loop (clone → review → report → PR)
│
├── tools/
│   ├── repo_loader.py         # GitPython clone + file walker
│   ├── reporter.py            # Markdown + JSON report generator
│   └── pr_opener.py           # GitHub API PR creator
│
└── data/
    ├── repos/                 # Cached repo clones (auto-generated)
    ├── reports/               # Markdown + JSON review reports
    └── patches/               # Refactored file versions
```

---

## 🚀 Quickstart

### 1. Clone & install

```bash
git clone https://github.com/yourusername/ai-code-review-agent.git
cd ai-code-review-agent

python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

### 3. Review a public repo

```bash
python main.py https://github.com/owner/repo
```

### 4. Check the report

```
data/reports/owner__repo_20240115_143022.md   ← full Markdown report
data/reports/owner__repo_20240115_143022.json ← structured JSON
data/patches/owner__repo/                     ← refactored files
```

### 5. Open a real PR (when ready)

```bash
# Add GITHUB_TOKEN to .env, then:
python main.py https://github.com/owner/repo --open-pr --live
```

---

## ⚙️ CLI Reference

```
python main.py [REPO_URL] [OPTIONS]

Arguments:
  REPO_URL              GitHub repo URL (https://github.com/owner/repo)

Options:
  --local PATH          Review a local directory instead of GitHub URL
  --focus CATEGORIES    Comma-separated: bugs,security,performance,style,refactor,documentation
                        Default: bugs,security,performance
  --severity LEVEL      Minimum severity: low | medium | high | critical
                        Default: medium
  --max INT             Max files to review per run (default: 20)
  --open-pr             Open a GitHub PR with findings
  --dry-run             Generate reports only, no PRs
  --live                Actually open GitHub PRs

Examples:
  # Security-only audit
  python main.py https://github.com/owner/repo --focus security --severity high

  # Full review of local project
  python main.py --local ./my-project --focus all

  # Review + auto open PR
  python main.py https://github.com/owner/repo --open-pr --live

  # Review just 5 files, focus on bugs
  python main.py https://github.com/owner/repo --max 5 --focus bugs
```

---

## 📊 Sample Report Output

The agent generates a full Markdown report like this:

```markdown
# 🤖 AI Code Review Report

**Repository:** https://github.com/owner/repo
**Overall Score:** 🟠 62/100

## 📊 Issue Summary
| Severity | Count |
|---|---|
| 🔴 Critical | 2 |
| 🟠 High | 4 |
| 🟡 Medium | 6 |
| 🟢 Low | 3 |

## 🚨 Top Issues

### 1. 🔴 SQL Injection Vulnerability
- **File:** `src/auth.py` (lines 42–45)
- **Severity:** CRITICAL | **Category:** 🔒 security
- **Problem:** User input is directly interpolated into SQL query without sanitization
- **Fix:** Use parameterized queries or an ORM

**Before:**
```python
query = f"SELECT * FROM users WHERE name = '{username}'"
```
**After:**
```python
query = "SELECT * FROM users WHERE name = %s"
cursor.execute(query, (username,))
```
```

---

## 🔑 API Keys & Cost

| Service | Used For | Cost |
|---|---|---|
| Anthropic Claude | Code analysis + refactoring | ~$0.05–0.20 per file |
| GitPython | Repo cloning | Free |
| GitHub API | Opening PRs | Free (needs token) |

**Estimated cost per run (20 files):** ~$1–4 depending on file size

---

## 🔧 Supported Languages

Python · JavaScript · TypeScript · React (JSX/TSX) · Java · Go · Rust · C · C++ · C# · Ruby · PHP

---

## 🛠️ Customization

### Add custom review rules

Edit the prompt in `agent/reviewer.py` to add domain-specific rules:

```python
# Add to the prompt string:
"Also check for: missing rate limiting on API endpoints, "
"improper use of async/await, missing input validation on forms."
```

### Ignore specific files or directories

Edit `IGNORE_PATTERNS` in `config.py`:

```python
IGNORE_PATTERNS = [
    "node_modules", "__pycache__", "migrations",
    "*.test.js", "*.spec.ts",   # skip test files
]
```

---

## 🤝 Contributing

PRs welcome! Ideas:

- [ ] Support for GitLab and Bitbucket
- [ ] VS Code extension integration
- [ ] Incremental review (only changed files in a PR)
- [ ] Test generation for uncovered functions
- [ ] Complexity metrics (cyclomatic complexity via radon)
- [ ] GitHub Actions workflow to auto-trigger on PRs

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

## 🙋 Author

Built by [Your Name](https://github.com/yourusername)

> ⭐ Star this repo if it helped you ship better code!
