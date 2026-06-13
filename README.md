# 🔍 Repo Explainer Agent

> An agentic AI system that reads any codebase, maps its architecture, and answers questions about how it works — built on the Claude Agent SDK.

---

## Overview

It demonstrates three pillars of production-grade agentic AI engineering:

| Pillar | What it does |
|--------|-------------|
| 🤖 **Agent** | Multi-step reasoning agent using Claude Agent SDK — reads files, searches code, maps dependencies |
| 📊 **Eval Harness** | Systematic test suite with 8 test cases and 4 weighted metrics to measure agent quality |
| ⚡ **Optimizer** | Automated prompt tuning loop that uses eval scores to iteratively improve the agent |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    CLI Entry Point                   │
│              scripts/run_agent.py                    │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│                  Agent Core                          │
│            agent/repo_explainer.py                   │
│                                                      │
│  ┌─────────────┐     ┌──────────────────────────┐   │
│  │System Prompt│     │      Agentic Loop         │   │
│  │agent/       │────▶│  send → tool_use →        │   │
│  │prompts.py   │     │  execute → send result →  │   │
│  └─────────────┘     │  repeat → final answer    │   │
│                      └──────────────────────────-┘   │
└─────────────────────────────────────────────────────-┘
                      │
┌─────────────────────▼───────────────────────────────┐
│                    Tools Layer                       │
│                  agent/tools.py                      │
│                                                      │
│  read_file │ list_directory │ search_code │          │
│  get_file_tree │ detect_language_and_framework       │
└─────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│                  Claude API                          │
│           claude-haiku-4-5-20251001                  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  Eval + Optimizer                    │
│                                                      │
│  evals/harness.py ──▶ evals/metrics.py              │
│         │                                            │
│         ▼                                            │
│  optimizer/optimizer.py                              │
│  (prompt tuning loop — uses eval scores to improve) │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- An Anthropic API key **or** Claude Code (Pro/Max — zero metered cost)

### Installation

```bash
# Clone the repo
git clone https://github.com/AxaySharma/repo-explainer.git
cd repo-explainer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Running with Claude Code (recommended — no API cost)
```bash
# Claude Code routes through your Pro/Max subscription
# Just run via Claude Code and it handles auth automatically
claude "python scripts/run_agent.py --repo . --question 'How does this project work?'"
```

---

## Usage

### 1. Run the Agent
```bash
python scripts/run_agent.py --repo /path/to/any/repo --question "How does authentication work?"
```

**Example output:**
```
🔍 Repo Explainer Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 Repo: /path/to/repo
❓ Question: How does authentication work?

🤖 Thinking...

✅ Answer:
The authentication system uses JWT tokens...

📊 Stats: 4 iterations | Tools used: get_file_tree, read_file, search_code
```

### 2. Run Evals
```bash
python scripts/run_evals.py
```

### 3. Run Optimizer
```bash
python scripts/run_optimizer.py --iterations 5
```

---

## The Agent

The agent runs a proper **agentic loop** — not a single-shot API call:

1. Receives repo path + question
2. Always starts with `get_file_tree` + `detect_language_and_framework`
3. Reads relevant files, searches for patterns
4. Synthesizes a grounded answer from actual code
5. Stops when it has enough context (max 10 iterations)

**Tools available:**

| Tool | Purpose |
|------|---------|
| `read_file` | Read any file with line numbers |
| `list_directory` | Browse directory contents |
| `search_code` | Grep patterns across the codebase |
| `get_file_tree` | Full ASCII repo structure |
| `detect_language_and_framework` | Identify stack from config files |

---

## Eval Harness

8 test cases against a sample FastAPI project in `evals/fixtures/sample_project/`.

**Metrics (weighted):**

| Metric | Weight | What it measures |
|--------|--------|-----------------|
| Topic Coverage | 40% | Are expected concepts present in the answer? |
| Hallucination Penalty | 30% | Does the answer contain wrong information? |
| Answer Length | 15% | Is the answer appropriately detailed? |
| Groundedness | 15% | Did the agent actually read the code? |

A test case **passes** if overall score ≥ 0.6.

---

## Optimizer

The optimizer runs a **prompt tuning loop**:

```
baseline eval → score failed cases → ask Claude to improve prompt
→ re-eval → keep if better → repeat N times → report best prompt
```

Uses `claude-haiku-4-5-20251001` for cost efficiency at every stage.

---

## Results

| Run | Pass Rate | Avg Score | Topic Coverage | Groundedness |
|-----|-----------|-----------|----------------|--------------|
| Baseline | — | — | — | — |
| After Optimization | — | — | — | — |
| Δ Improvement | — | — | — | — |

> Results will be filled in after running the optimizer. See `optimizer/results/` for full JSON reports.

---

## Design Decisions

- **Claude Agent SDK over raw API** — proper agentic loop with tool use, not a single-shot call
- **Haiku for cost efficiency** — fast iteration on evals and optimizer without burning credits
- **Grounded answers only** — agent is instructed to never claim something it hasn't read in the code
- **Weighted metrics** — hallucination penalty weighted heavily (30%) because wrong answers are worse than incomplete ones

---

## What I'd Do With More Time

- Add semantic search over code (embeddings) for large repos
- Support remote GitHub URLs, not just local paths
- Add a web UI for interactive Q&A
- Expand eval set to cover more edge cases (monorepos, polyglot projects)

---

## Project Structure

```
repo-explainer/
├── agent/
│   ├── repo_explainer.py    # Core agent + agentic loop
│   ├── tools.py             # File system tools
│   └── prompts.py           # System prompt + templates
├── evals/
│   ├── harness.py           # Eval runner
│   ├── metrics.py           # Scoring functions
│   ├── test_cases.py        # 8 test cases
│   └── fixtures/
│       └── sample_project/  # Fake FastAPI project for testing
├── optimizer/
│   ├── optimizer.py         # Prompt tuning loop
│   └── results/             # Before/after JSON reports
├── scripts/
│   ├── run_agent.py         # CLI: run the agent
│   ├── run_evals.py         # CLI: run eval suite
│   └── run_optimizer.py     # CLI: run optimizer
├── .env.example
├── requirements.txt
└── README.md
```

---

*Built with ❤️ using Claude Agent SDK*