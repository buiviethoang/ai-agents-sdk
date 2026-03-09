# How to Use AI Agents with notification-service

AI agents write Go code and review it for you. You describe a task; they build, review (max 2 rounds), and validate.

---

## 1. Prerequisites

- Go 1.22+
- [golangci-lint](https://golangci-lint.run/usage/install/)
- Anthropic API key (`ANTHROPIC_API_KEY`)

---

## 2. One-Time Setup (notification-service)

### 2.1 Install CLI

```bash
go install github.com/buiviethoang/ai-agents-sdk/cmd/ai-engineer@latest
```

### 2.2 Add SDK as dependency (optional, for Go tooling)

```bash
cd /path/to/notification-service
go get github.com/buiviethoang/ai-agents-sdk
```

### 2.3 Create `ARCHITECTURE.md` in project root

AI agents read this to understand your structure.

```markdown
# notification-service

## Overview

Notification service for sending emails, push, SMS.

## Layout

notification-service/
├── cmd/           # API server, workers
├── internal/      # Handlers, business logic, clients
├── pkg/           # Shared packages
└── scripts/       # validate.sh

## Conventions

- Use context.Context for cancellation
- Table-driven tests
- Avoid global state
```

### 2.4 Create `scripts/validate.sh`

```bash
#!/bin/bash
set -e
echo "Formatting"
go fmt ./...
echo "Vet"
go vet ./...
echo "Lint"
golangci-lint run
echo "Test"
go test ./...
echo "Coverage"
go test -cover ./...
```

```bash
chmod +x scripts/validate.sh
```

### 2.5 Set API key

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Or add to `~/.bashrc` / `~/.zshrc`.

---

## 3. Running Tasks

**Always run from your project root** (notification-service).

### Basic usage

```bash
cd /path/to/notification-service

# Simple form (easiest)
ai-engineer "Add Redis cache for notification templates"

# Or with run subcommand
ai-engineer run "Add Redis cache for notification templates"
```

### Example tasks

```bash
# New feature
ai-engineer "Add email retry logic with exponential backoff"

# Refactor
ai-engineer "Extract SMS sending into a separate package"

# Tests
ai-engineer "Add table-driven tests for notification validator"

# Bug fix
ai-engineer "Fix race condition in cache update"
```

### Useful flags

| Flag | Default | Description |
|------|---------|-------------|
| `--dry-run` | false | Don't write files or run validation |
| `--max-files` | 15 | Max files sent to AI (token control) |
| `--max-tokens` | 4096 | Max output tokens |

```bash
# Preview without changing files
ai-engineer --dry-run "Add Redis cache for templates"

# More context for large changes
ai-engineer --max-files=20 "Refactor notification pipeline"
```

---

## 4. What Happens When You Run

1. **Context** – Agent reads `ARCHITECTURE.md` and relevant `.go` files.
2. **Build** – Builder agent writes/updates code and tests.
3. **Review** – Reviewer checks for bugs, races, edge cases.
4. **Debate** – Up to 2 iterations if changes are requested.
5. **Validate** – `go fmt`, `go vet`, `golangci-lint`, `go test`, `go test -cover`.

If validation fails, no files are kept; you see the error.

---

## 5. Quick Reference

```bash
# From notification-service root
export ANTHROPIC_API_KEY=sk-ant-...
ai-engineer "Your task here"
```

---

## 6. Programmatic Use (Go library)

```go
import (
    "context"
    "github.com/buiviethoang/ai-agents-sdk/sdk"
)

result, err := sdk.Run(context.Background(), "Add Redis cache", sdk.Config{
    RootDir:   "/path/to/notification-service",
    MaxFiles:  15,
})
if err != nil {
    log.Fatal(err)
}
// result.Approved, result.Files, result.Iterations
```
