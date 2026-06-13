# 🔍 Repo Explainer Agent

> Point it at any codebase — local or GitHub URL — and ask it anything. It maps the architecture, reads the code, and gives you grounded answers.

---

## Overview

Repo Explainer is an agentic AI system built on the **Claude Agent SDK**. It uses multi-step reasoning and file-system tools to deeply understand any codebase and answer natural language questions about it.

It is built around three pillars:

| Pillar | What it does |
|--------|-------------|
| 🤖 **Agent** | Multi-step reasoning agent — reads files, searches code, maps dependencies, synthesizes answers |
| 📊 **Eval Harness** | Systematic test suite with 8 test cases and 4 weighted metrics to measure answer quality |
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
└──────────────────────────────────────────────────────┘
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
# Just run via Claude Code — it handles auth automatically
claude "python scripts/run_agent.py --repo . --question 'How does this project work?'"
```

---

## Usage

### Ask about a local repo
```bash
python scripts/run_agent.py --repo /path/to/any/repo --question "How does authentication work?"
```

### Ask about a GitHub repo (no cloning needed)
```bash
python scripts/run_agent.py --repo https://github.com/any/public-repo --question "What is the overall architecture?"
```

### Example output
```
🔍 Repo Explainer Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 Repo: /path/to/repo
❓ Question: How does authentication work?

🤖 Thinking...

✅ Answer:
The authentication system uses JWT tokens issued at /auth/login.
Tokens are validated in auth.py via the decode_token() function,
which is called by the require_auth decorator applied to protected routes.

📊 Stats: 4 iterations | Tools used: get_file_tree, read_file, search_code
```

### Run the Eval Suite
```bash
python scripts/run_evals.py
```

### Run the Optimizer
```bash
python scripts/run_optimizer.py --iterations 5
```

---

## The Agent

The agent runs a proper **agentic loop** — not a single-shot API call:

1. Receives repo path or GitHub URL + question
2. Always starts with `get_file_tree` + `detect_language_and_framework`
3. Reads relevant files, searches for patterns
4. Synthesizes a grounded answer from actual code it has read
5. Stops when it has sufficient context (max 10 iterations)

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

8 test cases run against a sample FastAPI project in `evals/fixtures/sample_project/`.

**Metrics (weighted):**

| Metric | Weight | What it measures |
|--------|--------|-----------------|
| Topic Coverage | 40% | Are expected concepts present in the answer? |
| Hallucination Penalty | 30% | Does the answer contain fabricated information? |
| Answer Length | 15% | Is the answer appropriately detailed? |
| Groundedness | 15% | Did the agent actually read the code to answer? |

A test case **passes** if overall score ≥ 0.6.

---

## Optimizer

The optimizer runs an automated **prompt tuning loop**:

```
baseline eval → identify failed cases → ask Claude to improve system prompt
→ re-run evals → keep if better → revert if worse → repeat N times
```

Uses `claude-haiku-4-5-20251001` for cost efficiency at every stage.

---

## Results

| Run | Pass Rate | Avg Score | Topic Coverage | Groundedness |
|-----|-----------|-----------|----------------|--------------|
| Baseline | — | — | — | — |
| After Optimization | — | — | — | — |
| Δ Improvement | — | — | — | — |

> Results populated after running the optimizer. See `optimizer/results/` for full JSON reports.

---

## Design Decisions

- **Claude Agent SDK over raw API** — proper agentic loop with tool use, not a single-shot prompt
- **Haiku for cost efficiency** — fast iteration on evals and optimizer without burning credits
- **Grounded answers only** — agent is instructed never to claim something it has not read in the actual code
- **GitHub URL support** — clones to a temp directory transparently so remote repos work out of the box
- **Weighted metrics** — hallucination penalty weighted heavily (30%) because a wrong answer is worse than an incomplete one

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
│       └── sample_project/  # Sample FastAPI project for testing
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

*Built with the Claude Agent SDK · MIT License*