# How to Use AI Agents Pipeline

LangGraph pipeline with 4 agents: Architect (C) → Coder (A) → Reviewer (B) → DevOps (D).

---

## 1. Prerequisites

- Python 3.10+
- [golangci-lint](https://golangci-lint.run/usage/install/)
- [gosec](https://github.com/securego/gosec) (optional; skips if not installed)
- Anthropic API key (`ANTHROPIC_API_KEY`)

---

## 2. Setup

### 2.1 Install

```bash
pip install ai-agents-pipeline
```

Or from local: `pip install -e /path/to/ai-agents-sdk`

### 2.2 Set API key

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

For claudible.io (OpenAI-compat endpoint):

```bash
export LLM_CLIENT=openai
export LLM_BASE_URL=https://claudible.io/v1
export ANTHROPIC_API_KEY=your-claudible-token
```

### 2.3 Scaffold Go project

```bash
cd /path/to/your-go-project
pipeline init
```

Creates `ARCHITECTURE.md` and `scripts/validate.sh`. Edit ARCHITECTURE.md with your project overview.

---

## 3. Running

**Run from your Go project root.**

### Basic

```bash
pipeline "Add Redis cache for notification templates"
```

### With flags

| Flag | Default | Description |
|------|---------|-------------|
| `--dry-run` | false | Skip writes and validation |
| `--root-dir` | cwd | Project root |
| `--verbose` | false | Stream LLM tokens |
| `--no-stream` | false | Disable step-by-step output |
| `--interactive` / `-i` | false | Step-by-step with prompts (apply/edit/skip) |

```bash
# Preview
pipeline --dry-run "Add retry logic"

# From another dir
pipeline --root-dir /path/to/project "Add unit tests"
```

---

## 4. Flow

1. **Architect (C)** – Receives requirement, produces plan.md and task list.
2. **Coder (A)** – Implements each task; outputs `feature.go`, `feature_test.go`.
3. **Reviewer (B)** – Runs gosec, LLM review; routes back to A if issues.
4. **DevOps (D)** – Writes files, `go fmt`, golangci-lint, tests, git push.

If no `.go` files are produced, the reviewer is skipped.

---

## 5. Env vars

| Env | Purpose |
|-----|---------|
| `ANTHROPIC_API_KEY` | Claude API (or proxy key for openai client) |
| `LLM_CLIENT` | `anthropic` (native /v1/messages) or `openai` (claudible /v1/chat/completions) |
| `LLM_BASE_URL` | Base URL for openai client (default: https://claudible.io/v1) |
| `ROOT_DIR` | Project root (default: cwd) |
| `PIPELINE_DRY_RUN` | 1/true/yes to skip writes |
| `PIPELINE_VERBOSE` | 1/true/yes for verbose logs |
| `JENKINS_URL`, `JENKINS_JOB`, `JENKINS_TOKEN` | Placeholder; no-op if unset |

---

## 6. Programmatic use

```python
from pipeline.graph import run_graph, run_graph_stream

# Blocking
result = run_graph(requirement="Add Redis cache", root_dir="/path/to/project")
# result["files"], result["plan_md"], result["tasks"], ...

# Streaming
for event_type, key, data in run_graph_stream(requirement="Add Redis cache", root_dir="/path/to/project"):
    if event_type == "step":
        print(key, data)
    elif event_type == "progress":
        print(data.get("msg"))
    elif event_type == "done":
        result = data
```
