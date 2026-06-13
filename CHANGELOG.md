# Changelog

All notable changes to this project will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/).

---

## [1.0.0] - 2026-06-13

### Added

#### Agent
- Core agentic loop in `agent/repo_explainer.py` using Anthropic Python SDK
- 5 filesystem tools: `read_file`, `list_directory`, `search_code`, `get_file_tree`, `detect_language_and_framework`
- Transparent GitHub URL support — clones to temp dir, cleans up automatically
- Path sandboxing to prevent traversal outside repo root
- `AgentResult` dataclass with answer, tools used, iterations, success, error

#### Prompts
- Detailed system prompt (600+ words) with mandatory exploration steps
- Optimizer meta-prompt for automated prompt improvement
- `build_user_prompt()` and `format_failed_cases()` helpers

#### Eval Harness
- 8 test cases covering architecture, framework, auth, database, endpoints, models, setup, and extensibility
- 4 weighted metrics: topic coverage (40%), hallucination penalty (30%), answer length (15%), groundedness (15%)
- Rich terminal output with color-coded pass/fail table
- JSON report auto-saved to `optimizer/results/` with timestamp

#### Optimizer
- Automated prompt tuning loop with N configurable iterations
- Keeps improved prompts, reverts regressions
- Saves best prompt to `agent/prompts_optimized.py`
- Full optimization report with before/after comparison table

#### CLI Scripts
- `scripts/run_agent.py` — ask any question about any repo with rich output and spinner
- `scripts/run_evals.py` — run full eval suite with optional custom prompt
- `scripts/run_optimizer.py` — run optimizer with dry-run mode and confirmation prompt

#### Infrastructure
- GitHub Actions CI workflow — runs on every push to `dev` and PR to `main`
- 25 unit tests for metrics module (all passing in 0.02s)
- Branch strategy: `dev` for development, `main` for stable releases
- `.env.example` with documented configuration options
- `CONTRIBUTING.md` with commit conventions and branch strategy
- Compatible with Anthropic API direct, OpenRouter, or any Claude-compatible gateway

### Results
- Baseline eval: **8/8 tests passing, average score 0.9917**
- Zero hallucinations across all baseline runs
- Perfect groundedness score (1.0000) — agent always reads code before answering
- Optimizer correctly identified baseline was already optimal and preserved the prompt

---

## [Unreleased]

### Potential Improvements
- Semantic search over code using embeddings for large repos
- Support for private GitHub repos via token auth
- Web UI for interactive Q&A sessions
- Expanded eval set for monorepos and polyglot projects

---