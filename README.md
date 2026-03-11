# ai-agents-sdk

LangGraph pipeline for AI coding agents: Architect → Coder → Reviewer → DevOps.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## CLI Usage

```bash
export ANTHROPIC_API_KEY=your-key
pipeline "Add Redis cache to user profile API"
```

Flags: `--dry-run`, `--root-dir`, `--verbose`

See [docs/HOWTO.md](docs/HOWTO.md) for setup and usage.

## Layout

- `src/pipeline/` – LangGraph pipeline
- `src/pipeline/nodes/` – Architect, Coder, Reviewer, DevOps
- `src/pipeline/tools/` – gosec, golangci-lint, validate, git
- `scripts/` – validate.sh, helper.sh
